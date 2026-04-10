# YOLO Auto-Audit SRS v1

This repository implements a patch-first audit system for YOLO prelabels.
The source requirement is the 2026-04-10 SRS provided in the bootstrap session.

## Scope

- Fixed-class, proprietary datasets
- Existing prelabels are available
- Only 2D detection boxes are in scope
- Segmentation, tracking, keypoints, 3D, and open-ontology discovery are out
  of scope for this phase

## Target Workflow

1. Import images, labels, class map, and golden set.
2. Normalize inputs into one internal contract.
3. Run static validation.
4. Rank risky images and boxes with Cleanlab and FiftyOne.
5. Review risky cases with Qwen2.5-VL via structured JSON.
6. Refine or add boxes with a closed-set detector.
7. Escalate uncertain or conflicting cases to CVAT.
8. Emit `patches.json` instead of mutating source labels.
9. Materialize a new dataset view for training and evaluation.

## Frozen Technology Choices

- Detection validation baseline: Datumaro `validate`
- Label-quality ranking: Cleanlab object detection
- Additional risk signals: FiftyOne Brain
- Structured semantic reviewer: Qwen2.5-VL
- Human fallback: CVAT
- Geometric refinement and missing-box recovery: closed-set detector trained on
  the same ontology
- Training compatibility target: Ultralytics custom dataset flow

## P0 Deliverables

- Input normalization and source traceability
- Class-map and version management
- Golden-set tracking
- Static rule validation
- Risk-score fusion and review candidate generation
- VLM review request and response schema
- Decision engine and patch generation
- Manual review queue
- Audit summary and idempotent run execution

## P1 Deliverables

- CVAT round-trip integration
- Missing-box enhancement
- Materialized dataset export
- Retraining manifests and evaluation reports
- Dashboard-ready metrics aggregation

## Canonical Artifact Files

- `normalized_annotations.jsonl`
- `image_index.json`
- `class_map.json`
- `run_manifest.json`
- `rule_issues.json`
- `class_stats.json`
- `risk_scores.json`
- `review_candidates.json`
- `vlm_requests.jsonl`
- `vlm_raw_responses.jsonl`
- `vlm_review.json`
- `decision_results.json`
- `refine_results.json`
- `missing_results.json`
- `manual_review_queue.json`
- `patches.json`
- `run_summary.json`

## Non-Functional Constraints

- Every change must be traceable to the original file and original annotation
- Identical inputs and versions must produce identical outputs
- Thresholds and paths must be configuration-driven
- Source images and labels remain read-only
- Scores without reasons are invalid
- Every patch must be reversible
- Components must remain replaceable behind stable contracts
