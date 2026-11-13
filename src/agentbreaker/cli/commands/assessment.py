"""Assessment configuration, scheduling, and execution workflow commands."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from agentbreaker.cli.orchestration import run_assessment_sync
from agentbreaker.cli.output import (
    console,
    create_table,
    print_error,
    print_header,
    print_success,
    print_warning,
)
from agentbreaker.cli.storage import storage
from agentbreaker.schemas.enums import AttackCategory, Verdict

assessment_app = typer.Typer(
    name="assessment",
    help="Create, manage, and dispatch AI security red teaming assessments.",
    no_args_is_help=True,
)


@assessment_app.command("create")
def create_assessment(
    name: Annotated[str, typer.Option("--name", "-n", help="Human-readable assessment name.")],
    target_id: Annotated[str, typer.Option("--target", "-t", help="Target endpoint identifier.")],
    categories: Annotated[
        list[str] | None, typer.Option("--category", "-c", help="Attack categories to evaluate.")
    ] = None,
    payload_ids: Annotated[
        list[str] | None, typer.Option("--payload", "-p", help="Specific payload IDs to evaluate.")
    ] = None,
    enable_mutation: Annotated[
        bool, typer.Option("--enable-mutation", help="Enable adversarial payload mutation.")
    ] = False,
    mutation_strategies: Annotated[
        list[str] | None,
        typer.Option(
            "--strategy",
            help="Mutation strategies (rot13, base64, leetspeak, markdown_obfuscation).",
        ),
    ] = None,
    max_variants: Annotated[
        int, typer.Option("--max-variants", help="Max mutated variants per payload.")
    ] = 2,
    concurrency: Annotated[
        int, typer.Option("--concurrency", help="Maximum in-flight requests.")
    ] = 5,
    timeout: Annotated[
        float, typer.Option("--timeout", help="Per-request timeout in seconds.")
    ] = 30.0,
    description: Annotated[
        str, typer.Option("--description", "-d", help="Assessment objective.")
    ] = "",
) -> None:
    """Configure a new assessment profile for an authorized target."""
    target_cfg = storage.get_target(target_id)
    if not target_cfg:
        print_error(f"Target '{target_id}' does not exist in local storage. Add it first.")
        raise typer.Exit(code=1)

    assessment_id = f"ASM-{uuid.uuid4().hex[:8].upper()}"

    # Validate categories if provided
    valid_categories = []
    if categories:
        for cat_str in categories:
            try:
                valid_categories.append(AttackCategory(cat_str).value)
            except ValueError as err:
                print_error(f"Invalid attack category: '{cat_str}'.")
                raise typer.Exit(code=1) from err

    assessment_data = {
        "id": assessment_id,
        "name": name,
        "target_id": target_id,
        "target_model": target_cfg.model_name,
        "attack_categories": valid_categories,
        "selected_payloads": payload_ids if payload_ids else ["all"],
        "enable_mutation": enable_mutation,
        "mutation_strategies": mutation_strategies or ["rot13", "base64"],
        "max_variants_per_payload": max_variants,
        "concurrency": concurrency,
        "timeout_seconds": timeout,
        "description": description,
        "status": "CONFIGURED",
        "created_at": datetime.now(UTC).isoformat(),
        "completed_at": None,
        "vulnerable_count": 0,
    }

    storage.save_assessment(assessment_data)
    print_success(f"Assessment '{assessment_id}' created successfully for target '{target_id}'.")
    console.print(
        f"Run it using: [bold cyan]agentbreaker assessment run {assessment_id}[/bold cyan]"
    )


@assessment_app.command("list")
def list_assessments() -> None:
    """List all created and executed assessments."""
    assessments = storage.list_assessments()
    if not assessments:
        print_warning("No assessments found. Create one with 'agentbreaker assessment create'.")
        return

    table = create_table(
        "AgentBreaker Security Assessments",
        [
            ("Assessment ID", "left"),
            ("Name", "left"),
            ("Target", "left"),
            ("Mutation", "center"),
            ("Status", "center"),
            ("Created", "left"),
        ],
    )

    for a in assessments:
        status_col = a.get("status", "CONFIGURED")
        if status_col == "COMPLETED":
            status_style = "[bold green]COMPLETED[/bold green]"
        elif status_col == "RUNNING":
            status_style = "[bold yellow]RUNNING[/bold yellow]"
        elif status_col == "CANCELLED":
            status_style = "[bold red]CANCELLED[/bold red]"
        else:
            status_style = "[dim]CONFIGURED[/dim]"

        mut_style = "[green]ON[/green]" if a.get("enable_mutation") else "[dim]OFF[/dim]"

        table.add_row(
            f"[bold cyan]{a.get('id')}[/bold cyan]",
            a.get("name", "Unnamed"),
            a.get("target_id", "Unknown"),
            mut_style,
            status_style,
            a.get("created_at", "")[:19],
        )

    console.print(table)


@assessment_app.command("show")
def show_assessment(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier.")],
) -> None:
    """Show details and configuration for an assessment."""
    a = storage.get_assessment(assessment_id)
    if not a:
        print_error(f"Assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    details = (
        f"[bold white]Assessment ID:[/bold white] {a.get('id')}\n"
        f"[bold white]Name:[/bold white] {a.get('name')}\n"
        f"[bold white]Target ID:[/bold white] {a.get('target_id')} "
        f"({a.get('target_model')})\n"
        f"[bold white]Status:[/bold white] {a.get('status')}\n"
        f"[bold white]Attack Categories:[/bold white] "
        f"{a.get('attack_categories') or 'All Categories'}\n"
        f"[bold white]Mutation Enabled:[/bold white] {a.get('enable_mutation')}\n"
        f"[bold white]Mutation Strategies:[/bold white] {a.get('mutation_strategies')}\n"
        f"[bold white]Concurrency:[/bold white] {a.get('concurrency')}\n"
        f"[bold white]Created At:[/bold white] {a.get('created_at')}\n"
        f"[bold white]Completed At:[/bold white] {a.get('completed_at') or 'Not completed'}\n"
        f"[bold white]Description:[/bold white] {a.get('description') or 'None'}\n"
    )

    console.print(Panel(details, title=f"Assessment: {assessment_id}", border_style="cyan"))


@assessment_app.command("run")
def run_assessment(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to execute.")],
) -> None:
    """Execute an assessment through connectors, attacks, mutators, and oracle."""
    a = storage.get_assessment(assessment_id)
    if not a:
        print_error(f"Assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    target_id = a.get("target_id")
    target_cfg = storage.get_target(target_id)
    if not target_cfg:
        print_error(f"Target '{target_id}' configured for this assessment no longer exists.")
        raise typer.Exit(code=1)

    print_header(
        f"Executing Assessment: {assessment_id}",
        f"Target: {target_id} ({target_cfg.model_name}) | Endpoint: {target_cfg.endpoint_url}",
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Executing adversarial attack suite...", total=100)

        def _progress_cb(current: int, total: int, payload_id: str) -> None:
            pct = (current / total) * 100 if total > 0 else 0
            progress.update(
                task_id,
                completed=pct,
                description=f"Probe [{current}/{total}]: {payload_id}",
            )

        try:
            results, summary = run_assessment_sync(
                assessment_config=a,
                progress_callback=_progress_cb,
            )
        except Exception as err:
            print_error(f"Assessment execution failed: {err}")
            raise typer.Exit(code=1) from err

    # Display Execution Summary
    print_success(f"Assessment '{assessment_id}' execution completed successfully!")

    summary_table = create_table(
        "Evaluation Outcome Summary",
        [
            ("Metric", "left"),
            ("Value", "right"),
        ],
    )
    summary_table.add_row("Total Payloads Dispatched", str(summary["total_payloads"]))
    summary_table.add_row(
        "Vulnerable Outcomes", f"[bold red]{summary['vulnerable_count']}[/bold red]"
    )
    summary_table.add_row(
        "Defended Outcomes", f"[bold green]{summary['defended_count']}[/bold green]"
    )
    summary_table.add_row(
        "Inconclusive Outcomes", f"[bold yellow]{summary['inconclusive_count']}[/bold yellow]"
    )
    summary_table.add_row(
        "Execution Duration", f"{summary['started_at'][:19]} -> {summary['completed_at'][:19]}"
    )

    console.print(summary_table)

    # Preview sample findings if any
    vuln_results = [r for r in results if r.verdict == Verdict.VULNERABLE]
    if vuln_results:
        print_warning(
            f"Detected {len(vuln_results)} security vulnerabilities! "
            "View with: 'agentbreaker findings list'"
        )


@assessment_app.command("cancel")
def cancel_assessment(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to mark cancelled.")],
) -> None:
    """Cancel an assessment or mark its status as cancelled."""
    a = storage.get_assessment(assessment_id)
    if not a:
        print_error(f"Assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    a["status"] = "CANCELLED"
    storage.save_assessment(a)
    print_success(f"Assessment '{assessment_id}' marked as CANCELLED.")
