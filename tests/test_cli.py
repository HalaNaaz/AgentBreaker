"""Tests for the baseline CLI interface."""

from typer.testing import CliRunner

from agentbreaker import __version__
from agentbreaker.cli.main import app

runner = CliRunner()


def test_cli_version() -> None:
    """Verify version command outputs framework version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AgentBreaker" in result.stdout
    assert __version__ in result.stdout


def test_cli_help() -> None:
    """Verify help command displays usage information."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AgentBreaker" in result.stdout
    assert "LLM & AI Agent Security Testing Framework" in result.stdout
