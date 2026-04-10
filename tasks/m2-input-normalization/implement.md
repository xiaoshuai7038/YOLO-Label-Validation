# Implement - M2 Input Normalization

## Execution Rules

- Keep M2 changes contract-first: define the normalized records and artifact
  payloads before adding CLI affordances.
- Preserve raw input information in lineage fields instead of normalizing it
  away.
- Treat source images and source labels as read-only inputs. Only artifact files
  under the run output directory are writable truth.
- Keep the runtime dependency set minimal. Prefer standard-library parsing and
  deterministic serialization over adding new packages.
- Use `uv run ...` for local execution because the shell-level `python` command
  is not usable in this environment.

## Iteration Loop

1. Keep one primary change active at a time and link it to one `CHG-*` row.
2. Update the affected `TC-*` expectations before or alongside the code change.
3. Run the smallest relevant test first.
4. If a test fails, record a `FAIL-*` row in `documentation.md`, confirm the
   root cause, fix only that cause plus direct fallout, then retest.
5. After a meaningful pass, sync `docs/prompt.md` and `docs/documentation.md`
   before expanding scope.
6. Re-run `T-001` and `T-002` before claiming the M2 slice complete.

## Verification Commands

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/m2-input-normalization
uv run python scripts/run_cli.py show-layout
```

Focused CLI verification targets after implementation:

```powershell
uv run python scripts/run_cli.py normalize-yolo --run-id smoke-yolo --output-dir artifacts/runs/smoke-yolo --images-dir <images> --labels-dir <labels> --class-names-file <names.txt> --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite
uv run python scripts/run_cli.py normalize-coco --run-id smoke-coco --output-dir artifacts/runs/smoke-coco --annotation-file <annotations.json> --images-dir <images> --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite
```

## Escalation

- Escalate only if a required M2 behavior cannot be implemented without
  external services or a product decision that changes the normalized contract.
- If class-map semantics become ambiguous, fail fast and record the exact
  ambiguity instead of inferring a potentially unsafe mapping.
