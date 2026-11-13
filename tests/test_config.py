"""Tests for application configuration and environment settings."""

import os
from unittest import mock

from pydantic import SecretStr

from agentbreaker.core.config import AgentBreakerSettings


def test_default_settings() -> None:
    """Verify default setting boundaries and safety values."""
    cfg = AgentBreakerSettings()
    assert cfg.request_timeout_seconds >= 1.0
    assert cfg.max_concurrency >= 1
    assert cfg.rate_limit_rps >= 0.1
    assert cfg.max_retries <= 5
    assert cfg.target_type == "openai_compatible"


def test_environment_override() -> None:
    """Verify environment variables with AGENTBREAKER_ prefix override defaults."""
    env_vars = {
        "AGENTBREAKER_TARGET_URL": "http://127.0.0.1:11434/v1",
        "AGENTBREAKER_TARGET_MODEL": "llama3.2",
        "AGENTBREAKER_MAX_CONCURRENCY": "12",
        "AGENTBREAKER_API_KEY": "env-secret-token",
    }
    with mock.patch.dict(os.environ, env_vars, clear=False):
        cfg = AgentBreakerSettings()
        assert cfg.target_url == "http://127.0.0.1:11434/v1"
        assert cfg.target_model == "llama3.2"
        assert cfg.max_concurrency == 12
        assert isinstance(cfg.api_key, SecretStr)
        assert cfg.api_key.get_secret_value() == "env-secret-token"
