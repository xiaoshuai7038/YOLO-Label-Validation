from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.decision import (
    build_decision_results,
    build_manual_review_queue,
    build_patch_records,
    run_decision_for_directory,
)
from yolo_label_validation.detector_refine import run_detector_refine_for_directory

from .support import build_risk_ready_run, build_vlm_ready_run, build_vlm_ready_zero_annotation_run


ROOT = Path(__file__).resolve().parents[1]


def test_run_decision_for_directory_emits_relabel_patch(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "relabel",
                "class_ok": False,
                "box_ok": True,
                "new_class_name": "dog",
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "outline matches dog better",
                "reason_code": "VLM_RELABEL_DOG",
                "confidence": 0.97,
            }
        ],
    )

    outputs = run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    assert (run_dir / "decision_results.json").exists()
    assert (run_dir / "patches.json").exists()
    assert outputs["decision_results"][0]["action"] == "relabel"
    assert outputs["decision_results"][0]["review_scope"] == "annotation"
    assert outputs["patches"][0]["action"] == "relabel"
    assert outputs["patches"][0]["new_class_name"] == "dog"
    assert outputs["manual_review_queue"] == []


def test_build_manual_review_queue_routes_uncertain_cases(tmp_path) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "uncertain",
                "class_ok": False,
                "box_ok": False,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "the image is too ambiguous for an automatic action",
                "reason_code": "VLM_UNCERTAIN",
                "confidence": 0.55,
            }
        ],
    )

    outputs = run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    queue = build_manual_review_queue(outputs["decision_results"])

    assert outputs["patches"] == []
    assert len(queue) == 1
    assert queue[0]["requested_action"] == "manual_review"
    assert queue[0]["reason_codes"][0] == "VLM_UNCERTAIN"


def test_build_decision_results_routes_rule_errors_to_manual_review_even_without_vlm(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    risk_scores = load_run_artifact(run_dir, "risk_scores")

    decision_results = build_decision_results(
        normalized_annotations,
        [
            {
                "issue_id": "fixture:error",
                "image_id": normalized_annotations[0]["image_id"],
                "ann_id": normalized_annotations[0]["ann_id"],
                "related_ann_id": None,
                "issue_type": "bbox_out_of_bounds",
                "severity": "error",
                "reason_code": "RULE_BBOX_OUT_OF_BOUNDS",
                "reason": "bbox exceeds image bounds",
                "auto_action_hint": "manual_review",
                "metric_kind": "measured",
                "evidence": {},
            }
        ],
        risk_scores,
        [],
        defaults_config=json.loads((ROOT / "configs" / "defaults.json").read_text(encoding="utf-8")),
    )

    assert decision_results[0]["status"] == "manual_review"
    assert decision_results[0]["reason_codes"] == ["DECISION_RULE_ERROR"]


def test_decision_uses_detector_refine_results_for_auto_refine(tmp_path) -> None:
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
    run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    outputs = run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )
    patches = build_patch_records(
        outputs["decision_results"],
        load_run_artifact(run_dir, "normalized_annotations"),
        timestamp="2026-04-10T00:00:00Z",
    )

    assert outputs["decision_results"][0]["action"] == "refine"
    assert outputs["decision_results"][0]["new_bbox_xyxy"]
    assert patches[0]["action"] == "refine"
    assert patches[0]["new_bbox_xyxy"] != patches[0]["old_bbox_xyxy"]


def test_run_decision_for_directory_emits_add_patch_from_image_level_missing(tmp_path) -> None:
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
    run_detector_refine_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    outputs = run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    add_decisions = [row for row in outputs["decision_results"] if row["action"] == "add"]
    assert len(add_decisions) == 1
    assert add_decisions[0]["review_scope"] == "image"
    assert add_decisions[0]["source_ann_id"] is None
    assert outputs["patches"][0]["action"] == "add"
    assert outputs["patches"][0]["review_source"]["review_scope"] == "image"


def test_build_manual_review_queue_routes_image_level_uncertain_cases(tmp_path) -> None:
    run_dir = build_vlm_ready_zero_annotation_run(
        tmp_path,
        [
            {
                "decision": "uncertain",
                "class_ok": False,
                "box_ok": False,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "image-level visibility is too ambiguous",
                "reason_code": "VLM_IMAGE_UNCERTAIN",
                "confidence": 0.4,
            }
        ],
    )

    outputs = run_decision_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    assert outputs["patches"] == []
    assert len(outputs["manual_review_queue"]) == 1
    assert outputs["manual_review_queue"][0]["ann_id"] is None
    assert outputs["manual_review_queue"][0]["review_scope"] == "image"


def test_cli_run_decision_writes_outputs(tmp_path, capsys) -> None:
    run_dir = build_vlm_ready_run(
        tmp_path,
        [
            {
                "decision": "relabel",
                "class_ok": False,
                "box_ok": True,
                "new_class_name": "dog",
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "outline matches dog better",
                "reason_code": "VLM_RELABEL_DOG",
                "confidence": 0.97,
            }
        ],
    )

    exit_code = main(
        [
            "run-decision",
            "--run-dir",
            str(run_dir),
            "--defaults-file",
            str(ROOT / "configs" / "defaults.json"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["decision_count"] >= 1
    assert payload["patch_count"] == 1
    assert (run_dir / "manual_review_queue.json").exists()
