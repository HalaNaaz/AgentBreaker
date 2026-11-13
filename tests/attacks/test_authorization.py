"""Tests verifying target authorization enforcement prior to attack execution."""

import pytest

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import TargetNotAuthorizedError
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import AttackCategory
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def sample_attack() -> BaseAttack:
    p = AttackPayload(
        id="AUTH-001",
        name="Auth Test Attack",
        category=AttackCategory.DIRECT_JAILBREAK,
        owasp_id="LLM01: Prompt Injection",
        description="Testing authorization boundary",
        payload_template="Hello",
    )
    return BaseAttack(p)


@pytest.mark.asyncio
async def test_runner_authorization_check_empty_endpoint(sample_attack: BaseAttack):
    """Verify AttackRunner rejects execution if endpoint is empty."""
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    # Artificially clear endpoint URL to verify guard
    connector.config.endpoint_url = ""
    with pytest.raises(TargetNotAuthorizedError, match="not configured"):
        await runner.run_suite([sample_attack])
