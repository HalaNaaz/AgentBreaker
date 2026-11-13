"""Adversarial mutation strategies and non-dispatched preview endpoints."""

from fastapi import APIRouter, Depends

from agentbreaker.api.dependencies import get_mutation_service, verify_local_auth
from agentbreaker.api.schemas.requests import MutationPreviewRequest
from agentbreaker.api.schemas.responses import MutationPreviewResponse, MutationStrategyResponse
from agentbreaker.api.services.mutation_service import MutationService

router = APIRouter(
    prefix="/api/v1/mutations",
    tags=["Mutations"],
    dependencies=[Depends(verify_local_auth)],
)


@router.get("/strategies", response_model=list[MutationStrategyResponse])
async def list_strategies(
    service: MutationService = Depends(get_mutation_service),
) -> list[MutationStrategyResponse]:
    """List available prompt mutation strategies."""
    return service.list_strategies()


@router.post("/preview", response_model=MutationPreviewResponse)
async def preview_mutation(
    req: MutationPreviewRequest,
    service: MutationService = Depends(get_mutation_service),
) -> MutationPreviewResponse:
    """Generate preview variants of a payload without dispatching to any target."""
    return service.preview_mutation(
        payload_id=req.payload_id,
        strategies=req.strategies,
        max_variants=req.max_variants,
    )
