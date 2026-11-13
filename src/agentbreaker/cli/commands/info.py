"""System information and environment diagnostics command."""

import platform
import sys

from rich.panel import Panel

from agentbreaker import __version__
from agentbreaker.cli.output import console, print_header
from agentbreaker.cli.storage import storage
from agentbreaker.mutators.registry import MutatorRegistry
from agentbreaker.schemas.enums import AttackCategory, TargetType


def info_command() -> None:
    """Display detailed AgentBreaker platform and research workstation diagnostics."""
    print_header(
        "AgentBreaker — AI Red Teaming & Security Research Platform",
        "AshlynxCyber Security Systems — Offensive AI Research",
    )

    categories = [c.value for c in AttackCategory]
    providers = [p.value for p in TargetType]
    registry = MutatorRegistry.get_default_registry()
    strategies = registry.list_strategies(include_disabled=True)

    info_text = (
        f"[bold white]Framework Version:[/bold white] {__version__}\n"
        f"[bold white]Python Runtime:[/bold white] {platform.python_version()} "
        f"({platform.system()} {platform.machine()})\n"
        f"[bold white]Executable:[/bold white] {sys.executable}\n"
        f"[bold white]Storage Directory:[/bold white] {storage.root}\n\n"
        f"[bold cyan]Supported Target Providers ({len(providers)}):[/bold cyan]\n"
        f"  {', '.join(providers)}\n\n"
        f"[bold cyan]Attack Categories ({len(categories)}):[/bold cyan]\n"
        f"  {', '.join(categories)}\n\n"
        f"[bold cyan]Active Mutation Strategies ({len(strategies)}):[/bold cyan]\n"
        f"  {', '.join(strategies)}\n\n"
        "[dim]Local-first security research workstation. "
        "Explicit target authorization enforced for all operations.[/dim]"
    )

    console.print(Panel(info_text, border_style="cyan", padding=(1, 2)))
