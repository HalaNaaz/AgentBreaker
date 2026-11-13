"""Pydantic data models for AgentBreaker research reports and analytics."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict


class ReportFormat(StrEnum):
    """Supported audit report output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class VerdictDistribution(BaseModel):
    """Aggregated evaluation verdict metrics."""

    model_config = ConfigDict(extra="forbid")

    total: int = 0
    vulnerable: int = 0
    defended: int = 0
    inconclusive: int = 0
    error: int = 0

    vulnerable_rate: float = 0.0
    defended_rate: float = 0.0
    inconclusive_rate: float = 0.0


class SeverityDistribution(BaseModel):
    """Aggregated vulnerability severity distribution metrics."""

    model_config = ConfigDict(extra="forbid")

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class CategoryMetric(BaseModel):
    """Metrics for an individual adversarial attack category."""

    model_config = ConfigDict(extra="forbid")

    category: AttackCategory
    name: str
    total_evaluated: int = 0
    vulnerable_count: int = 0
    defended_count: int = 0
    inconclusive_count: int = 0
    vulnerability_rate: float = 0.0


class MutationMetrics(BaseModel):
    """Adversarial mutation and payload lineage metrics."""

    model_config = ConfigDict(extra="forbid")

    mutation_enabled: bool = False
    original_payload_count: int = 0
    variant_payload_count: int = 0
    strategies_used: list[str] = Field(default_factory=list)
    strategy_distribution: dict[str, int] = Field(default_factory=dict)
    baseline_vulnerable_count: int = 0
    variant_vulnerable_count: int = 0
    lineage_map: dict[str, list[str]] = Field(default_factory=dict)


class EvidenceMetrics(BaseModel):
    """Structured evidence and confidence score analytics."""

    model_config = ConfigDict(extra="forbid")

    total_evidence_items: int = 0
    evaluator_distribution: dict[str, int] = Field(default_factory=dict)
    evidence_type_distribution: dict[str, int] = Field(default_factory=dict)
    mean_confidence: float = 0.0
    confidence_distribution: dict[str, int] = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0}
    )
    confirmed_evidence_count: int = 0
    heuristic_evidence_count: int = 0


class OWASPRecord(BaseModel):
    """Mapping record for an OWASP Top 10 for LLMs vulnerability category."""

    model_config = ConfigDict(extra="forbid")

    owasp_code: str
    title: str
    tested: bool = False
    evaluated_count: int = 0
    vulnerable_count: int = 0
    finding_ids: list[str] = Field(default_factory=list)
    limitation_note: str | None = None


class MitreAtlasRecord(BaseModel):
    """Mapping record for a MITRE ATLAS technique."""

    model_config = ConfigDict(extra="forbid")

    technique_id: str
    technique_name: str = "Unavailable"
    tested: bool = False
    evaluated_count: int = 0
    vulnerable_count: int = 0
    finding_ids: list[str] = Field(default_factory=list)


class FindingDetail(BaseModel):
    """Granular technical audit detail for an evaluated attack vector."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str
    assessment_id: str
    payload_id: str
    parent_id: str | None = None
    is_variant: bool = False
    mutation_strategy: str | None = None
    category: AttackCategory
    verdict: Verdict
    severity: Severity
    cvss_score: float = 0.0
    owasp_id: str | None = None
    mitre_atlas_id: str | None = None
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)
    matched_patterns: list[str] = Field(default_factory=list)
    detected_canaries: list[str] = Field(default_factory=list)
    tool_call_violations: list[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    timestamp_utc: str | None = None


class ExecutiveSummary(BaseModel):
    """Synthesized executive summary for research and leadership briefings."""

    model_config = ConfigDict(extra="forbid")

    purpose: str
    scope_description: str
    target_summary: str
    total_evaluations: int
    verdict_summary: str
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    confirmed_compromises: list[str] = Field(default_factory=list)
    key_limitations: list[str] = Field(default_factory=list)
    remediation_priorities: list[str] = Field(default_factory=list)


class AssessmentReport(BaseModel):
    """Root structured research audit report for a completed assessment."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    assessment_id: str
    generated_at: str
    target_id: str
    target_provider: str = "Unknown"
    target_model: str = "Unknown"
    duration_seconds: float | None = None
    started_at: str | None = None
    completed_at: str | None = None

    executive_summary: ExecutiveSummary
    verdicts: VerdictDistribution
    severities: SeverityDistribution
    categories: list[CategoryMetric] = Field(default_factory=list)
    mutation_metrics: MutationMetrics | None = None
    evidence_metrics: EvidenceMetrics
    owasp_coverage: list[OWASPRecord] = Field(default_factory=list)
    mitre_coverage: list[MitreAtlasRecord] = Field(default_factory=list)
    findings: list[FindingDetail] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AssessmentComparison(BaseModel):
    """Comparative analysis across two or more historical assessments."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str
    assessment_ids: list[str]
    generated_at: str
    target_ids: list[str]
    is_compatible: bool
    compatibility_warnings: list[str] = Field(default_factory=list)

    verdict_deltas: dict[str, dict[str, int]] = Field(default_factory=dict)
    severity_deltas: dict[str, dict[str, int]] = Field(default_factory=dict)
    category_deltas: dict[str, dict[str, int]] = Field(default_factory=dict)
    new_vulnerabilities: list[str] = Field(default_factory=list)
    resolved_vulnerabilities: list[str] = Field(default_factory=list)
    persistent_vulnerabilities: list[str] = Field(default_factory=list)
    comparative_notes: list[str] = Field(default_factory=list)
