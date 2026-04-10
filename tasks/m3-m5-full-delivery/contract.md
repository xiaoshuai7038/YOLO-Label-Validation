# Contract - M3-M5 Full Delivery

## Goal

Implement the remaining repository roadmap after M2 so the codebase can execute
the full local patch-first audit pipeline for fixed-class 2D detection boxes:
rules and thresholds, risk ranking, structured VLM review, decision and patch
generation, detector-backed refine/add proposals, manual review routing,
materialized dataset export, and run-level summaries.

## Scope

- M3 rule validation, class stats, threshold loading, and golden-set contracts
- M4 risk scoring, review candidate generation, VLM request/response handling,
  decision routing, patch generation, and manual queue output
- M5 refine/add proposals, materialized dataset export, run summary, and
  metrics artifact generation
- artifact schemas, tests, CLI wiring, and docs for the remaining milestones

## Out of Scope

- live external-service execution requiring credentials or network-side state
- model training, benchmark calibration, or dashboard frontend work
- any scope beyond fixed-class 2D detection boxes
- direct mutation of source labels or source images

## Closure Level

- Target closure: `full`
- Meaning: all remaining local roadmap requirements from M3 through M5 are
  implemented and validated in the repository, while live external-service
  execution remains explicitly outside this task scope

## Done When

- `DW-001` rule, threshold, and golden-set artifacts are emitted with explicit
  reasons and deterministic versions
- `DW-002` risk, review-candidate, VLM, decision, patch, and manual-review
  artifacts are emitted deterministically with machine-readable evidence
- `DW-003` refine/add, materialization, run-summary, and metrics artifacts are
  emitted without mutating source labels
- `DW-004` all remaining artifact schemas are frozen under `schemas/`
- `DW-005` tests cover the happy paths and key failure paths for M3-M5 modules
- `DW-006` roadmap, execution plans, and task evidence are synchronized to the
  final milestone state

## Changes

- `CHG-001` add `rules.py` for threshold loading, golden-set contracts, rule
  issues, and class stats
- `CHG-002` add `risk.py` for deterministic score fusion and candidate ranking
- `CHG-003` add `vlm.py` for request building and response parsing under stable
  schemas
- `CHG-004` add `decision.py` for decision results, patches, and manual queue
- `CHG-005` add `detector_refine.py` for refine/add proposal outputs
- `CHG-006` add `materialize.py` for patch-applied exports, run summaries, and
  metrics
- `CHG-007` extend `cli.py`, schemas, and tests to cover all new outputs

## Coverage

- `COV-001` `src/yolo_label_validation/rules.py` ->
  `load_threshold_policy()`, `build_golden_set_manifest()`,
  `run_rule_checks()`, `build_class_stats()`
- `COV-002` `src/yolo_label_validation/risk.py` ->
  `build_risk_scores()`, `build_review_candidates()`
- `COV-003` `src/yolo_label_validation/vlm.py` ->
  `build_vlm_requests()`, `parse_vlm_reviews()`
- `COV-004` `src/yolo_label_validation/decision.py` ->
  `build_decision_results()`, `build_patch_records()`,
  `build_manual_review_queue()`
- `COV-005` `src/yolo_label_validation/detector_refine.py` ->
  `build_refine_results()`, `build_missing_results()`
- `COV-006` `src/yolo_label_validation/materialize.py` ->
  `materialize_dataset_view()`, `build_run_summary()`,
  `build_metrics_dashboard_source()`
- `COV-007` `src/yolo_label_validation/cli.py` -> remaining artifact-producing
  subcommands
- `COV-008` `tests/test_rules.py` -> M3 regression coverage
- `COV-009` `tests/test_risk.py`, `tests/test_vlm.py`,
  `tests/test_decision.py` -> M4 regression coverage
- `COV-010` `tests/test_detector_refine.py`, `tests/test_materialize.py` ->
  M5 regression coverage

## Validation Plan

- `TC-001` threshold policies and golden-set manifests load deterministically
  and preserve version metadata
- `TC-002` invalid-class, invalid-geometry, and duplicate-box rule issues emit
  severity, reason, and auto-action hints
- `TC-003` class statistics and threshold snapshots are deterministic
- `TC-004` risk scores and review candidates are ranked deterministically with
  machine-readable reasons
- `TC-005` VLM request payloads serialize deterministically and invalid VLM
  responses are rejected before decision routing
- `TC-006` decision results, patches, and manual-review queue payloads remain
  traceable and deterministic
- `TC-007` detector refine/add outputs and materialized dataset exports preserve
  patch-only writes
- `TC-008` run summary and metrics outputs remain consistent with the emitted
  artifacts
- `TC-009` remaining task docs stay green through the doc gate

- `T-001` `uv run pytest -q`
- `T-002` `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery`
- `T-003` focused CLI smoke checks for remaining pipeline subcommands
