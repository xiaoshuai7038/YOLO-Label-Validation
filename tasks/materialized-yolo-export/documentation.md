# Documentation - Materialized YOLO Export

## Readiness Gate

- `DG-001` required repo docs exist: pass
- `DG-002` required task docs exist: pass
- `DG-003` no placeholder markers remain: pass
- `DG-004` active task-doc gate command passes: pass

## Log

### Entry: 2026-04-14 / DOC-001
- Scope: created task docs for the YOLO export slice
- Evidence: `tasks/materialized-yolo-export/`
- Result: pass

### Entry: 2026-04-14 / DOC-002
- Scope: implemented a formal YOLO export path from a materialized run
- Evidence:
  - `src/yolo_label_validation/materialize.py`
  - `src/yolo_label_validation/cli.py`
  - `tests/test_materialize.py`
- Result: pass

### Entry: 2026-04-14 / DOC-003
- Scope: validated the YOLO export command with tests and a real run
- Evidence:
  - `uv run pytest -q tests/test_materialize.py`
  - `uv run pytest -q`
  - `uv run python scripts/check_task_docs.py tasks/materialized-yolo-export`
  - `uv run python scripts/run_cli.py export-yolo --run-dir artifacts/runs/real-full-flow --overwrite`
  - real export output:
    `artifacts/runs/real-full-flow/materialized_yolo/`
  - real export counts:
    - `520` copied images
    - `520` YOLO label files
    - `1653` final annotations
- Result: pass
