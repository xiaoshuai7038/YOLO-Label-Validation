from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifact_io import write_run_artifact, load_run_artifact
from .risk import load_defaults_config


REQUIRED_VLM_RESPONSE_FIELDS = (
    "decision",
    "class_ok",
    "box_ok",
    "new_class_name",
    "need_refine_box",
    "need_add_missing",
    "missing_candidates",
    "reason",
    "reason_code",
    "confidence",
)


def build_vlm_requests(
    review_candidates: list[dict[str, Any]],
    normalized_annotations: list[dict[str, Any]],
    image_index: dict[str, Any],
    class_map: dict[str, Any],
    risk_scores: list[dict[str, Any]],
    rule_issues: list[dict[str, Any]],
    *,
    model: str,
    decision_enum: list[str],
    prompt_version: str = "vlm_prompt_v1",
) -> list[dict[str, Any]]:
    annotation_lookup = {
        annotation["ann_id"]: annotation
        for annotation in normalized_annotations
    }
    image_lookup = {
        image["image_id"]: image
        for image in image_index.get("images", [])
    }
    risk_lookup = {
        row["ann_id"]: row
        for row in risk_scores
    }
    issues_by_ann: dict[str, list[dict[str, Any]]] = {}
    for issue in sorted(
        rule_issues,
        key=lambda item: (item["image_id"], item["ann_id"], item["issue_type"], item.get("related_ann_id") or ""),
    ):
        issues_by_ann.setdefault(issue["ann_id"], []).append(issue)

    requests: list[dict[str, Any]] = []
    for image_row in sorted(review_candidates, key=lambda item: item["image_id"]):
        image = image_lookup.get(image_row["image_id"])
        if image is None:
            raise ValueError(f"review candidate references unknown image_id: {image_row['image_id']}")
        for candidate in sorted(
            image_row["candidate_annotations"],
            key=lambda item: item["ann_id"],
        ):
            annotation = annotation_lookup.get(candidate["ann_id"])
            if annotation is None:
                raise ValueError(f"review candidate references unknown ann_id: {candidate['ann_id']}")
            risk_row = risk_lookup.get(annotation["ann_id"])
            if risk_row is None:
                raise ValueError(f"review candidate references ann_id without risk score: {annotation['ann_id']}")

            requests.append(
                {
                    "request_id": f"vlm:{annotation['image_id']}:{annotation['ann_id']}",
                    "image_id": annotation["image_id"],
                    "ann_id": annotation["ann_id"],
                    "model": model,
                    "prompt_version": prompt_version,
                    "allowed_decisions": decision_enum,
                    "image_reference": {
                        "file_name": image["file_name"],
                        "relative_path": image["relative_path"],
                        "width": image["width"],
                        "height": image["height"],
                    },
                    "annotation_context": {
                        "class_id": annotation["class_id"],
                        "class_name": annotation["class_name"],
                        "bbox_xyxy": annotation["bbox_xyxy"],
                        "bbox_normalized_cxcywh": annotation["bbox_normalized_cxcywh"],
                        "risk_score": risk_row["risk_score"],
                        "image_score": risk_row["image_score"],
                        "risk_tags": risk_row["risk_tags"],
                        "reason_codes": candidate["reason_codes"],
                        "rule_issues": [
                            {
                                "issue_type": issue["issue_type"],
                                "severity": issue["severity"],
                                "reason_code": issue["reason_code"],
                                "reason": issue["reason"],
                            }
                            for issue in issues_by_ann.get(annotation["ann_id"], [])
                        ],
                    },
                    "class_candidates": [
                        {
                            "class_id": class_entry["class_id"],
                            "class_name": class_entry["class_name"],
                        }
                        for class_entry in sorted(
                            class_map.get("classes", []),
                            key=lambda item: item["class_id"],
                        )
                    ],
                    "response_contract": {
                        "required_fields": list(REQUIRED_VLM_RESPONSE_FIELDS),
                        "decision_enum": decision_enum,
                        "missing_candidate_fields": [
                            "class_name",
                            "bbox_xyxy",
                            "confidence",
                            "reason",
                            "reason_code",
                        ],
                    },
                }
            )
    return requests


def parse_vlm_reviews(
    raw_responses: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    class_map: dict[str, Any],
    *,
    decision_enum: list[str],
) -> list[dict[str, Any]]:
    request_lookup = {
        request["request_id"]: request
        for request in requests
    }
    class_name_lookup = {
        class_entry["class_name"]: class_entry["class_id"]
        for class_entry in class_map.get("classes", [])
    }

    parsed_reviews: list[dict[str, Any]] = []
    for raw_response in sorted(raw_responses, key=lambda item: item["request_id"]):
        request_id = raw_response["request_id"]
        request = request_lookup.get(request_id)
        if request is None:
            raise ValueError(f"unknown VLM request_id: {request_id}")

        payload = _coerce_response_payload(raw_response)
        decision = _validated_choice(payload, "decision", decision_enum)
        reason = _validated_non_empty_string(payload, "reason")
        reason_code = _validated_non_empty_string(payload, "reason_code")
        confidence = _validated_probability(payload.get("confidence"), "confidence")
        new_class_name = payload.get("new_class_name")
        if new_class_name is not None:
            new_class_name = _validated_non_empty_string(payload, "new_class_name")
            if new_class_name not in class_name_lookup:
                raise ValueError(f"unknown new_class_name in VLM response: {new_class_name}")

        missing_candidates = _validated_missing_candidates(
            payload.get("missing_candidates"),
            class_name_lookup,
        )
        need_refine_box = _validated_bool(payload, "need_refine_box")
        need_add_missing = _validated_bool(payload, "need_add_missing")
        class_ok = _validated_bool(payload, "class_ok")
        box_ok = _validated_bool(payload, "box_ok")

        if decision == "relabel" and new_class_name is None:
            raise ValueError("VLM relabel response requires new_class_name")
        if decision == "add_missing" and not missing_candidates:
            raise ValueError("VLM add_missing response requires at least one missing candidate")
        if decision == "keep" and new_class_name not in {None, request["annotation_context"]["class_name"]}:
            raise ValueError("VLM keep response cannot change class_name")

        parsed_reviews.append(
            {
                "request_id": request_id,
                "image_id": request["image_id"],
                "ann_id": request["ann_id"],
                "decision": decision,
                "class_ok": class_ok,
                "box_ok": box_ok,
                "new_class_name": new_class_name,
                "need_refine_box": need_refine_box,
                "need_add_missing": need_add_missing,
                "missing_candidates": missing_candidates,
                "reason": reason,
                "reason_code": reason_code,
                "confidence": confidence,
                "metric_kind": "proxy",
            }
        )
    return parsed_reviews


def run_vlm_for_directory(
    run_dir: Path,
    *,
    responses_file: Path | None = None,
    defaults_file: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    defaults_config = load_defaults_config(defaults_file)
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    review_candidates = load_run_artifact(run_dir, "review_candidates")
    rule_issues = load_run_artifact(run_dir, "rule_issues")

    vlm_config = defaults_config.get("vlm", {})
    decision_enum = list(vlm_config.get("decision_enum", []))
    requests = build_vlm_requests(
        review_candidates,
        normalized_annotations,
        image_index,
        class_map,
        risk_scores,
        rule_issues,
        model=str(run_manifest.get("vlm_version") or vlm_config.get("model", "qwen2.5-vl")),
        decision_enum=decision_enum,
    )
    raw_responses = _load_external_records(responses_file) if responses_file is not None else []
    normalized_raw_responses = _normalize_raw_responses(raw_responses, requests)
    reviews = parse_vlm_reviews(
        normalized_raw_responses,
        requests,
        class_map,
        decision_enum=decision_enum,
    ) if normalized_raw_responses else []

    write_run_artifact(run_dir, "vlm_requests", requests, overwrite=overwrite)
    write_run_artifact(run_dir, "vlm_raw_responses", normalized_raw_responses, overwrite=overwrite)
    write_run_artifact(run_dir, "vlm_review", reviews, overwrite=overwrite)
    return {
        "vlm_requests": requests,
        "vlm_raw_responses": normalized_raw_responses,
        "vlm_review": reviews,
    }


def _coerce_response_payload(raw_response: dict[str, Any]) -> dict[str, Any]:
    if "response" in raw_response:
        response = raw_response["response"]
        if isinstance(response, dict):
            payload = response
        elif isinstance(response, str):
            try:
                payload = json.loads(response)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON VLM response for request {raw_response['request_id']}") from exc
        else:
            raise ValueError(f"unsupported response payload type for request {raw_response['request_id']}")
    elif "response_text" in raw_response:
        try:
            payload = json.loads(raw_response["response_text"])
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON VLM response for request {raw_response['request_id']}") from exc
    else:
        payload = {
            key: value
            for key, value in raw_response.items()
            if key not in {"request_id", "image_id", "ann_id"}
        }

    if not isinstance(payload, dict):
        raise ValueError(f"VLM response must deserialize to an object for request {raw_response['request_id']}")
    return payload


def _load_external_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        records = [json.loads(line) for line in text.splitlines()]
    else:
        payload = json.loads(text)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict) and isinstance(payload.get("responses"), list):
            records = payload["responses"]
        else:
            records = [payload]
    if not all(isinstance(item, dict) for item in records):
        raise ValueError(f"response file must contain object records: {path}")
    return [dict(item) for item in records]


def _normalize_raw_responses(
    raw_responses: list[dict[str, Any]],
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    request_lookup = {
        request["request_id"]: request
        for request in requests
    }
    single_request_id = requests[0]["request_id"] if len(requests) == 1 else None

    normalized_records: list[dict[str, Any]] = []
    for raw_response in raw_responses:
        request_id = raw_response.get("request_id")
        if request_id is None:
            if single_request_id is None:
                raise ValueError("request_id is required when multiple VLM requests exist")
            request_id = single_request_id
        request = request_lookup.get(str(request_id))
        if request is None:
            raise ValueError(f"unknown VLM request_id in raw response: {request_id}")

        record: dict[str, Any] = {
            "request_id": request["request_id"],
            "image_id": request["image_id"],
            "ann_id": request["ann_id"],
        }
        if "response" in raw_response:
            record["response"] = raw_response["response"]
        elif "response_text" in raw_response:
            record["response_text"] = raw_response["response_text"]
        else:
            record["response"] = {
                key: value
                for key, value in raw_response.items()
                if key != "request_id"
            }
        normalized_records.append(record)
    return normalized_records


def _validated_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"VLM response field {key} must be boolean")
    return value


def _validated_choice(
    payload: dict[str, Any],
    key: str,
    valid_choices: list[str],
) -> str:
    value = _validated_non_empty_string(payload, key)
    if value not in valid_choices:
        raise ValueError(f"VLM response field {key} is outside the allowed enum: {value}")
    return value


def _validated_non_empty_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"VLM response field {key} must be a non-empty string")
    return value.strip()


def _validated_probability(value: Any, key: str) -> float:
    try:
        probability = round(float(value), 6)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"VLM response field {key} must be numeric") from exc
    if probability < 0.0 or probability > 1.0:
        raise ValueError(f"VLM response field {key} must remain inside [0, 1]")
    return probability


def _validated_missing_candidates(
    value: Any,
    class_name_lookup: dict[str, int],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("VLM response field missing_candidates must be an array")

    candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(value):
        if not isinstance(candidate, dict):
            raise ValueError(f"VLM missing candidate {index} must be an object")
        class_name = _validated_non_empty_string(candidate, "class_name")
        if class_name not in class_name_lookup:
            raise ValueError(f"unknown missing candidate class_name: {class_name}")
        bbox_xyxy = candidate.get("bbox_xyxy")
        if (
            not isinstance(bbox_xyxy, list)
            or len(bbox_xyxy) != 4
            or not all(isinstance(item, (int, float)) for item in bbox_xyxy)
        ):
            raise ValueError("VLM missing candidate bbox_xyxy must be a 4-item numeric array")

        candidates.append(
            {
                "class_id": class_name_lookup[class_name],
                "class_name": class_name,
                "bbox_xyxy": [round(float(item), 6) for item in bbox_xyxy],
                "confidence": _validated_probability(candidate.get("confidence"), "confidence"),
                "reason": _validated_non_empty_string(candidate, "reason"),
                "reason_code": _validated_non_empty_string(candidate, "reason_code"),
            }
        )
    return candidates
