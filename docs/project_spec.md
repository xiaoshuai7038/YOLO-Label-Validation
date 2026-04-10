# project_spec.md - YOLO Label Validation Harness Program Spec

Stable project-level spec for the patch-first audit system.
For current milestone scope, see `docs/prompt.md`.

## 1) North Star

- Goal: turn YOLO prelabel review into a machine-first pipeline that produces
  traceable patches and only escalates the hard cases to humans.
- Priority: traceability > source protection > correctness > stable automation
  > throughput > integration breadth.
- Forbidden: direct source overwrite, free-text contracts, silent version
  mixing, open-vocabulary scope creep, and heuristics that only pass a narrow
  sample set.

## 2) Execution & Artifacts

- Run:
  `pytest -q`
  `python scripts/check_task_docs.py tasks/repo-harness-bootstrap`
  `python scripts/run_cli.py show-layout`
  `python scripts/run_cli.py init-run --run-id local-smoke --output-dir artifacts/runs/local-smoke`
- Key artifacts:
  `normalized_annotations.jsonl`, `review_candidates.json`, `vlm_review.json`,
  `patches.json`, `run_summary.json`, `materialized_dataset/`

## 3) Success Metrics

| Metric | Code | Current Value | Measurement Method | Target |
|---|---|---|---|---|
| Manual review coverage | M1 | pending | reviewer_count / total_samples from `run_summary.json` | <= 20% |
| Explicit rule error recall | M2 | pending | golden-set recall on hard rule violations | 100% |
| Patch traceability rate | M3 | pending | reversible patch audit on emitted patches | 100% |
| Auto-pass sample correctness | M4 | pending | spot-check accuracy on auto-passed golden samples | >= 98% |

### Metric Honesty Contract

Every metric must be tagged with `metric_kind`:

- `measured`: directly observed from artifacts
- `proxy`: directional but not final
- `pending`: no evidence yet

A score without `metric_kind` is invalid.

### Metric Relationships

```text
Manual review coverage
|- depends on risk-ranking precision
|- depends on VLM decision quality
`- depends on detector-backed refine/add precision

Patch traceability rate
|- depends on normalized source mapping
`- depends on run-manifest version fidelity

Auto-pass sample correctness
|- depends on decision thresholds
|- depends on detector-backed confirmation
`- depends on conflict routing to manual review
```

## 4) Architecture Overview

| Layer/Phase | Purpose | Key Modules | Related Metrics | Typical Failures |
|---|---|---|---|---|
| Input normalization | unify YOLO and COCO into one contract | ingest, contracts, manifest | M2, M3 | source mapping lost, class-map drift |
| Rule and threshold pass | catch explicit annotation issues early | datumaro bridge, rules, stats | M2 | bad boxes not surfaced, thresholds unstable |
| Risk ranking | shrink the review set to the riskiest subset | cleanlab bridge, fiftyone bridge, rank fusion | M1, M4 | noisy candidate set, hidden dirty samples |
| Semantic review | produce structured keep/relabel/refine/delete decisions | vlm prompt builder, vlm parser | M1, M4 | invalid JSON, weak reasons, wrong class judgment |
| Geometry correction | accept or reject detector-backed box changes | detector_b bridge, refine, missing | M1, M4 | over-aggressive refinement, duplicate boxes |
| Decision, patching, fallback | finalize actions and human escalation | decision engine, patcher, CVAT bridge | M1, M3, M4 | untraceable actions, manual queue missing context |

Attribution principle: find the first layer that loses information, then decide
whether the fix belongs to parameters, module design, or interfaces.

## 5) Global Optimization Principles

1. Contracts come before integrations.
2. Patch-only writes are mandatory.
3. One primary lever per iteration.
4. Every automatic action needs reasoned evidence.
5. A risk score without explanation is insufficient.
6. If quality gates are red, only stabilization work is allowed.
7. Use golden-set evidence before changing thresholds.
8. Prefer side-by-side replacement over big-bang rewrites.
9. Repeated unexplained failure patterns trigger architecture review.
10. External tools may change, but artifact contracts must remain stable.

## 6) Verification Pyramid

1. Quality gates: `pytest -q` and `python scripts/check_task_docs.py tasks/repo-harness-bootstrap`
2. Focused: bootstrap or milestone-specific CLI checks
3. Adjacent: artifact schema conformance and cross-file consistency
4. Full: golden-set and end-to-end audit run validation

Only move up the pyramid when the lower level passes.

## 7) Architecture Escalation Rules

Three levels of change:

- `parameter-level`: thresholds, prompts, routing policy
- `module-design-level`: one module loses information repeatedly
- `cross-module-interface`: the sender has the right data but the receiver does
  not get it

Triggers for architecture review:

- Same metric + same failure pattern for 2 consecutive rounds
- Same information loss across 3-5 focused cases
- A fix spans more than 5 core source files
- The system cannot explain what evidence produced the final action
