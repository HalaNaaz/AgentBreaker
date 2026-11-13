"""Analytics aggregation and multi-assessment comparative service."""

import contextlib
from typing import Any

from agentbreaker.api.exceptions import ResourceNotFoundError, SecurityValidationError
from agentbreaker.api.schemas.requests import AssessmentCompareRequest
from agentbreaker.api.schemas.responses import AnalyticsOverviewResponse
from agentbreaker.cli.storage import StorageManager, storage
from agentbreaker.reporting.analytics import (
    build_mitre_atlas_coverage,
    build_owasp_coverage,
)
from agentbreaker.reporting.comparison import AssessmentComparator
from agentbreaker.reporting.models import (
    AssessmentComparison,
)
from agentbreaker.reporting.service import ReportingService as CoreReportingService
from agentbreaker.schemas.result import EvaluationResult


class AnalyticsService:
    """Service providing macro and micro-level analytical metrics across assessments."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage
        self.comparator = AssessmentComparator()
        self.core_reporting = CoreReportingService(storage_manager=self.storage)

    def get_overview(self) -> AnalyticsOverviewResponse:
        """Compute aggregate high-level metrics across all completed assessments in storage."""
        ids_from_asms = {asm.get("id") for asm in self.storage.list_assessments() if asm.get("id")}
        ids_from_results = (
            {
                p.stem.replace("_results", "")
                for p in self.storage.results_dir.glob("*_results.json")
            }
            if self.storage.results_dir.exists()
            else set()
        )
        all_asm_ids = sorted(ids_from_asms | ids_from_results)

        total_evals = 0
        total_vuln = 0
        total_def = 0
        total_inconc = 0
        cat_vulns: dict[str, int] = {}

        for a_id in all_asm_ids:
            res_data = self.storage.get_results(a_id)
            if not res_data:
                continue

            raw_results = res_data.get("results", [])
            for r in raw_results:
                total_evals += 1
                v = r.get("verdict")
                cat = r.get("category", "unknown")
                if v == "VULNERABLE":
                    total_vuln += 1
                    cat_vulns[cat] = cat_vulns.get(cat, 0) + 1
                elif v == "DEFENDED":
                    total_def += 1
                elif v == "INCONCLUSIVE":
                    total_inconc += 1

        vuln_rate = round((total_vuln / total_evals) * 100.0, 2) if total_evals > 0 else 0.0

        top_cats = [
            {"category": k, "name": k.replace("_", " ").title(), "vulnerabilities": v}
            for k, v in sorted(cat_vulns.items(), key=lambda item: item[1], reverse=True)
        ]

        return AnalyticsOverviewResponse(
            total_assessments=len(all_asm_ids),
            total_evaluations=total_evals,
            total_vulnerabilities=total_vuln,
            total_defended=total_def,
            total_inconclusive=total_inconc,
            overall_vulnerability_rate=vuln_rate,
            top_vulnerable_categories=top_cats,
        )

    def get_assessment_analytics(
        self,
        assessment_id: str,
    ) -> dict[str, Any]:
        """Compile detailed framework coverage and evidence telemetry for a specific assessment."""
        res_data = self.storage.get_results(assessment_id)
        if not res_data:
            raise ResourceNotFoundError(f"Assessment results for '{assessment_id}' not found.")

        raw_results = res_data.get("results", [])

        results: list[EvaluationResult] = []
        for r in raw_results:
            with contextlib.suppress(Exception):
                results.append(EvaluationResult.model_validate(r))

        owasp = build_owasp_coverage(results)
        mitre = build_mitre_atlas_coverage(results)

        # Build report to extract unified metrics safely
        report = self.core_reporting.build_report(assessment_id)

        return {
            "assessment_id": assessment_id,
            "verdicts": report.verdicts.model_dump(),
            "severities": report.severities.model_dump(),
            "categories": [c.model_dump() for c in report.categories],
            "mutation_metrics": report.mutation_metrics.model_dump()
            if report.mutation_metrics
            else None,
            "evidence_metrics": report.evidence_metrics.model_dump(),
            "owasp_coverage": [o.model_dump() for o in owasp],
            "mitre_atlas_coverage": [m.model_dump() for m in mitre],
        }

    def compare(self, req: AssessmentCompareRequest) -> AssessmentComparison:
        """Execute historical regression and progression comparison across assessments."""
        try:
            return self.core_reporting.compare_assessments(
                assessment_ids=req.assessment_ids,
            )
        except Exception as err:
            raise SecurityValidationError(f"Comparison failed: {err}") from err


analytics_service = AnalyticsService()
