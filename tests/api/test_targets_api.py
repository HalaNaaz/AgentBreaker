"""Tests for Target management, validation, and connectivity testing API."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from agentbreaker.schemas.target import TargetResponse


def test_target_crud_lifecycle(client: TestClient) -> None:
    """Verify complete CRUD lifecycle for target endpoints."""
    # 1. List targets (empty initially)
    res = client.get("/api/v1/targets")
    assert res.status_code == 200
    assert res.json() == []

    # 2. Create target
    payload = {
        "target_id": "test-ollama-local",
        "endpoint_url": "http://127.0.0.1:11434/api/generate",
        "target_type": "ollama",
        "model_name": "llama3:latest",
        "api_key": "sk-secret-token-key-1234567890",
        "headers": {"X-Custom": "secure-val"},
        "timeout_seconds": 25.0,
        "max_concurrency": 4,
    }
    create_res = client.post("/api/v1/targets", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["target_id"] == "test-ollama-local"
    assert created["endpoint_url"] == "http://127.0.0.1:11434/api/generate"
    assert created["target_type"] == "ollama"
    # Secret must be masked!
    assert "sk-secret-token-key-1234567890" not in created["api_key_masked"]
    assert "..." in created["api_key_masked"]
    assert created["headers_keys"] == ["X-Custom"]

    # 3. Get target
    get_res = client.get("/api/v1/targets/test-ollama-local")
    assert get_res.status_code == 200
    assert get_res.json()["target_id"] == "test-ollama-local"

    # 4. Update target
    patch_res = client.patch(
        "/api/v1/targets/test-ollama-local",
        json={"timeout_seconds": 45.0, "max_concurrency": 8},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["timeout_seconds"] == 45.0
    assert updated["max_concurrency"] == 8

    # 5. Delete target
    del_res = client.delete("/api/v1/targets/test-ollama-local")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 6. Verify 404 after deletion
    assert client.get("/api/v1/targets/test-ollama-local").status_code == 404


def test_target_creation_security_rejections(client: TestClient) -> None:
    """Verify target validation blocks cloud metadata and invalid schemes."""
    # Rejection of AWS metadata IP
    res1 = client.post(
        "/api/v1/targets",
        json={
            "target_id": "evil-metadata",
            "endpoint_url": "http://169.254.169.254/latest/meta-data/",
            "target_type": "openai_compatible",
            "model_name": "model",
        },
    )
    assert res1.status_code == 422

    # Rejection of non-http scheme
    res2 = client.post(
        "/api/v1/targets",
        json={
            "target_id": "evil-ftp",
            "endpoint_url": "ftp://example.com/api",
            "target_type": "openai_compatible",
            "model_name": "model",
        },
    )
    assert res2.status_code == 422


def test_target_validate_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/targets/{id}/validate checks parameters."""
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "valid-target",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
            "timeout_seconds": 120.0,  # Generates warning (>60s)
        },
    )

    res = client.post("/api/v1/targets/valid-target/validate")
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert len(data["warnings"]) > 0


def test_target_test_connection_mocked(client: TestClient) -> None:
    """Verify POST /api/v1/targets/{id}/test invokes connector probe."""
    client.post(
        "/api/v1/targets",
        json={
            "target_id": "probe-target",
            "endpoint_url": "http://127.0.0.1:8000/v1",
            "target_type": "openai_compatible",
            "model_name": "test-model",
        },
    )

    mock_resp = TargetResponse(
        raw_content="Pong! Diagnostic probe received.",
        status_code=200,
        latency_ms=12.5,
    )

    with patch(
        "agentbreaker.connectors.openai_compatible.OpenAICompatibleConnector.send_prompt",
        new=AsyncMock(return_value=mock_resp),
    ):
        res = client.post("/api/v1/targets/probe-target/test")
        assert res.status_code == 200
        data = res.json()
        assert data["connected"] is True
        assert data["status_code"] == 200
        assert "succeeded" in data["message"]
