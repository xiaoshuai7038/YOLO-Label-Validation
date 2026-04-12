# EP-005 Production Integrations

## Status

- Plan id: `EP-005`
- Milestone: `M6`
- State: completed
- Closure: `slice`

## Context

The repository started M6 with a fixture-only VLM stage and a detector stub
stage. The task closed by wiring both to production-oriented runtimes while
preserving fixture mode and stable downstream contracts.

## Delivered

- one committed runtime config file for live VLM and detector settings
- real OpenAI-compatible multimodal VLM transport with local image data URLs
- real Ultralytics-compatible detector inference path with runtime metadata
- green regression and mock-backed CLI smoke for both live-stage entrypoints

## Verification

```powershell
uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py tests/test_detector_refine.py
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration
```

## Residual Gap

- true credentialed endpoint execution still depends on the user's API key
- true detector execution still depends on the user's weights path and hardware
