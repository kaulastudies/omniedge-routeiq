import logging
from uuid import uuid4

from app.core.config import Settings
from app.models.enums import ProviderName, RouteTarget
from app.models.route import ProviderResponse, RouteRequest, RouteResponse
from app.providers.base import ProviderError
from app.providers.registry import ProviderRegistry
from app.services.audit_store import AuditStore
from app.services.classifier import RoutingClassifier
from app.services.decision_engine import DecisionEngine
from app.services.metrics_store import MetricsStore

logger = logging.getLogger(__name__)


class RouterService:
    """Main orchestration layer behind POST /route."""

    def __init__(
        self,
        *,
        settings: Settings,
        providers: ProviderRegistry,
        classifier: RoutingClassifier,
        decision_engine: DecisionEngine,
        audit_store: AuditStore,
        metrics_store: MetricsStore,
    ):
        self.settings = settings
        self.providers = providers
        self.classifier = classifier
        self.decision_engine = decision_engine
        self.audit_store = audit_store
        self.metrics_store = metrics_store

    async def route(self, request: RouteRequest) -> RouteResponse:
        request_id = str(uuid4())
        audit_id = self.audit_store.create_id()
        self.audit_store.add(
            audit_id=audit_id,
            request_id=request_id,
            stage="request.received",
            message="Route request accepted by OmniEdge RouteIQ.",
            data={"task_type": request.task_type, "privacy_level": request.privacy_level.value},
        )

        classification = self.classifier.classify(request)
        self.audit_store.add(
            audit_id=audit_id,
            request_id=request_id,
            stage="classification.completed",
            message="Prompt classified across privacy, complexity, latency, and cost dimensions.",
            data=classification.model_dump(mode="json"),
        )

        decision = self.decision_engine.decide(request, classification)
        self.audit_store.add(
            audit_id=audit_id,
            request_id=request_id,
            stage="decision.selected",
            message=decision.decision_summary,
            data=decision.model_dump(mode="json"),
        )

        provider_response, fallback_used = await self._execute_with_fallback(request, decision.primary_provider, decision.backup_providers, audit_id, request_id)

        token_savings = self._estimate_savings(decision.target, provider_response)
        self.metrics_store.record(
            request_id=request_id,
            decision=decision,
            provider_response=provider_response,
            fallback_used=fallback_used,
            token_savings_estimate_usd=token_savings,
        )

        self.audit_store.add(
            audit_id=audit_id,
            request_id=request_id,
            stage="response.completed",
            message="Provider response normalized and metrics recorded.",
            data={
                "provider": provider_response.provider.value,
                "latency_ms": provider_response.latency_ms,
                "cost_usd": provider_response.cost_usd,
                "token_savings_estimate_usd": token_savings,
                "fallback_used": fallback_used,
            },
        )

        return RouteResponse(
            request_id=request_id,
            decision=decision,
            classification=classification,
            provider_response=provider_response,
            audit_id=audit_id,
            token_savings_estimate_usd=token_savings,
            latency_ms=provider_response.latency_ms,
            fallback_used=fallback_used,
            audit_timeline=self.audit_store.timeline(audit_id),
        )

    async def _execute_with_fallback(
        self,
        request: RouteRequest,
        primary: ProviderName,
        backups: list[ProviderName],
        audit_id: str,
        request_id: str,
    ) -> tuple[ProviderResponse, bool]:
        chain = [primary, *backups]
        errors: list[str] = []
        for index, provider_name in enumerate(chain):
            provider = self.providers.get(provider_name)
            try:
                self.audit_store.add(
                    audit_id=audit_id,
                    request_id=request_id,
                    stage="provider.attempt",
                    message=f"Attempting provider: {provider_name.value}.",
                    data={"attempt": index + 1},
                )
                response = await provider.generate(request)
                self.audit_store.add(
                    audit_id=audit_id,
                    request_id=request_id,
                    stage="provider.success",
                    message=f"Provider {provider_name.value} completed successfully.",
                    data={"fallback_used": index > 0},
                )
                return response, index > 0
            except ProviderError as exc:
                error = f"{provider_name.value}: {exc}"
                errors.append(error)
                logger.warning("Provider failed: %s", error)
                self.audit_store.add(
                    audit_id=audit_id,
                    request_id=request_id,
                    stage="provider.failed",
                    message=f"Provider {provider_name.value} failed; evaluating fallback.",
                    data={"error": str(exc)},
                )

        raise ProviderError(f"All providers failed: {' | '.join(errors)}")

    def _estimate_savings(self, target: RouteTarget, response: ProviderResponse) -> float:
        cloud_equivalent = (response.total_tokens / 1_000) * self.settings.cloud_cost_per_1k_tokens_usd
        if target == RouteTarget.LOCAL:
            return round(cloud_equivalent, 6)
        if target == RouteTarget.HYBRID:
            return round(cloud_equivalent * 0.45, 6)
        return 0.0
