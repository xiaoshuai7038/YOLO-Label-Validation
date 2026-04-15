# Plan - Materialized YOLO Export

## Milestones

| ID | Goal | Status |
|---|---|---|
| `M-001` | define the export contract and task evidence | completed |
| `M-002` | implement YOLO export helpers and CLI entrypoint | completed |
| `M-003` | validate with tests and a real run export | completed |

## Validation Route

1. task-doc gate passes on `tasks/materialized-yolo-export/`
2. unit and CLI tests prove YOLO labels, copied images, and export metadata
3. the real run exports to a derived YOLO directory with the expected file
   counts
