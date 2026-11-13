"""Registry managing Evaluation Oracle rule modules."""

from agentbreaker.oracle.base import BaseEvaluator
from agentbreaker.oracle.exceptions import EvaluatorError
from agentbreaker.oracle.rules.canary import CanaryEvaluator
from agentbreaker.oracle.rules.content_analysis import ContentAnalysisEvaluator
from agentbreaker.oracle.rules.refusal import RefusalEvaluator
from agentbreaker.oracle.rules.regex import RegexEvaluator


class EvaluatorRegistry:
    """Thread-safe registry of active evaluation rule modules."""

    def __init__(self) -> None:
        self._evaluators: dict[str, BaseEvaluator] = {}

    def register(self, evaluator: BaseEvaluator) -> None:
        """Register an evaluator instance."""
        if not isinstance(evaluator, BaseEvaluator):
            raise TypeError(f"Expected BaseEvaluator, got {type(evaluator).__name__}")
        name = evaluator.name.lower().strip()
        if not name:
            raise ValueError("Evaluator name cannot be empty.")
        if name in self._evaluators:
            raise ValueError(f"Evaluator '{name}' is already registered.")
        self._evaluators[name] = evaluator

    def get(self, name: str) -> BaseEvaluator:
        """Retrieve an evaluator by name."""
        clean_name = name.lower().strip()
        if clean_name not in self._evaluators:
            available = list(self._evaluators.keys())
            raise EvaluatorError(
                f"Evaluator '{name}' is not registered. Available evaluators: {available}"
            )
        return self._evaluators[clean_name]

    def enable(self, name: str) -> None:
        """Enable an evaluator."""
        clean_name = name.lower().strip()
        if clean_name not in self._evaluators:
            raise EvaluatorError(f"Cannot enable unknown evaluator '{name}'.")
        self._evaluators[clean_name].is_enabled = True

    def disable(self, name: str) -> None:
        """Disable an evaluator without removing it."""
        clean_name = name.lower().strip()
        if clean_name not in self._evaluators:
            raise EvaluatorError(f"Cannot disable unknown evaluator '{name}'.")
        self._evaluators[clean_name].is_enabled = False

    def list_evaluators(self, include_disabled: bool = False) -> list[str]:
        """List registered evaluator names."""
        if include_disabled:
            return list(self._evaluators.keys())
        return [name for name, ev in self._evaluators.items() if ev.is_enabled]

    def get_all(self, include_disabled: bool = False) -> list[BaseEvaluator]:
        """Return list of evaluator instances."""
        if include_disabled:
            return list(self._evaluators.values())
        return [ev for ev in self._evaluators.values() if ev.is_enabled]

    @classmethod
    def get_default_registry(cls) -> "EvaluatorRegistry":
        """Instantiate a registry with the 4 standard rule evaluators."""
        reg = cls()
        reg.register(RegexEvaluator())
        reg.register(CanaryEvaluator())
        reg.register(RefusalEvaluator())
        reg.register(ContentAnalysisEvaluator())
        return reg
