from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ProviderHealth(BaseModel):
    name: str
    available: bool
    latency_ms: int | None = None
    detail: str | None = None


class StatusResponse(BaseModel):
    service: str = "omniedge-routeiq-api"
    version: str
    environment: str
    status: str = "ok"
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    providers: list[ProviderHealth]
