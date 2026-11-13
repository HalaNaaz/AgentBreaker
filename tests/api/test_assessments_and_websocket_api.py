"""Tests for assessment lifecycle, background execution, status polling, and WebSocket streaming."""

import asyncio
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def test_assessment_creation_and_authorization(client: TestClient) -> None:
    """Verify assessment creation requires an existing authorized target."""
    # 1. Attempt creating assessment for unauthorized/nonexistent target -> 403 Forbidden
    res_unauth = client.post(
        "/api/v1/assessments",
        json={"name": "Bad Target Run", "target_id": "unconfigured-target"},
    )
    assert res_unauth.status_code == 403

    # 2. Provision target first
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "target-asm-01",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
        },
    )

    # 3. Create assessment
    res_ok = client.post(
        "/api/v1/assessments",
        json={
            "name": "Integration Assessment #1",
            "target_id": "target-asm-01",
            "attack_categories": ["direct_jailbreak"],
            "enable_mutation": False,
        },
    )
    assert res_ok.status_code == 201
    created = res_ok.json()
    assert created["assessment_id"].startswith("ASM-")
    assert created["status"] == "CONFIGURED"
    assert created["target_id"] == "target-asm-01"

    # 4. List assessments
    list_res = client.get("/api/v1/assessments")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 5. Get assessment
    get_res = client.get(f"/api/v1/assessments/{created['assessment_id']}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Integration Assessment #1"


def test_assessment_start_and_status(client: TestClient) -> None:
    """Verify starting background assessment execution and polling status."""
    # Setup target & assessment
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "target-run-01",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
        },
    )
    asm_res = client.post(
        "/api/v1/assessments",
        json={"name": "Async Run Test", "target_id": "target-run-01"},
    )
    asm_id = asm_res.json()["assessment_id"]

    mock_results = [
        EvaluationResult(
            payload_id="P-01",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
        )
    ]
    mock_summary = {
        "assessment_id": asm_id,
        "target_id": "target-run-01",
        "total_payloads": 1,
        "completed_payloads": 1,
        "vulnerable_count": 0,
        "defended_count": 1,
        "inconclusive_count": 0,
    }

    with patch(
        "agentbreaker.cli.orchestration.AssessmentOrchestrator.execute_assessment",
        new=AsyncMock(return_value=(mock_results, mock_summary)),
    ):
        start_res = client.post(f"/api/v1/assessments/{asm_id}/start")
        assert start_res.status_code == 200
        data = start_res.json()
        assert data["assessment_id"] == asm_id

        # Polling status
        status_res = client.get(f"/api/v1/assessments/{asm_id}/status")
        assert status_res.status_code == 200
        assert status_res.json()["assessment_id"] == asm_id


def test_assessment_duplicate_start_conflict(client: TestClient) -> None:
    """Verify attempting to start an already running assessment raises 409 Conflict."""
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "target-conflict",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
        },
    )
    asm_res = client.post(
        "/api/v1/assessments",
        json={"name": "Conflict Run Test", "target_id": "target-conflict"},
    )
    asm_id = asm_res.json()["assessment_id"]

    # Mock long-running orchestrator that hangs until cancelled
    async def slow_execute(*_args, **_kwargs):
        await asyncio.sleep(10.0)
        return [], {}

    with patch(
        "agentbreaker.cli.orchestration.AssessmentOrchestrator.execute_assessment",
        new=slow_execute,
    ):
        start_res = client.post(f"/api/v1/assessments/{asm_id}/start")
        assert start_res.status_code == 200

        # Immediate second start attempt
        second_start = client.post(f"/api/v1/assessments/{asm_id}/start")
        assert second_start.status_code == 409

        # Clean cancel
        cancel_res = client.post(f"/api/v1/assessments/{asm_id}/cancel")
        assert cancel_res.status_code == 200


def test_assessment_websocket_streaming(client: TestClient) -> None:
    """Verify WebSocket connection receives structured progress events."""
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "target-ws",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
        },
    )
    asm_res = client.post(
        "/api/v1/assessments",
        json={"name": "WebSocket Test", "target_id": "target-ws"},
    )
    asm_id = asm_res.json()["assessment_id"]

    # Connect WebSocket
    with client.websocket_connect(f"/api/v1/assessments/{asm_id}/events") as websocket:
        # Broadcast test event via ws_manager
        from agentbreaker.api.websocket.events import event_payload_progress
        from agentbreaker.api.websocket.manager import ws_manager

        test_evt = event_payload_progress(asm_id, current=1, total=5, payload_id="P-01")
        asyncio.run(ws_manager.broadcast(asm_id, test_evt))

        received = websocket.receive_json()
        assert received["event_type"] == "payload.completed"
        assert received["assessment_id"] == asm_id
        assert received["data"]["payload_id"] == "P-01"
        assert received["data"]["percent"] == 20.0
