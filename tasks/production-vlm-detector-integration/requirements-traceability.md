# Requirements Traceability - Production VLM Detector Integration

| Req ID | Requirement | Design / Doc | Test / Validation | Status |
|---|---|---|---|---|
| `REQ-001` | One runtime config file centralizes user-decision parameters for VLM and detector integrations | `configs/runtime_integration.json`, `runtime_config.py` | `TC-001`, `T-001` | designed |
| `REQ-002` | The VLM stage can call a real OpenAI-compatible multimodal endpoint with local run images and structured prompts | `vlm.py`, `cli.py`, runtime config | `TC-002`, `T-001`, `T-002` | designed |
| `REQ-003` | Live VLM responses are rejected when they violate the structured contract | `vlm.py`, schemas | `TC-003`, `T-001`, `T-002` | designed |
| `REQ-004` | The detector stage can call a real Ultralytics-compatible model and emit refine/missing proposals | `detector_refine.py`, runtime config | `TC-004`, `T-001`, `T-002` | designed |
| `REQ-005` | Downstream decision and materialization logic remains compatible with live integration outputs | `decision.py`, `materialize.py`, schemas | `TC-005`, `T-001` | designed |
| `REQ-006` | Secrets are sourced from environment variables rather than committed files | runtime config design, docs | `TC-001`, doc inspection | designed |
