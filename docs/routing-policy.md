# RouteIQ Routing Policy Engine

The system uses a deterministic rule engine to evaluate tasks before execution.

## Phase 1: Complexity Analysis
The router analyzes the incoming prompt against three metrics:
1. Length: If input tokens > 1000 -> Route to Cloud (Local context window limit).
2. Keyword Triggers: If prompt contains ["analyze", "code", "derive", "financial", "strict"] -> Route to Cloud (High reasoning required).
3. User Override: If require_high_accuracy == true -> Route to Cloud.

## Phase 2: Execution Fork
* If all Complexity conditions are FALSE: Route to Edge Node (Local Ollama / Zero Cost).
* If ANY Complexity condition is TRUE: Route to AMD Hardware (Fireworks API / Paid Tokens).

## Phase 3: Fallback Mechanism (The Verifier)
If the Cloud API times out or fails (HTTP 500), the router automatically degrades to the Local Edge Node to ensure 100% uptime, flagging the UI with a "Degraded State" warning.
