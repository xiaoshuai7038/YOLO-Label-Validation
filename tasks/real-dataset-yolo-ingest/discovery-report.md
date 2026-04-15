# Discovery Report

## Task

- Task slug: `real-dataset-yolo-ingest`
- Real dataset path: `E:\workspace\cigarette-identify\预标注测试\20264010`

## Confirmed

- Repository mode: harness-first Python pipeline for fixed-class 2D detection
  audit runs.
- Relevant entrypoints: `uv run python scripts/run_cli.py normalize-yolo`,
  `uv run python scripts/run_cli.py run-vlm`, `uv run pytest -q`.
- Current YOLO ingest contract assumes `images_dir` and `labels_dir` are read
  separately and that label stem equals image stem exactly.
- The real dataset is a single mixed directory containing both `.jpeg` images
  and `.txt` YOLO labels.
- Real dataset facts:
  - `520` images
  - `275` label files
  - `1088` total boxes
  - all parsed label rows are valid YOLO 5-field rows
  - all class ids are `0`
- Exact-stem pairing only matches `171` image/label pairs.
- After removing a trailing `__hash` suffix from file stems, pairing becomes
  unambiguous:
  - `275` keys with `1 image + 1 label`
  - `245` keys with `1 image + 0 label`
  - `0` ambiguous collisions
- Real smoke with the current command fails immediately:
  `label file 01f0b_11-16-50_1__f7d9b7.txt has no matching image`.
- Sample unlabeled images still visibly contain cigarette cartons, so
  zero-annotation images are not safe to treat as guaranteed negatives.

## Existing Documentation Health

| File | Status | Action |
|---|---|---|
| `README.md` | salvageable | update after implementation to document real-dataset ingest mode |
| `docs/project_spec.md` | healthy | keep |
| `docs/architecture.md` | salvageable | update the YOLO ingest assumptions after the new pairing mode lands |
| `docs/prompt.md` | stale | move current focus from local Codex runtime integration to real-dataset ingest compatibility |
| `docs/plan.md` | salvageable | append the new real-dataset ingest slice after implementation |
| `src/yolo_label_validation/ingest.py` | salvageable | extend the YOLO pairing logic instead of creating a parallel ingest stack |
| `src/yolo_label_validation/cli.py` | salvageable | expose the new pairing mode through `normalize-yolo` |
| `src/yolo_label_validation/risk.py` | healthy for current scope | keep unchanged in this task, but record that zero-annotation images are still skipped downstream |

## Notes

- This task only covers getting the real dataset normalized into canonical run
  artifacts without renaming source files.
- A follow-up task is required to send zero-annotation images through the
  `risk -> vlm -> decision` chain for missing-object review.
