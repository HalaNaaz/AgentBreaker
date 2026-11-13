"""Global configuration settings for AgentBreaker using pydantic-settings."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentBreakerSettings(BaseSettings):
    """Application-wide settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="AGENTBREAKER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    target_url: str = Field(
        default="http://localhost:8000/v1",
        description="Default target endpoint URL.",
    )
    target_type: str = Field(
        default="openai_compatible",
        description="Default target adapter type.",
    )
    target_model: str = Field(
        default="default-model",
        description="Target model identifier.",
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="Target authentication API key (hidden).",
    )
    auth_header_name: str = Field(
        default="Authorization",
        description="Default authentication header name.",
    )

    # Operational safety limits
    request_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Default HTTP request timeout.",
    )
    max_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent in-flight requests.",
    )
    rate_limit_rps: float = Field(
        default=10.0,
        ge=0.1,
        le=100.0,
        description="Requests per second rate limit.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Retry attempts on transient network errors.",
    )
    retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Delay in seconds between retries.",
    )

    # Logging and output paths
    output_dir: str = Field(
        default="reports",
        description="Directory for generated audit reports.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )


settings = AgentBreakerSettings()
