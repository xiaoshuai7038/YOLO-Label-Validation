# Implement - Real Dataset Full Flow Run

## Execution Rules

- use the committed CLI entrypoints unless a real-runtime blocker requires a
  narrowly scoped workaround
- keep the source dataset read-only
- prefer stage-by-stage execution so counts and failures can be captured
- update task documentation after each completed stage or confirmed failure

## Iteration Loop

1. keep `tasks/real-dataset-full-flow-run/contract.md`,
   `plan.md`, and `documentation.md` synchronized
2. run the next stage command from the validation route
3. inspect the stage outputs and record counts or failures
4. if a runtime failure occurs, open a `FAIL-*` record before changing code
5. retest the smallest failed stage first, then continue the pipeline
6. stop only when materialization completes or a true external blocker remains

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/real-dataset-full-flow-run
uv run python scripts/run_cli.py normalize-yolo --run-id real-full-flow --output-dir artifacts/runs/real-full-flow --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_full_flow --class-map-version classes_real_full_flow --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite
uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-full-flow --overwrite
uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite
uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --runtime-config configs/runtime.integration.json --overwrite
uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/real-full-flow --overwrite
uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite
uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/real-full-flow --overwrite
```

## Escalation

- if `run-vlm` runtime is materially slower than the current timeout, record
  the observed timing and only then adjust the runtime config or execution
  method
- if detector live weights are unavailable, continue with the committed default
  path and record the mode in the task documentation
