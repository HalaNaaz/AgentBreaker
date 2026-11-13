"""Response models for AgentBreaker HTTP API with strict secret sanitization."""

from typing import Any

from pydantic import BaseModel, Field

from agentbreaker.schemas.enums import AttackCategory, Severity, TargetType


class HealthResponse(BaseModel):
    """Health check status representation."""

    status: str = "ok"
    version: str
    runtime_status: str = "healthy"
    storage_available: bool = True
    engine_available: bool = True
    timestamp: str


class SystemInfoResponse(BaseModel):
    """Diagnostic system metadata with zero secret disclosure."""

    name: str = "AgentBreaker"
    organization: str = "AshlynxCyber"
    version: str
    python_runtime: str
    os_platform: str
    registered_connectors: list[str]
    attack_categories: list[str]
    mutation_strategies: list[str]
    report_formats: list[str]


class SystemStatusResponse(BaseModel):
    """Real-time operational status of local engine."""

    status: str = "ONLINE"
    storage_ready: bool
    active_assessments_count: int
    running_task_ids: list[str]
    timestamp: str


class SystemCapabilitiesResponse(BaseModel):
    """Capabilities inventory exposed by backend."""

    attack_engine: bool = True
    mutation_engine: bool = True
    evaluation_oracle: bool = True
    reporting_engine: bool = True
    websockets_live_events: bool = True
    supported_connectors: list[str]
    supported_strategies: list[str]
    supported_frameworks: list[str] = ["OWASP Top 10 for LLMs 2025", "MITRE ATLAS"]


class TargetResponseModel(BaseModel):
    """Sanitized target configuration (secrets strictly masked)."""

    target_id: str
    endpoint_url: str
    target_type: TargetType
    model_name: str
    api_key_masked: str | None = None
    headers_keys: list[str] = Field(default_factory=list)
    timeout_seconds: float
    max_concurrency: int
    max_retries: int
    allow_redirects: bool = False


class TargetValidationResponse(BaseModel):
    """Target configuration verification report."""

    valid: bool
    target_id: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TargetTestResponse(BaseModel):
    """Connectivity test result against candidate target endpoint."""

    connected: bool
    target_id: str
    status_code: int | None = None
    latency_ms: float = 0.0
    message: str


class PayloadListItemResponse(BaseModel):
    """Brief metadata entry for payload browsing."""

    id: str
    category: AttackCategory
    name: str
    description: str | None = None
    severity: Severity = Severity.MEDIUM
    owasp_id: str | None = None
    mitre_atlas_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class CategorySummaryResponse(BaseModel):
    """Summary count per attack category."""

    category: AttackCategory
    name: str
    payload_count: int


class MutationStrategyResponse(BaseModel):
    """Available adversarial mutation strategy descriptor."""

    id: str
    name: str
    description: str


class MutationPreviewResponse(BaseModel):
    """Adversarial mutation preview results (non-dispatched)."""

    original_payload_id: str
    original_prompt: str
    generated_variants: list[dict[str, Any]]


class AssessmentListItemResponse(BaseModel):
    """Overview item for assessment lists."""

    assessment_id: str
    name: str
    target_id: str
    status: str
    created_at: str
    completed_at: str | None = None
    total_payloads: int = 0
    completed_payloads: int = 0
    vulnerable_count: int = 0
    mutation_enabled: bool = False


class AssessmentDetailResponse(BaseModel):
    """Full detail of an assessment configuration and execution summary."""

    assessment_id: str
    name: str
    target_id: str
    status: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    attack_categories: list[str] = Field(default_factory=list)
    selected_payloads: list[str] = Field(default_factory=list)
    enable_mutation: bool = False
    mutation_strategies: list[str] = Field(default_factory=list)
    total_payloads: int = 0
    completed_payloads: int = 0
    vulnerable_count: int = 0
    defended_count: int = 0
    inconclusive_count: int = 0
    error_message: str | None = None


class AssessmentStatusResponse(BaseModel):
    """Real-time progress status of an active or past assessment."""

    assessment_id: str
    status: str
    current: int = 0
    total: int = 0
    percent: float = 0.0
    last_payload_id: str | None = None
    is_running: bool = False


class ReportListItemResponse(BaseModel):
    """Summary descriptor of a saved research report."""

    report_file: str
    format: str
    size_bytes: int
    modified_at: str


class AnalyticsOverviewResponse(BaseModel):
    """Executive overview of all evaluated research runs."""

    total_assessments: int
    total_evaluations: int
    total_vulnerabilities: int
    total_defended: int
    total_inconclusive: int
    overall_vulnerability_rate: float
    top_vulnerable_categories: list[dict[str, Any]]
