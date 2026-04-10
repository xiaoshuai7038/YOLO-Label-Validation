# plan.md - Milestone Board

Current milestone marked with `->`.

## Milestone Overview

| ID | Title | Status | Depends On |
|---|---|---|---|
| M1 | Bootstrap harness docs, schemas, and run scaffold | completed | none |
| M2 | Build FR-001/FR-002 input normalization and run manifests | -> in progress | M1 |
| M3 | Build FR-003/FR-004/FR-005 golden set, rules, and thresholds | pending | M2 |
| M4 | Build FR-006/FR-007/FR-008/FR-009 risk, VLM review, and decision engine | pending | M3 |
| M5 | Build FR-010/FR-011/FR-012/FR-013/FR-015/FR-016 detector refine, CVAT, materialization, and ops | pending | M4 |

---

## M1: Bootstrap harness docs, schemas, and run scaffold

**Goal**: convert the empty repository into a harness-first codebase with
stable contracts, task execution docs, and a runnable bootstrap CLI.

**Scope**: top-level docs, task docs, schemas, bootstrap code, doc gate, smoke tests

**Deliverables**:
- [x] `AGENTS.md`, `PLANS.md`, and `docs/` control plane created
- [x] bootstrap CLI creates canonical run artifact files
- [x] `tasks/` doc layer, task-doc gate, and CI quality gate created

**Verification**:

```powershell
pytest -q
```

**Done When**:
- repository has a stable artifact contract and execution-plan structure
- bootstrap run initialization works through tests
- all verification commands pass

---

## -> M2: Build FR-001/FR-002 input normalization and run manifests

**Goal**: ingest YOLO txt and COCO JSON into one internal contract with
source-to-normalized traceability and versioned run manifests.

**Scope**: ingest parser, normalized JSONL writer, image index, class map,
source lineage, run-manifest fidelity

**Deliverables**:
- [ ] parse YOLO txt and COCO JSON into one `normalized_annotations.jsonl`
- [ ] emit `image_index.json`, `class_map.json`, and lineage fields for each ann
- [ ] reject ambiguous or inconsistent class-map definitions

**Verification**:

```powershell
pytest -q
```

**Done When**:
- sample fixtures can be normalized from both source formats
- every normalized annotation can be traced back to its raw source record
- all verification commands pass

---

## M3: Build FR-003/FR-004/FR-005 golden set, rules, and thresholds

**Goal**: establish explicit rule validation and thresholded statistics before
any model-assisted review.

**Scope**: golden-set manifest, rule checks, class stats, thresholds

**Deliverables**:
- [ ] implement explicit invalid-box and invalid-class checks
- [ ] emit class-level stats and threshold snapshots
- [ ] attach issue type, severity, and auto-action hints to every rule issue

**Verification**:

```powershell
pytest -q
```

**Done When**:
- explicit rule violations are surfaced with reasons
- threshold loads are versioned and deterministic
- all verification commands pass

---

## M4: Build FR-006/FR-007/FR-008/FR-009 risk, VLM review, and decision engine

**Goal**: rank risky annotations, review them with a structured VLM protocol,
and produce deterministic actions.

**Scope**: risk fusion, VLM request/response pipeline, decision engine, patches

**Deliverables**:
- [ ] emit candidate rankings with configurable fusion policy
- [ ] parse only schema-valid VLM JSON responses
- [ ] output deterministic `decision_results.json` and `patches.json`

**Verification**:

```powershell
pytest -q
```

**Done When**:
- candidate reasons and VLM decisions are machine-readable
- automatic actions always contain evidence and reason codes
- all verification commands pass

---

## M5: Build FR-010/FR-011/FR-012/FR-013/FR-015/FR-016 detector refine, CVAT, materialization, and ops

**Goal**: close the loop with detector-backed geometry changes, manual review,
materialized exports, and audit summaries.

**Scope**: refine/add flows, manual queue, CVAT bridge, materialization, run
summary, metrics

**Deliverables**:
- [ ] accept or reject detector-backed refine/add proposals with reasons
- [ ] emit manual review tasks with full evidence context
- [ ] materialize patch-applied dataset versions and run-level summaries

**Verification**:

```powershell
pytest -q
```

**Done When**:
- all automatic and manual outcomes are traceable through patches
- the system can export a new dataset view without mutating source labels
- all verification commands pass

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
