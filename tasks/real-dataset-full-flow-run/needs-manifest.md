# Needs Manifest - Real Dataset Full Flow Run

## Inputs

- source images and labels:
  `E:\workspace\cigarette-identify\预标注测试\20264010`
- defaults config: `configs/defaults.json`
- runtime config: `configs/runtime.integration.json`

## Outputs

- run workspace: `artifacts/runs/real-full-flow/`
- final artifacts:
  `normalized_annotations.jsonl`, `image_index.json`, `rule_issues.json`,
  `risk_scores.json`, `review_candidates.json`, `vlm_requests.jsonl`,
  `vlm_raw_responses.jsonl`, `vlm_review.json`, `refine_results.json`,
  `missing_results.json`, `decision_results.json`, `manual_review_queue.json`,
  `patches.json`, `materialized_dataset/`, `run_summary.json`,
  `metrics_dashboard_source.json`

## Operational Needs

- local `codex` CLI available on PATH
- enough time budget for sequential real-image VLM review
- source dataset must remain read-only

## Blocking Needs

- none at task start

## Deferred Needs

- live detector weights can be added later if measured detector validation is
  required for this same dataset run
