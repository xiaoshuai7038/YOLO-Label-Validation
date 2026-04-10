# Needs Manifest

## Task

- Task slug: `m3-m5-full-delivery`

## Blocking Needs

- None. The remaining repository roadmap can be implemented locally with
  synthetic fixtures and contract-level adapters.

## Non-Blocking Needs

- Live external credentials or runtimes for Cleanlab, FiftyOne, Qwen2.5-VL,
  detector checkpoints, and CVAT to validate real integrations beyond local
  contract behavior.
- Larger real datasets to calibrate candidate sampling and review precision.
- A future product decision on whether golden-set evaluation should persist
  per-annotation diffs or only aggregated metrics in `golden_eval_report.json`.

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| live Cleanlab/FiftyOne scoring | local heuristics and contract outputs are enough for code completion | M4 follow-up |
| live VLM execution | parser and request builder can be validated with fixtures | M4 follow-up |
| live detector model outputs | local deterministic proposals are enough for refine/add flow logic | M5 follow-up |
| live CVAT import/export | contract-compatible queue and export artifacts can be validated locally | M5 follow-up |
