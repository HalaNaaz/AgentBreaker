"""Attack execution data model capturing dispatch inputs, observed responses, and telemetry."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentbreaker.schemas.target import TargetResponse


class AttackExecution(BaseModel):
    """Record of a dispatched attack probe against a target connector."""

    model_config = ConfigDict(extra="forbid")

    payload_id: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="Identifier of the payload that was executed.",
    )
    prompt_sent: str = Field(
        ...,
        description="The actual prompt text delivered to the target.",
    )
    response: TargetResponse | None = Field(
        default=None,
        description="Observed target response if network dispatch completed.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed before or during network dispatch.",
    )
    latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Observed round-trip latency in milliseconds.",
    )
    is_success: bool = Field(
        default=True,
        description="Indicates whether the probe completed network transmission successfully.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional execution metadata and diagnostics.",
    )
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of execution.",
    )
