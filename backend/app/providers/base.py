from abc import ABC, abstractmethod

from app.models.enums import ProviderName
from app.models.route import ProviderResponse, RouteRequest


class ProviderError(RuntimeError):
    """Raised when an inference provider cannot fulfill the request."""


class BaseProvider(ABC):
    name: ProviderName

    @abstractmethod
    async def generate(self, request: RouteRequest) -> ProviderResponse:
        raise NotImplementedError

    @abstractmethod
    async def health(self) -> tuple[bool, int | None, str | None]:
        raise NotImplementedError
