# OmniEdge RouteIQ v1.0 — Batch First

Token-efficiency strategy:

1. Read every benchmark task.
2. Send one compact batch through the evaluator-provided Fireworks endpoint.
3. Require one strict JSON response containing every answer.
4. Recover only missing answers individually.
5. Use only models provided through ALLOWED_MODELS.

The qualified rollback image remains unchanged.
