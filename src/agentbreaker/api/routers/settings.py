"""Application settings and operational configuration endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from agentbreaker.api.config import api_settings
from agentbreaker.api.dependencies import get_storage, verify_local_auth
from agentbreaker.cli.storage import StorageManager

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["Settings"],
    dependencies=[Depends(verify_local_auth)],
)


class SettingsResponse(BaseModel):
    """Sanitized application and API server configuration."""

    api_host: str
    api_port: int
    cors_origins: list[str]
    max_request_size_bytes: int
    storage_root: str
    auth_enabled: bool
    environment: str = "local"


@router.get("", response_model=SettingsResponse)
async def get_settings(
    storage: StorageManager = Depends(get_storage),
) -> SettingsResponse:
    """Retrieve active server and storage settings with all credentials masked."""
    return SettingsResponse(
        api_host=api_settings.host,
        api_port=api_settings.port,
        cors_origins=api_settings.cors_origins,
        max_request_size_bytes=api_settings.max_request_size_bytes,
        storage_root=str(storage.root),
        auth_enabled=bool(api_settings.local_api_key),
    )
