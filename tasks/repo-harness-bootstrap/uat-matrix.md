# UAT Matrix - Repo Harness Bootstrap

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | A new engineer can discover the repo control plane and current milestone | `FLOW-001` | `AGENTS.md`, `docs/prompt.md`, `PLANS.md`, `discovery-report.md` | pass |
| `UAT-002` | A new task can be scaffolded into the required doc set | `FLOW-001` | `TC-002`, `TC-003` | pass |
| `UAT-003` | A canonical run workspace can be created locally | `FLOW-002` | `TC-001` | pass |
| `UAT-004` | The task-doc gate blocks weak docs and accepts valid docs | `FLOW-003` | `TC-004` | pass |
| `UAT-005` | CI mirrors the local harness quality gates | `FLOW-003` | `TC-005` | pass |
