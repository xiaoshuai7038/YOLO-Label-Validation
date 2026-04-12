# Discovery Report - Production VLM Detector Integration

## Confirmed

- The local M1-M5 harness is complete and regression-green.
- `vlm.py` already builds structured requests and parses structured responses,
  but only from fixture files.
- `detector_refine.py` currently emits deterministic geometric proposals and
  does not call a real detector runtime.
- Runtime parameters are split across `configs/defaults.json`,
  `configs/thresholds.example.yaml`, CLI flags, and hardcoded defaults.

## Repository Reality

- The local M1-M5 harness is complete and regression-green.
- `vlm.py` already builds structured requests and parses structured responses,
  but only from fixture files.
- `detector_refine.py` currently emits deterministic geometric proposals and
  does not call a real detector runtime.
- Runtime parameters are split across `configs/defaults.json`,
  `configs/thresholds.example.yaml`, CLI flags, and hardcoded defaults.

## Commands Confirmed

- `uv run pytest -q`
- `uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration`
- `uv run python scripts/run_cli.py run-vlm ...`
- `uv run python scripts/run_cli.py run-detector-refine ...`

## Existing Documentation Health

| Path | Status | Issue | Action |
|---|---|---|---|
| `docs/project_spec.md` | healthy | still matches the patch-first system boundaries | keep |
| `docs/prompt.md` | salvageable | pointed at closeout rather than the new production integration task | rewrite |
| `docs/plan.md` | salvageable | local roadmap stopped at M5 | extend with M6 |
| `tasks/m3-m5-full-delivery/` | healthy | remains valid evidence for local closure | keep as completed task memory |
| `SPEC.md` / `PLAN.md` / `STATUS.md` | salvageable | need to track the new target and active milestone | refresh |

## Implementation Gap

1. No live HTTP transport exists for the VLM stage.
2. No live Ultralytics inference path exists for detector-backed refine/add.
3. No single runtime config file exists for user-decision parameters.
4. No tests currently exercise a live-style VLM server or live-style detector adapter.
