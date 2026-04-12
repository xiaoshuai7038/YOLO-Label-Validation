# plan.md - Milestone Board

Current milestone marked with `->` when one is active.

## Milestone Overview

| ID | Title | Status | Depends On |
|---|---|---|---|
| M1 | Bootstrap harness docs, schemas, and run scaffold | completed | none |
| M2 | Build FR-001/FR-002 input normalization and run manifests | completed | M1 |
| M3 | Build FR-003/FR-004/FR-005 golden set, rules, and thresholds | completed | M2 |
| M4 | Build FR-006/FR-007/FR-008/FR-009 risk, VLM review, and decision engine | completed | M3 |
| M5 | Build FR-010/FR-011/FR-012/FR-013/FR-015/FR-016 detector refine, CVAT, materialization, and ops | completed | M4 |
| M6 | Build production VLM and detector integrations plus runtime config | completed | M5 |

---

## Completed Through M6

M1 through M6 are implemented. The repository now reaches `slice` closure for
the production-integration target: live runtime code paths exist, the config is
centralized, tests are green, and CLI smoke is mock-backed rather than
fixture-only.

---

## M6 Completed: Build production VLM and detector integrations plus runtime config

**Goal**: replace the former VLM fixture path and detector stub path with
production-oriented runtime integrations while keeping the same artifact
contracts and deterministic offline tests.

**Scope**: runtime integration config, live VLM transport, live detector
inference, version/config propagation, docs, and tests

**Deliverables**:
- [x] load one runtime config file that centralizes user-decided integration parameters
- [x] execute real OpenAI-compatible multimodal VLM requests from local run data
- [x] execute real Ultralytics detector inference for refine/add proposals
- [x] preserve fixture mode and green regression for offline development

**Verification**:

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration
```

**Result**:
- live integration code paths are implemented and test-covered
- runtime configuration is explicit and auditable
- no automatic action loses traceability or reason codes
- all verification commands pass
- remaining gap is limited to true credentialed runtime smoke with external
  secrets and weights

---

## Next

No active repository milestone is open. Any further work belongs to
environment-specific live validation or future scope expansion.

---

## Promotion Rules

A milestone is done when:

1. All deliverables are checked off
2. All verification commands pass
3. No quality gate regressions exist
4. Results are recorded in `docs/documentation.md`

After promotion:

1. Move `->` to the next milestone
2. Update `docs/prompt.md`
3. Move or refresh the active execution plan in `docs/exec-plans/`
