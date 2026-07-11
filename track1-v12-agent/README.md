# OmniEdge RouteIQ — Track 1 Local-First Agent

Token-efficient benchmark agent for AMD ACT II Track 1.

## Evaluator Contract

- Reads `/input/tasks.json`.
- Writes `/output/results.json`.
- Returns `task_id` and `answer` for every task.
- Uses evaluator-provided Fireworks credentials and allowed models.
- Runs on `linux/amd64`.

## Routing Architecture

```text
Input tasks
→ deterministic arithmetic and sentiment solvers
→ Qwen3 1.7B Q8 local inference
→ Fireworks batch fallback
→ individual recovery for missing answers
→ results.json
```

Local inference uses zero evaluator-counted Fireworks tokens.

## Protected v1.2 Champion

- Image: `ghcr.io/kaulastudies/omniedge-routeiq-track1:v1.2-local-core`
- Best completed evaluation observed: **94.7% accuracy**
- Fireworks usage: **3,974 tokens**
- Previous qualified baseline: **12,531 tokens**
- Token reduction: **68.3%**

The portal later displayed an infrastructure error during a recheck. The figures above record the completed evaluation observed before that recheck.

## v1.2.1 Guarded Challenger

- Image: `ghcr.io/kaulastudies/omniedge-routeiq-track1:v1.2.1-guarded-qwen`
- Splits unresolved tasks into guarded Qwen batches of four.
- A malformed response affects only its batch.
- Published and container-tested, but not yet benchmark-scored.

## Reliability Controls

- Strict task-ID validation
- Complete JSON-array validation
- Reasoning-tag and end-marker cleanup
- Deterministic handling of provably safe tasks
- Fireworks fallback for unresolved tasks
- Individual recovery for missing remote answers
- Tested with two CPUs and four gigabytes of memory
