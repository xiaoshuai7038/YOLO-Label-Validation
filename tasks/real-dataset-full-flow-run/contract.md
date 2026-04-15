# Contract - Real Dataset Full Flow Run

## Goal

Run the full harness pipeline on the real dataset at
`E:\workspace\cigarette-identify\预标注测试\20264010` using the local Codex CLI
review runtime and produce end-to-end artifacts through materialization.

## Scope

- real-dataset normalization into a dedicated run workspace
- rules, risk, VLM review, detector refine, decision, and materialization
- validation of artifact counts and key lineage contracts at each stage
- recording real-runtime failures and mitigations when they appear

## Out of Scope

- changing the source dataset
- changing the dataset content beyond emitted patches and materialized outputs
- large feature refactors unrelated to finishing the real run

## Closure Level

- Target closure: `run`
- Meaning: the real dataset completes the local pipeline and leaves a valid run
  workspace plus a short execution record

## Done When

- `DW-001` a dedicated real-run workspace is created and normalized from the
  source dataset
- `DW-002` `run-rules` and `run-risk` complete on the real run and record
  candidate scale
- `DW-003` `run-vlm` completes on the real run using the local `codex_cli`
  provider
- `DW-004` `run-detector-refine`, `run-decision`, and `run-materialize`
  complete on the same run
- `DW-005` final artifact counts and output paths are recorded in task docs
- `DW-006` any runtime-specific failures discovered during the run are logged
  with root cause and mitigation

## Changes

- `CHG-001` create and manage a dedicated run workspace for the real dataset
- `CHG-002` execute normalization, rules, and risk on the real dataset
- `CHG-003` execute local Codex VLM review on the real candidate set
- `CHG-004` execute detector refine, decision, and materialization on the same
  run
- `CHG-005` record real-run evidence, counts, and failures in task docs

## Coverage

- `COV-001` `scripts/run_cli.py normalize-yolo` on the real dataset path
- `COV-002` `scripts/run_cli.py run-rules` and `run-risk` on the same run dir
- `COV-003` `scripts/run_cli.py run-vlm` with
  `configs/runtime.integration.json`
- `COV-004` `scripts/run_cli.py run-detector-refine`,
  `run-decision`, and `run-materialize`
- `COV-005` `tasks/real-dataset-full-flow-run/documentation.md`

## Validation Plan

- `TC-001` normalization reproduces the known real-dataset shape
- `TC-002` risk stage emits both annotation-level and image-level candidates
- `TC-003` local Codex review completes and writes `vlm_*` artifacts
- `TC-004` downstream stages preserve image-level and annotation-level lineage
- `TC-005` materialization completes and writes the final run summary artifacts
- `TC-006` task-doc gate stays green while the run evidence is updated

- `T-001` `uv run python scripts/check_task_docs.py tasks/real-dataset-full-flow-run`
- `T-002` `uv run python scripts/run_cli.py normalize-yolo --run-id real-full-flow --output-dir artifacts/runs/real-full-flow --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_full_flow --class-map-version classes_real_full_flow --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite`
- `T-003` `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-full-flow --overwrite`
- `T-004` `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite`
- `T-005` `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --runtime-config configs/runtime.integration.json --overwrite`
- `T-006` `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/real-full-flow --overwrite`
- `T-007` `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-full-flow --defaults-file configs/defaults.json --overwrite`
- `T-008` `uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/real-full-flow --overwrite`
