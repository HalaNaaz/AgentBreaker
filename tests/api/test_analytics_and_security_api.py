"""Tests for Analytics endpoints, CORS allowlist, request size limits, and security headers."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def test_analytics_endpoints(client: TestClient, temp_storage: StorageManager) -> None:
    """Verify macro overview, assessment analytics, and comparative endpoints."""
    asm1 = "ASM-ANA-01"
    asm2 = "ASM-ANA-02"

    temp_storage.save_assessment(
        {"id": asm1, "name": "Run 1", "target_id": "t1", "status": "COMPLETED"}
    )
    temp_storage.save_assessment(
        {"id": asm2, "name": "Run 2", "target_id": "t1", "status": "COMPLETED"}
    )

    res1 = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            owasp_id="LLM01",
        )
    ]
    res2 = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
            owasp_id="LLM01",
        )
    ]
    temp_storage.save_results(asm1, res1, metadata={"target_id": "t1", "target_model": "gpt-4o"})
    temp_storage.save_results(asm2, res2, metadata={"target_id": "t1", "target_model": "gpt-4o"})

    # 1. Macro Overview
    overview_res = client.get("/api/v1/analytics/overview")
    assert overview_res.status_code == 200
    ov_data = overview_res.json()
    assert ov_data["total_assessments"] >= 2
    assert ov_data["total_evaluations"] == 2
    assert ov_data["total_vulnerabilities"] == 1
    assert ov_data["total_defended"] == 1
    assert ov_data["overall_vulnerability_rate"] == 50.0

    # 2. Granular Assessment Analytics
    ana_res = client.get(f"/api/v1/analytics/assessments/{asm1}")
    assert ana_res.status_code == 200
    ana_data = ana_res.json()
    assert ana_data["assessment_id"] == asm1
    assert "verdicts" in ana_data
    assert "owasp_coverage" in ana_data
    assert len(ana_data["owasp_coverage"]) == 10

    # 3. Assessment Comparison
    comp_res = client.post(
        "/api/v1/analytics/compare",
        json={"assessment_ids": [asm1, asm2]},
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["is_compatible"] is True
    assert "P-01" in comp_data["resolved_vulnerabilities"]


def test_security_headers_and_cors(client: TestClient) -> None:
    """Verify presence of security headers and CORS policy."""
    # Pre-flight OPTIONS request
    cors_res = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert cors_res.status_code == 200
    assert cors_res.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"

    # Untrusted origin should NOT receive allow-origin
    untrusted_res = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://evil-attacker-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert untrusted_res.headers.get("access-control-allow-origin") is None

    # Security headers on normal GET
    get_res = client.get("/api/v1/health")
    assert get_res.headers.get("x-content-type-options") == "nosniff"
    assert get_res.headers.get("x-frame-options") == "DENY"
    assert get_res.headers.get("server") == "AgentBreaker-Station"


def test_request_size_limit_middleware(client: TestClient) -> None:
    """Verify that oversized request bodies are rejected with 413 Payload Too Large."""
    # Send request with content-length larger than configured max
    res = client.post(
        "/api/v1/targets",
        content="x" * 100,
        headers={"Content-Length": str(20 * 1024 * 1024)},  # 20MB
    )
    assert res.status_code == 413
    assert "Payload too large" in res.json()["message"]


def test_local_api_key_auth(client: TestClient) -> None:
    """Verify optional local token authentication enforcement."""
    with patch("agentbreaker.api.config.api_settings.local_api_key", "secret-local-pass-123"):
        # Without header -> 401
        res_unauth = client.get("/api/v1/targets")
        assert res_unauth.status_code == 401

        # With correct header -> 200
        res_auth = client.get(
            "/api/v1/targets",
            headers={"X-AgentBreaker-Token": "secret-local-pass-123"},
        )
        assert res_auth.status_code == 200
