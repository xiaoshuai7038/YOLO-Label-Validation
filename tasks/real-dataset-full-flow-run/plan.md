# Plan - Real Dataset Full Flow Run

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | establish the dedicated real-run workspace and normalize inputs | completed |
| `M-002` | complete rules and risk on the real run | completed |
| `M-003` | complete local Codex VLM review on the real candidate set | completed |
| `M-004` | complete detector refine, decision, and materialization | completed |
| `M-005` | record evidence and close the run task | completed |

## Validation Route

1. `TC-006` / `T-001`: task-doc gate passes before running the pipeline
2. `TC-001` / `T-002`: normalization reproduces the known image and annotation
   counts
3. `TC-002` / `T-003` + `T-004`: rules and risk complete with explicit
   candidate counts
4. `TC-003` / `T-005`: local Codex review completes and writes `vlm_*`
   artifacts
5. `TC-004` / `T-006` + `T-007`: downstream stages preserve lineage into
   missing, decision, patch, and manual-review artifacts
6. `TC-005` / `T-008`: materialization completes and produces final run-level
   summary artifacts

## Exit Conditions

- the real run exists under `artifacts/runs/real-full-flow/`
- every stage from normalization through materialization completes or leaves a
  concrete, documented blocker
- the task documentation records the final counts and artifact paths
