# OmniEdge RouteIQ: System Architecture

## Core Flow
OmniEdge RouteIQ operates as an intelligent middleware layer. It intercepts user prompts, evaluates their complexity, and routes them to the most cost-efficient execution environment without sacrificing accuracy.

1. **User Interface (Next.js 15):** The client submits a natural language prompt via the Command Nexus dashboard.
2. **Routing Middleware (FastAPI):** Receives the payload. The `RoutePolicyEngine` evaluates the prompt using a lightweight NLP heuristic (length, required context, keyword complexity).
3. **Execution Fork:**
   - **Path A (Simple Task):** Routed to local `Ollama` (Llama 3 8B) running on the edge node. Cost: $0.00.
   - **Path B (Complex Task):** Routed to `Fireworks AI` (Llama 3 70B / AMD Hardware). Cost: Paid (Tokens).
4. **Audit Logging (SQLite):** The transaction (route taken, tokens consumed, tokens saved, latency) is logged asynchronously.
5. **Response:** Streamed back to the Next.js UI alongside updated telemetry metrics.

## Tech Stack
- **Frontend:** Next.js (App Router), Tailwind CSS, shadcn/ui, Recharts.
- **Backend:** Python 3.12, FastAPI, Pydantic, SQLAlchemy.
- **AI Infrastructure:** Ollama (Local), Fireworks AI (Remote).
