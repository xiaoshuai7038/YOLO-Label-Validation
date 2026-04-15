# Plan - Real Dataset YOLO Ingest Adapter

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | capture real dataset facts, failure evidence, and task boundaries | completed |
| `M-002` | implement configurable YOLO pairing for mixed-directory `__hash` datasets | completed |
| `M-003` | validate fixture regressions, real-dataset CLI smoke, and sync docs | completed |

## Validation Route

1. `TC-006` / `T-002`: task-doc gate passes before code edits
2. `TC-001` / `T-001`: existing YOLO fixture behavior stays unchanged
3. `TC-002` / `T-001`: mixed-directory `__hash` fixture normalizes successfully
4. `TC-003` / `T-001`: mixed-directory unlabeled image remains in the image index
5. `TC-004` / `T-001`: CLI path exposes and honors the new pairing mode
6. `TC-005` / `T-003`: real dataset normalization smoke succeeds

## Exit Conditions

- all `DW-*` items in `contract.md` are evidenced
- the real dataset no longer requires manual file renaming to normalize
- docs explicitly state that zero-annotation image review is deferred
