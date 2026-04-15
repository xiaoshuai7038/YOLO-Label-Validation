# Contract - Real Dataset YOLO Ingest Adapter

## Goal

Make the repository ingest the real YOLO dataset at
`E:\workspace\cigarette-identify\预标注测试\20264010` without renaming or moving
source files, while preserving canonical normalized artifacts and existing
separate-directory behavior.

## Scope

- extend YOLO normalization to support configurable image/label pairing keys
- support the real dataset shape where images and labels coexist in one
  directory and stems may differ only by a trailing `__hash`
- keep zero-label images in `image_index.json` with `annotation_count = 0`
- expose the new ingest behavior through the existing `normalize-yolo` CLI
- add tests and docs for the real-dataset ingest slice

## Out of Scope

- redesigning `risk.py`, `vlm.py`, or `decision.py` for image-level review of
  zero-annotation images
- adding a new annotation schema or changing canonical artifact names
- mutating, renaming, or reorganizing the source dataset on disk

## Closure Level

- Target closure: `slice`
- Meaning: the real dataset can be normalized into canonical run artifacts, but
  zero-annotation image review remains a documented follow-up slice

## Done When

- `DW-001` `normalize-yolo` accepts a pairing mode that can match image and
  label stems after stripping a trailing `__hash`
- `DW-002` the real dataset path can be normalized with one CLI command while
  keeping source files read-only
- `DW-003` separate-directory exact-stem YOLO normalization remains green
- `DW-004` the task-doc gate passes on `tasks/real-dataset-yolo-ingest/`
- `DW-005` pytest coverage proves the new pairing mode and mixed-directory case
- `DW-006` docs record both the delivered ingest slice and the deferred
  zero-annotation review gap

## Changes

- `CHG-001` extend `YoloSource` and YOLO ingest helpers with an explicit pairing
  mode
- `CHG-002` make `normalize_yolo_source()` resolve image and label stems through
  the selected pairing mode while preserving deterministic output
- `CHG-003` expose the pairing mode through `normalize-yolo`
- `CHG-004` add ingest and CLI regression tests for mixed-directory hash pairs
  and preserved zero-label images
- `CHG-005` synchronize prompt, roadmap, and task evidence with the real
  dataset findings

## Coverage

- `COV-001` `src/yolo_label_validation/ingest.py` ->
  `YoloSource`, `normalize_yolo_source()`, image/label key resolution helpers
- `COV-002` `src/yolo_label_validation/cli.py` ->
  `build_parser()`, `_handle_normalize_yolo()`
- `COV-003` `tests/test_ingest.py` -> mixed-directory hash-pair normalization
  and CLI regression path
- `COV-004` `docs/prompt.md`, `docs/plan.md`,
  `tasks/real-dataset-yolo-ingest/documentation.md` -> evidence and active
  milestone synchronization

## Validation Plan

- `TC-001` existing exact-stem YOLO fixture normalization still produces the
  same canonical annotations and manifest
- `TC-002` a mixed-directory fixture with `__hash` image/label suffixes
  normalizes successfully when the new pairing mode is selected
- `TC-003` unlabeled images in the mixed-directory fixture remain in
  `image_index.json` with `annotation_count = 0`
- `TC-004` CLI normalization succeeds for the mixed-directory fixture
- `TC-005` the real dataset path normalizes successfully with
  `--pairing-mode stem_before_double_underscore`
- `TC-006` the task-doc gate passes on `tasks/real-dataset-yolo-ingest/`

- `T-001` `uv run pytest -q tests/test_ingest.py`
- `T-002` `uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest`
- `T-003` `uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\\workspace\\cigarette-identify\\预标注测试\\20264010" --labels-dir "E:\\workspace\\cigarette-identify\\预标注测试\\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite`
