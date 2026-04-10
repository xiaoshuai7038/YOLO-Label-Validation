# prompt.md - Current Milestone Contract

This file describes only the current milestone.
For the full roadmap, see `docs/plan.md`. For stable spec, see
`docs/project_spec.md`.

## Current Milestone: M2 - Build FR-001/FR-002 input normalization and run manifests

## Scope

Implement the first real audit capability after repository bootstrap:
read YOLO txt or COCO JSON, normalize them into one internal annotation
contract, and preserve enough lineage to trace every normalized annotation back
to the raw source.

## In-Scope

- parser and writer contracts for YOLO txt and COCO JSON
- versioned `run_manifest.json`, `image_index.json`, and `class_map.json`
- per-annotation lineage fields required for later patch traceability

## Non-Goals

- Cleanlab, FiftyOne, Qwen2.5-VL, or CVAT integration
- detector-backed box refinement or missing-box recovery

## Hard Constraints

- downstream code must not consume raw source formats directly
- source images and source labels remain read-only
- normalization output must be deterministic for the same inputs and versions

## Verification Commands

```powershell
pytest -q
```

## Required Evidence

- fixture-based normalization output for both YOLO txt and COCO JSON
- a traceability proof from one normalized annotation back to its raw source

## Done When

- [ ] both source formats can be normalized into the same annotation contract
- [ ] `run_manifest.json` captures dataset and model versions explicitly
- [ ] all verification commands pass
- [ ] `docs/documentation.md` updated with results
