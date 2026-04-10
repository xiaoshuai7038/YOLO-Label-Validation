# Business Process Map - Repo Harness Bootstrap

## FLOW-001 Start a repo-level delivery session

- Actor: engineer or coding agent
- Entry: open repository and read `AGENTS.md`
- Main path:
  1. read stable docs under `docs/`
  2. locate current work in `docs/prompt.md` and `PLANS.md`
  3. open task docs under `tasks/repo-harness-bootstrap/`
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
- Entry: execute `python scripts/check_task_docs.py tasks/repo-harness-bootstrap`
- Main path:
  1. verify required files exist
  2. verify required headings exist
  3. reject placeholder markers
  4. accept the task docs if all checks pass
- Exception path: missing or weak docs block closure
- Evidence: `TC-004`, `TC-005`
