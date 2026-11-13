"""FastAPI dependency injection providers for AgentBreaker API."""

from fastapi import Header, HTTPException, Request, status

from agentbreaker.api.auth.session import session_manager
from agentbreaker.api.config import api_settings
from agentbreaker.api.services import (
    AnalyticsService,
    APIReportingService,
    AssessmentService,
    FindingService,
    MutationService,
    PayloadService,
    TargetService,
    analytics_service,
    assessment_service,
    finding_service,
    mutation_service,
    payload_service,
    reporting_service,
    target_service,
)
from agentbreaker.cli.storage import StorageManager, storage


def get_storage() -> StorageManager:
    """Provide shared local storage manager."""
    return storage


def get_target_service() -> TargetService:
    """Provide target configuration and testing service."""
    return target_service


def get_payload_service() -> PayloadService:
    """Provide attack vector library service."""
    return payload_service


def get_mutation_service() -> MutationService:
    """Provide mutation preview and strategy service."""
    return mutation_service


def get_assessment_service() -> AssessmentService:
    """Provide assessment lifecycle and background execution service."""
    return assessment_service


def get_finding_service() -> FindingService:
    """Provide technical audit findings inspection service."""
    return finding_service


def get_reporting_service() -> APIReportingService:
    """Provide research report compilation and file service."""
    return reporting_service


def get_analytics_service() -> AnalyticsService:
    """Provide macro analytics and comparison service."""
    return analytics_service


async def verify_local_auth(
    request: Request,
    x_agentbreaker_token: str | None = Header(default=None),
) -> None:
    """Optional defense-in-depth verification for local API requests.

    Supports both programmatic tokens (CLI/automation) and secure HttpOnly
    local session cookies with CSRF defense.
    """
    # If no local API key is configured, loopback requests are accepted
    expected_token = api_settings.local_api_key
    if not expected_token:
        return

    # 1. Check direct token in headers (CLI & script access)
    auth_header = request.headers.get("Authorization")
    bearer_token = None
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:].strip()

    provided = x_agentbreaker_token or bearer_token
    if provided and provided == expected_token:
        return

    # 2. Check HttpOnly local session cookie
    cookie_token = request.cookies.get("agentbreaker_session")
    sess = session_manager.get_session(cookie_token)
    if sess and sess.authenticated:
        # Enforce CSRF protection on mutating HTTP verbs
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            csrf_hdr = request.headers.get("X-CSRF-Token")
            if not csrf_hdr or csrf_hdr != sess.csrf_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token validation failed.",
                )
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing local API authorization token or session.",
    )
