"""Platform configuration inspection and validation commands."""

from rich.panel import Panel

from agentbreaker.cli.output import (
    console,
    create_table,
    mask_secret,
    print_error,
    print_header,
    print_success,
)
from agentbreaker.cli.storage import storage
from agentbreaker.core.config import AgentBreakerSettings

config_app = typer_app = __import__("typer").Typer(
    name="config",
    help="Inspect, validate, and manage global AgentBreaker platform settings.",
    no_args_is_help=True,
)


@config_app.command("show")
def show_config() -> None:
    """Display current platform configuration with masked secrets."""
    print_header("Global Platform Configuration", "Source: Environment & .env")

    current_settings = AgentBreakerSettings()
    api_key_str = current_settings.api_key.get_secret_value() if current_settings.api_key else None
    masked_key = mask_secret(api_key_str)

    table = create_table(
        "AgentBreaker Global Settings",
        [
            ("Setting Key", "left"),
            ("Configured Value", "left"),
        ],
    )

    table.add_row("target_url", current_settings.target_url)
    table.add_row("target_type", current_settings.target_type)
    table.add_row("target_model", current_settings.target_model)
    table.add_row("api_key", masked_key)
    table.add_row("auth_header_name", current_settings.auth_header_name)
    table.add_row("request_timeout_seconds", f"{current_settings.request_timeout_seconds:.1f}s")
    table.add_row("max_concurrency", str(current_settings.max_concurrency))
    table.add_row("rate_limit_rps", f"{current_settings.rate_limit_rps:.1f}")
    table.add_row("max_retries", str(current_settings.max_retries))
    table.add_row("retry_backoff_seconds", f"{current_settings.retry_backoff_seconds:.1f}s")
    table.add_row("output_dir", current_settings.output_dir)
    table.add_row("log_level", current_settings.log_level)

    console.print(table)


@config_app.command("validate")
def validate_config() -> None:
    """Validate active platform configuration against schema constraints."""
    try:
        current_settings = AgentBreakerSettings()
        current_settings.model_validate(current_settings.model_dump())
        print_success("Platform configuration is valid and adheres to all security constraints.")
    except Exception as err:
        print_error(f"Configuration validation failed: {err}")
        raise __import__("typer").Exit(code=1) from err


@config_app.command("path")
def show_paths() -> None:
    """Display active local storage and configuration directory paths."""
    current_settings = AgentBreakerSettings()
    details = (
        f"[bold white]Storage Root:[/bold white] {storage.root}\n"
        f"[bold white]Targets Directory:[/bold white] {storage.targets_dir}\n"
        f"[bold white]Assessments Directory:[/bold white] {storage.assessments_dir}\n"
        f"[bold white]Results Directory:[/bold white] {storage.results_dir}\n"
        f"[bold white]Reports Directory:[/bold white] {current_settings.output_dir}"
    )

    console.print(Panel(details, title="AgentBreaker Storage & Config Paths", border_style="cyan"))
