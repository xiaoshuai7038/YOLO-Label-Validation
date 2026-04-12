from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .artifact_io import load_run_artifact, write_run_artifact
from .rules import ThresholdPolicy, load_threshold_policy
from .runtime_config import load_runtime_config, resolve_runtime_path, runtime_config_reference


DetectorRunner = Callable[[Path, dict[str, Any], dict[str, dict[str, Any]]], list[dict[str, Any]]]


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
    runtime_config_file: Path | None = None,
    runtime_config_payload: dict[str, Any] | None = None,
    detector_runner: DetectorRunner | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    threshold_policy = load_threshold_policy(thresholds_file)
    runtime_config = (
        load_runtime_config(runtime_config_file, payload=runtime_config_payload)
        if runtime_config_file is not None or runtime_config_payload is not None
        else None
    )
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    vlm_review = load_run_artifact(run_dir, "vlm_review")

    if runtime_config is not None and runtime_config["detector"]["mode"] == "live":
        detections_by_image = _collect_live_detector_predictions(
            image_index,
            class_map,
            vlm_review,
            run_manifest=run_manifest,
            runtime_config=runtime_config,
            runtime_config_file=runtime_config_file,
            detector_runner=detector_runner,
        )
        refine_results = build_live_refine_results(
            normalized_annotations,
            image_index,
            vlm_review,
            detections_by_image=detections_by_image,
            detector_config=runtime_config["detector"],
        )
        missing_results = build_live_missing_results(
            vlm_review,
            image_index,
            detections_by_image=detections_by_image,
            detector_config=runtime_config["detector"],
        )
        active_mode = "live"
    else:
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
        active_mode = runtime_config["detector"]["mode"] if runtime_config is not None else "proxy"

    if runtime_config is not None:
        _write_detector_runtime_context(
            run_dir,
            run_manifest,
            runtime_config,
            runtime_config_file=runtime_config_file,
            active_mode=active_mode,
        )

    write_run_artifact(run_dir, "refine_results", refine_results, overwrite=overwrite)
    write_run_artifact(run_dir, "missing_results", missing_results, overwrite=overwrite)
    return {
        "refine_results": refine_results,
        "missing_results": missing_results,
    }


def build_live_refine_results(
    normalized_annotations: list[dict[str, Any]],
    image_index: dict[str, Any],
    vlm_review: list[dict[str, Any]],
    *,
    detections_by_image: dict[str, list[dict[str, Any]]],
    detector_config: dict[str, Any],
) -> list[dict[str, Any]]:
    annotation_lookup = {
        annotation["ann_id"]: annotation
        for annotation in normalized_annotations
    }
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }
    min_iou = float(detector_config["refine_match_iou"])

    results: list[dict[str, Any]] = []
    for review in sorted(vlm_review, key=lambda item: (item["image_id"], item["ann_id"])):
        if review["decision"] != "refine" and not review["need_refine_box"]:
            continue
        annotation = annotation_lookup.get(review["ann_id"])
        image = image_lookup.get(review["image_id"])
        if annotation is None or image is None:
            raise ValueError(f"cannot build live refine result for missing annotation/image: {review['ann_id']}")

        match = _best_detection_match(
            detections_by_image.get(review["image_id"], []),
            target_class_name=annotation["class_name"],
            target_bbox_xyxy=[float(item) for item in annotation["bbox_xyxy"]],
            min_iou=min_iou,
        )
        if match is None:
            continue

        original_bbox = [float(item) for item in annotation["bbox_xyxy"]]
        proposed_bbox = _clamp_bbox(
            [float(item) for item in match["bbox_xyxy"]],
            width=float(image["width"]),
            height=float(image["height"]),
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
                "detector_confidence": round(float(match["confidence"]), 6),
                "decision_hint": "refine",
                "reason": "live detector matched the existing annotation and supplied a measured geometry proposal",
                "reason_code": "DETECTOR_REFINE_LIVE",
                "metric_kind": "measured",
            }
        )
    return results


def build_live_missing_results(
    vlm_review: list[dict[str, Any]],
    image_index: dict[str, Any],
    *,
    detections_by_image: dict[str, list[dict[str, Any]]],
    detector_config: dict[str, Any],
) -> list[dict[str, Any]]:
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }
    min_iou = float(detector_config["missing_match_iou"])

    results: list[dict[str, Any]] = []
    for review in sorted(vlm_review, key=lambda item: (item["image_id"], item["ann_id"])):
        if review["decision"] != "add_missing" and not review["need_add_missing"]:
            continue
        image = image_lookup.get(review["image_id"])
        if image is None:
            raise ValueError(f"cannot build live missing result for unknown image_id: {review['image_id']}")

        used_detection_ids: set[str] = set()
        detections = detections_by_image.get(review["image_id"], [])
        for index, candidate in enumerate(review["missing_candidates"], start=1):
            candidate_bbox = [float(item) for item in candidate["bbox_xyxy"]]
            match = _best_detection_match(
                detections,
                target_class_name=candidate["class_name"],
                target_bbox_xyxy=candidate_bbox,
                min_iou=min_iou,
                excluded_detection_ids=used_detection_ids,
            )
            if match is not None:
                used_detection_ids.add(match["detection_id"])
                results.append(
                    {
                        "missing_id": f"missing:{review['ann_id']}:{index}",
                        "image_id": review["image_id"],
                        "source_ann_id": review["ann_id"],
                        "class_id": candidate["class_id"],
                        "class_name": candidate["class_name"],
                        "proposed_bbox_xyxy": _clamp_bbox(
                            [float(item) for item in match["bbox_xyxy"]],
                            width=float(image["width"]),
                            height=float(image["height"]),
                        ),
                        "detector_confidence": round(float(match["confidence"]), 6),
                        "decision_hint": "add",
                        "reason": "live detector confirmed the VLM missing-object candidate",
                        "reason_code": "DETECTOR_MISSING_CONFIRMED",
                        "metric_kind": "measured",
                    }
                )
            else:
                results.append(
                    {
                        "missing_id": f"missing:{review['ann_id']}:{index}",
                        "image_id": review["image_id"],
                        "source_ann_id": review["ann_id"],
                        "class_id": candidate["class_id"],
                        "class_name": candidate["class_name"],
                        "proposed_bbox_xyxy": _clamp_bbox(
                            candidate_bbox,
                            width=float(image["width"]),
                            height=float(image["height"]),
                        ),
                        "detector_confidence": 0.0,
                        "decision_hint": "add",
                        "reason": "VLM flagged a missing object but the live detector did not confirm it automatically",
                        "reason_code": "DETECTOR_MISSING_UNCONFIRMED",
                        "metric_kind": "pending",
                    }
                )
    return results


def _collect_live_detector_predictions(
    image_index: dict[str, Any],
    class_map: dict[str, Any],
    vlm_review: list[dict[str, Any]],
    *,
    run_manifest: dict[str, Any],
    runtime_config: dict[str, Any],
    runtime_config_file: Path | None,
    detector_runner: DetectorRunner | None,
) -> dict[str, list[dict[str, Any]]]:
    detector_settings = dict(runtime_config["detector"])
    weights_path = resolve_runtime_path(
        detector_settings.get("weights_path"),
        config_path=runtime_config_file,
    )
    if weights_path is None:
        raise ValueError("live detector requires detector.weights_path in runtime config")
    if not weights_path.exists():
        raise FileNotFoundError(f"live detector weights do not exist: {weights_path}")
    detector_settings["weights_path"] = str(weights_path)

    class_by_name = {
        class_entry["class_name"].casefold(): {
            "class_id": class_entry["class_id"],
            "class_name": class_entry["class_name"],
        }
        for class_entry in class_map.get("classes", [])
    }
    class_by_id = {
        class_entry["class_id"]: class_entry["class_name"]
        for class_entry in class_map.get("classes", [])
    }
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }
    runner = detector_runner or _build_ultralytics_detector_runner(detector_settings)

    relevant_image_ids = sorted(
        {
            review["image_id"]
            for review in vlm_review
            if review["decision"] in {"refine", "add_missing"} or review["need_refine_box"] or review["need_add_missing"]
        }
    )
    detections_by_image: dict[str, list[dict[str, Any]]] = {}
    for image_id in relevant_image_ids:
        image = image_lookup.get(image_id)
        if image is None:
            raise ValueError(f"live detector review references unknown image_id: {image_id}")
        image_path = _resolve_image_path(run_manifest, image_id, image["relative_path"])
        raw_rows = runner(image_path, detector_settings, class_by_name)
        detections_by_image[image_id] = _normalize_detector_rows(
            raw_rows,
            image=image,
            class_by_name=class_by_name,
            class_by_id=class_by_id,
        )
    return detections_by_image


def _build_ultralytics_detector_runner(detector_settings: dict[str, Any]) -> DetectorRunner:
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - depends on optional runtime extra
        raise RuntimeError(
            "live detector mode requires the optional runtime dependency. Install with `pip install -e .[runtime]`."
        ) from exc

    model = YOLO(detector_settings["weights_path"])

    def _runner(
        image_path: Path,
        settings: dict[str, Any],
        _: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        predictions = model.predict(
            source=str(image_path),
            conf=float(settings["confidence_threshold"]),
            iou=float(settings["iou_threshold"]),
            device=settings["device"],
            max_det=int(settings["max_det"]),
            verbose=False,
        )
        rows: list[dict[str, Any]] = []
        for prediction in predictions:
            boxes = getattr(prediction, "boxes", None)
            if boxes is None:
                continue
            names = getattr(prediction, "names", {})
            xyxy_rows = _tensor_rows_to_list(getattr(boxes, "xyxy", []))
            conf_rows = _tensor_rows_to_list(getattr(boxes, "conf", []))
            cls_rows = _tensor_rows_to_list(getattr(boxes, "cls", []))
            for bbox_xyxy, confidence, class_index in zip(xyxy_rows, conf_rows, cls_rows):
                rows.append(
                    {
                        "class_name": _class_name_from_prediction(names, class_index),
                        "bbox_xyxy": bbox_xyxy,
                        "confidence": confidence,
                    }
                )
        return rows

    return _runner


def _tensor_rows_to_list(value: Any) -> list[Any]:
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        payload = value.tolist()
    else:
        payload = list(value)
    if isinstance(payload, list):
        return payload
    return [payload]


def _class_name_from_prediction(names: Any, class_index: Any) -> str:
    parsed_index = int(class_index)
    if isinstance(names, dict):
        value = names.get(parsed_index, str(parsed_index))
    elif isinstance(names, list) and parsed_index < len(names):
        value = names[parsed_index]
    else:
        value = str(parsed_index)
    return str(value)


def _normalize_detector_rows(
    raw_rows: list[dict[str, Any]],
    *,
    image: dict[str, Any],
    class_by_name: dict[str, dict[str, Any]],
    class_by_id: dict[int, str],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(raw_rows, start=1):
        if not isinstance(row, dict):
            raise ValueError("detector runner must return object rows")
        class_name = row.get("class_name")
        class_id = row.get("class_id")
        canonical: dict[str, Any] | None = None
        if isinstance(class_name, str):
            canonical = class_by_name.get(class_name.casefold())
        elif isinstance(class_id, int) and class_id in class_by_id:
            canonical_name = class_by_id[class_id]
            canonical = class_by_name.get(canonical_name.casefold())
        if canonical is None:
            continue

        bbox_xyxy = row.get("bbox_xyxy")
        if (
            not isinstance(bbox_xyxy, list)
            or len(bbox_xyxy) != 4
            or not all(isinstance(item, (int, float)) for item in bbox_xyxy)
        ):
            raise ValueError("detector bbox_xyxy must be a 4-item numeric array")

        confidence = row.get("confidence", row.get("detector_confidence"))
        try:
            parsed_confidence = float(confidence)
        except (TypeError, ValueError) as exc:
            raise ValueError("detector confidence must be numeric") from exc
        if parsed_confidence < 0.0 or parsed_confidence > 1.0:
            raise ValueError("detector confidence must remain inside [0, 1]")

        normalized.append(
            {
                "detection_id": f"detection:{image['image_id']}:{index}",
                "class_id": canonical["class_id"],
                "class_name": canonical["class_name"],
                "bbox_xyxy": _clamp_bbox(
                    [float(item) for item in bbox_xyxy],
                    width=float(image["width"]),
                    height=float(image["height"]),
                ),
                "confidence": round(parsed_confidence, 6),
            }
        )
    return normalized


def _resolve_image_path(
    run_manifest: dict[str, Any],
    image_id: str,
    relative_path: str,
) -> Path:
    source_id = image_id.split(":", 1)[0]
    for source in run_manifest.get("input_sources", []):
        if source.get("source_id") != source_id:
            continue
        images_dir = source.get("images_dir")
        if not images_dir:
            raise ValueError(f"input source {source_id} does not expose images_dir for live detector")
        image_path = Path(images_dir) / Path(relative_path)
        if image_path.exists():
            return image_path
        raise ValueError(f"live detector image path does not exist: {image_path}")
    raise ValueError(f"cannot resolve live detector image path for source_id {source_id}")


def _best_detection_match(
    detections: list[dict[str, Any]],
    *,
    target_class_name: str,
    target_bbox_xyxy: list[float],
    min_iou: float,
    excluded_detection_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    best_match: dict[str, Any] | None = None
    best_score: tuple[float, float] | None = None
    for detection in detections:
        if detection["class_name"] != target_class_name:
            continue
        if excluded_detection_ids is not None and detection["detection_id"] in excluded_detection_ids:
            continue
        iou = _bbox_iou(target_bbox_xyxy, detection["bbox_xyxy"])
        if iou < min_iou:
            continue
        score = (iou, float(detection["confidence"]))
        if best_score is None or score > best_score:
            best_score = score
            best_match = detection
    return best_match


def _write_detector_runtime_context(
    run_dir: Path,
    run_manifest: dict[str, Any],
    runtime_config: dict[str, Any],
    *,
    runtime_config_file: Path | None,
    active_mode: str,
) -> None:
    runtime_context = dict(run_manifest.get("runtime_context") or {})
    runtime_context.update(
        runtime_config_reference(
            runtime_config,
            config_path=runtime_config_file,
        )
    )
    detector_config = runtime_config["detector"]
    weights_path = resolve_runtime_path(detector_config.get("weights_path"), config_path=runtime_config_file)
    runtime_context["detector"] = {
        "mode": active_mode,
        "family": detector_config["family"],
        "weights_path": str(weights_path) if weights_path is not None else None,
        "device": detector_config["device"],
        "confidence_threshold": detector_config["confidence_threshold"],
        "iou_threshold": detector_config["iou_threshold"],
        "max_det": detector_config["max_det"],
    }
    run_manifest["runtime_context"] = runtime_context
    run_manifest["secondary_detector_version"] = (
        f"{detector_config['family']}:{weights_path.name}"
        if weights_path is not None
        else detector_config["family"]
    )
    write_run_artifact(run_dir, "run_manifest", run_manifest, overwrite=True)


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
