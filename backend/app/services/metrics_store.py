from collections import deque
from statistics import mean
from typing import Any

from app.core.config import Settings
from app.models.enums import RouteTarget
from app.models.metrics import MetricsResponse
from app.models.route import RouteDecision, ProviderResponse


class MetricsStore:
    """Small in-memory metrics layer for the hackathon backend and dashboard."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.total_requests = 0
        self.local_requests = 0
        self.cloud_requests = 0
        self.hybrid_requests = 0
        self.fallback_count = 0
        self.latencies: list[int] = []
        self.estimated_cloud_tokens_avoided = 0
        self.estimated_token_savings_usd = 0.0
        self.recent_decisions: deque[dict[str, Any]] = deque(maxlen=12)

    def record(
        self,
        *,
        request_id: str,
        decision: RouteDecision,
        provider_response: ProviderResponse,
        fallback_used: bool,
        token_savings_estimate_usd: float,
    ) -> None:
        self.total_requests += 1
        if decision.target == RouteTarget.LOCAL:
            self.local_requests += 1
            self.estimated_cloud_tokens_avoided += provider_response.total_tokens
        elif decision.target == RouteTarget.CLOUD:
            self.cloud_requests += 1
        elif decision.target == RouteTarget.HYBRID:
            self.hybrid_requests += 1
            # Hybrid still avoids sending full raw context in the demo policy.
            self.estimated_cloud_tokens_avoided += max(0, provider_response.input_tokens // 2)

        if fallback_used:
            self.fallback_count += 1

        self.latencies.append(provider_response.latency_ms)
        self.estimated_token_savings_usd = round(
            self.estimated_token_savings_usd + max(0.0, token_savings_estimate_usd), 6
        )
        self.recent_decisions.appendleft(
            {
                "request_id": request_id,
                "target": decision.target.value,
                "provider": provider_response.provider.value,
                "latency_ms": provider_response.latency_ms,
                "fallback_used": fallback_used,
                "confidence": decision.confidence,
                "summary": decision.decision_summary,
            }
        )

    def snapshot(self) -> MetricsResponse:
        total = max(1, self.total_requests)
        provider_split = {
            "local": round((self.local_requests / total) * 100, 2),
            "cloud": round((self.cloud_requests / total) * 100, 2),
            "hybrid": round((self.hybrid_requests / total) * 100, 2),
        }
        return MetricsResponse(
            total_requests=self.total_requests,
            local_requests=self.local_requests,
            cloud_requests=self.cloud_requests,
            hybrid_requests=self.hybrid_requests,
            fallback_count=self.fallback_count,
            avg_latency_ms=round(mean(self.latencies), 2) if self.latencies else 0.0,
            estimated_cloud_tokens_avoided=self.estimated_cloud_tokens_avoided,
            estimated_token_savings_usd=round(self.estimated_token_savings_usd, 6),
            provider_split_percent=provider_split,
            recent_decisions=list(self.recent_decisions),
        )
