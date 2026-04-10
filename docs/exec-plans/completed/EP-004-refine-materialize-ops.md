# EP-004 Refine Materialize Ops

## Status

- Plan id: `EP-004`
- Milestone: `M5`
- State: completed

## Context

M4 now emits deterministic risk, VLM, decision, patch, and manual-review
artifacts. The final local milestone closes the loop with detector-backed
refine/add proposals, patch-applied materialization, run summaries, and
dashboard-ready metrics.

## Expected Outcome

- deterministic `refine_results.json` and `missing_results.json`
- patch-applied `materialized_dataset/` output under each run directory
- deterministic `run_summary.json` and `metrics_dashboard_source.json`

## Work Items

1. Implement detector-backed refine and missing-object proposal outputs.
2. Implement patch-applied materialization without source mutation.
3. Emit run summary and metrics artifacts.
4. Validate CLI entrypoints and full regression.

## Verification

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery
```

## Notes

- Source labels and images remain read-only.
- Materialization emits a derived dataset view inside the run workspace.
