"""Tests for attack payload library browsing and mutation preview endpoints."""

from fastapi.testclient import TestClient


def test_payloads_list_and_pagination(client: TestClient) -> None:
    """Verify browsing bundled attack vectors with filters and pagination."""
    # List all
    res = client.get("/api/v1/payloads?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 20
    assert len(data["items"]) == 10
    first = data["items"][0]
    assert "id" in first
    assert "category" in first
    assert "severity" in first

    # Filter by category
    cat_res = client.get("/api/v1/payloads?category=direct_jailbreak")
    assert cat_res.status_code == 200
    cat_data = cat_res.json()
    for item in cat_data["items"]:
        assert item["category"] == "direct_jailbreak"

    # Search filter
    search_res = client.get("/api/v1/payloads?search=dan")
    assert search_res.status_code == 200
    assert search_res.json()["total"] >= 1


def test_payloads_categories(client: TestClient) -> None:
    """Verify GET /api/v1/payloads/categories returns category counts."""
    res = client.get("/api/v1/payloads/categories")
    assert res.status_code == 200
    cats = res.json()
    assert len(cats) == 4
    names = [c["category"] for c in cats]
    assert "direct_jailbreak" in names
    assert "system_extraction" in names
    assert "indirect_injection" in names
    assert "tool_hijacking" in names


def test_payload_detail(client: TestClient) -> None:
    """Verify GET /api/v1/payloads/{id} returns full schema definition."""
    # First get a valid payload id
    list_res = client.get("/api/v1/payloads?page_size=1")
    p_id = list_res.json()["items"][0]["id"]

    res = client.get(f"/api/v1/payloads/{p_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == p_id
    assert "payload_template" in data
    assert "evaluator_rules" in data

    # 404 for missing payload
    assert client.get("/api/v1/payloads/NONEXISTENT_PAYLOAD").status_code == 404


def test_payload_validate_endpoint(client: TestClient) -> None:
    """Verify POST /api/v1/payloads/validate validates payload schema."""
    valid_payload = {
        "id": "VALID-01",
        "name": "Custom Test Vector",
        "category": "direct_jailbreak",
        "owasp_id": "LLM01: Prompt Injection",
        "description": "Custom test vector for payload validation endpoint testing.",
        "severity": "HIGH",
        "payload_template": "Test prompt text",
    }
    res = client.post("/api/v1/payloads/validate", json=valid_payload)
    assert res.status_code == 200
    assert res.json()["valid"] is True

    invalid_payload = {"invalid_only": True}
    res_bad = client.post("/api/v1/payloads/validate", json=invalid_payload)
    assert res_bad.status_code == 200
    assert res_bad.json()["valid"] is False


def test_mutations_strategies_list(client: TestClient) -> None:
    """Verify GET /api/v1/mutations/strategies returns available strategies."""
    res = client.get("/api/v1/mutations/strategies")
    assert res.status_code == 200
    strats = res.json()
    strat_ids = [s["id"] for s in strats]
    assert "rot13" in strat_ids
    assert "base64" in strat_ids
    assert "leetspeak" in strat_ids
    assert "markdown_obfuscation" in strat_ids


def test_mutations_preview(client: TestClient) -> None:
    """Verify POST /api/v1/mutations/preview generates variants without dispatching."""
    list_res = client.get("/api/v1/payloads?page_size=1")
    p_id = list_res.json()["items"][0]["id"]

    res = client.post(
        "/api/v1/mutations/preview",
        json={
            "payload_id": p_id,
            "strategies": ["rot13", "base64"],
            "max_variants": 2,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["original_payload_id"] == p_id
    assert len(data["generated_variants"]) == 2
    for var in data["generated_variants"]:
        assert var["parent_id"] == p_id
        assert "mutated_prompt" in var
        assert var["strategy"] in ("rot13", "base64")
