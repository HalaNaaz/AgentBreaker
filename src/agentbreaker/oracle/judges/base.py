"""Base abstraction for LLM-as-a-Judge evaluators."""

from abc import ABC, abstractmethod

from agentbreaker.oracle.base import EvaluationInput
from agentbreaker.oracle.evidence import EvidenceItem


class BaseJudge(ABC):
    """Abstract base class for optional LLM-as-a-Judge evaluation heuristics."""

    def __init__(self, is_enabled: bool = False, judge_model_name: str = "judge-model") -> None:
        self.is_enabled = is_enabled
        self.judge_model_name = judge_model_name

    @abstractmethod
    async def evaluate_trial(self, input_data: EvaluationInput) -> EvidenceItem | None:
        """Evaluate an adversarial trial using judge model inference."""
        ...
