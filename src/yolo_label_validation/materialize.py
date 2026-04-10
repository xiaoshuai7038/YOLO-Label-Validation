from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from .artifact_io import load_run_artifact, write_run_artifact


def materialize_dataset_view(
    normalized_annotations: list[dict[str, Any]],
    image_index: dict[str, Any],
    class_map: dict[str, Any],
    patches: list[dict[str, Any]],
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(f"refusing to overwrite existing materialized dataset without --overwrite: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_lookup = {
        image["image_id"]: dict(image)
        for image in image_index.get("images", [])
    }
    class_name_lookup = {
        class_entry["class_name"]: class_entry["class_id"]
        for class_entry in class_map.get("classes", [])
    }
    materialized_annotations = {
        annotation["ann_id"]: _copied_annotation(annotation)
        for annotation in normalized_annotations
    }

    for patch in sorted(patches, key=lambda item: (item["image_id"], item["timestamp"], item["patch_id"])):
        if patch["action"] == "relabel":
            annotation = materialized_annotations[patch["ann_id"]]
            annotation["class_name"] = patch["new_class_name"]
            annotation["class_id"] = class_name_lookup[patch["new_class_name"]]
        elif patch["action"] == "refine":
            annotation = materialized_annotations[patch["ann_id"]]
            image = image_lookup[annotation["image_id"]]
            _apply_bbox(annotation, patch["new_bbox_xyxy"], image)
        elif patch["action"] == "delete":
            materialized_annotations.pop(patch["ann_id"], None)
        elif patch["action"] == "add":
            image = image_lookup[patch["image_id"]]
            ann_id = f"materialized:{patch['patch_id']}"
            materialized_annotations[ann_id] = _new_annotation_from_patch(
                ann_id,
                patch,
                image,
                class_name_lookup,
            )

    ordered_annotations = sorted(
        materialized_annotations.values(),
        key=lambda item: (item["image_id"], item["ann_id"]),
    )
    counts_by_image = Counter(annotation["image_id"] for annotation in ordered_annotations)
    materialized_images = []
    for image in sorted(image_lookup.values(), key=lambda item: item["image_id"]):
        image["annotation_count"] = counts_by_image.get(image["image_id"], 0)
        materialized_images.append(image)

    _write_jsonl(output_dir / "normalized_annotations.jsonl", ordered_annotations)
    _write_json(
        output_dir / "image_index.json",
        {
            "dataset_version": image_index["dataset_version"],
            "images": materialized_images,
        },
    )
    _write_json(output_dir / "class_map.json", class_map)
    _write_json(
        output_dir / "materialization_manifest.json",
        {
            "annotation_count": len(ordered_annotations),
            "patch_count": len(patches),
            "source_overwrite": False,
        },
    )
    return {
        "output_dir": str(output_dir),
        "annotation_count": len(ordered_annotations),
        "patch_count": len(patches),
    }


def build_run_summary(
    run_manifest: dict[str, Any],
    normalized_annotations: list[dict[str, Any]],
    rule_issues: list[dict[str, Any]],
    risk_scores: list[dict[str, Any]],
    decision_results: list[dict[str, Any]],
    patches: list[dict[str, Any]],
    manual_review_queue: list[dict[str, Any]],
    refine_results: list[dict[str, Any]],
    missing_results: list[dict[str, Any]],
    *,
    materialized_output_dir: str,
) -> dict[str, Any]:
    decision_counts = Counter(decision["action"] for decision in decision_results)
    patch_counts = Counter(patch["action"] for patch in patches)
    manual_review_coverage = round(
        len(manual_review_queue) / max(len(decision_results), 1),
        6,
    )
    traceable_patch_count = sum(
        1
        for patch in patches
        if patch["reason"] and patch["reason_code"] and patch["review_source"]
    )
    patch_traceability_rate = round(
        traceable_patch_count / max(len(patches), 1),
        6,
    ) if patches else 1.0

    return {
        "run_id": run_manifest["run_id"],
        "materialized_output_dir": materialized_output_dir,
        "record_counts": {
            "normalized_annotations": len(normalized_annotations),
            "rule_issues": len(rule_issues),
            "risk_scores": len(risk_scores),
            "decision_results": len(decision_results),
            "refine_results": len(refine_results),
            "missing_results": len(missing_results),
            "patches": len(patches),
            "manual_review_queue": len(manual_review_queue),
        },
        "decision_counts": {
            key: decision_counts.get(key, 0)
            for key in ("keep", "relabel", "refine", "delete", "add", "manual_review")
        },
        "patch_counts": {
            key: patch_counts.get(key, 0)
            for key in ("relabel", "refine", "delete", "add")
        },
        "metrics": {
            "manual_review_coverage": {
                "value": manual_review_coverage,
                "metric_kind": "measured",
            },
            "patch_traceability_rate": {
                "value": patch_traceability_rate,
                "metric_kind": "measured",
            },
            "auto_pass_sample_correctness": {
                "value": None,
                "metric_kind": "pending",
            },
        },
        "source_protection": {
            "allow_source_overwrite": False,
            "metric_kind": "measured",
        },
    }


def build_metrics_dashboard_source(
    run_manifest: dict[str, Any],
    run_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": run_manifest["run_id"],
        "dataset_version": run_manifest["dataset_version"],
        "class_map_version": run_manifest["class_map_version"],
        "normalization_version": run_manifest["normalization_version"],
        "rules_version": run_manifest["rules_version"],
        "thresholds_version": run_manifest["thresholds_version"],
        "vlm_version": run_manifest["vlm_version"],
        "secondary_detector_version": run_manifest["secondary_detector_version"],
        "record_counts": run_summary["record_counts"],
        "decision_counts": run_summary["decision_counts"],
        "patch_counts": run_summary["patch_counts"],
        "manual_review_coverage": run_summary["metrics"]["manual_review_coverage"],
        "patch_traceability_rate": run_summary["metrics"]["patch_traceability_rate"],
        "auto_pass_sample_correctness": run_summary["metrics"]["auto_pass_sample_correctness"],
    }


def run_materialize_for_directory(
    run_dir: Path,
    *,
    output_subdir: str = "materialized_dataset",
    overwrite: bool = False,
) -> dict[str, Any]:
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    rule_issues = load_run_artifact(run_dir, "rule_issues")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    decision_results = load_run_artifact(run_dir, "decision_results")
    refine_results = load_run_artifact(run_dir, "refine_results")
    missing_results = load_run_artifact(run_dir, "missing_results")
    patches = load_run_artifact(run_dir, "patches")
    manual_review_queue = load_run_artifact(run_dir, "manual_review_queue")

    materialized = materialize_dataset_view(
        normalized_annotations,
        image_index,
        class_map,
        patches,
        run_dir / output_subdir,
        overwrite=overwrite,
    )
    run_summary = build_run_summary(
        run_manifest,
        normalized_annotations,
        rule_issues,
        risk_scores,
        decision_results,
        patches,
        manual_review_queue,
        refine_results,
        missing_results,
        materialized_output_dir=materialized["output_dir"],
    )
    metrics_dashboard_source = build_metrics_dashboard_source(run_manifest, run_summary)

    write_run_artifact(run_dir, "run_summary", run_summary, overwrite=overwrite)
    write_run_artifact(
        run_dir,
        "metrics_dashboard_source",
        metrics_dashboard_source,
        overwrite=overwrite,
    )
    return {
        "materialized": materialized,
        "run_summary": run_summary,
        "metrics_dashboard_source": metrics_dashboard_source,
    }


def _copied_annotation(annotation: dict[str, Any]) -> dict[str, Any]:
    copied = dict(annotation)
    copied["bbox_xyxy"] = list(annotation["bbox_xyxy"])
    copied["bbox_xywh"] = list(annotation["bbox_xywh"])
    copied["bbox_normalized_cxcywh"] = list(annotation["bbox_normalized_cxcywh"])
    copied["lineage"] = dict(annotation["lineage"])
    return copied


def _apply_bbox(
    annotation: dict[str, Any],
    bbox_xyxy: list[float] | None,
    image: dict[str, Any],
) -> None:
    if bbox_xyxy is None:
        raise ValueError("refine patches require new_bbox_xyxy")
    x_min, y_min, x_max, y_max = [round(float(item), 6) for item in bbox_xyxy]
    width = round(x_max - x_min, 6)
    height = round(y_max - y_min, 6)
    annotation["bbox_xyxy"] = [x_min, y_min, x_max, y_max]
    annotation["bbox_xywh"] = [x_min, y_min, width, height]
    annotation["bbox_normalized_cxcywh"] = [
        round(((x_min + x_max) / 2.0) / float(image["width"]), 6),
        round(((y_min + y_max) / 2.0) / float(image["height"]), 6),
        round(width / float(image["width"]), 6),
        round(height / float(image["height"]), 6),
    ]
    annotation["area"] = round(width * height, 6)


def _new_annotation_from_patch(
    ann_id: str,
    patch: dict[str, Any],
    image: dict[str, Any],
    class_name_lookup: dict[str, int],
) -> dict[str, Any]:
    bbox_xyxy = [round(float(item), 6) for item in patch["new_bbox_xyxy"]]
    x_min, y_min, x_max, y_max = bbox_xyxy
    width = round(x_max - x_min, 6)
    height = round(y_max - y_min, 6)
    return {
        "ann_id": ann_id,
        "image_id": patch["image_id"],
        "source_id": "materialized",
        "source_format": "coco_json",
        "class_id": class_name_lookup[patch["new_class_name"]],
        "class_name": patch["new_class_name"],
        "bbox_xyxy": bbox_xyxy,
        "bbox_xywh": [x_min, y_min, width, height],
        "bbox_normalized_cxcywh": [
            round(((x_min + x_max) / 2.0) / float(image["width"]), 6),
            round(((y_min + y_max) / 2.0) / float(image["height"]), 6),
            round(width / float(image["width"]), 6),
            round(height / float(image["height"]), 6),
        ],
        "area": round(width * height, 6),
        "iscrowd": False,
        "lineage": {
            "source_id": "materialized",
            "source_format": "patch",
            "source_annotation_ref": patch["patch_id"],
            "source_annotation_id": None,
            "source_image_id": image["source_image_id"],
            "source_image_path": image["relative_path"],
            "source_label_path": None,
            "source_category_id": None,
            "source_category_name": patch["new_class_name"],
            "raw_annotation": {
                "patch_id": patch["patch_id"],
                "reason_code": patch["reason_code"],
            },
        },
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True)
        for record in records
    ]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")
