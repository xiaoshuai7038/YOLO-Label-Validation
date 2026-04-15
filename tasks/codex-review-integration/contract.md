# Contract - Codex Review Integration

## Goal

Replace the current provider-specific VLM live path with a local Codex CLI
review runtime while preserving the repository's frozen `vlm_*` artifacts and
patch-first downstream flow.

## Scope

- extend runtime config and schema coverage so the review stage can select a
  local `codex_cli` provider in addition to the existing HTTP providers
- execute live local Codex review requests from local run artifacts, including
  image input derived from source data
- parse the returned response into the existing `vlm_review.json` contract and
  keep manifest traceability explicit
- preserve fixture mode, existing CLI shape, and downstream compatibility
- add tests, example config, and docs for the new runtime path

## Out of Scope

- renaming `vlm_requests.jsonl`, `vlm_raw_responses.jsonl`, `vlm_review.json`,
  or the `run-vlm` CLI command
- changing downstream decision, patch, detector, or materialization contracts
- claiming a fully general live validation beyond the operator's local Codex
  setup
- scope expansion beyond fixed-class 2D detection boxes

## Closure Level

- Target closure: `slice`
- Meaning: the local Codex-backed review runtime is implemented and
  regression-tested locally, but a true live smoke still depends on the user's
  installed Codex login/profile state

## Done When

- `DW-001` runtime config and schema validation can describe both the local
  `codex_cli` transport and the legacy HTTP transports
- `DW-002` `run-vlm` can execute a mocked `codex exec` request using local
  image data and parse the returned content into `vlm_review.json`
- `DW-003` existing fixture mode and legacy HTTP provider modes remain
  compatible
- `DW-004` `run_manifest.json` and downstream stages keep explicit traceability
  without contract churn
- `DW-005` regression tests, task-doc gate, and roadmap/docs synchronization
  pass

## Changes

- `CHG-001` extend `runtime_config.py` and
  `schemas/runtime_integration.schema.json` for provider-specific review
  transport settings
- `CHG-002` extend `vlm.py` with a local `codex exec` transport, output-schema
  builder, and response capture while preserving existing behavior
- `CHG-003` update example runtime configuration and operator-facing docs for
  local Codex review usage
- `CHG-004` add regression coverage for local Codex transport, config
  validation,
  and backward compatibility
- `CHG-005` synchronize milestone, plan, and task evidence docs for the new
  active task

## Coverage

- `COV-001` `src/yolo_label_validation/runtime_config.py` ->
  `load_runtime_config()`
- `COV-002` `schemas/runtime_integration.schema.json` -> runtime config
  contract
- `COV-003` `src/yolo_label_validation/vlm.py` ->
  `run_vlm_for_directory()`, live transport helpers, response parsing helpers
- `COV-004` `configs/runtime.integration.json` -> committed operator example
- `COV-005` `src/yolo_label_validation/cli.py` -> `run-vlm` compatibility path
- `COV-006` `tests/test_runtime_config.py` -> config normalization coverage
- `COV-007` `tests/test_vlm.py` -> fixture mode, legacy HTTP modes, and local
  Codex CLI mode coverage
- `COV-008` `docs/prompt.md`, `docs/plan.md`, `PLANS.md`,
  `docs/documentation.md` -> active-task synchronization

## Validation Plan

- `TC-001` runtime config accepts a `codex_cli` provider payload and
  normalizes provider-specific fields safely
- `TC-002` the `codex_cli` path can call a mocked local runner, send image
  input, and parse its returned text into `vlm_review.json`
- `TC-003` malformed local Codex outputs are rejected before decision
  routing
- `TC-004` existing fixture mode and legacy HTTP provider paths stay green
- `TC-005` task docs and roadmap docs remain synchronized for the new task

- `T-001` `uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py`
- `T-002` `uv run pytest -q`
- `T-003` `uv run python scripts/check_task_docs.py tasks/codex-review-integration`
