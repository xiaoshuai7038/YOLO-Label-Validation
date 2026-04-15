# Discovery Report - Materialized YOLO Export

## Confirmed

- the repository currently materializes only the internal normalized contract
  view under `materialized_dataset/`
- the user needs a real YOLO-format derived dataset, not only
  `normalized_annotations.jsonl`
- the completed real run is
  `artifacts/runs/real-full-flow/`
- source images must remain read-only

## Existing Documentation Health

- `docs/architecture.md` and `README.md` describe materialization at a high
  level but do not currently expose a YOLO export command
- `tests/test_materialize.py` covers internal materialization only
- the new work can stay bounded to materialization/export and does not need to
  reopen the review or decision milestones
