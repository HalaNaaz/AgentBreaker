"""Analytics engine for OWASP LLM Top 10, MITRE ATLAS, and executive summaries."""

from agentbreaker.reporting.models import (
    ExecutiveSummary,
    FindingDetail,
    MitreAtlasRecord,
    OWASPRecord,
    SeverityDistribution,
    VerdictDistribution,
)
from agentbreaker.reporting.redaction import redact_dict, redact_string
from agentbreaker.schemas.enums import Verdict
from agentbreaker.schemas.result import EvaluationResult

OWASP_CATALOG = [
    ("LLM01", "LLM01: Prompt Injection"),
    ("LLM02", "LLM02: Sensitive Information Disclosure"),
    ("LLM03", "LLM03: Supply Chain Vulnerabilities"),
    ("LLM04", "LLM04: Data and Model Poisoning"),
    ("LLM05", "LLM05: Improper Output Handling"),
    ("LLM06", "LLM06: Excessive Agency"),
    ("LLM07", "LLM07: System Prompt Leakage"),
    ("LLM08", "LLM08: Vector and Embedding Weaknesses"),
    ("LLM09", "LLM09: Misinformation"),
    ("LLM10", "LLM10: Unbounded Consumption"),
]

MITRE_ATLAS_CATALOG = {
    "AML.T0054": "LLM Jailbreak",
    "AML.T0051": "LLM Prompt Injection",
    "AML.T0053": "LLM Model Inversion / Execution",
    "AML.T0055": "Execution via Unsafe Tool Invocation",
    "AML.T0056": "System Prompt Extraction",
    "AML.T0057": "LLM Data Extraction",
    "AML.T0043": "Craft Adversarial Data",
    "AML.T0040": "ML Model Inference API Access",
}


def build_owasp_coverage(results: list[EvaluationResult]) -> list[OWASPRecord]:
    """Map evaluation results to the OWASP Top 10 for LLMs without inventing missing data."""
    records: list[OWASPRecord] = []

    for code, title in OWASP_CATALOG:
        matching = [
            r
            for r in results
            if r.owasp_id and (code in r.owasp_id.upper() or r.owasp_id.startswith(code))
        ]
        tested = len(matching) > 0
        v_count = sum(1 for r in matching if r.verdict == Verdict.VULNERABLE)
        f_ids = [r.payload_id for r in matching if r.verdict == Verdict.VULNERABLE]

        limitation = (
            None
            if tested
            else "Untested: No attack payloads in this assessment evaluated this category."
        )

        records.append(
            OWASPRecord(
                owasp_code=code,
                title=title,
                tested=tested,
                evaluated_count=len(matching),
                vulnerable_count=v_count,
                finding_ids=f_ids,
                limitation_note=limitation,
            )
        )
    return records


def build_mitre_atlas_coverage(results: list[EvaluationResult]) -> list[MitreAtlasRecord]:
    """Compile MITRE ATLAS technique coverage observed in evaluation records."""
    technique_ids: set[str] = set()
    for r in results:
        if r.mitre_atlas_id:
            technique_ids.add(r.mitre_atlas_id.strip())

    records: list[MitreAtlasRecord] = []
    for t_id in sorted(technique_ids):
        matching = [r for r in results if r.mitre_atlas_id and r.mitre_atlas_id.strip() == t_id]
        v_count = sum(1 for r in matching if r.verdict == Verdict.VULNERABLE)
        f_ids = [r.payload_id for r in matching if r.verdict == Verdict.VULNERABLE]

        tech_name = MITRE_ATLAS_CATALOG.get(t_id, "Unavailable")

        records.append(
            MitreAtlasRecord(
                technique_id=t_id,
                technique_name=tech_name,
                tested=True,
                evaluated_count=len(matching),
                vulnerable_count=v_count,
                finding_ids=f_ids,
            )
        )
    return records


def compile_findings(
    results: list[EvaluationResult],
    assessment_id: str,
) -> list[FindingDetail]:
    """Compile granular technical finding details from stored evaluation results."""
    findings: list[FindingDetail] = []
    seen_ids: dict[str, int] = {}
    for r in results:
        base_fid = f"{assessment_id}_{r.payload_id}"
        count = seen_ids.get(base_fid, 0)
        seen_ids[base_fid] = count + 1
        f_id = base_fid if count == 0 else f"{base_fid}_{count}"

        is_variant = bool(r.parent_id)

        # Sanitize sensitive content within evidence and findings
        sanitized_reasons = [redact_string(reason) for reason in r.reasons]
        sanitized_evidence = [redact_dict(ev) if isinstance(ev, dict) else ev for ev in r.evidence]
        sanitized_patterns = [redact_string(p) for p in r.matched_patterns]
        sanitized_canaries = [redact_string(c) for c in r.detected_canaries]
        sanitized_violations = [redact_string(t) for t in r.tool_call_violations]

        findings.append(
            FindingDetail(
                finding_id=f_id,
                assessment_id=assessment_id,
                payload_id=r.payload_id,
                parent_id=r.parent_id,
                is_variant=is_variant,
                category=r.category,
                verdict=r.verdict,
                severity=r.severity,
                cvss_score=r.cvss_score,
                owasp_id=r.owasp_id,
                mitre_atlas_id=r.mitre_atlas_id,
                confidence=r.confidence,
                reasons=sanitized_reasons,
                evidence_items=sanitized_evidence,
                matched_patterns=sanitized_patterns,
                detected_canaries=sanitized_canaries,
                tool_call_violations=sanitized_violations,
                latency_ms=r.latency_ms,
                timestamp_utc=r.timestamp_utc,
            )
        )
    return findings


def build_executive_summary(
    assessment_id: str,
    target_id: str,
    target_model: str,
    verdicts: VerdictDistribution,
    severities: SeverityDistribution,
    results: list[EvaluationResult],
) -> ExecutiveSummary:
    """Synthesize executive research summary strictly distinguishing confirmed from heuristic."""
    confirmed: list[str] = []
    for r in results:
        if r.verdict == Verdict.VULNERABLE:
            if r.detected_canaries:
                sanitized_tokens = [redact_string(c) for c in r.detected_canaries]
                confirmed.append(
                    f"Canary secret leakage detected in payload {r.payload_id} "
                    f"(Tokens: {sanitized_tokens})"
                )
            if r.tool_call_violations:
                sanitized_tools = [redact_string(t) for t in r.tool_call_violations]
                confirmed.append(
                    f"Unauthorized tool invocation request in payload {r.payload_id} "
                    f"(Tools: {sanitized_tools})"
                )

    priorities: list[str] = []
    if severities.critical > 0 or severities.high > 0:
        priorities.append(
            f"Remediate {severities.critical} CRITICAL and {severities.high} HIGH findings "
            "by hardening model instructions."
        )
    if any(r.tool_call_violations for r in results):
        priorities.append(
            "Implement strict deterministic server-side authorization boundaries for tools "
            "to prevent unauthorized function calls."
        )
    if verdicts.inconclusive > 0:
        priorities.append(
            f"Review {verdicts.inconclusive} inconclusive test cases caused by network timeouts "
            "or ambiguous model responses."
        )

    if not priorities:
        priorities.append(
            "Maintain continuous regression testing as model weights or prompts evolve."
        )

    verdict_summary = (
        f"Evaluated {verdicts.total} adversarial test vectors: {verdicts.vulnerable} confirmed "
        f"vulnerable ({verdicts.vulnerable_rate}%), {verdicts.defended} defended "
        f"({verdicts.defended_rate}%), and {verdicts.inconclusive} inconclusive "
        f"({verdicts.inconclusive_rate}%)."
    )

    limitations = [
        "Evaluations represent empirical observations and do not mathematically prove absolute "
        "security.",
        "Model behavior may vary due to sampling temperature, infrastructure updates, or "
        "context shifts.",
        "Heuristic analysis and LLM-as-a-judge observations require empirical verification.",
    ]

    return ExecutiveSummary(
        purpose="Adversarial vulnerability assessment and safety boundary verification.",
        scope_description=f"Evaluation of target '{target_id}' using AgentBreaker test suite.",
        target_summary=f"Target ID: {target_id} | Model Identifier: {target_model}",
        total_evaluations=verdicts.total,
        verdict_summary=verdict_summary,
        critical_vulnerabilities=severities.critical,
        high_vulnerabilities=severities.high,
        medium_vulnerabilities=severities.medium,
        low_vulnerabilities=severities.low,
        confirmed_compromises=confirmed[:5],
        key_limitations=limitations,
        remediation_priorities=priorities,
    )
