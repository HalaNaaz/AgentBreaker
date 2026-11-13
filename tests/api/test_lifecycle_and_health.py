"""Tests for FastAPI lifecycle, health probes, system diagnostic, and settings endpoints."""

from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient) -> None:
    """Verify GET /health and GET /api/v1/health return consistent operational status."""
    for path in ("/health", "/api/v1/health"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0.dev1"
        assert data["runtime_status"] == "healthy"
        assert data["storage_available"] is True
        assert data["engine_available"] is True
        assert "timestamp" in data


def test_system_info_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/system/info exposes platform metadata without credentials."""
    res = client.get("/api/v1/system/info")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "AgentBreaker"
    assert data["organization"] == "AshlynxCyber"
    assert "Python" in data["python_runtime"]
    assert len(data["registered_connectors"]) >= 2
    assert "direct_jailbreak" in data["attack_categories"]
    assert "rot13" in data["mutation_strategies"]
    assert "json" in data["report_formats"]


def test_system_status_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/system/status telemetry."""
    res = client.get("/api/v1/system/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ONLINE"
    assert data["storage_ready"] is True
    assert data["active_assessments_count"] == 0
    assert isinstance(data["running_task_ids"], list)


def test_system_capabilities_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/system/capabilities."""
    res = client.get("/api/v1/system/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["attack_engine"] is True
    assert data["mutation_engine"] is True
    assert data["evaluation_oracle"] is True
    assert data["reporting_engine"] is True
    assert data["websockets_live_events"] is True
    assert "OWASP Top 10 for LLMs 2025" in data["supported_frameworks"]


def test_settings_endpoint(client: TestClient) -> None:
    """Verify GET /api/v1/settings returns sanitized server settings."""
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["api_host"] == "127.0.0.1"
    assert data["api_port"] == 8000
    assert "http://127.0.0.1:3000" in data["cors_origins"]
    assert data["max_request_size_bytes"] > 0
    assert "storage_root" in data
