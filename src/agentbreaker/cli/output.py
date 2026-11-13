"""Terminal output formatting and Rich presentation utilities for AgentBreaker CLI."""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(width=200)
error_console = Console(stderr=True, width=200)


def mask_secret(secret_val: str | None) -> str:
    """Mask a secret value for safe terminal presentation."""
    if not secret_val:
        return "[dim]<none>[/dim]"
    if len(secret_val) <= 6:
        return "******"
    return f"{secret_val[:3]}...{secret_val[-3:]}"


def format_verdict(verdict: str) -> str:
    """Colorize evaluation verdicts according to brand and security standards."""
    v_upper = verdict.upper()
    if v_upper == "VULNERABLE":
        return "[bold red]VULNERABLE[/bold red]"
    if v_upper == "DEFENDED":
        return "[bold green]DEFENDED[/bold green]"
    if v_upper == "INCONCLUSIVE":
        return "[bold yellow]INCONCLUSIVE[/bold yellow]"
    return verdict


def format_severity(severity: str) -> str:
    """Colorize vulnerability severity levels."""
    s_upper = severity.upper()
    if s_upper == "CRITICAL":
        return "[bold red]CRITICAL[/bold red]"
    if s_upper == "HIGH":
        return "[bold orange3]HIGH[/bold orange3]"
    if s_upper == "MEDIUM":
        return "[bold yellow]MEDIUM[/bold yellow]"
    if s_upper == "LOW":
        return "[bold blue]LOW[/bold blue]"
    return "[dim]INFO[/dim]"


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a styled section header banner."""
    content = f"[bold white]{title}[/bold white]"
    if subtitle:
        content += f"\n[dim cyan]{subtitle}[/dim cyan]"
    console.print(
        Panel(
            content,
            border_style="bright_blue",
            expand=False,
            padding=(0, 2),
        )
    )


def create_table(
    title: str,
    columns: list[tuple[str, str]],  # (name, justify)
) -> Table:
    """Create a standardized Rich Table with technical styling."""
    table = Table(
        title=f"[bold cyan]{title}[/bold cyan]",
        title_justify="left",
        border_style="bright_black",
        header_style="bold bright_white",
        expand=False,
    )
    for name, justify in columns:
        table.add_column(name, justify=justify)  # type: ignore[arg-type]
    return table


def print_error(message: str, details: Any | None = None) -> None:
    """Print an error message to stderr."""
    error_console.print(f"[bold red]ERROR:[/bold red] {message}")
    if details:
        error_console.print(f"[dim]{details}[/dim]")


def print_success(message: str) -> None:
    """Print a success confirmation message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]![/bold yellow] {message}")
