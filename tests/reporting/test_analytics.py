"""Tests for OWASP LLM Top 10, MITRE ATLAS, and executive summary analytics."""

from agentbreaker.reporting.aggregations import (
    compute_severity_distribution,
    compute_verdict_distribution,
)
from agentbreaker.reporting.analytics import (
    build_executive_summary,
    build_mitre_atlas_coverage,
    build_owasp_coverage,
    compile_findings,
)
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def _sample_results_with_mappings() -> list[EvaluationResult]:
    return [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            cvss_score=7.5,
            owasp_id="LLM01: Prompt Injection",
            mitre_atlas_id="AML.T0054",
            detected_canaries=["AGY-CANARY-001"],
            reasons=["Disclosed canary"],
        ),
        EvaluationResult(
            payload_id="EXT-001",
            category=AttackCategory.SYSTEM_EXTRACTION,
            verdict=Verdict.DEFENDED,
            severity=Severity.MEDIUM,
            owasp_id="LLM02: Sensitive Information Disclosure",
            mitre_atlas_id="AML.T0056",
            reasons=["Clean refusal observed"],
        ),
    ]


def test_build_owasp_coverage() -> None:
    """Verify OWASP mapping preserves tested/untested distinction without inventing data."""
    results = _sample_results_with_mappings()
    coverage = build_owasp_coverage(results)
    assert len(coverage) == 10  # Top 10 categories

    llm01 = next(o for o in coverage if o.owasp_code == "LLM01")
    assert llm01.tested is True
    assert llm01.evaluated_count == 1
    assert llm01.vulnerable_count == 1
    assert "JB-001" in llm01.finding_ids

    llm02 = next(o for o in coverage if o.owasp_code == "LLM02")
    assert llm02.tested is True
    assert llm02.evaluated_count == 1
    assert llm02.vulnerable_count == 0  # Defended

    llm03 = next(o for o in coverage if o.owasp_code == "LLM03")
    assert llm03.tested is False
    assert llm03.evaluated_count == 0
    assert llm03.limitation_note is not None


def test_build_mitre_atlas_coverage() -> None:
    """Verify MITRE ATLAS mapping resolves technique names."""
    results = _sample_results_with_mappings()
    mitre = build_mitre_atlas_coverage(results)
    assert len(mitre) == 2

    t54 = next(m for m in mitre if m.technique_id == "AML.T0054")
    assert t54.technique_name == "LLM Jailbreak"
    assert t54.vulnerable_count == 1

    t56 = next(m for m in mitre if m.technique_id == "AML.T0056")
    assert t56.technique_name == "System Prompt Extraction"
    assert t56.vulnerable_count == 0


def test_compile_findings() -> None:
    """Verify conversion of EvaluationResult items into FindingDetail models."""
    results = _sample_results_with_mappings()
    findings = compile_findings(results, assessment_id="ASM-101")
    assert len(findings) == 2
    assert findings[0].finding_id == "ASM-101_JB-001"
    assert findings[0].verdict == Verdict.VULNERABLE
    assert findings[0].cvss_score == 7.5


def test_build_executive_summary() -> None:
    """Verify executive summary generation rules and confirmed compromise extraction."""
    results = _sample_results_with_mappings()
    v_dist = compute_verdict_distribution(results)
    s_dist = compute_severity_distribution(results)

    summary = build_executive_summary(
        assessment_id="ASM-101",
        target_id="my-llm",
        target_model="gpt-4o",
        verdicts=v_dist,
        severities=s_dist,
        results=results,
    )

    assert summary.total_evaluations == 2
    assert summary.high_vulnerabilities == 1
    assert len(summary.confirmed_compromises) == 1
    assert "AGY-CANARY-001" in summary.confirmed_compromises[0]
    assert len(summary.remediation_priorities) > 0
    assert len(summary.key_limitations) > 0
