# Plan - Repo Harness Bootstrap

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | establish repo and task doc layering | completed |
| `M-002` | add doc scaffold and task-doc gate scripts | completed |
| `M-003` | validate locally and wire the same checks into CI | completed |

## Validation Route

1. `TC-001` / `T-001`: bootstrap tests stay green
2. `TC-002` / `T-001`: context-doc scaffold tests stay green
3. `TC-003` / `T-001`: task-doc scaffold tests stay green
4. `TC-004` / `T-002`: task-doc gate passes on
   `tasks/repo-harness-bootstrap/`
5. `TC-005` / `T-001`: CI workflow content is checked by tests

## Exit Conditions

- all `DW-*` items in `contract.md` are evidenced
- task docs stay free of placeholders
- next active product milestone remains M2 in `docs/prompt.md`
