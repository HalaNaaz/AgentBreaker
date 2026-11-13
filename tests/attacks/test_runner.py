"""Tests for AttackRunner concurrency, callbacks, and cancellation."""

import pytest
import respx

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import AttackExecutionError
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import AttackCategory
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def mock_attacks() -> list[BaseAttack]:
    attacks = []
    for i in range(5):
        p = AttackPayload(
            id=f"JB-00{i}",
            name=f"Jailbreak Test {i}",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01: Prompt Injection",
            description=f"Description {i}",
            payload_template=f"Prompt {i}",
        )
        attacks.append(BaseAttack(p))
    return attacks


@pytest.mark.asyncio
@respx.mock
async def test_attack_runner_suite_execution(mock_attacks: list[BaseAttack]):
    """Verify batch suite execution with concurrency and progress callback."""
    respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": "Response"}}]},
    )

    progress_events = []

    def on_progress(rec, current, total):
        progress_events.append((current, total))

    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1", model_name="m", max_concurrency=3
    )
    connector = OpenAICompatibleConnector(config)

    runner = AttackRunner(connector=connector, max_concurrency=2, progress_callback=on_progress)

    async with connector:
        results = await runner.run_suite(mock_attacks)
        assert len(results) == 5
        assert all(r.is_success for r in results)
        assert len(progress_events) == 5
        assert progress_events[-1] == (5, 5)


@pytest.mark.asyncio
async def test_attack_runner_cancellation(mock_attacks: list[BaseAttack]):
    """Verify cancelling runner raises AttackExecutionError on subsequent execution."""
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    runner.cancel()
    with pytest.raises(AttackExecutionError, match="cancelled"):
        await runner.run_single(mock_attacks[0])


@pytest.mark.asyncio
async def test_attack_runner_empty_suite():
    """Verify empty attack list returns empty results immediately."""
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)
    results = await runner.run_suite([])
    assert results == []
