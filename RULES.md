# RULES

1. Do not stop for confirmation between milestones unless a real user decision
   or external blocker appears.
2. Keep changes deterministic and contract-first.
3. Preserve source data as read-only. Only artifacts under run outputs are writable.
4. Every milestone ends with verification, repair if needed, and status updates.
5. If a test fails, record the failure in task docs before or alongside the fix.
6. Preserve fixture mode for offline tests even when live integrations are added.
7. Keep docs synchronized with actual code state; no milestone promotion without evidence.
8. Never commit secrets, bearer tokens, or user-specific absolute model paths.
