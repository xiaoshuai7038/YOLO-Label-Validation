# Implement - Codex Review Integration

## Execution Rules

- Preserve the existing `vlm_*` artifact names and `run-vlm` command for this
  task.
- Keep source images and labels read-only; only the run workspace artifacts may
  change.
- Prefer one provider-extension seam in `vlm.py` over widespread renames across
  downstream modules.
- Keep fixture mode and the legacy HTTP provider paths working while adding
  local Codex CLI support.

## Iteration Loop

1. Read `AGENTS.md`, `docs/prompt.md`, `docs/plan.md`, and
   `docs/documentation.md`
2. Read `tasks/codex-review-integration/contract.md` and
   `tasks/codex-review-integration/plan.md`
3. Pass `uv run python scripts/check_task_docs.py tasks/codex-review-integration`
   before touching code
4. Implement `CHG-001` and `CHG-002` first in `runtime_config.py`,
   `schemas/runtime_integration.schema.json`, and `vlm.py`
5. Update `configs/runtime.integration.json`, tests, and docs for `CHG-003`
   through `CHG-005`
6. Run targeted validation first, then full regression, then update
   `tasks/codex-review-integration/documentation.md`

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/codex-review-integration
uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py
uv run pytest -q
```

## Escalation

- Stop only if a required behavior would force a breaking rename of frozen
  artifacts or CLI entrypoints.
- Treat any ambiguity about local Codex CLI flags or output handling as a local
  CLI inspection task before changing code.
