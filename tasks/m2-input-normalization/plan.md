# Plan - M2 Input Normalization

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | rewrite the scaffolded task docs into M2-specific discovery, contract, and validation artifacts | completed |
| `M-002` | implement YOLO txt and COCO JSON normalization plus class-map merging and lineage capture | completed |
| `M-003` | wire deterministic artifact writers and CLI entrypoints for the M2 slice | completed |
| `M-004` | validate with pytest, task-doc gate, and focused CLI checks; then sync repo docs and milestone status | completed |

## Validation Route

1. `TC-006` / `T-002`: M2 task docs pass the doc gate before code edits
2. `TC-001` / `T-001`: YOLO txt normalization passes fixture tests
3. `TC-002` / `T-001`: COCO JSON normalization passes fixture tests
4. `TC-003` / `T-001`: class-map conflict paths fail fast with explicit errors
5. `TC-004` / `T-001`: deterministic artifact output is proven in tests
6. `TC-005` / `T-001`: CLI integration covers run-manifest fidelity
7. Regression: repository quality gates remain green after M2 changes

## Exit Conditions

- all `DW-*` rows in `contract.md` are backed by test or CLI evidence
- `docs/prompt.md`, `docs/plan.md`, `PLANS.md`, and `docs/documentation.md`
  reflect the implemented M2 state
- no unresolved `FAIL-*` row remains open in `documentation.md`
