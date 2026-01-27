"""Workflow helper functions for CLI commands.

This module provides helper functions used by the --full workflow
and other multi-phase operations.
"""

import csv
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def run_probe_for_full(cfg: dict[str, Any], outdir: Path) -> bool:
    """Run probe phase as part of --full workflow.

    Returns True if probe succeeded, False otherwise.
    Probe failures are non-fatal - the benchmark continues with a warning.

    Args:
        cfg: Configuration dictionary
        outdir: Output directory for probe results

    Returns:
        True if all probes succeeded, False otherwise
    """
    from ..common.cli_helpers import (
        is_any_system_cloud_mode,
        is_any_system_managed_mode,
    )
    from ..gather.system_probe import probe_all
    from .probing import probe_managed_systems, probe_remote_systems

    has_cloud = is_any_system_cloud_mode(cfg)
    has_managed = is_any_system_managed_mode(cfg)

    try:
        any_success = True

        if has_cloud:
            console.print("[blue]Probing cloud instances...[/]")
            success = probe_remote_systems(cfg, outdir)
            if success:
                console.print("[green]✓ Cloud system probes completed[/]")
            else:
                console.print("[yellow]⚠ Some cloud system probes failed[/]")
                any_success = False

        if has_managed:
            console.print("[blue]Probing managed systems...[/]")
            success = probe_managed_systems(cfg, outdir)
            if success:
                console.print("[green]✓ Managed system probes completed[/]")
            else:
                console.print("[yellow]⚠ Some managed system probes failed[/]")
                any_success = False

        if not has_cloud and not has_managed:
            # Local benchmark - probe current system
            meta = probe_all(outdir)
            console.print(
                f"[green]✓ System probe saved to:[/] {outdir / 'system.json'}"
            )
            console.print(
                f"[dim]Found {meta['cpu_count_logical']} logical CPUs, "
                f"{meta['memory_total_gb']}GB RAM[/]"
            )

        return any_success

    except Exception as e:
        console.print(f"[yellow]⚠ Probe failed (continuing): {e}[/]")
        return False


def run_report_for_full(cfg: dict[str, Any], collect_report_files_fn: Any) -> bool:
    """Run report generation as part of --full workflow.

    Returns True if report generation succeeded, False otherwise.
    Report failures are non-fatal - results are already saved to runs.csv.

    Args:
        cfg: Configuration dictionary
        collect_report_files_fn: Function to collect report files from a directory

    Returns:
        True if report generation succeeded, False otherwise
    """
    from ..report.render import render_report

    try:
        actual_output_path = render_report(cfg)
        console.print(f"[green]✓ Report generated:[/] {actual_output_path}")
        report_files = collect_report_files_fn(actual_output_path)
        if report_files:
            console.print(f"[dim]Report available at:[/] {report_files[0]}")
        return True
    except Exception as e:
        console.print(f"[yellow]⚠ Report generation failed: {e}[/]")
        return False


def report_query_results(runs_file: Path) -> bool:
    """Report query results summary including any errors.

    Args:
        runs_file: Path to the runs.csv file

    Returns:
        True if all queries succeeded, False if any failed.
    """
    total = 0
    successful = 0
    failed = 0
    # Track unique errors per system: system -> {query -> error}
    errors_by_system: dict[str, dict[str, str]] = {}

    with open(runs_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            if row.get("success", "").lower() == "true":
                successful += 1
            else:
                failed += 1
                system = row.get("system", "unknown")
                query = row.get("query", "unknown")
                error = row.get("error", "unknown error")
                if system not in errors_by_system:
                    errors_by_system[system] = {}
                # Only keep first error per query per system
                if query not in errors_by_system[system]:
                    errors_by_system[system][query] = error

    # Print summary
    console.print()
    console.print("[bold]Query Execution Summary:[/bold]")
    console.print(f"  Total query runs: {total}")
    console.print(f"  [green]Successful: {successful}[/green]")

    if failed > 0:
        console.print(f"  [red]Failed: {failed}[/red]")
        console.print()
        console.print("[bold red]Failed Queries:[/bold red]")
        for system, errors in sorted(errors_by_system.items()):
            console.print(f"  [bold]{system}:[/bold]")
            for query, error in sorted(errors.items()):
                error_preview = error[:80] + "..." if len(error) > 80 else error
                console.print(f"    {query}: {error_preview}")
        return False

    return True
