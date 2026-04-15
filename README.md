# YOLO Label Validation Harness

Harness-first repository for auditing and patching YOLO prelabels for 2D
object detection tasks.

The repository is initialized around a patch-first workflow:

1. Normalize raw annotations into one internal contract.
2. Run static validation and threshold-based checks.
3. Rank risky images and boxes.
4. Review risky cases with a provider-configurable multimodal review model.
5. Refine geometry with a closed-set detector.
6. Escalate uncertain or conflicting cases to humans.
7. Emit patches and materialized dataset versions without touching source labels.

## Current Status

- `AGENTS.md`, `PLANS.md`, and `docs/` establish the harness engineering
  control plane.
- `tasks/` stores task-scoped discovery, contract, plan, and validation memory.
- `schemas/` freezes the minimum JSON contracts for `run_manifest`,
  `review_candidates`, `vlm_review`, and `patches`.
- `src/yolo_label_validation/` contains a minimal bootstrap CLI that creates
  canonical run artifact files for a new audit run.
- `normalize-yolo` now supports explicit pairing modes so real-world YOLO
  datasets with mixed image/label directories and trailing `__hash` filename
  suffixes can be normalized without renaming source files.
- zero-annotation images now become explicit image-level review candidates
  instead of being silently skipped by the semantic-review pipeline.
- materialized runs can now be exported as a ready-to-use YOLO dataset with
  copied images, labels, `classes.txt`, and `dataset.yaml`.
- `configs/runtime.integration.json` now demonstrates a local `codex exec`
  based live review runtime while preserving the historical `vlm_*` artifact
  contracts, with a timeout baseline that is practical for real image review.
- `scripts/init_context_docs.py`, `scripts/init_task_docs.py`, and
  `scripts/check_task_docs.py` make the harness reusable for future tasks.
- `tests/` verifies the scaffold, task-doc gate, and bootstrap logic.

## Quickstart

Use the repository `uv` environment.

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review
uv run python scripts/run_cli.py show-layout
uv run python scripts/run_cli.py init-run --run-id local-smoke --output-dir artifacts/runs/local-smoke
```

## Repository Layout

- `AGENTS.md` - entrypoint and guardrails for Codex or other coding agents
- `PLANS.md` - live execution-plan index
- `configs/` - frozen defaults and threshold examples
- `docs/` - stable spec, roadmap, active milestone, architecture, and logs
- `tasks/` - task-scoped discovery, contract, plan, and validation memory
- `schemas/` - canonical JSON schemas for core artifacts
- `scripts/` - local wrappers for running the scaffold CLI
- `src/yolo_label_validation/` - bootstrap code and data contracts
- `tests/` - smoke tests for scaffold behavior

## Source of Truth

- Product requirements: `docs/srs_v1.md`
- Stable project contract: `docs/project_spec.md`
- Current milestone: `docs/prompt.md`
- Milestone roadmap: `docs/plan.md`
- Active execution plan: `PLANS.md`
- Latest completed harness task: `tasks/zero-annotation-image-review/contract.md`
