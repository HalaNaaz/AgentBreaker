"""Assessment lifecycle, background task orchestration, and WebSocket streaming."""

import contextlib
import re

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status

from agentbreaker.api.auth.session import session_manager
from agentbreaker.api.config import api_settings
from agentbreaker.api.dependencies import get_assessment_service, verify_local_auth
from agentbreaker.api.schemas.requests import AssessmentCreateRequest
from agentbreaker.api.schemas.responses import (
    AssessmentDetailResponse,
    AssessmentListItemResponse,
    AssessmentStatusResponse,
)
from agentbreaker.api.services.assessment_service import AssessmentService
from agentbreaker.api.websocket.manager import ws_manager

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])


@router.get(
    "",
    response_model=list[AssessmentListItemResponse],
    dependencies=[Depends(verify_local_auth)],
)
async def list_assessments(
    service: AssessmentService = Depends(get_assessment_service),
) -> list[AssessmentListItemResponse]:
    """List all configured and completed assessment runs."""
    return service.list_assessments()


@router.post(
    "",
    response_model=AssessmentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_local_auth)],
)
async def create_assessment(
    req: AssessmentCreateRequest,
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentDetailResponse:
    """Define a new assessment evaluation run in local storage."""
    return service.create_assessment(req)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentDetailResponse,
    dependencies=[Depends(verify_local_auth)],
)
async def get_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentDetailResponse:
    """Retrieve details and execution summaries for an assessment."""
    return service.get_assessment(assessment_id)


@router.post(
    "/{assessment_id}/start",
    response_model=AssessmentStatusResponse,
    dependencies=[Depends(verify_local_auth)],
)
async def start_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentStatusResponse:
    """Start non-blocking background assessment execution."""
    return await service.start_assessment(assessment_id)


@router.post(
    "/{assessment_id}/cancel",
    response_model=AssessmentStatusResponse,
    dependencies=[Depends(verify_local_auth)],
)
async def cancel_assessment(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentStatusResponse:
    """Cancel an active in-flight assessment task."""
    return await service.cancel_assessment(assessment_id)


@router.get(
    "/{assessment_id}/status",
    response_model=AssessmentStatusResponse,
    dependencies=[Depends(verify_local_auth)],
)
async def get_assessment_status(
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
) -> AssessmentStatusResponse:
    """Get real-time execution status and progress counts for an assessment."""
    return service.get_status(assessment_id)


@router.websocket("/{assessment_id}/events")
async def assessment_events_websocket(
    websocket: WebSocket,
    assessment_id: str,
    service: AssessmentService = Depends(get_assessment_service),
) -> None:
    """Stream live assessment progress, payload executions, and findings over WebSocket."""
    # 1. Enforce local authentication if configured
    expected_token = api_settings.local_api_key
    if expected_token:
        ticket = websocket.query_params.get("ticket")
        if ticket is not None:
            # Single-use ticket flow: ticket must be valid and bound to this assessment
            if not session_manager.validate_and_consume_ws_ticket(ticket, assessment_id):
                await websocket.close(code=4001, reason="Invalid or expired WebSocket ticket")
                return
        else:
            # Check session cookie
            sess_cookie = websocket.cookies.get("agentbreaker_session")
            sess = session_manager.get_session(sess_cookie)
            is_valid_session = sess is not None and sess.authenticated

            # Check direct token (for CLI / script consumers)
            token = websocket.query_params.get("token") or websocket.headers.get(
                "x-agentbreaker-token"
            )
            if not token:
                auth_hdr = websocket.headers.get("authorization", "")
                if auth_hdr.startswith("Bearer "):
                    token = auth_hdr[7:].strip()
            is_valid_token = token == expected_token

            if not (is_valid_session or is_valid_token):
                await websocket.close(code=4001, reason="Unauthorized")
                return

    # 2. Strict ID syntax validation (prevent traversal or malformed injection)
    if not re.match(r"^[a-zA-Z0-9_\-]+$", assessment_id):
        await websocket.close(code=4000, reason="Invalid assessment identifier")
        return

    # 3. Validate assessment exists before accepting connection
    try:
        service.get_assessment(assessment_id)
    except Exception:
        await websocket.close(code=4004, reason="Assessment not found")
        return

    # 4. Connect with connection bounding
    accepted = await ws_manager.connect(assessment_id, websocket)
    if not accepted:
        return

    try:
        with contextlib.suppress(WebSocketDisconnect, Exception):
            while True:
                # Keep-alive receive loop
                _msg = await websocket.receive_text()
    finally:
        await ws_manager.disconnect(assessment_id, websocket)
