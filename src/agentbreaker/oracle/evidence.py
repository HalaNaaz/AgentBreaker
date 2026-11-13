"""Structured evidence data models for Evaluation Oracle findings."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.schemas.enums import Verdict


class EvidenceType(StrEnum):
    """Classification of observed adversarial evaluation evidence."""

    CANARY_DETECTED = "canary_detected"
    FORBIDDEN_TOOL = "forbidden_tool"
    REGEX_VIOLATION = "regex_violation"
    REFUSAL_DETECTED = "refusal_detected"
    POLICY_COMPLIANCE = "policy_compliance"
    SECRET_LEAK = "secret_leak"  # noqa: S105
    LLM_JUDGE_OPINION = "llm_judge_opinion"
    ERROR_RESPONSE = "error_response"
    EMPTY_RESPONSE = "empty_response"


class EvidenceItem(BaseModel):
    """A granular piece of traceable evidence produced by an evaluator."""

    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = Field(
        ...,
        description="Name of the evaluator module that discovered this evidence.",
    )
    evidence_type: EvidenceType = Field(
        ...,
        description="Type category of the discovered indicator.",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of the finding.",
    )
    supports_verdict: Verdict = Field(
        ...,
        description="Verdict option directly supported by this evidence item.",
    )
    confidence_weight: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Weight of this evidence (0.0 to 1.0) indicating signal strength.",
    )
    matched_text: str | None = Field(
        default=None,
        description="Exact substring, pattern, or token that triggered the finding.",
    )
    rule_identifier: str | None = Field(
        default=None,
        description="Specific rule or pattern ID responsible for this evidence.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic telemetry and contextual information.",
    )
