from functools import lru_cache

from app.core.config import Settings, get_settings
from app.providers.registry import ProviderRegistry
from app.services.audit_store import AuditStore
from app.services.classifier import RoutingClassifier
from app.services.decision_engine import DecisionEngine
from app.services.metrics_store import MetricsStore
from app.services.router_service import RouterService


@lru_cache
def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(get_settings())


@lru_cache
def get_audit_store() -> AuditStore:
    return AuditStore(get_settings())


@lru_cache
def get_metrics_store() -> MetricsStore:
    return MetricsStore(get_settings())


@lru_cache
def get_classifier() -> RoutingClassifier:
    return RoutingClassifier()


@lru_cache
def get_decision_engine() -> DecisionEngine:
    return DecisionEngine()


def get_router_service() -> RouterService:
    settings: Settings = get_settings()
    return RouterService(
        settings=settings,
        providers=get_provider_registry(),
        classifier=get_classifier(),
        decision_engine=get_decision_engine(),
        audit_store=get_audit_store(),
        metrics_store=get_metrics_store(),
    )
