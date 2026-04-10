# Contract - Repo Harness Bootstrap

## Goal

Establish a reusable harness engineering foundation for this repository so that
future delivery work follows stable docs, task gates, validation rules, and
canonical run artifacts.

## Scope

- repo-level navigation and stable docs
- task-level discovery, contract, plan, implement, and documentation docs
- reusable scripts for scaffolding and validating task docs
- CI checks for bootstrap code and the task-doc gate

## Out of Scope

- Full implementation of FR-001 through FR-016 business functionality
- External tool integrations that need credentials or running services

## Closure Level

- Target closure: `foundation`
- Achieved closure must not be described as `slice` or `full`

## Done When

- `DW-001` repo docs, task docs, and execution-plan docs are synchronized
- `DW-002` reusable doc-scaffolding scripts create the required files
- `DW-003` the task-doc gate passes on `tasks/repo-harness-bootstrap/`
- `DW-004` automated tests and local CLI checks pass
- `DW-005` CI workflow captures the same quality gates

## Changes

- `CHG-001` add durable task-doc structure under `tasks/repo-harness-bootstrap/`
- `CHG-002` add reusable context-doc and task-doc scaffold scripts
- `CHG-003` add a task-doc validation gate script
- `CHG-004` extend tests to cover the doc gate and scaffold automation
- `CHG-005` add CI wiring for the local quality gates

## Coverage

- `COV-001` `scripts/init_context_docs.py` -> `scaffold_context_docs()`
- `COV-002` `scripts/init_task_docs.py` -> `scaffold_task_docs()`
- `COV-003` `scripts/check_task_docs.py` -> `run_task_doc_check()`
- `COV-004` `scripts/run_cli.py` -> bootstrap layout inspection path
- `COV-005` `tests/test_bootstrap.py` -> bootstrap CLI validation path
- `COV-006` `tests/test_task_docs.py` -> doc scaffold and gate validation path
- `COV-007` `.github/workflows/ci.yml` -> repository quality gate automation

## Validation Plan

- `TC-001` bootstrap CLI still creates canonical run artifacts
- `TC-002` context-doc scaffolding creates the expected files
- `TC-003` task-doc scaffolding creates the expected files, including optional
  matrices when requested
- `TC-004` task-doc gate accepts the real task docs in
  `tasks/repo-harness-bootstrap/`
- `TC-005` CI workflow references the same test and doc-gate commands

- `T-001` `pytest -q`
- `T-002` `python scripts/check_task_docs.py tasks/repo-harness-bootstrap`
- `T-003` `python scripts/run_cli.py show-layout`
