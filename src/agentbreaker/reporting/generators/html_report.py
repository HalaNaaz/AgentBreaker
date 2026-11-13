"""HTML format report generator using Jinja2 with strict autoescaping."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentbreaker.reporting.base import BaseReportGenerator
from agentbreaker.reporting.models import AssessmentReport, ReportFormat


class HtmlReportGenerator(BaseReportGenerator):
    """Renders standalone HTML reports using secure Jinja2 autoescaping."""

    def __init__(self, templates_dir: Path | str | None = None) -> None:
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).parent.parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml", "j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    @property
    def report_format(self) -> ReportFormat:
        return ReportFormat.HTML

    def generate(self, report: AssessmentReport) -> str:
        """Render the complete AssessmentReport model into an HTML document."""
        template = self.env.get_template("report.html.j2")
        return template.render(report=report)
