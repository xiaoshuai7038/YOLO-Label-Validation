# Plan - Codex Review Integration

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | rewrite task docs for the local Codex review integration and pass the doc gate | completed |
| `M-002` | extend runtime config and `vlm.py` with local Codex CLI support while preserving legacy behavior | completed |
| `M-003` | add regression coverage, update example config, and sync roadmap/docs | completed |

## Validation Route

1. `TC-005` / `T-003`: task docs pass the gate before code edits
2. `TC-001` / `T-001`: runtime config tests cover the new provider shape
3. `TC-002` `TC-003` / `T-001`: local Codex transport and parser coverage
   pass
4. `TC-004` / `T-001`: fixture mode and legacy live-chat coverage remain green
5. `TC-001` `TC-002` `TC-003` `TC-004` / `T-002`: full regression passes
6. roadmap, prompt, plans, and documentation logs are synchronized

## Exit Conditions

- all `DW-*` items in `contract.md` are evidenced
- `tasks/codex-review-integration/` passes the task-doc gate
- `run-vlm` still writes the frozen `vlm_*` artifacts after the provider swap
- the achieved closure level remains `slice` until external credentialed smoke
  exists
