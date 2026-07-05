from enum import Enum


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    REGULATED = "regulated"


class RouteTarget(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class ProviderName(str, Enum):
    OLLAMA = "ollama"
    FIREWORKS = "fireworks"
    MOCK_CLOUD = "mock_cloud"


class FallbackMode(str, Enum):
    NONE = "none"
    LOCAL_TO_CLOUD = "local_to_cloud"
    CLOUD_TO_LOCAL = "cloud_to_local"
    CLOUD_TO_MOCK = "cloud_to_mock"
    HYBRID_TO_LOCAL = "hybrid_to_local"
    HYBRID_TO_CLOUD = "hybrid_to_cloud"


class RiskFlag(str, Enum):
    PII = "pii"
    SECRET = "secret"
    FINANCIAL = "financial"
    HEALTH = "health"
    LEGAL = "legal"
    SOURCE_CODE = "source_code"
    LONG_CONTEXT = "long_context"
    COMPLEX_REASONING = "complex_reasoning"
    URGENT_LATENCY = "urgent_latency"
    COST_SENSITIVE = "cost_sensitive"
