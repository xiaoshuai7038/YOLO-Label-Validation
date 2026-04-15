# Implement - Zero Annotation Image Review

## Execution Rules

- Do not hide image-level review behind fake annotation ids.
- Prefer explicit `review_scope` metadata to inference from nullable fields
  alone.
- Keep add-missing traceability compatible with the patch-first contract.
- Update the reusable failure taxonomy once the root cause is confirmed in code.

## Iteration Loop

1. Read `AGENTS.md`, `docs/project_spec.md`, `docs/prompt.md`, and
   `tasks/zero-annotation-image-review/contract.md`
2. Confirm the current skip behavior from real-dataset evidence
3. Implement the smallest artifact-contract extension that makes image-level
   review explicit
4. Update targeted tests first, then code, then rerun the tests
5. Record every real failure and fix in `documentation.md`
6. Re-run the full suite before closure

## Verification Commands

```powershell
uv run python scripts/check_task_docs.py tasks/zero-annotation-image-review
uv run pytest -q tests/test_risk.py tests/test_vlm.py tests/test_detector_refine.py tests/test_decision.py
uv run pytest -q
```

## Escalation

- Escalate if image-level review would require changing canonical normalized
  annotation artifacts instead of downstream review artifacts.
- Escalate if any patch path starts depending on source-label overwrite.
