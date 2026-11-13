"""Configuration settings for the local AgentBreaker FastAPI application."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """Runtime configuration for local AgentBreaker API server."""

    model_config = SettingsConfigDict(
        env_prefix="AGENTBREAKER_API_",
        env_file=".env",
        extra="ignore",
    )

    host: str = Field(
        default="127.0.0.1",
        description="Loopback binding interface. Public 0.0.0.0 binding is strictly discouraged.",
    )
    port: int = Field(
        default=8000,
        description="Local HTTP API listening port.",
    )
    cors_origins: list[str] = Field(
        default=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        description="Explicitly trusted frontend origin allowlist for CORS.",
    )
    max_request_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum permissible request payload body size (10MB default).",
    )
    local_api_key: str | None = Field(
        default=None,
        description="Optional pre-shared token for defense-in-depth authorization.",
    )
    trusted_hosts: list[str] = Field(
        default=["127.0.0.1", "localhost", "testserver"],
        description="Allowed Host header values for DNS rebinding protection.",
    )
    docs_enabled: bool = Field(
        default=True,
        description="Whether Swagger UI (/docs) and OpenAPI JSON are enabled.",
    )


api_settings = APISettings()
