"""Reporting and comparative analytics CLI commands."""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from agentbreaker.cli.output import (
    console,
    create_table,
    print_error,
    print_header,
    print_success,
    print_warning,
)
from agentbreaker.reporting.exceptions import ReportNotFoundError
from agentbreaker.reporting.models import ReportFormat
from agentbreaker.reporting.service import ReportingService

report_app = typer.Typer(
    name="report",
    help="Generate research reports, inspect analytical metrics, and compare assessments.",
    no_args_is_help=True,
)


@report_app.command("list")
def list_reports() -> None:
    """List all saved research audit report files in local storage."""
    service = ReportingService()
    reports = service.list_reports()
    if not reports:
        print_warning("No saved reports found. Generate one with 'agentbreaker report generate'.")
        return

    table = create_table(
        "Available Audit Reports",
        [
            ("Report File", "left"),
            ("Format", "center"),
            ("Size", "right"),
            ("Modified (UTC)", "left"),
        ],
    )

    for r in reports:
        size_kb = f"{r['size_bytes'] / 1024:.1f} KB"
        table.add_row(
            f"[bold cyan]{r['report_file']}[/bold cyan]",
            r["format"].upper(),
            size_kb,
            r["modified_at"][:19],
        )

    console.print(table)


@report_app.command("generate")
def generate_report(
    assessment_id: Annotated[
        str, typer.Argument(help="Assessment identifier to compile into report.")
    ],
    format: Annotated[
        str, typer.Option("--format", "-f", help="Output format ('json', 'markdown', or 'html').")
    ] = "json",
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Custom destination file path.")
    ] = None,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", "-y", help="Overwrite destination without prompting.")
    ] = False,
) -> None:
    """Generate a structured research audit report for a completed assessment."""
    fmt_clean = format.strip().lower()
    fmt_map = {
        "json": ReportFormat.JSON,
        "markdown": ReportFormat.MARKDOWN,
        "md": ReportFormat.MARKDOWN,
        "html": ReportFormat.HTML,
        "htm": ReportFormat.HTML,
    }

    if fmt_clean not in fmt_map:
        print_error(f"Unsupported report format '{format}'. Supported: 'json', 'markdown', 'html'.")
        raise typer.Exit(code=1)

    target_fmt = fmt_map[fmt_clean]
    service = ReportingService()

    if output and output.exists() and not overwrite:
        sure = typer.confirm(f"File '{output}' already exists. Overwrite?")
        if not sure:
            print_warning("Report generation aborted.")
            return

    try:
        saved_path = service.save_report(
            assessment_id=assessment_id,
            output_format=target_fmt,
            dest_path=output,
        )
        print_success(
            f"Report successfully generated in {target_fmt.value.upper()} format at: '{saved_path}'"
        )
    except ReportNotFoundError as err:
        print_error(str(err))
        raise typer.Exit(code=1) from err
    except Exception as err:
        print_error(f"Failed to generate report: {err}")
        raise typer.Exit(code=1) from err


@report_app.command("show")
def show_report(
    assessment_id: Annotated[
        str, typer.Argument(help="Assessment identifier (e.g. ASM-XXXX) or report ID.")
    ],
) -> None:
    """Display an executive summary and high-level analytical metrics for a report."""
    clean_id = assessment_id.removeprefix("RPT-")
    service = ReportingService()

    try:
        report = service.build_report(clean_id)
    except ReportNotFoundError as err:
        print_error(str(err))
        raise typer.Exit(code=1) from err

    print_header(
        f"Research Audit Report: {report.report_id}",
        f"Target: {report.target_id} ({report.target_model}) | UTC: {report.generated_at[:19]}",
    )

    # Executive summary panel
    exec_text = (
        f"[bold white]Summary Verdict:[/bold white] {report.executive_summary.verdict_summary}\n\n"
        f"[bold white]Evaluated Test Cases:[/bold white] {report.verdicts.total}\n"
        f"[bold red]Critical Vulnerabilities:[/bold red] {report.severities.critical} | "
        f"[bold orange3]High:[/bold orange3] {report.severities.high} | "
        f"[bold yellow]Medium:[/bold yellow] {report.severities.medium} | "
        f"[bold blue]Low:[/bold blue] {report.severities.low}\n"
        f"[bold green]Defended:[/bold green] {report.verdicts.defended} "
        f"({report.verdicts.defended_rate}%)\n"
        f"[bold yellow]Inconclusive:[/bold yellow] {report.verdicts.inconclusive} "
        f"({report.verdicts.inconclusive_rate}%)"
    )
    console.print(Panel(exec_text, title="Executive Summary", border_style="cyan"))

    # Category breakdown table
    cat_table = create_table(
        "Attack Category Analytics",
        [
            ("Category", "left"),
            ("Total", "right"),
            ("Vulnerable", "right"),
            ("Defended", "right"),
            ("Inconclusive", "right"),
            ("Vulnerability Rate", "right"),
        ],
    )
    for cat in report.categories:
        cat_table.add_row(
            cat.name,
            str(cat.total_evaluated),
            f"[bold red]{cat.vulnerable_count}[/bold red]",
            f"[bold green]{cat.defended_count}[/bold green]",
            f"[bold yellow]{cat.inconclusive_count}[/bold yellow]",
            f"{cat.vulnerability_rate:.1f}%",
        )
    console.print(cat_table)


@report_app.command("analytics")
def show_analytics(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to analyze.")],
) -> None:
    """Display OWASP LLM Top 10, MITRE ATLAS, and evidence metrics for an assessment."""
    clean_id = assessment_id.removeprefix("RPT-")
    service = ReportingService()

    try:
        report = service.build_report(clean_id)
    except ReportNotFoundError as err:
        print_error(str(err))
        raise typer.Exit(code=1) from err

    print_header(f"Assessment Security Analytics: {clean_id}")

    # OWASP Table
    owasp_table = create_table(
        "OWASP Top 10 for LLMs Coverage",
        [
            ("OWASP Category", "left"),
            ("Tested?", "center"),
            ("Evaluated", "right"),
            ("Vulnerabilities", "right"),
        ],
    )
    for o in report.owasp_coverage:
        status_str = "[bold green]YES[/bold green]" if o.tested else "[dim]NO[/dim]"
        vuln_str = f"[bold red]{o.vulnerable_count}[/bold red]" if o.vulnerable_count > 0 else "0"
        owasp_table.add_row(o.title, status_str, str(o.evaluated_count), vuln_str)
    console.print(owasp_table)

    # MITRE ATLAS Table
    if report.mitre_coverage:
        mitre_table = create_table(
            "MITRE ATLAS Matrix Techniques Observed",
            [
                ("Technique ID", "left"),
                ("Technique Name", "left"),
                ("Evaluated", "right"),
                ("Vulnerabilities", "right"),
            ],
        )
        for m in report.mitre_coverage:
            v_str = f"[bold red]{m.vulnerable_count}[/bold red]" if m.vulnerable_count > 0 else "0"
            mitre_table.add_row(m.technique_id, m.technique_name, str(m.evaluated_count), v_str)
        console.print(mitre_table)

    # Evidence & Confidence
    ev = report.evidence_metrics
    high_cnt = ev.confidence_distribution.get("high", 0)
    med_cnt = ev.confidence_distribution.get("medium", 0)
    low_cnt = ev.confidence_distribution.get("low", 0)
    ev_panel = (
        f"[bold white]Total Structured Evidence Items:[/bold white] {ev.total_evidence_items}\n"
        f"[bold white]Mean Confidence Score:[/bold white] {ev.mean_confidence:.2f}\n"
        f"[bold white]Confidence Distribution:[/bold white] High: {high_cnt} | "
        f"Medium: {med_cnt} | Low: {low_cnt}\n"
        f"[bold white]Confirmed Direct Evidence:[/bold white] {ev.confirmed_evidence_count}\n"
        f"[bold white]Heuristic / Advisory Observations:[/bold white] {ev.heuristic_evidence_count}"
    )
    console.print(Panel(ev_panel, title="Evidence & Confidence Metrics", border_style="cyan"))


@report_app.command("compare")
def compare_assessments(
    assessment_1: Annotated[str, typer.Argument(help="First assessment ID (baseline).")],
    assessment_2: Annotated[str, typer.Argument(help="Second assessment ID (comparison target).")],
) -> None:
    """Compare evaluation outcomes, vulnerabilities, and coverage across historical assessments."""
    service = ReportingService()
    try:
        comparison = service.compare_assessments([assessment_1, assessment_2])
    except Exception as err:
        print_error(f"Comparison failed: {err}")
        raise typer.Exit(code=1) from err

    print_header(
        f"Comparative Assessment Analysis: {assessment_1} vs {assessment_2}",
        f"Generated: {comparison.generated_at[:19]} UTC",
    )

    if comparison.compatibility_warnings:
        for w in comparison.compatibility_warnings:
            print_warning(f"Compatibility Warning: {w}")

    # Verdict delta table
    comp_table = create_table(
        "Verdict Outcome Comparison",
        [
            ("Assessment ID", "left"),
            ("Vulnerable", "right"),
            ("Defended", "right"),
            ("Inconclusive", "right"),
        ],
    )
    for a_id, v in comparison.verdict_deltas.items():
        comp_table.add_row(
            f"[bold cyan]{a_id}[/bold cyan]",
            f"[bold red]{v.get('vulnerable', 0)}[/bold red]",
            f"[bold green]{v.get('defended', 0)}[/bold green]",
            f"[bold yellow]{v.get('inconclusive', 0)}[/bold yellow]",
        )
    console.print(comp_table)

    res_str = ", ".join(comparison.resolved_vulnerabilities) or "None"
    new_str = ", ".join(comparison.new_vulnerabilities) or "None"
    per_str = ", ".join(comparison.persistent_vulnerabilities) or "None"

    res_count = len(comparison.resolved_vulnerabilities)
    new_count = len(comparison.new_vulnerabilities)
    per_count = len(comparison.persistent_vulnerabilities)

    summary_panel = (
        f"[bold green]Resolved Vulnerabilities ({res_count}):[/bold green] {res_str}\n\n"
        f"[bold red]New Vulnerabilities ({new_count}):[/bold red] {new_str}\n\n"
        f"[bold yellow]Persistent Vulnerabilities ({per_count}):[/bold yellow] {per_str}"
    )
    console.print(Panel(summary_panel, title="Vulnerability Progression", border_style="cyan"))


@report_app.command("export")
def export_report(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to export.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Target output file path.")],
    format: Annotated[
        str, typer.Option("--format", "-f", help="Export format ('json', 'markdown', 'html').")
    ] = "json",
    overwrite: Annotated[
        bool, typer.Option("--overwrite", "-y", help="Overwrite destination without prompting.")
    ] = False,
) -> None:
    """Export an assessment report directly to a specified output file path."""
    generate_report(
        assessment_id=assessment_id,
        format=format,
        output=output,
        overwrite=overwrite,
    )
