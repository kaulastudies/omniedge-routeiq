from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

from app.models.enums import FallbackMode, PrivacyLevel, ProviderName, RiskFlag, RouteTarget


class RouteRequest(BaseModel):
    """Public request body for POST /route."""

    prompt: str = Field(..., min_length=1, max_length=24_000)
    task_type: str = Field(default="general", examples=["summarization", "coding", "legal_review"])
    privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL
    user_id: str | None = None
    session_id: str | None = None
    max_latency_ms: int | None = Field(default=None, ge=250, le=120_000)
    token_budget_usd: float | None = Field(default=None, ge=0)
    force_route: RouteTarget | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Prompt cannot be empty.")
        return value


class ClassificationResult(BaseModel):
    privacy_score: float = Field(..., ge=0, le=1)
    complexity_score: float = Field(..., ge=0, le=1)
    latency_score: float = Field(..., ge=0, le=1)
    cost_score: float = Field(..., ge=0, le=1)
    estimated_input_tokens: int
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    explanation: list[str] = Field(default_factory=list)


class RouteDecision(BaseModel):
    target: RouteTarget
    primary_provider: ProviderName
    backup_providers: list[ProviderName] = Field(default_factory=list)
    confidence: float = Field(..., ge=0, le=1)
    fallback_mode: FallbackMode = FallbackMode.NONE
    reason_codes: list[str] = Field(default_factory=list)
    decision_summary: str


class ProviderResponse(BaseModel):
    provider: ProviderName
    model: str
    text: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    raw: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class RouteResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision: RouteDecision
    classification: ClassificationResult
    provider_response: ProviderResponse
    audit_id: str
    token_savings_estimate_usd: float
    latency_ms: int
    fallback_used: bool
    audit_timeline: list[dict[str, Any]]
