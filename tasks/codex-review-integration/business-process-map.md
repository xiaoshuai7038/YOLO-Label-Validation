# Business Process Map - Codex Review Integration

## FLOW-001 Select the active review runtime

- Domain: semantic review configuration
- Actor: operator or coding agent
- Entry: a run workspace already has `review_candidates.json`
- Main path:
  1. load runtime integration config
  2. choose the live provider branch from `vlm.provider`
  3. keep fixture mode available when `responses_file` is provided or the mode
     is not live
- Exception path: an unsupported provider or invalid config blocks execution
- Evidence: `TC-001`, `TC-004`

## FLOW-002 Execute local Codex-backed review

- Domain: semantic review execution
- Actor: review runtime adapter
- Entry: `run-vlm` receives a live `codex_cli` config
- Main path:
  1. resolve the source image from `run_manifest.input_sources`
  2. build one `codex exec` request per review candidate
  3. attach the image and output schema to the local CLI call
  4. capture the final message text and normalize it into the existing
     raw-response shape
- Exception path: CLI, schema, or payload errors fail fast before downstream
  routing
- Evidence: `TC-002`, `TC-003`

## FLOW-003 Persist review artifacts without downstream churn

- Domain: artifact compatibility
- Actor: review runtime adapter
- Entry: normalized live or fixture responses are available
- Main path:
  1. parse the returned JSON into `vlm_review.json`
  2. write `vlm_requests.jsonl` and `vlm_raw_responses.jsonl`
  3. update `run_manifest.runtime_context.vlm` with provider and model details
- Exception path: invalid decision payloads are rejected and no ambiguous review
  artifact is emitted
- Evidence: `TC-002`, `TC-004`
