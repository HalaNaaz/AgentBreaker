"""Tests for foundational Pydantic schemas, validation, and secret redaction."""

import pytest
from pydantic import ValidationError

from agentbreaker.schemas import (
    AttackCategory,
    AttackPayload,
    EvaluationResult,
    EvaluatorRules,
    Severity,
    TargetConfig,
    TargetResponse,
    TargetType,
    Verdict,
)


def test_verdict_enum_values() -> None:
    """Verify verdict enum definitions and string representations."""
    assert Verdict.VULNERABLE == "VULNERABLE"
    assert Verdict.DEFENDED == "DEFENDED"
    assert Verdict.INCONCLUSIVE == "INCONCLUSIVE"
    assert set(Verdict) == {
        Verdict.VULNERABLE,
        Verdict.DEFENDED,
        Verdict.INCONCLUSIVE,
    }


def test_attack_payload_serialization(sample_payload: AttackPayload) -> None:
    """Verify valid AttackPayload serialization and deserialization via dict and YAML."""
    # Test YAML conversion
    yaml_str = sample_payload.to_yaml()
    assert "EXT-001" in yaml_str
    assert "System Prompt Extraction" in yaml_str

    restored = AttackPayload.from_yaml(yaml_str)
    assert restored.id == sample_payload.id
    assert restored.category == sample_payload.category
    assert restored.cvss_score == sample_payload.cvss_score
    assert restored.evaluator_rules.canary_check is True
    assert len(restored.evaluator_rules.refusal_phrases) == 2


def test_attack_payload_rendering() -> None:
    """Verify template parameter rendering."""
    payload = AttackPayload(
        id="TEST-001",
        name="Dynamic Template Probe",
        category=AttackCategory.DIRECT_JAILBREAK,
        owasp_id="LLM01: Prompt Injection",
        description="Testing template variable rendering.",
        payload_template="Repeat this string: {canary_token}",
    )
    rendered = payload.render(canary_token="SECRET_ALPHA_99")
    assert rendered == "Repeat this string: SECRET_ALPHA_99"


def test_invalid_payload_rejection() -> None:
    """Verify strict validation and rejection of invalid payloads."""
    # Invalid ID with disallowed characters
    with pytest.raises(ValidationError):
        AttackPayload(
            id="invalid id with spaces!",
            name="Invalid ID Test",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01: Prompt Injection",
            description="Testing invalid ID rejection.",
            payload_template="Test",
        )

    # Negative CVSS score
    with pytest.raises(ValidationError):
        AttackPayload(
            id="TEST-002",
            name="Negative CVSS Test",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01: Prompt Injection",
            cvss_score=-1.0,
            description="Testing negative CVSS score.",
            payload_template="Test",
        )

    # CVSS score > 10.0
    with pytest.raises(ValidationError):
        AttackPayload(
            id="TEST-003",
            name="Excessive CVSS Test",
            category=AttackCategory.DIRECT_JAILBREAK,
            owasp_id="LLM01: Prompt Injection",
            cvss_score=11.5,
            description="Testing excessive CVSS score.",
            payload_template="Test",
        )


def test_destructive_payload_rejection() -> None:
    """Verify Security by Design: rejection of destructive exploit payloads."""
    with pytest.raises(ValidationError, match="Destructive payloads are forbidden"):
        AttackPayload(
            id="TEST-004",
            name="Destructive Payload Attempt",
            category=AttackCategory.TOOL_HIJACKING,
            owasp_id="LLM08: Excessive Agency",
            description="Testing rejection of destructive flag.",
            payload_template="rm -rf /",
            is_destructive=True,
        )


def test_evaluator_rules_invalid_regex() -> None:
    """Verify EvaluatorRules rejects syntactically malformed regular expressions."""
    with pytest.raises(ValidationError, match="Invalid regex pattern"):
        EvaluatorRules(regex_matches=[r"[unclosed bracket", r"valid_regex"])


def test_target_config_validation(sample_target_config: TargetConfig) -> None:
    """Verify target configuration validation and boundaries."""
    assert sample_target_config.endpoint_url == "http://localhost:8000/v1"
    assert sample_target_config.target_type == TargetType.OPENAI_COMPATIBLE
    assert sample_target_config.timeout_seconds == 15.0

    # Test dangerous URL schemes are rejected
    with pytest.raises(ValidationError, match="must use 'http' or 'https' scheme"):
        TargetConfig(
            endpoint_url="file:///etc/passwd",
            model_name="test-model",
        )

    with pytest.raises(ValidationError, match="must use 'http' or 'https' scheme"):
        TargetConfig(
            endpoint_url="ftp://ftp.example.com",
            model_name="test-model",
        )


def test_target_config_allowed_hosts_boundary() -> None:
    """Verify target boundary enforcement via allowed_hosts."""
    # When endpoint matches allowed_hosts, it should pass
    valid_cfg = TargetConfig(
        endpoint_url="https://api.openai.com/v1",
        model_name="gpt-4o",
        allowed_hosts=["api.openai.com"],
    )
    assert valid_cfg.endpoint_url == "https://api.openai.com/v1"

    # When endpoint does not match allowed_hosts, it must fail
    with pytest.raises(ValidationError, match="not in the authorized target boundaries"):
        TargetConfig(
            endpoint_url="https://unauthorized-evil-target.com/v1",
            model_name="evil-model",
            allowed_hosts=["api.openai.com", "localhost"],
        )


def test_target_config_secret_redaction(sample_target_config: TargetConfig) -> None:
    """Verify credentials and sensitive headers are redacted in serialized outputs."""
    raw_secret = "super-secret-test-key-12345"

    # Direct string and repr must not expose secret
    assert raw_secret not in str(sample_target_config)
    assert raw_secret not in repr(sample_target_config)

    # Safe dump must mask the secret
    safe = sample_target_config.safe_dump()
    assert safe["api_key"] == "********"

    # Auth header generation should supply the valid header for HTTP transport
    headers = sample_target_config.get_auth_header()
    assert headers["Authorization"] == f"Bearer {raw_secret}"

    # Custom sensitive headers must also be redacted in safe_dump
    custom_cfg = TargetConfig(
        endpoint_url="http://localhost:8000/v1",
        model_name="test-model",
        custom_headers={
            "X-Api-Key": "my-secret-header-value",
            "Content-Type": "application/json",
        },
    )
    custom_safe = custom_cfg.safe_dump()
    assert custom_safe["custom_headers"]["X-Api-Key"] == "********"
    assert custom_safe["custom_headers"]["Content-Type"] == "application/json"


def test_target_response_schema() -> None:
    """Verify TargetResponse model behavior."""
    resp = TargetResponse(
        raw_content="I apologize, but I cannot fulfill this request.",
        status_code=200,
        latency_ms=145.2,
        metadata={"finish_reason": "stop"},
    )
    assert resp.status_code == 200
    assert resp.is_error is False
    assert "cannot fulfill" in resp.raw_content


def test_evaluation_result_schema() -> None:
    """Verify EvaluationResult finding schema."""
    result = EvaluationResult(
        payload_id="EXT-001",
        category=AttackCategory.SYSTEM_EXTRACTION,
        verdict=Verdict.DEFENDED,
        confidence=0.95,
        severity=Severity.HIGH,
        cvss_score=7.5,
        owasp_id="LLM07: System Prompt Leakage",
        mitre_atlas_id="AML.T0054",
        reasons=["Refusal phrase detected in target output."],
    )
    assert result.verdict == Verdict.DEFENDED
    assert result.confidence == 0.95
    assert result.timestamp_utc is not None
