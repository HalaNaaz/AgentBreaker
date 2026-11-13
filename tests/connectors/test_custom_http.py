"""Tests for CustomHttpConnector."""

import json

import pytest
import respx

from agentbreaker.connectors.custom_http import CustomHttpConnector
from agentbreaker.connectors.exceptions import InvalidResponseError
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_custom_http_with_template_and_path():
    """Verify JSON template substitution and dot-path response extraction."""
    mock_resp = {
        "status": "success",
        "result": {
            "output_text": "Extracted custom response",
            "metadata": {"tokens": 42},
        },
    }
    route = respx.post("http://localhost:9000/api/generate").respond(200, json=mock_resp)

    config = TargetConfig(
        endpoint_url="http://localhost:9000/api/generate",
        target_type=TargetType.CUSTOM_HTTP,
        model_name="custom-agent",
        request_template={"query": "{prompt}", "options": {"temperature": 0.5}},
        response_path="result.output_text",
    )

    async with CustomHttpConnector(config) as conn:
        resp = await conn.send_prompt("Inject test")
        assert resp.raw_content == "Extracted custom response"
        assert resp.status_code == 200

    last_body = route.calls.last.request.read().decode("utf-8")
    parsed_body = json.loads(last_body)
    assert parsed_body["query"] == "Inject test"


@pytest.mark.asyncio
@respx.mock
async def test_custom_http_invalid_path():
    """Verify missing response path raises InvalidResponseError."""
    respx.post("http://localhost:9000/api/generate").respond(200, json={"other": "value"})

    config = TargetConfig(
        endpoint_url="http://localhost:9000/api/generate",
        target_type=TargetType.CUSTOM_HTTP,
        model_name="custom-agent",
        response_path="nonexistent.path",
    )

    async with CustomHttpConnector(config) as conn:
        with pytest.raises(InvalidResponseError, match="not found in JSON response"):
            await conn.send_prompt("Test")


@pytest.mark.asyncio
@respx.mock
async def test_custom_http_fallback_extraction():
    """Verify common key heuristic extraction when no path is specified."""
    respx.post("http://localhost:9000/api/generate").respond(
        200, json={"reply": "Heuristic extracted text"}
    )

    config = TargetConfig(
        endpoint_url="http://localhost:9000/api/generate",
        target_type=TargetType.CUSTOM_HTTP,
        model_name="custom-agent",
    )

    async with CustomHttpConnector(config) as conn:
        resp = await conn.send_prompt("Test")
        assert resp.raw_content == "Heuristic extracted text"
