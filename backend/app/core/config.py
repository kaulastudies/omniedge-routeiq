from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OmniEdge RouteIQ API"
    app_version: str = "0.1.0"
    environment: Literal["local", "staging", "production"] = "local"
    api_prefix: str = ""

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Provider settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 18.0

    fireworks_api_key: str | None = None
    fireworks_base_url: str = "https://api.fireworks.ai/inference/v1"
    fireworks_model: str = "accounts/fireworks/models/llama-v3p1-70b-instruct"
    fireworks_timeout_seconds: float = 28.0

    # Routing policy defaults
    local_cost_per_1k_tokens_usd: float = 0.0
    cloud_cost_per_1k_tokens_usd: float = 0.0009
    local_latency_target_ms: int = 2500
    cloud_latency_target_ms: int = 5500
    max_prompt_chars: int = 24_000

    # Audit trail
    audit_log_path: str = "./data/audit/events.jsonl"
    persist_audit_log: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
