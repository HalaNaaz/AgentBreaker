"""Tests for CLI report commands integration."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentbreaker.cli.main import app
from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult
from agentbreaker.schemas.target import TargetConfig

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> StorageManager:
    """Isolate CLI storage environment."""
    monkeypatch.setenv("AGENTBREAKER_HOME", str(tmp_path))
    monkeypatch.setenv("COLUMNS", "200")
    sm = StorageManager(tmp_path)

    # Pre-populate a target and assessment result for CLI commands
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="mock-target",
    )
    sm.save_target("cli-target", cfg)

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
            detected_canaries=["AGY-CANARY-CLI"],
            reasons=["Disclosed canary secret token"],
        )
    ]
    meta = {
        "assessment_id": "ASM-CLI01",
        "target_id": "cli-target",
        "target_model": "mock-target",
        "started_at": "2026-11-10T12:00:00Z",
        "completed_at": "2026-11-10T12:05:00Z",
        "total_payloads": 1,
        "vulnerable_count": 1,
        "defended_count": 0,
        "inconclusive_count": 0,
    }
    sm.save_results("ASM-CLI01", results, metadata=meta)

    # Pre-populate a second assessment for comparison
    results2 = [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
            confidence=0.90,
            reasons=["Defended cleanly"],
        )
    ]
    meta2 = {
        "assessment_id": "ASM-CLI02",
        "target_id": "cli-target",
        "target_model": "mock-target",
        "total_payloads": 1,
        "vulnerable_count": 0,
        "defended_count": 1,
        "inconclusive_count": 0,
    }
    sm.save_results("ASM-CLI02", results2, metadata=meta2)

    return sm


def test_cli_report_list_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify 'report list' displays warning when no reports exist."""
    res = runner.invoke(app, ["report", "list"])
    assert res.exit_code == 0
    assert "No saved reports found" in res.stdout


def test_cli_report_generate_json() -> None:
    """Verify 'report generate' generates JSON report successfully."""
    res = runner.invoke(app, ["report", "generate", "ASM-CLI01", "--format", "json"])
    assert res.exit_code == 0
    assert "Report successfully generated in JSON format" in res.stdout


def test_cli_report_generate_markdown() -> None:
    """Verify 'report generate' generates Markdown report successfully."""
    res = runner.invoke(app, ["report", "generate", "ASM-CLI01", "--format", "markdown"])
    assert res.exit_code == 0
    assert "Report successfully generated in MARKDOWN format" in res.stdout


def test_cli_report_generate_html() -> None:
    """Verify 'report generate' generates HTML report successfully."""
    res = runner.invoke(app, ["report", "generate", "ASM-CLI01", "--format", "html"])
    assert res.exit_code == 0
    assert "Report successfully generated in HTML format" in res.stdout


def test_cli_report_show() -> None:
    """Verify 'report show' prints executive summary and category analytics."""
    res = runner.invoke(app, ["report", "show", "ASM-CLI01"])
    assert res.exit_code == 0
    assert "Research Audit Report: RPT-ASM-CLI01" in res.stdout
    assert "Executive Summary" in res.stdout
    assert "Attack Category Analytics" in res.stdout


def test_cli_report_analytics() -> None:
    """Verify 'report analytics' displays OWASP and MITRE tables."""
    res = runner.invoke(app, ["report", "analytics", "ASM-CLI01"])
    assert res.exit_code == 0
    assert "OWASP Top 10 for LLMs Coverage" in res.stdout
    assert "MITRE ATLAS Matrix Techniques Observed" in res.stdout
    assert "Evidence & Confidence Metrics" in res.stdout


def test_cli_report_compare() -> None:
    """Verify 'report compare' compares two assessments."""
    res = runner.invoke(app, ["report", "compare", "ASM-CLI01", "ASM-CLI02"])
    assert res.exit_code == 0
    assert "Comparative Assessment Analysis: ASM-CLI01 vs ASM-CLI02" in res.stdout
    assert "Verdict Outcome Comparison" in res.stdout
    assert "Vulnerability Progression" in res.stdout
    assert "Resolved Vulnerabilities" in res.stdout


def test_cli_report_export(tmp_path: Path) -> None:
    """Verify 'report export' directly writes report to custom path."""
    dest = tmp_path / "custom_exports" / "report.json"
    res = runner.invoke(
        app,
        [
            "report",
            "export",
            "ASM-CLI01",
            "--output",
            str(dest),
            "--format",
            "json",
            "--overwrite",
        ],
    )
    assert res.exit_code == 0
    assert dest.exists()
