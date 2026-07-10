# OmniEdge RouteIQ — Local Gemma Hybrid

Track 1 scoring architecture:

1. General deterministic local handlers for high-confidence tasks
2. Gemma 3 1B IT Q4_K_M inference inside the container
3. Official evaluator-provided Fireworks fallback for unresolved tasks

No external inference provider is used. Fireworks requests use only the
runtime-provided FIREWORKS_BASE_URL, FIREWORKS_API_KEY, and ALLOWED_MODELS.

The previously qualified v0.4 image remains available as a rollback image.
