"""Markdown format report generator producing structured technical audit documentation."""

from agentbreaker.reporting.base import BaseReportGenerator
from agentbreaker.reporting.models import AssessmentReport, ReportFormat
from agentbreaker.reporting.redaction import redact_string


class MarkdownReportGenerator(BaseReportGenerator):
    """Renders comprehensive, publication-ready research reports in GitHub-Flavored Markdown."""

    @property
    def report_format(self) -> ReportFormat:
        return ReportFormat.MARKDOWN

    def generate(self, report: AssessmentReport) -> str:
        """Render complete AssessmentReport into structured Markdown document."""
        lines: list[str] = [
            f"# AgentBreaker Security Assessment Audit Report: {report.assessment_id}",
            "",
            "**Platform:** AgentBreaker — AI Red Teaming Framework  ",
            "**Organization:** AshlynxCyber Security Systems  ",
            f"**Report ID:** `{report.report_id}`  ",
            f"**Generated At (UTC):** {report.generated_at}  ",
            f"**Target System:** `{report.target_id}` (`{report.target_model}`)  ",
            f"**Target Provider:** {report.target_provider}  ",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            "",
            f"{report.executive_summary.verdict_summary}",
            "",
            f"- **Target Evaluated:** `{report.target_id}` ({report.target_model})",
            f"- **Total Payloads Tested:** {report.executive_summary.total_evaluations}",
            f"- **Critical Vulnerabilities:** {report.executive_summary.critical_vulnerabilities}",
            f"- **High Vulnerabilities:** {report.executive_summary.high_vulnerabilities}",
            f"- **Medium Vulnerabilities:** {report.executive_summary.medium_vulnerabilities}",
            f"- **Low Vulnerabilities:** {report.executive_summary.low_vulnerabilities}",
            "",
        ]

        # Key confirmed compromises
        if report.executive_summary.confirmed_compromises:
            lines.append("### Confirmed Compromise Highlights")
            for comp in report.executive_summary.confirmed_compromises:
                lines.append(f"- {redact_string(comp)}")
            lines.append("")

        # Remediation priorities
        if report.executive_summary.remediation_priorities:
            lines.append("### Recommended Remediation Priorities")
            for prio in report.executive_summary.remediation_priorities:
                lines.append(f"1. {redact_string(prio)}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 2. Evaluation Metrics & Verdict Breakdown",
                "",
                "| Verdict | Count | Rate (%) |",
                "|---|:---:|:---:|",
                f"| **Vulnerable** | {report.verdicts.vulnerable} | "
                f"{report.verdicts.vulnerable_rate}% |",
                f"| **Defended** | {report.verdicts.defended} | {report.verdicts.defended_rate}% |",
                f"| **Inconclusive** | {report.verdicts.inconclusive} | "
                f"{report.verdicts.inconclusive_rate}% |",
                f"| **Total** | {report.verdicts.total} | 100.0% |",
                "",
                "### Severity Distribution (Confirmed Vulnerabilities)",
                "",
                "| Severity | Count |",
                "|---|:---:|",
                f"| Critical | {report.severities.critical} |",
                f"| High | {report.severities.high} |",
                f"| Medium | {report.severities.medium} |",
                f"| Low | {report.severities.low} |",
                "",
                "---",
                "",
                "## 3. Attack Category Analysis",
                "",
                "| Category | Total | Vuln | Defended | Inconcl | Vuln Rate |",
                "|---|:---:|:---:|:---:|:---:|:---:|",
            ]
        )

        for cat in report.categories:
            lines.append(
                f"| **{cat.name}** | {cat.total_evaluated} | {cat.vulnerable_count} | "
                f"{cat.defended_count} | {cat.inconclusive_count} | {cat.vulnerability_rate}% |"
            )
        lines.append("")

        # Mutation analysis
        if report.mutation_metrics and report.mutation_metrics.mutation_enabled:
            strat_str = ", ".join(report.mutation_metrics.strategies_used) or "None"
            mm = report.mutation_metrics
            lines.extend(
                [
                    "---",
                    "",
                    "## 4. Adversarial Mutation & Lineage Analytics",
                    "",
                    f"- **Original Payloads:** {mm.original_payload_count}",
                    f"- **Mutated Variants:** {mm.variant_payload_count}",
                    f"- **Strategies Employed:** {strat_str}",
                    f"- **Baseline Vulnerable:** {mm.baseline_vulnerable_count}",
                    f"- **Variant Vulnerable:** {mm.variant_vulnerable_count}",
                    "",
                ]
            )

        # OWASP coverage
        lines.extend(
            [
                "---",
                "",
                "## 5. OWASP Top 10 for LLMs Coverage",
                "",
                "| OWASP Category | Tested? | Evaluated Cases | Confirmed Findings |",
                "|---|:---:|:---:|:---:|",
            ]
        )
        for o in report.owasp_coverage:
            tested_mark = "Yes" if o.tested else "Untested"
            lines.append(
                f"| **{o.title}** | {tested_mark} | {o.evaluated_count} | {o.vulnerable_count} |"
            )
        lines.append("")

        # MITRE ATLAS
        if report.mitre_coverage:
            lines.extend(
                [
                    "---",
                    "",
                    "## 6. MITRE ATLAS Matrix Mapping",
                    "",
                    "| Technique ID | Technique Name | Tested Cases | Confirmed Findings |",
                    "|---|---|:---:|:---:|",
                ]
            )
            for m in report.mitre_coverage:
                lines.append(
                    f"| `{m.technique_id}` | {m.technique_name} | "
                    f"{m.evaluated_count} | {m.vulnerable_count} |"
                )
            lines.append("")

        # Technical findings
        lines.extend(
            [
                "---",
                "",
                "## 7. Granular Technical Findings",
                "",
            ]
        )

        vuln_findings = [f for f in report.findings if f.verdict.value == "VULNERABLE"]
        if not vuln_findings:
            lines.append(
                "No confirmed security vulnerabilities were detected in this assessment run."
            )
            lines.append("")
        else:
            for f in vuln_findings:
                lines.append(f"### Finding `{f.finding_id}`")
                lines.append(f"- **Payload ID:** `{f.payload_id}`")
                if f.parent_id:
                    lines.append(f"- **Parent Payload ID (Lineage):** `{f.parent_id}`")
                lines.append(f"- **Category:** {f.category.value}")
                lines.append(
                    f"- **Severity:** {f.severity.value.upper()} (CVSS {f.cvss_score:.1f})"
                )
                lines.append(f"- **Confidence:** {f.confidence:.2f}")
                if f.owasp_id:
                    lines.append(f"- **OWASP:** {f.owasp_id}")
                if f.mitre_atlas_id:
                    lines.append(f"- **MITRE ATLAS:** {f.mitre_atlas_id}")

                if f.reasons:
                    lines.append("- **Evaluator Reasons:**")
                    for r in f.reasons:
                        lines.append(f"  - {redact_string(r)}")

                if f.matched_patterns:
                    lines.append(
                        f"- **Matched Patterns:** `{redact_string(str(f.matched_patterns))}`"
                    )
                if f.detected_canaries:
                    lines.append(f"- **Detected Canaries:** `{f.detected_canaries}`")
                if f.tool_call_violations:
                    lines.append(f"- **Tool Violations:** `{f.tool_call_violations}`")
                lines.append("")

        # Limitations & Recommendations
        lines.extend(
            [
                "---",
                "",
                "## 8. Assessment Limitations & Research Caveats",
                "",
            ]
        )
        for lim in report.limitations:
            lines.append(f"- {lim}")
        lines.append("")

        lines.extend(
            [
                "---",
                "",
                "## 9. Recommendations",
                "",
            ]
        )
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        return "\n".join(lines)
