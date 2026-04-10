from __future__ import annotations

import json
from pathlib import Path

from yolo_label_validation.cli import main
from yolo_label_validation.artifact_io import load_run_artifact
from yolo_label_validation.rules import (
    build_class_stats,
    load_threshold_policy,
    run_rule_checks,
    run_rules_for_directory,
)

from .support import build_normalized_yolo_run


ROOT = Path(__file__).resolve().parents[1]


def test_load_threshold_policy_supports_yaml_example() -> None:
    policy = load_threshold_policy(ROOT / "configs" / "thresholds.example.yaml")

    assert policy.thresholds_version == "th_v1"
    assert policy.global_thresholds["min_box_pixels"] == 4
    assert policy.per_class["helmet"]["aspect_ratio_max"] == 4.0


def test_run_rule_checks_emits_reasoned_issues(tmp_path) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    image_index = load_run_artifact(run_dir, "image_index")
    class_map = load_run_artifact(run_dir, "class_map")

    invalid_class = dict(normalized_annotations[0])
    invalid_class["ann_id"] = "invalid-class"
    invalid_class["class_id"] = 99
    invalid_class["class_name"] = "ghost"
    invalid_class["bbox_xyxy"] = [10.0, 10.0, 8.0, 20.0]
    invalid_class["bbox_normalized_cxcywh"] = [1.1, 0.5, 0.2, 0.4]

    duplicate = dict(normalized_annotations[0])
    duplicate["ann_id"] = "duplicate-cat"

    threshold_policy = load_threshold_policy(
        payload={
            "thresholds_version": "th_rules",
            "global": {
                "min_box_pixels": 4,
                "duplicate_iou": 0.9,
            },
            "per_class": {
                "cat": {
                    "aspect_ratio_max": 1.5,
                }
            },
        }
    )

    issues = run_rule_checks(
        normalized_annotations + [invalid_class, duplicate],
        image_index,
        class_map,
        threshold_policy,
    )
    issue_types = {issue["issue_type"] for issue in issues}

    assert "invalid_class" in issue_types
    assert "non_positive_box" in issue_types
    assert "normalized_box_out_of_range" in issue_types
    assert "duplicate_box" in issue_types
    assert all(issue["reason"] for issue in issues)
    assert all(issue["reason_code"] for issue in issues)


def test_build_class_stats_includes_threshold_snapshot(tmp_path) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)
    normalized_annotations = load_run_artifact(run_dir, "normalized_annotations")
    class_map = load_run_artifact(run_dir, "class_map")
    threshold_policy = load_threshold_policy(
        payload={
            "thresholds_version": "th_stats",
            "global": {"min_box_pixels": 4, "duplicate_iou": 0.9},
            "per_class": {},
        }
    )
    class_stats = build_class_stats(
        normalized_annotations,
        class_map,
        [],
        threshold_policy,
    )

    assert class_stats["thresholds_version"] == "th_stats"
    assert class_stats["threshold_snapshot"]["global"]["min_box_pixels"] == 4
    assert class_stats["classes"][0]["annotation_count"] == 1


def test_run_rules_for_directory_writes_m3_artifacts(tmp_path) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)

    outputs = run_rules_for_directory(
        run_dir,
        thresholds_file=ROOT / "configs" / "thresholds.example.yaml",
        overwrite=True,
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["thresholds_version"] == "th_v1"
    assert (run_dir / "golden_set_manifest.json").exists()
    assert (run_dir / "golden_eval_report.json").exists()
    assert (run_dir / "rule_issues.json").exists()
    assert (run_dir / "class_stats.json").exists()
    assert outputs["golden_set_manifest"]["golden_set_version"] == "golden_v1"


def test_run_rules_preserves_upstream_normalized_artifacts(tmp_path) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)

    before_annotations = load_run_artifact(run_dir, "normalized_annotations")
    before_image_index = load_run_artifact(run_dir, "image_index")
    before_class_map = load_run_artifact(run_dir, "class_map")

    run_rules_for_directory(run_dir, overwrite=True)

    assert load_run_artifact(run_dir, "normalized_annotations") == before_annotations
    assert load_run_artifact(run_dir, "image_index") == before_image_index
    assert load_run_artifact(run_dir, "class_map") == before_class_map


def test_cli_run_rules_writes_rule_outputs(tmp_path, capsys) -> None:
    run_dir = build_normalized_yolo_run(tmp_path)

    exit_code = main(
        [
            "run-rules",
            "--run-dir",
            str(run_dir),
            "--thresholds-file",
            str(ROOT / "configs" / "thresholds.example.yaml"),
            "--overwrite",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["thresholds_version"] == "th_v1"
    assert (run_dir / "rule_issues.json").exists()
