# Needs Manifest

## Task

- Task slug: `real-dataset-yolo-ingest`

## Blocking Needs

- None. The real dataset path, class-id shape, and current failure mode are all
  reproducible locally.

## Non-Blocking Needs

- Preferred human-facing class display name for class id `0`. The task can
  proceed with a caller-supplied `--class-name cigarette`.
- Confirmation of whether the `245` zero-label images should later be reviewed
  as possible missing-object cases instead of true negatives. The current task
  records this gap but does not block ingest compatibility.

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| image-level review contract for zero-annotation images | current `risk/vlm/decision` flow is annotation-driven and needs a separate design slice | follow-up review-slice task |
| detector-assisted confirmation for empty-prelabel images | not required to normalize the dataset safely | follow-up review-slice task |
| dataset-specific defaults for candidate sampling on empty-prelabel images | depends on the image-level review contract | follow-up review-slice task |
