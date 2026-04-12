# Architecture Bootstrap

This document translates the SRS into an initial repository shape and module map.

## Repository Layout

| Path | Purpose |
|---|---|
| `configs/` | frozen default policy and threshold examples |
| `docs/` | roadmap, current milestone, stable spec, execution plans, and logs |
| `tasks/` | task-specific discovery, contracts, plans, and validation memory |
| `schemas/` | JSON schema contracts for the minimum interchange files |
| `scripts/` | wrappers for local CLI execution |
| `src/yolo_label_validation/` | bootstrap code and future pipeline modules |
| `tests/` | smoke tests and future regression fixtures |
| `.github/workflows/` | CI gates that mirror local validation |
| `artifacts/runs/` | generated run workspaces; ignored by Git |

## Planned Module Boundaries

| Module | Responsibility | Inputs | Outputs |
|---|---|---|---|
| `contracts.py` | canonical contracts and artifact registry | SRS file contracts | typed Python data and filenames |
| `bootstrap.py` | initialize run workspace | run metadata | empty but valid artifact files |
| `task_docs.py` | scaffold task and context docs | task name, task slug | concrete markdown docs |
| `doc_check.py` | validate task-doc readiness | task folder | blocking findings or pass result |
| `ingest.py` | parse YOLO/COCO and normalize | raw images, labels, class map | `normalized_annotations.jsonl`, `image_index.json`, `class_map.json` |
| `rules.py` | run explicit validation and statistics | normalized annotations, thresholds | `rule_issues.json`, `class_stats.json` |
| `risk.py` | fuse Cleanlab and FiftyOne signals | predictions, labels, stats | `risk_scores.json`, `review_candidates.json` |
| `vlm.py` | build Qwen2.5-VL requests and parse JSON | candidates, crops, prompts | `vlm_requests.jsonl`, `vlm_raw_responses.jsonl`, `vlm_review.json` |
| `decision.py` | merge rules, risk, VLM, and detector evidence | all review outputs | `decision_results.json`, `patches.json`, `manual_review_queue.json` |
| `detector_refine.py` | refine or add boxes with detector B | crops, current boxes | `refine_results.json`, `missing_results.json` |
| `materialize.py` | apply patches into dataset views | source labels, patches | `materialized_dataset/`, export manifests |

## File Naming Rules

- Run workspaces live under `artifacts/runs/<run_id>/`
- Artifact names are frozen in `src/yolo_label_validation/contracts.py`
- Schema files use the pattern `schemas/<artifact>.schema.json`
- Execution plans use `docs/exec-plans/active/EP-XXX-<slug>.md`
- Test files mirror module names with `tests/test_<module>.py`

## Processing Sequence

```mermaid
flowchart LR
    A[Raw images + YOLO/COCO labels] --> B[Normalize contracts]
    B --> C[Static rules + threshold checks]
    B --> D[Risk ranking]
    C --> E[Decision engine]
    D --> F[VLM semantic review]
    F --> G[Detector-backed refine or add]
    G --> E
    C --> E
    E --> H[Patch generation]
    E --> I[Manual review queue]
    H --> J[Materialized dataset view]
    I --> H
```

## YOLO Validation Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Operator
    participant CLI as run_cli.py / cli.py
    participant YOLO as YOLO Images + Labels
    participant Ingest as ingest.py
    participant Rules as rules.py
    participant Risk as risk.py
    participant VLM as vlm.py
    participant Detector as detector_refine.py
    participant Decision as decision.py
    participant Materialize as materialize.py
    participant RunDir as artifacts/runs/<run_id>

    Operator->>CLI: normalize-yolo --images-dir --labels-dir --class-names-file
    CLI->>Ingest: parse YOLO txt and image sizes
    Ingest->>YOLO: read images, labels, classes
    Ingest->>RunDir: write normalized_annotations.jsonl
    Ingest->>RunDir: write image_index.json, class_map.json, run_manifest.json

    Operator->>CLI: run-rules --run-dir
    CLI->>Rules: load normalized internal contracts
    Rules->>RunDir: write rule_issues.json
    Rules->>RunDir: write class_stats.json
    Rules->>RunDir: write golden_set_manifest.json and golden_eval_report.json

    Operator->>CLI: run-risk --run-dir
    CLI->>Risk: fuse rule and class-level signals
    Risk->>RunDir: write risk_scores.json
    Risk->>RunDir: write review_candidates.json

    Operator->>CLI: run-vlm --run-dir --responses-file
    CLI->>VLM: build structured requests for risky annotations
    VLM->>RunDir: write vlm_requests.jsonl
    VLM->>RunDir: write vlm_raw_responses.jsonl
    VLM->>RunDir: write vlm_review.json

    Operator->>CLI: run-detector-refine --run-dir
    CLI->>Detector: build refine and add-missing proposals
    Detector->>RunDir: write refine_results.json
    Detector->>RunDir: write missing_results.json

    Operator->>CLI: run-decision --run-dir
    CLI->>Decision: merge rules, risk, VLM, detector evidence
    Decision->>RunDir: write decision_results.json
    Decision->>RunDir: write patches.json
    Decision->>RunDir: write manual_review_queue.json

    Operator->>CLI: run-materialize --run-dir
    CLI->>Materialize: apply patches to a derived dataset view
    Materialize->>RunDir: write materialized_dataset/
    Materialize->>RunDir: write run_summary.json
    Materialize->>RunDir: write metrics_dashboard_source.json
```

## Bootstrap Decision

The first committed code only implements scaffold bootstrap.
FR-001 and FR-002 are the next active engineering target after this
initialization pass. Harness hardening also adds task-scoped docs, a doc gate,
and CI wiring so future milestones start from a repeatable baseline.
