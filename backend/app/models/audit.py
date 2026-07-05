from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    audit_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    stage: str
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
