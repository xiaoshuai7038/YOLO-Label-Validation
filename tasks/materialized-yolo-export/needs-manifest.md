# Needs Manifest - Materialized YOLO Export

## Inputs

- run dir: `artifacts/runs/real-full-flow/`
- materialized view:
  `artifacts/runs/real-full-flow/materialized_dataset/`
- source images:
  `E:\workspace\cigarette-identify\预标注测试\20264010`

## Blocking Needs

- none at task start

## Deferred Needs

- optional future support for split-aware dataset yaml generation
- optional future support for link-based image transport when source and output
  live on the same volume
