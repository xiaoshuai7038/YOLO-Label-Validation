# Contract - Production VLM Detector Integration

## Goal

Replace the current fixture-only VLM and detector paths with production-oriented
runtime integrations that can call a real multimodal model and a real
Ultralytics-compatible detector while preserving the repository's patch-first
artifact contracts.

## Scope

- one committed runtime configuration file for user-decision parameters
- live VLM request execution against an OpenAI-compatible multimodal endpoint
- live detector inference against Ultralytics-compatible local weights
- propagation of runtime versions and config choices through artifacts
- CLI, tests, and docs needed to operate and validate the new runtime paths

## Out of Scope

- CVAT round-trip automation
- scope beyond fixed-class 2D detection boxes
- committing secrets or machine-local credentials into the repository
- removing offline fixture mode used by tests

## Closure Level

- Target closure: `slice`
- Meaning: production-oriented VLM and detector runtime paths are implemented
  and validated with mock-backed tests, but true credentialed live execution
  may still depend on the user's actual endpoint key and detector weights

## Done When

- `DW-001` one runtime configuration file captures all user-decision parameters
  for the VLM and detector integrations
- `DW-002` `run-vlm` can execute real multimodal requests using run artifacts
  and parse the returned structured JSON safely
- `DW-003` `run-detector-refine` can execute real Ultralytics inference and
  emit detector-backed refine and missing proposals
- `DW-004` integration outputs remain traceable, reasoned, and compatible with
  downstream decision and materialization stages
- `DW-005` tests, task-doc gate, and focused CLI validation pass

## Changes

- `CHG-001` add a runtime-config loader and committed config file for
  user-decision parameters
- `CHG-002` extend `vlm.py` with live OpenAI-compatible multimodal transport
  while preserving fixture mode
- `CHG-003` extend `detector_refine.py` with live Ultralytics inference while
  preserving deterministic test seams
- `CHG-004` propagate runtime metadata through CLI, manifest, and downstream
  decision flow
- `CHG-005` add regression coverage and task evidence for live-runtime code paths

## Coverage

- `COV-001` `src/yolo_label_validation/runtime_config.py` ->
  `load_runtime_config()`
- `COV-002` `src/yolo_label_validation/vlm.py` ->
  `run_vlm_for_directory()`, live request execution helpers
- `COV-003` `src/yolo_label_validation/detector_refine.py` ->
  `run_detector_refine_for_directory()`, live detector helpers
- `COV-004` `src/yolo_label_validation/cli.py` -> runtime-config aware CLI path
- `COV-005` `src/yolo_label_validation/contracts.py` -> run-manifest runtime metadata
- `COV-006` `tests/test_vlm.py` -> fixture mode and live VLM transport coverage
- `COV-007` `tests/test_detector_refine.py` -> fake-detector live path coverage
- `COV-008` `tests/test_decision.py`, `tests/test_materialize.py` -> downstream
  compatibility regression

## Validation Plan

- `TC-001` the runtime config loader accepts the committed config file and
  resolves env-var indirection safely
- `TC-002` the live VLM transport can call a mock OpenAI-compatible multimodal
  server and parse its response into `vlm_review.json`
- `TC-003` invalid live VLM payloads are rejected before decision routing
- `TC-004` the live detector path can call a fake Ultralytics model and emit
  `refine_results.json` / `missing_results.json`
- `TC-005` downstream decision and materialization stages remain green with the
  new live-runtime outputs
- `TC-006` task docs for this task pass the task-doc gate

- `T-001` `uv run pytest -q`
- `T-002` `uv run pytest -q tests/test_vlm.py tests/test_detector_refine.py`
- `T-003` `uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration`
- `T-004` focused CLI smoke using mocked runtime integrations
