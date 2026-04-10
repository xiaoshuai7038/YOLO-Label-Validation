# implement.md - Execution Runbook

How to execute one iteration inside the current milestone.
For the milestone definition, see `docs/prompt.md`.
For the full roadmap, see `docs/plan.md`.

## Iteration Cycle

### Step 1: Read context

Before writing code, read:

1. `docs/prompt.md`
2. `docs/plan.md`
3. `docs/documentation.md`
4. `docs/failures/taxonomy.md`

### Step 2: State the change

Write one sentence:

> I am changing [X] to achieve [Y] because [Z].

Rules:

- name exactly one primary change
- tie it to one milestone deliverable
- make it falsifiable by the verification command

### Step 3: Implement

- keep the change inside 1 module when possible, max 3 files
- update schemas and docs when a contract changes
- do not add external-service integration unless the milestone explicitly
  requires it

### Step 4: Verify

```powershell
# 4a. Quality gates
pytest -q
python scripts/check_task_docs.py tasks/repo-harness-bootstrap

# 4b. Focused verification
python scripts/run_cli.py show-layout

# 4c. Regression check
pytest -q
```

If any step fails, fix it before continuing.

### Step 5: Record

Update `docs/documentation.md` with:

```text
## Iteration: <date>
- Milestone: <id>
- Change: <one sentence>
- Files modified: <list>
- Verification result: <pass/fail + evidence>
- Decision: continue | adjust | rollback
- Next step: <what to do next>
```

### Step 6: Decide

- `continue`: verification passed and evidence is sufficient
- `adjust`: progress is partial, refine the approach
- `rollback`: regression or unexplained behavior

## Escalation Triggers

Stop and notify the human if:

1. the same approach fails twice
2. a fix would mutate source labels directly
3. the change crosses more than 5 core source files
4. you cannot explain the contract impact of the change
5. quality gates fail and the cause is unclear
