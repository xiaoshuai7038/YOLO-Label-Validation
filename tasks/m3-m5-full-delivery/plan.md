# Plan - M3-M5 Full Delivery

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | rewrite the scaffolded task docs and pass the doc gate | completed |
| `M-002` | implement M3 rules, thresholds, and golden-set contracts | completed |
| `M-003` | implement M4 risk, VLM, decision, patch, and manual-queue modules | completed |
| `M-004` | implement M5 refine/add, materialization, summary, and metrics modules | completed |
| `M-005` | run full regression and synchronize roadmap, plans, and status docs | completed |

## Validation Route

1. `TC-009` / `T-002`: task docs pass the gate before code edits
2. `TC-001` `TC-002` `TC-003` / `T-001`: M3 tests pass
3. `TC-004` `TC-005` `TC-006` / `T-001`: M4 tests pass
4. `TC-007` `TC-008` / `T-001`: M5 tests pass
5. full regression and focused smoke checks pass after milestone promotion

## Exit Conditions

- every `DW-*` row in `contract.md` is evidenced
- no open `FAIL-*` row remains in `documentation.md`
- `docs/plan.md`, `docs/prompt.md`, `PLANS.md`, execution plans, and
  `STATUS.md` match the delivered code state
