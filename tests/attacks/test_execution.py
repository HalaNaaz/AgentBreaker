"""Tests for BaseAttack and AttackExecution data structures."""

import pytest
import respx

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.execution import AttackExecution
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


def test_attack_execution_model():
    """Verify AttackExecution properties and timestamp generation."""
    rec = AttackExecution(
        payload_id="EXT-001",
        prompt_sent="System extraction prompt",
        latency_ms=120.5,
        is_success=True,
    )
    assert rec.payload_id == "EXT-001"
    assert rec.latency_ms == 120.5
    assert rec.timestamp_utc is not None
    assert rec.error is None


@pytest.mark.asyncio
@respx.mock
async def test_base_attack_execute_success():
    """Verify BaseAttack execution with a real mock connector."""
    mock_resp = {
        "choices": [{"message": {"role": "assistant", "content": "Defended refusal."}}],
    }
    respx.post("http://localhost:8000/v1/chat/completions").respond(200, json=mock_resp)

    payload = AttackPayload(
        id="JB-010",
        name="Test Jailbreak",
        category=AttackCategory.DIRECT_JAILBREAK,
        owasp_id="LLM01: Prompt Injection",
        severity=Severity.HIGH,
        description="Testing BaseAttack execution",
        payload_template="Test jailbreak prompt: {token}",
    )
    attack = BaseAttack(payload)
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")

    async with OpenAICompatibleConnector(config) as connector:
        result = await attack.execute(connector, token="SECRET_CANARY")
        assert result.is_success is True
        assert result.response is not None
        assert result.response.raw_content == "Defended refusal."
        assert "SECRET_CANARY" in result.prompt_sent
