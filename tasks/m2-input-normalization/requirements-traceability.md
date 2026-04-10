# Requirements Traceability - M2 Input Normalization

| Req ID | Requirement | Design / Interface / Data | Flow / UAT / TC / T | Status |
|---|---|---|---|---|
| `REQ-001` | Normalize YOLO txt annotations into the canonical internal contract | `ingest.py` / `normalize_yolo_source()` / `normalized_annotations.jsonl` | `FLOW-001`, `UAT-001`, `TC-001`, `T-001` | validated |
| `REQ-002` | Normalize COCO JSON annotations into the same canonical internal contract | `ingest.py` / `normalize_coco_source()` / `normalized_annotations.jsonl` | `FLOW-002`, `UAT-002`, `TC-002`, `T-001` | validated |
| `REQ-003` | Emit versioned `image_index.json`, `class_map.json`, and `run_manifest.json` for each normalization run | `contracts.py`, `ingest.py`, `cli.py` / artifact writers | `FLOW-004`, `UAT-005`, `TC-004`, `TC-005`, `T-001`, `T-003`, `T-004` | validated |
| `REQ-004` | Preserve enough lineage to trace each normalized annotation back to its raw source file, row, or object id | `ingest.py` / lineage payload on each normalized annotation | `FLOW-001`, `FLOW-002`, `UAT-004`, `TC-001`, `TC-002`, `T-001` | validated |
| `REQ-005` | Reject ambiguous or inconsistent class-map definitions before downstream artifacts are consumed | `ingest.py` / `merge_class_maps()` / `class_map.json` | `FLOW-003`, `UAT-003`, `TC-003`, `T-001` | validated |
| `REQ-006` | Keep source images and labels read-only and make output ordering deterministic for identical inputs and pinned versions | `ingest.py`, `cli.py`, `contracts.py` / deterministic sorting and explicit manifest metadata | `FLOW-004`, `UAT-005`, `TC-004`, `TC-005`, `T-001`, `T-003`, `T-004` | validated |
