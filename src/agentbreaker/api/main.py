"""ASGI entry point for running the AgentBreaker FastAPI application."""

import uvicorn

from agentbreaker.api.app import create_app
from agentbreaker.api.config import api_settings

app = create_app()


def run_server() -> None:
    """Run local uvicorn development server."""
    uvicorn.run(
        "agentbreaker.api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run_server()
