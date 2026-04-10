# YOLO Label Validation Harness

Harness-first repository for auditing and patching YOLO prelabels for 2D
object detection tasks.

The repository is initialized around a patch-first workflow:

1. Normalize raw annotations into one internal contract.
2. Run static validation and threshold-based checks.
3. Rank risky images and boxes.
4. Review risky cases with a VLM.
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
- `scripts/init_context_docs.py`, `scripts/init_task_docs.py`, and
  `scripts/check_task_docs.py` make the harness reusable for future tasks.
- `tests/` verifies the scaffold, task-doc gate, and bootstrap logic.

## Quickstart

Use your project Python interpreter.

```powershell
pytest -q
python scripts/check_task_docs.py tasks/repo-harness-bootstrap
python scripts/run_cli.py show-layout
python scripts/run_cli.py init-run --run-id local-smoke --output-dir artifacts/runs/local-smoke
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
- Active harness task: `tasks/repo-harness-bootstrap/contract.md`
