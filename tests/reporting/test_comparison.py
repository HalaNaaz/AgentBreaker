"""Tests for historical assessment comparison service."""

import pytest

from agentbreaker.reporting.comparison import AssessmentComparator
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict
from agentbreaker.schemas.result import EvaluationResult


def test_comparison_compatible_assessments() -> None:
    """Verify comparing two compatible runs on the same target."""
    meta1 = {"id": "ASM-001", "target_id": "llm-1", "target_model": "gpt-4o"}
    results1 = [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
        ),
        EvaluationResult(
            payload_id="JB-002",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
        ),
    ]

    meta2 = {"id": "ASM-002", "target_id": "llm-1", "target_model": "gpt-4o"}
    results2 = [
        EvaluationResult(
            payload_id="JB-001",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.DEFENDED,
            severity=Severity.HIGH,
        ),
        EvaluationResult(
            payload_id="JB-002",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.HIGH,
        ),
        EvaluationResult(
            payload_id="JB-003",
            category=AttackCategory.DIRECT_JAILBREAK,
            verdict=Verdict.VULNERABLE,
            severity=Severity.MEDIUM,
        ),
    ]

    comparator = AssessmentComparator()
    comp = comparator.compare([(meta1, results1), (meta2, results2)])

    assert comp.is_compatible is True
    assert len(comp.compatibility_warnings) == 0
    # JB-001 was vulnerable in ASM-001, defended in ASM-002 -> resolved
    assert "JB-001" in comp.resolved_vulnerabilities
    # JB-003 is new vulnerable in ASM-002
    assert "JB-003" in comp.new_vulnerabilities
    # JB-002 remained vulnerable
    assert "JB-002" in comp.persistent_vulnerabilities


def test_comparison_incompatible_targets_warning() -> None:
    """Verify comparison across different targets produces compatibility warnings."""
    meta1 = {"id": "ASM-001", "target_id": "target-a", "target_model": "model-a"}
    meta2 = {"id": "ASM-002", "target_id": "target-b", "target_model": "model-b"}

    comparator = AssessmentComparator()
    comp = comparator.compare([(meta1, []), (meta2, [])])

    assert comp.is_compatible is False
    assert len(comp.compatibility_warnings) > 0
    assert any("Targets differ" in w for w in comp.compatibility_warnings)


def test_comparison_fewer_than_two_raises() -> None:
    """Verify comparing fewer than 2 assessments raises ValueError."""
    comparator = AssessmentComparator()
    with pytest.raises(ValueError, match="requires at least two"):
        comparator.compare([({"id": "A"}, [])])
