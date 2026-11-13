"""Routers package for AgentBreaker API."""

from agentbreaker.api.routers.analytics import router as analytics_router
from agentbreaker.api.routers.assessments import router as assessments_router
from agentbreaker.api.routers.auth import router as auth_router
from agentbreaker.api.routers.findings import router as findings_router
from agentbreaker.api.routers.health import router as health_router
from agentbreaker.api.routers.mutations import router as mutations_router
from agentbreaker.api.routers.payloads import router as payloads_router
from agentbreaker.api.routers.reports import router as reports_router
from agentbreaker.api.routers.settings import router as settings_router
from agentbreaker.api.routers.system import router as system_router
from agentbreaker.api.routers.targets import router as targets_router

__all__ = [
    "analytics_router",
    "assessments_router",
    "auth_router",
    "findings_router",
    "health_router",
    "mutations_router",
    "payloads_router",
    "reports_router",
    "settings_router",
    "system_router",
    "targets_router",
]
