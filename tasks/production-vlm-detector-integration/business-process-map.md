# Business Process Map - Production VLM Detector Integration

## FLOW-001 Load production runtime configuration

- Domain: runtime bootstrap
- Actor: local operator
- Entry: run a CLI command with `--runtime-config`
- Main path:
  1. load one config file
  2. resolve env-var names for secrets
  3. validate provider, timeout, and model-path fields
- Exception paths:
  1. missing env var blocks live execution
  2. malformed config fails fast before any network or detector call
- Evidence: `TC-001`

## FLOW-002 Execute live VLM review

- Domain: semantic review
- Actor: VLM adapter
- Entry: `review_candidates.json` exists and runtime config enables live VLM
- Main path:
  1. resolve the source image path from run metadata
  2. build an OpenAI-compatible multimodal request
  3. send the request to the configured endpoint
  4. parse the returned JSON into `vlm_review.json`
- Exception paths:
  1. transport error or auth error returns a clear failure
  2. schema-invalid model output is rejected before decision routing
- Evidence: `TC-002`, `TC-003`

## FLOW-003 Execute live detector refinement

- Domain: geometry correction
- Actor: detector adapter
- Entry: `vlm_review.json` contains refine or add-missing requests
- Main path:
  1. load Ultralytics weights and runtime options from config
  2. run inference on the source image
  3. filter detections by class and region relevance
  4. emit `refine_results.json` and `missing_results.json`
- Exception paths:
  1. missing weights or unsupported runtime raises a clear failure
  2. empty detection result yields no automatic proposal instead of fabricated output
- Evidence: `TC-004`

## FLOW-004 Preserve downstream patch-first contracts

- Domain: decision and materialization
- Actor: decision engine
- Entry: live VLM and detector outputs are available
- Main path:
  1. merge live outputs into decision routing
  2. emit reasoned patches or manual-review tasks
  3. materialize a derived dataset view without touching source labels
- Evidence: `TC-005`
