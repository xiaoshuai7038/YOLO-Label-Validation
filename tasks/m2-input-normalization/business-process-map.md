# Business Process Map - M2 Input Normalization

## FLOW-001 Normalize a YOLO txt dataset

- Domain: input normalization
- Actor: engineer or agent running a local audit-prep step
- Entry: execute the M2 normalization path with a YOLO images directory, labels
  directory, and class-name definition
- Preconditions:
  1. images exist and have readable dimensions
  2. one label file maps to at most one image stem
  3. class-name definitions are unique and ordered
- Main path:
  1. resolve image metadata and class names
  2. parse each label line into a raw annotation
  3. convert normalized YOLO geometry into canonical internal geometry
  4. attach lineage back to label file path and line number
  5. stage image-index and class-map entries for artifact writing
- Exception paths:
  1. malformed label rows fail fast
  2. duplicate class names fail fast
  3. missing or ambiguous image matches fail fast
- Satisfies: `REQ-001`, `REQ-004`, `REQ-006`
- Evidence: `UAT-001`, `UAT-004`, `TC-001`

## FLOW-002 Normalize a COCO JSON dataset

- Domain: input normalization
- Actor: engineer or agent running a local audit-prep step
- Entry: execute the M2 normalization path with a COCO annotations file and an
  optional image root
- Preconditions:
  1. the COCO JSON contains `images`, `annotations`, and `categories`
  2. category ids and names are unique
- Main path:
  1. index categories and images from the COCO file
  2. convert each COCO bbox into canonical internal geometry
  3. attach lineage back to raw annotation id, raw image id, and source file
  4. stage image-index and class-map entries for artifact writing
- Exception paths:
  1. missing image references fail fast
  2. duplicate category ids or names fail fast
  3. annotations referencing unknown images or categories fail fast
- Satisfies: `REQ-002`, `REQ-004`, `REQ-006`
- Evidence: `UAT-002`, `UAT-004`, `TC-002`

## FLOW-003 Merge class maps and reject conflicts

- Domain: class-map management
- Actor: normalization pipeline
- Entry: one or more normalized sources need one canonical class-map snapshot
- Main path:
  1. collect unique class definitions from each source
  2. resolve canonical internal class ids deterministically
  3. preserve source-specific ids and names as lineage mappings
  4. reject ambiguous duplicates or incompatible definitions
- Exception paths:
  1. duplicate normalized names within a source fail fast
  2. incompatible names for the same normalized key fail fast
- Satisfies: `REQ-003`, `REQ-005`
- Evidence: `UAT-003`, `TC-003`, `TC-004`

## FLOW-004 Materialize the M2 artifact set for downstream stages

- Domain: run workspace output
- Actor: normalization pipeline
- Entry: normalized records and class-map snapshot are ready
- Main path:
  1. initialize or reuse the canonical run workspace
  2. write `normalized_annotations.jsonl` in deterministic order
  3. write `image_index.json` and `class_map.json`
  4. write `run_manifest.json` with explicit source-format and version fields
- Exception paths:
  1. existing outputs without `--overwrite` fail fast
  2. manifest fields missing required versions fail fast
- Satisfies: `REQ-003`, `REQ-006`
- Evidence: `UAT-005`, `TC-004`, `TC-005`
