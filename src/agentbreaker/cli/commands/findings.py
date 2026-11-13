"""Vulnerability findings inspection and filtering commands."""

from typing import Annotated, Any

import typer
from rich.panel import Panel

from agentbreaker.cli.output import (
    console,
    create_table,
    format_severity,
    format_verdict,
    print_error,
    print_warning,
)
from agentbreaker.cli.storage import storage
from agentbreaker.schemas.enums import AttackCategory, Severity, Verdict

findings_app = typer.Typer(
    name="findings",
    help="Inspect, search, and filter discovered vulnerability findings.",
    no_args_is_help=True,
)


def _collect_all_findings(
    assessment_id: str | None = None,
) -> list[dict[str, Any]]:
    """Gather all evaluated finding records from stored results."""
    records: list[dict[str, Any]] = []

    if assessment_id:
        res_data = storage.get_results(assessment_id)
        if res_data:
            for r in res_data.get("results", []):
                r["_assessment_id"] = assessment_id
                records.append(r)
    else:
        for res_data in storage.list_results():
            a_id = res_data.get("assessment_id", "Unknown")
            for r in res_data.get("results", []):
                r["_assessment_id"] = a_id
                records.append(r)

    return records


@findings_app.command("list")
def list_findings(
    assessment_id: Annotated[
        str | None, typer.Option("--assessment", "-a", help="Filter by assessment ID.")
    ] = None,
    severity: Annotated[
        Severity | None, typer.Option("--severity", "-s", help="Filter by severity level.")
    ] = None,
    verdict: Annotated[
        Verdict | None, typer.Option("--verdict", "-v", help="Filter by evaluation verdict.")
    ] = None,
    category: Annotated[
        AttackCategory | None, typer.Option("--category", "-c", help="Filter by attack category.")
    ] = None,
) -> None:
    """List evaluation findings with optional severity, verdict, and category filters."""
    findings = _collect_all_findings(assessment_id)

    if severity:
        findings = [f for f in findings if f.get("severity") == severity.value]
    if verdict:
        findings = [f for f in findings if f.get("verdict") == verdict.value]
    if category:
        findings = [f for f in findings if f.get("category") == category.value]

    if not findings:
        print_warning("No findings matched the specified filter criteria.")
        return

    table = create_table(
        f"Evaluation Findings ({len(findings)} records)",
        [
            ("Finding ID", "left"),
            ("Assessment", "left"),
            ("Verdict", "center"),
            ("Severity", "center"),
            ("Category", "left"),
            ("Confidence", "right"),
        ],
    )

    for f in findings:
        f_id = f"{f.get('_assessment_id')}_{f.get('payload_id')}"
        table.add_row(
            f"[bold cyan]{f_id}[/bold cyan]",
            str(f.get("_assessment_id")),
            format_verdict(f.get("verdict", "")),
            format_severity(f.get("severity", "")),
            f.get("category", ""),
            f"{f.get('confidence', 0.0):.2f}",
        )

    console.print(table)


@findings_app.command("show")
def show_finding(
    finding_id: Annotated[
        str, typer.Argument(help="Identifier of finding to inspect (e.g. ASM-XXXX_PAYLOAD).")
    ],
) -> None:
    """Display exhaustive technical evidence, reasons, and CVSS score for a finding."""
    # Finding ID format: <assessment_id>_<payload_id>
    if "_" not in finding_id:
        print_error("Invalid finding ID format. Expected format: '<assessment_id>_<payload_id>'.")
        raise typer.Exit(code=1)

    assessment_id, payload_id = finding_id.split("_", 1)
    res_data = storage.get_results(assessment_id)

    if not res_data:
        print_error(f"Results for assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    matching = next(
        (r for r in res_data.get("results", []) if r.get("payload_id") == payload_id),
        None,
    )
    if not matching:
        print_error(
            f"Finding with payload '{payload_id}' not found in assessment '{assessment_id}'."
        )
        raise typer.Exit(code=1)

    reasons_formatted = "\n".join(f"  • {r}" for r in matching.get("reasons", []))
    evidence_items = matching.get("evidence", [])
    evidence_desc = (
        "\n".join(
            f"  • [{e.get('evaluator_name')}] {e.get('description')} "
            f"(Confidence: {e.get('confidence_weight')})"
            for e in evidence_items
        )
        if evidence_items
        else "  None recorded"
    )

    details = (
        f"[bold white]Finding ID:[/bold white] {finding_id}\n"
        f"[bold white]Assessment ID:[/bold white] {assessment_id}\n"
        f"[bold white]Payload ID:[/bold white] {matching.get('payload_id')}\n"
        f"[bold white]Parent ID (Lineage):[/bold white] "
        f"{matching.get('parent_id') or 'Baseline (None)'}\n"
        f"[bold white]Verdict:[/bold white] {format_verdict(matching.get('verdict', ''))}\n"
        f"[bold white]Confidence:[/bold white] {matching.get('confidence', 0.0):.2f}\n"
        f"[bold white]Severity:[/bold white] {format_severity(matching.get('severity', ''))} "
        f"(CVSS {matching.get('cvss_score', 0.0):.1f})\n"
        f"[bold white]OWASP Mapping:[/bold white] {matching.get('owasp_id') or 'N/A'}\n"
        f"[bold white]MITRE ATLAS:[/bold white] {matching.get('mitre_atlas_id') or 'N/A'}\n"
        f"[bold white]Latency:[/bold white] {matching.get('latency_ms', 0.0):.1f}ms\n\n"
        f"[bold cyan]Evaluator Verdict Reasons:[/bold cyan]\n{reasons_formatted or '  None'}\n\n"
        f"[bold cyan]Structured Evidence Items ({len(evidence_items)}):[/bold cyan]\n"
        f"{evidence_desc}\n\n"
        f"[bold cyan]Detected Violations:[/bold cyan]\n"
        f"  Matched Patterns: {matching.get('matched_patterns') or 'None'}\n"
        f"  Detected Canaries: {matching.get('detected_canaries') or 'None'}\n"
        f"  Tool Call Violations: {matching.get('tool_call_violations') or 'None'}"
    )

    console.print(Panel(details, title=f"Finding Details: {finding_id}", border_style="cyan"))


@findings_app.command("filter")
def filter_findings(
    severity: Annotated[
        Severity | None, typer.Option("--severity", "-s", help="Filter by severity.")
    ] = None,
    verdict: Annotated[
        Verdict | None, typer.Option("--verdict", "-v", help="Filter by verdict.")
    ] = None,
    category: Annotated[
        AttackCategory | None, typer.Option("--category", "-c", help="Filter by category.")
    ] = None,
) -> None:
    """Filter findings across all completed assessments."""
    list_findings(severity=severity, verdict=verdict, category=category)
