# Business Process Map - M3-M5 Full Delivery

## FLOW-001 Load thresholds and golden-set contracts

- Domain: validation bootstrap
- Actor: local audit pipeline
- Entry: normalized artifacts are ready for rule evaluation
- Main path:
  1. load threshold policy from config or provided payload
  2. freeze `thresholds_version` and snapshot the policy
  3. build or load a golden-set manifest and evaluation placeholders
- Exception paths:
  1. malformed threshold payloads fail fast
  2. missing version fields fail fast
- Satisfies: `REQ-001`
- Evidence: `UAT-001`, `TC-001`

## FLOW-002 Validate normalized annotations

- Domain: explicit rule checks
- Actor: rule engine
- Entry: normalized annotations and image index are loaded
- Main path:
  1. detect invalid classes and invalid geometry
  2. detect duplicate or suspicious overlaps
  3. emit structured rule issues with severity, reason, and auto-action hints
- Exception paths:
  1. malformed normalized records fail fast
  2. missing lineage or missing class map fail fast
- Satisfies: `REQ-002`
- Evidence: `UAT-002`, `TC-002`

## FLOW-003 Summarize class-level statistics

- Domain: stats and thresholds
- Actor: rule engine
- Entry: normalized annotations have been validated
- Main path:
  1. aggregate counts and area statistics by class
  2. attach threshold snapshot metadata
  3. emit deterministic `class_stats.json`
- Satisfies: `REQ-003`
- Evidence: `UAT-003`, `TC-003`

## FLOW-004 Rank risk and sample review candidates

- Domain: model-assisted triage
- Actor: risk engine
- Entry: normalized annotations, rule issues, and class stats are ready
- Main path:
  1. compute risk signals and fused scores
  2. rank images and annotations
  3. emit `risk_scores.json` and `review_candidates.json`
- Satisfies: `REQ-004`
- Evidence: `UAT-004`, `TC-004`

## FLOW-005 Build and parse VLM review protocol

- Domain: structured semantic review
- Actor: VLM adapter
- Entry: review candidates are ready
- Main path:
  1. serialize VLM requests deterministically
  2. accept only schema-safe VLM response payloads
  3. emit parsed `vlm_review.json`
- Exception paths:
  1. invalid JSON or invalid decisions are rejected
- Satisfies: `REQ-005`
- Evidence: `UAT-005`, `TC-005`

## FLOW-006 Route decisions and patches

- Domain: decision and patching
- Actor: decision engine
- Entry: rules, risk, VLM, and detector evidence are available
- Main path:
  1. merge evidence into decision results
  2. emit patch records for automatic actions
  3. route uncertain cases to manual review
- Satisfies: `REQ-006`
- Evidence: `UAT-006`, `TC-006`

## FLOW-007 Propose refine and add actions

- Domain: detector-backed geometry
- Actor: detector refine engine
- Entry: candidate annotations require geometric confirmation
- Main path:
  1. emit refine proposals for existing boxes
  2. emit missing-object proposals
  3. preserve reasons and confidence for downstream decisions
- Satisfies: `REQ-007`
- Evidence: `UAT-007`, `TC-007`

## FLOW-008 Materialize patch-applied dataset views

- Domain: export and training compatibility
- Actor: materialization engine
- Entry: patches and manual queue status are finalized
- Main path:
  1. apply patches to source-derived views without mutating source files
  2. emit `materialized_dataset/` and related manifests
- Satisfies: `REQ-008`
- Evidence: `UAT-008`, `TC-007`

## FLOW-009 Summarize the full run

- Domain: ops and reporting
- Actor: materialization engine
- Entry: all prior artifact sets exist
- Main path:
  1. aggregate counts and route outcomes
  2. emit `run_summary.json`
  3. emit `metrics_dashboard_source.json`
- Satisfies: `REQ-009`
- Evidence: `UAT-009`, `TC-008`
