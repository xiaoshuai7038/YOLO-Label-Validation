# Plan - Zero Annotation Image Review

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | record the root cause and guardrail in docs | completed |
| `M-002` | add explicit image-level review candidates and VLM request scope | completed |
| `M-003` | route image-level missing review through detector and decision layers | completed |
| `M-004` | validate targeted regressions and sync milestone docs | completed |

## Validation Route

1. `TC-006` / `T-001`: task-doc gate passes before code edits
2. `TC-001` / `T-002`: risk stage emits image-level candidates for empty images
3. `TC-003` / `T-002`: VLM request/review artifacts distinguish review scope
4. `TC-004` / `T-002`: detector and decision stages preserve image-level
   missing traceability
5. `TC-005` / `T-002`: image-level uncertain cases survive into manual review
6. `TC-007` / `T-003`: full regression suite stays green
7. `TC-008` / `T-004`: a real local Codex mini-run produces image-level
   review, missing, decision, and patch artifacts

## Exit Conditions

- review universe is explicitly image-based in the harness logic
- zero-annotation images are not silently skipped
- the root cause and guardrail are documented in reusable repo docs
