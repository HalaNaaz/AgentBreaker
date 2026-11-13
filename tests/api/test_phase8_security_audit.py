"""Phase 8 Independent Security & Quality Audit Test Suite.

Rigorously verifies:
1. Authentication & authorization bypass resistance.
2. WebSocket channel isolation, auth rejection, malformed ID rejection, and connection bounding.
3. Zero credential disclosure across models, responses, and serializations.
4. SSRF and cloud metadata boundary enforcement.
5. Path traversal, null byte, and Windows reserved name rejection.
6. DNS rebinding & Host header validation.
7. Request size limiter & DoS prevention.
8. Error information disclosure prevention (no stack traces or internal paths in 500s).
9. Background task lifecycle, duplicate start conflicts, and cleanup.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from agentbreaker.api.app import create_app
from agentbreaker.api.config import api_settings
from agentbreaker.api.dependencies import (
    get_analytics_service,
    get_assessment_service,
    get_finding_service,
    get_reporting_service,
    get_storage,
    get_target_service,
)
from agentbreaker.api.schemas.events import AssessmentEvent
from agentbreaker.api.services import (
    AnalyticsService,
    APIReportingService,
    AssessmentService,
    FindingService,
    TargetService,
)
from agentbreaker.api.websocket.manager import WebSocketManager, ws_manager
from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def audit_storage(tmp_path: Path) -> StorageManager:
    """Provide isolated storage for audit tests."""
    mgr = StorageManager(base_dir=tmp_path)
    mgr.targets_dir.mkdir(parents=True, exist_ok=True)
    mgr.assessments_dir.mkdir(parents=True, exist_ok=True)
    mgr.results_dir.mkdir(parents=True, exist_ok=True)
    mgr.reports_dir.mkdir(parents=True, exist_ok=True)
    return mgr


@pytest.fixture
def audit_client(audit_storage: StorageManager) -> TestClient:
    """Provide isolated TestClient with dependency overrides."""
    app = create_app()

    target_svc = TargetService(audit_storage)
    assessment_svc = AssessmentService(audit_storage)
    finding_svc = FindingService(audit_storage)
    reporting_svc = APIReportingService(audit_storage)
    analytics_svc = AnalyticsService(audit_storage)

    app.dependency_overrides[get_storage] = lambda: audit_storage
    app.dependency_overrides[get_target_service] = lambda: target_svc
    app.dependency_overrides[get_assessment_service] = lambda: assessment_svc
    app.dependency_overrides[get_finding_service] = lambda: finding_svc
    app.dependency_overrides[get_reporting_service] = lambda: reporting_svc
    app.dependency_overrides[get_analytics_service] = lambda: analytics_svc

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# ==============================================================================
# 1. AUTHENTICATION & AUTHORIZATION AUDIT
# ==============================================================================


def test_audit_auth_enforcement_when_key_configured(audit_client: TestClient) -> None:
    """Verify that when local_api_key is configured, unauthenticated requests are rejected."""
    with patch.object(api_settings, "local_api_key", "secret-pre-shared-token-xyz"):
        # 1. Target creation without auth -> 401
        res = audit_client.get("/api/v1/targets")
        assert res.status_code == 401
        assert "Invalid or missing" in res.json()["detail"]

        # 2. Assessment creation without auth -> 401
        res_asm = audit_client.post(
            "/api/v1/assessments",
            json={"assessment_id": "ASM-X", "name": "X", "target_id": "T1"},
        )
        assert res_asm.status_code == 401

        # 3. System status without auth -> 401
        res_sys = audit_client.get("/api/v1/system/status")
        assert res_sys.status_code == 401

        # 4. Reports without auth -> 401
        res_rpt = audit_client.get("/api/v1/reports")
        assert res_rpt.status_code == 401

        # 5. Invalid token -> 401
        res_invalid = audit_client.get(
            "/api/v1/targets",
            headers={"X-AgentBreaker-Token": "wrong-token"},
        )
        assert res_invalid.status_code == 401

        # 6. Valid token via X-AgentBreaker-Token -> 200
        res_valid_hdr = audit_client.get(
            "/api/v1/targets",
            headers={"X-AgentBreaker-Token": "secret-pre-shared-token-xyz"},
        )
        assert res_valid_hdr.status_code == 200

        # 7. Valid token via Bearer header -> 200
        res_valid_bearer = audit_client.get(
            "/api/v1/targets",
            headers={"Authorization": "Bearer secret-pre-shared-token-xyz"},
        )
        assert res_valid_bearer.status_code == 200


# ==============================================================================
# 2. WEBSOCKET SECURITY & ISOLATION AUDIT
# ==============================================================================


def test_audit_websocket_unauthenticated_connection_rejected(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify that WebSocket rejects unauthenticated connections when local_api_key is set."""
    asm_id = "ASM-WS-AUTH"
    audit_storage.save_assessment(
        {"id": asm_id, "name": "Auth Test", "target_id": "t1", "status": "PENDING"}
    )

    with patch.object(api_settings, "local_api_key", "ws-guard-key-123"):
        # Without token -> rejected (code 4001)
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with audit_client.websocket_connect(f"/api/v1/assessments/{asm_id}/events"):
                pass
        assert exc_info.value.code == 4001

        # With invalid token -> rejected (code 4001)
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with audit_client.websocket_connect(
                f"/api/v1/assessments/{asm_id}/events?token=bad-token"
            ):
                pass
        assert exc_info.value.code == 4001

        # With valid token query param -> successfully connects
        with audit_client.websocket_connect(
            f"/api/v1/assessments/{asm_id}/events?token=ws-guard-key-123"
        ) as ws:
            assert ws is not None


def test_audit_websocket_malformed_and_missing_id_rejection(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify WebSocket rejects path traversal and non-existent assessment IDs."""
    # 1. Non-existent assessment -> rejected (code 4004)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with audit_client.websocket_connect("/api/v1/assessments/NON_EXISTENT_ID/events"):
            pass
    assert exc_info.value.code == 4004

    # 2. Malformed / injection syntax in ID -> rejected (code 4000)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with audit_client.websocket_connect("/api/v1/assessments/bad;id$traversal/events"):
            pass
    assert exc_info.value.code == 4000

    # 3. Path traversal sequence in ID -> rejected with WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with audit_client.websocket_connect("/api/v1/assessments/..%2F..%2Fetc/events"):
            pass
    assert exc_info.value.code in (1000, 4000)


def test_audit_websocket_cross_assessment_isolation(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify strictly zero event leakage between different assessment WebSocket channels."""
    import asyncio

    asm1 = "ASM-ISO-01"
    asm2 = "ASM-ISO-02"
    audit_storage.save_assessment(
        {"id": asm1, "name": "Run 1", "target_id": "t1", "status": "PENDING"}
    )
    audit_storage.save_assessment(
        {"id": asm2, "name": "Run 2", "target_id": "t1", "status": "PENDING"}
    )

    # Connect client to asm1
    with audit_client.websocket_connect(f"/api/v1/assessments/{asm1}/events") as ws1:
        # Broadcast event specifically to asm2
        evt2 = AssessmentEvent(
            assessment_id=asm2,
            event_type="payload.completed",
            data={"secret_probe": "ASM2_CONFIDENTIAL_EVENT"},
        )
        asyncio.run(ws_manager.broadcast(asm2, evt2))

        # Broadcast event to asm1
        evt1 = AssessmentEvent(
            assessment_id=asm1,
            event_type="payload.completed",
            data={"expected_probe": "ASM1_SAFE_EVENT"},
        )
        asyncio.run(ws_manager.broadcast(asm1, evt1))

        # Client 1 must receive ONLY evt1, never evt2!
        received = ws1.receive_json()
        assert received["assessment_id"] == asm1
        assert received["data"]["expected_probe"] == "ASM1_SAFE_EVENT"


def test_audit_websocket_connection_limits(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify WebSocket rejects excessive concurrent connections exceeding the safety limit."""
    asm = "ASM-LIMIT-TEST"
    audit_storage.save_assessment(
        {"id": asm, "name": "Limit Test", "target_id": "t1", "status": "PENDING"}
    )

    with patch.object(WebSocketManager, "MAX_CONNECTIONS_PER_ASSESSMENT", 2):
        with audit_client.websocket_connect(f"/api/v1/assessments/{asm}/events"):
            with audit_client.websocket_connect(f"/api/v1/assessments/{asm}/events"):
                # 3rd connection exceeds MAX_CONNECTIONS_PER_ASSESSMENT=2 -> rejected (4029)
                with pytest.raises(WebSocketDisconnect) as exc_info:
                    with audit_client.websocket_connect(f"/api/v1/assessments/{asm}/events"):
                        pass
                assert exc_info.value.code == 4029


# ==============================================================================
# 3. CREDENTIAL & SECRET DISCLOSURE AUDIT
# ==============================================================================


def test_audit_zero_secret_disclosure_in_api(audit_client: TestClient) -> None:
    """Verify raw API keys are never exposed in target GET, LIST, or error responses."""
    plaintext_key = "sk-super-secret-production-token-9876543210"

    # 1. Create target with secret
    create_res = audit_client.post(
        "/api/v1/targets",
        json={
            "target_id": "audit-secure-target",
            "endpoint_url": "http://127.0.0.1:11434/api/generate",
            "target_type": "ollama",
            "model_name": "llama3:latest",
            "api_key": plaintext_key,
            "headers": {"Authorization": f"Bearer {plaintext_key}"},
        },
    )
    assert create_res.status_code == 201
    created_text = create_res.text
    # Plaintext must never appear in response
    assert plaintext_key not in created_text
    assert "sk-" in created_text
    assert "..." in created_text

    # 2. Get target
    get_res = audit_client.get("/api/v1/targets/audit-secure-target")
    assert plaintext_key not in get_res.text

    # 3. List targets
    list_res = audit_client.get("/api/v1/targets")
    assert plaintext_key not in list_res.text


# ==============================================================================
# 4. NETWORK BOUNDARY & SSRF REGRESSION AUDIT
# ==============================================================================


def test_audit_cloud_metadata_and_ssrf_rejection(audit_client: TestClient) -> None:
    """Verify cloud metadata addresses (169.254.169.254, 0.0.0.0) are strictly rejected."""
    forbidden_urls = [
        "http://169.254.169.254/latest/meta-data/",
        "http://[fd00:ec2::254]/latest/meta-data/",
        "http://100.100.100.200/latest/meta-data/",
        "http://0.0.0.0:8000/api",
        "http://[::]:8080/probe",
    ]

    for bad_url in forbidden_urls:
        res = audit_client.post(
            "/api/v1/targets",
            json={
                "target_id": "ssrf-test",
                "endpoint_url": bad_url,
                "target_type": "openai_compatible",
                "model_name": "gpt-4o",
            },
        )
        assert res.status_code == 422
        assert "Invalid target configuration" in res.json()["message"]


# ==============================================================================
# 5. DATA INTEGRITY & PATH TRAVERSAL DEFENSE AUDIT
# ==============================================================================


def test_audit_path_traversal_rejections(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify directory traversal, null bytes, and Windows reserved device names are blocked."""
    traversal_filenames = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\cmd.exe",
        "valid_report.json%00evil.exe",
        "CON.json",
        "PRN.md",
        "AUX.html",
        "NUL.txt",
    ]

    for filename in traversal_filenames:
        res = audit_client.get(f"/api/v1/reports/{filename}/download")
        # Traversal and invalid characters are blocked by 422 or 404
        assert res.status_code in (404, 422)
        assert "etc/passwd" not in res.text


# ==============================================================================
# 6. DNS REBINDING & HOST HEADER AUDIT
# ==============================================================================


def test_audit_dns_rebinding_host_header_validation(audit_client: TestClient) -> None:
    """Verify requests with untrusted Host headers (DNS rebinding) are rejected with HTTP 400."""
    # Valid host: 127.0.0.1
    res_valid = audit_client.get("/health", headers={"Host": "127.0.0.1:8000"})
    assert res_valid.status_code == 200

    # Malicious host: attacker.com (DNS rebind attempt)
    res_invalid = audit_client.get("/health", headers={"Host": "attacker.com"})
    assert res_invalid.status_code == 400


# ==============================================================================
# 7. REQUEST SIZE LIMITER & DoS AUDIT
# ==============================================================================


def test_audit_request_size_limiter(audit_client: TestClient) -> None:
    """Verify oversized requests (>10MB) are rejected with HTTP 413 Payload Too Large."""
    # Attempting request with Content-Length larger than 10MB limit
    headers = {"Content-Length": str(15 * 1024 * 1024)}  # 15 MB
    res = audit_client.post(
        "/api/v1/targets",
        headers=headers,
        content=b"x" * 100,  # Simulated large body
    )
    assert res.status_code == 413
    assert res.json()["type"] == "PayloadTooLarge"


# ==============================================================================
# 8. ERROR INFORMATION DISCLOSURE AUDIT
# ==============================================================================


def test_audit_generic_exception_zero_system_leakage() -> None:
    """Verify unhandled 500 exceptions do not disclose internal tracebacks or paths."""
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    with patch(
        "agentbreaker.api.services.target_service.TargetService.list_targets",
        side_effect=RuntimeError("CRITICAL: C:\\Secret\\Path\\DB_CONN_FAILED password=admin123"),
    ):
        res = client.get("/api/v1/targets")
        assert res.status_code == 500
        # Traceback and internal arguments must NEVER appear
        assert "C:\\Secret\\Path" not in res.text
        assert "admin123" not in res.text
        assert res.json()["message"] == "An unexpected internal server error occurred."


# ==============================================================================
# 9. ASSESSMENT BACKGROUND CONCURRENCY & CANCEL AUDIT
# ==============================================================================


def test_audit_duplicate_start_conflict_prevention(
    audit_client: TestClient,
    audit_storage: StorageManager,
) -> None:
    """Verify duplicate background starts of the same assessment are blocked
    with HTTP 409 Conflict.
    """
    asm_id = "ASM-CONFLICT-AUDIT"
    audit_storage.save_target(
        "t-mock",
        TargetConfig(
            endpoint_url="http://127.0.0.1:11434/api/generate",
            model_name="m",
        ),
    )
    audit_storage.save_assessment(
        {
            "id": asm_id,
            "name": "Audit Run",
            "target_id": "t-mock",
            "status": "PENDING",
            "categories": ["direct_jailbreak"],
            "payload_ids": ["EXT-007"],
        }
    )

    import asyncio

    async def slow_execution(*args, **kwargs):
        await asyncio.sleep(1.0)
        return [], {}

    with patch(
        "agentbreaker.api.services.assessment_service.AssessmentOrchestrator.execute_assessment",
        side_effect=slow_execution,
    ):
        # 1. Start assessment
        res1 = audit_client.post(f"/api/v1/assessments/{asm_id}/start")
        assert res1.status_code == 200

        # 2. Duplicate start while active -> 409 Conflict
        res2 = audit_client.post(f"/api/v1/assessments/{asm_id}/start")
        assert res2.status_code == 409
        assert "already actively executing" in res2.json()["message"]

        # 3. Clean cancel
        cancel_res = audit_client.post(f"/api/v1/assessments/{asm_id}/cancel")
        assert cancel_res.status_code == 200
