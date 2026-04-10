# UAT Matrix - M3-M5 Full Delivery

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | A local operator can load thresholds and build golden-set contracts with explicit versions | `FLOW-001` | `TC-001`, golden-set manifest artifacts | pass |
| `UAT-002` | Invalid classes, invalid geometry, and duplicate boxes surface as structured rule issues with reasons | `FLOW-002` | `TC-002`, `rule_issues.json` fixture assertions | pass |
| `UAT-003` | Class-level statistics remain deterministic and carry threshold metadata | `FLOW-003` | `TC-003`, `class_stats.json` fixture assertions | pass |
| `UAT-004` | Risk scores and review candidates remain machine-readable and deterministic | `FLOW-004` | `TC-004`, `risk_scores.json`, `review_candidates.json` | pass |
| `UAT-005` | VLM requests serialize deterministically and invalid VLM responses are rejected | `FLOW-005` | `TC-005`, `vlm_requests.jsonl`, `vlm_review.json` | pass |
| `UAT-006` | Decision results, patches, and manual queue items remain traceable and reasoned | `FLOW-006` | `TC-006`, `decision_results.json`, `patches.json`, `manual_review_queue.json` | pass |
| `UAT-007` | Detector-backed refine and missing proposals preserve confidence and reasons | `FLOW-007` | `TC-007`, `refine_results.json`, `missing_results.json` | pass |
| `UAT-008` | Materialized dataset outputs apply patches without touching source labels | `FLOW-008` | `TC-007`, `materialized_dataset/` fixture assertions | pass |
| `UAT-009` | Run summary and metrics artifacts remain consistent with all emitted outputs | `FLOW-009` | `TC-008`, `run_summary.json`, `metrics_dashboard_source.json` | pass |
