"""Domain exceptions and uniform HTTP error representations for AgentBreaker API."""

from fastapi import Request, status
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base exception for all AgentBreaker API domain errors."""

    def __init__(
        self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ResourceNotFoundError(APIError):
    """Raised when an identified resource does not exist in storage."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(APIError):
    """Raised when an operation conflicts with existing server or task state."""

    def __init__(self, message: str = "Resource conflict or operation already in progress") -> None:
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class TargetAuthorizationError(APIError):
    """Raised when an action violates target authorization boundaries."""

    def __init__(self, message: str = "Target authorization boundary check failed") -> None:
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class SecurityValidationError(APIError):
    """Raised when an untrusted input fails security or safety validation."""

    def __init__(self, message: str = "Input failed security validation") -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)


async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
    """Serialize domain API errors into uniform, safe error JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "type": exc.__class__.__name__,
        },
    )


async def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Catch unhandled server exceptions without leaking internal system traces."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An unexpected internal server error occurred.",
            "type": "InternalServerError",
        },
    )
