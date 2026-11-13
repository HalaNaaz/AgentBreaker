"""AgentBreaker Local-First FastAPI Backend Package."""

from agentbreaker.api.app import create_app
from agentbreaker.api.main import app

__all__ = ["app", "create_app"]
