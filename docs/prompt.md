# prompt.md - Current Milestone Contract

This file describes only the current execution focus.
For the full roadmap, see `docs/plan.md`. For stable spec, see
`docs/project_spec.md`.

## Current Milestone: Closeout - Local roadmap completed through M5

## Scope

Keep the repository in a verified closeout state after the full local roadmap
delivery: normalization, rules, risk, VLM review, decision routing, detector
proposals, patch generation, materialization, and run-level summaries are now
implemented.

## In-Scope

- preserve the delivered artifact contracts and schema set
- keep M1-M5 regression and task-doc gates green
- maintain traceability, patch-only writes, and explicit reasons in all
  downstream outputs

## Non-Goals

- live external-service execution that requires credentials or remote state
- scope expansion beyond fixed-class 2D detection boxes

## Hard Constraints

- downstream code must consume normalized internal contracts, not raw source
  formats
- source images and source labels remain read-only
- every automatic decision or patch must include `reason` or `reason_code`
- no future change may reintroduce upstream artifact clobbering across stages

## Verification Commands

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery
```

## Required Evidence

- green regression for all modules from M1 through M5
- focused CLI smoke for the full staged flow
- synchronized roadmap, execution plans, and documentation

## Done When

- [x] full local roadmap remains implemented and validated
- [x] all verification commands pass
- [x] `docs/documentation.md` and task docs reflect the delivered state
- [x] no automatic action omits `reason` or `reason_code`
