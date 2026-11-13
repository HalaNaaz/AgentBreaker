"""Tests for attack runner resource limits, concurrency throttling, and timeouts."""

import asyncio

import httpx
import pytest
import respx

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import AttackCategory
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_runner_concurrency_bounding():
    """Verify maximum active in-flight requests does not exceed configured semaphore."""
    active_requests = 0
    max_observed_concurrency = 0

    async def mock_handler(request):
        nonlocal active_requests, max_observed_concurrency
        active_requests += 1
        max_observed_concurrency = max(max_observed_concurrency, active_requests)
        await asyncio.sleep(0.05)
        active_requests -= 1
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "Done"}}]},
        )

    respx.post("http://localhost:8000/v1/chat/completions").mock(side_effect=mock_handler)

    attacks = [
        BaseAttack(
            AttackPayload(
                id=f"CONC-{i:03d}",
                name=f"Concurrency Test {i}",
                category=AttackCategory.DIRECT_JAILBREAK,
                owasp_id="LLM01",
                description="Testing bounded concurrency",
                payload_template="Test",
            )
        )
        for i in range(6)
    ]

    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1", model_name="m", max_concurrency=2
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=2)

    async with connector:
        results = await runner.run_suite(attacks)
        assert len(results) == 6
        assert max_observed_concurrency <= 2


@pytest.mark.asyncio
@respx.mock
async def test_runner_individual_timeout_does_not_abort_suite():
    """Verify an individual timeout is recorded as a failure while remaining attacks proceed."""
    respx.post("http://localhost:8000/v1/chat/completions").side_effect = [
        httpx.ReadTimeout("Request timed out"),
        httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "Success"}}]}
        ),
    ]

    p1 = BaseAttack(
        AttackPayload(
            id="FAIL-001",
            name="Timeout Test",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01",
            description="Testing timeout recovery",
            payload_template="Test 1",
        )
    )
    p2 = BaseAttack(
        AttackPayload(
            id="PASS-002",
            name="Success Test",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01",
            description="Testing timeout recovery",
            payload_template="Test 2",
        )
    )

    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="m",
        timeout_seconds=1.0,
        max_retries=0,
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=1)

    async with connector:
        results = await runner.run_suite([p1, p2])
        assert len(results) == 2
        assert results[0].is_success is False
        assert "timed out" in results[0].error.lower()
        assert results[1].is_success is True
        assert results[1].response.raw_content == "Success"
