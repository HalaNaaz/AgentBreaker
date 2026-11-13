"""Adversarial security, correctness, and edge-case audit tests for Phase 7."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from agentbreaker.cli.storage import StorageManager
from agentbreaker.reporting.comparison import AssessmentComparator
from agentbreaker.reporting.exceptions import InvalidReportPathError
from agentbreaker.reporting.models import ReportFormat
from agentbreaker.reporting.redaction import validate_report_path
from agentbreaker.reporting.service import ReportingService
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def _write_raw(storage_mgr: StorageManager, asm_id: str, data: dict) -> Path:
    storage_mgr.results_dir.mkdir(parents=True, exist_ok=True)
    p = storage_mgr.results_dir / f"{asm_id}_results.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_audit_nested_secret_leakage(tmp_path: Path) -> None:
    """Audit: verify nested secrets, URL credentials, and tokens are redacted across all formats."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-LEAK"

    raw_results = {
        "metadata": {
            "target_id": "test-leak-target",
            "target_model": "gpt-4o",
            "auth_token": "secret_token_12345",
        },
        "results": [
            {
                "payload_id": "P-LEAK-01",
                "category": "system_extraction",
                "verdict": "VULNERABLE",
                "severity": "CRITICAL",
                "confidence": 1.0,
                "reasons": [
                    "Leaked via http://admin:SuperSecretPass123@api.internal.com/data",
                    "Header present: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.topsecret",
                    "Parameter observed: api_key=sk-proj-1234567890abcdef1234567890",
                ],
                "evidence": [
                    {
                        "evaluator_name": "canary",
                        "nested": {
                            "deep_secret": "sk-deepsecret1234567890abcdef",
                            "user_pass": "https://service:PassWord999@domain.org",
                        },
                    }
                ],
                "detected_canaries": ["sk-leakedcanary1234567890"],
                "tool_call_violations": ["exec_cmd(api_key='sk-execsecret1234567890')"],
            }
        ],
    }

    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)

    # 1. JSON
    json_out = service.generate_report(asm_id, output_format=ReportFormat.JSON)
    assert "SuperSecretPass123" not in json_out
    assert "PassWord999" not in json_out
    assert "sk-proj-1234567890abcdef1234567890" not in json_out
    assert "sk-deepsecret1234567890abcdef" not in json_out
    assert "sk-leakedcanary1234567890" not in json_out
    assert "sk-execsecret1234567890" not in json_out

    # 2. Markdown
    md_out = service.generate_report(asm_id, output_format=ReportFormat.MARKDOWN)
    assert "SuperSecretPass123" not in md_out
    assert "PassWord999" not in md_out
    assert "sk-proj-" not in md_out
    assert "sk-leakedcanary" not in md_out

    # 3. HTML
    html_out = service.generate_report(asm_id, output_format=ReportFormat.HTML)
    assert "SuperSecretPass123" not in html_out
    assert "PassWord999" not in html_out
    assert "sk-proj-" not in html_out
    assert "sk-leakedcanary" not in html_out


def test_audit_html_injection_prevention(tmp_path: Path) -> None:
    """Audit: verify malicious HTML/script payloads in evaluation findings cannot execute."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-XSS"

    xss_payload = '<script>alert("XSS")</script><img src="x" onerror="evil()">'
    raw_results = {
        "metadata": {
            "target_id": 'target"><script>alert(1)</script>',
            "target_model": "model-xss",
        },
        "results": [
            {
                "payload_id": 'P-XSS"><b onmouseover="alert(2)">',
                "category": "direct_jailbreak",
                "verdict": "VULNERABLE",
                "severity": "HIGH",
                "confidence": 0.95,
                "reasons": [xss_payload],
                "evidence": [{"evaluator_name": "xss", "payload": xss_payload}],
                "detected_canaries": [xss_payload],
                "tool_call_violations": [xss_payload],
            }
        ],
    }

    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)
    html_out = service.generate_report(asm_id, output_format=ReportFormat.HTML)

    # Verify no unescaped script or onerror handlers exist
    assert "<script>" not in html_out
    assert "</script>" not in html_out
    assert 'onerror="evil()"' not in html_out
    assert 'onmouseover="alert(2)"' not in html_out

    # Verify presence of escaped entities
    assert "&lt;script&gt;" in html_out


def test_audit_path_traversal_rejection(tmp_path: Path) -> None:
    """Audit: verify path traversal vectors are rejected."""
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Traversal via parent directories
    with pytest.raises(InvalidReportPathError):
        validate_report_path(base_dir / ".." / "escaped.json", base_dir=base_dir)

    with pytest.raises(InvalidReportPathError):
        validate_report_path(base_dir / "subdir" / ".." / ".." / "outside.html", base_dir=base_dir)

    # Traversal via null bytes
    with pytest.raises(InvalidReportPathError):
        validate_report_path("report\0.json", base_dir=base_dir)


def test_audit_windows_path_handling(tmp_path: Path) -> None:
    """Audit: verify Windows UNC network paths and reserved device names are forbidden."""
    # UNC paths
    with pytest.raises(InvalidReportPathError, match="UNC network paths are forbidden"):
        validate_report_path(r"\\evil-host\share\report.json")

    with pytest.raises(InvalidReportPathError, match="UNC network paths are forbidden"):
        validate_report_path("//evil-host/share/report.html")

    # Windows reserved device names
    for dev in ("CON", "PRN", "AUX", "NUL", "COM1", "LPT1"):
        with pytest.raises(InvalidReportPathError, match="reserved device"):
            validate_report_path(tmp_path / f"{dev}.json")


def test_audit_duplicate_aggregation_and_collision(tmp_path: Path) -> None:
    """Audit: verify multiple findings with identical payload IDs do not collide or crash."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-DUP"

    raw_results = {
        "metadata": {"target_id": "test-dup", "target_model": "model-1"},
        "results": [
            {
                "payload_id": "P-DUP-01",
                "category": "direct_jailbreak",
                "verdict": "VULNERABLE",
                "severity": "HIGH",
            },
            {
                "payload_id": "P-DUP-01",  # Duplicate payload ID evaluated twice
                "category": "direct_jailbreak",
                "verdict": "DEFENDED",
                "severity": "HIGH",
            },
        ],
    }

    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)
    report = service.build_report(asm_id)

    assert len(report.findings) == 2
    f_ids = [f.finding_id for f in report.findings]
    assert len(f_ids) == len(set(f_ids)), "Finding IDs must remain unique despite duplicate inputs"


def test_audit_incompatible_historical_comparisons() -> None:
    """Audit: verify comparison flags targets and does not falsely resolve omitted payloads."""
    comparator = AssessmentComparator()

    # Target divergence
    meta1 = {"id": "ASM-1", "target_id": "target-a", "target_model": "model-a"}
    res1 = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
        ),
        EvaluationResult(
            payload_id="P-02",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
        ),
    ]

    meta2 = {"id": "ASM-2", "target_id": "target-b", "target_model": "model-b"}
    # P-01 is defended, P-02 is OMITTED entirely (not tested in run 2)
    res2 = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
        ),
        EvaluationResult(
            payload_id="P-03",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.LOW,
        ),
    ]

    comp = comparator.compare([(meta1, res1), (meta2, res2)])
    assert comp.is_compatible is False
    assert any("Targets differ" in w for w in comp.compatibility_warnings)

    # P-01 was vulnerable and is now defended -> resolved
    assert "P-01" in comp.resolved_vulnerabilities
    # P-02 was vulnerable and omitted in run 2 -> MUST NOT be in resolved_vulnerabilities!
    assert "P-02" not in comp.resolved_vulnerabilities
    # P-03 was not in run 1 and is vulnerable in run 2 -> new
    assert "P-03" in comp.new_vulnerabilities


def test_audit_missing_mapping_data_handling() -> None:
    """Audit: verify reports handle missing, malformed, or unknown OWASP/MITRE IDs gracefully."""
    results = [
        EvaluationResult(
            payload_id="P-UNKNOWN-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            owasp_id=None,
            mitre_atlas_id="AML.T9999_NONEXISTENT",
        )
    ]

    from agentbreaker.reporting.analytics import build_mitre_atlas_coverage, build_owasp_coverage

    owasp = build_owasp_coverage(results)
    # Since owasp_id is None, all categories should be marked untested
    for rec in owasp:
        assert rec.tested is False
        assert rec.evaluated_count == 0

    mitre = build_mitre_atlas_coverage(results)
    assert len(mitre) == 1
    assert mitre[0].technique_id == "AML.T9999_NONEXISTENT"
    assert mitre[0].technique_name == "Unavailable"


def test_audit_incorrect_denominators_and_zero_division() -> None:
    """Audit: verify aggregation formulas on empty results return 0.0% without division-by-zero."""
    from agentbreaker.reporting.aggregations import (
        compute_category_metrics,
        compute_evidence_metrics,
        compute_verdict_distribution,
    )

    empty_res: list[EvaluationResult] = []
    verdicts = compute_verdict_distribution(empty_res)
    assert verdicts.total == 0
    assert verdicts.vulnerable_rate == 0.0
    assert verdicts.defended_rate == 0.0
    assert verdicts.inconclusive_rate == 0.0

    cats = compute_category_metrics(empty_res)
    for c in cats:
        assert c.total_evaluated == 0
        assert c.vulnerability_rate == 0.0

    ev = compute_evidence_metrics(empty_res)
    assert ev.total_evidence_items == 0
    assert ev.mean_confidence == 0.0


def test_audit_corrupted_assessment_records(tmp_path: Path) -> None:
    """Audit: verify service gracefully handles corrupted records in results file."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-CORRUPT"

    raw_results = {
        "metadata": {"target_id": "test-corrupt", "target_model": "gpt-4"},
        "results": [
            {"invalid_field_only": True},  # Missing required fields
            "not a dictionary",  # Corrupted type
            {
                "payload_id": "P-VALID-01",
                "category": "direct_jailbreak",
                "verdict": "DEFENDED",
            },
        ],
    }

    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)
    report = service.build_report(asm_id)

    # Only valid entry should be parsed
    assert report.verdicts.total == 1
    assert report.findings[0].payload_id == "P-VALID-01"


def test_audit_atomic_write_safety(tmp_path: Path) -> None:
    """Audit: verify atomic report writing creates target file and cleans up scratch files."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-ATOMIC"

    raw_results = {
        "metadata": {"target_id": "test-target", "target_model": "test-model"},
        "results": [
            {
                "payload_id": "P-01",
                "category": "direct_jailbreak",
                "verdict": "DEFENDED",
            }
        ],
    }
    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)

    out_file = tmp_path / "reports" / "safe_report.json"
    saved = service.save_report(asm_id, output_format=ReportFormat.JSON, dest_path=out_file)

    assert saved.exists()
    assert saved.is_file()
    # Ensure no lingering .tmp files exist
    tmp_files = list(out_file.parent.glob("*.tmp_*"))
    assert len(tmp_files) == 0


def test_audit_concurrent_report_generation(tmp_path: Path) -> None:
    """Audit: verify concurrent multi-threaded report generation does not cause race conditions."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-CONCUR"

    raw_results = {
        "metadata": {"target_id": "test-target", "target_model": "test-model"},
        "results": [
            {
                "payload_id": f"P-{i:02d}",
                "category": "direct_jailbreak",
                "verdict": "VULNERABLE" if i % 2 == 0 else "DEFENDED",
            }
            for i in range(10)
        ],
    }
    _write_raw(storage_mgr, asm_id, raw_results)
    service = ReportingService(storage_manager=storage_mgr)

    def generate_worker(fmt: ReportFormat) -> str:
        return service.generate_report(asm_id, output_format=fmt)

    formats = [
        ReportFormat.JSON,
        ReportFormat.MARKDOWN,
        ReportFormat.HTML,
        ReportFormat.JSON,
        ReportFormat.MARKDOWN,
        ReportFormat.HTML,
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generate_worker, fmt) for fmt in formats]
        results = [f.result() for f in futures]

    assert len(results) == len(formats)
    for r in results:
        assert len(r) > 100


def test_audit_source_result_immutability(tmp_path: Path) -> None:
    """Audit: verify source evaluation records remain unchanged after report generation."""
    storage_mgr = StorageManager(base_dir=tmp_path)
    asm_id = "ASM-AUDIT-IMMUTABLE"

    raw_results = {
        "metadata": {"target_id": "test-target", "target_model": "test-model"},
        "results": [
            {
                "payload_id": "P-IMMUT-01",
                "category": "direct_jailbreak",
                "verdict": "DEFENDED",
                "confidence": 0.99,
            }
        ],
    }
    res_path = _write_raw(storage_mgr, asm_id, raw_results)
    before_sha256 = hashlib.sha256(res_path.read_bytes()).hexdigest()

    service = ReportingService(storage_manager=storage_mgr)

    # Perform report compilation, generation in all formats, and saving
    service.build_report(asm_id)
    service.generate_report(asm_id, output_format=ReportFormat.JSON)
    service.generate_report(asm_id, output_format=ReportFormat.MARKDOWN)
    service.generate_report(asm_id, output_format=ReportFormat.HTML)
    service.save_report(asm_id, output_format=ReportFormat.JSON)

    after_sha256 = hashlib.sha256(res_path.read_bytes()).hexdigest()
    assert before_sha256 == after_sha256, "Source results file on disk must remain unchanged"
