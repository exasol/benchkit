"""Status display functionality for benchmark projects.

This module handles displaying benchmark status:
- Project summaries from config files
- Detailed status with phase completion
- Infrastructure details (IPs, SSH commands)
- Query execution statistics
"""

import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    import pandas as pd

console = Console()


def extract_error_summary(error_msg: str | None) -> str:
    """Extract key error type from verbose error messages.

    Examples:
        'MEMORY_LIMIT_EXCEEDED (14.07 GiB > 13.97 GiB)'
        'Query timeout'
        'Connection refused'
    """
    if not error_msg:
        return "-"

    error_lower = error_msg.lower()

    # ClickHouse specific errors
    if "memory_limit_exceeded" in error_lower:
        # Extract memory values if present
        match = re.search(
            r"would use ([\d.]+\s*\w+).*maximum:\s*([\d.]+\s*\w+)", error_msg
        )
        if match:
            return f"MEMORY_LIMIT_EXCEEDED ({match.group(1)} > {match.group(2)})"
        return "MEMORY_LIMIT_EXCEEDED"

    if "timeout" in error_lower:
        return "Query timeout"

    if "connection refused" in error_lower:
        return "Connection refused"

    if "syntax error" in error_lower:
        return "Syntax error"

    # Exasol specific errors
    if "exasol" in error_lower and "exception" in error_lower:
        # Try to extract error code
        match = re.search(r"error code:\s*(\w+)", error_msg, re.IGNORECASE)
        if match:
            return f"Exasol: {match.group(1)}"

    # Generic truncation for unknown errors
    if len(error_msg) > 50:
        return error_msg[:47] + "..."
    return error_msg


def load_phase_data(
    results_dir: Path, system_names: list[str]
) -> dict[str, dict[str, Any]]:
    """Load phase completion data for all systems.

    Returns dict: {system_name: {'setup': {...}, 'load': {...}, 'infra_timing_s': float|None}}
    """
    from ..util import load_json

    phase_data: dict[str, dict[str, Any]] = {}

    for system_name in system_names:
        # Get deployment timing (unified: checks managed state first, then cloud infra)
        infra_timing_s = get_deployment_timing(results_dir, system_name)

        phase_data[system_name] = {
            "setup": None,
            "load": None,
            "infra_timing_s": infra_timing_s,
        }

        # Load setup completion data
        setup_path = results_dir / f"setup_complete_{system_name}.json"
        if setup_path.exists():
            try:
                phase_data[system_name]["setup"] = load_json(setup_path)
            except Exception:
                phase_data[system_name]["setup"] = {"exists": True}

        # Load load completion data
        load_path = results_dir / f"load_complete_{system_name}.json"
        if load_path.exists():
            try:
                phase_data[system_name]["load"] = load_json(load_path)
            except Exception:
                phase_data[system_name]["load"] = {"exists": True}

    return phase_data


def get_deployment_timing(results_dir: Path, system_name: str) -> float | None:
    """Get deployment timing in seconds for any system type.

    Timing retrieval that checks the appropriate source based on system type:
    - Managed systems: Only use managed state file (no fallback to terraform)
    - Cloud systems: Use global terraform timing

    Args:
        results_dir: Results directory path
        system_name: Name of the system

    Returns:
        Deployment timing in seconds, or None if not available.
    """
    from ..util import load_json

    # Check managed state first (per-system timing for self-managed deployments)
    state_file = results_dir / "managed" / system_name / "benchkit_state.json"
    if state_file.exists():
        # This is a managed system - only use its own timing, don't fall back to terraform
        try:
            data = load_json(state_file)
            if isinstance(data, dict):
                timing = data.get("deployment_timing_s")
                if timing and timing > 0:
                    return float(timing)
        except Exception:
            pass
        # Managed system with no timing recorded - return None (don't use terraform timing)
        return None

    # Only use terraform timing for cloud systems (no managed state file exists)
    infra_path = results_dir / "infrastructure_provisioning.json"
    if infra_path.exists():
        try:
            data = load_json(infra_path)
            if isinstance(data, dict):
                timing = data.get("infrastructure_provisioning_s")
                if timing and timing > 0:
                    return float(timing)
        except Exception:
            pass

    return None


def load_runs_data(results_dir: Path) -> "pd.DataFrame | None":
    """Load runs.csv and return as DataFrame, or None if not found."""
    import pandas as pd

    runs_csv = results_dir / "runs.csv"
    if not runs_csv.exists():
        return None

    try:
        return pd.read_csv(runs_csv)
    except Exception:
        return None


def get_query_stats_per_system(
    df: "pd.DataFrame",
) -> dict[str, dict[str, Any]]:
    """Compute query statistics per system.

    Returns: {system: {total, success, failed, avg_ms, errors: [(query, failed, total, error)]}}
    """
    stats: dict[str, dict[str, Any]] = {}

    for system in df["system"].unique():
        system_df = df[df["system"] == system]
        total = len(system_df)
        success = len(system_df[system_df["success"] == True])  # noqa: E712
        failed = total - success

        # Calculate average for successful queries only
        success_df = system_df[system_df["success"] == True]  # noqa: E712
        avg_ms = success_df["elapsed_ms"].mean() if len(success_df) > 0 else 0

        # Get error details for failed queries
        errors: list[tuple[str, int, int, str]] = []
        if failed > 0:
            failed_df = system_df[system_df["success"] == False]  # noqa: E712
            for query in failed_df["query"].unique():
                query_df = system_df[system_df["query"] == query]
                query_failed = len(query_df[query_df["success"] == False])  # noqa: E712
                query_total = len(query_df)
                # Get first error message
                first_error = failed_df[failed_df["query"] == query]["error"].iloc[0]
                error_summary = extract_error_summary(first_error)
                errors.append((query, query_failed, query_total, error_summary))

        stats[system] = {
            "total": total,
            "success": success,
            "failed": failed,
            "avg_ms": avg_ms,
            "errors": errors,
        }

    return stats


def check_infra_available(
    cfg: dict[str, Any], system_name: str, infra_ips: dict[str, Any] | None
) -> tuple[str, str]:
    """Check if infrastructure for system is still running.

    Handles both cloud (Terraform) and managed (self-managed) systems.

    Returns (status, display):
    - ('up', '[green]✓ up[/]') - SSH connectivity confirmed
    - ('down', '[red]✗ down[/]') - Cannot reach instance
    - ('na', '[dim]-[/]') - Local mode, N/A
    - ('unknown', '[yellow]?[/]') - No IP info available
    """
    from ..common.cli_helpers import (
        get_cloud_ssh_key_path,
        get_managed_deployment_dir,
        get_managed_systems,
        is_any_system_cloud_mode,
        is_managed_system,
    )

    # Check if system has infrastructure (cloud or managed)
    has_cloud = is_any_system_cloud_mode(cfg)
    has_managed = is_managed_system(cfg, system_name)

    # Local mode - infrastructure N/A
    if not has_cloud and not has_managed:
        return ("na", "[dim]-[/]")

    # No infrastructure IPs available
    if not infra_ips or system_name not in infra_ips:
        return ("unknown", "[yellow]?[/]")

    system_ips = infra_ips[system_name]

    # Get the public IP (handle both single and multinode)
    if "public_ip" in system_ips:
        ip = system_ips["public_ip"]
    elif "public_ips" in system_ips:
        ip = system_ips["public_ips"][0]  # Check first node
    else:
        return ("unknown", "[yellow]?[/]")

    # For managed systems, check if we have SSH command in infra_ips
    ssh_command = system_ips.get("ssh_command")
    if ssh_command and has_managed:
        # Parse the SSH command to extract key path
        key_match = re.search(r"-i\s+([^\s]+)", ssh_command)
        key_path = key_match.group(1) if key_match else None

        # Extract user from command
        user_match = re.search(r"(\w+)@", ssh_command)
        ssh_user = user_match.group(1) if user_match else "ubuntu"

        # Resolve key path (may be relative to deployment dir)
        if key_path:
            key_path = os.path.expanduser(key_path)
            # If relative, try to resolve from managed system deployment dir
            if not os.path.isabs(key_path) and not os.path.exists(key_path):
                for system in get_managed_systems(cfg):
                    if system["name"] == system_name:
                        deployment_dir = get_managed_deployment_dir(cfg, system)
                        resolved_path = os.path.join(deployment_dir, key_path)
                        if os.path.exists(resolved_path):
                            key_path = resolved_path
                        break

        ssh_opts = "-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes"
        if key_path and os.path.exists(key_path):
            ssh_opts += f" -i {key_path}"

        cmd = f'ssh {ssh_opts} {ssh_user}@{ip} "echo ok" 2>/dev/null'
    else:
        # Cloud system - use cloud SSH key
        ssh_key = get_cloud_ssh_key_path(cfg) or ""
        if ssh_key:
            ssh_key = os.path.expanduser(ssh_key)

        ssh_opts = "-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes"
        if ssh_key and os.path.exists(ssh_key):
            ssh_opts += f" -i {ssh_key}"

        cmd = f'ssh {ssh_opts} ubuntu@{ip} "echo ok" 2>/dev/null'

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10  # nosec B602
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return ("up", "[green]✓ up[/]")
        else:
            return ("down", "[red]✗ down[/]")
    except subprocess.TimeoutExpired:
        return ("down", "[red]✗ down[/]")
    except Exception:
        return ("unknown", "[yellow]?[/]")


def format_timing(seconds: float | None) -> str:
    """Format timing value for display."""
    if seconds is None or seconds == 0:
        return ""
    if seconds < 60:
        return f"({seconds:.1f}s)"
    minutes = seconds / 60
    return f"({minutes:.1f}m)"


def show_project_status_basic(project: str, project_dir: Path) -> None:
    """Show basic status for a single project (without config)."""
    console.print(f"\n[bold]Project: {project}[/bold]")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("File")
    table.add_column("Status")
    table.add_column("Size")
    table.add_column("Modified")

    # Check for system info - handle both local and cloud benchmarks
    system_json = project_dir / "system.json"
    system_pattern_files = list(project_dir.glob("system_*.json"))

    if system_json.exists():
        # Local benchmark - single system.json
        stat = system_json.stat()
        size = f"{stat.st_size:,} bytes"
        modified = system_json.stat().st_mtime
        table.add_row("system.json", "[green]✓[/]", size, str(modified))
    elif system_pattern_files:
        # Cloud benchmark - multiple system_*.json files
        total_size = sum(f.stat().st_size for f in system_pattern_files)
        latest_modified = max(f.stat().st_mtime for f in system_pattern_files)
        system_count = len(system_pattern_files)
        table.add_row(
            f"system_*.json ({system_count} systems)",
            "[green]✓[/]",
            f"{total_size:,} bytes",
            str(latest_modified),
        )
    else:
        # No system info found
        table.add_row("system.json", "[red]✗[/]", "-", "-")

    # Check other files
    other_files = ["runs.csv", "summary.json"]
    for filename in other_files:
        filepath = project_dir / filename
        if filepath.exists():
            stat = filepath.stat()
            size = f"{stat.st_size:,} bytes"
            modified = filepath.stat().st_mtime
            table.add_row(filename, "[green]✓[/]", size, str(modified))
        else:
            table.add_row(filename, "[red]✗[/]", "-", "-")

    console.print(table)


def show_detailed_status(
    cfg: dict[str, Any], config_file: Path, collect_report_files_fn: Any
) -> None:
    """Show detailed status for a benchmark including config information.

    Args:
        cfg: Configuration dictionary
        config_file: Path to the config file
        collect_report_files_fn: Function to collect report files from a directory
    """
    project_id = cfg.get("project_id", "unknown")
    results_dir = Path("results") / project_id

    console.print(f"\n[bold cyan]═══ {project_id} ═══[/bold cyan]")
    console.print(f"[dim]Config: {config_file}[/dim]\n")

    # Project Info
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="bold")
    info_table.add_column("Value")

    info_table.add_row("Title", cfg.get("title", "-"))
    info_table.add_row("Author", cfg.get("author", "-"))
    info_table.add_row("Environment", (cfg.get("env") or {}).get("mode", "local"))

    systems = cfg.get("systems", [])
    system_names = [s["name"] for s in systems]
    info_table.add_row("Systems", ", ".join(system_names))

    workload = cfg.get("workload", {})
    info_table.add_row(
        "Workload",
        f"{workload.get('name', '-')} (SF={workload.get('scale_factor', '-')})",
    )
    info_table.add_row(
        "Queries/Runs",
        f"{workload.get('runs_per_query', '-')} runs, {workload.get('warmup_runs', '-')} warmup",
    )

    console.print(info_table)
    console.print()

    # Check if results directory exists
    if not results_dir.exists():
        console.print("[red]No results directory found[/red]")
        console.print("[dim]Run 'benchkit setup' to begin[/dim]")
        return

    # Load phase data and run results
    phase_data = load_phase_data(results_dir, system_names)
    runs_df = load_runs_data(results_dir)
    query_stats = get_query_stats_per_system(runs_df) if runs_df is not None else {}

    # Get infrastructure IPs for availability check (cloud + managed)
    from ..common.cli_helpers import (
        get_all_infrastructure_ips,
        is_any_system_cloud_mode,
        is_any_system_managed_mode,
    )

    is_cloud = is_any_system_cloud_mode(cfg)
    is_managed = is_any_system_managed_mode(cfg)
    has_infra = is_cloud or is_managed

    # Get combined infrastructure IPs from both cloud and managed systems
    infra_ips: dict[str, Any] | None = None
    if has_infra:
        try:
            infra_ips = get_all_infrastructure_ips(cfg)
        except Exception:
            infra_ips = None

    # Phase Status Table
    phase_table = Table(
        show_header=True, header_style="bold blue", title="Phase Status by System"
    )
    phase_table.add_column("System", style="bold")
    phase_table.add_column("Setup", justify="center")
    phase_table.add_column("Load", justify="center")
    phase_table.add_column("Run", justify="center")
    if has_infra:
        phase_table.add_column("Infra", justify="center")

    # Track overall health
    has_errors = False
    all_phases_complete = True
    total_failed_queries = 0

    for system_name in system_names:
        system_phase = phase_data.get(system_name, {"setup": None, "load": None})

        # Setup status
        setup_data = system_phase.get("setup")
        if setup_data:
            timing = setup_data.get("installation_s", 0)
            setup_cell = f"[green]✓[/] {format_timing(timing)}"
        else:
            setup_cell = "[dim]-[/]"
            all_phases_complete = False

        # Load status
        load_data = system_phase.get("load")
        if load_data:
            load_timing = (
                load_data.get("data_generation_s", 0)
                + load_data.get("schema_creation_s", 0)
                + load_data.get("data_loading_s", 0)
            )
            load_cell = f"[green]✓[/] {format_timing(load_timing)}"
        else:
            load_cell = "[dim]-[/]"
            all_phases_complete = False

        # Run status
        if system_name in query_stats:
            stats = query_stats[system_name]
            total = stats["total"]
            failed = stats["failed"]
            total_failed_queries += failed

            if failed == 0:
                run_cell = f"[green]✓[/] {total} queries"
            elif failed == total:
                run_cell = f"[red]✗[/] {total} failed"
                has_errors = True
            else:
                run_cell = f"[yellow]⚠[/] {total - failed}/{total}"
                has_errors = True
        else:
            run_cell = "[dim]-[/]"
            all_phases_complete = False

        # Infrastructure availability (cloud or managed)
        if has_infra:
            _, infra_cell = check_infra_available(cfg, system_name, infra_ips)
            # Add infrastructure provisioning timing if available
            infra_timing = system_phase.get("infra_timing_s")
            if infra_timing and infra_timing > 0:
                infra_cell = infra_cell + f" {format_timing(infra_timing)}"
            phase_table.add_row(
                system_name, setup_cell, load_cell, run_cell, infra_cell
            )
        else:
            phase_table.add_row(system_name, setup_cell, load_cell, run_cell)

    console.print(phase_table)

    # Show error details (only when there are failures)
    if has_errors:
        for system_name in system_names:
            if system_name in query_stats and query_stats[system_name]["errors"]:
                errors = query_stats[system_name]["errors"]
                error_table = Table(
                    show_header=True,
                    header_style="bold red",
                    title=f"Failed Queries: {system_name}",
                )
                error_table.add_column("Query", style="bold")
                error_table.add_column("Failed", justify="center")
                error_table.add_column("Error", style="dim")

                for query, failed_count, total_count, error_msg in errors:
                    error_table.add_row(
                        query, f"{failed_count}/{total_count}", error_msg
                    )

                console.print()
                console.print(error_table)

    # Overall status line
    console.print()
    if has_errors:
        console.print(
            f"[yellow]Overall: ⚠ {total_failed_queries} query failures detected[/yellow]"
        )
    elif all_phases_complete:
        console.print("[green]Overall: ✓ All phases completed successfully[/green]")
    else:
        console.print("[dim]Overall: Some phases pending[/dim]")

    # Report status (compact)
    report_config = cfg.get("report", {})
    output_path = Path(
        report_config.get("output_path", f"results/{project_id}/reports")
    )
    report_dir = output_path.parent / output_path.stem
    report_files = collect_report_files_fn(report_dir)
    if report_files:
        console.print(f"[dim]Report: {report_files[0]}[/dim]")

    # Show infrastructure details (IPs and connection strings) for cloud and managed
    if has_infra:
        console.print()
        show_infrastructure_details(cfg, systems)


def show_infrastructure_details(
    cfg: dict[str, Any], systems: list[dict[str, Any]]
) -> None:
    """Show infrastructure details including IPs, connection strings, and SSH commands.

    This function displays a unified table for both cloud (Terraform) and
    managed (self-managed) systems.
    """
    from ..common.cli_helpers import get_all_infrastructure_ips
    from ..systems import SYSTEM_IMPLEMENTATIONS, _lazy_import_system

    try:
        # Get combined infrastructure IPs from cloud and managed systems
        infra_ips = get_all_infrastructure_ips(cfg)
        if not infra_ips:
            console.print("\n[dim]Infrastructure details not available[/dim]")
            return

        # Create infrastructure table
        infra_table = Table(
            show_header=True,
            header_style="bold magenta",
            title="Infrastructure Details",
        )
        infra_table.add_column("System", style="bold", no_wrap=True)
        infra_table.add_column("Public IP", no_wrap=True)
        infra_table.add_column("Private IP", no_wrap=True)
        infra_table.add_column("Connection String", overflow="fold")

        # Collect SSH commands for display after table
        ssh_commands: list[tuple[str, str]] = []

        for system in systems:
            system_name = system["name"]
            system_kind = system.get("kind", "")

            ips = infra_ips.get(system_name)
            if not ips:
                continue

            # Handle both single-node and multi-node formats
            if "public_ips" in ips:
                # Multi-node: show all IPs
                public_ip_list = ips["public_ips"]
                private_ip_list = ips["private_ips"]
                public_ip = ", ".join(public_ip_list)
                private_ip = ", ".join(private_ip_list)
                # Use first IP for connection string
                first_public_ip = public_ip_list[0]
                first_private_ip = private_ip_list[0]
            else:
                # Single-node
                public_ip = ips["public_ip"]
                private_ip = ips["private_ip"]
                first_public_ip = public_ip
                first_private_ip = private_ip

            # Get connection string from system class
            connection_str = "-"
            if system_kind in SYSTEM_IMPLEMENTATIONS:
                try:
                    system_class = _lazy_import_system(system_kind)
                    # Create temporary system configuration for connection string
                    system_config = {
                        "name": system_name,
                        "kind": system_kind,
                        "version": system.get("version", "unknown"),
                        "setup": system.get("setup", {}).copy(),
                    }
                    # Override host with first public IP
                    system_config["setup"]["host"] = first_public_ip

                    system_instance = system_class(system_config)
                    connection_str = system_instance.get_connection_string(
                        first_public_ip, first_private_ip
                    )
                except Exception:
                    connection_str = f"{system_kind}://{first_public_ip}"

            # Build SSH command
            ssh_command = build_ssh_command(cfg, system, ips, first_public_ip)
            if ssh_command and ssh_command != "-":
                ssh_commands.append((system_name, ssh_command))

            infra_table.add_row(system_name, public_ip, private_ip, connection_str)

        console.print(infra_table)

        # Print SSH commands separately for easy copy-paste
        if ssh_commands:
            console.print("\n[bold magenta]SSH Commands[/bold magenta]")
            for system_name, ssh_cmd in ssh_commands:
                console.print(f"  [bold]{system_name}:[/bold]")
                console.print(f"    {ssh_cmd}", soft_wrap=True)

    except Exception as e:
        console.print(
            f"[yellow]Could not retrieve infrastructure details: {e}[/yellow]"
        )


def build_ssh_command(
    cfg: dict[str, Any],
    system: dict[str, Any],
    ips: dict[str, Any],
    public_ip: str,
) -> str:
    """Build SSH command for a system.

    For managed systems, uses the SSH command stored in their deployment state.
    For cloud systems, constructs the SSH command from the environment config.

    Args:
        cfg: Full configuration dict
        system: System configuration dict
        ips: IP information dict for the system (may include ssh_command for managed)
        public_ip: The public IP to connect to

    Returns:
        SSH command string or "-" if not available
    """
    from ..common.cli_helpers import (
        get_environment_for_system,
        get_managed_deployment_dir,
        get_managed_systems,
        is_managed_system,
    )

    system_name = system["name"]

    # For managed systems, use the stored SSH command
    if is_managed_system(cfg, system_name):
        ssh_command = str(ips.get("ssh_command", ""))
        if ssh_command:
            # For managed systems, the key path may be relative to deployment dir
            # Make it copy-pasteable by making paths absolute if needed
            if " -i " in ssh_command:
                key_match = re.search(r"-i\s+([^\s]+)", ssh_command)
                if key_match:
                    key_path = key_match.group(1)
                    # Check if key is relative path
                    if not os.path.isabs(key_path) and not key_path.startswith("~"):
                        # Try to resolve from managed deployment dir
                        for managed_sys in get_managed_systems(cfg):
                            if managed_sys["name"] == system_name:
                                deployment_dir = get_managed_deployment_dir(
                                    cfg, managed_sys
                                )
                                resolved_path = os.path.join(deployment_dir, key_path)
                                if os.path.exists(resolved_path):
                                    ssh_command = ssh_command.replace(
                                        f"-i {key_path}", f"-i {resolved_path}"
                                    )
                                break
            return ssh_command
        return "-"

    # For cloud systems, construct SSH command from environment config
    _, env_config = get_environment_for_system(cfg, system_name)
    ssh_key_path = str(env_config.get("ssh_private_key_path", ""))

    if ssh_key_path:
        # Expand ~ to full path for copy-paste convenience
        expanded_path = os.path.expanduser(ssh_key_path)
        return f"ssh -i {expanded_path} ubuntu@{public_ip}"

    # No SSH key configured
    return f"ssh ubuntu@{public_ip}"


def show_configs_summary(
    config_files: list[Path], load_config_fn: Any, collect_report_files_fn: Any
) -> None:
    """Show summary table of all configs.

    Args:
        config_files: List of config file paths
        load_config_fn: Function to load config from file
        collect_report_files_fn: Function to collect report files from a directory
    """
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Project", style="bold")
    table.add_column("Systems")
    table.add_column("Workload")
    table.add_column("Probe", justify="center")
    table.add_column("Bench", justify="center")
    table.add_column("Report", justify="center")

    results_dir = Path("results")

    for config_file in config_files:
        try:
            cfg = load_config_fn(str(config_file))
            project_id = cfg.get("project_id", config_file.stem)
            project_dir = results_dir / project_id

            # System names
            systems = cfg.get("systems", [])
            system_names = ", ".join([s["name"] for s in systems])

            # Workload info
            workload = cfg.get("workload", {})
            workload_str = (
                f"{workload.get('name', '-')} SF{workload.get('scale_factor', '?')}"
            )

            # Check statuses
            has_system_json = (project_dir / "system.json").exists()
            has_system_pattern = len(list(project_dir.glob("system_*.json"))) > 0
            probe_status = (
                "[green]✓[/]"
                if (has_system_json or has_system_pattern)
                else "[red]✗[/]"
            )

            runs_csv = project_dir / "runs.csv"
            summary_json = project_dir / "summary.json"
            bench_status = (
                "[green]✓[/]"
                if (runs_csv.exists() and summary_json.exists())
                else "[red]✗[/]"
            )

            # Use output_path from config
            report_config = cfg.get("report", {})
            output_path = Path(
                report_config.get("output_path", f"results/{project_id}/reports")
            )
            report_dir = output_path.parent / output_path.stem
            report_files = collect_report_files_fn(report_dir)
            report_status = "[green]✓[/]" if report_files else "[red]✗[/]"

            table.add_row(
                project_id,
                system_names,
                workload_str,
                probe_status,
                bench_status,
                report_status,
            )

        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not load {config_file}: {e}[/yellow]"
            )

    console.print(table)


def show_all_projects(
    results_dir: Path, load_config_fn: Any, collect_report_files_fn: Any
) -> None:
    """Show overview of all projects.

    Args:
        results_dir: Directory containing project results
        load_config_fn: Function to load config from file
        collect_report_files_fn: Function to collect report files from a directory
    """
    if not results_dir.exists():
        console.print(
            "[yellow]No results directory found. Run 'benchkit probe' first.[/]"
        )
        return

    projects = [d for d in results_dir.iterdir() if d.is_dir()]

    if not projects:
        console.print("[yellow]No benchmark projects found.[/]")
        return

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Project")
    table.add_column("System Info")
    table.add_column("Benchmark Data")
    table.add_column("Report")

    for project_dir in sorted(projects):
        project_name = project_dir.name

        # Check for system info - handle both local (system.json) and cloud (system_*.json) benchmarks
        has_system_json = (project_dir / "system.json").exists()
        has_system_pattern = len(list(project_dir.glob("system_*.json"))) > 0
        system_status = (
            "[green]✓[/]" if (has_system_json or has_system_pattern) else "[red]✗[/]"
        )

        runs_status = (
            "[green]✓[/]" if (project_dir / "runs.csv").exists() else "[red]✗[/]"
        )

        # Check if report exists using default output_path pattern
        # Try to find config to get actual output_path, otherwise use default
        config_file = Path("configs") / f"{project_name}.yaml"
        if config_file.exists():
            try:
                cfg = load_config_fn(str(config_file))
                report_config = cfg.get("report", {})
                output_path = Path(
                    report_config.get("output_path", f"results/{project_name}/reports")
                )
                report_dir = output_path.parent / output_path.stem
                report_files = collect_report_files_fn(report_dir)
                report_status = "[green]✓[/]" if report_files else "[red]✗[/]"
            except Exception:
                # Fallback to checking default location
                report_dir = Path("results") / project_name / "reports"
                report_files = collect_report_files_fn(report_dir)
                report_status = "[green]✓[/]" if report_files else "[red]✗[/]"
        else:
            # No config found, check default location
            report_dir = Path("results") / project_name / "reports"
            report_files = collect_report_files_fn(report_dir)
            report_status = "[green]✓[/]" if report_files else "[red]✗[/]"

        table.add_row(project_name, system_status, runs_status, report_status)

    console.print(table)
