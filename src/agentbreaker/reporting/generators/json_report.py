"""JSON format report generator producing structured, validated research data."""

from agentbreaker.reporting.base import BaseReportGenerator
from agentbreaker.reporting.models import AssessmentReport, ReportFormat
from agentbreaker.reporting.serializers import serialize_report_to_json


class JsonReportGenerator(BaseReportGenerator):
    """Generates structured JSON security evaluation reports."""

    @property
    def report_format(self) -> ReportFormat:
        return ReportFormat.JSON

    def generate(self, report: AssessmentReport) -> str:
        """Render report into formatted, redacted JSON string."""
        return serialize_report_to_json(report, indent=2)
