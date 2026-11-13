"""Research report generation, inspection, and download endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from agentbreaker.api.dependencies import get_reporting_service, verify_local_auth
from agentbreaker.api.schemas.requests import ReportGenerateRequest
from agentbreaker.api.schemas.responses import ReportListItemResponse
from agentbreaker.api.services.reporting_service import APIReportingService
from agentbreaker.reporting.models import AssessmentReport

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("", response_model=list[ReportListItemResponse])
async def list_reports(
    service: APIReportingService = Depends(get_reporting_service),
) -> list[ReportListItemResponse]:
    """List all available generated research reports in local storage."""
    return service.list_reports()


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_report(
    assessment_id: str,
    req: ReportGenerateRequest,
    service: APIReportingService = Depends(get_reporting_service),
) -> dict[str, str]:
    """Generate and persist a report in JSON, Markdown, or HTML format."""
    saved_path = service.generate_report(assessment_id=assessment_id, req=req)
    return {
        "status": "success",
        "message": f"Report generated in {req.format.value.upper()} format.",
        "filename": saved_path.name,
    }


@router.get("/{assessment_id}/model", response_model=AssessmentReport)
async def get_report_model(
    assessment_id: str,
    service: APIReportingService = Depends(get_reporting_service),
) -> AssessmentReport:
    """Compile and return the complete in-memory AssessmentReport model."""
    clean_id = assessment_id.removeprefix("RPT-")
    return service.build_report_model(clean_id)


@router.get("/{filename}/download")
async def download_report_file(
    filename: str,
    service: APIReportingService = Depends(get_reporting_service),
) -> FileResponse:
    """Download a generated report file with safe content disposition headers."""
    file_path = service.get_report_file(filename)
    media_types = {
        ".json": "application/json",
        ".md": "text/markdown",
        ".html": "text/html",
    }
    media_type = media_types.get(file_path.suffix.lower(), "application/octet-stream")
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )
