"""Tests for JSON, Markdown, and HTML report generators."""

import json

from agentbreaker.reporting.aggregations import (
    compute_category_metrics,
    compute_evidence_metrics,
    compute_mutation_metrics,
    compute_severity_distribution,
    compute_verdict_distribution,
)
from agentbreaker.reporting.analytics import (
    build_executive_summary,
    build_mitre_atlas_coverage,
    build_owasp_coverage,
    compile_findings,
)
from agentbreaker.reporting.generators.html_report import HtmlReportGenerator
from agentbreaker.reporting.generators.json_report import JsonReportGenerator
from agentbreaker.reporting.generators.markdown_report import MarkdownReportGenerator
from agentbreaker.reporting.models import AssessmentReport
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def _build_test_report(malicious_text: str = "") -> AssessmentReport:
    results = [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            cvss_score=7.5,
            confidence=0.95,
            owasp_id="LLM01: Prompt Injection",
            mitre_atlas_id="AML.T0054",
            detected_canaries=["AGY-CANARY-SEC-99"],
            reasons=[f"Breach detected: {malicious_text}" if malicious_text else "Breach detected"],
        ),
        EvaluationResult(
            payload_id="JB-001_ROT_1",
            parent_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
            confidence=0.90,
            reasons=["Refusal detected"],
        ),
    ]

    verdicts = compute_verdict_distribution(results)
    severities = compute_severity_distribution(results)
    categories = compute_category_metrics(results)
    mutation = compute_mutation_metrics(results, metadata={"mutation_enabled": True})
    evidence = compute_evidence_metrics(results)
    owasp = build_owasp_coverage(results)
    mitre = build_mitre_atlas_coverage(results)
    findings = compile_findings(results, assessment_id="ASM-GEN")
    summary = build_executive_summary(
        assessment_id="ASM-GEN",
        target_id="test-target",
        target_model="gpt-4o",
        verdicts=verdicts,
        severities=severities,
        results=results,
    )

    return AssessmentReport(
        report_id="RPT-ASM-GEN",
        assessment_id="ASM-GEN",
        generated_at="2026-11-10T14:00:00Z",
        target_id="test-target",
        target_provider="openai_compatible",
        target_model="gpt-4o",
        executive_summary=summary,
        verdicts=verdicts,
        severities=severities,
        categories=categories,
        mutation_metrics=mutation,
        evidence_metrics=evidence,
        owasp_coverage=owasp,
        mitre_coverage=mitre,
        findings=findings,
        limitations=["Empirical findings only."],
        recommendations=["Deploy guardrails."],
    )


def test_json_report_generation() -> None:
    """Verify JSON report generates valid, parseable JSON conforming to schema."""
    report = _build_test_report()
    generator = JsonReportGenerator()
    output = generator.generate(report)

    data = json.loads(output)
    assert data["report_id"] == "RPT-ASM-GEN"
    assert data["verdicts"]["total"] == 2
    assert data["verdicts"]["vulnerable"] == 1
    assert data["mutation_metrics"]["original_payload_count"] == 1
    assert data["mutation_metrics"]["variant_payload_count"] == 1


def test_markdown_report_generation() -> None:
    """Verify Markdown report contains all required headers and tables."""
    report = _build_test_report()
    generator = MarkdownReportGenerator()
    md = generator.generate(report)

    assert "# AgentBreaker Security Assessment Audit Report: ASM-GEN" in md
    assert "## 1. Executive Summary" in md
    assert "## 2. Evaluation Metrics & Verdict Breakdown" in md
    assert "## 3. Attack Category Analysis" in md
    assert "## 4. Adversarial Mutation & Lineage Analytics" in md
    assert "## 5. OWASP Top 10 for LLMs Coverage" in md
    assert "## 7. Granular Technical Findings" in md
    assert "AGY-CANARY-SEC-99" in md


def test_html_report_generation_and_autoescaping() -> None:
    """Verify HTML report generates complete document and autoescapes malicious script payloads."""
    xss_payload = '<script>alert("xss")</script><img src=x onerror=alert(1)>'
    report = _build_test_report(malicious_text=xss_payload)
    generator = HtmlReportGenerator()
    html_output = generator.generate(report)

    assert "<!DOCTYPE html>" in html_output
    assert "AgentBreaker Audit Report: ASM-GEN" in html_output
    assert "AshlynxCyber Security Systems" in html_output

    # Crucial security assertion: unescaped script tags must NEVER appear in HTML
    assert '<script>alert("xss")</script>' not in html_output
    assert "&lt;script&gt;alert(" in html_output
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_output
