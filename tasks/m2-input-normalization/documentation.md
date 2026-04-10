# Documentation - M2 Input Normalization

## Readiness Gate

- `DG-001` required repo docs were read in `AGENTS.md` order: pass
- `DG-002` M2-specific discovery, needs, contract, plan, implement, and
  documentation docs exist: pass
- `DG-003` optional M2 closure docs exist and are task-specific: pass
- `DG-004` placeholder markers removed from task docs: pass
- `DG-005` active task-doc gate command passes: pass

## Log

### Entry: 2026-04-10 / DOC-001
- Scope: audited the repository after bootstrap completion and confirmed that
  `ingest.py`, M2 normalization tests, and M2 schemas were still missing.
- Evidence: `README.md`, `docs/prompt.md`, `docs/plan.md`,
  `docs/exec-plans/active/EP-001-bootstrap-and-ingest.md`,
  `src/yolo_label_validation/`
- Result: pass

### Entry: 2026-04-10 / DOC-002
- Scope: confirmed the shell-level `python` command is a non-working Windows
  Store shim and switched the execution path for this task to `uv run ...`.
- Evidence: `uv run python --version`, `uv run pytest -q`
- Result: pass

### Entry: 2026-04-10 / DOC-003
- Scope: rewrote the scaffolded M2 task docs so they reflect FR-001/FR-002
  instead of the earlier bootstrap milestone.
- Evidence: `tasks/m2-input-normalization/`
- Result: pass

### Entry: 2026-04-10 / DOC-004
- Scope: run the M2 task-doc gate before code edits.
- Evidence: `uv run python scripts/check_task_docs.py tasks/m2-input-normalization`
- Result: pass

### Entry: 2026-04-10 / DOC-005
- Scope: implemented the M2 normalization slice with a new `ingest.py`
  module, manifest extensions, CLI normalization subcommands, and frozen
  artifact schemas for normalized annotations, image index, and class map.
- Evidence: `src/yolo_label_validation/ingest.py`,
  `src/yolo_label_validation/contracts.py`,
  `src/yolo_label_validation/cli.py`,
  `schemas/normalized_annotation.schema.json`,
  `schemas/image_index.schema.json`,
  `schemas/class_map.schema.json`,
  `schemas/run_manifest.schema.json`
- Result: pass

### Entry: 2026-04-10 / DOC-006
- Scope: validated the M2 slice with regression tests, the task-doc gate, and
  focused CLI smoke runs for both source formats.
- Evidence: `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/m2-input-normalization`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id smoke-yolo ...`,
  `uv run python scripts/run_cli.py normalize-coco --run-id smoke-coco ...`
- Result: pass
