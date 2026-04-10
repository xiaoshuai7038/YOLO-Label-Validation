from __future__ import annotations

from pathlib import Path


REQUIRED_CONTEXT_DOCS: tuple[str, ...] = (
    "discovery-report.md",
    "needs-manifest.md",
)

REQUIRED_TASK_DOCS: tuple[str, ...] = (
    "contract.md",
    "plan.md",
    "implement.md",
    "documentation.md",
)

OPTIONAL_TASK_DOCS: tuple[str, ...] = (
    "requirements-traceability.md",
    "business-process-map.md",
    "uat-matrix.md",
)


def ensure_text(path: Path, content: str, overwrite: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return True


def render_discovery_report(task_slug: str) -> str:
    return f"""# Discovery Report

## Task

- Task slug: `{task_slug}`

## Confirmed

- Repository mode: harness-first Python scaffold
- Current entrypoints: `pytest -q`, `python scripts/run_cli.py show-layout`,
  `python scripts/run_cli.py init-run --run-id <id> --output-dir <dir>`
- Stable docs live in `docs/`
- Task execution docs live in `tasks/{task_slug}/`

## Existing Documentation Health

| File | Status | Action |
|---|---|---|
| `README.md` | healthy | keep |
| `AGENTS.md` | healthy | keep |
| `docs/project_spec.md` | healthy | keep |
| `docs/prompt.md` | healthy | keep |
| `docs/plan.md` | healthy | keep |

## Notes

- Update this report when command discovery or doc mapping changes.
"""


def render_needs_manifest(task_slug: str) -> str:
    return f"""# Needs Manifest

## Task

- Task slug: `{task_slug}`

## Blocking Needs

- None currently.

## Non-Blocking Needs

- Real sample datasets for FR-001 fixture expansion
- Real service credentials for VLM or CVAT integrations in later milestones

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| Golden set payloads | not required for harness bootstrap | M3 |
| Cleanlab/FiftyOne runtime wiring | not required for harness bootstrap | M4 |
| Detector B weights and configs | not required for harness bootstrap | M5 |
"""


def render_contract(task_name: str, task_slug: str) -> str:
    return f"""# Contract - {task_name}

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
- Meaning: the delivery harness is operational and validated, but the product
  requirements in `docs/srs_v1.md` are not yet fully implemented

## Done When

- `DW-001` repo docs, task docs, and execution-plan docs are synchronized
- `DW-002` reusable doc-scaffolding scripts create the required files
- `DW-003` the task-doc gate passes on `tasks/{task_slug}/`
- `DW-004` automated tests and local CLI checks pass
- `DW-005` CI workflow captures the same quality gates

## Changes

- `CHG-001` add durable task-doc structure under `tasks/{task_slug}/`
- `CHG-002` add reusable context-doc and task-doc scaffold scripts
- `CHG-003` add a task-doc validation gate script
- `CHG-004` extend tests to cover the doc gate and scaffold automation
- `CHG-005` add CI wiring for the local quality gates

## Coverage

- `COV-001` `scripts/init_context_docs.py` -> `scaffold_context_docs()`
- `COV-002` `scripts/init_task_docs.py` -> `scaffold_task_docs()`
- `COV-003` `scripts/check_task_docs.py` -> `run_task_doc_check()`
- `COV-004` `tests/test_bootstrap.py` -> bootstrap CLI validation path
- `COV-005` `tests/test_task_docs.py` -> doc scaffold and gate validation path
- `COV-006` `.github/workflows/ci.yml` -> repository quality gate automation

## Validation Plan

- `TC-001` bootstrap CLI still creates canonical run artifacts
- `TC-002` context-doc scaffolding creates the expected files
- `TC-003` task-doc scaffolding creates the expected files, including optional
  matrices when requested
- `TC-004` task-doc gate accepts the real task docs in `tasks/{task_slug}/`
- `TC-005` CI workflow references the same test and doc-gate commands

- `T-001` `pytest -q`
- `T-002` `python scripts/check_task_docs.py tasks/{task_slug}`
- `T-003` `python scripts/run_cli.py show-layout`
"""


def render_task_plan(task_name: str, task_slug: str) -> str:
    return f"""# Plan - {task_name}

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | establish repo and task doc layering | completed |
| `M-002` | add doc scaffold and task-doc gate scripts | completed |
| `M-003` | validate locally and wire the same checks into CI | completed |

## Validation Route

1. `TC-001` / `T-001`: bootstrap tests stay green
2. `TC-002` / `T-001`: context-doc scaffold tests stay green
3. `TC-003` / `T-001`: task-doc scaffold tests stay green
4. `TC-004` / `T-002`: task-doc gate passes on `tasks/{task_slug}/`
5. `TC-005` / `T-001`: CI workflow content is checked by tests

## Exit Conditions

- all `DW-*` items in `contract.md` are evidenced
- task docs stay free of placeholders
- next active product milestone remains M2 in `docs/prompt.md`
"""


def render_task_implement(task_name: str, task_slug: str) -> str:
    return f"""# Implement - {task_name}

## Execution Rules

- Keep harness changes deterministic and file-based.
- Prefer reusable scripts over one-off shell snippets.
- Keep repo-level docs aligned with task-level docs.
- Do not claim `slice` or `full` closure for product requirements.

## Iteration Loop

1. Read `AGENTS.md`, `docs/project_spec.md`, and `docs/prompt.md`
2. Read `tasks/{task_slug}/contract.md` and `tasks/{task_slug}/plan.md`
3. Implement one `CHG-*` item at a time
4. Run the smallest validating command first
5. Update `tasks/{task_slug}/documentation.md`
6. Re-run the quality gates before closing the task

## Verification Commands

```powershell
pytest -q
python scripts/check_task_docs.py tasks/{task_slug}
python scripts/run_cli.py show-layout
```

## Escalation

- Stop only if a required task doc cannot be made concrete without a user
  decision or external credentials.
- Any missing evidence blocks closure.
"""


def render_task_documentation(task_name: str, task_slug: str) -> str:
    return f"""# Documentation - {task_name}

## Readiness Gate

- `DG-001` required repo docs exist: pass
- `DG-002` required task docs exist: pass
- `DG-003` no placeholder markers remain: pass
- `DG-004` active task-doc gate command passes: pass

## Log

### Entry: 2026-04-10 / DOC-001
- Scope: created task-scoped discovery, needs, contract, plan, implement, and
  documentation docs under `tasks/{task_slug}/`
- Evidence: `tasks/{task_slug}/`
- Result: pass

### Entry: 2026-04-10 / DOC-002
- Scope: added reusable scaffold scripts and the doc gate
- Evidence: `scripts/init_context_docs.py`, `scripts/init_task_docs.py`,
  `scripts/check_task_docs.py`, `tests/test_task_docs.py`
- Result: pass

### Entry: 2026-04-10 / DOC-003
- Scope: validated harness quality gates and aligned CI
- Evidence: `pytest -q`, `python scripts/check_task_docs.py tasks/{task_slug}`
- Result: pending update by execution
"""


def render_requirements_traceability(task_name: str, task_slug: str) -> str:
    return f"""# Requirements Traceability - {task_name}

This matrix tracks the harness-foundation requirements, not the full product
delivery requirements from `docs/srs_v1.md`.

| Req ID | Requirement | Design / Doc | Test / Validation | Status |
|---|---|---|---|---|
| `REQ-001` | Repo has stable navigation docs and active execution-plan mapping | `AGENTS.md`, `PLANS.md`, `docs/plan.md` | `TC-004`, `TC-005` | validated |
| `REQ-002` | Canonical artifact contracts are frozen for core run files | `schemas/`, `contracts.py` | `TC-001` | validated |
| `REQ-003` | A bootstrap CLI initializes a canonical run workspace | `bootstrap.py`, `cli.py` | `TC-001` | validated |
| `REQ-004` | Task docs can be scaffolded and validated with a gate | `task_docs.py`, `doc_check.py`, `scripts/` | `TC-002`, `TC-003`, `TC-004` | validated |
| `REQ-005` | Local quality gates are mirrored in CI | `.github/workflows/ci.yml` | `TC-005` | validated |
| `REQ-006` | Product SRS implementation remains explicitly deferred beyond foundation closure | `docs/prompt.md`, `docs/plan.md`, `tasks/{task_slug}/contract.md` | doc inspection | validated |
"""


def render_business_process_map(task_name: str, task_slug: str) -> str:
    return f"""# Business Process Map - {task_name}

## FLOW-001 Start a repo-level delivery session

- Actor: engineer or coding agent
- Entry: open repository and read `AGENTS.md`
- Main path:
  1. read stable docs under `docs/`
  2. locate current work in `docs/prompt.md` and `PLANS.md`
  3. open task docs under `tasks/{task_slug}/`
- Exception path: if task docs are missing, scaffold them first
- Evidence: `TC-002`, `TC-003`, `TC-004`

## FLOW-002 Initialize a canonical audit run

- Actor: engineer or coding agent
- Entry: execute `python scripts/run_cli.py init-run ...`
- Main path:
  1. build canonical artifact layout
  2. write `run_manifest.json`
  3. write empty artifact placeholders
- Exception path: existing run directory without `--overwrite`
- Evidence: `TC-001`

## FLOW-003 Enforce the doc gate before major code edits

- Actor: engineer or CI
- Entry: execute `python scripts/check_task_docs.py tasks/{task_slug}`
- Main path:
  1. verify required files exist
  2. verify required headings exist
  3. reject placeholder markers
  4. accept the task docs if all checks pass
- Exception path: missing or weak docs block closure
- Evidence: `TC-004`, `TC-005`
"""


def render_uat_matrix(task_name: str, task_slug: str) -> str:
    return f"""# UAT Matrix - {task_name}

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | A new engineer can discover the repo control plane and current milestone | `FLOW-001` | `AGENTS.md`, `docs/prompt.md`, `PLANS.md`, `tasks/{task_slug}/discovery-report.md` | pass |
| `UAT-002` | A new task can be scaffolded into the required doc set | `FLOW-001` | `TC-002`, `TC-003` | pass |
| `UAT-003` | A canonical run workspace can be created locally | `FLOW-002` | `TC-001` | pass |
| `UAT-004` | The task-doc gate blocks weak docs and accepts valid docs | `FLOW-003` | `TC-004` | pass |
| `UAT-005` | CI mirrors the local harness quality gates | `FLOW-003` | `TC-005` | pass |
"""


def scaffold_context_docs(
    workspace: Path,
    task_slug: str,
    overwrite: bool = False,
) -> list[Path]:
    task_dir = workspace / "tasks" / task_slug
    created: list[Path] = []

    mapping = {
        "discovery-report.md": render_discovery_report(task_slug),
        "needs-manifest.md": render_needs_manifest(task_slug),
    }

    for filename, content in mapping.items():
        path = task_dir / filename
        if ensure_text(path, content, overwrite=overwrite):
            created.append(path)

    return created


def scaffold_task_docs(
    workspace: Path,
    task_name: str,
    task_slug: str,
    overwrite: bool = False,
    include_requirements_traceability: bool = False,
    include_business_process_map: bool = False,
    include_uat_matrix: bool = False,
) -> list[Path]:
    task_dir = workspace / "tasks" / task_slug
    created: list[Path] = []

    mapping = {
        "contract.md": render_contract(task_name, task_slug),
        "plan.md": render_task_plan(task_name, task_slug),
        "implement.md": render_task_implement(task_name, task_slug),
        "documentation.md": render_task_documentation(task_name, task_slug),
    }

    if include_requirements_traceability:
        mapping["requirements-traceability.md"] = render_requirements_traceability(
            task_name,
            task_slug,
        )
    if include_business_process_map:
        mapping["business-process-map.md"] = render_business_process_map(
            task_name,
            task_slug,
        )
    if include_uat_matrix:
        mapping["uat-matrix.md"] = render_uat_matrix(task_name, task_slug)

    for filename, content in mapping.items():
        path = task_dir / filename
        if ensure_text(path, content, overwrite=overwrite):
            created.append(path)

    return created
