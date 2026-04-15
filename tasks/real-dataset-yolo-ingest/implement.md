# Implement - Real Dataset YOLO Ingest Adapter

## Execution Rules

- Keep the change centered on ingest compatibility; do not mix in the later
  zero-annotation review redesign.
- Preserve canonical artifact shapes and existing exact-stem YOLO behavior.
- Keep source dataset files read-only; solve compatibility in code, not by
  renaming input files.
- Prefer one new pairing abstraction that both image and label resolution share.

## Iteration Loop

1. Read `AGENTS.md`, `docs/project_spec.md`, and `docs/prompt.md`
2. Reproduce the real failure with the current `normalize-yolo` command
3. Add the smallest pairing-mode abstraction that fixes the reproduced failure
4. Validate unit/CLI fixtures before running the real-dataset smoke
5. Record each meaningful result in `tasks/real-dataset-yolo-ingest/documentation.md`
6. Re-run the task-doc gate and targeted pytest suite before closure

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest
uv run pytest -q tests/test_ingest.py
uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite
```

## Escalation

- Escalate if the pairing rule needs dataset-specific hardcoding beyond the
  explicit `pairing_mode` enum.
- Escalate if fixing the real dataset requires changing canonical artifact
  schemas.
- Record but do not solve zero-annotation image review gaps in this task.
