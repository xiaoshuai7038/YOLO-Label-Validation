from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "runtime.integration.json"


def load_runtime_config(
    config_path: Path | None = None,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if payload is not None:
        raw_config = payload
    else:
        target_path = config_path or DEFAULT_RUNTIME_CONFIG_PATH
        raw_config = json.loads(target_path.read_text(encoding="utf-8"))
    if not isinstance(raw_config, dict):
        raise ValueError("runtime config must be a JSON object")
    return _normalized_runtime_config(raw_config)


def resolve_runtime_path(
    raw_path: str | None,
    *,
    config_path: Path | None = None,
) -> Path | None:
    if raw_path is None:
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    base_dir = (config_path or DEFAULT_RUNTIME_CONFIG_PATH).resolve().parent
    return (base_dir / candidate).resolve()


def resolve_required_env(
    variable_name: str | None,
    *,
    label: str,
) -> str:
    if variable_name is None:
        raise ValueError(f"{label} requires an env var name in runtime config")
    value = os.getenv(variable_name)
    if value is None or not value.strip():
        raise ValueError(f"{label} requires environment variable {variable_name}")
    return value.strip()


def runtime_config_reference(
    runtime_config: dict[str, Any],
    *,
    config_path: Path | None = None,
) -> dict[str, Any]:
    return {
        "runtime_config_version": runtime_config["version"],
        "runtime_config_path": str((config_path or DEFAULT_RUNTIME_CONFIG_PATH).resolve()) if config_path is not None else None,
        "defaults_file": runtime_config.get("defaults_file"),
        "thresholds_file": runtime_config.get("thresholds_file"),
    }


def _normalized_runtime_config(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": _non_empty_string(payload.get("version"), "version"),
        "defaults_file": _optional_string(payload.get("defaults_file"), "defaults_file"),
        "thresholds_file": _optional_string(payload.get("thresholds_file"), "thresholds_file"),
        "vlm": _normalized_vlm_config(payload.get("vlm")),
        "detector": _normalized_detector_config(payload.get("detector")),
    }


def _normalized_vlm_config(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "vlm")
    mode = _enum_string(payload.get("mode"), "vlm.mode", {"fixture", "live"})
    return {
        "mode": mode,
        "provider": _non_empty_string(payload.get("provider"), "vlm.provider"),
        "base_url": _non_empty_string(payload.get("base_url"), "vlm.base_url"),
        "endpoint_path": _non_empty_string(payload.get("endpoint_path"), "vlm.endpoint_path"),
        "api_key_env": _optional_string(payload.get("api_key_env"), "vlm.api_key_env"),
        "model": _non_empty_string(payload.get("model"), "vlm.model"),
        "timeout_seconds": _bounded_float(payload.get("timeout_seconds"), "vlm.timeout_seconds", minimum=1.0),
        "max_retries": _bounded_int(payload.get("max_retries"), "vlm.max_retries", minimum=0),
        "temperature": _bounded_float(payload.get("temperature"), "vlm.temperature", minimum=0.0, maximum=2.0),
        "response_format": _enum_string(payload.get("response_format"), "vlm.response_format", {"json_object", "none"}),
        "max_tokens": _bounded_int(payload.get("max_tokens"), "vlm.max_tokens", minimum=1),
        "image_transport": _enum_string(payload.get("image_transport"), "vlm.image_transport", {"data_url"}),
        "system_prompt": _non_empty_string(payload.get("system_prompt"), "vlm.system_prompt"),
    }


def _normalized_detector_config(value: Any) -> dict[str, Any]:
    payload = _mapping(value, "detector")
    return {
        "mode": _enum_string(payload.get("mode"), "detector.mode", {"proxy", "live"}),
        "family": _non_empty_string(payload.get("family"), "detector.family"),
        "weights_path": _non_empty_string(payload.get("weights_path"), "detector.weights_path"),
        "device": _non_empty_string(payload.get("device"), "detector.device"),
        "confidence_threshold": _bounded_float(
            payload.get("confidence_threshold"),
            "detector.confidence_threshold",
            minimum=0.0,
            maximum=1.0,
        ),
        "iou_threshold": _bounded_float(
            payload.get("iou_threshold"),
            "detector.iou_threshold",
            minimum=0.0,
            maximum=1.0,
        ),
        "max_det": _bounded_int(payload.get("max_det"), "detector.max_det", minimum=1),
        "refine_match_iou": _bounded_float(
            payload.get("refine_match_iou"),
            "detector.refine_match_iou",
            minimum=0.0,
            maximum=1.0,
        ),
        "missing_match_iou": _bounded_float(
            payload.get("missing_match_iou"),
            "detector.missing_match_iou",
            minimum=0.0,
            maximum=1.0,
        ),
    }


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _non_empty_string(value, label)


def _non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _enum_string(value: Any, label: str, valid_values: set[str]) -> str:
    text = _non_empty_string(value, label)
    if text not in valid_values:
        raise ValueError(f"{label} must be one of {sorted(valid_values)}")
    return text


def _bounded_int(
    value: Any,
    label: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return parsed


def _bounded_float(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    if maximum is not None and parsed > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return parsed
