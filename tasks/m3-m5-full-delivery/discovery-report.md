# Discovery Report

## Task

- Task slug: `m3-m5-full-delivery`

## Confirmed

- The repository now implements M1 bootstrap and M2 input normalization.
- Existing production modules: `contracts.py`, `bootstrap.py`, `cli.py`,
  `task_docs.py`, `doc_check.py`, and `ingest.py`.
- Missing product modules for the remaining roadmap: `rules.py`, `risk.py`,
  `vlm.py`, `decision.py`, `detector_refine.py`, and `materialize.py`.
- Existing config seeds: `configs/defaults.json` and
  `configs/thresholds.example.yaml`.
- Existing schemas cover `run_manifest`, `normalized_annotation`,
  `image_index`, `class_map`, `review_candidate`, `vlm_review`, and `patch`.
  Remaining artifact schemas still need to be added for M3-M5 outputs.
- Reliable local commands in this environment:
  `uv run pytest -q`,
  `uv run python scripts/check_task_docs.py <task-dir>`,
  `uv run python scripts/run_cli.py <subcommand>`.
- The shell-level `python` shim is not reliable and should not be used for
  verification.

## Existing Documentation Health

| File | Status | Issue | Action |
|---|---|---|---|
| `README.md` | healthy | high-level flow still matches the desired full pipeline | keep |
| `docs/srs_v1.md` | healthy | remains the source-of-truth artifact list and constraints | keep |
| `docs/project_spec.md` | healthy | priorities and metrics still align with remaining work | keep |
| `docs/architecture.md` | salvageable | module map is accurate, but still describes only planned modules | refresh after module delivery |
| `docs/plan.md` | healthy | M3 is active and M4/M5 remain pending | keep and promote as milestones close |
| `docs/prompt.md` | healthy | currently scoped to M3 and should move milestone-by-milestone | refresh after each promotion |
| `docs/documentation.md` | healthy | contains M2 evidence and should continue receiving milestone evidence | append |
| `docs/failures/taxonomy.md` | salvageable | covers traceability loss but not remaining M3-M5 failure classes | extend when new repeated patterns appear |
| `PLANS.md` | healthy | active execution plan already points to M3 | keep and update as plans move |
| `docs/exec-plans/*` | healthy | M2 is archived, M3 is active | keep and promote |
| `tasks/m2-input-normalization/*` | healthy | complete milestone evidence for M2 | keep as historical slice |
| `tasks/m3-m5-full-delivery/*` | stale | just scaffolded from templates and not task-specific yet | rewrite in this task |

## Notes

- Remaining delivery spans multiple business domains and should keep
  `REQ-*`, `FLOW-*`, and `UAT-*` artifacts in sync with tests.
- Live execution against external services is not required to complete the
  local codebase, but the repository must expose contract-stable seams for
  those integrations.
