# UAT Matrix - Production VLM Detector Integration

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | An operator can edit one runtime config file instead of scattering provider and detector parameters across code and CLI flags | `FLOW-001` | `TC-001`, runtime config docs | planned |
| `UAT-002` | A risky annotation can be sent to a real multimodal endpoint and return a parsed review artifact | `FLOW-002` | `TC-002`, `vlm_raw_responses.jsonl`, `vlm_review.json` | planned |
| `UAT-003` | A malformed live VLM response is rejected before decision routing | `FLOW-002` | `TC-003`, test assertions | planned |
| `UAT-004` | A refine or add-missing request can be backed by real detector inference rather than a stub | `FLOW-003` | `TC-004`, `refine_results.json`, `missing_results.json` | planned |
| `UAT-005` | Downstream patches and materialized outputs remain traceable after live integrations are enabled | `FLOW-004` | `TC-005`, regression assertions | planned |
