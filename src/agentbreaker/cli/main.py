"""AgentBreaker command line interface entrypoint and root command registration."""

from typing import Annotated

import typer

from agentbreaker import __version__
from agentbreaker.cli.commands.assessment import assessment_app
from agentbreaker.cli.commands.config import config_app
from agentbreaker.cli.commands.findings import findings_app
from agentbreaker.cli.commands.info import info_command
from agentbreaker.cli.commands.mutations import mutations_app
from agentbreaker.cli.commands.payloads import payloads_app
from agentbreaker.cli.commands.report import report_app
from agentbreaker.cli.commands.results import results_app
from agentbreaker.cli.commands.target import target_app
from agentbreaker.cli.output import console

app = typer.Typer(
    name="agentbreaker",
    help=(
        "AgentBreaker — LLM & AI Agent Security Testing Framework.\n\n"
        "AshlynxCyber Security Systems — Offensive AI Research.\n\n"
        "Usage Examples:\n"
        "  agentbreaker info\n"
        "  agentbreaker target list\n"
        "  agentbreaker payloads list --category direct_jailbreak\n"
        "  agentbreaker mutations preview JB-DAN-001 --strategy rot13\n"
        "  agentbreaker assessment create --name 'Audit #1' --target local_vllm\n"
        "  agentbreaker assessment run ASM-12345678\n"
        "  agentbreaker findings list\n"
        "  agentbreaker results export ASM-12345678 --format markdown"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is passed."""
    if value:
        console.print(f"AgentBreaker v{__version__}")
        console.print("AshlynxCyber Security Systems — Offensive AI Research")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Display AgentBreaker version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """AgentBreaker: LLM & AI Agent Security Testing Framework."""


@app.command("version")
def version_cmd() -> None:
    """Display AgentBreaker version and framework info."""
    console.print(f"AgentBreaker v{__version__}")
    console.print("AshlynxCyber Security Systems — Offensive AI Research")


@app.command("info")
def info_cmd() -> None:
    """Display platform diagnostics, supported targets, and attack capabilities."""
    info_command()


@app.command("api")
def api_cmd(
    host: Annotated[str, typer.Option("--host", "-h", help="API host address.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="API port number.")] = 8000,
    reload: Annotated[bool, typer.Option("--reload", "-r", help="Enable hot reload.")] = False,
) -> None:
    """Launch the local FastAPI backend server."""
    import uvicorn

    console.print(
        f"[bold green]Starting AgentBreaker API Station on http://{host}:{port}[/bold green]"
    )
    uvicorn.run("agentbreaker.api.main:app", host=host, port=port, reload=reload)


# Register Command Groups
app.add_typer(target_app, name="target")
app.add_typer(payloads_app, name="payloads")
app.add_typer(mutations_app, name="mutations")
app.add_typer(assessment_app, name="assessment")
app.add_typer(findings_app, name="findings")
app.add_typer(results_app, name="results")
app.add_typer(report_app, name="report")
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
