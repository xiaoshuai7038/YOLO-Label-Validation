# Documentation - Zero Annotation Image Review

## Readiness Gate

- `DG-001` required repo docs exist: pass
- `DG-002` required task docs exist: pass
- `DG-003` no placeholder markers remain: pass
- `DG-004` active task-doc gate command passes: pass

## Failure Loop

### FAIL-001
- Trigger: `TC-008` / `T-004`
- Observed failure: `run-vlm` on Windows could launch `codex --version` from
  PowerShell but failed to launch `codex` from Python `subprocess.run(...)`
  inside the harness, which blocked the real local Codex smoke
- Root-cause hypothesis: the harness passed the configured command name
  directly into `subprocess.run`, but Windows command resolution for
  `shell=False` did not resolve the installed `codex.cmd` wrapper the same way
  PowerShell did
- Confirmation: `subprocess.run(["codex", "--version"])` failed with
  `FileNotFoundError`, while `subprocess.run(["codex.cmd", "--version"])` and
  `shutil.which("codex")` succeeded
- Fix: resolve the configured Codex command through `shutil.which(...)` before
  spawning the subprocess and add regression coverage in `tests/test_vlm.py`
- Retest: `uv run pytest -q tests/test_vlm.py`; real local Codex mini-run
  advanced from command-launch failure to a model-timeout failure
- Status: closed

### FAIL-002
- Trigger: `TC-008` / `T-004`
- Observed failure: the first real image-level local Codex smoke timed out at
  `180s` even after command resolution was fixed
- Root-cause hypothesis: the committed runtime example used a timeout that was
  too low for real local Codex image review on this machine
- Confirmation:
  - a minimal `codex exec` JSON smoke took roughly `115s` and showed multiple
    reconnect attempts
  - the same real image-level request succeeded in roughly `161s` when the
    timeout was raised to `600s`
- Fix: raise the example `configs/runtime.integration.json` live-review timeout
  baseline from `180` to `600` seconds
- Retest: `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/real-zero-one-vlm --defaults-file configs/defaults.json --runtime-config configs/runtime.integration.json --overwrite`
- Status: closed

## Log

### Entry: 2026-04-13 / DOC-001
- Scope: created task-scoped docs for the zero-annotation image-review slice
- Evidence: `tasks/zero-annotation-image-review/`
- Result: pass

### Entry: 2026-04-13 / DOC-002
- Scope: confirmed the architectural root cause of the skip bug
- Evidence:
  - real dataset contains `245` zero-annotation images
  - `run-risk` on the real dataset emitted `1088` risk rows and `28`
    candidate images, with `0` zero-annotation images in
    `review_candidates.json`
  - `src/yolo_label_validation/risk.py` builds the review universe from
    `normalized_annotations`
  - `schemas/review_candidate.schema.json` only models
    `candidate_annotations`
  - `schemas/vlm_request.schema.json` requires `ann_id` and
    `annotation_context`
- Result: pass
- Notes: the original design mistake was treating existing annotations as the
  entire review universe, which collapses image-level missing-object cases out
  of the harness entirely

### Entry: 2026-04-13 / DOC-003
- Scope: implemented the image-level review path across risk, VLM, detector,
  decision, and schema layers
- Evidence:
  - `src/yolo_label_validation/risk.py` now emits image-scope risk rows and
    `review_candidates.json` image-level candidates for zero-annotation images
  - `src/yolo_label_validation/vlm.py`,
    `src/yolo_label_validation/detector_refine.py`, and
    `src/yolo_label_validation/decision.py` now preserve explicit
    `review_scope`
  - `schemas/risk_score.schema.json`,
    `schemas/review_candidate.schema.json`,
    `schemas/vlm_request.schema.json`,
    `schemas/vlm_review.schema.json`,
    `schemas/missing_result.schema.json`,
    `schemas/decision_result.schema.json`, and
    `schemas/manual_review_item.schema.json` now model image-level review
    directly instead of forcing fake annotation ids
- Result: pass

### Entry: 2026-04-13 / DOC-004
- Scope: validated the zero-annotation review path on tests and on the real
  dataset
- Evidence:
  - `uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review`
  - `uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py`
  - `uv run pytest -q`
  - real dataset `run-risk` emitted `1333` risk rows, including `245`
    image-level rows for zero-annotation images
  - `review_candidates.json` contains `245` image-level candidates and misses
    `0` of the `245` zero-annotation images
  - real mini-run `artifacts/runs/real-zero-one-vlm/` completed
    `run-vlm -> run-detector-refine -> run-decision` and produced
    `vlm_review.json`, `missing_results.json`, `decision_results.json`, and
    `patches.json` with `review_scope: image` and `ann_id: null`
- Result: pass
