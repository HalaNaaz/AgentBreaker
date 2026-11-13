"""Tests for secret redaction, string sanitization, and path safety enforcement."""

from pathlib import Path

import pytest

from agentbreaker.reporting.exceptions import InvalidReportPathError
from agentbreaker.reporting.redaction import (
    escape_html,
    redact_dict,
    redact_string,
    validate_report_path,
)


def test_redact_string_api_keys() -> None:
    """Verify that OpenAI and other API keys are redacted from strings."""
    raw = (
        "Target key: sk-abcdef123456789012345678 and token: "
        "ghp_123456789012345678901234567890123456."
    )
    redacted = redact_string(raw)
    assert "sk-abcdef" not in redacted
    assert "ghp_" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_string_bearer_tokens() -> None:
    """Verify Authorization Bearer tokens are scrubbed."""
    raw = "Request failed with header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token"
    redacted = redact_string(raw)
    assert "Bearer [REDACTED_TOKEN]" in redacted
    assert "eyJhbGciOiJI" not in redacted


def test_redact_dict_sensitive_keys() -> None:
    """Verify sensitive dictionary keys and values are recursively redacted."""
    sensitive_data = {
        "target_id": "test_target",
        "api_key": "super-secret-key-12345",
        "headers": {
            "Authorization": "Bearer token123456789",
            "Content-Type": "application/json",
            "x-custom-secret": "classified",
        },
        "safe_list": ["safe item", "leak: sk-secret-token-key-999999999999"],
    }
    cleaned = redact_dict(sensitive_data)
    assert cleaned["target_id"] == "test_target"
    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["headers"]["Authorization"] == "[REDACTED]"
    assert cleaned["headers"]["x-custom-secret"] == "[REDACTED]"
    assert cleaned["headers"]["Content-Type"] == "application/json"
    assert "[REDACTED_SECRET]" in cleaned["safe_list"][1]


def test_escape_html_xss_prevention() -> None:
    """Verify that dangerous script and HTML tags are safely escaped."""
    malicious = '<script>alert("pwned")</script><img src="x" onerror="evil()">'
    escaped = escape_html(malicious)
    assert "<script>" not in escaped
    assert "&lt;script&gt;" in escaped
    assert "&quot;evil()&quot;" in escaped


def test_validate_report_path_safe(tmp_path: Path) -> None:
    """Verify that safe relative and absolute paths within base directory succeed."""
    safe_target = tmp_path / "reports" / "report.json"
    resolved = validate_report_path(safe_target, base_dir=tmp_path)
    assert resolved == safe_target.resolve()


def test_validate_report_path_escape_rejected(tmp_path: Path) -> None:
    """Verify that paths escaping the base directory are rejected with InvalidReportPathError."""
    escaped = tmp_path / ".." / "evil_report.json"
    with pytest.raises(InvalidReportPathError):
        validate_report_path(escaped, base_dir=tmp_path)


def test_validate_report_path_null_byte() -> None:
    """Verify null bytes in paths raise InvalidReportPathError."""
    with pytest.raises(InvalidReportPathError):
        validate_report_path("report\0.json")
