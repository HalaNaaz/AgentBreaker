"""Unit tests for the MutatorRegistry."""

import pytest

from agentbreaker.mutators.base import BaseMutator
from agentbreaker.mutators.exceptions import UnsupportedStrategyError
from agentbreaker.mutators.registry import MutatorRegistry
from agentbreaker.mutators.strategies.base64 import Base64Mutator
from agentbreaker.mutators.strategies.rot13 import Rot13Mutator


class DummyMutator(BaseMutator):
    name = "dummy"
    description = "Dummy test mutator"

    def mutate_text(self, text: str, **kwargs) -> str:
        return text.upper()


def test_registry_registration_and_lookup():
    """Verify mutators can be registered and retrieved by name."""
    reg = MutatorRegistry()
    dummy = DummyMutator()
    reg.register(dummy)

    assert reg.get("dummy") is dummy
    assert reg.get("DUMMY") is dummy  # case-insensitive
    assert "dummy" in reg.list_strategies()


def test_registry_duplicate_registration_rejected():
    """Verify registering a duplicate strategy name raises ValueError."""
    reg = MutatorRegistry()
    reg.register(DummyMutator())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(DummyMutator())


def test_registry_invalid_type_rejected():
    """Verify registering non-BaseMutator raises TypeError."""
    reg = MutatorRegistry()
    with pytest.raises(TypeError, match="Expected BaseMutator"):
        reg.register("not_a_mutator")  # type: ignore


def test_registry_unknown_strategy_raises():
    """Verify getting an unknown strategy raises UnsupportedStrategyError."""
    reg = MutatorRegistry()
    with pytest.raises(UnsupportedStrategyError, match="not recognized"):
        reg.get("nonexistent_strategy")


def test_registry_enable_and_disable():
    """Verify strategies can be enabled and disabled."""
    reg = MutatorRegistry()
    dummy = DummyMutator()
    reg.register(dummy)

    assert "dummy" in reg.list_strategies()
    reg.disable("dummy")
    assert "dummy" not in reg.list_strategies()
    assert "dummy" in reg.list_strategies(include_disabled=True)

    with pytest.raises(UnsupportedStrategyError, match="currently disabled"):
        reg.get("dummy")

    reg.enable("dummy")
    assert reg.get("dummy") is dummy


def test_registry_disable_unknown_raises():
    """Verify disabling unknown strategy raises UnsupportedStrategyError."""
    reg = MutatorRegistry()
    with pytest.raises(UnsupportedStrategyError, match="unknown strategy"):
        reg.disable("unknown")


def test_default_registry_contents():
    """Verify get_default_registry includes the four standard strategies."""
    reg = MutatorRegistry.get_default_registry()
    strategies = reg.list_strategies()

    assert "base64" in strategies
    assert "rot13" in strategies
    assert "leetspeak" in strategies
    assert "markdown_obfuscation" in strategies

    assert isinstance(reg.get("base64"), Base64Mutator)
    assert isinstance(reg.get("rot13"), Rot13Mutator)
