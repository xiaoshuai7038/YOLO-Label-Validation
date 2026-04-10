# Needs Manifest

## Task

- Task slug: `m2-input-normalization`

## Blocking Needs

- None. The M2 scope can be implemented and validated locally with synthetic
  fixtures and the existing repository constraints.

## Non-Blocking Needs

- Real dataset samples to broaden fixture coverage beyond one synthetic YOLO
  sample and one synthetic COCO sample.
- A future decision on whether export-time class ids must preserve original
  source ordering or may rely on the canonical internal class-map snapshot.
  Current M2 assumption: internal canonical ids are deterministic and source
  ids are preserved in lineage and `class_map.json`.
- A future decision on whether downstream materialization should enforce image
  checksum tracking in `image_index.json`. Current M2 assumption: image path
  and dimensions are sufficient lineage for this slice.

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| Golden-set manifests and coverage rules | not needed until explicit rule validation and metric tracking | M3 |
| Threshold config loaders and rule policy snapshots | not needed until FR-003/FR-005 | M3 |
| Cleanlab and FiftyOne runtime wiring | not needed until risk ranking | M4 |
| Qwen2.5-VL request execution and parser hardening | not needed until structured semantic review | M4 |
| Detector B checkpoints and refine/add policies | not needed until detector-backed geometry changes | M5 |
| CVAT connectivity and export/import mapping | not needed until manual review round-trip | M5 |
