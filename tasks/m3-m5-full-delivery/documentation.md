# Documentation - M3-M5 Full Delivery

## Readiness Gate

- `DG-001` required repo docs were read in `AGENTS.md` order: pass
- `DG-002` long-horizon memory files exist for the remaining work: pass
- `DG-003` M3-M5 task docs exist and are task-specific: pass
- `DG-004` optional closure docs exist and are task-specific: pass
- `DG-005` placeholder markers removed from task docs: pass
- `DG-006` active task-doc gate command passes: pass

## Log

### Entry: 2026-04-10 / DOC-001
- Scope: audited the repository after M2 and confirmed the remaining roadmap
  still needs `rules.py`, `risk.py`, `vlm.py`, `decision.py`,
  `detector_refine.py`, `materialize.py`, plus additional schemas and tests.
- Evidence: `docs/plan.md`, `docs/architecture.md`,
  `src/yolo_label_validation/`, `schemas/`
- Result: pass

### Entry: 2026-04-10 / DOC-002
- Scope: created long-horizon memory files for the remaining roadmap.
- Evidence: `SPEC.md`, `PLAN.md`, `RULES.md`, `STATUS.md`
- Result: pass

### Entry: 2026-04-10 / DOC-003
- Scope: rewrote the scaffolded M3-M5 task docs to reflect the remaining
  product milestones rather than the bootstrap template.
- Evidence: `tasks/m3-m5-full-delivery/`
- Result: pass

### Entry: 2026-04-10 / DOC-004
- Scope: run the task-doc gate before code edits.
- Evidence: `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery`
- Result: pass

### Entry: 2026-04-10 / FAIL-001
- Scope: `tests/test_rules.py` failed because `run_rule_checks()` stopped after
  `non_positive_box` and under-reported additional explicit rule issues on the
  same annotation.
- Trigger: `T-001` / `TC-002`
- Root-cause hypothesis: the rule engine short-circuits too early on invalid
  geometry and skips independent range checks.
- Confirmed root cause: `rules.py` used `continue` immediately after emitting
  `non_positive_box`, so `normalized_box_out_of_range` was never emitted for
  that record.
- Fix linkage: `CHG-001`
- Retest chain: targeted `uv run pytest -q tests/test_rules.py` -> pass;
  regression `uv run pytest -q` -> pass
- Result: closed

### Entry: 2026-04-10 / DOC-005
- Scope: implemented M3 rule/threshold/golden-set code paths and CLI support.
- Evidence: `src/yolo_label_validation/artifact_io.py`,
  `src/yolo_label_validation/rules.py`, `src/yolo_label_validation/cli.py`,
  `schemas/golden_set_manifest.schema.json`,
  `schemas/golden_eval_report.schema.json`,
  `schemas/rule_issue.schema.json`, `schemas/class_stats.schema.json`,
  `tests/support.py`, `tests/test_rules.py`, `tests/__init__.py`
- Result: pass

### Entry: 2026-04-10 / DOC-006
- Scope: validated the M3 slice with targeted and full regression runs.
- Evidence: `uv run pytest -q tests/test_rules.py`, `uv run pytest -q`
- Result: pass

### Entry: 2026-04-10 / FAIL-002
- Scope: `tests/test_risk.py` failed because `run_rules_for_directory()` erased
  populated upstream artifacts when `overwrite=True`, so the risk stage read an
  empty `normalized_annotations.jsonl`.
- Trigger: `T-001` / `TC-004`
- Root-cause hypothesis: the rules stage reused bootstrap overwrite semantics
  that are safe for empty workspaces but unsafe for staged runs.
- Confirmed root cause: `initialize_run_directory(..., overwrite=True)` was
  called inside `rules.py`, which rewrote `normalized_annotations.jsonl`,
  `image_index.json`, and `class_map.json` back to placeholders before M4 could
  read them.
- Fix linkage: `CHG-001`
- Retest chain: targeted `uv run pytest -q tests/test_rules.py` -> pass;
  targeted `uv run pytest -q tests/test_risk.py` -> pass
- Result: closed

### Entry: 2026-04-10 / DOC-007
- Scope: implemented the remaining M4 pipeline: deterministic VLM requests,
  schema-safe VLM review parsing, decision routing, patch generation, manual
  review queue emission, and CLI entrypoints for each stage.
- Evidence: `src/yolo_label_validation/bootstrap.py`,
  `src/yolo_label_validation/vlm.py`,
  `src/yolo_label_validation/decision.py`,
  `src/yolo_label_validation/cli.py`, `schemas/vlm_request.schema.json`,
  `schemas/vlm_review.schema.json`,
  `schemas/decision_result.schema.json`,
  `schemas/manual_review_item.schema.json`, `schemas/patch.schema.json`,
  `tests/test_vlm.py`, `tests/test_decision.py`
- Result: pass

### Entry: 2026-04-10 / DOC-008
- Scope: implemented the remaining M5 pipeline: detector-backed refine/add
  proposals, patch-applied materialization, run summary, metrics output, and
  the remaining CLI entrypoints.
- Evidence: `src/yolo_label_validation/detector_refine.py`,
  `src/yolo_label_validation/materialize.py`,
  `schemas/refine_result.schema.json`,
  `schemas/missing_result.schema.json`,
  `schemas/run_summary.schema.json`,
  `schemas/metrics_dashboard_source.schema.json`,
  `tests/test_detector_refine.py`, `tests/test_materialize.py`
- Result: pass

### Entry: 2026-04-10 / DOC-009
- Scope: validated the full remaining roadmap with regression, task-doc gate,
  and CLI smoke runs.
- Evidence: `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery`,
  `uv run python scripts/run_cli.py normalize-yolo --run-id cli-m45 --output-dir artifacts/runs/cli-m45 --images-dir artifacts/runs/_m45_cli_fixture/yolo-images --labels-dir artifacts/runs/_m45_cli_fixture/yolo-labels --class-names-file artifacts/runs/_m45_cli_fixture/classes.txt --dataset-version ds_m45 --class-map-version classes_m45 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite`,
  `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/cli-m45 --thresholds-file configs/thresholds.example.yaml --overwrite`,
  `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/cli-m45 --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-vlm --run-dir artifacts/runs/cli-m45 --responses-file artifacts/runs/_m45_cli_fixture/responses.json --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-decision --run-dir artifacts/runs/cli-m45 --defaults-file configs/defaults.json --overwrite`,
  `uv run python scripts/run_cli.py run-detector-refine --run-dir artifacts/runs/cli-m45 --thresholds-file configs/thresholds.example.yaml --overwrite`,
  `uv run python scripts/run_cli.py run-materialize --run-dir artifacts/runs/cli-m45 --overwrite`
- Result: pass

### Entry: 2026-04-10 / DOC-010
- Scope: tightened the decision fallback so annotations with blocking rule
  errors route to manual review even when they were not sampled into the VLM
  stage.
- Evidence: `src/yolo_label_validation/decision.py`,
  `tests/test_decision.py`,
  `uv run pytest -q tests/test_decision.py`,
  `uv run pytest -q`
- Result: pass
