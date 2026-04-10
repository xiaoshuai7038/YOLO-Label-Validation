# SPEC

## Core Goal

Complete the remaining repository roadmap after M2 so the harness can execute a
full local patch-first audit flow for fixed-class 2D detection datasets:
normalized input -> rules and thresholds -> risk ranking -> structured VLM
review -> decision and patching -> detector-backed refine/add -> manual queue ->
materialized dataset outputs -> run summary and metrics.

## Non-Goals

- live external-service execution against Cleanlab, FiftyOne, Qwen2.5-VL, or
  CVAT credentials
- scope expansion beyond fixed-class 2D detection boxes
- direct source-label overwrite
- free-form or non-schema outputs

## Hard Constraints

- source images and source labels remain read-only
- downstream stages consume normalized internal contracts only
- every automatic action must carry `reason` or `reason_code`
- patches are the only writable truth for annotation edits
- model and threshold versions are explicit in every run
- outputs must be deterministic for identical inputs and pinned versions

## Target Users

- dataset QA engineers validating prelabels locally
- future agents extending the harness without breaking artifact contracts
- downstream training and audit tooling that consumes deterministic artifacts

## Deliverables

1. M3 local rule-validation, class-stats, threshold, and golden-set contracts
2. M4 local risk-ranking, VLM protocol, decision, and patch generation modules
3. M5 detector-refine, manual-review, materialization, summary, and metrics modules
4. schemas and tests for all newly emitted artifacts
5. synchronized docs, execution plans, and task evidence

## Product Requirements

### M3

- emit `golden_set_manifest.json` and `golden_eval_report.json` contracts
- emit `rule_issues.json` with machine-readable issue types, severity, reason,
  and auto-action hints
- emit deterministic `class_stats.json`
- load and snapshot threshold policy versions deterministically

### M4

- emit deterministic `risk_scores.json` and `review_candidates.json`
- build and parse schema-safe VLM request and response artifacts
- merge evidence into `decision_results.json`, `patches.json`, and
  `manual_review_queue.json`

### M5

- emit `refine_results.json` and `missing_results.json`
- materialize a patch-applied dataset view without mutating source labels
- emit `run_summary.json` and `metrics_dashboard_source.json`
- preserve full traceability from normalized inputs to emitted patches

## Done Criteria

- all milestone roadmap outputs from M3 to M5 are implemented locally
- repo tests validate the happy paths and key failure paths for each module
- docs and task evidence show which requirements were validated
- remaining gaps, if any, are limited to live external-service execution rather
  than missing local code paths
