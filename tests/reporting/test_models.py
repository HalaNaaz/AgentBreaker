"""Tests for reporting data models validation and serialization."""

import pytest
from pydantic import ValidationError

from agentbreaker.reporting.models import (
    AssessmentReport,
    EvidenceMetrics,
    ExecutiveSummary,
    FindingDetail,
    MitreAtlasRecord,
    OWASPRecord,
    SeverityDistribution,
    VerdictDistribution,
)
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict


def test_verdict_distribution_model() -> None:
    """Verify VerdictDistribution default values and rate constraints."""
    vd = VerdictDistribution(
        total=10,
        vulnerable=3,
        defended=5,
        inconclusive=2,
        vulnerable_rate=30.0,
        defended_rate=50.0,
        inconclusive_rate=20.0,
    )
    assert vd.total == 10
    assert vd.vulnerable == 3
    assert vd.vulnerable_rate == 30.0


def test_severity_distribution_model() -> None:
    """Verify SeverityDistribution aggregation schema."""
    sd = SeverityDistribution(critical=1, high=2, medium=3, low=4, informational=0)
    assert sd.critical == 1
    assert sd.high == 2
    assert sd.medium == 3
    assert sd.low == 4


def test_owasp_record_model() -> None:
    """Verify OWASPRecord validation."""
    owasp = OWASPRecord(
        owasp_code="LLM01",
        title="LLM01: Prompt Injection",
        tested=True,
        evaluated_count=8,
        vulnerable_count=2,
        finding_ids=["JB-001", "JB-002"],
    )
    assert owasp.tested is True
    assert len(owasp.finding_ids) == 2


def test_mitre_record_model() -> None:
    """Verify MitreAtlasRecord validation."""
    mitre = MitreAtlasRecord(
        technique_id="AML.T0054",
        technique_name="LLM Jailbreak",
        tested=True,
        evaluated_count=5,
        vulnerable_count=1,
    )
    assert mitre.technique_id == "AML.T0054"
    assert mitre.technique_name == "LLM Jailbreak"


def test_finding_detail_model() -> None:
    """Verify FindingDetail attributes and schema validation."""
    fd = FindingDetail(
        finding_id="ASM-123_JB-001",
        assessment_id="ASM-123",
        payload_id="JB-001",
        category=AttackCategory.DIRECT_JAILBREAK,
        verdict=Verdict.VULNERABLE,
        severity=Severity.HIGH,
        cvss_score=7.5,
        confidence=0.95,
        reasons=["Detected violation"],
    )
    assert fd.finding_id == "ASM-123_JB-001"
    assert fd.verdict == Verdict.VULNERABLE
    assert fd.severity == Severity.HIGH


def test_assessment_report_root_validation() -> None:
    """Verify full AssessmentReport model assembly."""
    exec_summary = ExecutiveSummary(
        purpose="Safety audit",
        scope_description="All jailbreaks",
        target_summary="Target local-llm",
        total_evaluations=1,
        verdict_summary="1 test case evaluated",
        critical_vulnerabilities=0,
        high_vulnerabilities=1,
        medium_vulnerabilities=0,
        low_vulnerabilities=0,
    )
    report = AssessmentReport(
        report_id="RPT-ASM-TEST",
        assessment_id="ASM-TEST",
        generated_at="2026-11-10T12:00:00Z",
        target_id="local-llm",
        executive_summary=exec_summary,
        verdicts=VerdictDistribution(total=1, vulnerable=1, vulnerable_rate=100.0),
        severities=SeverityDistribution(high=1),
        evidence_metrics=EvidenceMetrics(),
    )
    assert report.report_id == "RPT-ASM-TEST"
    assert report.verdicts.vulnerable == 1


def test_report_model_extra_forbid() -> None:
    """Verify that unexpected extra fields are forbidden in reporting models."""
    with pytest.raises(ValidationError):
        VerdictDistribution(total=5, unknown_field=123)  # type: ignore[call-arg]
