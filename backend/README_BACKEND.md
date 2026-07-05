# OmniEdge RouteIQ Backend

FastAPI backend for an enterprise-grade hybrid AI routing layer. The service routes tasks between local inference, cloud inference, or hybrid execution based on privacy, complexity, latency, token cost, and fallback reliability.

## Core endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/route` | Classify prompt, decide route, execute provider, return audit trail |
| `GET` | `/status` | API + provider health |
| `GET` | `/metrics` | Dashboard metrics for token savings, latency, fallback, split |
| `GET` | `/simulations` | Built-in scenario list for frontend console |
| `POST` | `/simulations/{scenario_id}` | Run scenario through the real routing path |
| `GET` | `/audit/recent` | Recent audit events for demo/debugging |

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open docs at `http://localhost:8000/docs`.

## Optional Ollama setup

```bash
ollama pull llama3.1:8b
ollama serve
```

If Ollama is not running, RouteIQ automatically falls back to the configured backup chain. If Fireworks API keys are absent, the mock cloud provider keeps the hackathon demo working.

## Example route request

```bash
curl -X POST http://localhost:8000/route \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "privacy_review",
    "privacy_level": "regulated",
    "prompt": "Summarize this patient note. Phone: +91 9876543210. Keep sensitive data local.",
    "max_latency_ms": 3500,
    "token_budget_usd": 0.001
  }'
```

## Architecture

```txt
POST /route
  -> RoutingClassifier
  -> DecisionEngine
  -> ProviderRegistry
       -> OllamaProvider
       -> FireworksProvider
       -> MockCloudProvider
  -> Fallback execution chain
  -> AuditStore + MetricsStore
  -> RouteResponse for dashboard
```

## Frontend-ready response fields

The `/route` response includes:

- `decision.target`: `local`, `cloud`, or `hybrid`
- `decision.reason_codes`: displayable explanation tags
- `decision.confidence`: panel confidence score
- `classification.privacy_score`, `complexity_score`, `latency_score`, `cost_score`
- `provider_response.provider`, `latency_ms`, `input_tokens`, `output_tokens`, `cost_usd`
- `token_savings_estimate_usd`
- `fallback_used`
- `audit_timeline`

## Demo scenarios

Use `/simulations` to populate the frontend simulation console. Current scenarios:

- `local_sensitive_prompt`
- `cloud_complex_architecture`
- `hybrid_confidential_code`
- `fallback_no_key_demo`

## Deployment

### Docker

```bash
docker build -t omniedge-routeiq-api .
docker run -p 8000:8000 --env-file .env omniedge-routeiq-api
```

### Render

This backend includes `render.yaml`. Add environment variables in Render dashboard and set the health check path to `/status`.
