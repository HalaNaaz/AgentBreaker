"""Tests for Cloud LLM connectors (OpenAI, Anthropic, Gemini)."""

import pytest
import respx
from pydantic import SecretStr

from agentbreaker.connectors.cloud import (
    AnthropicCloudConnector,
    GeminiCloudConnector,
    OpenAICloudConnector,
)
from agentbreaker.connectors.exceptions import AuthenticationError
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_openai_cloud_connector_success():
    """Verify OpenAI cloud connector payload and response."""
    mock_resp = {
        "id": "chatcmpl-oai",
        "model": "gpt-4o",
        "choices": [{"message": {"role": "assistant", "content": "OpenAI answer"}}],
    }
    respx.post("https://api.openai.com/v1/chat/completions").respond(200, json=mock_resp)

    config = TargetConfig(
        endpoint_url="https://api.openai.com/v1",
        target_type=TargetType.OPENAI,
        model_name="gpt-4o",
        api_key=SecretStr("sk-openai-test-key"),
        allowed_hosts=["api.openai.com"],
    )
    async with OpenAICloudConnector(config) as conn:
        resp = await conn.send_prompt("Hello cloud")
        assert resp.raw_content == "OpenAI answer"
        assert resp.status_code == 200


@pytest.mark.asyncio
@respx.mock
async def test_anthropic_cloud_connector_success():
    """Verify Anthropic connector custom headers and text extraction."""
    mock_resp = {
        "id": "msg_123",
        "type": "message",
        "content": [
            {"type": "text", "text": "Anthropic response"},
            {
                "type": "tool_use",
                "id": "toolu_01",
                "name": "search_db",
                "input": {"query": "credentials"},
            },
        ],
    }
    route = respx.post("https://api.anthropic.com/v1/messages").respond(200, json=mock_resp)

    config = TargetConfig(
        endpoint_url="https://api.anthropic.com",
        target_type=TargetType.ANTHROPIC,
        model_name="claude-3-5-sonnet-20241022",
        api_key=SecretStr("sk-ant-test-key"),
        allowed_hosts=["api.anthropic.com"],
    )
    async with AnthropicCloudConnector(config) as conn:
        resp = await conn.send_prompt("Hello Claude")
        assert resp.raw_content == "Anthropic response"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["name"] == "search_db"

    # Verify Anthropic headers were sent
    last_req = route.calls.last.request
    assert last_req.headers["x-api-key"] == "sk-ant-test-key"
    assert last_req.headers["anthropic-version"] == "2023-06-01"


@pytest.mark.asyncio
@respx.mock
async def test_gemini_cloud_connector_success():
    """Verify Gemini connector headers and candidates extraction."""
    mock_resp = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Gemini response text"},
                        {"functionCall": {"name": "query_api", "args": {"id": 1}}},
                    ]
                }
            }
        ]
    }
    route = respx.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    ).respond(200, json=mock_resp)

    config = TargetConfig(
        endpoint_url="https://generativelanguage.googleapis.com",
        target_type=TargetType.GEMINI,
        model_name="gemini-1.5-pro",
        api_key=SecretStr("AIzaSy-test-key"),
        allowed_hosts=["generativelanguage.googleapis.com"],
    )
    async with GeminiCloudConnector(config) as conn:
        resp = await conn.send_prompt("Hello Gemini")
        assert resp.raw_content == "Gemini response text"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["name"] == "query_api"

    last_req = route.calls.last.request
    assert last_req.headers["x-goog-api-key"] == "AIzaSy-test-key"


@pytest.mark.asyncio
async def test_cloud_connector_missing_api_key():
    """Verify cloud connectors raise AuthenticationError when API key is missing."""
    config = TargetConfig(
        endpoint_url="https://api.openai.com/v1",
        target_type=TargetType.OPENAI,
        model_name="gpt-4o",
        api_key=None,
        allowed_hosts=["api.openai.com"],
    )
    conn = OpenAICloudConnector(config)
    with pytest.raises(AuthenticationError, match="requires an API key"):
        await conn.send_prompt("Hello")
