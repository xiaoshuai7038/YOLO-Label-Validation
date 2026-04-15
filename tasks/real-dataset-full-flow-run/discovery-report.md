# Discovery Report - Real Dataset Full Flow Run

## Request

Run the full harness pipeline on the real dataset at
`E:\workspace\cigarette-identify\预标注测试\20264010`.

## Confirmed

- the real dataset path is fixed and available locally
- the correct YOLO ingest pairing mode is
  `stem_before_double_underscore`
- zero-annotation images are in scope and must not be skipped
- the local review backend is the installed `codex` CLI, not an HTTP API
- the current committed live-review timeout baseline is `600s`

## Relevant Context

- the dataset is a mixed image/label directory and requires
  `--pairing-mode stem_before_double_underscore`
- normalization has already been proven on this dataset in a prior slice
- the semantic-review gap for zero-annotation images has already been fixed
- the local review runtime uses `codex exec`
- a real single-image Codex smoke has already succeeded after increasing the
  live timeout baseline to `600s`

## Expected Run Shape

- source images: `520`
- source annotations: `1088`
- zero-annotation images: `245`
- expected `run-risk` candidate images: materially larger than the pre-fix
  annotation-only candidate set because image-level empty-prelabel cases are
  now included

## Known Risks

- `run-vlm` is the long pole because local Codex review is sequential
- detector live weights are not currently present at `artifacts/models/yolo11n.pt`
- if the real run hits another runtime blocker, it must be recorded before any
  code workaround is applied

## Existing Documentation Health

- repo-level roadmap and failure taxonomy are already updated for the
  zero-annotation image-review fix
- prior tasks already cover the ingest compatibility slice and the
  zero-annotation review closure slice
- this task exists only to capture the real end-to-end execution evidence
