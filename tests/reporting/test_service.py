"""Tests for ReportingService orchestration with StorageManager."""

from pathlib import Path

import pytest

from agentbreaker.cli.storage import StorageManager
from agentbreaker.reporting.exceptions import ReportNotFoundError
from agentbreaker.reporting.models import ReportFormat
from agentbreaker.reporting.service import ReportingService
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def test_storage(tmp_path: Path) -> StorageManager:
    """Fixture providing isolated storage for reporting service tests."""
    return StorageManager(tmp_path)


def test_reporting_service_build_and_save(test_storage: StorageManager, tmp_path: Path) -> None:
    """Verify building and saving reports across JSON, Markdown, and HTML."""
    # 1. Setup target
    cfg = TargetConfig(
        endpoint_url="http://127.0.0.1:8000/v1",
        model_name="mock-target",
    )
    test_storage.save_target("t1", cfg)

    # 2. Setup assessment results
    results = [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            cvss_score=7.5,
            confidence=0.95,
        )
    ]
    meta = {
        "assessment_id": "ASM-SRVTEST",
        "target_id": "t1",
        "target_model": "mock-target",
        "started_at": "2026-11-10T10:00:00Z",
        "completed_at": "2026-11-10T10:01:00Z",
        "total_payloads": 1,
        "vulnerable_count": 1,
        "defended_count": 0,
        "inconclusive_count": 0,
    }
    test_storage.save_results("ASM-SRVTEST", results, metadata=meta)

    service = ReportingService(test_storage)

    # 3. Build report model
    report = service.build_report("ASM-SRVTEST")
    assert report.report_id == "RPT-ASM-SRVTEST"
    assert report.verdicts.vulnerable == 1
    assert report.target_provider == "openai_compatible"

    # 4. Save JSON report
    json_path = service.save_report("ASM-SRVTEST", output_format=ReportFormat.JSON)
    assert json_path.exists()
    assert json_path.suffix == ".json"

    # 5. Save Markdown report
    md_path = service.save_report("ASM-SRVTEST", output_format=ReportFormat.MARKDOWN)
    assert md_path.exists()
    assert md_path.suffix == ".md"

    # 6. Save HTML report
    html_path = service.save_report("ASM-SRVTEST", output_format=ReportFormat.HTML)
    assert html_path.exists()
    assert html_path.suffix == ".html"

    # 7. List reports
    listed = service.list_reports()
    assert len(listed) == 3


def test_reporting_service_missing_assessment(test_storage: StorageManager) -> None:
    """Verify ReportNotFoundError when attempting to build report for non-existent assessment."""
    service = ReportingService(test_storage)
    with pytest.raises(ReportNotFoundError):
        service.build_report("ASM-NONEXISTENT")
