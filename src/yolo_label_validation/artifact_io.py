from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .contracts import artifact_specs, build_artifact_layout


_ARTIFACT_KIND_BY_NAME = {spec.name: spec.kind for spec in artifact_specs()}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    payload = path.read_text(encoding="utf-8").strip()
    if not payload:
        return []
    return [json.loads(line) for line in payload.splitlines()]


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    lines = [
        json.dumps(record, ensure_ascii=False, sort_keys=True)
        for record in records
    ]
    payload = "\n".join(lines)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")


def ensure_artifact_writable(path: Path, *, overwrite: bool) -> None:
    if overwrite or not path.exists():
        return
    existing = path.read_text(encoding="utf-8").strip()
    if existing in {"", "{}", "[]"}:
        return
    raise FileExistsError(f"refusing to overwrite populated artifact without --overwrite: {path}")


def run_artifact_path(run_dir: Path, artifact_name: str) -> Path:
    return build_artifact_layout(run_dir).path_for(artifact_name)


def load_run_artifact(run_dir: Path, artifact_name: str) -> Any:
    path = run_artifact_path(run_dir, artifact_name)
    artifact_kind = _ARTIFACT_KIND_BY_NAME[artifact_name]
    if artifact_kind == "jsonl":
        return load_jsonl(path)
    return load_json(path)


def write_run_artifact(
    run_dir: Path,
    artifact_name: str,
    payload: Any,
    *,
    overwrite: bool = False,
) -> Path:
    path = run_artifact_path(run_dir, artifact_name)
    ensure_artifact_writable(path, overwrite=overwrite)
    artifact_kind = _ARTIFACT_KIND_BY_NAME[artifact_name]
    if artifact_kind == "jsonl":
        write_jsonl(path, payload)
    else:
        write_json(path, payload)
    return path
