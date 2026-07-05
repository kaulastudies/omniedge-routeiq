import time

import httpx

from app.core.config import Settings
from app.models.enums import ProviderName
from app.models.route import ProviderResponse, RouteRequest
from app.providers.base import BaseProvider, ProviderError
from app.utils.tokens import estimate_tokens


class OllamaProvider(BaseProvider):
    name = ProviderName.OLLAMA

    def __init__(self, settings: Settings):
        self.settings = settings

    async def generate(self, request: RouteRequest) -> ProviderResponse:
        started = time.perf_counter()
        url = f"{self.settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.settings.ollama_model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 600,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.ollama_timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001 - convert provider errors into routing fallback
            raise ProviderError(f"Ollama unavailable: {exc}") from exc

        text = data.get("response", "").strip()
        if not text:
            raise ProviderError("Ollama returned an empty response.")

        latency_ms = round((time.perf_counter() - started) * 1000)
        input_tokens = estimate_tokens(request.prompt)
        output_tokens = estimate_tokens(text)
        return ProviderResponse(
            provider=self.name,
            model=self.settings.ollama_model,
            text=text,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
            raw={"engine": "ollama"},
        )

    async def health(self) -> tuple[bool, int | None, str | None]:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.settings.ollama_base_url.rstrip('/')}/api/tags")
                response.raise_for_status()
            return True, round((time.perf_counter() - started) * 1000), "Ollama reachable"
        except Exception as exc:  # noqa: BLE001
            return False, None, f"Ollama not reachable: {exc}"
