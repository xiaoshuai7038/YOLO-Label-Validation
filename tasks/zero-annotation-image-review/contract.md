# Contract - Zero Annotation Image Review

## Goal

Stop silently skipping zero-annotation images by making image-level review a
first-class path in the harness, from risk candidate selection through VLM
review and decision routing.

## Scope

- redefine the review universe from `image_index`, not only
  `normalized_annotations`
- add explicit review-scope metadata so artifacts can distinguish
  annotation-level review from image-level review
- guarantee that zero-annotation images produce review candidates instead of
  being sampled away silently
- route image-level VLM outputs into missing-object proposals and manual-review
  records without fake annotation ids
- record the failure pattern in the reusable harness docs

## Out of Scope

- changing source data or the normalized annotation schema
- optimizing review cost for the newly included zero-annotation images
- CVAT, materialization, or external-service workflow redesign beyond what is
  needed for correct traceability

## Closure Level

- Target closure: `slice`
- Meaning: zero-annotation images are no longer skipped and can flow into
  missing-object review, but broader cost and policy tuning remain future work

## Done When

- `DW-001` zero-annotation images appear in `review_candidates.json`
- `DW-002` `run-vlm` emits image-level review requests with explicit
  `review_scope`
- `DW-003` image-level `add_missing` reviews become `missing_results`,
  `decision_results`, `patches`, or manual-review items with traceable lineage
- `DW-004` no fake annotation ids are introduced to represent image-level work
- `DW-005` failure taxonomy and milestone docs record the root cause and the
  new guardrail
- `DW-006` targeted tests and full pytest pass
- `DW-007` a real local Codex mini-run proves image-level review survives into
  downstream artifacts without fake annotation ids

## Changes

- `CHG-001` extend risk scoring and review candidate assembly with explicit
  image-level candidates for zero-annotation images
- `CHG-002` extend VLM request/review contracts with `review_scope` and
  image-level context
- `CHG-003` update detector refine and decision routing to handle image-level
  missing proposals without ann-id collisions
- `CHG-004` add regression tests for zero-annotation risk, VLM, detector, and
  decision flows
- `CHG-005` add a reusable failure-taxonomy entry and sync roadmap/task docs
- `CHG-006` harden local Codex CLI invocation for Windows command resolution
  and a realistic image-review timeout baseline

## Coverage

- `COV-001` `src/yolo_label_validation/risk.py` ->
  `build_risk_scores()`, `build_review_candidates()`
- `COV-002` `src/yolo_label_validation/vlm.py` ->
  `build_vlm_requests()`, `parse_vlm_reviews()`, live/fake response handling
- `COV-003` `src/yolo_label_validation/detector_refine.py` ->
  missing-result generation for image-level source reviews
- `COV-004` `src/yolo_label_validation/decision.py` ->
  image-level review routing and manual-review generation
- `COV-005` `tests/test_risk.py`, `tests/test_vlm.py`,
  `tests/test_detector_refine.py`, `tests/test_decision.py`
- `COV-006` `docs/failures/taxonomy.md`, `docs/prompt.md`, `docs/plan.md`,
  `tasks/zero-annotation-image-review/documentation.md`
- `COV-007` `configs/runtime.integration.json`, real local Codex CLI mini-run

## Validation Plan

- `TC-001` risk scoring emits explicit image-level risk rows for
  zero-annotation images
- `TC-002` review candidates include zero-annotation images even when normal
  annotation sampling would not
- `TC-003` VLM requests for zero-annotation images carry `review_scope=image`
  and no fake `ann_id`
- `TC-004` image-level VLM `add_missing` output becomes traceable
  `missing_results` and downstream `decision_results`
- `TC-005` image-level uncertain review becomes a manual-review item instead of
  disappearing
- `TC-006` the task-doc gate passes on `tasks/zero-annotation-image-review`
- `TC-007` full pytest remains green
- `TC-008` a real zero-annotation image can complete the local
  `codex_cli -> vlm_review -> missing_results -> decision_results -> patches`
  chain with explicit `review_scope=image`

- `T-001` `uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review`
- `T-002` `uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py`
- `T-003` `uv run pytest -q`
- `T-004` `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/real-zero-one-vlm --defaults-file configs/defaults.json --runtime-config configs/runtime.integration.json --overwrite`, then `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/real-zero-one-vlm --overwrite`, then `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-zero-one-vlm --defaults-file configs/defaults.json --overwrite`
