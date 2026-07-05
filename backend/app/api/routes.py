from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_audit_store, get_metrics_store, get_provider_registry, get_router_service
from app.core.config import get_settings
from app.models.metrics import MetricsResponse
from app.models.route import RouteRequest, RouteResponse
from app.models.status import ProviderHealth, StatusResponse
from app.providers.base import ProviderError
from app.providers.registry import ProviderRegistry
from app.services.audit_store import AuditStore
from app.services.metrics_store import MetricsStore
from app.services.router_service import RouterService
from app.services.simulation import SIMULATION_SCENARIOS

router = APIRouter(tags=["RouteIQ"])


@router.post("/route", response_model=RouteResponse)
async def route_task(request: RouteRequest, service: RouterService = Depends(get_router_service)) -> RouteResponse:
    """Classify, route, execute, fallback if required, and return an auditable routing decision."""
    try:
        return await service.route(request)
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/status", response_model=StatusResponse)
async def status(registry: ProviderRegistry = Depends(get_provider_registry)) -> StatusResponse:
    """Health check for API and inference providers."""
    settings = get_settings()
    provider_health: list[ProviderHealth] = []
    for provider in registry.all():
        available, latency_ms, detail = await provider.health()
        provider_health.append(
            ProviderHealth(name=provider.name.value, available=available, latency_ms=latency_ms, detail=detail)
        )
    return StatusResponse(
        version=settings.app_version,
        environment=settings.environment,
        providers=provider_health,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics(store: MetricsStore = Depends(get_metrics_store)) -> MetricsResponse:
    """Dashboard-ready metrics: token savings, latency, fallback count, provider split."""
    return store.snapshot()


@router.get("/audit/recent")
async def recent_audit(limit: int = 20, store: AuditStore = Depends(get_audit_store)) -> dict:
    """Developer/demo endpoint for recent audit events."""
    return {"events": store.recent(limit=limit)}


@router.get("/simulations")
async def list_simulations() -> dict:
    """List built-in demo scenarios for the simulation console."""
    return {
        "scenarios": [
            {
                "id": scenario_id,
                "task_type": scenario.task_type,
                "privacy_level": scenario.privacy_level.value,
                "force_route": scenario.force_route.value if scenario.force_route else None,
                "prompt_preview": scenario.prompt[:140],
            }
            for scenario_id, scenario in SIMULATION_SCENARIOS.items()
        ]
    }


@router.post("/simulations/{scenario_id}", response_model=RouteResponse)
async def run_simulation(scenario_id: str, service: RouterService = Depends(get_router_service)) -> RouteResponse:
    """Run a built-in scenario through the same /route orchestration path."""
    scenario = SIMULATION_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Unknown simulation scenario.")
    try:
        return await service.route(scenario)
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
