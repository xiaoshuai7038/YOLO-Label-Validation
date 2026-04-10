# UAT Matrix - M2 Input Normalization

| UAT ID | Scenario | Flow | Acceptance Evidence | Status |
|---|---|---|---|---|
| `UAT-001` | A local operator can normalize a YOLO txt sample into the shared internal annotation contract | `FLOW-001` | `TC-001`, emitted `normalized_annotations.jsonl`, emitted `image_index.json` | pass |
| `UAT-002` | A local operator can normalize a COCO JSON sample into the same internal annotation contract | `FLOW-002` | `TC-002`, emitted `normalized_annotations.jsonl`, emitted `class_map.json` | pass |
| `UAT-003` | Conflicting or ambiguous class-map definitions are rejected before downstream artifacts are consumed | `FLOW-003` | `TC-003`, explicit exception text | pass |
| `UAT-004` | One normalized annotation can be traced back to its raw source line or raw source annotation id | `FLOW-001`, `FLOW-002` | `TC-001`, `TC-002`, lineage assertions in tests | pass |
| `UAT-005` | A normalization run writes a version-explicit `run_manifest.json` and deterministic artifact ordering when manifest metadata is pinned | `FLOW-004` | `TC-004`, `TC-005`, CLI smoke checks | pass |
