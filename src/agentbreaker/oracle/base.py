"""Base abstraction and contract for evaluation oracle rule modules."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.oracle.evidence import EvidenceItem
from agentbreaker.schemas.payload import AttackPayload
from agentbreaker.schemas.target import TargetResponse


class EvaluationInput(BaseModel):
    """Encapsulates all relevant data necessary for evaluating an adversarial trial."""

    model_config = ConfigDict(extra="forbid")

    payload: AttackPayload = Field(
        ...,
        description="The executed adversarial attack payload (original or mutated variant).",
    )
    response: TargetResponse = Field(
        ...,
        description="Observed target response produced by the model or agent under test.",
    )
    canary_token: str | None = Field(
        default=None,
        description="Active canary token associated with this trial if tracking leaks.",
    )
    target_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context regarding the target runtime or connector.",
    )
    max_scan_bytes: int = Field(
        default=65_536,
        description="Maximum characters of raw response to scan to prevent resource exhaustion.",
    )


class BaseEvaluator(ABC):
    """Abstract base class defining the contract for an individual evaluation rule."""

    name: str = "base_evaluator"
    description: str = "Base evaluator interface"

    def __init__(self, is_enabled: bool = True) -> None:
        self.is_enabled = is_enabled

    @abstractmethod
    def evaluate(self, input_data: EvaluationInput) -> list[EvidenceItem]:
        """Analyze evaluation input and produce structured evidence items.

        Must be a side-effect-free, local analysis. No network operations,
        subprocess execution, or tool commands may be executed.
        """
        ...
