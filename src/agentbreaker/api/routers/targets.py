"""Target configuration and connectivity endpoints."""

from fastapi import APIRouter, Depends, status

from agentbreaker.api.dependencies import get_target_service, verify_local_auth
from agentbreaker.api.schemas.common import StatusMessageResponse
from agentbreaker.api.schemas.requests import TargetCreateRequest, TargetUpdateRequest
from agentbreaker.api.schemas.responses import (
    TargetResponseModel,
    TargetTestResponse,
    TargetValidationResponse,
)
from agentbreaker.api.services.target_service import TargetService

router = APIRouter(
    prefix="/api/v1/targets",
    tags=["Targets"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("", response_model=list[TargetResponseModel])
async def list_targets(
    service: TargetService = Depends(get_target_service),
) -> list[TargetResponseModel]:
    """List all configured targets with credentials strictly masked."""
    return service.list_targets()


@router.post("", response_model=TargetResponseModel, status_code=status.HTTP_201_CREATED)
async def create_target(
    req: TargetCreateRequest,
    service: TargetService = Depends(get_target_service),
) -> TargetResponseModel:
    """Register and validate a new authorized target configuration."""
    return service.create_target(req)


@router.get("/{target_id}", response_model=TargetResponseModel)
async def get_target(
    target_id: str,
    service: TargetService = Depends(get_target_service),
) -> TargetResponseModel:
    """Retrieve target configuration by identifier."""
    return service.get_target(target_id)


@router.patch("/{target_id}", response_model=TargetResponseModel)
async def update_target(
    target_id: str,
    req: TargetUpdateRequest,
    service: TargetService = Depends(get_target_service),
) -> TargetResponseModel:
    """Update settings for an existing target configuration."""
    return service.update_target(target_id, req)


@router.delete("/{target_id}", response_model=StatusMessageResponse)
async def delete_target(
    target_id: str,
    service: TargetService = Depends(get_target_service),
) -> StatusMessageResponse:
    """Delete target configuration from local storage."""
    service.delete_target(target_id)
    return StatusMessageResponse(message=f"Target '{target_id}' successfully removed.")


@router.post("/{target_id}/validate", response_model=TargetValidationResponse)
async def validate_target(
    target_id: str,
    service: TargetService = Depends(get_target_service),
) -> TargetValidationResponse:
    """Perform security and configuration parameter verification on a target."""
    return service.validate_target(target_id)


@router.post("/{target_id}/test", response_model=TargetTestResponse)
async def test_target_connection(
    target_id: str,
    service: TargetService = Depends(get_target_service),
) -> TargetTestResponse:
    """Execute live connectivity probe against target endpoint."""
    return await service.test_target_connection(target_id)
