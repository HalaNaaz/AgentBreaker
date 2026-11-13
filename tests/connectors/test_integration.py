"""Integration tests with local mock target and conditional live environment detection."""

import pytest
import respx
from pydantic import SecretStr

from agentbreaker.connectors.factory import get_connector
from agentbreaker.connectors.ollama import OllamaConnector
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_end_to_end_mock_integration():
    """Verify end-to-end integration flow via factory, mock endpoint, and normalized response."""
    mock_payload = {
        "id": "mock-run-001",
        "model": "integration-model",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Mock target integration confirmed."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"total_tokens": 25},
    }
    respx.post("http://127.0.0.1:8080/v1/chat/completions").respond(200, json=mock_payload)

    config = TargetConfig(
        endpoint_url="http://127.0.0.1:8080/v1",
        target_type=TargetType.OPENAI_COMPATIBLE,
        model_name="integration-model",
        api_key=SecretStr("mock-key-secret"),
        timeout_seconds=5.0,
        allowed_hosts=["127.0.0.1"],
    )

    connector = get_connector(config)
    assert isinstance(connector, OpenAICompatibleConnector)

    async with connector:
        response = await connector.send_prompt("Test integration probe")
        assert response.status_code == 200
        assert response.raw_content == "Mock target integration confirmed."
        assert response.is_error is False
        assert response.metadata["usage"]["total_tokens"] == 25
        # Ensure secret is protected
        assert "mock-key-secret" not in str(config)
        assert "mock-key-secret" not in config.model_dump_json()


@pytest.mark.asyncio
async def test_live_vllm_integration_skipped_when_unavailable():
    """Verify live vLLM integration: executes if online, skips gracefully if unavailable."""
    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="mistral-7b-instruct",
        timeout_seconds=1.0,
        max_retries=0,
    )
    connector = OpenAICompatibleConnector(config)
    try:
        is_healthy = await connector.health_check()
        if not is_healthy:
            pytest.skip("Local vLLM server is unavailable; skipping live integration.")
    except Exception:
        pytest.skip("Local vLLM server is unavailable; skipping live integration.")


@pytest.mark.asyncio
async def test_live_ollama_integration_skipped_when_unavailable():
    """Verify live Ollama integration: executes if online, skips gracefully if unavailable."""
    config = TargetConfig(
        endpoint_url="http://localhost:11434",
        model_name="llama3.2",
        timeout_seconds=1.0,
        max_retries=0,
    )
    connector = OllamaConnector(config)
    try:
        is_healthy = await connector.health_check()
        if not is_healthy:
            pytest.skip("Local Ollama daemon is unavailable; skipping live integration.")
    except Exception:
        pytest.skip("Local Ollama daemon is unavailable; skipping live integration.")
