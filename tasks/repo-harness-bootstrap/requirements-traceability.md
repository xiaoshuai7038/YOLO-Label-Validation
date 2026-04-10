# Requirements Traceability - Repo Harness Bootstrap

This matrix tracks the harness-foundation requirements, not the full product
delivery requirements from `docs/srs_v1.md`.

| Req ID | Requirement | Design / Doc | Test / Validation | Status |
|---|---|---|---|---|
| `REQ-001` | Repo has stable navigation docs and active execution-plan mapping | `AGENTS.md`, `PLANS.md`, `docs/plan.md` | `TC-004`, `TC-005` | validated |
| `REQ-002` | Canonical artifact contracts are frozen for core run files | `schemas/`, `contracts.py` | `TC-001` | validated |
| `REQ-003` | A bootstrap CLI initializes a canonical run workspace | `bootstrap.py`, `cli.py` | `TC-001` | validated |
| `REQ-004` | Task docs can be scaffolded and validated with a gate | `task_docs.py`, `doc_check.py`, `scripts/` | `TC-002`, `TC-003`, `TC-004` | validated |
| `REQ-005` | Local quality gates are mirrored in CI | `.github/workflows/ci.yml` | `TC-005` | validated |
| `REQ-006` | Product SRS implementation remains explicitly deferred beyond foundation closure | `docs/prompt.md`, `docs/plan.md`, `contract.md` | doc inspection | validated |
