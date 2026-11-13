"""Security controls and boundary validation tests for target connectors."""

import pytest
import respx
from pydantic import SecretStr, ValidationError

from agentbreaker.connectors.base import BaseConnector
from agentbreaker.connectors.exceptions import (
    OversizedResponseError,
    SecurityBoundaryError,
)
from agentbreaker.schemas.target import TargetConfig, TargetResponse


class SecurityTestConnector(BaseConnector):
    async def send_prompt(self, prompt: str, **kwargs) -> TargetResponse:
        resp, latency_ms = await self._safe_execute_request(
            "POST", self.config.endpoint_url, json={"p": prompt}
        )
        return TargetResponse(
            raw_content=resp.text,
            status_code=resp.status_code,
            latency_ms=latency_ms,
        )

    async def health_check(self) -> bool:
        return True


def test_ssrf_cloud_metadata_ip_blocked():
    """Verify cloud metadata IPs are rejected during configuration and connector initialization."""
    with pytest.raises(ValidationError, match="cloud metadata"):
        TargetConfig(endpoint_url="http://169.254.169.254/latest/meta-data/", model_name="m")

    with pytest.raises(ValidationError, match="cloud metadata"):
        TargetConfig(endpoint_url="http://[fd00:ec2::254]/", model_name="m")

    with pytest.raises(ValidationError, match="cloud metadata"):
        TargetConfig(endpoint_url="http://0.0.0.0:8000/", model_name="m")


def test_ssrf_embedded_credentials_blocked():
    """Verify URLs with embedded credentials in authority are rejected."""
    with pytest.raises(ValidationError, match="embedded user:password credentials"):
        TargetConfig(endpoint_url="http://admin:secret123@localhost:8000/v1", model_name="m")


def test_ssrf_forbidden_schemes_blocked():
    """Verify non-HTTP schemes are rejected."""
    for scheme in (
        "file:///etc/passwd",
        "gopher://localhost:70",
        "ftp://ftp.local",
        "javascript:alert(1)",
    ):
        with pytest.raises(ValidationError, match="must use 'http' or 'https' scheme"):
            TargetConfig(endpoint_url=scheme, model_name="m")


def test_crlf_header_injection_blocked():
    """Verify CRLF characters in headers are rejected."""
    with pytest.raises(ValidationError, match="CRLF"):
        TargetConfig(
            endpoint_url="http://localhost:8000",
            model_name="m",
            auth_header_name="Auth\r\nInjected",
        )

    with pytest.raises(ValidationError, match="CRLF"):
        TargetConfig(
            endpoint_url="http://localhost:8000",
            model_name="m",
            custom_headers={"X-Custom\r\nInjected": "val"},
        )


def test_secret_redaction_in_all_dumps():
    """Verify API keys and sensitive custom headers are masked across all serialization modes."""
    cfg = TargetConfig(
        endpoint_url="http://localhost:8000",
        model_name="m",
        api_key=SecretStr("super-secret-api-key"),
        custom_headers={"X-Custom-Token": "secret-token-val", "Content-Type": "application/json"},
    )
    # Check model_dump
    dumped = cfg.model_dump()
    assert dumped["api_key"] == "********"
    assert dumped["custom_headers"]["X-Custom-Token"] == "********"
    assert dumped["custom_headers"]["Content-Type"] == "application/json"

    # Check model_dump_json
    json_dump = cfg.model_dump_json()
    assert "super-secret-api-key" not in json_dump
    assert "secret-token-val" not in json_dump
    assert "********" in json_dump


@pytest.mark.asyncio
@respx.mock
async def test_redirect_to_disallowed_target_blocked():
    """Verify redirect to unwhitelisted target is blocked even when allow_redirects is enabled."""
    respx.post("http://localhost:8000/test").respond(
        302, headers={"location": "http://evil-external-domain.com/v1"}
    )

    cfg = TargetConfig(
        endpoint_url="http://localhost:8000/test",
        model_name="m",
        allow_redirects=True,
        allowed_hosts=["localhost", "127.0.0.1"],
    )

    async with SecurityTestConnector(cfg) as conn:
        with pytest.raises(SecurityBoundaryError, match="authorized target boundaries"):
            await conn.send_prompt("Test")


@pytest.mark.asyncio
@respx.mock
async def test_oversized_response_blocked():
    """Verify response exceeding max_response_bytes raises OversizedResponseError."""
    respx.post("http://localhost:8000/test").respond(200, text="X" * 1500)

    cfg = TargetConfig(
        endpoint_url="http://localhost:8000/test",
        model_name="m",
        max_response_bytes=1024,
    )

    async with SecurityTestConnector(cfg) as conn:
        with pytest.raises(OversizedResponseError):
            await conn.send_prompt("Test")
