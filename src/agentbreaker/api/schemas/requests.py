"""Request payload schemas for AgentBreaker HTTP API."""

from pydantic import BaseModel, Field

from agentbreaker.reporting.models import ReportFormat
from agentbreaker.schemas.enums import AttackCategory, TargetType


class TargetCreateRequest(BaseModel):
    """Request model for provisioning an authorized target configuration."""

    target_id: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Unique identifier for target configuration.",
    )
    endpoint_url: str = Field(
        ...,
        description="Valid HTTP/HTTPS target endpoint URL (loopback or authorized server).",
    )
    target_type: TargetType = Field(
        default=TargetType.OPENAI_COMPATIBLE,
        description="Target connection interface adapter category.",
    )
    model_name: str = Field(
        default="mock-model",
        min_length=1,
        max_length=128,
        description="Target model identifier passed in requests.",
    )
    api_key: str | None = Field(
        default=None,
        description="Authentication API key. Stored masked and never returned in plaintext.",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers sent with target requests.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Target request timeout limit in seconds.",
    )
    max_concurrency: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Max concurrent HTTP requests to dispatch to target.",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Max retry attempts on transient network or 5xx failures.",
    )


class TargetUpdateRequest(BaseModel):
    """Request model for updating an existing target configuration."""

    endpoint_url: str | None = None
    target_type: TargetType | None = None
    model_name: str | None = None
    api_key: str | None = None
    headers: dict[str, str] | None = None
    timeout_seconds: float | None = Field(default=None, ge=1.0, le=300.0)
    max_concurrency: int | None = Field(default=None, ge=1, le=50)
    max_retries: int | None = Field(default=None, ge=0, le=10)


class AssessmentCreateRequest(BaseModel):
    """Request model for defining a new assessment evaluation run."""

    name: str = Field(
        default="Adversarial Assessment Run",
        min_length=1,
        max_length=128,
        description="Human-readable title for the assessment.",
    )
    target_id: str = Field(
        ...,
        description="Identifier of pre-configured, authorized target.",
    )
    attack_categories: list[AttackCategory] = Field(
        default_factory=list,
        description="List of attack categories to include. Empty implies all categories.",
    )
    selected_payloads: list[str] = Field(
        default_factory=list,
        description="Specific payload IDs to execute. Empty or ['all'] includes all matching.",
    )
    enable_mutation: bool = Field(
        default=False,
        description="Whether adversarial mutation engine is enabled (opt-in only).",
    )
    mutation_strategies: list[str] = Field(
        default_factory=lambda: ["base64", "rot13"],
        description="Mutation strategies to apply if mutation is enabled.",
    )
    max_variants_per_payload: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Max mutated variants to generate per seed payload.",
    )
    concurrency: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Concurrent attack execution bounds.",
    )


class MutationPreviewRequest(BaseModel):
    """Request model to preview payload mutation without dispatching."""

    payload_id: str = Field(..., description="Base payload ID to mutate.")
    strategies: list[str] = Field(
        default_factory=lambda: ["base64", "rot13"],
        description="Mutation strategies to test.",
    )
    max_variants: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum variants to generate in preview.",
    )


class ReportGenerateRequest(BaseModel):
    """Request model to generate and persist a research audit report."""

    format: ReportFormat = Field(
        default=ReportFormat.JSON,
        description="Target report format ('json', 'markdown', or 'html').",
    )
    overwrite: bool = Field(
        default=True,
        description="Whether to overwrite existing report files with same name.",
    )


class AssessmentCompareRequest(BaseModel):
    """Request model to compare two or more historical assessments."""

    assessment_ids: list[str] = Field(
        ...,
        min_length=2,
        description="List of two or more assessment identifiers to compare.",
    )
    labels: list[str] | None = Field(
        default=None,
        description="Optional friendly labels corresponding to each assessment ID.",
    )
