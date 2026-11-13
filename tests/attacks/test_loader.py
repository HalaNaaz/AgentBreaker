"""Tests for PayloadLoader filesystem discovery and validation."""

from pathlib import Path

import pytest

from agentbreaker.attacks.exceptions import (
    PayloadLoadError,
    PayloadValidationError,
)
from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.attacks.registry import AttackRegistry


def test_loader_from_directory():
    """Verify scanning and loading bundled YAML payloads from payloads/ directory."""
    payloads_dir = Path("payloads")
    loaded = PayloadLoader.load_from_directory(payloads_dir, recursive=True)
    assert len(loaded) >= 6
    assert any(p.id == "JB-001" for p in loaded)
    assert any(p.id == "EXT-001" for p in loaded)
    assert any(p.id == "IND-001" for p in loaded)
    assert any(p.id == "TOOL-001" for p in loaded)


def test_loader_load_into_registry():
    """Verify loading directory directly into an AttackRegistry."""
    registry = AttackRegistry()
    count = PayloadLoader.load_into_registry(Path("payloads"), registry)
    assert count >= 6
    assert registry.count() == count


def test_loader_nonexistent_file():
    """Verify loading nonexistent file raises PayloadLoadError."""
    with pytest.raises(PayloadLoadError, match="not found"):
        PayloadLoader.load_from_file("payloads/nonexistent_file.yaml")


def test_loader_unsupported_extension(tmp_path: Path):
    """Verify unsupported file extensions are rejected."""
    bad_file = tmp_path / "payload.txt"
    bad_file.write_text("id: 123", encoding="utf-8")
    with pytest.raises(PayloadLoadError, match="Unsupported extension"):
        PayloadLoader.load_from_file(bad_file)


def test_loader_empty_file(tmp_path: Path):
    """Verify empty file raises PayloadLoadError."""
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("", encoding="utf-8")
    with pytest.raises(PayloadLoadError, match="is empty"):
        PayloadLoader.load_from_file(empty_file)


def test_loader_malformed_yaml(tmp_path: Path):
    """Verify malformed YAML syntax raises PayloadLoadError."""
    broken_file = tmp_path / "broken.yaml"
    broken_file.write_text("id: [unclosed list", encoding="utf-8")
    with pytest.raises(PayloadLoadError, match="Malformed syntax"):
        PayloadLoader.load_from_file(broken_file)


def test_loader_schema_validation_error(tmp_path: Path):
    """Verify invalid schema content raises PayloadValidationError."""
    invalid_file = tmp_path / "invalid_schema.yaml"
    invalid_file.write_text("id: 'INV'\nname: 'Invalid'", encoding="utf-8")
    with pytest.raises(PayloadValidationError, match="schema validation error"):
        PayloadLoader.load_from_file(invalid_file)
