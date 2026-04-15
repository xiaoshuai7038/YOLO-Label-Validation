# Discovery Report - Codex Review Integration

## Task

- Task slug: `codex-review-integration`

## Confirmed

- Repository mode: harness-first Python project with semantic review centered in
  `src/yolo_label_validation/vlm.py`
- Current live review path originally supported an HTTP transport configured by
  `configs/runtime.integration.json`
- Downstream stages consume frozen `vlm_*` artifacts and
  `run_manifest.runtime_context.vlm`; renaming those contracts would ripple
  through `decision.py`, `detector_refine.py`, `materialize.py`, and tests
- Existing review entrypoint is the `run-vlm` CLI command in
  `src/yolo_label_validation/cli.py`
- Current regression surface for this stage lives in
  `tests/test_vlm.py` and `tests/test_runtime_config.py`
- The local environment exposes `codex exec` with `--image`,
  `--output-schema`, and `--output-last-message`, which is enough to run the
  review stage without any direct HTTP integration

## Existing Documentation Health

| File | Status | Issue | Action |
|---|---|---|---|
| `README.md` | salvageable | accurately describes the pipeline but still frames the reviewer as a generic VLM stage | keep and clarify the new provider option |
| `docs/srs_v1.md` | salvageable | frozen technology choice names `Qwen2.5-VL`, which is now too specific for the runtime layer | keep as historical source doc and note the provider abstraction |
| `docs/project_spec.md` | healthy | artifact and priority rules are still correct | keep |
| `docs/prompt.md` | stale | current milestone is closed around the prior VLM integration task | replace with the new active milestone |
| `docs/plan.md` | salvageable | M6 is complete, but a new follow-up milestone is now needed | extend with a new milestone |
| `tasks/production-vlm-detector-integration/` | salvageable | useful implementation history, but scoped to the old provider-specific live path | keep as prior task evidence and do not reuse as the active task |

## Commands Discovered

- `uv run pytest -q`
- `uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration`
- `uv run python scripts/run_cli.py run-vlm --run-dir <dir> --runtime-config <file> --overwrite`
- `uv run python scripts/run_cli.py run-detector-refine --run-dir <dir> --runtime-config <file> --overwrite`

## Notes

- The lowest-risk change is to preserve `vlm_*` artifact names and make the
  provider behind the semantic-review stage pluggable.
- A full rename from `vlm` to `review_model` is deferred because it would cross
  more than 5 core files and violate the repo's escalation guidance for this
  iteration.
