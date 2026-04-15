# Documentation - Real Dataset YOLO Ingest Adapter

## Readiness Gate

- `DG-001` required repo docs exist: pass
- `DG-002` required task docs exist: pass
- `DG-003` no placeholder markers remain: pass
- `DG-004` active task-doc gate command passes: pass

## Log

### Entry: 2026-04-13 / DOC-001
- Scope: created and specialized the task-scoped discovery, needs, contract,
  plan, implement, and documentation docs for the real dataset ingest slice
- Evidence: `tasks/real-dataset-yolo-ingest/`
- Result: pass

### Entry: 2026-04-13 / DOC-002
- Scope: inspected the real dataset layout and reproduced the current ingest
  failure mode
- Evidence:
  - dataset counts: `520` images, `275` label files, `1088` boxes
  - exact-stem match count: `171`
  - normalized `stem_before_double_underscore` distribution:
    `275` paired keys, `245` image-only keys, `0` ambiguous collisions
  - failure command: `uv run python scripts/run_cli.py normalize-yolo ...`
  - failure text:
    `label file 01f0b_11-16-50_1__f7d9b7.txt has no matching image`
- Result: pass

### Entry: 2026-04-13 / DOC-003
- Scope: identified a deferred downstream gap outside this task's closure
- Evidence: `src/yolo_label_validation/risk.py`,
  `src/yolo_label_validation/vlm.py`, visual inspection of unlabeled image
  `021dfc759ed044bfa907748f1eb12c78_1050_1.jpeg`
- Result: pass
- Notes: zero-annotation images currently survive ingest but are skipped by the
  annotation-driven `risk -> vlm -> decision` flow; this follow-up is deferred
  deliberately and must not be conflated with ingest compatibility

### Entry: 2026-04-13 / DOC-004
- Scope: implemented the pairing-mode ingest slice and validated it against
  fixtures plus the real dataset
- Evidence:
  - `src/yolo_label_validation/ingest.py`
  - `src/yolo_label_validation/cli.py`
  - `tests/test_ingest.py`
  - `uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest`
  - `uv run pytest -q tests/test_ingest.py`
  - `uv run pytest -q`
  - `uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite`
  - `uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-smoke --overwrite`
  - `uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-smoke --defaults-file configs/defaults.json --overwrite`
- Result: pass
- Notes:
  - real dataset normalization now succeeds with `520` images, `1088`
    annotations, and `1` class
  - `245` zero-annotation images remain present in `image_index.json`
  - `0` zero-annotation images appear in `review_candidates.json`, confirming
    the deferred downstream gap is real
