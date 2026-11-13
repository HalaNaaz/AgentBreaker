"""Payload vector library and category endpoints."""

from fastapi import APIRouter, Depends, Query

from agentbreaker.api.dependencies import get_payload_service, verify_local_auth
from agentbreaker.api.schemas.common import PaginatedResponse
from agentbreaker.api.schemas.responses import CategorySummaryResponse, PayloadListItemResponse
from agentbreaker.api.services.payload_service import PayloadService
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload

router = APIRouter(
    prefix="/api/v1/payloads",
    tags=["Payloads"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("", response_model=PaginatedResponse[PayloadListItemResponse])
async def list_payloads(
    category: AttackCategory | None = None,
    severity: Severity | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    service: PayloadService = Depends(get_payload_service),
) -> PaginatedResponse[PayloadListItemResponse]:
    """Browse attack payload vectors with multi-attribute filtering."""
    items, total = service.list_payloads(
        category=category,
        severity=severity,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/categories", response_model=list[CategorySummaryResponse])
async def get_payload_categories(
    service: PayloadService = Depends(get_payload_service),
) -> list[CategorySummaryResponse]:
    """Retrieve vector breakdown across all attack categories."""
    return service.get_categories()


@router.get("/{payload_id}", response_model=AttackPayload)
async def get_payload_detail(
    payload_id: str,
    service: PayloadService = Depends(get_payload_service),
) -> AttackPayload:
    """Retrieve complete definition and evaluation rules for an attack payload."""
    return service.get_payload(payload_id)


@router.post("/validate")
async def validate_payload_content(
    payload_data: dict,
) -> dict:
    """Validate attack payload schema definition without persisting."""
    try:
        validated = AttackPayload.model_validate(payload_data)
        return {"valid": True, "payload_id": validated.id}
    except Exception as err:
        return {"valid": False, "error": str(err)}
