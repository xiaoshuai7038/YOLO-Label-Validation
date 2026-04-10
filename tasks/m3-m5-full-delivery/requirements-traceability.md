# Requirements Traceability - M3-M5 Full Delivery

| Req ID | Requirement | Design / Interface / Data | Flow / UAT / TC / T | Status |
|---|---|---|---|---|
| `REQ-001` | Emit deterministic golden-set contracts and threshold snapshots | `rules.py`, `schemas/golden_set_manifest.schema.json`, `schemas/golden_eval_report.schema.json` | `FLOW-001`, `UAT-001`, `TC-001`, `T-001` | validated |
| `REQ-002` | Emit machine-readable rule issues with severity and reasons | `rules.py`, `schemas/rule_issue.schema.json` | `FLOW-002`, `UAT-002`, `TC-002`, `T-001` | validated |
| `REQ-003` | Emit deterministic class statistics from normalized annotations | `rules.py`, `schemas/class_stats.schema.json` | `FLOW-003`, `UAT-003`, `TC-003`, `T-001` | validated |
| `REQ-004` | Emit deterministic risk scores and review candidates | `risk.py`, `schemas/risk_score.schema.json`, `schemas/review_candidate.schema.json` | `FLOW-004`, `UAT-004`, `TC-004`, `T-001` | validated |
| `REQ-005` | Build VLM requests and parse VLM responses into schema-safe review records | `vlm.py`, `schemas/vlm_request.schema.json`, `schemas/vlm_review.schema.json` | `FLOW-005`, `UAT-005`, `TC-005`, `T-001` | validated |
| `REQ-006` | Merge rules, risk, VLM, and detector evidence into deterministic decisions, patches, and manual queue outputs | `decision.py`, `schemas/decision_result.schema.json`, `schemas/patch.schema.json`, `schemas/manual_review_item.schema.json` | `FLOW-006`, `UAT-006`, `TC-006`, `T-001` | validated |
| `REQ-007` | Emit detector-backed refine/add proposals with reasons and confidence | `detector_refine.py`, `schemas/refine_result.schema.json`, `schemas/missing_result.schema.json` | `FLOW-007`, `UAT-007`, `TC-007`, `T-001` | validated |
| `REQ-008` | Materialize a patch-applied dataset view without mutating source labels | `materialize.py`, materialized dataset writer | `FLOW-008`, `UAT-008`, `TC-007`, `T-001` | validated |
| `REQ-009` | Emit run summary and dashboard-ready metrics that remain consistent with all previous artifacts | `materialize.py`, `schemas/run_summary.schema.json`, `schemas/metrics_dashboard_source.schema.json` | `FLOW-009`, `UAT-009`, `TC-008`, `T-001` | validated |
