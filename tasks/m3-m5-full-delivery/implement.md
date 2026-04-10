# Implement - M3-M5 Full Delivery

## Execution Rules

- Keep each milestone contract-first and schema-first before adding CLI
  plumbing.
- Prefer local deterministic algorithms and fixtures when an external service
  would otherwise block validation.
- Keep source labels and images read-only. Patch and materialized outputs are
  the only writable truth.
- Use `uv run ...` for all verification in this environment.
- Update task evidence after every meaningful implementation or failure loop.

## Iteration Loop

1. Read `docs/prompt.md`, `PLAN.md`, and `STATUS.md`.
2. Read `tasks/m3-m5-full-delivery/contract.md` and this runbook.
3. Implement one `CHG-*` slice at a time.
4. Run the smallest relevant test first.
5. If validation fails, record a `FAIL-*` row in task documentation, confirm
   root cause, fix it, and retest in targeted -> milestone -> regression order.
6. Update docs before moving to the next milestone.
7. Re-run `T-001` and `T-002` before any milestone promotion.

## Verification Commands

```powershell
uv run pytest -q
uv run python scripts/check_task_docs.py tasks/m3-m5-full-delivery
uv run python scripts/run_cli.py show-layout
```

Focused smoke commands will be added or updated as subcommands land.

## Escalation

- Escalate only if a required remaining behavior truly needs a live external
  runtime or an ambiguous product decision.
- If a contract becomes ambiguous, fail fast and record the ambiguity rather
  than guessing.
