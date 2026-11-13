"""Tests for AttackRegistry catalog and filtering."""

import pytest

from agentbreaker.attacks.exceptions import AttackRegistryError
from agentbreaker.attacks.registry import AttackRegistry
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload


def test_registry_register_and_get(sample_payload: AttackPayload):
    """Verify registering a payload and retrieving it by ID."""
    registry = AttackRegistry()
    registry.register(sample_payload)

    assert registry.count() == 1
    retrieved = registry.get(sample_payload.id)
    assert retrieved.id == sample_payload.id
    assert retrieved.name == sample_payload.name


def test_registry_duplicate_rejection(sample_payload: AttackPayload):
    """Verify duplicate payload ID raises AttackRegistryError."""
    registry = AttackRegistry()
    registry.register(sample_payload)

    with pytest.raises(AttackRegistryError, match="Duplicate payload ID"):
        registry.register(sample_payload)


def test_registry_missing_item_raises():
    """Verify retrieving nonexistent ID raises AttackRegistryError."""
    registry = AttackRegistry()
    with pytest.raises(AttackRegistryError, match="not registered"):
        registry.get("NONEXISTENT-999")


def test_registry_filtering():
    """Verify category, tag, severity, and OWASP filtering."""
    registry = AttackRegistry()

    p1 = AttackPayload(
        id="JB-001",
        name="Jailbreak 1",
        category=AttackCategory.DIRECT_JAILBREAK,
        owasp_id="LLM01: Prompt Injection",
        severity=Severity.HIGH,
        description="Jailbreak test",
        payload_template="Test 1",
        tags=["roleplay", "test"],
    )
    p2 = AttackPayload(
        id="EXT-001",
        name="Extraction 1",
        category=AttackCategory.SYSTEM_EXTRACTION,
        owasp_id="LLM07: System Prompt Leakage",
        severity=Severity.CRITICAL,
        description="Extraction test",
        payload_template="Test 2",
        tags=["canary"],
    )

    registry.register_many([p1, p2])

    assert len(registry.filter_by_category(AttackCategory.DIRECT_JAILBREAK)) == 1
    assert len(registry.filter_by_category("system_extraction")) == 1
    assert len(registry.filter_by_tag("canary")) == 1
    assert len(registry.filter_by_severity(Severity.CRITICAL)) == 1
    assert len(registry.filter_by_owasp("LLM01")) == 1
    assert registry.categories() == {
        AttackCategory.DIRECT_JAILBREAK,
        AttackCategory.SYSTEM_EXTRACTION,
    }

    registry.clear()
    assert registry.count() == 0


def test_registry_invalid_item_type():
    """Verify registering invalid item type raises AttackRegistryError."""
    registry = AttackRegistry()
    with pytest.raises(AttackRegistryError, match="Unsupported item type"):
        registry.register("invalid_string_not_payload")  # type: ignore
