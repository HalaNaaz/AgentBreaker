"""Tests for OllamaConnector."""

import pytest
import respx

from agentbreaker.connectors.ollama import OllamaConnector
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_ollama_successful_chat():
    """Verify Ollama /api/chat payload and response normalization."""
    mock_response = {
        "model": "llama3.2",
        "created_at": "2026-11-10T00:00:00Z",
        "message": {"role": "assistant", "content": "I am llama model."},
        "done": True,
        "total_duration": 500000000,
        "prompt_eval_count": 15,
        "eval_count": 10,
    }
    respx.post("http://localhost:11434/api/chat").respond(200, json=mock_response)

    config = TargetConfig(endpoint_url="http://localhost:11434", model_name="llama3.2")
    async with OllamaConnector(config) as connector:
        resp = await connector.send_prompt("Hello Ollama")
        assert resp.status_code == 200
        assert resp.raw_content == "I am llama model."
        assert resp.metadata["total_duration"] == 500000000
        assert resp.metadata["eval_count"] == 10


@pytest.mark.asyncio
@respx.mock
async def test_ollama_health_check():
    """Verify Ollama health check queries /api/version."""
    respx.get("http://localhost:11434/api/version").respond(200, json={"version": "0.3.14"})
    config = TargetConfig(endpoint_url="http://localhost:11434", model_name="llama3.2")
    async with OllamaConnector(config) as connector:
        assert await connector.health_check() is True
