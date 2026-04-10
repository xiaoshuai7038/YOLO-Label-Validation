# EP-001 Bootstrap and Ingest

## Status

- Plan id: `EP-001`
- Milestone: `M2`
- State: completed
- Closure level: `slice`

## Outcome

- YOLO txt and COCO JSON normalize into one internal annotation contract
- every normalized annotation preserves raw-source lineage
- `run_manifest.json`, `image_index.json`, and `class_map.json` are emitted
  deterministically when manifest metadata is pinned

## Delivered Work

1. Added fixture-backed normalization coverage for YOLO txt and COCO JSON.
2. Implemented canonical normalized annotation records with raw-source lineage.
3. Added deterministic writers for `normalized_annotations.jsonl`,
   `image_index.json`, and `class_map.json`.
4. Extended the CLI with `normalize-yolo` and `normalize-coco`.
5. Extended `run_manifest.json` with normalization metadata, input sources, and
   record counts.

## Verification

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/m2-input-normalization
uv run python scripts/run_cli.py normalize-yolo --run-id smoke-yolo --output-dir artifacts/runs/smoke-yolo --images-dir artifacts/runs/_m2_cli_fixtures/yolo-images --labels-dir artifacts/runs/_m2_cli_fixtures/yolo-labels --class-names-file artifacts/runs/_m2_cli_fixtures/classes.txt --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite
uv run python scripts/run_cli.py normalize-coco --run-id smoke-coco --output-dir artifacts/runs/smoke-coco --annotation-file artifacts/runs/_m2_cli_fixtures/annotations.json --images-dir artifacts/runs/_m2_cli_fixtures/coco-images --dataset-version ds_m2 --class-map-version classes_m2 --prelabel-source prelabel_model_v1 --created-at 2026-04-10T00:00:00Z --overwrite
```

## Notes

- Source images and labels remain read-only.
- The next active milestone is M3 for rule validation, golden-set, and
  threshold work.
