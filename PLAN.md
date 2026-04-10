# PLAN

## Verification Checklist

- `uv run pytest -q`
- `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery`
- focused CLI or module smoke checks for each milestone slice

## Milestones

| ID | Scope | Key Files | Acceptance |
|---|---|---|---|
| `LH-01` | durable-memory docs for remaining work | `SPEC.md`, `PLAN.md`, `RULES.md`, `STATUS.md` | long-horizon files exist and match repo roadmap |
| `LH-02` | M3-M5 task docs and gate | `tasks/m3-m5-full-delivery/*` | task-doc gate passes |
| `LH-03` | M3 threshold and golden-set contracts | `rules.py`, `schemas/*`, `tests/*` | threshold loader and golden-set artifacts validated |
| `LH-04` | M3 rule-issue engine | `rules.py`, `tests/test_rules.py` | invalid-class and invalid-box issues emitted with reasons |
| `LH-05` | M3 class stats and writer paths | `rules.py`, `cli.py`, `tests/test_rules.py` | deterministic stats and artifact writing validated |
| `LH-06` | M3 doc promotion | `docs/*`, `tasks/*` | roadmap moves to M4 |
| `LH-07` | M4 risk score fusion | `risk.py`, `tests/test_risk.py` | deterministic risk scores and reasons validated |
| `LH-08` | M4 review candidate generation | `risk.py`, `cli.py`, `tests/test_risk.py` | candidate sampling and ranking validated |
| `LH-09` | M4 VLM request builder | `vlm.py`, `schemas/*`, `tests/test_vlm.py` | requests serialize deterministically |
| `LH-10` | M4 VLM response parser and decision-safe review records | `vlm.py`, `tests/test_vlm.py` | invalid responses rejected, valid reviews parsed |
| `LH-11` | M4 decision engine and patch generation | `decision.py`, `tests/test_decision.py` | patches and manual queue are deterministic and reasoned |
| `LH-12` | M5 detector-backed refine and missing proposals | `detector_refine.py`, `tests/test_detector_refine.py` | refine/add proposals emitted with reasons |
| `LH-13` | M5 materialization, summary, and metrics | `materialize.py`, `tests/test_materialize.py` | dataset view, run summary, and metrics artifacts validated |
| `LH-14` | final docs sync and full regression | `docs/*`, `PLANS.md`, `STATUS.md` | roadmap promoted and full regression green |

## Architecture Notes

- `contracts.py` stays the canonical artifact registry and manifest contract
- each processing stage gets its own module and tests
- local adapters simulate integration seams behind stable contracts
- CLI remains thin and delegates to module functions

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| contract drift across modules | high | freeze schemas and drive tests from artifact payloads |
| false `full` closure claim while external services are mocked | high | document closure level honestly and name live-integration gap if it remains |
| determinism regressions in JSON output ordering | medium | sort records and keys consistently in writers and tests |
| oversized implementation diff causing cross-module bugs | medium | validate after each module slice and keep failure notes in task docs |

## Decision Log

- `2026-04-10`: use `uv run ...` as the canonical execution path because shell-level `python` is a broken Windows Store shim.
- `2026-04-10`: treat live external-service execution as non-blocking to local code completion, but keep contract surfaces explicit and testable.
- `2026-04-10`: downstream stages must preserve populated upstream artifacts;
  bootstrap overwrite semantics are restricted to empty workspace creation.
