"""Assessment results inspection and structured audit report export commands."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from agentbreaker.cli.output import (
    console,
    create_table,
    format_severity,
    format_verdict,
    print_error,
    print_success,
    print_warning,
)
from agentbreaker.cli.storage import storage

results_app = typer.Typer(
    name="results",
    help="Review evaluation outcomes and export structured research audit reports.",
    no_args_is_help=True,
)


@results_app.command("list")
def list_results() -> None:
    """List all available assessment execution outcome records."""
    all_results = storage.list_results()
    if not all_results:
        print_warning("No assessment results available. Run an assessment first.")
        return

    table = create_table(
        "Available Assessment Results",
        [
            ("Assessment ID", "left"),
            ("Target", "left"),
            ("Total", "right"),
            ("Vulnerable", "right"),
            ("Defended", "right"),
            ("Inconclusive", "right"),
            ("Completed", "left"),
        ],
    )

    for item in all_results:
        meta = item.get("metadata", {})
        table.add_row(
            f"[bold cyan]{item.get('assessment_id')}[/bold cyan]",
            meta.get("target_id", "Unknown"),
            str(meta.get("total_payloads", 0)),
            f"[bold red]{meta.get('vulnerable_count', 0)}[/bold red]",
            f"[bold green]{meta.get('defended_count', 0)}[/bold green]",
            f"[bold yellow]{meta.get('inconclusive_count', 0)}[/bold yellow]",
            meta.get("completed_at", "")[:19],
        )

    console.print(table)


@results_app.command("show")
def show_results(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to inspect.")],
) -> None:
    """Show detailed results summary and breakdown for an assessment."""
    res_data = storage.get_results(assessment_id)
    if not res_data:
        print_error(f"Results for assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    meta = res_data.get("metadata", {})
    records = res_data.get("results", [])

    summary_panel = (
        f"[bold white]Assessment ID:[/bold white] {assessment_id}\n"
        f"[bold white]Target:[/bold white] {meta.get('target_id')} "
        f"({meta.get('target_model')})\n"
        f"[bold white]Execution Interval:[/bold white] "
        f"{meta.get('started_at', '')[:19]} -> {meta.get('completed_at', '')[:19]}\n"
        f"[bold white]Total Evaluated:[/bold white] {len(records)}\n"
        f"[bold red]Vulnerable:[/bold red] {meta.get('vulnerable_count', 0)} | "
        f"[bold green]Defended:[/bold green] {meta.get('defended_count', 0)} | "
        f"[bold yellow]Inconclusive:[/bold yellow] {meta.get('inconclusive_count', 0)}"
    )

    console.print(Panel(summary_panel, title=f"Results: {assessment_id}", border_style="cyan"))

    table = create_table(
        f"Evaluated Vectors ({len(records)} items)",
        [
            ("Payload ID", "left"),
            ("Parent ID", "left"),
            ("Verdict", "center"),
            ("Confidence", "right"),
            ("Severity", "center"),
            ("CVSS", "right"),
        ],
    )

    for r in records:
        table.add_row(
            r.get("payload_id", ""),
            r.get("parent_id") or "[dim]None[/dim]",
            format_verdict(r.get("verdict", "")),
            f"{r.get('confidence', 0.0):.2f}",
            format_severity(r.get("severity", "")),
            f"{r.get('cvss_score', 0.0):.1f}",
        )

    console.print(table)


def _render_markdown_report(assessment_id: str, meta: dict, records: list[dict]) -> str:
    """Generate Markdown structured security report."""
    md = [
        f"# AgentBreaker Security Assessment Audit Report: {assessment_id}",
        "",
        "**Platform:** AgentBreaker — AI Red Teaming Framework  ",
        "**Organization:** AshlynxCyber Security Systems  ",
        f"**Date:** {meta.get('completed_at', '')}  ",
        f"**Target System:** {meta.get('target_id')} ({meta.get('target_model')})  ",
        f"**Execution Status:** {meta.get('status', 'COMPLETED')}  ",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"- **Total Payloads Evaluated:** {len(records)}",
        f"- **Vulnerabilities Detected:** {meta.get('vulnerable_count', 0)}",
        f"- **Defended Vectors:** {meta.get('defended_count', 0)}",
        f"- **Inconclusive Outcomes:** {meta.get('inconclusive_count', 0)}",
        "",
        "| Metric | Count | Rate (%) |",
        "|---|:---:|:---:|",
    ]

    total = max(1, len(records))
    v_cnt = meta.get("vulnerable_count", 0)
    d_cnt = meta.get("defended_count", 0)
    i_cnt = meta.get("inconclusive_count", 0)

    md.append(f"| Vulnerable | {v_cnt} | {(v_cnt / total) * 100:.1f}% |")
    md.append(f"| Defended | {d_cnt} | {(d_cnt / total) * 100:.1f}% |")
    md.append(f"| Inconclusive | {i_cnt} | {(i_cnt / total) * 100:.1f}% |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Granular Evaluation Findings")
    md.append("")
    md.append("| Payload ID | Parent ID | Category | Verdict | Confidence | Severity | CVSS |")
    md.append("|---|---|---|:---:|:---:|:---:|:---:|")

    for r in records:
        md.append(
            f"| `{r.get('payload_id')}` | "
            f"`{r.get('parent_id') or 'Baseline'}` | "
            f"{r.get('category')} | "
            f"**{r.get('verdict')}** | "
            f"{r.get('confidence', 0.0):.2f} | "
            f"{r.get('severity')} | "
            f"{r.get('cvss_score', 0.0):.1f} |"
        )

    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Discovered Vulnerability Details")
    md.append("")

    vulns = [r for r in records if r.get("verdict") == "VULNERABLE"]
    if not vulns:
        md.append("No security vulnerabilities were identified during this assessment.")
    else:
        for v in vulns:
            md.append(f"### Vulnerability: `{v.get('payload_id')}`")
            md.append(f"- **Category:** {v.get('category')}")
            md.append(f"- **Severity:** {v.get('severity')} (CVSS {v.get('cvss_score')})")
            md.append(f"- **OWASP:** {v.get('owasp_id') or 'N/A'}")
            md.append(f"- **MITRE ATLAS:** {v.get('mitre_atlas_id') or 'N/A'}")
            md.append(f"- **Confidence:** {v.get('confidence', 0.0):.2f}")
            md.append("- **Evaluator Reasons:**")
            for reason in v.get("reasons", []):
                md.append(f"  - {reason}")
            md.append("- **Violations Detected:**")
            if v.get("matched_patterns"):
                md.append(f"  - Matched Patterns: `{v.get('matched_patterns')}`")
            if v.get("detected_canaries"):
                md.append(f"  - Leaked Canaries: `{v.get('detected_canaries')}`")
            if v.get("tool_call_violations"):
                md.append(f"  - Forbidden Tools: `{v.get('tool_call_violations')}`")
            md.append("")

    return "\n".join(md)


@results_app.command("export")
def export_results(
    assessment_id: Annotated[str, typer.Argument(help="Assessment identifier to export.")],
    format: Annotated[
        str, typer.Option("--format", "-f", help="Export format ('json' or 'markdown').")
    ] = "json",
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Target output file path.")
    ] = None,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", "-y", help="Overwrite destination without prompt.")
    ] = False,
) -> None:
    """Export assessment results as valid structured JSON or Markdown security report."""
    res_data = storage.get_results(assessment_id)
    if not res_data:
        print_error(f"Results for assessment '{assessment_id}' not found.")
        raise typer.Exit(code=1)

    fmt_lower = format.strip().lower()
    if fmt_lower not in ("json", "markdown", "md"):
        print_error(f"Unsupported export format '{format}'. Supported: 'json', 'markdown'.")
        raise typer.Exit(code=1)

    default_filename = (
        f"{assessment_id}_report.json" if fmt_lower == "json" else f"{assessment_id}_report.md"
    )
    dest_path = output or Path(default_filename)

    if dest_path.exists() and not overwrite:
        sure = typer.confirm(f"File '{dest_path}' already exists. Overwrite?")
        if not sure:
            print_warning("Export aborted.")
            return

    meta = res_data.get("metadata", {})
    records = res_data.get("results", [])

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt_lower == "json":
        # Structured clean JSON export
        export_payload = {
            "report_id": f"RPT-{assessment_id}",
            "assessment_id": assessment_id,
            "generated_at": meta.get("completed_at"),
            "metadata": meta,
            "results": records,
        }
        dest_path.write_text(json.dumps(export_payload, indent=2), encoding="utf-8")
    else:
        # Markdown export
        md_content = _render_markdown_report(assessment_id, meta, records)
        dest_path.write_text(md_content, encoding="utf-8")

    print_success(f"Results for assessment '{assessment_id}' exported to '{dest_path}'.")
