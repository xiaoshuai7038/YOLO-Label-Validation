# Needs Manifest - Production VLM Detector Integration

## Blocking Needs

- true live credentialed VLM execution requires the user to set the API key env
  var named in the runtime config
- true live detector execution requires the user to provide the detector
  weights path referenced in the runtime config

## Blocking Human Decisions

None for code implementation. The repository can proceed with:

- an OpenAI-compatible VLM transport contract
- env-var based secret loading
- a committed runtime config file with placeholder values
- Ultralytics-compatible local detector integration

## Blocking Environment Gaps

- true live credentialed VLM execution will require the user to set the API key
  env var named in the runtime config
- true live detector execution will require the user to provide the weights path
  referenced in the runtime config

## Non-Blocking Context Gaps

- final provider choice may be DashScope, vLLM, or another OpenAI-compatible
  endpoint; the implementation can stay provider-agnostic
- exact detector weights and device choice are user/runtime specific, so they
  belong in config rather than code

## Deferred Needs

| Need | Why deferred | Milestone |
|---|---|---|
| real credentialed smoke against the user's endpoint | blocked on secrets not present in repo | post-implementation validation |
| real detector smoke against the user's weights | blocked on local weights path and hardware | post-implementation validation |
