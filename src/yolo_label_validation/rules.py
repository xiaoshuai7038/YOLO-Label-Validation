from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable

from .artifact_io import (
    load_run_artifact,
    write_run_artifact,
)
from .bootstrap import ensure_run_directory_layout
from .contracts import RunManifest


@dataclass(frozen=True, slots=True)
class ThresholdPolicy:
    thresholds_version: str
    global_thresholds: dict[str, Any]
    per_class: dict[str, dict[str, Any]]

    def snapshot(self) -> dict[str, Any]:
        return {
            "thresholds_version": self.thresholds_version,
            "global": self.global_thresholds,
            "per_class": self.per_class,
        }


def load_threshold_policy(
    config_path: Path | None = None,
    *,
    payload: dict[str, Any] | None = None,
) -> ThresholdPolicy:
    if payload is None and config_path is None:
        payload = {
            "thresholds_version": "th_v1",
            "global": {
                "min_box_pixels": 4,
                "duplicate_iou": 0.9,
                "expanded_crop_ratio": 1.5,
                "refine_window_ratio": 1.5,
            },
            "per_class": {},
        }
    elif payload is None:
        payload = _load_mapping_file(config_path)

    if not isinstance(payload, dict):
        raise ValueError("threshold policy must be a mapping")
    thresholds_version = str(payload.get("thresholds_version", "")).strip()
    if not thresholds_version:
        raise ValueError("threshold policy is missing thresholds_version")

    global_thresholds = payload.get("global", {})
    per_class = payload.get("per_class", {})
    if not isinstance(global_thresholds, dict) or not isinstance(per_class, dict):
        raise ValueError("threshold policy global and per_class sections must be mappings")
    return ThresholdPolicy(
        thresholds_version=thresholds_version,
        global_thresholds=_sorted_mapping(global_thresholds),
        per_class={
            str(class_name): _sorted_mapping(values)
            for class_name, values in sorted(per_class.items())
        },
    )


def build_golden_set_manifest(
    image_index: dict[str, Any],
    *,
    run_manifest: dict[str, Any],
    golden_set_version: str = "golden_v1",
    selected_image_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    images = image_index.get("images", [])
    selected_ids = sorted(set(selected_image_ids or []))
    if not selected_ids:
        selected_ids = [image["image_id"] for image in sorted(images, key=lambda item: item["image_id"])[: min(5, len(images))]]

    image_lookup = {image["image_id"]: image for image in images}
    selected_images = []
    for image_id in selected_ids:
        image = image_lookup.get(image_id)
        if image is None:
            raise ValueError(f"golden-set image_id not found in image index: {image_id}")
        selected_images.append(
            {
                "image_id": image_id,
                "selection_reason": "deterministic_seed",
                "annotation_count": image.get("annotation_count", 0),
            }
        )

    return {
        "golden_set_version": golden_set_version,
        "dataset_version": run_manifest["dataset_version"],
        "source_run_id": run_manifest["run_id"],
        "selected_images": selected_images,
        "metric_kind": "pending",
        "notes": [
            "Local harness contract generated without live golden labels.",
        ],
    }


def build_golden_eval_report(
    golden_set_manifest: dict[str, Any],
    *,
    rule_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    selected_image_ids = {image["image_id"] for image in golden_set_manifest["selected_images"]}
    observed_issue_count = sum(1 for issue in rule_issues if issue["image_id"] in selected_image_ids)
    return {
        "golden_set_version": golden_set_manifest["golden_set_version"],
        "source_run_id": golden_set_manifest["source_run_id"],
        "evaluated_image_count": len(selected_image_ids),
        "observed_issue_count": observed_issue_count,
        "rule_issue_precision": {
            "value": None,
            "metric_kind": "pending",
        },
        "rule_issue_recall": {
            "value": None,
            "metric_kind": "pending",
        },
        "notes": [
            "Live golden-label comparison is outside the local harness scope.",
        ],
    }


def run_rule_checks(
    normalized_annotations: list[dict[str, Any]],
    image_index: dict[str, Any],
    class_map: dict[str, Any],
    threshold_policy: ThresholdPolicy,
) -> list[dict[str, Any]]:
    class_ids = {item["class_id"] for item in class_map.get("classes", [])}
    class_names = {item["class_name"] for item in class_map.get("classes", [])}
    image_lookup = {image["image_id"]: image for image in image_index.get("images", [])}
    issues: list[dict[str, Any]] = []
    min_box_pixels = float(threshold_policy.global_thresholds.get("min_box_pixels", 0))
    duplicate_iou = float(threshold_policy.global_thresholds.get("duplicate_iou", 1.0))

    annotations_by_image: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for annotation in normalized_annotations:
        annotations_by_image[annotation["image_id"]].append(annotation)

        if annotation["class_id"] not in class_ids or annotation["class_name"] not in class_names:
            issues.append(
                _issue(
                    annotation,
                    issue_type="invalid_class",
                    severity="error",
                    reason_code="RULE_INVALID_CLASS",
                    reason="annotation class is not present in class_map.json",
                    auto_action_hint="manual_review",
                    evidence={
                        "class_id": annotation["class_id"],
                        "class_name": annotation["class_name"],
                    },
                )
            )

        x_min, y_min, x_max, y_max = annotation["bbox_xyxy"]
        box_width = x_max - x_min
        box_height = y_max - y_min
        positive_box = box_width > 0 and box_height > 0
        if not positive_box:
            issues.append(
                _issue(
                    annotation,
                    issue_type="non_positive_box",
                    severity="error",
                    reason_code="RULE_NON_POSITIVE_BOX",
                    reason="bbox_xyxy must have positive width and height",
                    auto_action_hint="delete",
                    evidence={"bbox_xyxy": annotation["bbox_xyxy"]},
                )
            )

        if positive_box and (box_width < min_box_pixels or box_height < min_box_pixels):
            issues.append(
                _issue(
                    annotation,
                    issue_type="box_too_small",
                    severity="warning",
                    reason_code="RULE_BOX_TOO_SMALL",
                    reason="bbox dimensions are smaller than the configured min_box_pixels threshold",
                    auto_action_hint="manual_review",
                    evidence={
                        "box_width": round(box_width, 6),
                        "box_height": round(box_height, 6),
                        "min_box_pixels": min_box_pixels,
                    },
                )
            )

        if any(value < 0 or value > 1 for value in annotation["bbox_normalized_cxcywh"]):
            issues.append(
                _issue(
                    annotation,
                    issue_type="normalized_box_out_of_range",
                    severity="error",
                    reason_code="RULE_NORMALIZED_BOX_RANGE",
                    reason="normalized bbox values must remain inside the inclusive [0, 1] range",
                    auto_action_hint="manual_review",
                    evidence={"bbox_normalized_cxcywh": annotation["bbox_normalized_cxcywh"]},
                )
            )

        image = image_lookup.get(annotation["image_id"])
        if image is not None:
            if x_min < 0 or y_min < 0 or x_max > image["width"] or y_max > image["height"]:
                issues.append(
                    _issue(
                        annotation,
                        issue_type="bbox_out_of_bounds",
                        severity="error",
                        reason_code="RULE_BBOX_OUT_OF_BOUNDS",
                        reason="bbox_xyxy exceeds image bounds",
                        auto_action_hint="manual_review",
                        evidence={
                            "bbox_xyxy": annotation["bbox_xyxy"],
                            "image_width": image["width"],
                            "image_height": image["height"],
                        },
                    )
                )

        class_thresholds = threshold_policy.per_class.get(annotation["class_name"], {})
        aspect_ratio_max = class_thresholds.get("aspect_ratio_max")
        if positive_box and aspect_ratio_max is not None:
            aspect_ratio = max(box_width / box_height, box_height / box_width)
            if aspect_ratio > float(aspect_ratio_max):
                issues.append(
                    _issue(
                        annotation,
                        issue_type="aspect_ratio_exceeded",
                        severity="warning",
                        reason_code="RULE_ASPECT_RATIO_MAX",
                        reason="bbox aspect ratio exceeds the configured per-class limit",
                        auto_action_hint="refine",
                        evidence={
                            "aspect_ratio": round(aspect_ratio, 6),
                            "aspect_ratio_max": float(aspect_ratio_max),
                        },
                    )
                )

    for image_id, items in annotations_by_image.items():
        sorted_items = sorted(items, key=lambda item: item["ann_id"])
        for index, left in enumerate(sorted_items):
            for right in sorted_items[index + 1 :]:
                if left["class_id"] != right["class_id"]:
                    continue
                iou = _bbox_iou(left["bbox_xyxy"], right["bbox_xyxy"])
                if iou >= duplicate_iou:
                    issues.append(
                        {
                            "issue_id": f"{image_id}:duplicate:{left['ann_id']}:{right['ann_id']}",
                            "image_id": image_id,
                            "ann_id": left["ann_id"],
                            "related_ann_id": right["ann_id"],
                            "issue_type": "duplicate_box",
                            "severity": "warning",
                            "reason_code": "RULE_DUPLICATE_BOX",
                            "reason": "two annotations of the same class overlap above the configured duplicate_iou threshold",
                            "auto_action_hint": "manual_review",
                            "metric_kind": "measured",
                            "evidence": {
                                "duplicate_iou": round(iou, 6),
                                "duplicate_iou_threshold": duplicate_iou,
                            },
                        }
                    )

    return sorted(issues, key=lambda item: (item["image_id"], item["ann_id"], item["issue_type"], item.get("related_ann_id", "")))


def build_class_stats(
    normalized_annotations: list[dict[str, Any]],
    class_map: dict[str, Any],
    rule_issues: list[dict[str, Any]],
    threshold_policy: ThresholdPolicy,
) -> dict[str, Any]:
    issue_count_by_ann = defaultdict(int)
    for issue in rule_issues:
        issue_count_by_ann[issue["ann_id"]] += 1

    stats_rows = []
    for class_entry in sorted(class_map.get("classes", []), key=lambda item: item["class_id"]):
        class_annotations = [
            annotation
            for annotation in normalized_annotations
            if annotation["class_id"] == class_entry["class_id"]
        ]
        areas = [float(annotation["area"]) for annotation in class_annotations]
        image_ids = {annotation["image_id"] for annotation in class_annotations}
        stats_rows.append(
            {
                "class_id": class_entry["class_id"],
                "class_name": class_entry["class_name"],
                "annotation_count": len(class_annotations),
                "image_count": len(image_ids),
                "issue_count": sum(issue_count_by_ann[annotation["ann_id"]] for annotation in class_annotations),
                "area_min": round(min(areas), 6) if areas else None,
                "area_max": round(max(areas), 6) if areas else None,
                "area_mean": round(sum(areas) / len(areas), 6) if areas else None,
            }
        )
    return {
        "thresholds_version": threshold_policy.thresholds_version,
        "threshold_snapshot": threshold_policy.snapshot(),
        "total_classes": len(stats_rows),
        "total_annotations": len(normalized_annotations),
        "total_rule_issues": len(rule_issues),
        "classes": stats_rows,
    }


def run_rules_for_directory(
    run_dir: Path,
    *,
    thresholds_file: Path | None = None,
    golden_set_version: str = "golden_v1",
    selected_image_ids: Iterable[str] | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    threshold_policy = load_threshold_policy(thresholds_file)

    manifest = RunManifest(**run_manifest)
    manifest.thresholds_version = threshold_policy.thresholds_version
    ensure_run_directory_layout(run_dir, manifest)

    golden_set_manifest = build_golden_set_manifest(
        image_index,
        run_manifest=manifest.to_dict(),
        golden_set_version=golden_set_version,
        selected_image_ids=selected_image_ids,
    )
    rule_issues = run_rule_checks(
        normalized_annotations,
        image_index,
        class_map,
        threshold_policy,
    )
    golden_eval_report = build_golden_eval_report(
        golden_set_manifest,
        rule_issues=rule_issues,
    )
    class_stats = build_class_stats(
        normalized_annotations,
        class_map,
        rule_issues,
        threshold_policy,
    )

    write_run_artifact(run_dir, "golden_set_manifest", golden_set_manifest, overwrite=overwrite)
    write_run_artifact(run_dir, "golden_eval_report", golden_eval_report, overwrite=overwrite)
    write_run_artifact(run_dir, "rule_issues", rule_issues, overwrite=overwrite)
    write_run_artifact(run_dir, "class_stats", class_stats, overwrite=overwrite)
    write_run_artifact(run_dir, "run_manifest", manifest.to_dict(), overwrite=True)

    return {
        "golden_set_manifest": golden_set_manifest,
        "golden_eval_report": golden_eval_report,
        "rule_issues": rule_issues,
        "class_stats": class_stats,
    }


def _issue(
    annotation: dict[str, Any],
    *,
    issue_type: str,
    severity: str,
    reason_code: str,
    reason: str,
    auto_action_hint: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "issue_id": f"{annotation['ann_id']}:{issue_type}",
        "image_id": annotation["image_id"],
        "ann_id": annotation["ann_id"],
        "related_ann_id": None,
        "issue_type": issue_type,
        "severity": severity,
        "reason_code": reason_code,
        "reason": reason,
        "auto_action_hint": auto_action_hint,
        "metric_kind": "measured",
        "evidence": evidence,
    }


def _bbox_iou(left: list[float], right: list[float]) -> float:
    x_min = max(left[0], right[0])
    y_min = max(left[1], right[1])
    x_max = min(left[2], right[2])
    y_max = min(left[3], right[3])
    if x_max <= x_min or y_max <= y_min:
        return 0.0
    intersection = (x_max - x_min) * (y_max - y_min)
    left_area = (left[2] - left[0]) * (left[3] - left[1])
    right_area = (right[2] - right[0]) * (right[3] - right[1])
    union = left_area + right_area - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def _load_mapping_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        raise ValueError("config_path must be provided when payload is omitted")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        payload = json.loads(text)
    elif path.suffix.lower() in {".yaml", ".yml"}:
        payload = _parse_simple_yaml(text)
    else:
        raise ValueError(f"unsupported threshold config format: {path.suffix}")
    if not isinstance(payload, dict):
        raise ValueError("threshold config must deserialize to a mapping")
    return payload


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"unsupported YAML line: {raw_line}")
        key, value = stripped.split(":", 1)
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        key = key.strip()
        value = value.strip()
        if not value:
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
            continue
        parent[key] = _parse_yaml_scalar(value)
    return root


def _parse_yaml_scalar(value: str) -> Any:
    lowered = value.casefold()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _sorted_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    return {str(key): payload[key] for key in sorted(payload)}
