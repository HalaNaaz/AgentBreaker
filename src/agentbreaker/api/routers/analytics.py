"""Analytical framework coverage and comparative assessment endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from agentbreaker.api.dependencies import get_analytics_service, verify_local_auth
from agentbreaker.api.schemas.requests import AssessmentCompareRequest
from agentbreaker.api.schemas.responses import AnalyticsOverviewResponse
from agentbreaker.api.services.analytics_service import AnalyticsService
from agentbreaker.reporting.models import AssessmentComparison

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    """Return macro-level security statistics aggregated across all completed evaluations."""
    return service.get_overview()


@router.get("/assessments/{assessment_id}")
async def get_assessment_analytics(
    assessment_id: str,
    service: AnalyticsService = Depends(get_analytics_service),
) -> dict[str, Any]:
    """Retrieve OWASP Top 10 for LLMs, MITRE ATLAS, and evidence telemetry for an assessment."""
    return service.get_assessment_analytics(assessment_id)


@router.post("/compare", response_model=AssessmentComparison)
async def compare_assessments(
    req: AssessmentCompareRequest,
    service: AnalyticsService = Depends(get_analytics_service),
) -> AssessmentComparison:
    """Compare historical assessments, computing progression and regressions."""
    return service.compare(req)
