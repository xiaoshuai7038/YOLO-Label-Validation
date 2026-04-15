# EP-007 Real Dataset YOLO Ingest

## Status

- Plan id: `EP-007`
- Milestone: `M8`
- State: completed
- Closure: `slice`

## Context

The repository could already normalize standard YOLO directory layouts, but the
real dataset at `E:\workspace\cigarette-identify\预标注测试\20264010` exposed a
practical incompatibility: images and labels were mixed in one directory and
paired filenames could differ only by a trailing `__hash` suffix.

## Delivered

- explicit YOLO `pairing_mode` support with
  `stem_before_double_underscore`
- `normalize-yolo` CLI exposure for the new pairing mode
- regression tests for mixed-directory hash-pair ingestion and preserved
  unlabeled images
- successful real-dataset normalization into canonical artifacts without source
  file renaming

## Verification

```powershell
uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest
uv run pytest -q tests/test_ingest.py
uv run pytest -q
uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite
uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-smoke --overwrite
uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-smoke --defaults-file configs/defaults.json --overwrite
```

## Residual Gap

- `245` zero-annotation images remain outside `review_candidates.json`
  because the current `risk -> vlm -> decision` flow is annotation-driven
- a follow-up architecture slice is required to support image-level missing
  review for empty-prelabel images
