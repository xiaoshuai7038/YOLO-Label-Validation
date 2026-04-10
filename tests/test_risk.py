from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.cli import main
from yolo_label_validation.risk import (
    build_review_candidates,
    build_risk_scores,
    run_risk_for_directory,
)

from tests.support import build_rule_ready_run


ROOT = Path(__file__).resolve().parents[1]


def test_build_risk_scores_and_candidates_are_deterministic(tmp_path) -> None:
    run_dir = build_rule_ready_run(tmp_path)
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    rule_issues = load_run_artifact(run_dir, "rule_issues")
    class_stats = load_run_artifact(run_dir, "class_stats")

    risk_scores = build_risk_scores(
        normalized_annotations,
        rule_issues,
        class_stats,
    )
    review_candidates = build_review_candidates(
        risk_scores,
        json.loads((ROOT / "configs" / "defaults.json").read_text(encoding="utf-8")),
    )

    assert len(risk_scores) == 1
    assert risk_scores[0]["metric_kind"] == "proxy"
    assert risk_scores[0]["risk_tags"]
    assert risk_scores[0]["reason_codes"]
    assert len(review_candidates) == 1
    assert review_candidates[0]["candidate_annotations"][0]["reason_codes"]


def test_run_risk_for_directory_writes_artifacts(tmp_path) -> None:
    run_dir = build_rule_ready_run(tmp_path)

    outputs = run_risk_for_directory(
        run_dir,
        defaults_file=ROOT / "configs" / "defaults.json",
        overwrite=True,
    )

    assert (run_dir / "risk_scores.json").exists()
    assert (run_dir / "review_candidates.json").exists()
    assert len(outputs["risk_scores"]) == 1
    assert outputs["review_candidates"][0]["image_id"]


def test_cli_run_risk_writes_risk_outputs(tmp_path, capsys) -> None:
    run_dir = build_rule_ready_run(tmp_path)

    exit_code = main(
        [
            "run-risk",
            "--run-dir",
            str(run_dir),
            "--defaults-file",
            str(ROOT / "configs" / "defaults.json"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["risk_score_count"] == 1
    assert (run_dir / "risk_scores.json").exists()
