from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.artifact_io import load_run_artifact, write_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.materialize import run_materialize_for_directory

from .support import build_decision_ready_run, build_normalized_yolo_run


ROOT = Path(__file__).resolve().parents[1]


def test_run_materialize_for_directory_applies_patches_without_mutating_source(tmp_path) -> None:
    run_dir = build_decision_ready_run(
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
    original_annotations = load_run_artifact(run_dir, "normalized_annotations")

    outputs = run_materialize_for_directory(
        run_dir,
        overwrite=True,
    )

    materialized_dir = Path(outputs["materialized"]["output_dir"])
    materialized_annotations = [
        json.loads(line)
        for line in (materialized_dir / "normalized_annotations.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert materialized_annotations[0]["class_name"] == "dog"
    assert original_annotations[0]["class_name"] == "cat"
    assert (run_dir / "run_summary.json").exists()
    assert outputs["run_summary"]["patch_counts"]["relabel"] == 1


def test_materialize_supports_add_patches(tmp_path) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)
    write_run_artifact(
        run_dir,
        "patches",
        [
            {
                "patch_id": "patch:add-001",
                "image_id": "fixture-yolo:img-001.png",
                "ann_id": None,
                "old_class_name": None,
                "old_bbox_xyxy": None,
                "action": "add",
                "new_class_name": "dog",
                "new_bbox_xyxy": [55.0, 8.0, 90.0, 42.0],
                "reason": "detected a second object in the frame",
                "reason_code": "DETECTOR_ADD_PATCH",
                "review_source": {"decision_id": "decision:missing:1", "reason_codes": ["DETECTOR_ADD_PATCH"]},
                "confidence": 0.95,
                "human_reviewed": False,
                "timestamp": "2026-04-10T00:00:00Z",
                "metric_kind": "proxy",
                "evidence": {"missing_result_ids": ["missing:1"]},
            }
        ],
        overwrite=True,
    )
    write_run_artifact(run_dir, "decision_results", [], overwrite=True)
    write_run_artifact(run_dir, "manual_review_queue", [], overwrite=True)
    write_run_artifact(run_dir, "rule_issues", [], overwrite=True)
    write_run_artifact(run_dir, "risk_scores", [], overwrite=True)
    write_run_artifact(run_dir, "refine_results", [], overwrite=True)
    write_run_artifact(run_dir, "missing_results", [], overwrite=True)

    outputs = run_materialize_for_directory(run_dir, overwrite=True)
    materialized_dir = Path(outputs["materialized"]["output_dir"])
    materialized_annotations = [
        json.loads(line)
        for line in (materialized_dir / "normalized_annotations.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert len(materialized_annotations) == 2
    assert any(annotation["class_name"] == "dog" for annotation in materialized_annotations)


def test_cli_run_materialize_writes_outputs(tmp_path, capsys) -> None:
    run_dir = build_decision_ready_run(
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
            "run-materialize",
            "--run-dir",
            str(run_dir),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["summary_run_id"] == "rules-smoke"
    assert payload["patch_count"] == 1
    assert (run_dir / "metrics_dashboard_source.json").exists()
