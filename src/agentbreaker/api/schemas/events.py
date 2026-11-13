"""Structured WebSocket event schema for real-time assessment streaming."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AssessmentEvent(BaseModel):
    """Structured telemetry event emitted during live assessment orchestration."""

    event_id: str = Field(
        default_factory=lambda: f"EVT-{uuid.uuid4().hex[:12].upper()}",
        description="Globally unique telemetry event identifier.",
    )
    assessment_id: str = Field(..., description="Target assessment identifier.")
    event_type: str = Field(
        ...,
        description="Type of event (e.g. 'assessment.started', 'assessment.completed').",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of event generation.",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured contextual payload data associated with the event.",
    )
