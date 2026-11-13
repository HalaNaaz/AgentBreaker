"""Health check and ping endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from agentbreaker.api.dependencies import get_storage
from agentbreaker.api.schemas.responses import HealthResponse
from agentbreaker.cli.storage import StorageManager

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check probe",
    description="Returns service availability, storage health, and engine status.",
)
@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="API v1 Health check probe",
)
async def check_health(storage: StorageManager = Depends(get_storage)) -> HealthResponse:
    storage_ok = storage.targets_dir.exists() and storage.assessments_dir.exists()
    return HealthResponse(
        status="ok",
        version="0.1.0.dev1",
        runtime_status="healthy",
        storage_available=storage_ok,
        engine_available=True,
        timestamp=datetime.now(UTC).isoformat(),
    )
