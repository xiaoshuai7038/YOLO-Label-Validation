# Contract - M2 Input Normalization

## Goal

Implement FR-001 and FR-002 so the repository can normalize YOLO txt and COCO
JSON annotations into one deterministic internal contract with explicit
raw-source lineage, a frozen class-map snapshot, and a run manifest that keeps
dataset and model versions explicit for later patch generation.

## Scope

- one internal normalized annotation contract for both YOLO txt and COCO JSON
- deterministic writers for `normalized_annotations.jsonl`, `image_index.json`,
  and `class_map.json`
- run-manifest extension or reuse so normalization runs record source formats
  and version fields explicitly
- class-map validation that rejects ambiguous or inconsistent definitions
- local CLI entrypoints and tests for the M2 normalization path

## Out of Scope

- static rule validation, golden-set logic, or threshold policy evaluation
- model-assisted risk scoring, VLM review, detector refine/add, or CVAT
  integration
- mutating any source labels or source images

## Closure Level

- Target closure: `slice`
- Meaning: FR-001 and FR-002 are implemented and validated locally, but the
  broader SRS remains incomplete beyond normalization and run-manifest fidelity

## Done When

- `DW-001` YOLO txt sources normalize into the canonical annotation contract
  with traceable lineage back to source file and line number
- `DW-002` COCO JSON sources normalize into the same contract with traceable
  lineage back to source annotation and image ids
- `DW-003` `image_index.json`, `class_map.json`, and `run_manifest.json` are
  emitted with explicit version fields and deterministic ordering
- `DW-004` ambiguous or inconsistent class-map definitions are rejected with
  actionable errors before downstream artifacts are written
- `DW-005` local tests prove traceability, deterministic output, and CLI or
  writer integration for the M2 slice
- `DW-006` M2 docs, task docs, and validation evidence are synchronized

## Changes

- `CHG-001` add an ingestion module that parses YOLO txt labels plus image
  metadata and parses COCO JSON annotations into a shared intermediate model
- `CHG-002` add canonical normalized annotation, image-index, and class-map
  serialization with deterministic ordering and lineage payloads
- `CHG-003` extend `RunManifest` and the CLI so normalization runs emit the
  M2 artifacts without relying on raw source formats downstream
- `CHG-004` freeze the M2 artifact contracts in `schemas/` and document the
  touched interfaces in `docs/prompt.md`
- `CHG-005` add regression tests that cover YOLO normalization, COCO
  normalization, class-map rejection, and deterministic artifact output

## Coverage

- `COV-001` `src/yolo_label_validation/ingest.py` ->
  `normalize_yolo_source()`
- `COV-002` `src/yolo_label_validation/ingest.py` ->
  `normalize_coco_source()`
- `COV-003` `src/yolo_label_validation/ingest.py` ->
  `merge_class_maps()` and `normalize_sources()`
- `COV-004` `src/yolo_label_validation/ingest.py` ->
  `write_normalized_run_artifacts()`
- `COV-005` `src/yolo_label_validation/contracts.py` ->
  `RunManifest.to_dict()` and any M2 manifest fields
- `COV-006` `src/yolo_label_validation/cli.py` -> normalization subcommands
- `COV-007` `tests/test_ingest.py` -> fixture-based M2 regression coverage

## Validation Plan

- `TC-001` normalize a YOLO txt sample into one annotation record with
  absolute box coordinates, normalized coordinates, and lineage to the raw txt
  line
- `TC-002` normalize a COCO JSON sample into the same annotation contract with
  lineage to raw annotation id and raw image id
- `TC-003` reject duplicate or conflicting class-map definitions before
  artifacts are written
- `TC-004` write `normalized_annotations.jsonl`, `image_index.json`, and
  `class_map.json` in deterministic order for repeated runs with the same
  pinned manifest metadata
- `TC-005` CLI normalization commands emit a `run_manifest.json` that keeps
  dataset, class-map, source-format, and model versions explicit
- `TC-006` M2 task docs pass the doc gate and repository regression tests stay
  green

- `T-001` `uv run pytest -q`
- `T-002` `uv run python scripts/check_task_docs.py tasks/m2-input-normalization`
- `T-003` focused `uv run python scripts/run_cli.py normalize-yolo ...`
- `T-004` focused `uv run python scripts/run_cli.py normalize-coco ...`
