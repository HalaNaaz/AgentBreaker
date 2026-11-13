"""Registry managing available payload mutation strategies."""

from agentbreaker.mutators.base import BaseMutator
from agentbreaker.mutators.exceptions import UnsupportedStrategyError
from agentbreaker.mutators.strategies.base64 import Base64Mutator
from agentbreaker.mutators.strategies.leetspeak import LeetspeakMutator
from agentbreaker.mutators.strategies.markdown_obfuscation import MarkdownObfuscationMutator
from agentbreaker.mutators.strategies.rot13 import Rot13Mutator


class MutatorRegistry:
    """Thread-safe, in-memory registry of mutation strategies."""

    def __init__(self) -> None:
        self._mutators: dict[str, BaseMutator] = {}

    def register(self, mutator: BaseMutator) -> None:
        """Register a new mutator strategy instance."""
        if not isinstance(mutator, BaseMutator):
            raise TypeError(f"Expected BaseMutator instance, got {type(mutator).__name__}")
        name = mutator.name.lower().strip()
        if not name:
            raise ValueError("Mutator name cannot be empty.")
        if name in self._mutators:
            raise ValueError(f"Mutator strategy '{name}' is already registered.")
        self._mutators[name] = mutator

    def get(self, name: str) -> BaseMutator:
        """Retrieve a registered mutator by name.

        Raises:
            UnsupportedStrategyError: If the strategy is unknown or currently disabled.
        """
        clean_name = name.lower().strip()
        if clean_name not in self._mutators:
            available = list(self._mutators.keys())
            raise UnsupportedStrategyError(
                f"Mutation strategy '{name}' is not recognized. Available strategies: {available}"
            )
        mutator = self._mutators[clean_name]
        if not mutator.is_enabled:
            raise UnsupportedStrategyError(f"Mutation strategy '{name}' is currently disabled.")
        return mutator

    def enable(self, name: str) -> None:
        """Enable a registered mutator strategy."""
        clean_name = name.lower().strip()
        if clean_name not in self._mutators:
            raise UnsupportedStrategyError(f"Cannot enable unknown strategy '{name}'.")
        self._mutators[clean_name].is_enabled = True

    def disable(self, name: str) -> None:
        """Disable a registered mutator strategy without removing it."""
        clean_name = name.lower().strip()
        if clean_name not in self._mutators:
            raise UnsupportedStrategyError(f"Cannot disable unknown strategy '{name}'.")
        self._mutators[clean_name].is_enabled = False

    def list_strategies(self, include_disabled: bool = False) -> list[str]:
        """Return the names of available strategies."""
        if include_disabled:
            return list(self._mutators.keys())
        return [name for name, m in self._mutators.items() if m.is_enabled]

    @classmethod
    def get_default_registry(cls) -> "MutatorRegistry":
        """Instantiate a registry populated with the standard 4 mutation strategies."""
        registry = cls()
        registry.register(Base64Mutator())
        registry.register(Rot13Mutator())
        registry.register(LeetspeakMutator())
        registry.register(MarkdownObfuscationMutator())
        return registry
