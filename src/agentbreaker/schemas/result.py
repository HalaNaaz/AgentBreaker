"""Evaluation finding and verdict result schema."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict


class EvaluationResult(BaseModel):
    """The security assessment finding produced after evaluating a target response."""

    model_config = ConfigDict(extra="forbid")

    payload_id: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Identifier of the attack payload tested.",
    )
    category: AttackCategory = Field(
        ...,
        description="Category classification of the tested attack.",
    )
    verdict: Verdict = Field(
        ...,
        description="Determined security verdict (VULNERABLE, DEFENDED, or INCONCLUSIVE).",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Evaluation confidence score between 0.0 and 1.0.",
    )
    severity: Severity = Field(
        default=Severity.MEDIUM,
        description="Effective vulnerability severity level.",
    )
    cvss_score: float = Field(
        default=0.0,
        ge=0.0,
        le=10.0,
        description="CVSS score attributed to the finding if vulnerable.",
    )
    owasp_id: str | None = Field(
        default=None,
        description="Mapped OWASP Top 10 for LLM vulnerability code.",
    )
    mitre_atlas_id: str | None = Field(
        default=None,
        description="Mapped MITRE ATLAS technique ID.",
    )
    reasons: list[str] = Field(
        default_factory=list,
        description="Explanatory rationales justifying the verdict.",
    )
    matched_patterns: list[str] = Field(
        default_factory=list,
        description="Regex patterns or canary markers observed in target output.",
    )
    detected_canaries: list[str] = Field(
        default_factory=list,
        description="Canary secret tokens detected as leaked in target output.",
    )
    tool_call_violations: list[str] = Field(
        default_factory=list,
        description="Forbidden tool calls or dangerous function parameters detected.",
    )
    parent_id: str | None = Field(
        default=None,
        max_length=32,
        description="Parent payload identifier if this evaluation tested a mutated variant.",
    )
    evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured evidence items supporting the verdict.",
    )
    target_model: str | None = Field(
        default=None,
        description="The target model evaluated.",
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Target response round-trip latency in milliseconds.",
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of evaluation.",
    )
