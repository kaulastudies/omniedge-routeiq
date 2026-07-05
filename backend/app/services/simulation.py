from app.models.enums import PrivacyLevel
from app.models.route import RouteRequest


SIMULATION_SCENARIOS: dict[str, RouteRequest] = {
    "local_sensitive_prompt": RouteRequest(
        task_type="privacy_review",
        privacy_level=PrivacyLevel.REGULATED,
        prompt="Summarize this patient discharge note and insurance ID AB123456 without exposing PII. Patient phone: +91 9876543210.",
        max_latency_ms=3500,
        token_budget_usd=0.001,
    ),
    "cloud_complex_architecture": RouteRequest(
        task_type="architecture",
        privacy_level=PrivacyLevel.PUBLIC,
        prompt="Design a production-grade multi-agent architecture for a global SaaS routing layer with retries, audit logs, and observability.",
        max_latency_ms=9000,
        token_budget_usd=0.02,
    ),
    "hybrid_confidential_code": RouteRequest(
        task_type="code_review",
        privacy_level=PrivacyLevel.CONFIDENTIAL,
        prompt="Review this internal FastAPI authentication architecture and suggest a secure refactor without exposing private implementation details. def login(user): pass",
        max_latency_ms=7000,
        token_budget_usd=0.005,
    ),
    "fallback_no_key_demo": RouteRequest(
        task_type="demo",
        privacy_level=PrivacyLevel.PUBLIC,
        prompt="Create a short executive summary for a hackathon demo showing why AI routing reduces cloud token waste and improves reliability.",
        force_route="cloud",
    ),
}
