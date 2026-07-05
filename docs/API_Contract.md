# API Contract: RouteIQ Engine

## Endpoint: `POST /api/v1/route`
Analyzes a prompt and executes the AI response via the optimal route.

### Request Payload (JSON)
```json
{
  "prompt": "Summarize this 10-page document...",
  "max_tokens": 500
}
