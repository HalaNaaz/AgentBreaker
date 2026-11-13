"""Historical assessment comparison service across multiple evaluation runs."""

import uuid
from datetime import UTC, datetime
from typing import Any

from agentbreaker.reporting.models import AssessmentComparison
from agentbreaker.schemas.enums import Verdict
from agentbreaker.schemas.result import EvaluationResult


class AssessmentComparator:
    """Compares historical assessment evaluation records with explicit compatibility guards."""

    def compare(
        self,
        assessments: list[tuple[dict[str, Any], list[EvaluationResult]]],
    ) -> AssessmentComparison:
        """Execute structured comparative analysis across two or more assessments."""
        if len(assessments) < 2:
            raise ValueError("Comparison requires at least two assessments.")

        comp_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"
        asm_ids = [meta.get("assessment_id", meta.get("id", "Unknown")) for meta, _ in assessments]
        targets = [
            meta.get("target_id", meta.get("metadata", {}).get("target_id", "Unknown"))
            for meta, _ in assessments
        ]
        models = [
            meta.get("target_model", meta.get("metadata", {}).get("target_model", "Unknown"))
            for meta, _ in assessments
        ]

        warnings: list[str] = []
        # Target compatibility check
        if len(set(targets)) > 1:
            warnings.append(
                f"Targets differ across assessments ({', '.join(set(targets))}). "
                "Differences reflect architectural divergence rather than defensive progression."
            )
        if len(set(models)) > 1:
            warnings.append(f"Target models differ across assessments ({', '.join(set(models))}).")

        is_compatible = len(warnings) == 0

        verdict_deltas: dict[str, dict[str, int]] = {}
        severity_deltas: dict[str, dict[str, int]] = {}
        category_deltas: dict[str, dict[str, int]] = {}

        assessment_vulns: list[set[str]] = []

        for idx, (_meta, results) in enumerate(assessments):
            a_id = asm_ids[idx]
            v_counts = {
                "vulnerable": sum(1 for r in results if r.verdict == Verdict.VULNERABLE),
                "defended": sum(1 for r in results if r.verdict == Verdict.DEFENDED),
                "inconclusive": sum(1 for r in results if r.verdict == Verdict.INCONCLUSIVE),
            }
            verdict_deltas[a_id] = v_counts

            s_counts = {
                "critical": sum(
                    1
                    for r in results
                    if r.verdict == Verdict.VULNERABLE and r.severity.value == "critical"
                ),
                "high": sum(
                    1
                    for r in results
                    if r.verdict == Verdict.VULNERABLE and r.severity.value == "high"
                ),
                "medium": sum(
                    1
                    for r in results
                    if r.verdict == Verdict.VULNERABLE and r.severity.value == "medium"
                ),
                "low": sum(
                    1
                    for r in results
                    if r.verdict == Verdict.VULNERABLE and r.severity.value == "low"
                ),
            }
            severity_deltas[a_id] = s_counts

            c_counts: dict[str, int] = {}
            for r in results:
                cat_val = r.category.value
                if r.verdict == Verdict.VULNERABLE:
                    c_counts[cat_val] = c_counts.get(cat_val, 0) + 1
            category_deltas[a_id] = c_counts

            vuln_set = {r.payload_id for r in results if r.verdict == Verdict.VULNERABLE}
            assessment_vulns.append(vuln_set)

        # Baseline (first) vs Latest (last) comparison
        earlier_vulns = assessment_vulns[0]
        latest_vulns = assessment_vulns[-1]

        latest_results = assessments[-1][1]
        latest_all = {r.payload_id for r in latest_results}
        latest_defended = {r.payload_id for r in latest_results if r.verdict == Verdict.DEFENDED}

        # True resolution requires confirmed defense in latest run
        resolved = sorted(earlier_vulns & latest_defended)
        new_vulns = sorted(latest_vulns - earlier_vulns)
        persistent = sorted(earlier_vulns & latest_vulns)

        omitted_from_latest = sorted(earlier_vulns - latest_all)

        notes: list[str] = [
            f"Comparing baseline {asm_ids[0]} against latest {asm_ids[-1]}.",
            f"Resolved vulnerabilities (confirmed defended): {len(resolved)}.",
            f"New vulnerabilities discovered: {len(new_vulns)}.",
            f"Persistent vulnerabilities across runs: {len(persistent)}.",
        ]
        if omitted_from_latest:
            notes.append(
                f"Notice: {len(omitted_from_latest)} baseline vulnerabilities were omitted in "
                "the latest assessment and cannot be verified as resolved."
            )
        if not is_compatible:
            notes.append(
                "Notice: Assessments evaluated distinct target profiles; metrics are non-causal."
            )

        return AssessmentComparison(
            comparison_id=comp_id,
            assessment_ids=asm_ids,
            generated_at=datetime.now(UTC).isoformat(),
            target_ids=targets,
            is_compatible=is_compatible,
            compatibility_warnings=warnings,
            verdict_deltas=verdict_deltas,
            severity_deltas=severity_deltas,
            category_deltas=category_deltas,
            new_vulnerabilities=new_vulns,
            resolved_vulnerabilities=resolved,
            persistent_vulnerabilities=persistent,
            comparative_notes=notes,
        )
