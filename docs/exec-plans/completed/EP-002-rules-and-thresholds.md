# EP-002 Rules and Thresholds

## Status

- Plan id: `EP-002`
- Milestone: `M3`
- State: completed
- Closure level: `slice`

## Outcome

- explicit rule issues emit severity, reasons, and auto-action hints
- threshold policies and golden-set contracts are versioned and deterministic
- class-level statistics are emitted from normalized annotations

## Delivered Work

1. Added deterministic threshold loading with YAML support.
2. Added golden-set manifest and evaluation report contracts.
3. Added rule checks for invalid class, invalid geometry, out-of-bounds,
   duplicate boxes, and per-class aspect ratio limits.
4. Added deterministic `class_stats.json` generation.
5. Added `run-rules` CLI support and regression tests.

## Verification

```powershell
uv run pytest -q tests/test_rules.py
uv run pytest -q
```

## Notes

- The next active milestone is M4 for risk ranking, VLM protocol, and
  decision routing.
