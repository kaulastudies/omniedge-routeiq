# OmniEdge RouteIQ v0.9 — Local-Heavy Prove-or-Escalate

## Locked objective

Pass the accuracy gate while reducing Fireworks usage by avoiding remote
calls, not by truncating model outputs.

## Execution order

1. Parse the complete task without dropping instruction, input, or context.
2. Detect task family conservatively.
3. Attempt a category-specific deterministic or local solution.
4. Validate the local answer using independent evidence.
5. Accept only when the validation gate passes.
6. Otherwise make one Fireworks call using an evaluator-provided model.
7. Normalize the result into the required output schema.

## Local acceptance rules

### Arithmetic
Accept only when the expression or word problem can be parsed and independently
recomputed.

### Sentiment
Accept only when lexical and local-classifier signals agree strongly.

### Named entities
Accept only when extracted spans exist in the source and match the requested
schema.

### Code
Accept only when syntax validation and generated tests pass.

### Logic
Accept only when constraints can be converted into a deterministic form.

### Summarization
Accept locally only after length, coverage, and contradiction checks.

### Factual knowledge
Escalate unless the answer can be verified from bundled local knowledge.

## Remote policy

- Use only FIREWORKS_BASE_URL supplied by the evaluator.
- Use only models supplied through ALLOWED_MODELS.
- Use MiniMax as the initial accuracy baseline.
- Never use an external inference provider.
- Never reduce accuracy by imposing unsafe output truncation.

## Production stop rules

- Do not submit a version that has not passed unseen randomized tests.
- Do not overwrite a qualified image tag.
- Do not accept local-model confidence as proof of correctness.
- Do not modify multiple scoring variables in one experiment.
