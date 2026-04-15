# documentation.md - Experiment & Change Log

Record every meaningful change here. Keep only the most recent entries in this
file and archive older ones if needed.

## Log

### Iteration: 2026-04-14
- **Milestone**: post-M9 utility
- **Change**: added a formal `export-yolo` CLI path that converts a
  materialized run into a ready-to-use YOLO dataset with copied source images,
  derived labels, `classes.txt`, `dataset.yaml`, and an export manifest, then
  ran it on `artifacts/runs/real-full-flow`
- **Files modified**: `src/yolo_label_validation/materialize.py`,
  `src/yolo_label_validation/cli.py`, `tests/test_materialize.py`,
  `tasks/materialized-yolo-export/`, `README.md`, `docs/architecture.md`,
  `docs/documentation.md`
- **Verification result**: pass (`uv run pytest -q tests/test_materialize.py`,
  `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/materialized-yolo-export`,
  `uv run python scripts/run_cli.py export-yolo --run-dir artifacts/runs/real-full-flow --overwrite`)
- **Decision**: complete
- **Next step**: none; the exported YOLO dataset is available under
  `artifacts/runs/real-full-flow/materialized_yolo/`

### Iteration: 2026-04-13
- **Milestone**: M9
- **Change**: closed the zero-annotation image-review gap by redefining the
  review universe from `image_index`, adding explicit `review_scope` metadata
  across risk/VLM/decision artifacts, preserving image-level missing proposals
  into downstream patches, and hardening local Codex execution for Windows
  command resolution plus a more realistic timeout baseline
- **Files modified**: `configs/defaults.json`,
  `configs/runtime.integration.json`, `src/yolo_label_validation/risk.py`,
  `src/yolo_label_validation/vlm.py`,
  `src/yolo_label_validation/detector_refine.py`,
  `src/yolo_label_validation/decision.py`,
  `schemas/risk_score.schema.json`, `schemas/review_candidate.schema.json`,
  `schemas/vlm_request.schema.json`, `schemas/vlm_review.schema.json`,
  `schemas/missing_result.schema.json`,
  `schemas/decision_result.schema.json`,
  `schemas/manual_review_item.schema.json`, `tests/support.py`,
  `tests/test_risk.py`, `tests/test_vlm.py`,
  `tests/test_detector_refine.py`, `tests/test_decision.py`,
  `tasks/zero-annotation-image-review/`, `docs/failures/taxonomy.md`,
  `docs/prompt.md`, `docs/plan.md`, `docs/documentation.md`,
  `docs/architecture.md`, `README.md`, `PLANS.md`,
  `docs/exec-plans/completed/EP-008-zero-annotation-image-review.md`
- **Verification result**: pass (`uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review`,
  `uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py`,
  `uv run pytest -q`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite`,
  `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-smoke --overwrite`,
  `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-smoke --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/real-zero-one-vlm --defaults-file configs/defaults.json --runtime-config configs/runtime.integration.json --overwrite`,
  `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/real-zero-one-vlm --overwrite`,
  `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/real-zero-one-vlm --defaults-file configs/defaults.json --overwrite`)
- **Decision**: complete at `slice`
- **Next step**: start M10 cost and policy tuning for the expanded
  zero-annotation image-review workload

### Iteration: 2026-04-13
- **Milestone**: M8
- **Change**: added explicit YOLO pairing-mode support so a real mixed
  image/label directory with trailing `__hash` filename suffixes can normalize
  directly into canonical artifacts without renaming source files
- **Files modified**: `src/yolo_label_validation/ingest.py`,
  `src/yolo_label_validation/cli.py`, `tests/test_ingest.py`,
  `tasks/real-dataset-yolo-ingest/`, `docs/prompt.md`, `docs/plan.md`,
  `docs/documentation.md`, `docs/architecture.md`, `README.md`, `PLANS.md`,
  `docs/exec-plans/completed/EP-007-real-dataset-yolo-ingest.md`
- **Verification result**: pass (`uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest`,
  `uv run pytest -q tests/test_ingest.py`, `uv run pytest -q`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite`,
  `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-smoke --overwrite`,
  `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-smoke --defaults-file configs/defaults.json --overwrite`)
- **Decision**: complete at `slice`
- **Next step**: redesign the annotation-driven `risk -> vlm -> decision` path
  so zero-annotation images can receive image-level missing-object review

### Iteration: 2026-04-13
- **Milestone**: M7
- **Change**: added local Codex CLI review-runtime support while preserving the
  frozen `vlm_*` artifacts, kept the legacy HTTP provider paths working,
  aligned the default review runtime with the local Codex setup, and synced the
  roadmap/task docs around the new provider direction
- **Files modified**: `configs/runtime.integration.json`,
  `configs/defaults.json`, `src/yolo_label_validation/runtime_config.py`,
  `src/yolo_label_validation/vlm.py`, `src/yolo_label_validation/cli.py`,
  `src/yolo_label_validation/contracts.py`,
  `schemas/runtime_integration.schema.json`,
  `tests/test_runtime_config.py`, `tests/test_vlm.py`,
  `tasks/codex-review-integration/`, `docs/prompt.md`, `docs/plan.md`,
  `docs/architecture.md`, `docs/documentation.md`, `README.md`, `PLANS.md`,
  `docs/exec-plans/completed/EP-006-codex-review-integration.md`
- **Verification result**: pass (`uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py`,
  `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/codex-review-integration`,
  real local smoke via `codex exec --image --output-schema ...`)
- **Decision**: complete at `slice`
- **Next step**: run a true local smoke with the operator's installed Codex
  profile and dataset sample

### Iteration: 2026-04-10
- **Milestone**: M6
- **Change**: implemented a committed runtime integration config, live
  OpenAI-compatible multimodal VLM transport with local-image data URLs, live
  Ultralytics detector integration with manifest runtime propagation, and
  mock-backed regression plus CLI smoke coverage
- **Files modified**: `configs/runtime.integration.json`,
  `src/yolo_label_validation/runtime_config.py`,
  `src/yolo_label_validation/vlm.py`,
  `src/yolo_label_validation/detector_refine.py`,
  `src/yolo_label_validation/cli.py`,
  `src/yolo_label_validation/contracts.py`,
  `schemas/runtime_integration.schema.json`,
  `schemas/run_manifest.schema.json`,
  `tests/test_runtime_config.py`,
  `tests/test_vlm.py`,
  `tests/test_detector_refine.py`,
  `tasks/production-vlm-detector-integration/`,
  `docs/plan.md`,
  `docs/prompt.md`,
  `PLANS.md`,
  `STATUS.md`
- **Verification result**: pass (`uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py tests/test_detector_refine.py`,
  `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/production-vlm-detector-integration`,
  mocked CLI smoke for live `run-vlm` and live `run-detector-refine`)
- **Decision**: complete at `slice`
- **Next step**: wait for environment-specific credentialed smoke with real API
  key and detector weights

### Iteration: 2026-04-10
- **Milestone**: Closeout docs
- **Change**: added a Mermaid sequence diagram for the end-to-end YOLO label
  validation flow so the CLI-to-artifact lifecycle is visible in one place
- **Files modified**: `docs/architecture.md`, `docs/documentation.md`
- **Verification result**: n/a (documentation-only update)
- **Decision**: continue
- **Next step**: none

### Iteration: 2026-04-10
- **Milestone**: M5
- **Change**: implemented detector-backed refine/add proposal artifacts,
  patch-applied materialization, run summaries, metrics export, and the
  remaining CLI entrypoints
- **Files modified**: `src/yolo_label_validation/detector_refine.py`,
  `src/yolo_label_validation/materialize.py`,
  `src/yolo_label_validation/decision.py`,
  `src/yolo_label_validation/cli.py`,
  `schemas/refine_result.schema.json`,
  `schemas/missing_result.schema.json`,
  `schemas/run_summary.schema.json`,
  `schemas/metrics_dashboard_source.schema.json`,
  `tests/test_detector_refine.py`, `tests/test_materialize.py`,
  `tasks/m3-m5-full-delivery/`, `docs/plan.md`, `docs/prompt.md`, `PLANS.md`
- **Verification result**: pass (`uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id cli-m45 --output-dir artifacts/runs/cli-m45 --images-dir artifacts/runs/_m45_cli_fixture/yolo-images --labels-dir artifacts/runs/_m45_cli_fixture/yolo-labels --class-names-file artifacts/runs/_m45_cli_fixture/classes.txt --dataset-version ds_m45 --class-map-version classes_m45 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite`,
  `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/cli-m45 --thresholds-file configs/thresholds.example.yaml --overwrite`,
  `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/cli-m45 --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/cli-m45 --responses-file artifacts/runs/_m45_cli_fixture/responses.json --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/cli-m45 --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/cli-m45 --thresholds-file configs/thresholds.example.yaml --overwrite`,
  `uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/cli-m45 --overwrite`)
- **Decision**: complete
- **Next step**: none

### Iteration: 2026-04-10
- **Milestone**: M4
- **Change**: implemented deterministic risk/VLM/decision flow, added request
  and decision schemas, and fixed downstream artifact clobbering so M4 stages
  preserve normalized upstream inputs
- **Files modified**: `src/yolo_label_validation/bootstrap.py`,
  `src/yolo_label_validation/risk.py`, `src/yolo_label_validation/vlm.py`,
  `src/yolo_label_validation/decision.py`,
  `src/yolo_label_validation/cli.py`,
  `schemas/risk_score.schema.json`, `schemas/review_candidate.schema.json`,
  `schemas/vlm_request.schema.json`, `schemas/vlm_review.schema.json`,
  `schemas/decision_result.schema.json`,
  `schemas/manual_review_item.schema.json`, `schemas/patch.schema.json`,
  `tests/test_risk.py`, `tests/test_vlm.py`, `tests/test_decision.py`,
  `tests/test_rules.py`, `tests/support.py`, `docs/failures/taxonomy.md`,
  `tasks/m3-m5-full-delivery/`
- **Verification result**: pass (`uv run pytest -q tests/test_rules.py`,
  `uv run pytest -q tests/test_risk.py`, `uv run pytest -q tests/test_vlm.py`,
  `uv run pytest -q tests/test_decision.py`, `uv run pytest -q`)
- **Decision**: continue
- **Next step**: implement M5 detector refine, materialization, and run summary

### Iteration: 2026-04-10
- **Milestone**: M3
- **Change**: implemented threshold loading, golden-set contracts, explicit
  rule validation, deterministic class stats, and a `run-rules` CLI entrypoint
- **Files modified**: `src/yolo_label_validation/artifact_io.py`,
  `src/yolo_label_validation/rules.py`, `src/yolo_label_validation/cli.py`,
  `schemas/golden_set_manifest.schema.json`,
  `schemas/golden_eval_report.schema.json`,
  `schemas/rule_issue.schema.json`, `schemas/class_stats.schema.json`,
  `tests/support.py`, `tests/test_rules.py`, `tests/__init__.py`,
  `tasks/m3-m5-full-delivery/`, `docs/failures/taxonomy.md`
- **Verification result**: pass (`uv run pytest -q tests/test_rules.py`,
  `uv run pytest -q`)
- **Decision**: continue
- **Next step**: promote M3 to completed and implement M4 risk, VLM, and
  decision routing

### Iteration: 2026-04-10
- **Milestone**: M2
- **Change**: implemented FR-001/FR-002 input normalization for YOLO txt and
  COCO JSON with deterministic artifact writers, class-map validation, source
  lineage, and CLI entrypoints for both formats
- **Files modified**: `src/yolo_label_validation/contracts.py`,
  `src/yolo_label_validation/ingest.py`, `src/yolo_label_validation/cli.py`,
  `schemas/run_manifest.schema.json`, `schemas/normalized_annotation.schema.json`,
  `schemas/image_index.schema.json`, `schemas/class_map.schema.json`,
  `tests/test_ingest.py`, `tasks/m2-input-normalization/`
- **Verification result**: pass (`uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/m2-input-normalization`,
  `uv run python scripts/run_cli.py show-layout`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id smoke-yolo --output-dir artifacts/runs/smoke-yolo --images-dir artifacts/runs/_m2_cli_fixtures/yolo-images --labels-dir artifacts/runs/_m2_cli_fixtures/yolo-labels --class-names-file artifacts/runs/_m2_cli_fixtures/classes.txt --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite`,
  `uv run python scripts/run_cli.py normalize-coco --run-id smoke-coco --output-dir artifacts/runs/smoke-coco --annotation-file artifacts/runs/_m2_cli_fixtures/annotations.json --images-dir artifacts/runs/_m2_cli_fixtures/coco-images --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite`)
- **Decision**: continue
- **Next step**: promote M2 to completed and start FR-003/FR-004/FR-005 rule
  validation, golden-set, and threshold work

### Iteration: 2026-04-10
- **Milestone**: M1
- **Change**: initialized the repository as a harness-first project with docs,
  schemas, config defaults, and a bootstrap CLI for run workspaces
- **Files modified**: repository scaffold
- **Verification result**: pass (`pytest -q`, `python scripts/run_cli.py show-layout`,
  `python scripts/run_cli.py init-run --run-id smoke-run --output-dir artifacts\runs\smoke-run`)
- **Decision**: continue
- **Next step**: implement FR-001/FR-002 input normalization and source lineage

### Iteration: 2026-04-10
- **Milestone**: M1 hardening
- **Change**: added task-scoped execution docs, reusable doc scaffold scripts,
  a task-doc gate, and CI wiring for the same local quality gates
- **Files modified**: `tasks/`, `scripts/init_context_docs.py`,
  `scripts/init_task_docs.py`, `scripts/check_task_docs.py`,
  `src/yolo_label_validation/task_docs.py`,
  `src/yolo_label_validation/doc_check.py`, `.github/workflows/ci.yml`,
  `tests/test_task_docs.py`
- **Verification result**: pass (`pytest -q`,
  `python scripts\check_task_docs.py tasks\repo-harness-bootstrap`,
  `python scripts\run_cli.py show-layout`)
- **Decision**: continue
- **Next step**: start FR-001/FR-002 ingestion implementation with fixture data

### Iteration: 2026-04-10
- **Milestone**: M1 hardening
- **Change**: fixed GitHub Actions CI by declaring a `test` extra in
  `pyproject.toml` and installing `.[test]` before running `python -m pytest`
- **Files modified**: `pyproject.toml`, `.github/workflows/ci.yml`
- **Verification result**: pass (`python -m pip install -e ".[test]"`,
  `python -m pytest -q`, `python scripts\check_task_docs.py tasks\repo-harness-bootstrap`)
- **Decision**: continue
- **Next step**: wait for GitHub Actions to rerun with the updated workflow
