# SPEC

## Core Goal

Extend the completed local harness into a production-oriented runtime that can
invoke a real multimodal reviewer and a real closed-set detector for fixed-class
2D detection datasets:
normalized input -> rules and thresholds -> risk ranking -> live VLM review ->
live detector-backed refine/add -> decision and patching -> manual fallback ->
materialized dataset outputs -> run summary and metrics.

## Non-Goals

- CVAT round-trip automation
- scope expansion beyond fixed-class 2D detection boxes
- direct source-label overwrite
- free-form or non-schema outputs
- hardcoding provider credentials or machine-local paths into source control

## Hard Constraints

- source images and source labels remain read-only
- downstream stages consume normalized internal contracts only
- every automatic action must carry `reason` or `reason_code`
- patches are the only writable truth for annotation edits
- model and threshold versions are explicit in every run
- outputs must be deterministic for identical inputs and pinned versions
- secrets come only from environment variables, never from committed config

## Target Users

- dataset QA engineers validating prelabels locally
- operators running live multimodal review and detector-backed correction
- future agents extending the harness without breaking artifact contracts

## Deliverables

1. live VLM runtime integration against an OpenAI-compatible multimodal endpoint
2. live detector runtime integration against Ultralytics-compatible weights
3. one runtime configuration file for user-decided production parameters
4. tests and schemas covering both fixture mode and live-runtime code paths
5. synchronized docs, execution plans, and task evidence for the new milestone

## Product Requirements

### M6

- load one runtime integration config file with user-decided endpoint, model,
  environment-variable, and detector parameters
- invoke a real Qwen2.5-VL-compatible multimodal endpoint and parse schema-safe
  responses back into `vlm_review.json`
- invoke a real Ultralytics-compatible detector to emit `refine_results.json`
  and `missing_results.json`
- preserve fixture mode so tests and offline local development remain stable
- record runtime versions and paths explicitly enough for auditability

## Done Criteria

- the repo contains production-oriented live VLM and live detector code paths
- one committed runtime config file captures the user-decision parameters
- repo tests validate both fixture mode and live-runtime interfaces
- docs and task evidence show the remaining gap, if any, between mocked
  verification and true credentialed execution
