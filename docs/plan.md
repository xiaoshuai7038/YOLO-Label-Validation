# plan.md - Milestone Board

Current milestone marked with `->` when one is active.

## Milestone Overview

| ID | Title | Status | Depends On |
|---|---|---|---|
| M1 | Bootstrap harness docs, schemas, and run scaffold | completed | none |
| M2 | Build FR-001/FR-002 input normalization and run manifests | completed | M1 |
| M3 | Build FR-003/FR-004/FR-005 golden set, rules, and thresholds | completed | M2 |
| M4 | Build FR-006/FR-007/FR-008/FR-009 risk, VLM review, and decision engine | completed | M3 |
| M5 | Build FR-010/FR-011/FR-012/FR-013/FR-015/FR-016 detector refine, CVAT, materialization, and ops | completed | M4 |
| M6 | Build production VLM and detector integrations plus runtime config | completed | M5 |
| M7 | Add local Codex review runtime support while preserving `vlm_*` contracts | completed | M6 |
| M8 | Add real-dataset YOLO ingest compatibility for mixed-directory `__hash` pairs | completed | M7 |
| M9 | Close the zero-annotation image review gap in the semantic-review pipeline | completed | M8 |
| M10 | Tune cost and policy for the expanded zero-annotation review workload | pending | M9 |

---

## Completed Through M7

M1 through M7 are implemented. The repository now reaches `slice` closure for
the current review-runtime target: the semantic-review stage supports a local
Codex CLI backend, the prior HTTP provider paths still work, and the frozen
downstream artifacts did not change.

---

## M8 Completed: Add real-dataset YOLO ingest compatibility for mixed-directory `__hash` pairs

**Goal**: normalize the real YOLO dataset at
`E:\workspace\cigarette-identify\预标注测试\20264010` without renaming source
files, even though images and labels live in one directory and paired stems may
differ only by a trailing `__hash` suffix.

**Scope**: explicit YOLO pairing-mode support, CLI exposure, fixture coverage,
real-dataset smoke validation, and synchronized task evidence

**Deliverables**:
- [x] `normalize-yolo` exposes a pairing mode for non-exact filename pairing
- [x] YOLO ingest supports `stem_before_double_underscore` matching while
  keeping exact-stem behavior unchanged
- [x] mixed-directory fixture coverage proves labeled and unlabeled image
  behavior
- [x] the real dataset normalizes successfully into canonical artifacts
- [x] docs record that zero-annotation images still need a later review-flow
  redesign

**Verification**:

```powershell
uv run python scripts/check_task_docs.py tasks/real-dataset-yolo-ingest
uv run pytest -q tests/test_ingest.py
uv run pytest -q
uv run python scripts/run_cli.py normalize-yolo --run-id real-smoke --output-dir artifacts/runs/real-smoke --images-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --labels-dir "E:\workspace\cigarette-identify\预标注测试\20264010" --class-name cigarette --pairing-mode stem_before_double_underscore --dataset-version ds_real_smoke --class-map-version classes_real_smoke --prelabel-source prelabel_model_v1 --created-at 2026-04-13T00:00:00Z --overwrite
uv run python scripts/run_cli.py run-rules --run-dir artifacts/runs/real-smoke --overwrite
uv run python scripts/run_cli.py run-risk --run-dir artifacts/runs/real-smoke --defaults-file configs/defaults.json --overwrite
```

**Result**:
- real dataset normalization succeeds with `520` images, `1088` annotations,
  and `1` class
- `245` zero-annotation images remain represented in the normalized run
- downstream review candidates still exclude those zero-annotation images, so a
  follow-up image-level review slice remains open

---

## M7 Completed: Add local Codex review runtime support while preserving `vlm_*` contracts

**Goal**: replace the old API-oriented review runtime with a direct local
Codex CLI integration while keeping `vlm_requests.jsonl`,
`vlm_raw_responses.jsonl`, `vlm_review.json`, and `run-vlm` stable for
downstream stages.

**Scope**: local `codex exec` transport, provider-aware runtime config,
backward-compatible HTTP provider support, default-model alignment, docs, and
tests

**Deliverables**:
- [x] runtime config can describe a local `codex_cli` review provider as well
  as the legacy HTTP providers
- [x] `run-vlm` can execute mocked `codex exec` requests with local image input
  and parse them into `vlm_review.json`
- [x] fixture mode and legacy HTTP transport paths remain regression-covered
- [x] repository defaults and docs align on the new local Codex review
  direction

**Verification**:

```powershell
uv run pytest -q tests/test_runtime_config.py tests/test_vlm.py
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/codex-review-integration
```

**Result**:
- local Codex review support is implemented and test-covered
- the previous HTTP provider paths remain compatible
- the default review runtime and committed config now point at local Codex CLI
- remaining gap is limited to a true local live smoke with the operator's
  Codex login/profile state

---

## M9 Completed: Close the zero-annotation image review gap in the semantic-review pipeline

**Goal**: stop silently skipping zero-annotation images by making image-level
review explicit across risk selection, VLM request assembly, detector refine,
and decision routing.

**Scope**: image-level risk candidates, explicit review scope metadata, missing
proposal routing without fake annotation ids, tests, and reusable failure-taxonomy
documentation

**Deliverables**:
- [x] zero-annotation images appear in `review_candidates.json`
- [x] VLM request/review artifacts distinguish image-level and annotation-level
  review
- [x] image-level missing proposals survive into `missing_results.json` and
  downstream decisions
- [x] failure taxonomy records the root cause and guardrail

**Verification**:

```powershell
uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review
uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py
uv run pytest -q
```

**Result**:
- real dataset `run-risk` now emits `1333` risk rows, including `245`
  image-level rows for zero-annotation images
- `review_candidates.json` now contains `245` image-level candidates and
  misses `0` of the `245` zero-annotation images in `image_index.json`
- a real single-image Codex CLI smoke now produces
  `vlm_review.json -> missing_results.json -> decision_results.json -> patches.json`
  with explicit `review_scope: image` and no fake `ann_id`
- local Codex integration is hardened for Windows command resolution and a more
  realistic live-review timeout baseline

---

## Next

After M9, the next repository slice should focus on cost and policy tuning for
the newly included zero-annotation image-review workload.

---

## Promotion Rules

A milestone is done when:

1. All deliverables are checked off
2. All verification commands pass
3. No quality gate regressions exist
4. Results are recorded in `docs/documentation.md`

After promotion:

1. Move `->` to the next milestone
2. Update `docs/prompt.md`
3. Move or refresh the active execution plan in `docs/exec-plans/`
