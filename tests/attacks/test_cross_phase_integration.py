"""Cross-phase integration verification between Phase 2 and Phase 3."""

import asyncio
from pathlib import Path

import httpx
import pytest
import respx
from pydantic import SecretStr, ValidationError

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import (
    AttackExecutionError,
    TargetNotAuthorizedError,
)
from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.attacks.registry import AttackRegistry
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.exceptions import SecurityBoundaryError
from agentbreaker.connectors.factory import get_connector
from agentbreaker.connectors.ollama import OllamaConnector
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


@pytest.mark.asyncio
@respx.mock
async def test_integration_runner_with_openai_compatible():
    """1. AttackRunner -> OpenAICompatibleConnector dispatch."""
    respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={
            "choices": [{"message": {"role": "assistant", "content": "I refuse this jailbreak."}}]
        },
    )
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="test-model")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    payload = AttackPayload(
        id="INT-001",
        name="Integration Jailbreak",
        category="direct_jailbreak",  # type: ignore
        owasp_id="LLM01",
        description="Testing integration",
        payload_template="Test jailbreak",
    )
    attack = BaseAttack(payload)

    async with connector:
        execution = await runner.run_single(attack)
        assert execution.is_success is True
        assert execution.response is not None
        assert execution.response.raw_content == "I refuse this jailbreak."


@pytest.mark.asyncio
@respx.mock
async def test_integration_runner_with_mocked_ollama():
    """2. AttackRunner -> mocked Ollama connector dispatch."""
    respx.post("http://localhost:11434/api/chat").respond(
        200,
        json={"message": {"role": "assistant", "content": "Ollama response text"}, "done": True},
    )
    config = TargetConfig(
        endpoint_url="http://localhost:11434",
        target_type=TargetType.OLLAMA,
        model_name="llama3.2",
    )
    connector = get_connector(config)
    assert isinstance(connector, OllamaConnector)
    runner = AttackRunner(connector=connector)

    payload = AttackPayload(
        id="INT-002",
        name="Ollama Extraction",
        category="system_extraction",  # type: ignore
        owasp_id="LLM07",
        description="Testing Ollama integration",
        payload_template="Exfiltrate prompt",
    )
    attack = BaseAttack(payload)

    async with connector:
        execution = await runner.run_single(attack)
        assert execution.is_success is True
        assert execution.response.raw_content == "Ollama response text"


@pytest.mark.asyncio
@respx.mock
async def test_integration_pipeline_loading_registry_runner():
    """3. End-to-end pipeline: Directory load -> Registry -> Runner."""
    registry = AttackRegistry()
    count = PayloadLoader.load_into_registry(Path("payloads"), registry)
    assert count >= 50

    respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": "Defended"}}]},
    )
    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1", model_name="m", max_concurrency=4
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=4)

    attacks = registry.list_all()[:5]
    async with connector:
        results = await runner.run_suite(attacks)
        assert len(results) == 5
        assert all(r.is_success for r in results)


@pytest.mark.asyncio
@respx.mock
async def test_integration_response_and_metadata_propagation():
    """4. Successful response and metadata propagation into execution records."""
    respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": "Observed output"}}]},
    )
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    payload = AttackPayload(
        id="INT-004",
        name="Meta Test",
        category="indirect_injection",  # type: ignore
        owasp_id="LLM01",
        severity="HIGH",  # type: ignore
        description="Testing metadata propagation",
        payload_template="Meta prompt",
    )
    attack = BaseAttack(payload)

    async with connector:
        rec = await runner.run_single(attack)
        assert rec.payload_id == "INT-004"
        assert rec.metadata["category"] == "indirect_injection"
        assert rec.metadata["severity"] == "HIGH"
        assert rec.latency_ms > 0.0


@pytest.mark.asyncio
@respx.mock
async def test_integration_connector_failure_propagation():
    """5. Connector failure propagation into execution record without crashing."""
    respx.post("http://localhost:8000/v1/chat/completions").respond(503)
    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="m",
        max_retries=0,
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    attack = BaseAttack(
        AttackPayload(
            id="INT-005",
            name="Error Test",
            category="direct_jailbreak",  # type: ignore
            owasp_id="LLM01",
            description="Testing error propagation",
            payload_template="Test",
        )
    )

    async with connector:
        rec = await runner.run_single(attack)
        assert rec.is_success is False
        assert rec.error is not None
        assert "503" in rec.error


@pytest.mark.asyncio
@respx.mock
async def test_integration_timeout_handling():
    """6. Timeout handling across runner and connector."""
    respx.post("http://localhost:8000/v1/chat/completions").mock(
        side_effect=httpx.ReadTimeout("Timeout connecting to target")
    )
    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="m",
        timeout_seconds=1.0,
        max_retries=0,
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    attack = BaseAttack(
        AttackPayload(
            id="INT-006",
            name="Timeout Test",
            category="direct_jailbreak",  # type: ignore
            owasp_id="LLM01",
            description="Testing timeout handling",
            payload_template="Test",
        )
    )

    async with connector:
        rec = await runner.run_single(attack)
        assert rec.is_success is False
        assert "timed out" in rec.error.lower()


@pytest.mark.asyncio
async def test_integration_cancellation_handling():
    """7. Cancellation handling in attack runner."""
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    attack = BaseAttack(
        AttackPayload(
            id="INT-007",
            name="Cancel Test",
            category="direct_jailbreak",  # type: ignore
            owasp_id="LLM01",
            description="Testing cancellation",
            payload_template="Test",
        )
    )
    runner.cancel()
    with pytest.raises(AttackExecutionError, match="cancelled"):
        await runner.run_single(attack)


@pytest.mark.asyncio
async def test_integration_target_authorization_before_dispatch():
    """8. Target authorization check before network dispatch."""
    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    connector.config.endpoint_url = ""
    attack = BaseAttack(
        AttackPayload(
            id="INT-008",
            name="Auth Test",
            category="direct_jailbreak",  # type: ignore
            owasp_id="LLM01",
            description="Testing auth guard",
            payload_template="Test",
        )
    )
    with pytest.raises(TargetNotAuthorizedError, match="not configured"):
        await runner.run_suite([attack])


@pytest.mark.asyncio
@respx.mock
async def test_integration_tool_call_capture_without_execution():
    """9. Tool-call capture without executing target tools."""
    mock_resp = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {"name": "run_shell", "arguments": '{"cmd":"ls"}'},
                        }
                    ],
                }
            }
        ]
    }
    respx.post("http://localhost:8000/v1/chat/completions").respond(200, json=mock_resp)

    config = TargetConfig(endpoint_url="http://localhost:8000/v1", model_name="m")
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector)

    attack = BaseAttack(
        AttackPayload(
            id="INT-009",
            name="Tool Capture Test",
            category="tool_hijacking",  # type: ignore
            owasp_id="LLM08",
            description="Testing tool capture",
            payload_template="Run ls",
        )
    )

    async with connector:
        rec = await runner.run_single(attack)
        assert rec.is_success is True
        assert len(rec.response.tool_calls) == 1
        assert rec.response.tool_calls[0]["function"]["name"] == "run_shell"


@pytest.mark.asyncio
@respx.mock
async def test_integration_secret_redaction_in_exceptions_and_results():
    """10. Secret redaction in configuration, dump, and error states."""
    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="m",
        api_key=SecretStr("super-confidential-token-999"),
        custom_headers={"X-Auth-Token": "secret-auth-value"},
    )
    safe = config.safe_dump()
    assert safe["api_key"] == "********"
    assert safe["custom_headers"]["X-Auth-Token"] == "********"

    dump_json = config.model_dump_json()
    assert "super-confidential-token-999" not in dump_json
    assert "secret-auth-value" not in dump_json


@pytest.mark.asyncio
@respx.mock
async def test_integration_resource_limits_concurrency():
    """11. Resource limits under concurrent execution."""
    active = 0
    max_active = 0

    async def sleep_handler(req):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.02)
        active -= 1
        return httpx.Response(
            200, json={"choices": [{"message": {"role": "assistant", "content": "Ok"}}]}
        )

    respx.post("http://localhost:8000/v1/chat/completions").mock(side_effect=sleep_handler)

    config = TargetConfig(
        endpoint_url="http://localhost:8000/v1", model_name="m", max_concurrency=2
    )
    connector = OpenAICompatibleConnector(config)
    runner = AttackRunner(connector=connector, max_concurrency=2)

    attacks = [
        BaseAttack(
            AttackPayload(
                id=f"INT-C{i}",
                name=f"Concurrent {i}",
                category="direct_jailbreak",  # type: ignore
                owasp_id="LLM01",
                description="Testing concurrency",
                payload_template=f"Test {i}",
            )
        )
        for i in range(4)
    ]

    async with connector:
        results = await runner.run_suite(attacks)
        assert len(results) == 4
        assert max_active <= 2


@pytest.mark.asyncio
async def test_integration_invalid_target_boundary_rejection():
    """12. Invalid target boundary rejection prior to dispatch."""
    with pytest.raises(ValidationError, match="authorized target boundaries"):
        TargetConfig(
            endpoint_url="http://localhost:8000/v1",
            model_name="m",
            allowed_hosts=["allowed-domain.org"],
        )

    valid_config = TargetConfig(
        endpoint_url="http://allowed-domain.org/v1",
        model_name="m",
        allowed_hosts=["allowed-domain.org"],
    )
    connector = OpenAICompatibleConnector(valid_config)
    with pytest.raises(SecurityBoundaryError, match="authorized target boundaries"):
        connector._validate_target_security("http://unauthorized-domain.com/v1")
