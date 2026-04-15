# Needs Manifest

## Task

- Task slug: `zero-annotation-image-review`

## Blocking Needs

- None. The dataset evidence and current incorrect behavior are already
  reproducible locally.

## Non-Blocking Needs

- Tuning guidance for how aggressively to sample annotated images once all
  zero-annotation images are guaranteed to enter review.
- Later business guidance on whether every zero-annotation image should always
  be VLM-reviewed or whether a cheaper first-pass model can prefilter them.

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| business KPI for acceptable empty-image false-negative rate | needed for threshold tuning, not for structural closure | later policy milestone |
| detector-first shortcut for image-level empty cases | optimization only after correctness is restored | later performance milestone |
