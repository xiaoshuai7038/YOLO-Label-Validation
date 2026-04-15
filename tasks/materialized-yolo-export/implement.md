# Implement - Materialized YOLO Export

## Execution Rules

- preserve the existing internal materialization contract
- add the YOLO export as a separate derived output, not as a source mutation
- prefer deterministic filenames and manifests over ad-hoc shell export logic

## Iteration Loop

1. implement the smallest export helpers first
2. cover them with unit tests before the real export
3. validate the CLI path
4. run the real export and record counts and output paths

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/materialized-yolo-export
uv run pytest -q tests/test_materialize.py
uv run python scripts/run_cli.py export-yolo --run-dir artifacts/runs/real-full-flow --overwrite
```
