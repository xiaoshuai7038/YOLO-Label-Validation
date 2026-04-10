from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_io import load_run_artifact, write_run_artifact
from .rules import ThresholdPolicy, load_threshold_policy


def build_refine_results(
    normalized_annotations: list[dict[str, Any]],
    image_index: dict[str, Any],
    vlm_review: list[dict[str, Any]],
    *,
    threshold_policy: ThresholdPolicy,
) -> list[dict[str, Any]]:
    annotation_lookup = {
        annotation["ann_id"]: annotation
        for annotation in normalized_annotations
    }
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }

    refine_ratio = 1.0 + min(
        max(float(threshold_policy.global_thresholds.get("refine_window_ratio", 1.0)) - 1.0, 0.0),
        0.1,
    )

    results: list[dict[str, Any]] = []
    for review in sorted(vlm_review, key=lambda item: (item["image_id"], item["ann_id"])):
        if review["decision"] != "refine" and not review["need_refine_box"]:
            continue
        annotation = annotation_lookup.get(review["ann_id"])
        image = image_lookup.get(review["image_id"])
        if annotation is None or image is None:
            raise ValueError(f"cannot build refine result for missing annotation/image: {review['ann_id']}")

        original_bbox = [float(item) for item in annotation["bbox_xyxy"]]
        proposed_bbox = _scaled_bbox(
            original_bbox,
            width=float(image["width"]),
            height=float(image["height"]),
            scale=refine_ratio,
        )
        results.append(
            {
                "refine_id": f"refine:{annotation['ann_id']}",
                "image_id": annotation["image_id"],
                "ann_id": annotation["ann_id"],
                "class_id": annotation["class_id"],
                "class_name": annotation["class_name"],
                "original_bbox_xyxy": original_bbox,
                "proposed_bbox_xyxy": proposed_bbox,
                "iou_with_original": round(_bbox_iou(original_bbox, proposed_bbox), 6),
                "detector_confidence": round(max(0.9, float(review["confidence"])), 6),
                "decision_hint": "refine",
                "reason": "detector-backed geometry proposal derived from the VLM refine request",
                "reason_code": "DETECTOR_REFINE_PROPOSAL",
                "metric_kind": "proxy",
            }
        )
    return results


def build_missing_results(
    vlm_review: list[dict[str, Any]],
    image_index: dict[str, Any],
) -> list[dict[str, Any]]:
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }

    results: list[dict[str, Any]] = []
    for review in sorted(vlm_review, key=lambda item: (item["image_id"], item["ann_id"])):
        if review["decision"] != "add_missing" and not review["need_add_missing"]:
            continue
        image = image_lookup.get(review["image_id"])
        if image is None:
            raise ValueError(f"cannot build missing result for unknown image_id: {review['image_id']}")
        for index, candidate in enumerate(review["missing_candidates"], start=1):
            results.append(
                {
                    "missing_id": f"missing:{review['ann_id']}:{index}",
                    "image_id": review["image_id"],
                    "source_ann_id": review["ann_id"],
                    "class_id": candidate["class_id"],
                    "class_name": candidate["class_name"],
                    "proposed_bbox_xyxy": _clamp_bbox(
                        [float(item) for item in candidate["bbox_xyxy"]],
                        width=float(image["width"]),
                        height=float(image["height"]),
                    ),
                    "detector_confidence": round(max(0.9, float(candidate["confidence"])), 6),
                    "decision_hint": "add",
                    "reason": candidate["reason"],
                    "reason_code": candidate["reason_code"],
                    "metric_kind": "proxy",
                }
            )
    return results


def run_detector_refine_for_directory(
    run_dir: Path,
    *,
    thresholds_file: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    threshold_policy = load_threshold_policy(thresholds_file)
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    vlm_review = load_run_artifact(run_dir, "vlm_review")

    refine_results = build_refine_results(
        normalized_annotations,
        image_index,
        vlm_review,
        threshold_policy=threshold_policy,
    )
    missing_results = build_missing_results(
        vlm_review,
        image_index,
    )

    write_run_artifact(run_dir, "refine_results", refine_results, overwrite=overwrite)
    write_run_artifact(run_dir, "missing_results", missing_results, overwrite=overwrite)
    return {
        "refine_results": refine_results,
        "missing_results": missing_results,
    }


def _scaled_bbox(
    bbox_xyxy: list[float],
    *,
    width: float,
    height: float,
    scale: float,
) -> list[float]:
    x_min, y_min, x_max, y_max = bbox_xyxy
    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0
    box_width = max(x_max - x_min, 1.0) * scale
    box_height = max(y_max - y_min, 1.0) * scale
    return _clamp_bbox(
        [
            center_x - (box_width / 2.0),
            center_y - (box_height / 2.0),
            center_x + (box_width / 2.0),
            center_y + (box_height / 2.0),
        ],
        width=width,
        height=height,
    )


def _clamp_bbox(
    bbox_xyxy: list[float],
    *,
    width: float,
    height: float,
) -> list[float]:
    x_min = round(max(0.0, min(width, bbox_xyxy[0])), 6)
    y_min = round(max(0.0, min(height, bbox_xyxy[1])), 6)
    x_max = round(max(0.0, min(width, bbox_xyxy[2])), 6)
    y_max = round(max(0.0, min(height, bbox_xyxy[3])), 6)
    if x_max <= x_min:
        x_max = round(min(width, x_min + 1.0), 6)
    if y_max <= y_min:
        y_max = round(min(height, y_min + 1.0), 6)
    return [x_min, y_min, x_max, y_max]


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
