"""Integration tests for MutationEngine with AttackRunner."""

import pytest
import respx

from agentbreaker.attacks.base import BaseAttack
from agentbreaker.attacks.exceptions import AttackExecutionError
from agentbreaker.attacks.runner import AttackRunner
from agentbreaker.connectors.openai_compatible import OpenAICompatibleConnector
from agentbreaker.mutators.engine import MutationEngine
from agentbreaker.schemas.enums import AttackCategory
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def target_config() -> TargetConfig:
    return TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="mock-model",
    )


@pytest.fixture
def test_attack() -> BaseAttack:
    payload = AttackPayload(
        id="RUN-TEST-001",
        name="Runner Integration Attack",
        category=AttackCategory.DIRECT_JAILBREAK,
        owasp_id="LLM01: Prompt Injection",
        description="Verify runner integration and default behavior",
        payload_template="Base original prompt text.",
    )
    return BaseAttack(payload)


@pytest.mark.asyncio
@respx.mock
async def test_runner_uses_original_payload_by_default(
    target_config: TargetConfig, test_attack: BaseAttack
):
    """Verify that AttackRunner runs original payloads by default without applying mutations."""
    route = respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": "Defended."}}]},
    )

    async with OpenAICompatibleConnector(target_config) as connector:
        runner = AttackRunner(connector=connector)
        assert runner.enable_mutation is False
        assert runner.mutation_engine is None

        results = await runner.run_suite([test_attack])

        assert len(results) == 1
        assert results[0].payload_id == test_attack.payload.id
        assert results[0].prompt_sent == test_attack.payload.payload_template

        # Verify sent HTTP request body used the original template
        last_body = route.calls.last.request.read().decode("utf-8")
        assert "Base original prompt text." in last_body


def test_runner_mutation_disabled_by_default_raises(
    target_config: TargetConfig, test_attack: BaseAttack
):
    """Verify calling generate_mutations raises error when mutation is disabled."""
    connector = OpenAICompatibleConnector(target_config)
    runner = AttackRunner(connector=connector)

    with pytest.raises(AttackExecutionError, match="Payload mutation is disabled"):
        runner.generate_mutations([test_attack])


def test_runner_explicit_mutation_generation_without_dispatch(
    target_config: TargetConfig, test_attack: BaseAttack
):
    """Verify generate_mutations generates variants locally without dispatching network calls."""
    connector = OpenAICompatibleConnector(target_config)
    runner = AttackRunner(connector=connector, enable_mutation=True)

    # Calling generate_mutations should NOT produce any network activity
    mutated_attacks = runner.generate_mutations(
        [test_attack],
        strategies=["base64", "rot13"],
        max_variants_per_payload=2,
    )

    assert len(mutated_attacks) == 2
    assert all(isinstance(a, BaseAttack) for a in mutated_attacks)
    assert mutated_attacks[0].payload.parent_id == test_attack.payload.id
    assert mutated_attacks[0].payload.mutation_strategy == "base64"
    assert mutated_attacks[1].payload.mutation_strategy == "rot13"


@pytest.mark.asyncio
@respx.mock
async def test_runner_can_explicitly_execute_mutated_attacks(
    target_config: TargetConfig, test_attack: BaseAttack
):
    """Verify that explicitly passed mutated attacks execute through the runner."""
    route = respx.post("http://localhost:8000/v1/chat/completions").respond(
        200,
        json={"choices": [{"message": {"role": "assistant", "content": "Defended."}}]},
    )

    async with OpenAICompatibleConnector(target_config) as connector:
        runner = AttackRunner(connector=connector, enable_mutation=True)
        mutated_attacks = runner.generate_mutations(
            [test_attack],
            strategies=["rot13"],
            max_variants_per_payload=1,
        )

        results = await runner.run_suite(mutated_attacks)

        assert len(results) == 1
        assert results[0].payload_id == mutated_attacks[0].payload.id
        assert results[0].prompt_sent == mutated_attacks[0].payload.payload_template
        assert route.call_count == 1


def test_custom_mutation_engine_passed_to_runner(
    target_config: TargetConfig, test_attack: BaseAttack
):
    """Verify a custom MutationEngine instance can be provided to AttackRunner."""
    custom_engine = MutationEngine(max_variants_per_payload=1)
    connector = OpenAICompatibleConnector(target_config)
    runner = AttackRunner(connector=connector, mutation_engine=custom_engine)

    mutated = runner.generate_mutations([test_attack], strategies=["base64"])
    assert len(mutated) == 1
    assert mutated[0].payload.mutation_strategy == "base64"
