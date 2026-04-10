# EP-001 Bootstrap and Ingest

## Status

- Plan id: `EP-001`
- Milestone: `M2`
- State: active

## Context

The repository bootstrap is complete: docs, schemas, config examples, and a
run-scaffold CLI now exist. The next deliverable is the first real data path:
FR-001 and FR-002 input normalization plus version-fidelity.

## Expected Outcome

- YOLO txt and COCO JSON are normalized into one contract
- every normalized annotation preserves raw-source lineage
- `run_manifest.json` is reliable enough to gate later patches and training

## Work Items

1. Define fixture datasets for YOLO txt and COCO JSON ingestion.
2. Implement normalized annotation records with raw-source lineage.
3. Add deterministic writers for `normalized_annotations.jsonl`,
   `image_index.json`, and `class_map.json`.
4. Extend tests to prove traceability and deterministic output.

## Verification

```powershell
pytest -q
python scripts/run_cli.py show-layout
```

## Notes

- Do not integrate external model services in this plan.
- Do not mutate source labels.
- Keep artifact naming consistent with `contracts.py` and `schemas/`.
