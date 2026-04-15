# Documentation - Real Dataset Full Flow Run

## Readiness Gate

- `DG-001` required repo docs exist: pass
- `DG-002` required task docs exist: pass
- `DG-003` no placeholder markers remain: pass
- `DG-004` active task-doc gate command passes: pass

## Failure Loop

### FAIL-001
- Trigger: downstream stage execution after shard merge
- Observed failure: `run-materialize` first reported `patch_count: 0` even
  though `run-decision` had already produced `576` patches
- Root-cause hypothesis: `run-materialize` was started in parallel with
  upstream stages and read stale artifacts before the new `patches.json` had
  been written
- Confirmation:
  - `run-decision` reported `patch_count: 576`
  - `run-materialize` reported `patch_count: 0`
  - `patches.json` contained `576` records after `run-decision`
- Fix: rerun downstream stages in dependency order
- Retest:
  - `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite`
  - `uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/real-full-flow --overwrite`
- Status: closed

## Log

### Entry: 2026-04-13 / DOC-001
- Scope: created a dedicated task record for the real-dataset end-to-end run
- Evidence: `tasks/real-dataset-full-flow-run/`
- Result: pass

### Entry: 2026-04-13 / DOC-002
- Scope: passed the task-doc gate for the real full-flow execution task
- Evidence: `uv run python scripts/check_task_docs.py tasks/real-dataset-full-flow-run`
- Result: pass

### Entry: 2026-04-13 / DOC-003
- Scope: completed normalization, rules, and risk on the dedicated real run
- Evidence:
  - run dir: `artifacts/runs/real-full-flow/`
  - normalization: `520` images, `1088` annotations, `1` class
  - rules: `9` rule issues
  - risk: `1333` risk rows and `273` candidate images
  - expected VLM requests from `review_candidates.json`: `289`
    (`245` image-level + `44` annotation-level)
- Result: pass

### Entry: 2026-04-13 / DOC-004
- Scope: started the real local Codex VLM stage using 4 balanced shards to
  reduce wall-clock time
- Evidence:
  - shards:
    - `artifacts/runs/real-full-flow-shard-01/` with `73` expected requests
    - `artifacts/runs/real-full-flow-shard-02/` with `72` expected requests
    - `artifacts/runs/real-full-flow-shard-03/` with `72` expected requests
    - `artifacts/runs/real-full-flow-shard-04/` with `72` expected requests
  - launched processes recorded in
    `artifacts/runs/real-full-flow-vlm-jobs.json`
- Result: in progress
- Notes: `run-vlm` only writes its summary artifacts after a shard finishes, so
  early progress is visible through process liveness rather than artifact file
  growth

### Entry: 2026-04-13 / DOC-005
- Scope: completed the real local Codex VLM stage by merging 4 finished shard
  runs back into the main run directory
- Evidence:
  - merged `289` records into `artifacts/runs/real-full-flow/vlm_requests.jsonl`
  - merged `289` records into
    `artifacts/runs/real-full-flow/vlm_raw_responses.jsonl`
  - merged `289` records into
    `artifacts/runs/real-full-flow/vlm_review.json`
  - shard completion totals:
    - `73` reviews from shard 01
    - `72` reviews from shard 02
    - `72` reviews from shard 03
    - `72` reviews from shard 04
- Result: pass

### Entry: 2026-04-13 / DOC-006
- Scope: completed the real downstream stages after VLM review
- Evidence:
  - `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/real-full-flow --overwrite`
  - `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite`
  - `uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/real-full-flow --overwrite`
  - final `run_summary.json` counts:
    - `1654` decision results
    - `576` patches
    - `33` manual-review items
    - `565` missing results
    - `20` refine results
  - final patch breakdown:
    - `565` add
    - `11` refine
  - final decision breakdown:
    - `1045` keep
    - `565` add
    - `11` refine
    - `33` manual_review
  - materialized output dir:
    `artifacts/runs/real-full-flow/materialized_dataset/`
- Result: pass

### Entry: 2026-04-13 / DOC-007
- Scope: closed the real full-flow run task with final validation
- Evidence:
  - `uv run python scripts/check_task_docs.py tasks/real-dataset-full-flow-run`
  - `run_summary.metrics.patch_traceability_rate.value = 1.0`
  - `run_summary.metrics.manual_review_coverage.value = 0.019952`
- Result: pass
