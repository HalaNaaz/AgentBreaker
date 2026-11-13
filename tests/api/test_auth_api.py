"""Tests for local session authentication, CSRF defense, and WebSocket connection tickets."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from agentbreaker.api.app import create_app
from agentbreaker.api.config import api_settings
from agentbreaker.api.dependencies import (
    get_assessment_service,
    get_storage,
    get_target_service,
)
from agentbreaker.api.services import AssessmentService, TargetService
from agentbreaker.cli.storage import StorageManager
from agentbreaker.schemas.target import TargetConfig


@pytest.fixture
def auth_storage(tmp_path: Path) -> StorageManager:
    mgr = StorageManager(base_dir=tmp_path)
    mgr.targets_dir.mkdir(parents=True, exist_ok=True)
    mgr.assessments_dir.mkdir(parents=True, exist_ok=True)
    return mgr


@pytest.fixture
def client(auth_storage: StorageManager) -> TestClient:
    app = create_app()
    target_svc = TargetService(auth_storage)
    assessment_svc = AssessmentService(auth_storage)

    app.dependency_overrides[get_storage] = lambda: auth_storage
    app.dependency_overrides[get_target_service] = lambda: target_svc
    app.dependency_overrides[get_assessment_service] = lambda: assessment_svc

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_session_lifecycle_and_csrf_protection(client: TestClient) -> None:
    """Verify session creation, cookie generation, CSRF token issuance, and logout."""
    # 1. Inspect initial session status
    status_res = client.get("/api/v1/auth/session")
    assert status_res.status_code == 200

    # 2. Create session
    create_res = client.post("/api/v1/auth/session")
    assert create_res.status_code == 200
    data = create_res.json()
    assert data["authenticated"] is True
    assert data["csrf_token"] is not None
    assert "agentbreaker_session" in client.cookies

    csrf_token = data["csrf_token"]

    # 3. Status now reflects active session
    status_res2 = client.get("/api/v1/auth/session")
    assert status_res2.status_code == 200
    assert status_res2.json()["authenticated"] is True
    assert status_res2.json()["csrf_token"] == csrf_token

    # 4. Logout clears session
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "logged_out"


def test_session_auth_enforcement_with_station_key(
    client: TestClient,
    auth_storage: StorageManager,
) -> None:
    """Verify session login requires correct station key when configured."""
    station_key = "station-guard-secret-passphrase-999"

    with patch.object(api_settings, "local_api_key", station_key):
        # 1. Unauthenticated request to protected endpoint -> 401
        res_unauth = client.get("/api/v1/targets")
        assert res_unauth.status_code == 401

        # 2. Login with wrong token -> 401
        res_bad_login = client.post(
            "/api/v1/auth/session",
            json={"token": "incorrect-token"},
        )
        assert res_bad_login.status_code == 401

        # 3. Login with correct token -> 200 and establishes session
        res_good_login = client.post(
            "/api/v1/auth/session",
            json={"token": station_key},
        )
        assert res_good_login.status_code == 200
        csrf_token = res_good_login.json()["csrf_token"]
        assert "agentbreaker_session" in client.cookies

        # 4. GET requests with session cookie now succeed
        res_targets = client.get("/api/v1/targets")
        assert res_targets.status_code == 200

        # 5. Mutating request without CSRF token -> 403 Forbidden
        res_post_no_csrf = client.post(
            "/api/v1/targets",
            json={
                "target_id": "t-csrf-test",
                "endpoint_url": "http://127.0.0.1:11434/api/generate",
                "target_type": "ollama",
                "model_name": "m",
            },
        )
        assert res_post_no_csrf.status_code == 403
        assert "CSRF" in res_post_no_csrf.json()["detail"]

        # 6. Mutating request with valid CSRF token -> 201 Created
        res_post_with_csrf = client.post(
            "/api/v1/targets",
            headers={"X-CSRF-Token": csrf_token},
            json={
                "target_id": "t-csrf-test",
                "endpoint_url": "http://127.0.0.1:11434/api/generate",
                "target_type": "ollama",
                "model_name": "m",
            },
        )
        assert res_post_with_csrf.status_code == 201


def test_websocket_single_use_ticket_flow(
    client: TestClient,
    auth_storage: StorageManager,
) -> None:
    """Verify single-use ticket issuance, binding to assessment, and immediate consumption."""
    station_key = "station-key-for-ws-ticket"
    asm_id = "ASM-TICKET-TEST"

    auth_storage.save_target(
        "t1",
        TargetConfig(
            endpoint_url="http://127.0.0.1:11434/api/generate",
            model_name="m",
        ),
    )
    auth_storage.save_assessment(
        {
            "id": asm_id,
            "name": "Ticket Test",
            "target_id": "t1",
            "status": "PENDING",
        }
    )

    with patch.object(api_settings, "local_api_key", station_key):
        # 1. Authenticate session
        login_res = client.post("/api/v1/auth/session", json={"token": station_key})
        csrf_token = login_res.json()["csrf_token"]

        # 2. Request single-use ticket
        ticket_res = client.post(
            "/api/v1/auth/ws-ticket",
            headers={"X-CSRF-Token": csrf_token},
            json={"assessment_id": asm_id},
        )
        assert ticket_res.status_code == 200
        ticket = ticket_res.json()["ticket"]
        assert ticket is not None

        # 3. Connect to WebSocket with ticket -> succeeds!
        with client.websocket_connect(f"/api/v1/assessments/{asm_id}/events?ticket={ticket}") as ws:
            assert ws is not None

        # 4. Attempt to RE-USE ticket -> rejected (ticket consumed)
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/api/v1/assessments/{asm_id}/events?ticket={ticket}"):
                pass
        assert exc_info.value.code == 4001
