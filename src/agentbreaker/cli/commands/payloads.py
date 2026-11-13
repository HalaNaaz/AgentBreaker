"""Payload library inspection and validation commands."""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from agentbreaker.attacks.loader import PayloadLoader
from agentbreaker.cli.output import (
    console,
    create_table,
    format_severity,
    print_error,
    print_header,
    print_success,
    print_warning,
)
from agentbreaker.schemas.enums import AttackCategory, Severity
from agentbreaker.schemas.payload import AttackPayload

payloads_app = typer.Typer(
    name="payloads",
    help="Inspect, filter, and validate adversarial attack payloads.",
    no_args_is_help=True,
)


def _get_payloads(payloads_dir: Path) -> list[AttackPayload]:
    """Helper to load all payloads safely from directory."""
    if not payloads_dir.exists():
        return []
    return PayloadLoader.load_from_directory(payloads_dir)


@payloads_app.command("list")
def list_payloads(
    category: Annotated[
        AttackCategory | None, typer.Option("--category", "-c", help="Filter by attack category.")
    ] = None,
    severity: Annotated[
        Severity | None, typer.Option("--severity", "-s", help="Filter by severity level.")
    ] = None,
    path: Annotated[Path, typer.Option("--path", "-p", help="Payload directory path.")] = Path(
        "payloads"
    ),
) -> None:
    """List attack payloads with optional category and severity filtering."""
    if not path.exists():
        print_error(f"Payload directory '{path}' not found.")
        raise typer.Exit(code=1)

    payloads = _get_payloads(path)

    if category:
        payloads = [p for p in payloads if p.category == category]
    if severity:
        payloads = [p for p in payloads if p.severity == severity]

    if not payloads:
        print_warning("No payloads matched the specified criteria.")
        return

    table = create_table(
        f"Attack Payload Library ({len(payloads)} vectors)",
        [
            ("Payload ID", "left"),
            ("Name", "left"),
            ("Category", "left"),
            ("Severity", "center"),
            ("CVSS", "right"),
            ("OWASP", "left"),
        ],
    )

    for p in payloads:
        table.add_row(
            f"[bold cyan]{p.id}[/bold cyan]",
            p.name,
            p.category.value,
            format_severity(p.severity.value),
            f"{p.cvss_score:.1f}",
            p.owasp_id or "[dim]N/A[/dim]",
        )

    console.print(table)


@payloads_app.command("show")
def show_payload(
    payload_id: Annotated[str, typer.Argument(help="Identifier of payload to inspect.")],
    path: Annotated[Path, typer.Option("--path", "-p", help="Payload directory path.")] = Path(
        "payloads"
    ),
) -> None:
    """Inspect full details, template, and evaluation rules for a payload."""
    payloads = _get_payloads(path)
    target = next((p for p in payloads if p.id == payload_id), None)

    if not target:
        print_error(f"Payload '{payload_id}' not found in '{path}'.")
        raise typer.Exit(code=1)

    rules = target.evaluator_rules
    rules_desc = (
        f"  Canary Check: {rules.canary_check}\n"
        f"  Regex Matches: {len(rules.regex_matches)} rules\n"
        f"  Refusal Phrases: {len(rules.refusal_phrases)} phrases\n"
        f"  Forbidden Tools: {rules.forbidden_tools or 'None'}"
    )

    details = (
        f"[bold white]ID:[/bold white] {target.id}\n"
        f"[bold white]Name:[/bold white] {target.name}\n"
        f"[bold white]Category:[/bold white] {target.category.value}\n"
        f"[bold white]Severity:[/bold white] {format_severity(target.severity.value)} "
        f"(CVSS {target.cvss_score:.1f})\n"
        f"[bold white]OWASP ID:[/bold white] {target.owasp_id or 'None'}\n"
        f"[bold white]MITRE ATLAS:[/bold white] {target.mitre_atlas_id or 'None'}\n"
        f"[bold white]Destructive:[/bold white] {target.is_destructive}\n"
        f"[bold white]Description:[/bold white] {target.description}\n\n"
        f"[bold cyan]Evaluator Rules:[/bold cyan]\n{rules_desc}\n\n"
        f"[bold cyan]Payload Template:[/bold cyan]\n"
        f"[dim]{target.payload_template}[/dim]"
    )

    console.print(Panel(details, title=f"Payload: {target.id}", border_style="cyan"))


@payloads_app.command("categories")
def list_categories() -> None:
    """List available attack categories and descriptions."""
    table = create_table(
        "Supported Attack Categories",
        [
            ("Category Enum", "left"),
            ("Description", "left"),
        ],
    )

    descriptions = {
        AttackCategory.DIRECT_JAILBREAK: (
            "Direct adversarial prompt engineering to bypass safety filters."
        ),
        AttackCategory.SYSTEM_EXTRACTION: (
            "Probing to elicit system prompt, hidden instructions, or canary tokens."
        ),
        AttackCategory.INDIRECT_INJECTION: (
            "Injecting instructions via untrusted third-party inputs or documents."
        ),
        AttackCategory.TOOL_HIJACKING: (
            "Manipulating agent tools to execute unauthorized passive actions."
        ),
    }

    for cat in AttackCategory:
        table.add_row(
            f"[bold cyan]{cat.value}[/bold cyan]",
            descriptions.get(cat, "Adversarial evaluation vector category."),
        )

    console.print(table)


@payloads_app.command("validate")
def validate_payloads(
    path: Annotated[
        Path, typer.Option("--path", "-p", help="Payload directory path to validate.")
    ] = Path("payloads"),
) -> None:
    """Validate all payload files in directory against schema and safety bounds."""
    print_header("Validating Payload Repository", f"Path: {path}")

    if not path.is_dir():
        print_error(f"Directory '{path}' does not exist.")
        raise typer.Exit(code=1)

    try:
        payloads = PayloadLoader.load_from_directory(path)
        print_success(f"All {len(payloads)} payloads loaded and validated successfully.")
    except Exception as err:
        print_error(f"Payload validation failed: {err}")
        raise typer.Exit(code=1) from err
