"""System diagnostic and capability endpoints."""

import platform
import sys
from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from agentbreaker import __version__
from agentbreaker.api.dependencies import get_assessment_service, get_storage, verify_local_auth
from agentbreaker.api.schemas.responses import (
    SystemCapabilitiesResponse,
    SystemInfoResponse,
    SystemStatusResponse,
)
from agentbreaker.api.services.assessment_service import AssessmentService
from agentbreaker.cli.storage import StorageManager
from agentbreaker.mutators.engine import MutationEngine
from agentbreaker.reporting.models import ReportFormat
from agentbreaker.schemas.enums import AttackCategory, TargetType

router = APIRouter(
    prefix="/api/v1/system",
    tags=["System"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info() -> SystemInfoResponse:
    """Return diagnostic framework metadata with zero secret disclosure."""
    mutation_engine = MutationEngine()
    return SystemInfoResponse(
        name="AgentBreaker",
        organization="AshlynxCyber",
        version=__version__,
        python_runtime=f"{platform.python_implementation()} {sys.version.split()[0]}",
        os_platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        registered_connectors=[t.value for t in TargetType],
        attack_categories=[c.value for c in AttackCategory],
        mutation_strategies=mutation_engine.registry.list_strategies(),
        report_formats=[f.value for f in ReportFormat],
    )


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    storage: StorageManager = Depends(get_storage),
    assessments: AssessmentService = Depends(get_assessment_service),
) -> SystemStatusResponse:
    """Return live operational telemetry of storage and background execution tasks."""
    running_ids = list(assessments._active_tasks.keys())
    return SystemStatusResponse(
        status="ONLINE",
        storage_ready=storage.targets_dir.exists(),
        active_assessments_count=len(running_ids),
        running_task_ids=running_ids,
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.get("/capabilities", response_model=SystemCapabilitiesResponse)
async def get_system_capabilities() -> SystemCapabilitiesResponse:
    """Return functional module capabilities inventory."""
    mutation_engine = MutationEngine()
    return SystemCapabilitiesResponse(
        attack_engine=True,
        mutation_engine=True,
        evaluation_oracle=True,
        reporting_engine=True,
        websockets_live_events=True,
        supported_connectors=[t.value for t in TargetType],
        supported_strategies=mutation_engine.registry.list_strategies(),
        supported_frameworks=["OWASP Top 10 for LLMs 2025", "MITRE ATLAS"],
    )
