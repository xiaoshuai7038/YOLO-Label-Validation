# Implement - Production VLM Detector Integration

## Execution Rules

- Keep artifact contracts deterministic and file-based.
- Keep fixture mode available for offline tests even after live integrations are added.
- Use env-var indirection for secrets and keep user-decision parameters in one committed config file.
- Keep repo-level docs aligned with task-level docs.
- Do not claim more than `slice` closure unless live credentialed execution is actually evidenced.

## Iteration Loop

1. Read `AGENTS.md`, `docs/project_spec.md`, and `docs/prompt.md`
2. Read `tasks/production-vlm-detector-integration/contract.md` and `tasks/production-vlm-detector-integration/plan.md`
3. Implement one `CHG-*` item at a time
4. Run the smallest validating command first
5. If a live path fails, record a `FAIL-*` row before or alongside the fix
6. Update `tasks/production-vlm-detector-integration/documentation.md`
7. Re-run the quality gates before closing the task

## Verification Commands

```powershell
uv run pytest -q
uv run pytest -q tests/test_vlm.py tests/test_detector_refine.py
uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration
```

## Escalation

- Stop only if a required task doc cannot be made concrete without a user
  decision or external credentials.
- Any missing evidence blocks closure.
- Missing secrets or weights are not blockers for mocked validation, but they
  are blockers for claiming live credentialed execution.
