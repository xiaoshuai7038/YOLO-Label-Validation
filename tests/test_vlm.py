from __future__ import annotations

import json
from pathlib import Path

import pytest

from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.vlm import (
    build_vlm_requests,
    parse_vlm_reviews,
    run_vlm_for_directory,
)

from .support import build_risk_ready_run, write_json


ROOT = Path(__file__).resolve().parents[1]


def test_build_vlm_requests_and_parse_reviews_are_deterministic(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    review_candidates = load_run_artifact(run_dir, "review_candidates")
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")
    risk_scores = load_run_artifact(run_dir, "risk_scores")
    rule_issues = load_run_artifact(run_dir, "rule_issues")

    requests = build_vlm_requests(
        review_candidates,
        normalized_annotations,
        image_index,
        class_map,
        risk_scores,
        rule_issues,
        model="qwen2.5-vl",
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
    )
    reviews = parse_vlm_reviews(
        [
            {
                "request_id": requests[0]["request_id"],
                "response": {
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
                },
            }
        ],
        requests,
        class_map,
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
    )

    assert len(requests) == 1
    assert requests[0]["annotation_context"]["rule_issues"] == []
    assert requests[0]["allowed_decisions"][1] == "relabel"
    assert reviews[0]["decision"] == "relabel"
    assert reviews[0]["reason_code"] == "VLM_RELABEL_DOG"
    assert reviews[0]["metric_kind"] == "proxy"


def test_parse_vlm_reviews_rejects_invalid_enum(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    requests = build_vlm_requests(
        load_run_artifact(run_dir, "review_candidates"),
        load_run_artifact(run_dir, "normalized_annotations"),
        load_run_artifact(run_dir, "image_index"),
        load_run_artifact(run_dir, "class_map"),
        load_run_artifact(run_dir, "risk_scores"),
        load_run_artifact(run_dir, "rule_issues"),
        model="qwen2.5-vl",
        decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
    )

    with pytest.raises(ValueError, match="allowed enum"):
        parse_vlm_reviews(
            [
                {
                    "request_id": requests[0]["request_id"],
                    "response": {
                        "decision": "explode",
                        "class_ok": True,
                        "box_ok": True,
                        "new_class_name": None,
                        "need_refine_box": False,
                        "need_add_missing": False,
                        "missing_candidates": [],
                        "reason": "bad response",
                        "reason_code": "VLM_BAD",
                        "confidence": 0.1,
                    },
                }
            ],
            requests,
            load_run_artifact(run_dir, "class_map"),
            decision_enum=["keep", "relabel", "refine", "delete", "add_missing", "uncertain"],
        )


def test_run_vlm_for_directory_writes_artifacts(tmp_path) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    responses_file = tmp_path / "responses.json"
    write_json(
        responses_file,
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

    outputs = run_vlm_for_directory(
        run_dir,
        responses_file=responses_file,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    assert (run_dir / "vlm_requests.jsonl").exists()
    assert (run_dir / "vlm_raw_responses.jsonl").exists()
    assert (run_dir / "vlm_review.json").exists()
    assert len(outputs["vlm_requests"]) == 1
    assert outputs["vlm_review"][0]["new_class_name"] == "dog"


def test_cli_run_vlm_writes_review_outputs(tmp_path, capsys) -> None:
    run_dir = build_risk_ready_run(tmp_path)
    responses_file = tmp_path / "responses.json"
    write_json(
        responses_file,
        [
            {
                "decision": "keep",
                "class_ok": True,
                "box_ok": True,
                "new_class_name": None,
                "need_refine_box": False,
                "need_add_missing": False,
                "missing_candidates": [],
                "reason": "label and geometry are acceptable",
                "reason_code": "VLM_KEEP_OK",
                "confidence": 0.95,
            }
        ],
    )

    exit_code = main(
        [
            "run-vlm",
            "--run-dir",
            str(run_dir),
            "--responses-file",
            str(responses_file),
            "--defaults-file",
            str(ROOT / "configs" / "defaults.json"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["request_count"] == 1
    assert payload["review_count"] == 1
    assert (run_dir / "vlm_review.json").exists()
