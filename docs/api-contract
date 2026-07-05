# RouteIQ API Contract

## Endpoint: POST /api/v1/route
This endpoint receives a user prompt, decides the optimal route (local vs. cloud), and executes the generation.

### Request Payload (from Frontend to Backend)
{
  "prompt": "Summarize this log file...",
  "max_tokens": 500,
  "require_high_accuracy": false
}

### Response Payload (from Backend to Frontend)
{
  "task_id": "req_a1b2c3d4",
  "route_decision": {
    "target": "local", 
    "reason": "Task complexity is low. Context window is under 500 tokens.",
    "confidence_score": 0.88
  },
  "execution": {
    "model_used": "ollama/llama3-8b",
    "response_text": "Here is the summary of your log file...",
    "latency_ms": 412.5
  },
  "metrics": {
    "estimated_cloud_cost_tokens": 150,
    "actual_paid_tokens": 0,
    "tokens_saved": 150
  }
}

*Note: If target is "cloud", model_used becomes a Fireworks AI model, actual_paid_tokens is updated, and tokens_saved becomes 0.*
