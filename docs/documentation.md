# documentation.md - Experiment & Change Log

Record every meaningful change here. Keep only the most recent entries in this
file and archive older ones if needed.

## Log

### Iteration: 2026-04-10
- **Milestone**: M1
- **Change**: initialized the repository as a harness-first project with docs,
  schemas, config defaults, and a bootstrap CLI for run workspaces
- **Files modified**: repository scaffold
- **Verification result**: pass (`pytest -q`, `python scripts/run_cli.py show-layout`,
  `python scripts/run_cli.py init-run --run-id smoke-run --output-dir artifacts\runs\smoke-run`)
- **Decision**: continue
- **Next step**: implement FR-001/FR-002 input normalization and source lineage

### Iteration: 2026-04-10
- **Milestone**: M1 hardening
- **Change**: added task-scoped execution docs, reusable doc scaffold scripts,
  a task-doc gate, and CI wiring for the same local quality gates
- **Files modified**: `tasks/`, `scripts/init_context_docs.py`,
  `scripts/init_task_docs.py`, `scripts/check_task_docs.py`,
  `src/yolo_label_validation/task_docs.py`,
  `src/yolo_label_validation/doc_check.py`, `.github/workflows/ci.yml`,
  `tests/test_task_docs.py`
- **Verification result**: pass (`pytest -q`,
  `python scripts\check_task_docs.py tasks\repo-harness-bootstrap`,
  `python scripts\run_cli.py show-layout`)
- **Decision**: continue
- **Next step**: start FR-001/FR-002 ingestion implementation with fixture data

### Iteration: 2026-04-10
- **Milestone**: M1 hardening
- **Change**: fixed GitHub Actions CI by declaring a `test` extra in
  `pyproject.toml` and installing `.[test]` before running `python -m pytest`
- **Files modified**: `pyproject.toml`, `.github/workflows/ci.yml`
- **Verification result**: pass (`python -m pip install -e ".[test]"`,
  `python -m pytest -q`, `python scripts\check_task_docs.py tasks\repo-harness-bootstrap`)
- **Decision**: continue
- **Next step**: wait for GitHub Actions to rerun with the updated workflow
