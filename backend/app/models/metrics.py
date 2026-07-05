from pydantic import BaseModel, Field


class MetricsResponse(BaseModel):
    total_requests: int
    local_requests: int
    cloud_requests: int
    hybrid_requests: int
    fallback_count: int
    avg_latency_ms: float
    estimated_cloud_tokens_avoided: int
    estimated_token_savings_usd: float
    provider_split_percent: dict[str, float] = Field(default_factory=dict)
    recent_decisions: list[dict] = Field(default_factory=list)
