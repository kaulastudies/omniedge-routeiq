import time

import httpx

from app.core.config import Settings
from app.models.enums import ProviderName
from app.models.route import ProviderResponse, RouteRequest
from app.providers.base import BaseProvider, ProviderError
from app.utils.tokens import estimate_tokens


class FireworksProvider(BaseProvider):
    name = ProviderName.FIREWORKS

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: RouteRequest) -> ProviderResponse:
        if not self.settings.fireworks_api_key:
            raise ProviderError("FIREWORKS_API_KEY is not configured.")

        started = time.perf_counter()
        url = f"{self.settings.fireworks_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.fireworks_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are the cloud inference provider behind OmniEdge RouteIQ. Be precise, enterprise-grade, and concise.",
                },
                {"role": "user", "content": request.prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.fireworks_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.fireworks_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"Fireworks request failed: {exc}") from exc

        try:
            text = data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            raise ProviderError("Fireworks returned an unexpected response shape.") from exc

        input_tokens = data.get("usage", {}).get("prompt_tokens") or estimate_tokens(request.prompt)
        output_tokens = data.get("usage", {}).get("completion_tokens") or estimate_tokens(text)
        cost_usd = ((input_tokens + output_tokens) / 1_000) * self.settings.cloud_cost_per_1k_tokens_usd
        latency_ms = round((time.perf_counter() - started) * 1000)

        return ProviderResponse(
            provider=self.name,
            model=self.settings.fireworks_model,
            text=text,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=round(cost_usd, 6),
            raw={"engine": "fireworks", "usage": data.get("usage", {})},
        )

    async def health(self) -> tuple[bool, int | None, str | None]:
        if not self.settings.fireworks_api_key:
            return False, None, "FIREWORKS_API_KEY missing; mock cloud fallback will be used."
        return True, None, "Fireworks API key configured"
