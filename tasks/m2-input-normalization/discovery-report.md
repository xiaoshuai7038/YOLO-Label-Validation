# Discovery Report

## Task

- Task slug: `m2-input-normalization`

## Confirmed

- Repository mode: harness-first Python package with minimal runtime
  dependencies and a bootstrap CLI already in place.
- Current implemented modules under `src/yolo_label_validation/` cover
  artifact layout, run bootstrap, CLI dispatch, task-doc scaffolding, and the
  doc gate. No ingestion or normalization module exists yet.
- Current tests cover only bootstrap and task-doc tooling. There is no
  regression coverage yet for YOLO txt or COCO JSON ingestion.
- Current schemas only freeze `run_manifest`, `review_candidate`,
  `vlm_review`, and `patch`. M2 still needs schemas or contract coverage for
  `normalized_annotations`, `image_index`, and `class_map`.
- The shell environment exposes a non-working Windows Store `python.exe`
  shim. `uv run python ...` and `uv run pytest ...` are the reliable local
  execution path for this repository as of 2026-04-10.
- The active milestone in `docs/prompt.md` and `docs/plan.md` is M2:
  normalize YOLO txt and COCO JSON into one internal annotation contract,
  preserve raw-source lineage, and make run-manifest versions explicit.

## Existing Documentation Health

| File | Status | Issue | Action |
|---|---|---|---|
| `README.md` | healthy | repository goal and current status match the codebase | keep |
| `docs/srs_v1.md` | healthy | defines canonical artifact list and M2 scope clearly | keep |
| `docs/project_spec.md` | healthy | stable priorities and metrics still align with M2 | keep |
| `docs/architecture.md` | healthy | planned `ingest.py` boundary matches the missing work | keep |
| `docs/prompt.md` | salvageable | milestone is correct, but touched interfaces and tests are still generic | refresh after implementation |
| `docs/plan.md` | healthy | milestone board already tracks M2 as active | keep |
| `docs/implement.md` | salvageable | verification examples still emphasize bootstrap commands | keep and supplement in task docs |
| `docs/documentation.md` | healthy | latest entry explicitly points to FR-001/FR-002 as next step | append evidence after validation |
| `docs/failures/taxonomy.md` | healthy | already includes normalization traceability loss as a category | keep and extend only if a new failure pattern appears |
| `PLANS.md` | healthy | active execution plan already points at FR-001/FR-002 | keep |
| `docs/exec-plans/active/EP-001-bootstrap-and-ingest.md` | healthy | work items match the missing M2 implementation | keep |
| `tasks/repo-harness-bootstrap/*` | healthy | foundation task is complete and should remain separate from M2 delivery docs | keep as prior milestone record |
| `tasks/m2-input-normalization/*` | stale | freshly scaffolded from the bootstrap template and not task-specific yet | rewrite in this task |

## Notes

- M2 will treat the normalized annotation contract as the only downstream input
  format. Raw YOLO and COCO payloads remain read-only lineage evidence.
- The working assumption for internal geometry is absolute `bbox_xyxy` plus a
  deterministic normalized `bbox_cxcywh` view so downstream rule, review, and
  patch modules can consume one shape.
