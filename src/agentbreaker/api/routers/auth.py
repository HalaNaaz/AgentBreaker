"""Authentication and local session management endpoints."""

from fastapi import APIRouter, Cookie, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from agentbreaker.api.auth.session import session_manager
from agentbreaker.api.config import api_settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

SESSION_COOKIE_NAME = "agentbreaker_session"


class SessionLoginRequest(BaseModel):
    """Optional station access token for defense-in-depth login."""

    token: str | None = Field(default=None, description="Pre-shared station token.")


class SessionStatusResponse(BaseModel):
    """Current session authentication status and CSRF token."""

    authenticated: bool
    csrf_token: str | None = None
    expires_at: float | None = None
    station_auth_required: bool = False


class WsTicketRequest(BaseModel):
    """Request a short-lived single-use WebSocket connection ticket."""

    assessment_id: str


class WsTicketResponse(BaseModel):
    """Issued single-use ticket bound to a specific assessment."""

    ticket: str
    assessment_id: str
    expires_in_seconds: int = 60


@router.post(
    "/session",
    response_model=SessionStatusResponse,
    summary="Establish authenticated station session",
)
async def create_session(
    response: Response,
    body: SessionLoginRequest | None = None,
    authorization: str | None = Header(default=None),
) -> SessionStatusResponse:
    """Create or verify a local authenticated session.

    Sets an HttpOnly, SameSite=Lax cookie and returns a CSRF token.
    """
    station_key = api_settings.local_api_key
    station_required = bool(station_key)

    if station_required:
        # Check token in body or Authorization header
        candidate = (body.token if body else None) or ""
        if not candidate and authorization and authorization.startswith("Bearer "):
            candidate = authorization[7:].strip()

        if candidate != station_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid station authentication token.",
            )

    sess = session_manager.create_session(authenticated=True)

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=sess.session_id,
        httponly=True,
        samesite="lax",
        secure=False,  # Local loopback HTTP deployment
        path="/",
        max_age=session_manager.ttl_seconds,
    )

    return SessionStatusResponse(
        authenticated=True,
        csrf_token=sess.csrf_token,
        expires_at=sess.expires_at,
        station_auth_required=station_required,
    )


@router.get(
    "/session",
    response_model=SessionStatusResponse,
    summary="Inspect current station session status",
)
async def get_session_status(
    agentbreaker_session: str | None = Cookie(default=None),
) -> SessionStatusResponse:
    """Check whether the client holds an active, unexpired session."""
    station_required = bool(api_settings.local_api_key)
    sess = session_manager.get_session(agentbreaker_session)

    if sess and sess.authenticated:
        return SessionStatusResponse(
            authenticated=True,
            csrf_token=sess.csrf_token,
            expires_at=sess.expires_at,
            station_auth_required=station_required,
        )

    # In default mode (no station key set), unauthenticated loopback can query status
    return SessionStatusResponse(
        authenticated=not station_required,
        csrf_token=None,
        expires_at=None,
        station_auth_required=station_required,
    )


@router.post(
    "/logout",
    summary="Revoke session and clear session cookie",
)
async def logout(
    response: Response,
    agentbreaker_session: str | None = Cookie(default=None),
) -> dict[str, str]:
    """Terminate the active session and invalidate cookie."""
    if agentbreaker_session:
        session_manager.revoke_session(agentbreaker_session)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )
    return {"status": "logged_out"}


@router.post(
    "/ws-ticket",
    response_model=WsTicketResponse,
    summary="Generate single-use WebSocket ticket",
)
async def get_ws_ticket(
    req: WsTicketRequest,
    request: Request,
    agentbreaker_session: str | None = Cookie(default=None),
    x_csrf_token: str | None = Header(default=None),
) -> WsTicketResponse:
    """Generate a 60-second single-use ticket for WebSocket streaming.

    Prevents transmitting long-lived credentials in WebSocket query parameters.
    """
    station_key = api_settings.local_api_key

    # 1. Verify via session cookie
    sess = session_manager.get_session(agentbreaker_session)
    if sess and sess.authenticated:
        # Enforce CSRF token match
        if not x_csrf_token or x_csrf_token != sess.csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed for ticket request.",
            )
        ticket = session_manager.create_ws_ticket(req.assessment_id, sess.session_id)
        return WsTicketResponse(ticket=ticket, assessment_id=req.assessment_id)

    # 2. Allow if no station key is configured (local loopback mode)
    if not station_key:
        # Create ephemeral session to generate ticket
        ephemeral = session_manager.create_session(authenticated=True)
        ticket = session_manager.create_ws_ticket(req.assessment_id, ephemeral.session_id)
        return WsTicketResponse(ticket=ticket, assessment_id=req.assessment_id)

    # 3. Direct token header check (for CLI / script consumers)
    auth_hdr = request.headers.get("authorization", "")
    token_hdr = request.headers.get("x-agentbreaker-token", "")
    bearer_token = auth_hdr[7:].strip() if auth_hdr.startswith("Bearer ") else ""
    provided_key = token_hdr or bearer_token

    if provided_key == station_key:
        ephemeral = session_manager.create_session(authenticated=True)
        ticket = session_manager.create_ws_ticket(req.assessment_id, ephemeral.session_id)
        return WsTicketResponse(ticket=ticket, assessment_id=req.assessment_id)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authenticated session or token required to generate ticket.",
    )
