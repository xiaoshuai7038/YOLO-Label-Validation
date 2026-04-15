# Discovery Report

## Task

- Task slug: `zero-annotation-image-review`
- Driving dataset: `E:\workspace\cigarette-identify\预标注测试\20264010`

## Confirmed

- The real dataset normalizes successfully after the ingest pairing-mode fix.
- The normalized run contains `520` images, of which `245` have
  `annotation_count = 0`.
- Those `245` images are not true negatives by contract; visual inspection
  already found carton stacks in sample image
  `021dfc759ed044bfa907748f1eb12c78_1050_1.jpeg`.
- Current downstream behavior is incorrect:
  - `run-risk` produces `1088` risk rows, exactly one per existing annotation
  - `review_candidates.json` contains `0` zero-annotation images
  - `run-vlm` therefore emits no review request for zero-annotation images
- Root cause is architectural, not just a missing branch:
  - `risk.py` defines the review universe from `normalized_annotations`
  - `review_candidate.schema.json` only models `candidate_annotations`
  - `vlm_request.schema.json` and `vlm_review.schema.json` require a concrete
    `ann_id` and annotation context
  - `decision.py` keys review evidence by `ann_id`, which cannot represent
    image-level review without fake annotation ids

## Existing Documentation Health

| File | Status | Action |
|---|---|---|
| `docs/failures/taxonomy.md` | salvageable | add a new failure category for review-universe contraction |
| `docs/prompt.md` | stale | move the active milestone to zero-annotation image review closure |
| `docs/plan.md` | salvageable | append a new milestone for image-level missing review |
| `src/yolo_label_validation/risk.py` | stale for real data | redefine review-universe logic from `image_index`, not just annotations |
| `src/yolo_label_validation/vlm.py` | salvageable | add explicit review-scope metadata instead of faking annotation ids |
| `src/yolo_label_validation/decision.py` | salvageable | merge image-level review and missing proposals without ann-id collisions |
| `src/yolo_label_validation/detector_refine.py` | salvageable | support missing proposals whose source review is image-level |

## Notes

- This task must not solve image-level review by inventing fake annotations.
- The harness fix should make review scope explicit in artifacts so the same
  mistake is harder to reintroduce later.
