from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.detector_refine import run_detector_refine_for_directory

from .support import build_vlm_ready_run, build_vlm_ready_zero_annotation_run


ROOT = Path(__file__).resolve().parents[1]


def _live_runtime_config(tmp_path: Path) -> dict[str, object]:
    weights_path = tmp_path / "weights" / "yolo11n.pt"
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights_path.write_text("stub weights", encoding="utf-8")
    return {
        "version": "runtime_integration_v1",
        "defaults_file": "configs/defaults.json",
        "thresholds_file": "configs/thresholds.example.yaml",
        "vlm": {
            "mode": "fixture",
            "provider": "openai_compatible",
            "base_url": "http://127.0.0.1:0",
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
            "weights_path": str(weights_path),
            "device": "cpu",
            "confidence_threshold": 0.25,
            "iou_threshold": 0.45,
            "max_det": 100,
            "refine_match_iou": 0.1,
            "missing_match_iou": 0.1,
        },
    }


def test_run_detector_refine_for_directory_writes_refine_results(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "refine",
                "class_ok": True,
                "box_ok": False,
                "new_class_name": None,
                "need_refine_box": True,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "box needs a geometry refresh",
                "reason_code": "VLM_REFINE_GEOMETRY",
                "confidence": 0.94,
            }
        ],
    )

    outputs = run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    assert (run_dir / "refine_results.json").exists()
    assert outputs["refine_results"][0]["decision_hint"] == "refine"
    assert outputs["refine_results"][0]["iou_with_original"] >= 0.5


def test_run_detector_refine_for_directory_writes_missing_results(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "add_missing",
                "class_ok": True,
                "box_ok": True,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": True,
                "missing_candidates": [
                    {
                        "class_name": "dog",
                        "bbox_xyxy": [55.0, 8.0, 90.0, 42.0],
                        "confidence": 0.96,
                        "reason": "second dog is visible at the right side of the frame",
                        "reason_code": "VLM_MISSING_DOG",
                    }
                ],
                "reason": "a second object is visible in the scene",
                "reason_code": "VLM_ADD_MISSING",
                "confidence": 0.96,
            }
        ],
    )

    outputs = run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    assert (run_dir / "missing_results.json").exists()
    assert outputs["missing_results"][0]["decision_hint"] == "add"
    assert outputs["missing_results"][0]["class_name"] == "dog"


def test_cli_run_detector_refine_writes_outputs(tmp_path, capsys) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "refine",
                "class_ok": True,
                "box_ok": False,
                "new_class_name": None,
                "need_refine_box": True,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "box needs a geometry refresh",
                "reason_code": "VLM_REFINE_GEOMETRY",
                "confidence": 0.94,
            }
        ],
    )

    exit_code = main(
        [
            "run-detector-refine",
            "--run-dir",
            str(run_dir),
            "--thresholds-file",
            str(ROOT / "configs" / "thresholds.example.yaml"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["refine_count"] == 1
    assert payload["missing_count"] == 0


def test_run_detector_refine_live_mode_uses_detector_runner(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "refine",
                "class_ok": True,
                "box_ok": False,
                "new_class_name": None,
                "need_refine_box": True,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "box needs a geometry refresh",
                "reason_code": "VLM_REFINE_GEOMETRY",
                "confidence": 0.94,
            }
        ],
    )
    runtime_config = _live_runtime_config(tmp_path)

    def fake_detector_runner(image_path: Path, settings: dict[str, object], class_by_name: dict[str, dict[str, object]]):
        assert image_path.exists()
        assert Path(str(settings["weights_path"])).exists()
        assert "cat" in class_by_name
        return [
            {
                "class_name": "cat",
                "bbox_xyxy": [38.0, 16.0, 62.0, 44.0],
                "confidence": 0.88,
            }
        ]

    outputs = run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        runtime_config_payload=runtime_config,
        detector_runner=fake_detector_runner,
        overwrite=True,
    )

    assert outputs["refine_results"][0]["metric_kind"] == "measured"
    assert outputs["refine_results"][0]["reason_code"] == "DETECTOR_REFINE_LIVE"
    manifest = load_run_artifact(run_dir, "run_manifest")
    assert manifest["runtime_context"]["detector"]["mode"] == "live"


def test_run_detector_refine_live_mode_marks_unconfirmed_missing_as_pending(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "add_missing",
                "class_ok": True,
                "box_ok": True,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": True,
                "missing_candidates": [
                    {
                        "class_name": "dog",
                        "bbox_xyxy": [55.0, 8.0, 90.0, 42.0],
                        "confidence": 0.96,
                        "reason": "second dog is visible at the right side of the frame",
                        "reason_code": "VLM_MISSING_DOG",
                    }
                ],
                "reason": "a second object is visible in the scene",
                "reason_code": "VLM_ADD_MISSING",
                "confidence": 0.96,
            }
        ],
    )
    runtime_config = _live_runtime_config(tmp_path)

    outputs = run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        runtime_config_payload=runtime_config,
        detector_runner=lambda image_path, settings, class_by_name: [],
        overwrite=True,
    )

    assert outputs["missing_results"][0]["metric_kind"] == "pending"
    assert outputs["missing_results"][0]["detector_confidence"] == 0.0
    assert outputs["missing_results"][0]["reason_code"] == "DETECTOR_MISSING_UNCONFIRMED"


def test_run_detector_refine_supports_image_level_missing_reviews(tmp_path) -> None:
    run_dir = build_vlm_ready_zero_annotation_run(
        tmp_path,
        [
            {
                "decision": "add_missing",
                "class_ok": True,
                "box_ok": True,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": True,
                "missing_candidates": [
                    {
                        "class_name": "dog",
                        "bbox_xyxy": [55.0, 8.0, 90.0, 42.0],
                        "confidence": 0.96,
                        "reason": "the image contains an unlabeled carton stack",
                        "reason_code": "VLM_IMAGE_LEVEL_MISSING",
                    }
                ],
                "reason": "the image contains an unlabeled object",
                "reason_code": "VLM_IMAGE_REVIEW_MISSING",
                "confidence": 0.96,
            }
        ],
    )

    outputs = run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    assert outputs["missing_results"][0]["source_ann_id"] is None
    assert outputs["missing_results"][0]["review_scope"] == "image"
    assert outputs["missing_results"][0]["missing_id"].startswith("missing:vlm:")
