# Requirements Traceability - Codex Review Integration

| Req ID | Requirement | Design / Doc | Test / Validation | Status |
|---|---|---|---|---|
| `REQ-001` | The semantic-review stage must support a local Codex-backed provider without changing frozen `vlm_*` artifact names | `src/yolo_label_validation/vlm.py`, `docs/project_spec.md`, `tasks/codex-review-integration/contract.md` | `TC-002`, `TC-004` | validated |
| `REQ-002` | Runtime config must describe both `codex_cli` transport and the legacy HTTP transports | `src/yolo_label_validation/runtime_config.py`, `schemas/runtime_integration.schema.json`, `configs/runtime.integration.json` | `TC-001` | validated |
| `REQ-003` | `run-vlm` must send local image input and parse returned output into `vlm_review.json` safely | `src/yolo_label_validation/vlm.py`, `src/yolo_label_validation/cli.py` | `TC-002`, `TC-003` | validated |
| `REQ-004` | Run-manifest traceability must record the active provider and model explicitly | `src/yolo_label_validation/vlm.py`, `schemas/run_manifest.schema.json` | `TC-002`, `TC-004` | validated |
| `REQ-005` | Fixture mode and the prior HTTP provider paths must remain backward compatible | `src/yolo_label_validation/vlm.py`, `tests/test_vlm.py` | `TC-004` | validated |
| `REQ-006` | Repo roadmap and task evidence must identify this as a `slice` closure task rather than a full runtime certification | `docs/prompt.md`, `docs/plan.md`, `PLANS.md`, `docs/documentation.md` | `TC-005` | validated |
