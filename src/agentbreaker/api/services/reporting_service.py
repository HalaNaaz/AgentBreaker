"""Reporting service bridging HTTP API to the Phase 7 Reporting Engine."""

from pathlib import Path

from agentbreaker.api.exceptions import ResourceNotFoundError, SecurityValidationError
from agentbreaker.api.schemas.requests import ReportGenerateRequest
from agentbreaker.api.schemas.responses import ReportListItemResponse
from agentbreaker.cli.storage import StorageManager, storage
from agentbreaker.reporting.models import AssessmentReport
from agentbreaker.reporting.redaction import validate_report_path
from agentbreaker.reporting.service import ReportingService as CoreReportingService


class APIReportingService:
    """Service handling report compilation, retrieval, and disk delivery for API clients."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage
        self.core = CoreReportingService(storage_manager=self.storage)

    def list_reports(self) -> list[ReportListItemResponse]:
        """List all generated report documents available in local storage."""
        raw_list = self.core.list_reports()
        return [
            ReportListItemResponse(
                report_file=r["report_file"],
                format=r["format"].upper(),
                size_bytes=r["size_bytes"],
                modified_at=r["modified_at"],
            )
            for r in raw_list
        ]

    def build_report_model(self, assessment_id: str) -> AssessmentReport:
        """Compile complete in-memory AssessmentReport model."""
        try:
            return self.core.build_report(assessment_id)
        except Exception as err:
            raise ResourceNotFoundError(f"Failed to compile report: {err}") from err

    def generate_report(
        self,
        assessment_id: str,
        req: ReportGenerateRequest,
    ) -> Path:
        """Render and atomically persist report in requested format."""
        # Verify assessment exists
        if not self.storage.get_assessment(assessment_id):
            raise ResourceNotFoundError(f"Assessment '{assessment_id}' not found.")

        try:
            return self.core.save_report(
                assessment_id=assessment_id,
                output_format=req.format,
            )
        except Exception as err:
            raise SecurityValidationError(f"Report generation error: {err}") from err

    def get_report_file(self, report_filename: str) -> Path:
        """Retrieve path to a generated report with strict directory traversal prevention."""
        if (
            "\0" in report_filename
            or ".." in report_filename
            or "/" in report_filename
            or "\\" in report_filename
        ):
            raise SecurityValidationError(
                "Invalid report filename or directory traversal detected."
            )
        clean_name = Path(report_filename).name
        target = self.storage.reports_dir / clean_name
        try:
            valid_path = validate_report_path(target, base_dir=self.storage.reports_dir)
        except Exception as err:
            raise SecurityValidationError(f"Invalid report path: {err}") from err

        if not valid_path.exists() or not valid_path.is_file():
            raise ResourceNotFoundError(f"Report file '{clean_name}' not found.")

        return valid_path


reporting_service = APIReportingService()
