"""Tests for OpenAICompatibleConnector (vLLM / OpenAI standard endpoints)."""

import pytest
import respx

from agentbreaker.connectors.exceptions import InvalidResponseError
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_successful_prompt():
    """Verify chat completions formatting and response normalization."""
    mock_response = {
        "id": "chatcmpl-123",
        "model": "mistral-7b-instruct",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "I am a helpful assistant."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
    }
    respx.post("http://localhost:8000/v1/chat/completions").respond(200, json=mock_response)

    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="mistral-7b-instruct",
    )
    connector = OpenAICompatibleConnector(config)

    async with connector:
        resp = await connector.send_prompt("Hello")
        assert resp.status_code == 200
        assert resp.raw_content == "I am a helpful assistant."
        assert resp.metadata["finish_reason"] == "stop"
        assert resp.metadata["usage"]["total_tokens"] == 18
        assert resp.tool_calls == []


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_tool_calls_extracted_safely():
    """Verify model-generated tool calls are extracted without executing them."""
    mock_response = {
        "id": "chatcmpl-tool",
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {"name": "run_shell", "arguments": '{"cmd": "whoami"}'},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
    }
    respx.post("http://localhost:8000/v1/chat/completions").respond(200, json=mock_response)

    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="gpt-4o")
    async with OpenAICompatibleConnector(config) as connector:
        resp = await connector.send_prompt("Run whoami")
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["function"]["name"] == "run_shell"


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_missing_choices():
    """Verify invalid API response without choices raises InvalidResponseError."""
    respx.post("http://localhost:8000/v1/chat/completions").respond(
        200, json={"error": "no choices"}
    )
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    async with OpenAICompatibleConnector(config) as connector:
        with pytest.raises(InvalidResponseError, match="missing valid 'choices'"):
            await connector.send_prompt("Test")


@pytest.mark.asyncio
@respx.mock
async def test_openai_compatible_health_check():
    """Verify health check verifies endpoint via /models."""
    respx.get("http://localhost:8000/v1/models").respond(200, json={"data": []})
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    async with OpenAICompatibleConnector(config) as connector:
        assert await connector.health_check() is True
