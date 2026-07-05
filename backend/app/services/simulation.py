from app.models.enums import PrivacyLevel
from app.models.route import RouteRequest


SIMULATION_SCENARIOS: dict[str, RouteRequest] = {
    "local_sensitive_prompt": RouteRequest(
        task_type="privacy_review",
        privacy_level=PrivacyLevel.REGULATED,
        prompt="Summarize this confidential enterprise incident report containing employee ID EMP-48291 and internal access logs without exposing sensitive identifiers.",
        max_latency_ms=3500,
        token_budget_usd=0.001,
    ),
    "cloud_complex_architecture": RouteRequest(
        task_type="architecture",
        privacy_level=PrivacyLevel.PUBLIC,
        prompt="Design a production-grade AI inference routing architecture for OmniEdge RouteIQ with local-first execution, cloud escalation, retries, audit logs, and observability.",
        max_latency_ms=9000,
        token_budget_usd=0.02,
    ),
    "hybrid_confidential_code": RouteRequest(
        task_type="code_review",
        privacy_level=PrivacyLevel.CONFIDENTIAL,
        prompt="Review this confidential RouteIQ provider-router code path and suggest a secure refactor while keeping secrets, keys, and internal implementation details protected. def login(user): pass",
        max_latency_ms=7000,
        token_budget_usd=0.005,
    ),
    "fallback_no_key_demo": RouteRequest(
        task_type="demo",
        privacy_level=PrivacyLevel.PUBLIC,
        prompt="Create a short executive summary for the OmniEdge RouteIQ demo showing how hybrid AI routing reduces cloud token waste, protects private prompts, and improves fallback reliability.",
        force_route="cloud",
    ),
}

# RouteIQ simulation copy aligned for final demo.
