# PLAN

## Verification Checklist

- `uv run pytest -q`
- `uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration`
- focused CLI or module smoke checks for each milestone slice

## Milestones

| ID | Scope | Key Files | Acceptance |
|---|---|---|---|
| `LH-15` | durable-memory and task docs for production integration | `SPEC.md`, `PLAN.md`, `RULES.md`, `STATUS.md`, `tasks/production-vlm-detector-integration/*` | completed |
| `LH-16` | runtime integration config and loader | `configs/*`, `runtime_config.py`, `tests/*` | completed |
| `LH-17` | live VLM request execution | `vlm.py`, `cli.py`, `tests/test_vlm.py` | completed |
| `LH-18` | live detector inference | `detector_refine.py`, `cli.py`, `tests/test_detector_refine.py` | completed |
| `LH-19` | decision and manifest/runtime propagation | `decision.py`, `contracts.py`, `schemas/*`, `tests/*` | completed |
| `LH-20` | final docs sync and regression | `docs/*`, `PLANS.md`, `STATUS.md` | completed at `slice` closure |

## Architecture Notes

- `contracts.py` stays the canonical artifact registry and manifest contract
- each processing stage keeps its own module and tests
- fixture mode remains available for offline testing, but live integrations
  become first-class runtime paths
- CLI remains thin and delegates to module functions

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| false `full` closure claim while external services are mocked | high | document closure level honestly and name whether live credentials were actually exercised |
| secrets or machine-local paths leak into git | high | use env-var indirection and committed placeholder paths only |
| live integration breaks deterministic offline tests | high | preserve fixture mode and add explicit runtime-mode tests |
| oversized implementation diff causes cross-module bugs | medium | validate after each module slice and keep failure notes in task docs |

## Decision Log

- `2026-04-10`: use `uv run ...` as the canonical execution path because shell-level `python` is a broken Windows Store shim.
- `2026-04-10`: production integration parameters must live in one runtime
  config file, while secrets still come from environment variables.
- `2026-04-10`: fixture mode remains part of the supported contract even after
  live integrations are added.
- `2026-04-10`: M6 reached `slice` closure with mock-backed live VLM and live
  detector paths; true credentialed endpoint and weights execution remains an
  environment-side follow-up, not a repo-code gap.
