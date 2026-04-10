# STATUS

## Project

YOLO Label Validation harness, remaining delivery after M2 normalization.

## Milestone State

| Item | Status | Notes |
|---|---|---|
| M1 bootstrap | completed | foundation closed |
| M2 normalization | completed | slice closed |
| M3 rules and thresholds | completed | regression green |
| M4 risk, VLM, decision | completed | regression and CLI smoke green |
| M5 refine, materialize, ops | completed | local roadmap closed |
| long-horizon docs | completed | ready for milestone execution |

## Environment

- Use `uv run python ...` and `uv run pytest -q`
- Local shell `python` command is not reliable in this environment

## Latest Validation

- `uv run pytest -q` passed at the start of this session
- `uv run python scripts/check_task_docs.py tasks/m2-input-normalization` passed at the start of this session
- `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery` passed in this session
- `uv run pytest -q tests/test_rules.py` passed in this session
- `uv run pytest -q tests/test_risk.py` passed in this session
- `uv run pytest -q tests/test_vlm.py` passed in this session
- `uv run pytest -q tests/test_decision.py` passed in this session
- `uv run pytest -q tests/test_detector_refine.py` passed in this session
- `uv run pytest -q tests/test_materialize.py` passed in this session
- `uv run pytest -q` passed after full M3-M5 delivery in this session
- staged CLI smoke passed for `normalize-yolo`, `run-rules`, `run-risk`,
  `run-vlm`, `run-decision`, `run-detector-refine`, and `run-materialize`

## Current Focus

Keep the repository in a verified closeout state after the completed M1-M5
local roadmap delivery.
