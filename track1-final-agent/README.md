# OmniEdge RouteIQ — Conservative v0.8

Track 1 token-efficient agent router.

## Production strategy

1. Exact arithmetic is solved locally only when the expression can be parsed
   and evaluated deterministically.
2. Ambiguous arithmetic and all reasoning tasks use evaluator-provided
   Fireworks inference.
3. MiniMax is the proven primary remote model.
4. Kimi and Gemma 4 models remain evaluator-approved fallbacks.
5. No external inference provider is used.
6. Only models supplied through `ALLOWED_MODELS` are called.

## Runtime contract

Input:

`/input/tasks.json`

Output:

`/output/results.json`

Runtime environment:

- `FIREWORKS_API_KEY`
- `FIREWORKS_BASE_URL`
- `ALLOWED_MODELS`
