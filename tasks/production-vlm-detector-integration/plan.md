# Plan - Production VLM Detector Integration

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | rewrite task docs and pass the gate for the production integration task | completed |
| `M-002` | implement runtime config loader and live VLM transport | completed |
| `M-003` | implement live detector inference and downstream compatibility | completed |
| `M-004` | run regression, CLI validation, and sync docs | completed |

## Validation Route

1. `TC-006` / `T-003`: task docs pass the gate before code edits
2. `TC-001` `TC-002` `TC-003` / `T-001` `T-002`: runtime config and live VLM tests pass
3. `TC-004` `TC-005` / `T-001` `T-002`: live detector and downstream regression pass
4. focused mocked CLI smoke passes
5. roadmap, plans, and docs are synchronized

## Exit Conditions

- all `DW-*` items in `contract.md` are evidenced
- task docs stay free of placeholders
- `docs/prompt.md`, `docs/plan.md`, `PLANS.md`, and `STATUS.md` reflect the
  completed production integration task
