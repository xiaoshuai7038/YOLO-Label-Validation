from __future__ import annotations

import json

from yolo_label_validation.bootstrap import initialize_run_directory
from yolo_label_validation.cli import main
from yolo_label_validation.contracts import RunManifest, artifact_specs, build_artifact_layout


def test_initialize_run_directory_creates_all_artifacts(tmp_path) -> None:
    run_dir = tmp_path / "run-001"
    manifest = RunManifest(
        run_id="run-001",
        dataset_version="ds_v1",
        class_map_version="classes_v1",
        prelabel_source="prelabel_model_v1",
    )

    initialize_run_directory(run_dir, manifest)
    layout = build_artifact_layout(run_dir)

    for spec in artifact_specs():
        assert layout.path_for(spec.name).exists()

    run_manifest = json.loads(
        layout.path_for("run_manifest").read_text(encoding="utf-8")
    )
    assert run_manifest["run_id"] == "run-001"
    assert run_manifest["artifacts"]["patches"].endswith("patches.json")

    patches = json.loads(layout.path_for("patches").read_text(encoding="utf-8"))
    assert patches == []


def test_show_layout_lists_core_artifacts(capsys) -> None:
    exit_code = main(["show-layout"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "normalized_annotations.jsonl" in captured.out
    assert "patches.json" in captured.out


def test_cli_init_run_prints_manifest_json(tmp_path, capsys) -> None:
    output_dir = tmp_path / "cli-run"
    exit_code = main(
        [
            "init-run",
            "--run-id",
            "cli-run",
            "--output-dir",
            str(output_dir),
            "--note",
            "bootstrap smoke",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["run_id"] == "cli-run"
    assert payload["notes"] == ["bootstrap smoke"]
    assert (output_dir / "run_manifest.json").exists()
