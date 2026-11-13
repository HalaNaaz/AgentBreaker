"""Target endpoint management and connectivity validation commands."""

import asyncio
import os
from typing import Annotated

import typer
from pydantic import SecretStr, ValidationError
from rich.panel import Panel

from agentbreaker.cli.output import (
    console,
    create_table,
    mask_secret,
    print_error,
    print_header,
    print_success,
    print_warning,
)
from agentbreaker.cli.storage import storage
from agentbreaker.connectors.factory import get_connector
from agentbreaker.schemas.enums import TargetType
from agentbreaker.schemas.target import TargetConfig

target_app = typer.Typer(
    name="target",
    help="Manage and validate target model and agent endpoints.",
    no_args_is_help=True,
)


@target_app.command("list")
def list_targets() -> None:
    """List all configured target endpoints."""
    targets = storage.list_targets()
    if not targets:
        print_warning("No targets configured. Add one with 'agentbreaker target add'.")
        return

    table = create_table(
        "Configured Target Endpoints",
        [
            ("Target ID", "left"),
            ("Provider Type", "left"),
            ("Model Name", "left"),
            ("Endpoint URL", "left"),
            ("Concurrency", "right"),
            ("Timeout (s)", "right"),
        ],
    )

    for target_id, cfg in targets.items():
        table.add_row(
            f"[bold cyan]{target_id}[/bold cyan]",
            cfg.target_type.value,
            cfg.model_name,
            cfg.endpoint_url,
            str(cfg.max_concurrency),
            f"{cfg.timeout_seconds:.1f}",
        )

    console.print(table)


@target_app.command("show")
def show_target(
    target_id: Annotated[str, typer.Argument(help="Identifier of target to inspect.")],
) -> None:
    """Show detailed configuration for a target (secrets are masked)."""
    cfg = storage.get_target(target_id)
    if not cfg:
        print_error(f"Target '{target_id}' not found.")
        raise typer.Exit(code=1)

    api_key_str = cfg.api_key.get_secret_value() if cfg.api_key else None
    masked_key = mask_secret(api_key_str)

    details = (
        f"[bold white]Target ID:[/bold white] {target_id}\n"
        f"[bold white]Endpoint URL:[/bold white] {cfg.endpoint_url}\n"
        f"[bold white]Provider Type:[/bold white] {cfg.target_type.value}\n"
        f"[bold white]Model Identifier:[/bold white] {cfg.model_name}\n"
        f"[bold white]API Key:[/bold white] {masked_key}\n"
        f"[bold white]Auth Header:[/bold white] {cfg.auth_header_name} "
        f"({cfg.auth_scheme})\n"
        f"[bold white]Timeout Limit:[/bold white] {cfg.timeout_seconds:.1f}s\n"
        f"[bold white]Max Concurrency:[/bold white] {cfg.max_concurrency}\n"
        f"[bold white]Custom Headers:[/bold white] {len(cfg.custom_headers)} headers configured\n"
    )

    console.print(Panel(details, title=f"Target: {target_id}", border_style="cyan"))


@target_app.command("add")
def add_target(
    target_id: Annotated[str, typer.Option("--id", help="Unique target identifier.")],
    endpoint_url: Annotated[
        str, typer.Option("--url", help="Endpoint URL (e.g. http://localhost:8000/v1)")
    ],
    model_name: Annotated[str, typer.Option("--model", help="Target model identifier.")],
    provider: Annotated[
        TargetType, typer.Option("--provider", help="Adapter provider type.")
    ] = TargetType.OPENAI_COMPATIBLE,
    api_key: Annotated[
        str | None, typer.Option("--api-key", help="Target API key (optional).", prompt=False)
    ] = None,
    api_key_env: Annotated[
        str | None,
        typer.Option(
            "--api-key-env",
            help="Name of environment variable holding API key (prevents CLI history exposure).",
        ),
    ] = None,
    timeout: Annotated[
        float, typer.Option("--timeout", help="HTTP request timeout in seconds.")
    ] = 30.0,
    concurrency: Annotated[
        int, typer.Option("--concurrency", help="Maximum in-flight requests.")
    ] = 5,
) -> None:
    """Add a new target endpoint configuration."""
    if storage.get_target(target_id):
        print_error(f"Target '{target_id}' already exists. Use another ID or remove it first.")
        raise typer.Exit(code=1)

    effective_api_key = api_key
    if api_key_env:
        env_val = os.getenv(api_key_env)
        if not env_val:
            print_error(f"Environment variable '{api_key_env}' is not set or is empty.")
            raise typer.Exit(code=1)
        effective_api_key = env_val

    try:
        secret_obj = SecretStr(effective_api_key) if effective_api_key else None
        cfg = TargetConfig(
            endpoint_url=endpoint_url,
            target_type=provider,
            model_name=model_name,
            api_key=secret_obj,
            timeout_seconds=timeout,
            max_concurrency=concurrency,
        )
    except ValidationError as err:
        print_error(f"Target configuration validation failed:\n{err}")
        raise typer.Exit(code=1) from err

    try:
        storage.save_target(target_id, cfg)
    except ValueError as err:
        print_error(f"Invalid target identifier: {err}")
        raise typer.Exit(code=1) from err

    print_success(f"Target '{target_id}' successfully saved. (Not tested yet; use 'target test')")


@target_app.command("validate")
def validate_target(
    target_id: Annotated[str, typer.Argument(help="Identifier of target to validate.")],
) -> None:
    """Validate target configuration against schema and boundary constraints."""
    cfg = storage.get_target(target_id)
    if not cfg:
        print_error(f"Target '{target_id}' not found.")
        raise typer.Exit(code=1)

    try:
        # Re-validate model
        TargetConfig.model_validate(cfg.model_dump())
        print_success(
            f"Target '{target_id}' configuration is valid and adheres to security constraints."
        )
    except ValidationError as err:
        print_error(f"Target '{target_id}' configuration is invalid:\n{err}")
        raise typer.Exit(code=1) from err


@target_app.command("test")
def test_target(
    target_id: Annotated[str, typer.Argument(help="Identifier of target to test connectivity.")],
) -> None:
    """Test network connectivity and authorization against target endpoint."""
    cfg = storage.get_target(target_id)
    if not cfg:
        print_error(f"Target '{target_id}' not found.")
        raise typer.Exit(code=1)

    print_header(f"Testing Connectivity: {target_id}", f"Endpoint: {cfg.endpoint_url}")

    async def _test() -> None:
        connector = get_connector(cfg)
        try:
            # Send harmless probe prompt
            resp = await connector.send_prompt("ping", max_tokens=5, temperature=0.0)
            if resp.is_error or resp.status_code >= 400:
                print_error(f"Target responded with HTTP {resp.status_code}: {resp.error_message}")
            else:
                print_success(
                    f"Successfully connected! Model: {cfg.model_name} "
                    f"(Latency: {resp.latency_ms:.1f}ms)"
                )
        except Exception as err:
            print_error(f"Connection test failed: {err}")
        finally:
            await connector.aclose()

    asyncio.run(_test())


@target_app.command("remove")
def remove_target(
    target_id: Annotated[str, typer.Argument(help="Identifier of target to remove.")],
    confirm: Annotated[
        bool, typer.Option("--confirm", "-y", help="Skip confirmation prompt.")
    ] = False,
) -> None:
    """Remove a configured target endpoint."""
    if not storage.get_target(target_id):
        print_error(f"Target '{target_id}' not found.")
        raise typer.Exit(code=1)

    if not confirm:
        sure = typer.confirm(f"Are you sure you want to remove target '{target_id}'?")
        if not sure:
            print_warning("Removal aborted.")
            return

    if storage.delete_target(target_id):
        print_success(f"Target '{target_id}' removed.")
    else:
        print_error(f"Failed to remove target '{target_id}'.")
