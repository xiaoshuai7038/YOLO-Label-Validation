# EP-003 Risk VLM Decision

## Status

- Plan id: `EP-003`
- Milestone: `M4`
- State: completed

## Context

M3 now emits deterministic rule issues, class stats, and threshold contracts.
The next deliverable is the model-assisted review layer: deterministic risk
scores, review candidates, schema-safe VLM protocol handling, decision results,
patches, and manual-review routing.

## Expected Outcome

- deterministic `risk_scores.json` and `review_candidates.json`
- deterministic `vlm_requests.jsonl`, `vlm_raw_responses.jsonl`, and parsed
  `vlm_review.json`
- deterministic `decision_results.json`, `patches.json`, and
  `manual_review_queue.json`

## Work Items

1. Define risk scoring and candidate-selection fixtures.
2. Implement deterministic risk fusion and candidate ranking.
3. Implement VLM request builder and response parser with schema validation.
4. Implement decision routing, patch generation, and manual queue emission.

## Verification

```powershell
uv run pytest -q
```

## Notes

- Keep all outputs reasoned and traceable.
- Validated with `tests/test_risk.py`, `tests/test_vlm.py`,
  `tests/test_decision.py`, and full regression.
