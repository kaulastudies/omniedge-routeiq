import asyncio
import time

from app.core.config import Settings
from app.models.enums import ProviderName
from app.models.route import ProviderResponse, RouteRequest
from app.providers.base import BaseProvider
from app.utils.tokens import estimate_tokens


class MockCloudProvider(BaseProvider):
    """Deterministic provider for demos, hackathon judging, and API-key-free deployments."""

    name = ProviderName.MOCK_CLOUD

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: RouteRequest) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.18)
        text = (
            "[Mock Cloud Completion] RouteIQ processed this task through the cloud fallback path. "
            "In production, this slot is fulfilled by Fireworks AI. The router preserved an audit trail, "
            "captured token economics, and returned a provider-normalized response."
        )
        input_tokens = estimate_tokens(request.prompt)
        output_tokens = estimate_tokens(text)
        cost_usd = ((input_tokens + output_tokens) / 1_000) * self.settings.cloud_cost_per_1k_tokens_usd
        return ProviderResponse(
            provider=self.name,
            model="routeiq-mock-cloud-v1",
            text=text,
            latency_ms=round((time.perf_counter() - started) * 1000),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 6),
            raw={"engine": "mock_cloud", "deterministic": True},
        )

    async def health(self) -> tuple[bool, int | None, str | None]:
        return True, 1, "Mock cloud provider ready"
