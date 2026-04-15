# EP-006 Codex Review Integration

## Status

- Plan id: `EP-006`
- Milestone: `M7`
- State: completed
- Closure: `slice`

## Context

The repository started M7 with a provider-specific live review path that only
supported HTTP transport. The task closed by adding local `codex exec`
support, aligning the default review runtime with the local Codex setup, and
preserving the frozen `vlm_*` artifacts for downstream stages.

## Delivered

- runtime config support for a local `codex_cli` provider and the legacy HTTP
  review providers
- mocked local `codex exec` review execution with image input and parsed
  `vlm_review.json` output
- backward-compatible fixture mode and legacy HTTP-provider regression coverage
- synchronized README, roadmap, prompt, task docs, and execution-plan evidence

## Verification

```powershell
uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/codex-review-integration
```

## Residual Gap

- true local Codex execution still depends on the user's installed Codex login
  and profile state
- a future architecture task would still be needed to rename the historical
  `vlm_*` contracts without downstream churn
