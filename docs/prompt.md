# prompt.md - Current Milestone Contract

This file describes only the current execution focus.
For the full roadmap, see `docs/plan.md`. For stable spec, see
`docs/project_spec.md`.

## Current Milestone: M9 - Zero-annotation image review closure (`slice` closed)

## Scope

The current execution focus is the next bounded `slice`: stop silently skipping
zero-annotation images in the review pipeline and make image-level missing
review a first-class path after the real-dataset ingest compatibility work.

## In-Scope

- explicit image-level review candidates for zero-annotation images
- `review_scope` metadata in review artifacts so image-level work is not faked
  as annotation-level work
- detector and decision routing for image-level missing proposals
- regression coverage and task evidence for the zero-annotation review slice

## Non-Goals

- renaming canonical artifact files or changing normalized source annotations
- scope expansion beyond fixed-class 2D detection boxes

## Hard Constraints

- downstream code must continue consuming the normalized internal contracts
- source images and source labels remain read-only
- every automatic decision or patch must include `reason` or `reason_code`
- image-level review must remain explicit in artifacts instead of being encoded
  through fake annotation ids
- completion is `slice`, not a claim that review-cost optimization is solved

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review
uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py
uv run pytest -q
```

## Required Evidence

- proof that zero-annotation images appear in `review_candidates.json`
- proof that image-level VLM reviews carry explicit scope and no fake `ann_id`
- proof that image-level `add_missing` results survive into decisions and
  patches or manual review
- synchronized roadmap, prompt, task docs, and failure taxonomy

## Done When

- [x] zero-annotation image candidates are no longer skipped
- [x] image-level review scope is explicit in downstream artifacts
- [x] image-level missing review survives through detector and decision routing
- [x] roadmap, prompt, task docs, and failure taxonomy reflect the delivered state
