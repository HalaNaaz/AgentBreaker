"""Connector exception definitions and error classifications."""


class ConnectorError(Exception):
    """Base exception for all target connector failures."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        target_url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.target_url = target_url

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(Status: {self.status_code})")
        return " ".join(parts)


class AuthenticationError(ConnectorError):
    """Raised when target authentication fails (e.g. 401 Unauthorized, 403 Forbidden)."""


class TargetUnavailableError(ConnectorError):
    """Raised when the target endpoint is unreachable, offline, or returns 502/503/504."""


class RateLimitError(ConnectorError):
    """Raised when the target returns HTTP 429 Too Many Requests."""

    def __init__(
        self,
        message: str,
        status_code: int = 429,
        target_url: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, target_url=target_url)
        self.retry_after = retry_after


class TimeoutError(ConnectorError):
    """Raised when a connection or response exceeds configured timeout limit."""


class SecurityBoundaryError(ConnectorError):
    """Raised when an SSRF boundary or target policy violation is detected."""


class OversizedResponseError(ConnectorError):
    """Raised when a target response exceeds the configured maximum response byte size."""


class InvalidResponseError(ConnectorError):
    """Raised when target response is malformed, truncated, or lacks required structure."""


class ToolExecutionForbiddenError(ConnectorError):
    """Raised if an unsafe attempt to execute model-generated tool calls occurs."""
