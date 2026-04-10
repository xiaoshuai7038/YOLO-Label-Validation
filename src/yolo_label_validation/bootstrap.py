from __future__ import annotations

import json
from pathlib import Path

from .contracts import ArtifactKind, RunManifest, artifact_specs, build_artifact_layout


EMPTY_CONTENT_BY_KIND: dict[ArtifactKind, object] = {
    "json_array": [],
    "json_object": {},
    "jsonl": "",
}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_empty_artifact(path: Path, artifact_kind: ArtifactKind) -> None:
    payload = EMPTY_CONTENT_BY_KIND[artifact_kind]
    if artifact_kind == "jsonl":
        path.write_text("", encoding="utf-8")
        return
    _write_json(path, payload)


def initialize_run_directory(
    output_dir: Path,
    manifest: RunManifest,
    overwrite: bool = False,
) -> RunManifest:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout = build_artifact_layout(output_dir)
    manifest.artifacts = layout.as_dict()

    for spec in artifact_specs():
        path = layout.path_for(spec.name)
        if path.exists() and not overwrite:
            continue
        if spec.name == "run_manifest":
            _write_json(path, manifest.to_dict())
            continue
        _write_empty_artifact(path, spec.kind)

    return manifest


def ensure_run_directory_layout(
    output_dir: Path,
    manifest: RunManifest,
) -> RunManifest:
    output_dir.mkdir(parents=True, exist_ok=True)
    layout = build_artifact_layout(output_dir)
    manifest.artifacts = layout.as_dict()

    for spec in artifact_specs():
        path = layout.path_for(spec.name)
        if path.exists():
            continue
        if spec.name == "run_manifest":
            _write_json(path, manifest.to_dict())
            continue
        _write_empty_artifact(path, spec.kind)

    _write_json(layout.path_for("run_manifest"), manifest.to_dict())
    return manifest


def render_layout_table() -> str:
    header = "name | file | kind | required | description"
    divider = "--- | --- | --- | --- | ---"
    rows = [header, divider]
    for spec in artifact_specs():
        rows.append(
            f"{spec.name} | {spec.filename} | {spec.kind} | "
            f"{'yes' if spec.required else 'no'} | {spec.description}"
        )
    return "\n".join(rows)
