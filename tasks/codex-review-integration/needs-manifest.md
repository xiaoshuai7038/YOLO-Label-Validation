# Needs Manifest - Codex Review Integration

## Task

- Task slug: `codex-review-integration`

## Blocking Needs

- None. This task can proceed with a safe default: preserve existing `vlm_*`
  contracts and add a local `codex_cli` provider beside the current HTTP
  providers.

## Non-Blocking Needs

- A real local Codex login/profile for a true live smoke after local regression
  is green
- Final operator choice of Codex profile/model when the repo wants to override
  the global CLI defaults
- Real dataset samples for latency and cost tuning beyond unit and mock tests

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| Full artifact rename away from `vlm_*` | too much contract churn for a provider swap task | future architecture refactor |
| Deeper prompt/schema hardening for local Codex review | current parser and output schema already enforce the output contract locally | future prompt-hardening task |
| End-to-end live smoke against the operator's real Codex setup | depends on local login/profile state outside regression tests | post-implementation validation |

## Assumptions

- The semantic-review stage may keep its historical `vlm` naming as long as the
  runtime path and docs clearly state that the backend reviewer is now
  provider-configurable.
- Local Codex integration should be implemented without adding a mandatory SDK
  dependency when the existing standard-library HTTP seam is sufficient.
