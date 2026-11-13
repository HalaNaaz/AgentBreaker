"""Target endpoint configuration and response models with strict security validation."""

import ipaddress
import re
from typing import Any
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_serializer,
    model_validator,
)

from agentbreaker.schemas.enums import TargetType

# Blocked cloud metadata addresses and link-local ranges
METADATA_IPS = {
    "169.254.169.254",  # AWS/GCP/Azure link-local metadata
    "fd00:ec2::254",  # AWS IPv6 metadata
    "100.100.100.200",  # Alibaba Cloud metadata
    "0.0.0.0",  # noqa: S104 - Blocked address, not a socket binding
    "::",  # IPv6 unspecified
}

SENSITIVE_HEADER_KEYWORDS = (
    "auth",
    "key",
    "token",
    "secret",
    "cookie",
    "credential",
    "signature",
)


def _is_metadata_or_disallowed_ip(host: str) -> bool:
    """Check if host resolves syntactically to a forbidden metadata or broadcast IP."""
    host_clean = host.strip("[]").lower()
    if host_clean in METADATA_IPS:
        return True
    try:
        ip = ipaddress.ip_address(host_clean)
        if ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            return True
    except ValueError:
        # Not an IP literal (it's a domain name)
        pass
    return False


def _check_crlf(val: str, field_name: str) -> None:
    """Ensure string does not contain carriage return or newline characters."""
    if "\r" in val or "\n" in val:
        raise ValueError(f"Field '{field_name}' must not contain CRLF characters (found newline).")


class TargetConfig(BaseModel):
    """Configuration model for interacting with an AI target endpoint."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    endpoint_url: str = Field(
        ...,
        description="Target endpoint URL (must start with http:// or https://).",
    )
    target_type: TargetType = Field(
        default=TargetType.OPENAI_COMPATIBLE,
        description="Architecture/protocol adapter type.",
    )
    model_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Target model identifier (e.g., 'mistral-7b-instruct', 'gpt-4o').",
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="Target authentication credential (redacted on output).",
    )
    credential_ref: str | None = Field(
        default=None,
        description="Reference identifier to OS-backed secure credential storage.",
    )
    auth_header_name: str = Field(
        default="Authorization",
        description="HTTP header name used for authentication.",
    )
    auth_scheme: str = Field(
        default="Bearer",
        description="Authentication scheme prefix (e.g., 'Bearer', 'ApiKey').",
    )
    custom_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Additional custom HTTP headers for target requests.",
    )
    request_template: dict[str, Any] | None = Field(
        default=None,
        description="Optional custom JSON body template for custom HTTP target.",
    )
    response_path: str | None = Field(
        default=None,
        description="Optional dot-path to extract content from custom JSON response.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="HTTP request timeout limit in seconds.",
    )
    max_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum concurrent in-flight requests allowed.",
    )
    rate_limit_rps: float = Field(
        default=10.0,
        ge=0.1,
        le=100.0,
        description="Rate limit in requests per second.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts on transient network error.",
    )
    retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Base backoff delay in seconds between retries.",
    )
    allowed_hosts: list[str] = Field(
        default_factory=list,
        description="Optional whitelist of allowed domain names/IPs for security boundaries.",
    )
    max_response_bytes: int = Field(
        default=5_000_000,
        ge=1024,
        le=50_000_000,
        description="Maximum allowed response body size in bytes to prevent DoS.",
    )
    allow_redirects: bool = Field(
        default=False,
        description="Whether to follow HTTP redirects. Disabled by default for SSRF mitigation.",
    )
    verify_ssl: bool = Field(
        default=True,
        description="Whether to verify SSL/TLS certificates.",
    )

    @field_validator("endpoint_url")
    @classmethod
    def validate_url_scheme_and_netloc(cls, url_val: str) -> str:
        """Enforce strict HTTP/HTTPS schemes and valid network location."""
        _check_crlf(url_val, "endpoint_url")
        parsed = urlparse(url_val)
        if parsed.scheme.lower() not in ("http", "https"):
            raise ValueError(
                f"Target URL must use 'http' or 'https' scheme; got '{parsed.scheme}'."
            )
        if not parsed.netloc:
            raise ValueError(f"Target URL '{url_val}' lacks a valid host network location.")
        if parsed.username or parsed.password:
            raise ValueError(
                "Target URL must not contain embedded user:password credentials in authority."
            )
        host = (parsed.hostname or "").lower()
        if _is_metadata_or_disallowed_ip(host):
            raise ValueError(
                f"Target endpoint host '{host}' is restricted (cloud metadata / link-local)."
            )
        return url_val

    @field_validator("auth_header_name")
    @classmethod
    def validate_auth_header_name(cls, v: str) -> str:
        """Enforce header name sanity and reject CRLF injection."""
        _check_crlf(v, "auth_header_name")
        if not re.match(r"^[A-Za-z0-9\-_]+$", v.strip()):
            raise ValueError(
                f"Invalid auth_header_name '{v}'. Must be alphanumeric with hyphens/underscores."
            )
        return v.strip()

    @field_validator("auth_scheme")
    @classmethod
    def validate_auth_scheme(cls, v: str) -> str:
        """Enforce scheme name sanity and reject CRLF injection."""
        _check_crlf(v, "auth_scheme")
        if v.strip() and not re.match(r"^[A-Za-z0-9\-_]+$", v.strip()):
            raise ValueError(f"Invalid auth_scheme '{v}'. Must be alphanumeric.")
        return v.strip()

    @field_validator("custom_headers")
    @classmethod
    def validate_custom_headers_crlf(cls, headers: dict[str, str]) -> dict[str, str]:
        """Reject CRLF in custom header keys or values."""
        clean_headers: dict[str, str] = {}
        for k, v in headers.items():
            _check_crlf(k, f"custom_headers key '{k}'")
            _check_crlf(v, f"custom_headers value for '{k}'")
            clean_headers[k.strip()] = v
        return clean_headers

    @model_validator(mode="after")
    def validate_allowed_hosts_boundary(self) -> "TargetConfig":
        """Enforce authorized target boundaries if allowed_hosts is configured."""
        if self.allowed_hosts:
            parsed = urlparse(self.endpoint_url)
            host = (parsed.hostname or "").lower()
            allowed = [h.lower().strip() for h in self.allowed_hosts if h.strip()]
            if host not in allowed:
                raise ValueError(
                    f"Host '{host}' is not in the authorized target boundaries: {allowed}"
                )
        return self

    def get_auth_header(self) -> dict[str, str]:
        """Produce the active authorization header with the unmasked credential."""
        if not self.api_key:
            return {}
        secret_val = self.api_key.get_secret_value().strip()
        if not secret_val:
            return {}
        if self.auth_scheme.strip():
            header_val = f"{self.auth_scheme.strip()} {secret_val}"
        else:
            header_val = secret_val
        return {self.auth_header_name: header_val}

    def safe_dump(self) -> dict[str, Any]:
        """Serialize configuration with all credentials and sensitive headers redacted."""
        return self.model_dump(mode="json")

    @model_serializer(mode="wrap")
    def _serialize_safely(self, handler: Any) -> dict[str, Any]:
        """Automatically mask secrets and sensitive headers in all serialization paths."""
        data = handler(self)
        if isinstance(data, dict):
            if "api_key" in data and data["api_key"] is not None:
                data["api_key"] = "********"
            if "custom_headers" in data and isinstance(data["custom_headers"], dict):
                masked: dict[str, str] = {}
                for k, v in data["custom_headers"].items():
                    if any(sec in k.lower() for sec in SENSITIVE_HEADER_KEYWORDS):
                        masked[k] = "********"
                    else:
                        masked[k] = v
                data["custom_headers"] = masked
        return data


class TargetResponse(BaseModel):
    """Raw response observed from an AI target model or agent system."""

    model_config = ConfigDict(extra="forbid")

    raw_content: str = Field(
        ...,
        description="The primary text response returned by the target system.",
    )
    status_code: int = Field(
        default=200,
        ge=100,
        le=599,
        description="HTTP status code from target endpoint.",
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Observed round-trip latency in milliseconds.",
    )
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Parsed tool/function calling invocations produced by target model.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Diagnostic metadata (model version, finish reason, tokens).",
    )
    error_message: str | None = Field(
        default=None,
        description="Error detail if target failed or produced network error.",
    )
    is_error: bool = Field(
        default=False,
        description="Indicates whether this response represents a target/connection failure.",
    )
