# Implement - Repo Harness Bootstrap

## Execution Rules

- Keep harness changes deterministic and file-based.
- Prefer reusable scripts over one-off shell snippets.
- Keep repo-level docs aligned with task-level docs.
- Do not claim `slice` or `full` closure for product requirements.

## Iteration Loop

1. Read `AGENTS.md`, `docs/project_spec.md`, and `docs/prompt.md`
2. Read `tasks/repo-harness-bootstrap/contract.md` and `plan.md`
3. Implement one `CHG-*` item at a time
4. Run the smallest validating command first
5. Update `tasks/repo-harness-bootstrap/documentation.md`
6. Re-run the quality gates before closing the task

## Verification Commands

```powershell
pytest -q
python scripts/check_task_docs.py tasks/repo-harness-bootstrap
python scripts/run_cli.py show-layout
```

## Escalation

- Stop only if a required task doc cannot be made concrete without a user
  decision or external credentials.
- Any missing evidence blocks closure.
