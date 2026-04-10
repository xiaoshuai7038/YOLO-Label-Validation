# Needs Manifest

## Task

- Task slug: `repo-harness-bootstrap`

## Blocking Needs

- None.

## Non-Blocking Needs

| Need | Reason | Action |
|---|---|---|
| Real sample datasets | needed for FR-001 ingestion fixtures later | defer to M2 |
| Service credentials | needed for VLM or CVAT integrations later | defer to M4/M5 |
| Production Python version pin | useful for CI parity | use Python 3.12 default for now |

## Deferred Needs

| Need | Reason | Target Milestone |
|---|---|---|
| Golden set payloads | not needed for harness foundation | M3 |
| Threshold calibration evidence | not needed for harness foundation | M3 |
| Cleanlab and FiftyOne runtime integration | not needed for harness foundation | M4 |
| Detector B weights and eval data | not needed for harness foundation | M5 |
| CVAT endpoint and auth | not needed for harness foundation | M5 |
