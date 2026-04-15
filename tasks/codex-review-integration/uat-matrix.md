# UAT Matrix - Codex Review Integration

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | An operator can point the review stage at a local Codex runtime without renaming the `run-vlm` command or `vlm_*` artifacts | `FLOW-001` | `TC-001`, config and CLI inspection | pass |
| `UAT-002` | A risky annotation can be sent to local Codex with image input and return a parsed `vlm_review.json` record | `FLOW-002` | `TC-002`, mocked local runner capture, `vlm_review.json` assertions | pass |
| `UAT-003` | A malformed local Codex response is rejected before it reaches decision routing | `FLOW-002` | `TC-003`, negative test assertions | pass |
| `UAT-004` | Existing fixture mode and legacy HTTP transports continue to work after the provider extension | `FLOW-001`, `FLOW-003` | `TC-004`, regression assertions in `tests/test_vlm.py` | pass |
| `UAT-005` | The active milestone and task evidence reflect this integration at `slice` closure | `FLOW-003` | `TC-005`, `docs/prompt.md`, `docs/plan.md`, `PLANS.md`, `docs/documentation.md` | pass |
