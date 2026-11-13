"""Convenience builders for typed live progress events."""

from agentbreaker.api.schemas.events import AssessmentEvent


def event_assessment_started(
    assessment_id: str, total_payloads: int, target_id: str
) -> AssessmentEvent:
    """Generate assessment.started event."""
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="assessment.started",
        data={
            "total_payloads": total_payloads,
            "target_id": target_id,
        },
    )


def event_payload_progress(
    assessment_id: str,
    current: int,
    total: int,
    payload_id: str,
) -> AssessmentEvent:
    """Generate payload.completed event."""
    percent = round((current / total) * 100.0, 1) if total > 0 else 0.0
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="payload.completed",
        data={
            "current": current,
            "total": total,
            "percent": percent,
            "payload_id": payload_id,
        },
    )


def event_finding_detected(
    assessment_id: str,
    payload_id: str,
    verdict: str,
    severity: str,
) -> AssessmentEvent:
    """Generate finding.detected event."""
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="finding.detected",
        data={
            "payload_id": payload_id,
            "verdict": verdict,
            "severity": severity,
        },
    )


def event_assessment_completed(
    assessment_id: str,
    total: int,
    vulnerable_count: int,
    defended_count: int,
    inconclusive_count: int,
) -> AssessmentEvent:
    """Generate assessment.completed event."""
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="assessment.completed",
        data={
            "total_evaluated": total,
            "vulnerable_count": vulnerable_count,
            "defended_count": defended_count,
            "inconclusive_count": inconclusive_count,
        },
    )


def event_assessment_cancelled(assessment_id: str, current: int, total: int) -> AssessmentEvent:
    """Generate assessment.cancelled event."""
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="assessment.cancelled",
        data={
            "completed_payloads": current,
            "total_payloads": total,
        },
    )


def event_assessment_failed(assessment_id: str, error_message: str) -> AssessmentEvent:
    """Generate assessment.failed event."""
    return AssessmentEvent(
        assessment_id=assessment_id,
        event_type="assessment.failed",
        data={
            "error": error_message,
        },
    )
