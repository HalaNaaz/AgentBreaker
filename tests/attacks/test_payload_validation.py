"""Tests validating the integrity, schema compliance, and safety of bundled payloads."""

from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from agentbreaker.attacks.exceptions import PayloadLoadError
from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.schemas.payload import AttackPayload


def test_bundled_payloads_schema_and_safety_validation():
    """Verify all bundled YAML files in payloads/ pass strict validation and safety requirements."""
    payloads_dir = Path("payloads")
    payloads = PayloadLoader.load_from_directory(payloads_dir, recursive=True)

    assert len(payloads) >= 30, f"Expected at least 30 payloads, found {len(payloads)}"

    counts = Counter(p.category.value for p in payloads)
    assert counts["direct_jailbreak"] >= 8
    assert counts["system_extraction"] >= 7
    assert counts["indirect_injection"] >= 8
    assert counts["tool_hijacking"] >= 7

    seen_ids = set()
    for p in payloads:
        # 1. Uniqueness of ID
        assert p.id not in seen_ids, f"Duplicate payload ID found: {p.id}"
        seen_ids.add(p.id)

        # 2. Strict ID pattern
        assert p.id.isalnum() or "-" in p.id or "_" in p.id

        # 3. Non-destructive safety invariant
        assert p.is_destructive is False

        # 4. Required fields
        assert len(p.name) >= 3
        assert len(p.description) >= 5
        assert len(p.payload_template) >= 1
        assert p.category in {
            "direct_jailbreak",
            "system_extraction",
            "indirect_injection",
            "tool_hijacking",
        }
        assert "LLM" in p.owasp_id


def test_payload_invalid_id_rejected():
    """Verify payload with invalid ID format is rejected."""
    with pytest.raises(ValidationError):
        AttackPayload(
            id="bad id!!",
            name="Bad ID",
            category="direct_jailbreak",  # type: ignore
            owasp_id="LLM01",
            description="Testing invalid ID rejection",
            payload_template="Test",
        )


def test_loader_rejects_oversized_payload(tmp_path: Path):
    """Verify PayloadLoader rejects files exceeding MAX_PAYLOAD_FILE_BYTES."""
    oversized = tmp_path / "oversized.yaml"
    oversized.write_text("a" * (PayloadLoader.MAX_PAYLOAD_FILE_BYTES + 10), encoding="utf-8")

    with pytest.raises(PayloadLoadError, match="exceeds maximum size"):
        PayloadLoader.load_from_file(oversized)
