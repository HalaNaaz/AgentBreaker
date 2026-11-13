"""Secure local session management and single-use WebSocket ticket dispatcher."""

import secrets
import time
from dataclasses import dataclass


@dataclass
class Session:
    """Represents an active local HTTP session."""

    session_id: str
    csrf_token: str
    created_at: float
    expires_at: float
    authenticated: bool


class SessionManager:
    """Manages short-lived HttpOnly authenticated sessions and single-use WebSocket tickets.

    Invariants:
    - Never stores persistent secrets in browser storage.
    - Employs cryptographically secure random tokens.
    - Single-use WebSocket connection tickets bounded by 60s expiration.
    - Thread-safe and in-memory.
    """

    DEFAULT_TTL_SECONDS = 3600  # 1 hour
    WS_TICKET_TTL_SECONDS = 60  # 60 seconds

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, Session] = {}
        # Mapping: ticket -> (assessment_id, expires_at)
        self._ws_tickets: dict[str, tuple[str, float]] = {}

    def create_session(self, authenticated: bool = True) -> Session:
        """Create a new session with an associated CSRF token."""
        now = time.time()
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        sess = Session(
            session_id=session_id,
            csrf_token=csrf_token,
            created_at=now,
            expires_at=now + self.ttl_seconds,
            authenticated=authenticated,
        )
        self._sessions[session_id] = sess
        self._cleanup_expired()
        return sess

    def get_session(self, session_id: str | None) -> Session | None:
        """Retrieve and validate session if active and unexpired."""
        if not session_id:
            return None
        sess = self._sessions.get(session_id)
        if not sess:
            return None
        if time.time() > sess.expires_at:
            del self._sessions[session_id]
            return None
        return sess

    def revoke_session(self, session_id: str) -> bool:
        """Revoke and invalidate an active session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def create_ws_ticket(self, assessment_id: str, session_id: str) -> str:
        """Generate a single-use ticket bound to a specific assessment."""
        sess = self.get_session(session_id)
        if not sess or not sess.authenticated:
            raise PermissionError("Valid authenticated session required to issue WebSocket ticket.")

        ticket = secrets.token_urlsafe(24)
        expires_at = time.time() + self.WS_TICKET_TTL_SECONDS
        self._ws_tickets[ticket] = (assessment_id, expires_at)
        return ticket

    def validate_and_consume_ws_ticket(self, ticket: str | None, assessment_id: str) -> bool:
        """Validate ticket matching the assessment and immediately consume it."""
        if not ticket:
            return False
        entry = self._ws_tickets.pop(ticket, None)
        if not entry:
            return False
        bound_assessment_id, expires_at = entry
        if time.time() > expires_at:
            return False
        return bound_assessment_id == assessment_id

    def _cleanup_expired(self) -> None:
        """Remove stale sessions and tickets."""
        now = time.time()
        expired_sessions = [k for k, v in self._sessions.items() if now > v.expires_at]
        for k in expired_sessions:
            del self._sessions[k]

        expired_tickets = [k for k, v in self._ws_tickets.items() if now > v[1]]
        for k in expired_tickets:
            del self._ws_tickets[k]


session_manager = SessionManager()
