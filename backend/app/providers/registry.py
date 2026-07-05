from app.core.config import Settings
from app.models.enums import ProviderName
from app.providers.base import BaseProvider
from app.providers.cloud_fireworks import FireworksProvider
from app.providers.local_ollama import OllamaProvider
from app.providers.mock_cloud import MockCloudProvider


class ProviderRegistry:
    def __init__(self, settings: Settings):
        self.providers: dict[ProviderName, BaseProvider] = {
            ProviderName.OLLAMA: OllamaProvider(settings),
            ProviderName.FIREWORKS: FireworksProvider(settings),
            ProviderName.MOCK_CLOUD: MockCloudProvider(settings),
        }

    def get(self, name: ProviderName) -> BaseProvider:
        return self.providers[name]

    def all(self) -> list[BaseProvider]:
        return list(self.providers.values())
