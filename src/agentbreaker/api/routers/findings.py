"""Technical evaluation findings inspection endpoints."""

from fastapi import APIRouter, Depends, Query

from agentbreaker.api.dependencies import get_finding_service, verify_local_auth
from agentbreaker.api.schemas.common import PaginatedResponse
from agentbreaker.api.services.finding_service import FindingService
from agentbreaker.reporting.models import FindingDetail
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict

router = APIRouter(
    prefix="/api/v1/findings",
    tags=["Findings"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("", response_model=PaginatedResponse[FindingDetail])
async def list_findings(
    assessment_id: str | None = None,
    severity: Severity | None = None,
    verdict: Verdict | None = None,
    category: AttackCategory | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    service: FindingService = Depends(get_finding_service),
) -> PaginatedResponse[FindingDetail]:
    """Query granular evaluation findings across assessments with comprehensive filters."""
    items, total = service.list_findings(
        assessment_id=assessment_id,
        severity=severity,
        verdict=verdict,
        category=category,
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


@router.get("/{finding_id}", response_model=FindingDetail)
async def get_finding(
    finding_id: str,
    service: FindingService = Depends(get_finding_service),
) -> FindingDetail:
    """Retrieve full technical finding details including evidence and reproduction hints."""
    return service.get_finding(finding_id)
