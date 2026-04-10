# AGENTS.md

Navigation layer + guardrails for this harness-first repository.
Implementation details live in `docs/` and `src/`.

## 1) Project Goal

- Goal: replace full manual review of YOLO prelabels with a patch-first audit
  pipeline for fixed-class 2D detection datasets.
- Priority: traceability > source-data safety > correctness > stable automation
  > throughput > external integrations.
- Forbidden: direct overwrite of source labels, out-of-schema natural-language
  outputs, task-specific hardcoding, silent version mixing, scope creep beyond
  2D detection boxes in this phase.

## 2) Required Reading (in order)

1. `README.md`
2. `docs/srs_v1.md`
3. `docs/project_spec.md`
4. `docs/architecture.md`
5. `docs/prompt.md`
6. `docs/plan.md`
7. `docs/implement.md`
8. `docs/documentation.md`
9. `docs/failures/taxonomy.md`
10. `PLANS.md`
11. `tasks/repo-harness-bootstrap/contract.md`
12. `tasks/repo-harness-bootstrap/plan.md`

## 3) Code Map

- `src/yolo_label_validation/contracts.py` - canonical artifact registry and
  run-manifest contract
- `src/yolo_label_validation/bootstrap.py` - run workspace bootstrap logic
- `src/yolo_label_validation/cli.py` - scaffold CLI for layout inspection and
  run initialization
- `schemas/` - JSON schema contracts for the minimum interchange files
- `configs/` - default policy and threshold examples
- `tests/` - smoke tests; treat them as the minimum quality gate

## 4) Execution Entry Points

- Smoke tests: `pytest -q`
- Task-doc gate: `python scripts/check_task_docs.py tasks/repo-harness-bootstrap`
- Show scaffold layout: `python scripts/run_cli.py show-layout`
- Initialize a run workspace:
  `python scripts/run_cli.py init-run --run-id local-smoke --output-dir artifacts/runs/local-smoke`

## 5) Development Cycle (must follow)

1. Read `docs/prompt.md` before changing code.
2. Keep one primary change per iteration.
3. Prefer artifact-contract changes before tool integrations.
4. Run verification immediately after code changes.
5. Record evidence in `docs/documentation.md`.
6. No evidence = not done.

## 6) Hard Constraints

- Phase scope is only 2D detection boxes.
- Source images and source labels are read-only by policy.
- All downstream stages must consume normalized internal contracts.
- Every automatic action must carry `reason` or `reason_code`.
- Patches are the only writable truth for annotation edits.
- Model and threshold versions must be explicit in every run.

## 7) Quality Gates

Run before every commit:

```powershell
pytest -q
python scripts/check_task_docs.py tasks/repo-harness-bootstrap
```

## 8) Escalation Conditions

- Same failure pattern repeats twice without new evidence.
- A fix would require overwriting source labels.
- A change crosses more than 5 core source files.
- The output contract or schema becomes ambiguous.
- External service integration is required to prove a local change.

## 9) Feedback Loop

- Update `docs/failures/taxonomy.md` when a new failure pattern appears.
- Update `docs/documentation.md` after every meaningful iteration.
- Promote the milestone in `docs/plan.md` only after verification passes.
- Keep `PLANS.md` in sync with the active execution plan.
