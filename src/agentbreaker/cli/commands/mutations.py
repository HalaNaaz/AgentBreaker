"""Adversarial payload mutation preview and strategy inspection commands."""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from agentbreaker.attacks.loader import PayloadLoader, get_default_payloads_dir
from agentbreaker.cli.output import (
    console,
    create_table,
    print_error,
    print_header,
    print_warning,
)
from agentbreaker.mutators.engine import MutationEngine
from agentbreaker.mutators.registry import MutatorRegistry

mutations_app = typer.Typer(
    name="mutations",
    help="Explore mutation strategies and preview adversarial payload variants.",
    no_args_is_help=True,
)


@mutations_app.command("list")
def list_mutators() -> None:
    """List registered mutation mutator instances and descriptions."""
    registry = MutatorRegistry.get_default_registry()
    table = create_table(
        "Registered Mutation Strategies",
        [
            ("Strategy Name", "left"),
            ("Enabled", "center"),
            ("Description", "left"),
        ],
    )

    for strat_name in registry.list_strategies(include_disabled=True):
        m = registry.get(strat_name)
        table.add_row(
            f"[bold cyan]{m.name}[/bold cyan]",
            "[bold green]YES[/bold green]" if m.is_enabled else "[dim red]NO[/dim red]",
            m.description,
        )

    console.print(table)


@mutations_app.command("strategies")
def list_strategies() -> None:
    """Alias for 'mutations list' displaying strategy descriptions."""
    list_mutators()


@mutations_app.command("preview")
def preview_mutation(
    payload_id: Annotated[str, typer.Argument(help="Identifier of payload to mutate.")],
    strategy: Annotated[
        str,
        typer.Option(
            "--strategy",
            "-s",
            help=(
                "Strategy (base64, rot13, leetspeak, markdown_obfuscation, "
                "ascii_smuggling, multilingual)."
            ),
        ),
    ] = "rot13",
    max_variants: Annotated[
        int, typer.Option("--max-variants", "-m", help="Max variants to generate.")
    ] = 1,
    seed: Annotated[int | None, typer.Option("--seed", help="Deterministic random seed.")] = 42,
    path: Annotated[
        Path | None, typer.Option("--path", "-p", help="Payload directory path.")
    ] = None,
) -> None:
    """Preview mutated adversarial variants without dispatching them to any target."""
    target_path = path or get_default_payloads_dir()
    if not target_path.is_dir():
        print_error(f"Payload directory '{target_path}' not found.")
        raise typer.Exit(code=1)

    payloads = PayloadLoader.load_from_directory(target_path)
    base_payload = next((p for p in payloads if p.id == payload_id), None)

    if not base_payload:
        print_error(f"Payload '{payload_id}' not found.")
        raise typer.Exit(code=1)

    print_header(
        f"Adversarial Mutation Preview: {payload_id}",
        f"Strategy: {strategy} (Preview only — not dispatched)",
    )

    engine = MutationEngine()
    try:
        variants = engine.mutate_payload(
            base_payload,
            strategies=[strategy],
            max_variants=max_variants,
            seed=seed,
        )
    except Exception as err:
        print_error(f"Mutation generation failed: {err}")
        raise typer.Exit(code=1) from err

    if not variants:
        print_warning("No variants were produced.")
        return

    # Display original
    console.print(
        Panel(
            base_payload.payload_template,
            title="Original Baseline Prompt Template",
            border_style="dim white",
        )
    )

    for idx, v in enumerate(variants, 1):
        info_meta = (
            f"[bold cyan]Variant ID:[/bold cyan] {v.id}\n"
            f"[bold cyan]Parent ID:[/bold cyan] {v.parent_id}\n"
            f"[bold cyan]Strategy:[/bold cyan] {v.mutation_strategy}\n"
            f"[bold cyan]Metadata:[/bold cyan] {v.mutation_metadata}\n\n"
            f"[bold white]Mutated Output Preview:[/bold white]\n"
            f"{v.payload_template}"
        )
        console.print(
            Panel(
                info_meta,
                title=f"Variant #{idx} ({v.id}) [RESEARCH DATA ONLY]",
                border_style="bright_blue",
            )
        )
