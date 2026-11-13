"""FastAPI application factory for AgentBreaker local-first API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from agentbreaker.api.config import api_settings
from agentbreaker.api.exceptions import APIError, api_error_handler, generic_exception_handler
from agentbreaker.api.lifecycle import lifespan
from agentbreaker.api.middleware import RequestSizeLimitMiddleware, SecurityHeadersMiddleware
from agentbreaker.api.routers import (
    analytics_router,
    assessments_router,
    auth_router,
    findings_router,
    health_router,
    mutations_router,
    payloads_router,
    reports_router,
    settings_router,
    system_router,
    targets_router,
)


def create_app() -> FastAPI:
    """Build and configure the AgentBreaker FastAPI application."""
    application = FastAPI(
        title="AgentBreaker Security Station API",
        description=(
            "Local-first AI Security Research and Red Teaming Platform HTTP & WebSocket API."
        ),
        version="0.1.0.dev1",
        lifespan=lifespan,
        docs_url="/docs" if api_settings.docs_enabled else None,
        redoc_url="/redoc" if api_settings.docs_enabled else None,
    )

    # 1. Security Headers, Trusted Host, & Request Limit Middleware
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=api_settings.trusted_hosts,
    )
    application.add_middleware(
        RequestSizeLimitMiddleware,
        max_bytes=api_settings.max_request_size_bytes,
    )

    # 2. CORS Middleware with Explicit Allowlist
    application.add_middleware(
        CORSMiddleware,
        allow_origins=api_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. Exception Handlers
    application.add_exception_handler(APIError, api_error_handler)  # type: ignore[arg-type]
    application.add_exception_handler(Exception, generic_exception_handler)

    # 4. Mount Routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(system_router)
    application.include_router(targets_router)
    application.include_router(payloads_router)
    application.include_router(mutations_router)
    application.include_router(assessments_router)
    application.include_router(findings_router)
    application.include_router(reports_router)
    application.include_router(analytics_router)
    application.include_router(settings_router)

    return application
