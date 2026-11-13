"""Tests for technical audit findings, report generation, and safe downloads."""

from fastapi.testclient import TestClient

from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def test_findings_queries_and_filters(client: TestClient, temp_storage: StorageManager) -> None:
    """Verify findings querying with multi-criteria filtering."""
    asm_id = "ASM-FIND-01"
    # Seed storage with mock results
    results = [
        EvaluationResult(
            payload_id="P-CRIT-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.CRITICAL,
            reasons=["Canary secret revealed"],
            owasp_id="LLM01: Prompt Injection",
            mitre_atlas_id="AML.T0054",
        ),
        EvaluationResult(
            payload_id="P-DEF-01",
            category=AttackCategory.SYSTEM_EXTRACTION,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
            reasons=["Model refused cleanly"],
        ),
    ]
    temp_storage.save_results(asm_id, results, metadata={"target_id": "test", "target_model": "m"})

    # 1. Query all findings
    res = client.get("/api/v1/findings")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

    # 2. Filter by verdict
    vuln_res = client.get("/api/v1/findings?verdict=VULNERABLE")
    assert vuln_res.status_code == 200
    assert vuln_res.json()["total"] == 1
    assert vuln_res.json()["items"][0]["payload_id"] == "P-CRIT-01"

    # 3. Filter by severity
    crit_res = client.get("/api/v1/findings?severity=CRITICAL")
    assert crit_res.status_code == 200
    assert crit_res.json()["total"] == 1

    # 4. Get specific finding detail
    f_id = vuln_res.json()["items"][0]["finding_id"]
    detail_res = client.get(f"/api/v1/findings/{f_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["finding_id"] == f_id
    assert detail["owasp_id"] == "LLM01: Prompt Injection"
    assert detail["mitre_atlas_id"] == "AML.T0054"


def test_reports_generation_and_download(client: TestClient, temp_storage: StorageManager) -> None:
    """Verify generating JSON, Markdown, and HTML reports, and downloading via API."""
    asm_id = "ASM-REP-01"
    # Create target & assessment records
    temp_storage.save_assessment(
        {
            "id": asm_id,
            "name": "Report Test Assessment",
            "target_id": "t1",
            "status": "COMPLETED",
        }
    )
    results = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
        )
    ]
    temp_storage.save_results(asm_id, results, metadata={"target_id": "t1", "target_model": "m"})

    # 1. Generate JSON report
    gen_json = client.post(
        f"/api/v1/reports/generate?assessment_id={asm_id}",
        json={"format": "json"},
    )
    assert gen_json.status_code == 201
    assert "JSON" in gen_json.json()["message"]

    # 2. Generate Markdown report
    gen_md = client.post(
        f"/api/v1/reports/generate?assessment_id={asm_id}",
        json={"format": "markdown"},
    )
    assert gen_md.status_code == 201

    # 3. Generate HTML report
    gen_html = client.post(
        f"/api/v1/reports/generate?assessment_id={asm_id}",
        json={"format": "html"},
    )
    assert gen_html.status_code == 201

    # 4. List reports
    list_res = client.get("/api/v1/reports")
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) == 3

    # 5. Download report
    json_filename = f"RPT-{asm_id}.json"
    dl_res = client.get(f"/api/v1/reports/{json_filename}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/json"
    assert "report_id" in dl_res.json()

    # 6. Verify directory traversal rejected on download
    bad_dl = client.get("/api/v1/reports/..%2f..%2fetc%2fpasswd/download")
    assert bad_dl.status_code in (404, 422)
