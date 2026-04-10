from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.cli import main
from yolo_label_validation.detector_refine import run_detector_refine_for_directory

from .support import build_vlm_ready_run


ROOT = Path(__file__).resolve().parents[1]


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
