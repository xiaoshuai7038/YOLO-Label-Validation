# EP-008 Zero Annotation Image Review

## Status

- Plan id: `EP-008`
- Milestone: `M9`
- State: completed
- Closure target: `slice`

## Context

The real dataset proved that ingest compatibility was not enough: `245`
zero-annotation images survived normalization but were completely absent from
`review_candidates.json`, which meant the semantic-review pipeline could never
detect whole-image missing-label cases.

## Planned Work

- extend risk and review-candidate assembly so image-level empty-prelabel cases
  are explicit candidates
- extend VLM request/review artifacts with explicit review scope
- route image-level missing proposals through detector refine and decision
  stages without fake annotation ids
- update the failure taxonomy so this review-universe contraction pattern is
  called out explicitly in the harness

## Verification

```powershell
uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review
uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py
uv run pytest -q
```

## Result

- completed at `slice` closure
- real dataset `run-risk` now emits explicit image-level rows for all `245`
  zero-annotation images
- a real local Codex mini-run proved image-level review survives into
  `vlm_review.json`, `missing_results.json`, `decision_results.json`, and
  `patches.json`
