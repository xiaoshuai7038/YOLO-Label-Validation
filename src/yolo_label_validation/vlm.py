from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Any, Callable
from urllib import error, request as urllib_request

from .artifact_io import load_run_artifact, write_run_artifact
from .risk import load_defaults_config
from .runtime_config import (
    load_runtime_config,
    resolve_required_env,
    runtime_config_reference,
)


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
VALID_METRIC_KINDS = {"measured", "proxy", "pending"}
VLMTransport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


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
                "metric_kind": _validated_metric_kind(raw_response.get("metric_kind")),
            }
        )
    return parsed_reviews


def run_vlm_for_directory(
    run_dir: Path,
    *,
    responses_file: Path | None = None,
    defaults_file: Path | None = None,
    runtime_config_file: Path | None = None,
    runtime_config_payload: dict[str, Any] | None = None,
    transport: VLMTransport | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    defaults_config = load_defaults_config(defaults_file)
    runtime_config = (
        load_runtime_config(runtime_config_file, payload=runtime_config_payload)
        if runtime_config_file is not None or runtime_config_payload is not None
        else None
    )
    run_manifest = load_run_artifact(run_dir, "run_manifest")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    review_candidates = load_run_artifact(run_dir, "review_candidates")
    rule_issues = load_run_artifact(run_dir, "rule_issues")

    vlm_config = defaults_config.get("vlm", {})
    runtime_vlm = runtime_config["vlm"] if runtime_config is not None else None
    decision_enum = list(vlm_config.get("decision_enum", []))
    model_name = (
        runtime_vlm["model"]
        if runtime_vlm is not None
        else str(run_manifest.get("vlm_version") or vlm_config.get("model", "qwen2.5-vl"))
    )
    requests = build_vlm_requests(
        review_candidates,
        normalized_annotations,
        image_index,
        class_map,
        risk_scores,
        rule_issues,
        model=model_name,
        decision_enum=decision_enum,
    )

    if responses_file is not None:
        normalized_raw_responses = _normalize_raw_responses(
            _load_external_records(responses_file),
            requests,
        )
        active_mode = "fixture"
    elif runtime_vlm is not None and runtime_vlm["mode"] == "live":
        normalized_raw_responses = _execute_live_vlm_requests(
            requests,
            run_manifest=run_manifest,
            runtime_config=runtime_config,
            runtime_config_file=runtime_config_file,
            transport=transport,
        )
        active_mode = "live"
    else:
        normalized_raw_responses = []
        active_mode = runtime_vlm["mode"] if runtime_vlm is not None else "fixture"

    reviews = parse_vlm_reviews(
        normalized_raw_responses,
        requests,
        class_map,
        decision_enum=decision_enum,
    ) if normalized_raw_responses else []

    if runtime_config is not None:
        _write_vlm_runtime_context(
            run_dir,
            run_manifest,
            runtime_config,
            runtime_config_file=runtime_config_file,
            active_mode=active_mode,
            model_name=model_name,
        )

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
            if key not in {"request_id", "image_id", "ann_id", "metric_kind", "provider_response", "provider", "model"}
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
        request_payload = request_lookup.get(str(request_id))
        if request_payload is None:
            raise ValueError(f"unknown VLM request_id in raw response: {request_id}")

        record: dict[str, Any] = {
            "request_id": request_payload["request_id"],
            "image_id": request_payload["image_id"],
            "ann_id": request_payload["ann_id"],
            "metric_kind": _validated_metric_kind(raw_response.get("metric_kind")),
        }
        if "response" in raw_response:
            record["response"] = raw_response["response"]
        elif "response_text" in raw_response:
            record["response_text"] = raw_response["response_text"]
        else:
            record["response"] = {
                key: value
                for key, value in raw_response.items()
                if key not in {"request_id", "metric_kind"}
            }
        normalized_records.append(record)
    return normalized_records


def _execute_live_vlm_requests(
    requests: list[dict[str, Any]],
    *,
    run_manifest: dict[str, Any],
    runtime_config: dict[str, Any],
    runtime_config_file: Path | None,
    transport: VLMTransport | None,
) -> list[dict[str, Any]]:
    if not requests:
        return []

    vlm_runtime = runtime_config["vlm"]
    api_key = resolve_required_env(vlm_runtime.get("api_key_env"), label="live VLM")
    url = _build_chat_completions_url(vlm_runtime["base_url"], vlm_runtime["endpoint_path"])
    timeout_seconds = float(vlm_runtime["timeout_seconds"])
    max_retries = int(vlm_runtime["max_retries"])
    transport_fn = transport or _default_vlm_transport

    normalized_records: list[dict[str, Any]] = []
    for request_payload in requests:
        image_path = _resolve_request_image_path(run_manifest, request_payload)
        provider_response = _execute_live_vlm_request(
            url=url,
            api_key=api_key,
            request_payload=request_payload,
            runtime_config=runtime_config,
            image_path=image_path,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            transport=transport_fn,
        )
        response_text = _extract_chat_completion_text(provider_response)
        normalized_records.append(
            {
                "request_id": request_payload["request_id"],
                "image_id": request_payload["image_id"],
                "ann_id": request_payload["ann_id"],
                "response_text": response_text,
                "metric_kind": "measured",
                "provider": vlm_runtime["provider"],
                "model": str(provider_response.get("model") or vlm_runtime["model"]),
                "provider_response": provider_response,
            }
        )
    return normalized_records


def _execute_live_vlm_request(
    *,
    url: str,
    api_key: str,
    request_payload: dict[str, Any],
    runtime_config: dict[str, Any],
    image_path: Path,
    timeout_seconds: float,
    max_retries: int,
    transport: VLMTransport,
) -> dict[str, Any]:
    vlm_runtime = runtime_config["vlm"]
    request_body = _build_chat_completions_payload(
        request_payload,
        runtime_config=runtime_config,
        image_path=image_path,
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return transport(url, headers, request_body, timeout_seconds)
        except Exception as exc:  # pragma: no cover - retried branches depend on injected failures
            last_error = exc
            if attempt >= max_retries:
                raise RuntimeError(
                    f"live VLM request failed after {max_retries + 1} attempts for {request_payload['request_id']}"
                ) from exc
    raise RuntimeError(
        f"live VLM request failed without a captured exception for {request_payload['request_id']}"
    ) from last_error


def _build_chat_completions_payload(
    request_payload: dict[str, Any],
    *,
    runtime_config: dict[str, Any],
    image_path: Path,
) -> dict[str, Any]:
    vlm_runtime = runtime_config["vlm"]
    payload: dict[str, Any] = {
        "model": vlm_runtime["model"],
        "temperature": vlm_runtime["temperature"],
        "max_tokens": vlm_runtime["max_tokens"],
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": vlm_runtime["system_prompt"],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": _build_live_user_prompt(request_payload),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": _image_path_to_data_url(image_path),
                        },
                    },
                ],
            },
        ],
    }
    if vlm_runtime["response_format"] == "json_object":
        payload["response_format"] = {"type": "json_object"}
    return payload


def _build_live_user_prompt(request_payload: dict[str, Any]) -> str:
    envelope = {
        "task": "Validate one fixed-class 2D detection annotation and return one JSON object only.",
        "instructions": [
            "Use exactly one decision from allowed_decisions.",
            "Keep new_class_name null unless the decision is relabel.",
            "Keep missing_candidates as an empty array unless the decision is add_missing.",
            "Do not add markdown fences or explanatory prose outside the JSON object.",
        ],
        "request": request_payload,
    }
    return json.dumps(envelope, ensure_ascii=False)


def _default_vlm_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    http_request = urllib_request.Request(
        url=url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib_request.urlopen(http_request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"VLM HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"VLM transport error: {exc.reason}") from exc

    try:
        provider_response = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("VLM endpoint returned non-JSON content") from exc
    if not isinstance(provider_response, dict):
        raise RuntimeError("VLM endpoint response must be a JSON object")
    return provider_response


def _build_chat_completions_url(base_url: str, endpoint_path: str) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
    return f"{normalized_base}{normalized_path}"


def _resolve_request_image_path(
    run_manifest: dict[str, Any],
    request_payload: dict[str, Any],
) -> Path:
    source_id = request_payload["image_id"].split(":", 1)[0]
    relative_path = Path(request_payload["image_reference"]["relative_path"])
    for source in run_manifest.get("input_sources", []):
        if source.get("source_id") != source_id:
            continue
        images_dir = source.get("images_dir")
        if not images_dir:
            raise ValueError(f"input source {source_id} does not expose images_dir for live VLM")
        image_path = Path(images_dir) / relative_path
        if image_path.exists():
            return image_path
        raise ValueError(f"live VLM image path does not exist: {image_path}")
    raise ValueError(f"cannot resolve live VLM image path for source_id {source_id}")


def _image_path_to_data_url(image_path: Path) -> str:
    mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_chat_completion_text(provider_response: dict[str, Any]) -> str:
    choices = provider_response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("VLM endpoint response does not include choices[0]")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("VLM endpoint choice payload must be an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("VLM endpoint choice must include a message object")
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
        text = "\n".join(part for part in text_parts if part.strip())
    else:
        raise RuntimeError("VLM endpoint message content must be text or a text-part array")
    cleaned = _strip_code_fences(text).strip()
    if not cleaned:
        raise RuntimeError("VLM endpoint returned empty message content")
    return cleaned


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 3 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _write_vlm_runtime_context(
    run_dir: Path,
    run_manifest: dict[str, Any],
    runtime_config: dict[str, Any],
    *,
    runtime_config_file: Path | None,
    active_mode: str,
    model_name: str,
) -> None:
    runtime_context = dict(run_manifest.get("runtime_context") or {})
    runtime_context.update(
        runtime_config_reference(
            runtime_config,
            config_path=runtime_config_file,
        )
    )
    runtime_context["vlm"] = {
        "mode": active_mode,
        "provider": runtime_config["vlm"]["provider"],
        "base_url": runtime_config["vlm"]["base_url"],
        "endpoint_path": runtime_config["vlm"]["endpoint_path"],
        "api_key_env": runtime_config["vlm"]["api_key_env"],
        "model": model_name,
        "response_format": runtime_config["vlm"]["response_format"],
    }
    run_manifest["runtime_context"] = runtime_context
    run_manifest["vlm_version"] = model_name
    write_run_artifact(run_dir, "run_manifest", run_manifest, overwrite=True)


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


def _validated_metric_kind(value: Any) -> str:
    if value is None:
        return "proxy"
    if not isinstance(value, str) or value not in VALID_METRIC_KINDS:
        raise ValueError(f"metric_kind must be one of {sorted(VALID_METRIC_KINDS)}")
    return value
