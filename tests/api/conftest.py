"""Pytest fixtures for AgentBreaker API integration test suite."""

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentbreaker.api.app import create_app
from agentbreaker.api.dependencies import get_storage
from agentbreaker.api.services.assessment_service import AssessmentService
from agentbreaker.api.services.finding_service import FindingService
from agentbreaker.api.services.reporting_service import APIReportingService
from agentbreaker.api.services.target_service import TargetService
from agentbreaker.cli.storage import StorageManager


@pytest.fixture
def temp_storage(tmp_path: Path) -> StorageManager:
    """Create isolated StorageManager bound to temporary directory."""
    mgr = StorageManager(base_dir=tmp_path)
    mgr.targets_dir.mkdir(parents=True, exist_ok=True)
    mgr.assessments_dir.mkdir(parents=True, exist_ok=True)
    mgr.results_dir.mkdir(parents=True, exist_ok=True)
    mgr.reports_dir.mkdir(parents=True, exist_ok=True)
    return mgr


@pytest.fixture
def client(temp_storage: StorageManager) -> Generator[TestClient, None, None]:
    """TestClient configured with isolated storage overrides."""
    app = create_app()

    # Override dependencies
    app.dependency_overrides[get_storage] = lambda: temp_storage

    from agentbreaker.api.services.analytics_service import AnalyticsService

    # Configure services to use temporary storage
    target_svc = TargetService(storage_manager=temp_storage)
    assessment_svc = AssessmentService(storage_manager=temp_storage)
    finding_svc = FindingService(storage_manager=temp_storage)
    reporting_svc = APIReportingService(storage_manager=temp_storage)
    analytics_svc = AnalyticsService(storage_manager=temp_storage)

    from agentbreaker.api.dependencies import (
        get_analytics_service,
        get_assessment_service,
        get_finding_service,
        get_reporting_service,
        get_target_service,
    )

    app.dependency_overrides[get_target_service] = lambda: target_svc
    app.dependency_overrides[get_assessment_service] = lambda: assessment_svc
    app.dependency_overrides[get_finding_service] = lambda: finding_svc
    app.dependency_overrides[get_reporting_service] = lambda: reporting_svc
    app.dependency_overrides[get_analytics_service] = lambda: analytics_svc

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
