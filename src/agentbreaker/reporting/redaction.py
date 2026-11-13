"""Centralized secret redaction, string sanitization, and path safety enforcement."""

import html
import re
from pathlib import Path
from typing import Any

from agentbreaker.reporting.exceptions import InvalidReportPathError

SENSITIVE_KEY_PATTERNS = (
    "auth",
    "key",
    "token",
    "secret",
    "cookie",
    "credential",
    "signature",
    "password",
    "api_key",
)

SECRET_VALUE_REGEXES = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}", re.IGNORECASE),
    re.compile(r"ghp_[A-Za-z0-9_]{36}", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z]{10,48}"),
    re.compile(r"-----BEGIN\s+([A-Z\s]+)?PRIVATE\s+KEY-----", re.IGNORECASE),
]

# Sensitive query parameter e.g. api_key=secret, token=secret
PARAM_SECRET_REGEX = re.compile(
    r"((?:api[_-]?key|token|access_token|secret|password)=)[^&\s'\"]+",
    re.IGNORECASE,
)

# Embedded URL credentials e.g. https://user:password@hostname
URL_CREDENTIAL_REGEX = re.compile(r"([a-zA-Z][a-zA-Z0-9+\-.]*://[^:\s]+):([^@\s/]+)@")

WINDOWS_RESERVED_DEVICES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


def redact_string(value: str) -> str:
    """Scrub known secret value patterns from arbitrary string content."""
    if not value:
        return value

    sanitized = value
    for pattern in SECRET_VALUE_REGEXES:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)

    # Redact Authorization header strings e.g. "Bearer sk-..."
    sanitized = re.sub(
        r"(Bearer\s+)[A-Za-z0-9_\-\.]{8,}",
        r"\1[REDACTED_TOKEN]",
        sanitized,
        flags=re.IGNORECASE,
    )
    # Redact Basic auth header strings e.g. "Basic dXNlcjpwYXNz"
    sanitized = re.sub(
        r"(Basic\s+)[A-Za-z0-9+/=]{8,}",
        r"\1[REDACTED_TOKEN]",
        sanitized,
        flags=re.IGNORECASE,
    )
    # Redact URL credentials
    sanitized = URL_CREDENTIAL_REGEX.sub(r"\1:[REDACTED_SECRET]@", sanitized)
    # Redact sensitive parameters
    sanitized = PARAM_SECRET_REGEX.sub(r"\1[REDACTED_SECRET]", sanitized)
    return sanitized


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys and secret values from a dictionary."""
    clean: dict[str, Any] = {}
    for k, v in data.items():
        k_lower = str(k).lower()
        if any(sec in k_lower for sec in SENSITIVE_KEY_PATTERNS):
            clean[k] = "[REDACTED]"
            continue

        if isinstance(v, dict):
            clean[k] = redact_dict(v)
        elif isinstance(v, (list, tuple, set)):
            sanitized_list = [
                redact_dict(item)
                if isinstance(item, dict)
                else (redact_string(item) if isinstance(item, str) else item)
                for item in v
            ]
            clean[k] = type(v)(sanitized_list) if not isinstance(v, list) else sanitized_list
        elif isinstance(v, str):
            clean[k] = redact_string(v)
        else:
            clean[k] = v
    return clean


def escape_html(text: str | None) -> str:
    """Safely escape untrusted text content for direct HTML injection prevention."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def validate_report_path(
    output_path: Path | str,
    base_dir: Path | str | None = None,
) -> Path:
    """Enforce that report output paths remain within approved directories without traversal."""
    str_path = str(output_path)
    if "\0" in str_path:
        raise InvalidReportPathError("Path contains null byte.")

    # Reject UNC network paths
    if str_path.startswith(r"\\") or str_path.startswith("//"):
        raise InvalidReportPathError("UNC network paths are forbidden for report exports.")

    try:
        p = Path(output_path).resolve()
    except (ValueError, OSError) as err:
        raise InvalidReportPathError(f"Invalid path: {err}") from err

    # Reject Windows reserved device names
    for part in p.parts:
        root_part = part.split(".")[0].upper()
        if root_part in WINDOWS_RESERVED_DEVICES:
            raise InvalidReportPathError(f"Windows reserved device name '{part}' is forbidden.")

    if base_dir:
        base = Path(base_dir).resolve()
        if not p.is_relative_to(base):
            raise InvalidReportPathError(
                f"Path '{output_path}' escapes the authorized base directory '{base}'."
            )

    return p
