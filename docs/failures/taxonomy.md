# Failure Taxonomy

Classify failures by where information is lost and which metric they hurt.

## Classification Axes

1. Which metric is impacted? See `docs/project_spec.md`.
2. Which phase loses information first?
3. Is the fix parameter-level, module-level, or cross-module?

## Failure Categories

### Category 1: normalization_traceability_loss

- **Impacted metric**: patch traceability rate
- **Layer**: input normalization
- **Symptoms**: a normalized annotation cannot be mapped back to its raw source
  file, row, or object id
- **Example instances**: add examples as they are discovered
- **Fix level**: module or cross-module

### Category 2: unsafe_source_mutation_risk

- **Impacted metric**: patch traceability rate and source protection
- **Layer**: decision and patching
- **Symptoms**: code paths attempt to rewrite raw labels instead of emitting
  patches or a materialized dataset version
- **Example instances**: add examples as they are discovered
- **Fix level**: module or cross-module

### Category 3: rule_signal_underreporting

- **Impacted metric**: explicit rule error recall
- **Layer**: rule and threshold pass
- **Symptoms**: the rule engine stops after the first issue on an annotation and
  fails to emit additional independent rule issues that should also surface
- **Example instances**: `FAIL-001` in `tasks/m3-m5-full-delivery/documentation.md`
- **Fix level**: module

### Category 4: upstream_artifact_clobber

- **Impacted metric**: patch traceability rate and deterministic automation
- **Layer**: cross-module artifact lifecycle
- **Symptoms**: a downstream stage recreates the run workspace with overwrite
  semantics and silently clears populated upstream artifacts such as normalized
  annotations or image indexes
- **Example instances**: `FAIL-002` in
  `tasks/m3-m5-full-delivery/documentation.md`
- **Fix level**: cross-module

### Category 5: review_universe_contraction

- **Impacted metric**: missing-object recall and manual-review coverage
- **Layer**: risk, review-candidate, and VLM request assembly
- **Symptoms**: the review universe is derived from existing annotations rather
  than the full image index, so zero-annotation images or other image-level
  cases are silently excluded from downstream semantic review
- **Example instances**: `DOC-002` in
  `tasks/zero-annotation-image-review/documentation.md`
- **Fix level**: cross-module

## How to Add a New Category

1. Identify which metric dropped.
2. Trace where the information was lost.
3. Add a new category with concrete symptoms.
4. Record the discovery in `docs/documentation.md`.
