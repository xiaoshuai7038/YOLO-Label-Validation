# Contract - Materialized YOLO Export

## Goal

Export a materialized run into a directly usable YOLO-format dataset directory
with images, labels, and class metadata.

## Scope

- add a formal CLI path to export a run's materialized annotations into YOLO
  `images/` and `labels/` directories
- emit `classes.txt`, `dataset.yaml`, and an export manifest for traceability
- copy source images into the derived export without mutating the source data
- run the export on `artifacts/runs/real-full-flow/`

## Done When

- `DW-001` the repository exposes a CLI command for YOLO export
- `DW-002` exported labels use image filenames as YOLO label stems and preserve
  zero-annotation images through empty label files
- `DW-003` tests cover label export, image copy, and CLI behavior
- `DW-004` the real run is exported into a derived YOLO directory

## Changes

- `CHG-001` implement YOLO export helpers in `src/yolo_label_validation/materialize.py`
- `CHG-002` add a CLI entrypoint in `src/yolo_label_validation/cli.py`
- `CHG-003` add regression tests in `tests/test_materialize.py`
- `CHG-004` record task evidence and run a real export on `real-full-flow`
