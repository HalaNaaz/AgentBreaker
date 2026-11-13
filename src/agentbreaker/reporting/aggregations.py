"""Deterministic aggregation functions for assessment metrics and evaluation results."""

from typing import Any

from agentbreaker.reporting.models import (
    CategoryMetric,
    EvidenceMetrics,
    MutationMetrics,
    SeverityDistribution,
    VerdictDistribution,
)
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def compute_verdict_distribution(results: list[EvaluationResult]) -> VerdictDistribution:
    """Compute counts and percentage rates for evaluation verdicts safely without div-by-zero."""
    total = len(results)
    if total == 0:
        return VerdictDistribution()

    v_count = sum(1 for r in results if r.verdict == Verdict.VULNERABLE)
    d_count = sum(1 for r in results if r.verdict == Verdict.DEFENDED)
    i_count = sum(1 for r in results if r.verdict == Verdict.INCONCLUSIVE)

    return VerdictDistribution(
        total=total,
        vulnerable=v_count,
        defended=d_count,
        inconclusive=i_count,
        error=0,
        vulnerable_rate=round((v_count / total) * 100.0, 2),
        defended_rate=round((d_count / total) * 100.0, 2),
        inconclusive_rate=round((i_count / total) * 100.0, 2),
    )


def compute_severity_distribution(results: list[EvaluationResult]) -> SeverityDistribution:
    """Compute distribution of severity for confirmed vulnerabilities."""
    vulns = [r for r in results if r.verdict == Verdict.VULNERABLE]
    dist = SeverityDistribution()
    for v in vulns:
        if v.severity == Severity.CRITICAL:
            dist.critical += 1
        elif v.severity == Severity.HIGH:
            dist.high += 1
        elif v.severity == Severity.MEDIUM:
            dist.medium += 1
        elif v.severity == Severity.LOW:
            dist.low += 1
        else:
            dist.informational += 1
    return dist


def compute_category_metrics(results: list[EvaluationResult]) -> list[CategoryMetric]:
    """Compute granular metrics per attack category."""
    metrics: list[CategoryMetric] = []

    for cat in AttackCategory:
        cat_results = [r for r in results if r.category == cat]
        total = len(cat_results)
        v_count = sum(1 for r in cat_results if r.verdict == Verdict.VULNERABLE)
        d_count = sum(1 for r in cat_results if r.verdict == Verdict.DEFENDED)
        i_count = sum(1 for r in cat_results if r.verdict == Verdict.INCONCLUSIVE)

        rate = round((v_count / total) * 100.0, 2) if total > 0 else 0.0

        metrics.append(
            CategoryMetric(
                category=cat,
                name=cat.value.replace("_", " ").title(),
                total_evaluated=total,
                vulnerable_count=v_count,
                defended_count=d_count,
                inconclusive_count=i_count,
                vulnerability_rate=rate,
            )
        )
    return metrics


def compute_mutation_metrics(
    results: list[EvaluationResult],
    metadata: dict[str, Any] | None = None,
) -> MutationMetrics:
    """Analyze baseline vs mutated adversarial variant performance and parental lineage."""
    meta = metadata or {}
    mutation_enabled = bool(meta.get("mutation_enabled", False))

    original_results = [r for r in results if not r.parent_id]
    variant_results = [r for r in results if bool(r.parent_id)]

    # If any variants exist even if flag was omitted in metadata, detect mutation
    if variant_results:
        mutation_enabled = True

    strategies: set[str] = set()
    strat_dist: dict[str, int] = {}
    lineage_map: dict[str, list[str]] = {}

    for var in variant_results:
        parent = str(var.parent_id)
        lineage_map.setdefault(parent, []).append(var.payload_id)

        # Strategy inference from payload suffix or metadata
        strat = "unknown"
        if "_ROT" in var.payload_id:
            strat = "rot13"
        elif "_B64" in var.payload_id:
            strat = "base64"
        elif "_LEET" in var.payload_id:
            strat = "leetspeak"
        elif "_MD" in var.payload_id:
            strat = "markdown_obfuscation"

        strategies.add(strat)
        strat_dist[strat] = strat_dist.get(strat, 0) + 1

    base_vuln = sum(1 for r in original_results if r.verdict == Verdict.VULNERABLE)
    var_vuln = sum(1 for r in variant_results if r.verdict == Verdict.VULNERABLE)

    return MutationMetrics(
        mutation_enabled=mutation_enabled,
        original_payload_count=len(original_results),
        variant_payload_count=len(variant_results),
        strategies_used=sorted(strategies),
        strategy_distribution=strat_dist,
        baseline_vulnerable_count=base_vuln,
        variant_vulnerable_count=var_vuln,
        lineage_map=lineage_map,
    )


def compute_evidence_metrics(results: list[EvaluationResult]) -> EvidenceMetrics:
    """Aggregate evidence items and calculate confidence distribution."""
    total_items = 0
    eval_dist: dict[str, int] = {}
    type_dist: dict[str, int] = {}
    conf_scores: list[float] = []
    conf_dist = {"high": 0, "medium": 0, "low": 0}
    confirmed_count = 0
    heuristic_count = 0

    for r in results:
        conf_scores.append(r.confidence)
        if r.confidence >= 0.85:
            conf_dist["high"] += 1
        elif r.confidence >= 0.50:
            conf_dist["medium"] += 1
        else:
            conf_dist["low"] += 1

        for ev in r.evidence:
            total_items += 1
            evaluator = str(ev.get("evaluator_name", "unknown"))
            ev_type = str(ev.get("evidence_type", "unknown"))

            eval_dist[evaluator] = eval_dist.get(evaluator, 0) + 1
            type_dist[ev_type] = type_dist.get(ev_type, 0) + 1

            if evaluator in ("llm_judge", "heuristic"):
                heuristic_count += 1
            else:
                confirmed_count += 1

    mean_conf = round(sum(conf_scores) / len(conf_scores), 2) if conf_scores else 0.0

    return EvidenceMetrics(
        total_evidence_items=total_items,
        evaluator_distribution=eval_dist,
        evidence_type_distribution=type_dist,
        mean_confidence=mean_conf,
        confidence_distribution=conf_dist,
        confirmed_evidence_count=confirmed_count,
        heuristic_evidence_count=heuristic_count,
    )
