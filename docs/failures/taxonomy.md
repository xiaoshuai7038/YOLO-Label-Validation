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

## How to Add a New Category

1. Identify which metric dropped.
2. Trace where the information was lost.
3. Add a new category with concrete symptoms.
4. Record the discovery in `docs/documentation.md`.
