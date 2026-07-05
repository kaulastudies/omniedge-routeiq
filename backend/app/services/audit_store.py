import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.models.audit import AuditEvent


class AuditStore:
    """In-memory audit timeline with optional JSONL persistence for demo traceability."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._events: list[AuditEvent] = []

    def create_id(self) -> str:
        return str(uuid4())

    def add(self, *, audit_id: str, request_id: str, stage: str, message: str, data: dict[str, Any] | None = None) -> AuditEvent:
        event = AuditEvent(
            audit_id=audit_id,
            request_id=request_id,
            stage=stage,
            message=message,
            data=data or {},
        )
        self._events.append(event)
        if self.settings.persist_audit_log:
            self._persist(event)
        return event

    def timeline(self, audit_id: str) -> list[dict[str, Any]]:
        return [event.model_dump(mode="json") for event in self._events if event.audit_id == audit_id]

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [event.model_dump(mode="json") for event in self._events[-limit:]]

    def _persist(self, event: AuditEvent) -> None:
        path = Path(self.settings.audit_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=False) + "\n")
