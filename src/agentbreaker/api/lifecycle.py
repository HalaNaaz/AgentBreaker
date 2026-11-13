"""FastAPI application lifecycle management and graceful shutdown hooks."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agentbreaker.api.services.assessment_service import assessment_service
from agentbreaker.api.websocket.manager import ws_manager
from agentbreaker.cli.storage import storage


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup preparation and safe graceful shutdown."""
    # 1. Startup: Verify local storage directories
    storage.targets_dir.mkdir(parents=True, exist_ok=True)
    storage.assessments_dir.mkdir(parents=True, exist_ok=True)
    storage.results_dir.mkdir(parents=True, exist_ok=True)
    storage.reports_dir.mkdir(parents=True, exist_ok=True)

    yield

    # 2. Shutdown: Cancel active assessment tasks and close WebSocket connections
    await assessment_service.cleanup_all()
    await ws_manager.close_all()
