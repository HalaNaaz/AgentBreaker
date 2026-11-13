"""Orchestration service for report generation, storage, and comparative analytics."""

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from agentbreaker.cli.storage import StorageManager, storage
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
from agentbreaker.reporting.exceptions import ReportNotFoundError
from agentbreaker.reporting.generators.html_report import HtmlReportGenerator
from agentbreaker.reporting.generators.json_report import JsonReportGenerator
from agentbreaker.reporting.generators.markdown_report import MarkdownReportGenerator
from agentbreaker.reporting.models import (
    AssessmentComparison,
    AssessmentReport,
    ReportFormat,
)
from agentbreaker.reporting.redaction import validate_report_path
from agentbreaker.schemas.result import EvaluationResult


class ReportingService:
    """Service orchestrating assessment analysis, report compilation, and multi-format exports."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage
        self.comparator = AssessmentComparator()
        self.generators = {
            ReportFormat.JSON: JsonReportGenerator(),
            ReportFormat.MARKDOWN: MarkdownReportGenerator(),
            ReportFormat.HTML: HtmlReportGenerator(),
        }

    def build_report(self, assessment_id: str) -> AssessmentReport:
        """Compile a fully populated AssessmentReport from stored assessment evaluation records."""
        res_data = self.storage.get_results(assessment_id)
        if not res_data:
            raise ReportNotFoundError(
                f"No results found for assessment '{assessment_id}'. Run assessment first."
            )

        metadata = res_data.get("metadata", {})
        raw_results = res_data.get("results", [])

        # Deserialize results
        results: list[EvaluationResult] = []
        for item in raw_results:
            try:
                results.append(EvaluationResult.model_validate(item))
            except (ValidationError, ValueError, KeyError):
                continue

        # If metadata is missing target info, try loading assessment definition
        asm_def = self.storage.get_assessment(assessment_id) or {}
        target_id = metadata.get("target_id") or asm_def.get("target_id", "Unknown")
        target_model = metadata.get("target_model") or asm_def.get("target_model", "Unknown")

        # Try to find target provider
        target_cfg = self.storage.get_target(target_id)
        target_provider = target_cfg.target_type.value if target_cfg else "Unknown"

        # Compute aggregations
        verdicts = compute_verdict_distribution(results)
        severities = compute_severity_distribution(results)
        categories = compute_category_metrics(results)
        mutation_metrics = compute_mutation_metrics(results, metadata=metadata)
        evidence_metrics = compute_evidence_metrics(results)

        # Build analytics
        owasp_coverage = build_owasp_coverage(results)
        mitre_coverage = build_mitre_atlas_coverage(results)
        findings = compile_findings(results, assessment_id=assessment_id)
        executive_summary = build_executive_summary(
            assessment_id=assessment_id,
            target_id=target_id,
            target_model=target_model,
            verdicts=verdicts,
            severities=severities,
            results=results,
        )

        # Standard research recommendations
        recommendations = [
            "Implement input content validation and boundary containment prior to LLM ingestion.",
            "Deploy deterministic canary tracking in workflows to alert on data exfiltration.",
            "Enforce tool parameter whitelisting and isolate tool execution from untrusted output.",
            "Execute automated regression testing with mutated prompts on prompt updates.",
        ]

        limitations = [
            "Evaluations reflect empirical target resistance under test environment parameters.",
            "Defended verdicts do not guarantee mathematical safety against novel vectors.",
            "Heuristic judge assessments should be verified against concrete violation markers.",
        ]

        report_id = f"RPT-{assessment_id}"
        generated_at = datetime.now(UTC).isoformat()

        return AssessmentReport(
            report_id=report_id,
            assessment_id=assessment_id,
            generated_at=generated_at,
            target_id=target_id,
            target_provider=target_provider,
            target_model=target_model,
            started_at=metadata.get("started_at"),
            completed_at=metadata.get("completed_at"),
            executive_summary=executive_summary,
            verdicts=verdicts,
            severities=severities,
            categories=categories,
            mutation_metrics=mutation_metrics,
            evidence_metrics=evidence_metrics,
            owasp_coverage=owasp_coverage,
            mitre_coverage=mitre_coverage,
            findings=findings,
            limitations=limitations,
            recommendations=recommendations,
        )

    def generate_report(
        self,
        assessment_id: str,
        output_format: ReportFormat = ReportFormat.JSON,
    ) -> str:
        """Build and render an assessment report into the specified format."""
        report = self.build_report(assessment_id)
        generator = self.generators.get(output_format)
        if not generator:
            raise ValueError(f"Unsupported report format: {output_format}")
        return generator.generate(report)

    def save_report(
        self,
        assessment_id: str,
        output_format: ReportFormat = ReportFormat.JSON,
        dest_path: Path | str | None = None,
    ) -> Path:
        """Generate and write report to disk atomically with path safety enforcement."""
        content = self.generate_report(assessment_id, output_format=output_format)
        ext = (
            "json"
            if output_format == ReportFormat.JSON
            else ("md" if output_format == ReportFormat.MARKDOWN else "html")
        )

        if dest_path:
            target_file = validate_report_path(dest_path)
        else:
            default_filename = f"RPT-{assessment_id}.{ext}"
            target_file = self.storage.reports_dir / default_filename

        target_file.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write
        tmp_file = target_file.with_suffix(f"{target_file.suffix}.tmp_{os.getpid()}")
        try:
            tmp_file.write_text(content, encoding="utf-8")
            os.replace(tmp_file, target_file)
        finally:
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except OSError:
                    pass

        return target_file

    def compare_assessments(
        self,
        assessment_ids: list[str],
    ) -> AssessmentComparison:
        """Compare two or more assessments by loading their evaluation records."""
        data_tuples: list[tuple[dict[str, Any], list[EvaluationResult]]] = []

        for a_id in assessment_ids:
            res_data = self.storage.get_results(a_id)
            if not res_data:
                raise ReportNotFoundError(f"Assessment '{a_id}' results not found.")
            meta = res_data.get("metadata", {})
            raw_results = res_data.get("results", [])
            results = [EvaluationResult.model_validate(r) for r in raw_results]
            data_tuples.append((meta, results))

        return self.comparator.compare(data_tuples)

    def list_reports(self) -> list[dict[str, Any]]:
        """List generated reports present in the reports directory."""
        reports: list[dict[str, Any]] = []
        if not self.storage.reports_dir.exists():
            return reports

        for item in sorted(
            self.storage.reports_dir.glob("RPT-*.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            ext = item.suffix.lstrip(".")
            reports.append(
                {
                    "report_file": item.name,
                    "format": ext,
                    "size_bytes": item.stat().st_size,
                    "path": str(item.resolve()),
                    "modified_at": datetime.fromtimestamp(item.stat().st_mtime, UTC).isoformat(),
                }
            )
        return reports
