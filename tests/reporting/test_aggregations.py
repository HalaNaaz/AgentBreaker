"""Tests for metrics aggregation functions."""

from agentbreaker.reporting.aggregations import (
    compute_category_metrics,
    compute_evidence_metrics,
    compute_mutation_metrics,
    compute_severity_distribution,
    compute_verdict_distribution,
)
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def _create_sample_results() -> list[EvaluationResult]:
    return [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
            cvss_score=7.5,
            confidence=0.95,
            evidence=[{"evaluator_name": "regex", "evidence_type": "pattern"}],
        ),
        EvaluationResult(
            payload_id="JB-001_ROT_1",
            parent_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
            cvss_score=0.0,
            confidence=0.90,
            evidence=[{"evaluator_name": "refusal", "evidence_type": "refusal_phrase"}],
        ),
        EvaluationResult(
            payload_id="EXT-001",
            category=AttackCategory.SYSTEM_EXTRACTION,
            verdict=Verdict.VULNERABLE,
            severity=Severity.CRITICAL,
            cvss_score=9.0,
            confidence=1.0,
            detected_canaries=["AGY-CANARY-1234"],
            evidence=[{"evaluator_name": "canary", "evidence_type": "canary_leak"}],
        ),
        EvaluationResult(
            payload_id="IND-001",
            category=AttackCategory.INDIRECT_INJECTION,
            verdict=Verdict.INCONCLUSIVE,
            severity=Severity.MEDIUM,
            cvss_score=0.0,
            confidence=0.45,
            evidence=[{"evaluator_name": "llm_judge", "evidence_type": "heuristic"}],
        ),
    ]


def test_compute_verdict_distribution() -> None:
    """Verify verdict aggregation and rates computation."""
    results = _create_sample_results()
    vd = compute_verdict_distribution(results)
    assert vd.total == 4
    assert vd.vulnerable == 2
    assert vd.defended == 1
    assert vd.inconclusive == 1
    assert vd.vulnerable_rate == 50.0
    assert vd.defended_rate == 25.0
    assert vd.inconclusive_rate == 25.0


def test_compute_verdict_distribution_empty() -> None:
    """Verify that empty result set does not trigger division by zero."""
    vd = compute_verdict_distribution([])
    assert vd.total == 0
    assert vd.vulnerable == 0
    assert vd.vulnerable_rate == 0.0


def test_compute_severity_distribution() -> None:
    """Verify severity distribution counts only vulnerable findings."""
    results = _create_sample_results()
    sd = compute_severity_distribution(results)
    assert sd.critical == 1  # EXT-001
    assert sd.high == 1  # JB-001
    assert sd.medium == 0
    assert sd.low == 0


def test_compute_category_metrics() -> None:
    """Verify category breakdown calculates rates correctly."""
    results = _create_sample_results()
    cats = compute_category_metrics(results)
    assert len(cats) == 4  # 4 attack categories

    jb = next(c for c in cats if c.category == AttackCategory.DIRECT_JAILBREAK)
    assert jb.total_evaluated == 2
    assert jb.vulnerable_count == 1
    assert jb.defended_count == 1
    assert jb.vulnerability_rate == 50.0


def test_compute_mutation_metrics() -> None:
    """Verify mutation analytics and parental lineage extraction."""
    results = _create_sample_results()
    mm = compute_mutation_metrics(results, metadata={"mutation_enabled": True})
    assert mm.mutation_enabled is True
    assert mm.original_payload_count == 3
    assert mm.variant_payload_count == 1
    assert "rot13" in mm.strategies_used
    assert "JB-001" in mm.lineage_map
    assert mm.lineage_map["JB-001"] == ["JB-001_ROT_1"]


def test_compute_evidence_metrics() -> None:
    """Verify structured evidence counting and mean confidence."""
    results = _create_sample_results()
    em = compute_evidence_metrics(results)
    assert em.total_evidence_items == 4
    assert em.confirmed_evidence_count == 3  # regex, refusal, canary
    assert em.heuristic_evidence_count == 1  # llm_judge
    assert em.mean_confidence > 0.8
    assert em.confidence_distribution["high"] == 3
    assert em.confidence_distribution["low"] == 1
