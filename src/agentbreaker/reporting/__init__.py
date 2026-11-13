"""AgentBreaker reporting and analytics subsystem."""

from agentbreaker.reporting.aggregations import (
    compute_category_metrics,
    compute_evidence_metrics,
    compute_mutation_metrics,
    compute_severity_distribution,
    compute_verdict_distribution,
)
from agentbreaker.reporting.analytics import (
    build_executive_summary,
    build_mitre_atlas_coverage,
    build_owasp_coverage,
    compile_findings,
)
from agentbreaker.reporting.comparison import AssessmentComparator
from agentbreaker.reporting.exceptions import (
    IncompatibleAssessmentError,
    InvalidReportPathError,
    RedactionError,
    ReportGenerationError,
    ReportingError,
    ReportNotFoundError,
)
from agentbreaker.reporting.generators.html_report import HtmlReportGenerator
from agentbreaker.reporting.generators.json_report import JsonReportGenerator
from agentbreaker.reporting.generators.markdown_report import MarkdownReportGenerator
from agentbreaker.reporting.models import (
    AssessmentComparison,
    AssessmentReport,
    CategoryMetric,
    EvidenceMetrics,
    ExecutiveSummary,
    FindingDetail,
    MitreAtlasRecord,
    MutationMetrics,
    OWASPRecord,
    ReportFormat,
    SeverityDistribution,
    VerdictDistribution,
)
from agentbreaker.reporting.redaction import (
    escape_html,
    redact_dict,
    redact_string,
    validate_report_path,
)
from agentbreaker.reporting.service import ReportingService

__all__ = [
    "AssessmentComparison",
    "AssessmentComparator",
    "AssessmentReport",
    "CategoryMetric",
    "EvidenceMetrics",
    "ExecutiveSummary",
    "FindingDetail",
    "HtmlReportGenerator",
    "IncompatibleAssessmentError",
    "InvalidReportPathError",
    "JsonReportGenerator",
    "MarkdownReportGenerator",
    "MitreAtlasRecord",
    "MutationMetrics",
    "OWASPRecord",
    "RedactionError",
    "ReportFormat",
    "ReportGenerationError",
    "ReportNotFoundError",
    "ReportingError",
    "ReportingService",
    "SeverityDistribution",
    "VerdictDistribution",
    "build_executive_summary",
    "build_mitre_atlas_coverage",
    "build_owasp_coverage",
    "compile_findings",
    "compute_category_metrics",
    "compute_evidence_metrics",
    "compute_mutation_metrics",
    "compute_severity_distribution",
    "compute_verdict_distribution",
    "escape_html",
    "redact_dict",
    "redact_string",
    "validate_report_path",
]
