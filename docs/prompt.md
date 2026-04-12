# prompt.md - Current Milestone Contract

This file describes only the current execution focus.
For the full roadmap, see `docs/plan.md`. For stable spec, see
`docs/project_spec.md`.

## Current Milestone: M6 - Production VLM and detector integrations (`slice` closed)

## Scope

The repository milestone is complete at `slice` closure: the VLM stage can call
a real OpenAI-compatible multimodal endpoint, the detector stage can call real
Ultralytics inference, and one committed runtime config captures the
user-decision integration parameters.

## In-Scope

- one runtime integration config file for provider, model, timeout, env-var,
  detector weight, and confidence settings
- real VLM execution path while preserving fixture mode for offline tests
- real detector execution path while preserving deterministic fallback tests
- traceability, patch-only writes, and explicit reasons in all downstream
  outputs

## Non-Goals

- CVAT round-trip automation
- scope expansion beyond fixed-class 2D detection boxes

## Hard Constraints

- downstream code must consume normalized internal contracts, not raw source
  formats
- source images and source labels remain read-only
- every automatic decision or patch must include `reason` or `reason_code`
- no future change may reintroduce upstream artifact clobbering across stages
- secrets must be sourced from environment variables, not committed config

## Verification Commands

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration
```

## Required Evidence

- mock-backed proof that live VLM requests can execute and parse correctly
- fake-detector proof that live detector inference path is exercised
- synchronized roadmap, execution plans, task docs, and runtime config docs
- explicit note that true credentialed runtime smoke still depends on external
  secrets and weights

## Done When

- [x] VLM live runtime path is implemented and test-covered
- [x] detector live runtime path is implemented and test-covered
- [x] one runtime config file captures user-decision parameters
- [x] all verification commands pass
- [x] `docs/documentation.md` and task docs reflect the delivered state
