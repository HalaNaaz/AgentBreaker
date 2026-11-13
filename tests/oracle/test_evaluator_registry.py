"""Unit tests for EvaluatorRegistry."""

import pytest

from agentbreaker.oracle.base import BaseEvaluator, EvaluationInput
from agentbreaker.oracle.evidence import EvidenceItem
from agentbreaker.oracle.exceptions import EvaluatorError
from agentbreaker.oracle.registry import EvaluatorRegistry


class DummyEvaluator(BaseEvaluator):
    name = "dummy"
    description = "Dummy test evaluator"

    def evaluate(self, input_data: EvaluationInput) -> list[EvidenceItem]:
        return []


def test_registry_register_and_lookup():
    """Verify registration and case-insensitive retrieval of evaluators."""
    reg = EvaluatorRegistry()
    dummy = DummyEvaluator()
    reg.register(dummy)

    assert reg.get("dummy") is dummy
    assert reg.get("DUMMY") is dummy
    assert "dummy" in reg.list_evaluators()


def test_registry_duplicate_rejection():
    """Verify duplicate registration raises ValueError."""
    reg = EvaluatorRegistry()
    reg.register(DummyEvaluator())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(DummyEvaluator())


def test_registry_invalid_type_rejection():
    """Verify non-BaseEvaluator registration raises TypeError."""
    reg = EvaluatorRegistry()
    with pytest.raises(TypeError, match="Expected BaseEvaluator"):
        reg.register("not_an_evaluator")  # type: ignore


def test_registry_unknown_evaluator_raises():
    """Verify requesting unregistered evaluator raises EvaluatorError."""
    reg = EvaluatorRegistry()
    with pytest.raises(EvaluatorError, match="not registered"):
        reg.get("nonexistent")


def test_registry_enable_and_disable():
    """Verify evaluators can be enabled and disabled."""
    reg = EvaluatorRegistry()
    dummy = DummyEvaluator()
    reg.register(dummy)

    assert "dummy" in reg.list_evaluators()
    reg.disable("dummy")
    assert "dummy" not in reg.list_evaluators()
    assert "dummy" in reg.list_evaluators(include_disabled=True)

    reg.enable("dummy")
    assert "dummy" in reg.list_evaluators()


def test_registry_default_contents():
    """Verify get_default_registry includes the 4 standard evaluators."""
    reg = EvaluatorRegistry.get_default_registry()
    evaluators = reg.list_evaluators()

    assert "regex" in evaluators
    assert "canary" in evaluators
    assert "refusal" in evaluators
    assert "content_analysis" in evaluators
