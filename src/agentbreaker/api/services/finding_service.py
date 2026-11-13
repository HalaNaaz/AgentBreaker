"""Findings inspection service extracting and querying technical audit findings."""

import contextlib

from agentbreaker.api.exceptions import ResourceNotFoundError
from agentbreaker.cli.storage import StorageManager, storage
from agentbreaker.reporting.analytics import compile_findings
from agentbreaker.reporting.models import FindingDetail
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


class FindingService:
    """Service providing filtering, sorting, and detail retrieval for evaluation findings."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage

    def _load_findings_for_assessment(self, assessment_id: str) -> list[FindingDetail]:
        """Load and compile finding details for a single assessment."""
        res_data = self.storage.get_results(assessment_id)
        if not res_data:
            return []

        raw_results = res_data.get("results", [])
        results: list[EvaluationResult] = []
        for r in raw_results:
            with contextlib.suppress(Exception):
                results.append(EvaluationResult.model_validate(r))

        return compile_findings(results, assessment_id=assessment_id)

    def list_findings(
        self,
        assessment_id: str | None = None,
        severity: Severity | None = None,
        verdict: Verdict | None = None,
        category: AttackCategory | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FindingDetail], int]:
        """Query findings across one or all stored assessments with comprehensive filters."""
        if assessment_id:
            asm_ids = [assessment_id]
        else:
            ids_from_asms = {
                asm.get("id") for asm in self.storage.list_assessments() if asm.get("id")
            }
            ids_from_results = (
                {
                    p.stem.replace("_results", "")
                    for p in self.storage.results_dir.glob("*_results.json")
                }
                if self.storage.results_dir.exists()
                else set()
            )
            asm_ids = sorted(ids_from_asms | ids_from_results)

        all_findings: list[FindingDetail] = []
        for a_id in asm_ids:
            all_findings.extend(self._load_findings_for_assessment(a_id))

        filtered: list[FindingDetail] = []
        for f in all_findings:
            if severity and f.severity != severity:
                continue
            if verdict and f.verdict != verdict:
                continue
            if category and f.category != category:
                continue
            if search:
                q = search.lower()
                text_match = (
                    q in f.finding_id.lower()
                    or q in f.payload_id.lower()
                    or any(q in r.lower() for r in f.reasons)
                    or (f.owasp_id and q in f.owasp_id.lower())
                    or (f.mitre_atlas_id and q in f.mitre_atlas_id.lower())
                )
                if not text_match:
                    continue
            filtered.append(f)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        return filtered[start:end], total

    def get_finding(self, finding_id: str) -> FindingDetail:
        """Find a specific finding by its unique identifier."""
        # Try finding in assessment derived from finding_id prefix or scan
        parts = finding_id.split("_", 1)
        if len(parts) == 2:
            candidate_asm = parts[0]
            findings = self._load_findings_for_assessment(candidate_asm)
            for f in findings:
                if f.finding_id == finding_id:
                    return f

        # Fallback scan all assessments
        for asm in self.storage.list_assessments():
            a_id = asm.get("id")
            if a_id:
                for f in self._load_findings_for_assessment(a_id):
                    if f.finding_id == finding_id:
                        return f

        raise ResourceNotFoundError(f"Finding '{finding_id}' not found.")


finding_service = FindingService()
