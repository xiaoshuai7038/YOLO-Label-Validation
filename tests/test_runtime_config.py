from __future__ import annotations

from pathlib import Path

from yolo_label_validation.runtime_config import load_runtime_config, resolve_runtime_path


def test_load_runtime_config_normalizes_live_payload() -> None:
    payload = {
        "version": "runtime_integration_v1",
        "defaults_file": "configs/defaults.json",
        "thresholds_file": "configs/thresholds.example.yaml",
        "vlm": {
            "mode": "live",
            "provider": "openai_compatible",
            "base_url": "http://127.0.0.1:8000",
            "endpoint_path": "/chat/completions",
            "api_key_env": "TEST_VLM_API_KEY",
            "model": "mock-live-vlm",
            "timeout_seconds": 15,
            "max_retries": 0,
            "temperature": 0.0,
            "response_format": "json_object",
            "max_tokens": 256,
            "image_transport": "data_url",
            "system_prompt": "Return JSON only.",
        },
        "detector": {
            "mode": "live",
            "family": "ultralytics",
            "weights_path": "artifacts/models/yolo11n.pt",
            "device": "cpu",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 100,
            "refine_match_iou": 0.1,
            "missing_match_iou": 0.1,
        },
    }

    config = load_runtime_config(payload=payload)

    assert config["vlm"]["mode"] == "live"
    assert config["detector"]["family"] == "ultralytics"
    assert config["detector"]["max_det"] == 100


def test_resolve_runtime_path_uses_config_directory(tmp_path) -> None:
    config_path = tmp_path / "runtime.integration.json"
    config_path.write_text("{}", encoding="utf-8")

    resolved = resolve_runtime_path("models/yolo11n.pt", config_path=config_path)

    assert resolved == (tmp_path / "models" / "yolo11n.pt").resolve()
