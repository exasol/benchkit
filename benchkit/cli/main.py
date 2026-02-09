"""Command line interface for the benchmark framework."""

import copy
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

# Load .env file if it exists - this must be done early before other imports
try:
    from dotenv import find_dotenv, load_dotenv

    # Use usecwd=True so that the .env search starts from the user's current
    # working directory rather than from this installed module's location in
    # site-packages (the default frame-based resolution).
    load_dotenv(find_dotenv(usecwd=True), override=True)
except ImportError:
    pass  # python-dotenv not installed, continue without .env support

from ..config import load_config
from ..debug import set_debug
from ..gather.system_probe import probe_all
from ..infra.manager import InfraManager
from ..infra.self_managed import SelfManagedDeployment, get_self_managed_deployment
from ..package.creator import create_workload_zip
from ..report.render import render_global_report_index, render_report
from ..run.runner import run_benchmark

# Import from refactored modules
from .probing import probe_managed_systems, probe_remote_systems
from .status import (
    show_all_projects,
    show_configs_summary,
    show_detailed_status,
    show_project_status_basic,
)
from .workflows import report_query_results, run_probe_for_full, run_report_for_full

app = typer.Typer(
    name="benchkit",
    help="Database benchmark framework for generating reproducible reports",
    no_args_is_help=True,
)

console = Console()


@app.command()
def probe(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to probe"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed command tracing"
    ),
) -> None:
    """Probe system information and save to results directory."""

    # Set global debug state
    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Filter systems if --systems parameter is provided
    if systems:
        requested_systems = [s.strip() for s in systems.split(",")]
        original_count = len(cfg.get("systems", []))
        cfg["systems"] = [
            s for s in cfg.get("systems", []) if s["name"] in requested_systems
        ]
        if not cfg["systems"]:
            console.print(
                f"[red]No matching systems found. Available: {[s['name'] for s in cfg.get('systems', [])]}[/red]"
            )
            raise typer.Exit(1)
        console.print(
            f"[blue]Probing {len(cfg['systems'])} of {original_count} systems: {', '.join(requested_systems)}[/blue]"
        )

    console.print(f"[blue]Probing system info for project:[/] {cfg['project_id']}")

    # Check if this is a cloud or managed benchmark
    from ..common.cli_helpers import (
        is_any_system_cloud_mode,
        is_any_system_managed_mode,
    )

    has_cloud = is_any_system_cloud_mode(cfg)
    has_managed = is_any_system_managed_mode(cfg)

    any_success = True

    if has_cloud:
        console.print("[blue]Cloud benchmark detected - probing remote instances...[/]")
        success = probe_remote_systems(cfg, outdir)
        if success:
            console.print("[green]✓ Cloud system probes completed[/]")
        else:
            console.print("[red]✗ Some cloud system probes failed[/]")
            any_success = False

    if has_managed:
        console.print(
            "[blue]Managed systems detected - probing managed deployments...[/]"
        )
        success = probe_managed_systems(cfg, outdir)
        if success:
            console.print("[green]✓ Managed system probes completed[/]")
        else:
            console.print("[red]✗ Some managed system probes failed[/]")
            any_success = False

    if not has_cloud and not has_managed:
        # Local benchmark - probe current system
        meta = probe_all(outdir)
        console.print(f"[green]✓ System probe saved to:[/] {outdir / 'system.json'}")
        console.print(
            f"[dim]Found {meta['cpu_count_logical']} logical CPUs, "
            f"{meta['memory_total_gb']}GB RAM[/]"
        )

    if (has_cloud or has_managed) and not any_success:
        raise typer.Exit(1)


@app.command()
def setup(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to setup"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reinstall even if already installed"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed command tracing"
    ),
) -> None:
    """Set up and install database systems.

    This is Phase 1 of the benchmark workflow. It handles:
    - Cloud infrastructure provisioning (if cloud mode)
    - Storage preparation (disk partitioning, RAID setup)
    - Database system installation and configuration

    After setup completes, use 'benchkit load' to load data.
    """
    from ..run.runner import BenchmarkRunner

    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Override config with CLI options
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]

    console.print(f"[blue]Setting up systems for project:[/] {cfg['project_id']}")
    console.print(f"[dim]Systems: {[s['name'] for s in cfg['systems']]}[/]")

    runner = BenchmarkRunner(cfg, outdir, debug=debug)
    success = runner.run_setup(force=force)

    if success:
        console.print("[green]✓ Setup phase completed successfully[/]")
    else:
        console.print("[red]✗ Setup phase failed[/]")
        raise typer.Exit(1)


@app.command()
def load(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to load data into"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force reload even if data already loaded"
    ),
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Execute locally against remote databases (skip package deployment)",
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed command tracing"
    ),
) -> None:
    """Load benchmark data into configured systems.

    This is Phase 2 of the benchmark workflow. It handles:
    - Data generation (TPC-H data files)
    - Schema creation (tables, indexes)
    - Data loading (bulk insert)

    Requires setup phase to be completed first.
    After load completes, use 'benchkit run' to execute queries.

    Use --local to execute data loading from your local machine directly
    against remote databases (using their public IPs). This is useful for
    faster iteration during workload development and debugging.
    """
    from ..run.runner import BenchmarkRunner

    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Override config with CLI options
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]

    if local:
        console.print("[cyan]Mode: Local-to-remote (connecting to remote DBs)[/]")

    runner = BenchmarkRunner(cfg, outdir, debug=debug)
    success = runner.run_load(force=force, local=local)

    if success:
        console.print("[green]✓ Load phase completed successfully[/]")
    else:
        console.print("[red]✗ Load phase failed[/]")
        raise typer.Exit(1)


@app.command()
def run(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to run"
    ),
    queries: str | None = typer.Option(
        None, "--queries", help="Comma-separated list of queries to run"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force run even if results already exist"
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Run complete workflow (probe + setup + load + run + report)",
    ),
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Execute locally against remote databases (skip package deployment)",
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed command tracing"
    ),
) -> None:
    """Execute benchmark queries against configured systems.

    This is Phase 3 of the benchmark workflow (query execution only).
    Requires setup and load phases to be completed first.

    Use --full flag to run the complete workflow (probe + setup + load + run + report).

    Use --local to execute queries from your local machine directly
    against remote databases (using their public IPs). This is useful for
    faster iteration during workload development and debugging.
    """
    from ..run.runner import BenchmarkRunner

    set_debug(debug)

    cfg = load_config(config)
    # Save original config before CLI overrides for report generation
    # Reports should reflect all data in runs.csv, not just filtered systems
    original_cfg = copy.deepcopy(cfg)

    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Override config with CLI options
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]

    if queries:
        query_names = [q.strip() for q in queries.split(",")]
        cfg["workload"]["queries"]["include"] = query_names

    console.print(f"[blue]Running benchmark for project:[/] {cfg['project_id']}")
    console.print(f"[dim]Systems: {[s['name'] for s in cfg['systems']]}[/]")
    console.print(
        f"[dim]Workload: {cfg['workload']['name']} (SF={cfg['workload']['scale_factor']})[/]"
    )
    if local:
        console.print("[cyan]Mode: Local-to-remote (connecting to remote DBs)[/]")

    runner = BenchmarkRunner(cfg, outdir, debug=debug)

    if full:
        # Check if sequential mode is enabled
        exec_config = cfg.get("execution", {})
        is_sequential = exec_config.get("sequential", False)
        is_parallel = exec_config.get("parallel", False)

        if is_sequential and is_parallel:
            # Parallel sequential mode: complete lifecycle per system, in parallel
            # Each system runs independently: provision → benchmark → destroy
            console.print(
                "[bold blue]Running parallel sequential benchmark workflow[/bold blue]"
            )
            console.print("[dim]Each system runs full lifecycle in parallel[/dim]\n")

            if not runner.run_parallel_sequential(
                run_probe_fn=run_probe_for_full,
                run_report_fn=run_report_for_full,
            ):
                raise typer.Exit(1)

        elif is_sequential:
            # Sequential mode: complete lifecycle per system
            # Each system: provision → probe → setup → load → queries → destroy
            console.print(
                "[bold blue]Running sequential benchmark workflow[/bold blue]"
            )
            console.print("[dim]Each system: provision → benchmark → destroy[/dim]\n")

            if not runner.run_sequential(
                run_probe_fn=run_probe_for_full,
                run_report_fn=run_report_for_full,
            ):
                raise typer.Exit(1)
        else:
            # Standard mode: all infrastructure provisioned upfront
            # Run all phases: [infra] -> probe -> setup -> load -> run -> report
            console.print("[bold blue]Running full benchmark workflow[/bold blue]")
            console.print()

            # Import helpers for detecting cloud/managed modes
            from ..common.cli_helpers import (
                is_any_system_cloud_mode,
                is_any_system_managed_mode,
            )

            has_cloud = is_any_system_cloud_mode(cfg)
            has_managed = is_any_system_managed_mode(cfg)

            # Phase 0: Infrastructure Provisioning (cloud + managed)
            # This must happen BEFORE probe so terraform/managed state exists
            if has_cloud or has_managed:
                console.print("[bold]Phase 0: Infrastructure Provisioning[/bold]")

                # Cloud systems: Terraform provisioning
                if has_cloud:
                    console.print("[blue]Provisioning cloud infrastructure...[/]")
                    if not runner.ensure_cloud_infrastructure():
                        console.print(
                            "[red]✗ Cloud infrastructure provisioning failed[/]"
                        )
                        raise typer.Exit(1)
                    console.print("[green]✓ Cloud infrastructure ready[/]")

                # Managed systems: Self-managed deployments (like Exasol PE)
                if has_managed:
                    console.print("[blue]Deploying managed systems...[/]")
                    if not _apply_managed_systems(cfg):
                        console.print("[red]✗ Managed systems deployment failed[/]")
                        raise typer.Exit(1)
                    console.print("[green]✓ Managed systems ready[/]")

                console.print()

            # Phase 1: Probe (now infrastructure exists for both cloud + managed)
            console.print("[bold]Phase 1: System Probe[/bold]")
            run_probe_for_full(cfg, outdir)
            console.print()

            # Phase 2: Setup (infra already provisioned, just install/configure DB)
            console.print("[bold]Phase 2: Setup[/bold]")
            if not runner.run_setup(force=force):
                console.print("[red]✗ Setup phase failed[/]")
                raise typer.Exit(1)
            console.print()

            # Phase 3: Load
            console.print("[bold]Phase 3: Load[/bold]")
            if not runner.run_load(force=force, local=local):
                console.print("[red]✗ Load phase failed[/]")
                raise typer.Exit(1)
            console.print()

            # Phase 4: Queries
            console.print("[bold]Phase 4: Query Execution[/bold]")
            if not runner.run_queries(force=force, local=local):
                console.print("[red]✗ Query execution failed[/]")
                raise typer.Exit(1)

            # Phase 5: Report
            console.print()
            console.print("[bold]Phase 5: Report Generation[/bold]")
            # Use original config so report includes all systems from runs.csv
            run_report_for_full(original_cfg, _collect_report_files)
    else:
        # Run queries only (strict mode - check prerequisites)
        if not runner.run_queries(force=force, local=local):
            raise typer.Exit(1)

    # Check for query errors in results and report them
    runs_file = outdir / "runs.csv"
    all_queries_passed = True
    if runs_file.exists():
        all_queries_passed = report_query_results(runs_file)

    if all_queries_passed:
        console.print(f"\n[green]✓ Benchmark completed successfully:[/] {runs_file}")
    else:
        console.print(
            f"\n[yellow]⚠ Benchmark completed with some query failures:[/] {runs_file}"
        )


@app.command()
def execute(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    system: str = typer.Option(
        ..., "--system", help="System to execute workload against"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed command tracing"
    ),
) -> None:
    """Execute workload against a specific system (for remote packages)."""

    # Set global debug state
    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Filter config to only include the specified system
    system_configs = [s for s in cfg["systems"] if s["name"] == system]
    if not system_configs:
        console.print(f"[red]System '{system}' not found in configuration[/red]")
        raise typer.Exit(1)

    cfg["systems"] = system_configs

    console.print(f"[blue]Executing workload for system:[/] {system}")
    run_benchmark(cfg, outdir)


@app.command()
def report(
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config YAML file",
        envvar="BENCHKIT_CONFIG",
    ),
    index_dir: str = typer.Option(
        "results",
        "--index-dir",
        help="Directory containing project reports for global index regeneration",
    ),
) -> None:
    """Generate report from benchmark results or rebuild the report index."""

    if config is None:
        index_path = Path(index_dir)
        console.print(
            f"[blue]Regenerating global report index in directory:[/] {index_path}"
        )
        index_file = render_global_report_index(index_path)
        console.print(f"[green]✓ Report index updated:[/] {index_file}")
        return

    cfg = load_config(config)

    console.print(f"[blue]Generating report for project:[/] {cfg['project_id']}")
    actual_output_path = render_report(cfg)

    console.print(f"[green]✓ Report generated:[/] {actual_output_path}")
    report_files = _collect_report_files(actual_output_path)
    if report_files:
        primary_report = report_files[0]
        console.print(f"[dim]Report available at:[/] {primary_report}")
        if len(report_files) > 1:
            console.print(
                f"[dim]Additional report variants:[/] {len(report_files) - 1}"
            )
    else:
        console.print(
            "[yellow]Warning: No REPORT.md files detected in generated report directory[/yellow]"
        )

    primary_package = (
        actual_output_path / "3-full" / f"{cfg['project_id']}-workload.zip"
    )
    if primary_package.exists():
        console.print(f"[dim]Benchmark package:[/] {primary_package}")


@app.command()
def status(
    config: list[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Config file(s) to check status for",
        envvar="BENCHKIT_CONFIG",
    ),
    project: str | None = typer.Option(
        None, "--project", "-p", help="Project ID to check (auto-finds config)"
    ),
) -> None:
    """Show status of benchmark projects from configs."""
    configs_dir = Path("configs")
    results_dir = Path("results")

    if project:
        # Find config for this project
        config_file = _find_config_for_project(project, configs_dir)
        if config_file:
            cfg = load_config(str(config_file))
            show_detailed_status(cfg, config_file, _collect_report_files)
        else:
            # Fallback to basic status if no config found
            console.print(
                f"[yellow]No config found for project {project}, showing basic status[/yellow]"
            )
            project_dir = results_dir / project
            if not project_dir.exists():
                console.print(f"[red]Project not found:[/] {project}")
                raise typer.Exit(1)
            show_project_status_basic(project, project_dir)
    elif config:
        # Show status for specific config(s)
        for config_path in config:
            cfg = load_config(config_path)
            show_detailed_status(cfg, Path(config_path), _collect_report_files)
            console.print()  # Empty line between configs
    else:
        # Show status for all configs in configs directory
        if not configs_dir.exists():
            console.print(
                "[yellow]No configs directory found. Showing all projects in results.[/]"
            )
            show_all_projects(results_dir, load_config, _collect_report_files)
            return

        config_files = sorted(configs_dir.glob("*.yaml"))
        if not config_files:
            console.print("[yellow]No config files found in configs directory.[/]")
            return

        console.print("[bold blue]Benchmark Status Summary[/bold blue]\n")
        show_configs_summary(config_files, load_config, _collect_report_files)


def _dump_config_yaml(cfg: dict[str, Any], config_path: Path | str) -> None:
    """Dump configuration as commented YAML to stdout.

    Outputs a fully expanded configuration with all defaults filled in,
    along with comments explaining each section and marking default values.
    The output is pure YAML suitable for redirection to a file.
    """
    # Define known default values for marking
    DEFAULTS = {
        # WorkloadConfig defaults
        "workload.queries": {"include": []},
        "workload.runs_per_query": 3,
        "workload.warmup_runs": 1,
        "workload.data_format": "csv",
        "workload.generator": "dbgen",
        "workload.variant": "official",
        "workload.system_variants": None,
        "workload.multiuser": None,
        # EnvironmentConfig defaults
        "env.mode": "local",
        "env.region": None,
        "env.instances": None,
        "env.os_image": None,
        "env.ssh_key_name": None,
        "env.ssh_private_key_path": None,
        "env.allow_external_database_access": False,
        # ReportConfig defaults
        "report.generate_index": True,
        "report.show_boxplots": True,
        "report.show_latency_cdf": False,
        "report.show_heatmap": True,
        "report.show_bar_chart": True,
        # ExecutionConfig defaults
        "execution.parallel": False,
        "execution.max_workers": None,
        "execution.sequential": False,
        "execution.continue_on_failure": False,
        # BenchmarkConfig defaults
        "metrics": {},
    }

    def is_default(path: str, value: Any) -> bool:
        """Check if a value matches its default."""
        if path in DEFAULTS:
            return bool(value == DEFAULTS[path])
        return False

    def format_value(value: Any, indent: int = 0) -> str:
        """Format a value for YAML output."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            # Quote strings that might be ambiguous
            if value == "" or value in ("true", "false", "null", "yes", "no"):
                return f'"{value}"'
            # Quote strings with special characters
            if any(c in value for c in ":#{}[]&*!|>'\"%@`"):
                return f'"{value}"'
            return value
        if isinstance(value, int | float):
            return str(value)
        if isinstance(value, dict):
            # Format nested dicts as inline YAML
            if not value:
                return "{}"
            items = [f"{k}: {format_value(v)}" for k, v in value.items()]
            return "{" + ", ".join(items) + "}"
        if isinstance(value, list):
            # Format lists as inline YAML
            if not value:
                return "[]"
            items = [format_value(v) for v in value]
            return "[" + ", ".join(items) + "]"
        return str(value)

    def print_yaml_value(
        key: str, value: Any, indent: int = 0, comment: str = ""
    ) -> None:
        """Print a YAML key-value pair with optional comment."""
        prefix = "  " * indent
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            for k, v in value.items():
                print_yaml_value(k, v, indent + 1)
        elif isinstance(value, list):
            if not value:
                suffix = f"  # {comment}" if comment else ""
                print(f"{prefix}{key}: []{suffix}")
            else:
                print(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        # First item of dict gets the dash
                        items = list(item.items())
                        if items:
                            k, v = items[0]
                            if isinstance(v, dict):
                                print(f"{prefix}  - {k}:")
                                for kk, vv in v.items():
                                    print_yaml_value(kk, vv, indent + 3)
                            else:
                                print(f"{prefix}  - {k}: {format_value(v)}")
                            for k, v in items[1:]:
                                print_yaml_value(k, v, indent + 2)
                    else:
                        print(f"{prefix}  - {format_value(item)}")
        else:
            suffix = f"  # {comment}" if comment else ""
            print(f"{prefix}{key}: {format_value(value)}{suffix}")

    # Output header
    print("# Benchkit Configuration (expanded with defaults)")
    print(f"# Generated from: {config_path}")
    print("#")
    print("# This file shows all configuration options with their current values.")
    print("# Options marked [DEFAULT] were not specified and use default values.")
    print()

    # === Project Section ===
    print("# === Project ===")
    project_id = cfg.get("project_id", "")
    print(
        f"project_id: {format_value(project_id)}  # Derived from filename if not specified"
    )
    print()
    print(f"title: {format_value(cfg.get('title', ''))}")
    print(f"author: {format_value(cfg.get('author', ''))}")
    print()

    # === Environment Section ===
    print("# === Environment ===")
    print("# mode: local | aws | gcp | azure")
    env = cfg.get("env") or {}
    print("env:")

    mode = env.get("mode", "local")
    mode_comment = "[DEFAULT]" if is_default("env.mode", mode) else ""
    print(
        f"  mode: {format_value(mode)}  # Execution environment {mode_comment}".rstrip()
    )

    region = env.get("region")
    if region:
        print(f"  region: {format_value(region)}")
    else:
        print("  # region: null  # [DEFAULT] Only needed for cloud modes")

    ssh_key = env.get("ssh_key_name")
    if ssh_key:
        print(f"  ssh_key_name: {format_value(ssh_key)}")

    ssh_path = env.get("ssh_private_key_path")
    if ssh_path:
        print(f"  ssh_private_key_path: {format_value(ssh_path)}")

    ext_access = env.get("allow_external_database_access", False)
    if is_default("env.allow_external_database_access", ext_access):
        print(
            f"  allow_external_database_access: {format_value(ext_access)}  # [DEFAULT]"
        )
    else:
        print(f"  allow_external_database_access: {format_value(ext_access)}")

    instances = env.get("instances")
    if instances:
        print("  instances:")
        for inst_name, inst_cfg in instances.items():
            print(f"    {inst_name}:")
            for k, v in inst_cfg.items():
                print(f"      {k}: {format_value(v)}")
    print()

    # === Systems Section ===
    print("# === Systems ===")
    print("# Each system defines a database to benchmark")
    print("systems:")
    for system in cfg.get("systems", []):
        print(f"  - name: {format_value(system.get('name', ''))}")
        print(f"    kind: {format_value(system.get('kind', ''))}")
        print(f"    version: {format_value(system.get('version', ''))}")
        print("    setup:")
        setup = system.get("setup", {})
        for k, v in setup.items():
            # Mask passwords in output
            if "password" in k.lower():
                print(f'      {k}: "********"')
            else:
                print(f"      {k}: {format_value(v)}")
        print()

    # === Workload Section ===
    print("# === Workload ===")
    print("# Configuration for benchmark execution")
    workload = cfg.get("workload", {})
    print("workload:")
    print(f"  name: {format_value(workload.get('name', ''))}")
    print(
        f"  scale_factor: {workload.get('scale_factor', 1)}  # Data size in GB for TPC-H"
    )

    queries = workload.get("queries", {"include": []})
    queries_comment = (
        "[DEFAULT] All queries" if is_default("workload.queries", queries) else ""
    )
    print("  queries:")
    include = queries.get("include", [])
    exclude = queries.get("exclude", [])
    if include:
        print(f"    include: {include}")
    else:
        print(f"    include: []  # {queries_comment}".rstrip())
    if exclude:
        print(f"    exclude: {exclude}")

    runs = workload.get("runs_per_query", 3)
    runs_comment = "[DEFAULT]" if is_default("workload.runs_per_query", runs) else ""
    print(
        f"  runs_per_query: {runs}  # Number of timed runs per query {runs_comment}".rstrip()
    )

    warmup = workload.get("warmup_runs", 1)
    warmup_comment = "[DEFAULT]" if is_default("workload.warmup_runs", warmup) else ""
    print(
        f"  warmup_runs: {warmup}  # Warmup queries before measurement {warmup_comment}".rstrip()
    )

    data_fmt = workload.get("data_format", "csv")
    fmt_comment = "[DEFAULT]" if is_default("workload.data_format", data_fmt) else ""
    print(
        f"  data_format: {format_value(data_fmt)}  # csv | parquet {fmt_comment}".rstrip()
    )

    generator = workload.get("generator", "dbgen")
    gen_comment = "[DEFAULT]" if is_default("workload.generator", generator) else ""
    print(
        f"  generator: {format_value(generator)}  # Data generator {gen_comment}".rstrip()
    )

    variant = workload.get("variant", "official")
    var_comment = "[DEFAULT]" if is_default("workload.variant", variant) else ""
    print(
        f"  variant: {format_value(variant)}  # Query variant: official | tuned | custom {var_comment}".rstrip()
    )

    sys_variants = workload.get("system_variants")
    if sys_variants:
        print("  system_variants:")
        for sys_name, var_name in sys_variants.items():
            print(f"    {sys_name}: {format_value(var_name)}")
    else:
        print("  # system_variants: null  # [DEFAULT] Per-system variant overrides")

    multiuser = workload.get("multiuser")
    if multiuser:
        print("  multiuser:")
        for k, v in multiuser.items():
            print(f"    {k}: {format_value(v)}")
    else:
        print("  # multiuser: null  # [DEFAULT] Multiuser/concurrent execution config")
    print()

    # === Execution Section ===
    print("# === Execution ===")
    print("# Execution mode settings")
    execution = cfg.get("execution", {})
    print("execution:")

    parallel = execution.get("parallel", False)
    parallel_comment = "[DEFAULT]" if is_default("execution.parallel", parallel) else ""
    print(
        f"  parallel: {format_value(parallel)}  # Enable parallel system setup {parallel_comment}".rstrip()
    )

    max_workers = execution.get("max_workers")
    if max_workers:
        print(f"  max_workers: {max_workers}")
    else:
        print("  # max_workers: null  # [DEFAULT] Uses number of systems")

    sequential = execution.get("sequential", False)
    sequential_comment = (
        "[DEFAULT]" if is_default("execution.sequential", sequential) else ""
    )
    print(
        f"  sequential: {format_value(sequential)}  # Per-system lifecycle mode {sequential_comment}".rstrip()
    )

    continue_on_failure = execution.get("continue_on_failure", False)
    cof_comment = (
        "[DEFAULT]"
        if is_default("execution.continue_on_failure", continue_on_failure)
        else ""
    )
    print(
        f"  continue_on_failure: {format_value(continue_on_failure)}  # Continue if system fails {cof_comment}".rstrip()
    )
    print()

    # === Report Section ===
    print("# === Report ===")
    report = cfg.get("report", {})
    print("report:")

    output_path = report.get("output_path", "")
    print(f"  output_path: {format_value(output_path)}  # Derived from project_id")

    figures_dir = report.get("figures_dir", "")
    print(f"  figures_dir: {format_value(figures_dir)}  # Derived from project_id")

    index_dir = report.get("index_output_dir", "results")
    print(f"  index_output_dir: {format_value(index_dir)}")

    gen_index = report.get("generate_index", True)
    if is_default("report.generate_index", gen_index):
        print(f"  generate_index: {format_value(gen_index)}  # [DEFAULT]")
    else:
        print(f"  generate_index: {format_value(gen_index)}")

    boxplots = report.get("show_boxplots", True)
    if is_default("report.show_boxplots", boxplots):
        print(f"  show_boxplots: {format_value(boxplots)}  # [DEFAULT]")
    else:
        print(f"  show_boxplots: {format_value(boxplots)}")

    cdf = report.get("show_latency_cdf", False)
    if is_default("report.show_latency_cdf", cdf):
        print(f"  show_latency_cdf: {format_value(cdf)}  # [DEFAULT]")
    else:
        print(f"  show_latency_cdf: {format_value(cdf)}")

    heatmap = report.get("show_heatmap", True)
    if is_default("report.show_heatmap", heatmap):
        print(f"  show_heatmap: {format_value(heatmap)}  # [DEFAULT]")
    else:
        print(f"  show_heatmap: {format_value(heatmap)}")

    bar = report.get("show_bar_chart", True)
    if is_default("report.show_bar_chart", bar):
        print(f"  show_bar_chart: {format_value(bar)}  # [DEFAULT]")
    else:
        print(f"  show_bar_chart: {format_value(bar)}")

    # === Metrics Section ===
    metrics = cfg.get("metrics", {})
    if metrics:
        print()
        print("# === Metrics ===")
        print("# Custom metrics configuration")
        print("metrics:")
        for k, v in metrics.items():
            print_yaml_value(k, v, indent=1)


@app.command()
def check(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show all configuration details"
    ),
    dump: bool = typer.Option(
        False,
        "--dump",
        "-d",
        help="Dump full config with defaults as YAML (for redirection)",
    ),
    skip_aws_check: bool = typer.Option(
        False,
        "--skip-aws-check",
        help="Skip AWS API validation (for offline validation)",
    ),
) -> None:
    """Check and display configuration file contents.

    With --dump, outputs the expanded configuration as commented YAML that can be
    redirected to a file. This shows all default values that were auto-filled.

    For cloud modes (aws/gcp/azure), validates SSH key configuration including:
    - File existence and permissions
    - AWS key pair existence and fingerprint match (unless --skip-aws-check)
    """
    from pathlib import Path

    from rich.panel import Panel
    from rich.text import Text

    config_path = Path(config)

    # Try to load and validate the config
    validation_errors: list[str] = []
    cfg: dict[str, Any] | None = None

    try:
        cfg = load_config(config)
    except FileNotFoundError as e:
        console.print(
            Panel(
                f"[red]Configuration file not found:[/red] {config_path}",
                title="Configuration Check",
                border_style="red",
            )
        )
        raise typer.Exit(1) from e
    except ValueError as e:
        # Parse validation errors from the exception
        error_msg = str(e)
        validation_errors.append(error_msg)
    except Exception as e:
        validation_errors.append(f"Unexpected error: {e}")

    # Display header with validation status
    if validation_errors:
        status_text = Text()
        status_text.append("Configuration: ", style="bold")
        status_text.append(str(config_path), style="cyan")
        status_text.append("\nStatus: ", style="bold")
        status_text.append("✗ Invalid", style="red bold")
        console.print(Panel(status_text, border_style="red"))

        console.print("\n[red bold]Errors found:[/red bold]")
        for i, error in enumerate(validation_errors, 1):
            # Clean up the error message
            error = error.replace("Invalid configuration: ", "")
            console.print(f"  {i}. {error}")

        raise typer.Exit(1)

    if cfg is None:
        raise typer.Exit(1)

    # If dump requested, output YAML and exit (no rich formatting)
    if dump:
        _dump_config_yaml(cfg, config_path)
        return

    # Config is valid - display it with rich formatting
    status_text = Text()
    status_text.append("Configuration: ", style="bold")
    status_text.append(str(config_path), style="cyan")
    status_text.append("\nStatus: ", style="bold")
    status_text.append("✓ Valid", style="green bold")
    console.print(Panel(status_text, border_style="green"))

    # Display Project section
    project_table = Table(show_header=False, box=None, padding=(0, 2))
    project_table.add_column("Key", style="bold")
    project_table.add_column("Value")
    project_table.add_row("ID", cfg.get("project_id", "-"))
    project_table.add_row("Title", cfg.get("title", "-"))
    project_table.add_row("Author", cfg.get("author", "-"))
    console.print(Panel(project_table, title="Project", border_style="blue"))

    # Display Environment section
    env = cfg.get("env") or {}
    environments = cfg.get("environments") or {}
    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column("Key", style="bold")
    env_table.add_column("Value")

    if environments:
        # New format: show each named environment
        for env_name, env_cfg in environments.items():
            mode = env_cfg.get("mode", "local")
            instance_type = env_cfg.get("instance_type", "")
            region = env_cfg.get("region", "")
            details = []
            if region:
                details.append(region)
            if instance_type:
                details.append(instance_type)
            value = mode
            if details:
                value += f" ({', '.join(details)})"
            env_table.add_row(env_name, value)
        panel_title = "Environments"
    else:
        # Legacy format
        env_table.add_row("Mode", env.get("mode", "local"))
        if env.get("region"):
            env_table.add_row("Region", env.get("region"))
        env_table.add_row(
            "External DB Access",
            "Yes" if env.get("allow_external_database_access") else "No",
        )
        if env.get("ssh_key_name"):
            env_table.add_row("SSH Key", env.get("ssh_key_name"))
        panel_title = "Environment"

    console.print(Panel(env_table, title=panel_title, border_style="blue"))

    # Display Systems section
    systems = cfg.get("systems", [])
    instances = env.get("instances", {}) or {}

    # Collect all system names for IP variable validation display
    system_names_upper = {s["name"].upper() for s in systems}

    systems_content = []
    for i, system in enumerate(systems, 1):
        name = system.get("name", "unnamed")
        kind = system.get("kind", "unknown")
        version = system.get("version", "unknown")
        setup = system.get("setup", {})
        method = setup.get("method", "default")
        node_count = setup.get("node_count", 1)

        system_lines = [
            f"[bold cyan]{i}. {name}[/bold cyan]",
            f"   Kind:     {kind}",
            f"   Version:  {version}",
            f"   Method:   {method}",
        ]

        # Node count
        node_desc = "single-node" if node_count == 1 else f"{node_count}-node cluster"
        system_lines.append(f"   Nodes:    {node_count} ({node_desc})")

        # Instance type if available
        instance_config = instances.get(name, {})
        if instance_config.get("instance_type"):
            system_lines.append(f"   Instance: {instance_config.get('instance_type')}")

        # IP variables
        ip_vars = []
        ip_fields = ["host", "host_addrs", "host_external_addrs"]
        for field in ip_fields:
            value = setup.get(field, "")
            if isinstance(value, str) and value.startswith("$"):
                ip_vars.append(value)

        if ip_vars:
            # Check if IP vars are valid
            all_valid = True
            for var in ip_vars:
                var_name = var[1:]  # Remove $
                import re

                match = re.match(r"^([A-Z_][A-Z0-9_]*)_(PRIVATE|PUBLIC)_IP$", var_name)
                if match and match.group(1) not in system_names_upper:
                    all_valid = False
                    break

            status = "[green]✓[/green]" if all_valid else "[red]✗[/red]"
            system_lines.append(f"   IP Vars:  {', '.join(ip_vars)} {status}")

        # Verbose mode: show all setup params
        if verbose:
            system_lines.append("   [dim]Setup:[/dim]")
            for key, value in setup.items():
                if key not in ["method", "node_count"]:
                    # Mask passwords
                    if "password" in key.lower():
                        value = "********"
                    system_lines.append(f"      {key}: {value}")

        systems_content.append("\n".join(system_lines))

    console.print(
        Panel(
            "\n\n".join(systems_content),
            title=f"Systems ({len(systems)})",
            border_style="blue",
        )
    )

    # Display Workload section
    workload = cfg.get("workload", {})
    workload_table = Table(show_header=False, box=None, padding=(0, 2))
    workload_table.add_column("Key", style="bold")
    workload_table.add_column("Value")
    workload_table.add_row("Name", workload.get("name", "-"))
    sf = workload.get("scale_factor", 1)
    workload_table.add_row("Scale Factor", f"{sf} ({sf} GB for TPC-H)")
    workload_table.add_row("Data Format", workload.get("data_format", "csv"))
    workload_table.add_row("Runs/Query", str(workload.get("runs_per_query", 3)))
    workload_table.add_row("Warmup Runs", str(workload.get("warmup_runs", 1)))

    # Query info
    queries = workload.get("queries", {})
    include = queries.get("include", [])
    exclude = queries.get("exclude", [])
    if include:
        workload_table.add_row("Queries", f"Include: {', '.join(include)}")
    elif exclude:
        workload_table.add_row("Queries", f"All except: {', '.join(exclude)}")
    else:
        workload_table.add_row("Queries", "All (22 queries for TPC-H)")

    # Multiuser
    multiuser = workload.get("multiuser")
    if multiuser and multiuser.get("enabled", True):
        num_streams = multiuser.get("num_streams", 1)
        randomize = multiuser.get("randomize", False)
        random_seed = multiuser.get("random_seed", "-")
        workload_table.add_row(
            "Multiuser",
            f"{num_streams} streams, randomize: {randomize}, seed: {random_seed}",
        )

    console.print(Panel(workload_table, title="Workload", border_style="blue"))

    # Display Execution section
    execution = cfg.get("execution", {})
    if execution.get("parallel"):
        exec_table = Table(show_header=False, box=None, padding=(0, 2))
        exec_table.add_column("Key", style="bold")
        exec_table.add_column("Value")
        exec_table.add_row("Parallel", "Yes")
        if execution.get("max_workers"):
            exec_table.add_row("Max Workers", str(execution.get("max_workers")))
        console.print(Panel(exec_table, title="Execution", border_style="blue"))

    # Display Report section
    report = cfg.get("report", {})
    if report:
        report_table = Table(show_header=False, box=None, padding=(0, 2))
        report_table.add_column("Key", style="bold")
        report_table.add_column("Value")
        report_table.add_row("Output", report.get("output_path", "-"))
        report_table.add_row("Figures", report.get("figures_dir", "-"))

        # Charts enabled
        charts = []
        if report.get("show_boxplots", True):
            charts.append("boxplots")
        if report.get("show_latency_cdf"):
            charts.append("latency CDF")
        if report.get("show_bar_chart", True):
            charts.append("bar chart")
        if report.get("show_heatmap", True):
            charts.append("heatmap")
        report_table.add_row("Charts", ", ".join(charts) if charts else "none")

        console.print(Panel(report_table, title="Report Settings", border_style="blue"))

    # Run pre-flight validation for cloud modes and display at the bottom
    from ..common.cli_helpers import is_any_system_cloud_mode
    from ..validation import PreflightChecker

    preflight_failed = False

    if is_any_system_cloud_mode(cfg):
        checker = PreflightChecker(cfg, skip_aws_checks=skip_aws_check, console=console)
        validation_report = checker.run_check_command_validation()

        # Build compact validation content for panel
        validation_lines = []
        for check in validation_report.checks:
            symbol = check.symbol
            # Compact format: symbol + name + message
            validation_lines.append(f"{symbol} {check.name}: {check.message}")
            if not check.passed and check.suggestion:
                validation_lines.append(f"    [dim]\u2192 {check.suggestion}[/dim]")

        # Add summary line
        if validation_report.has_errors:
            summary = f"[red bold]{validation_report.passed_count} passed, {validation_report.failed_count} failed[/red bold]"
            preflight_failed = True
        elif validation_report.has_warnings:
            summary = f"[yellow]{validation_report.passed_count} passed, {validation_report.failed_count} warnings[/yellow]"
        else:
            summary = f"[green]{validation_report.passed_count} passed[/green]"

        validation_lines.append(f"\nSummary: {summary}")
        validation_content = "\n".join(validation_lines)

        # Display in green panel (or red if failed)
        border_color = "red" if preflight_failed else "green"
        console.print(
            Panel(
                validation_content,
                title="Pre-flight Validation",
                border_style=border_color,
            )
        )

        if preflight_failed:
            if not skip_aws_check:
                console.print(
                    "[dim]Use --skip-aws-check to skip AWS API validation[/dim]"
                )
            raise typer.Exit(1)
    else:
        # Local mode - just show success
        console.print(
            Panel(
                "[green]\u2713 Local mode: No cloud validation required[/green]",
                title="Pre-flight Validation",
                border_style="green",
            )
        )

    console.print("\n[green]Configuration is valid and ready to use.[/green]")


def _apply_managed_systems(cfg: dict[str, Any]) -> bool:
    """Deploy all self-managed systems in the config.

    This is called during 'infra apply' to deploy systems like Exasol Personal Edition
    that manage their own infrastructure.

    Args:
        cfg: Configuration dictionary

    Returns:
        True if all managed systems deployed successfully
    """
    from ..common.cli_helpers import get_managed_deployment_dir, get_managed_systems
    from ..infra.managed_state import save_managed_state

    managed_systems = get_managed_systems(cfg)
    project_id = cfg.get("project_id", "default")

    if not managed_systems:
        return True

    all_success = True

    for system in managed_systems:
        system_name = system["name"]
        system_kind = system["kind"]
        setup_config = system.get("setup", {})

        console.print(f"\n  Deploying [bold]{system_name}[/bold] ({system_kind})...")

        # Get deployment directory
        deployment_dir = get_managed_deployment_dir(cfg, system)

        # Create deployment handler
        deployment = get_self_managed_deployment(
            system_kind=system_kind,
            deployment_dir=deployment_dir,
            output_callback=lambda msg: console.print(f"    {msg}"),
            setup_config=setup_config,
        )

        if deployment is None:
            console.print(
                f"  [red]✗ System kind '{system_kind}' does not support managed deployment[/red]"
            )
            all_success = False
            continue

        # Ensure CLI is available (download if needed)
        if hasattr(deployment, "ensure_cli_available"):
            console.print("    Ensuring CLI is available...")
            if not deployment.ensure_cli_available():
                console.print("  [red]✗ Failed to ensure CLI is available[/red]")
                all_success = False
                continue

        # Build options from setup config
        options = {}
        option_keys = [
            "cluster_size",
            "instance_type",
            "data_volume_size",
            "os_volume_size",
            "volume_type",
            "db_password",
            "adminui_password",
            "allowed_cidr",
            "vpc_cidr",
            "subnet_cidr",
        ]
        for key in option_keys:
            value = setup_config.get(key)
            if value is not None:
                options[key] = value

        # Deploy the system
        if not deployment.ensure_running(options):
            console.print(f"  [red]✗ Failed to deploy {system_name}[/red]")
            all_success = False
            continue

        # Get recorded infrastructure commands for report reproduction
        infra_commands = []
        if hasattr(deployment, "get_recorded_commands"):
            infra_commands = deployment.get_recorded_commands()

        # Get connection info and save state
        conn_info = deployment.get_connection_info()
        if conn_info:
            console.print(f"    Connection: {conn_info.host}:{conn_info.port}")
            save_managed_state(
                project_id=project_id,
                system_name=system_name,
                system_kind=system_kind,
                status="deployed",
                connection_info=conn_info,
                deployment_dir=deployment_dir,
                infrastructure_commands=infra_commands,
                deployment_timing_s=deployment.deployment_timing_s,
            )
            console.print(f"  [green]✓ {system_name} deployed successfully[/green]")
        else:
            console.print(
                f"  [yellow]⚠ {system_name} deployed but no connection info available[/yellow]"
            )
            save_managed_state(
                project_id=project_id,
                system_name=system_name,
                system_kind=system_kind,
                status="deployed",
                connection_info=None,
                deployment_dir=deployment_dir,
                infrastructure_commands=infra_commands,
                deployment_timing_s=deployment.deployment_timing_s,
            )

    return all_success


def _destroy_all_environments(cfg: dict[str, Any]) -> tuple[bool, list[str]]:
    """Destroy infrastructure for all environments in a multi-environment config.

    Handles both terraform-managed (aws, gcp, azure) and self-managed (managed) environments.

    Args:
        cfg: Configuration dictionary with environments and systems

    Returns:
        Tuple of (all_success, list of error messages)
    """
    from ..common.cli_helpers import get_all_environments, get_managed_deployment_dir
    from ..common.enums import EnvironmentMode
    from ..infra.managed_state import clear_managed_state

    environments = get_all_environments(cfg)
    project_id = cfg.get("project_id", "default")

    # Track which environments are actually used by systems
    used_env_names: set[str] = set()
    for system in cfg.get("systems", []):
        env_name = system.get("environment") or "default"
        used_env_names.add(env_name)

    all_success = True
    errors: list[str] = []

    # Group environments by mode for efficient handling
    cloud_envs: list[tuple[str, dict[str, Any]]] = []  # (env_name, env_config)
    managed_envs: list[tuple[str, dict[str, Any], dict[str, Any]]] = (
        []
    )  # (env_name, env_config, system_config)

    for env_name in used_env_names:
        env_config = environments.get(env_name, {})
        mode = env_config.get("mode", EnvironmentMode.LOCAL.value)

        if EnvironmentMode.is_cloud_provider(mode):
            cloud_envs.append((env_name, env_config))
        elif mode == EnvironmentMode.MANAGED.value:
            # Find the system(s) using this managed environment
            for system in cfg.get("systems", []):
                if (system.get("environment") or "default") == env_name:
                    managed_envs.append((env_name, env_config, system))

    # Destroy cloud-provider environments (terraform-managed)
    # Group by provider since terraform state is per-provider
    providers_processed: set[str] = set()
    for env_name, env_config in cloud_envs:
        provider = env_config.get("mode", "aws")
        if provider in providers_processed:
            continue  # Already destroyed this provider's resources

        console.print(
            f"\n[blue]Destroying {provider} infrastructure (env: {env_name})...[/blue]"
        )

        try:
            manager = InfraManager(provider, cfg)
            console.print(
                f"  State directory: [cyan]{manager.project_state_dir}[/cyan]"
            )

            result = manager.destroy()
            if result.success:
                console.print(f"  [green]✓ {provider} infrastructure destroyed[/green]")
                providers_processed.add(provider)
            else:
                all_success = False
                error_msg = f"{provider} destroy failed: {result.error}"
                errors.append(error_msg)
                console.print(f"  [red]✗ {error_msg}[/red]")
        except Exception as e:
            all_success = False
            error_msg = f"{provider} destroy exception: {e}"
            errors.append(error_msg)
            console.print(f"  [red]✗ {error_msg}[/red]")

    # Destroy managed environments (e.g., Exasol Personal Edition)
    for env_name, _env_config, system_config in managed_envs:
        system_name = system_config.get("name", "unknown")

        console.print(
            f"\n[blue]Destroying managed infrastructure for {system_name} (env: {env_name})...[/blue]"
        )

        # Get deployment directory using the standard path
        deployment_dir = get_managed_deployment_dir(cfg, system_config)

        console.print(f"  Deployment directory: [cyan]{deployment_dir}[/cyan]")

        # Check if deployment directory exists
        if not Path(deployment_dir).exists():
            console.print(
                "  [yellow]⚠ Deployment directory does not exist, skipping[/yellow]"
            )
            # Still clear state file if it exists
            clear_managed_state(project_id, system_name)
            continue

        try:
            # Use factory function to get appropriate self-managed deployment handler
            system_kind = system_config.get("kind", "")
            deployment_manager = get_self_managed_deployment(
                system_kind=system_kind,
                deployment_dir=deployment_dir,
                output_callback=lambda msg: console.print(f"  {msg}"),
            )

            if deployment_manager is None:
                console.print(
                    f"  [yellow]⚠ No self-managed handler for system kind '{system_kind}', skipping[/yellow]"
                )
                continue

            # Check status first
            status = deployment_manager.get_status()
            if status.status == SelfManagedDeployment.STATUS_NOT_INITIALIZED:
                console.print(
                    f"  [yellow]⚠ No deployment found in {deployment_dir}, skipping[/yellow]"
                )
                # Still clear state file if it exists
                clear_managed_state(project_id, system_name)
                continue

            # Destroy the deployment
            if deployment_manager.destroy():
                console.print(
                    f"  [green]✓ Managed infrastructure for {system_name} destroyed[/green]"
                )
                # Clear state file after successful destroy
                if clear_managed_state(project_id, system_name):
                    console.print(
                        f"  [green]✓ State file cleared for {system_name}[/green]"
                    )
            else:
                all_success = False
                error_msg = f"Managed destroy failed for {system_name}"
                errors.append(error_msg)
                console.print(f"  [red]✗ {error_msg}[/red]")
        except Exception as e:
            all_success = False
            error_msg = f"Managed destroy exception for {system_name}: {e}"
            errors.append(error_msg)
            console.print(f"  [red]✗ {error_msg}[/red]")

    return all_success, errors


@app.command()
def infra(
    action: str = typer.Argument(..., help="Action: plan, apply, destroy"),
    provider: str = typer.Option("aws", "--provider", "-p", help="Cloud provider"),
    config: str | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Config file for infrastructure settings",
        envvar="BENCHKIT_CONFIG",
    ),
    systems: str | None = typer.Option(
        None,
        "--systems",
        help="Comma-separated list of systems to apply infrastructure for",
    ),
    no_wait: bool = typer.Option(
        False, "--no-wait", help="Don't wait for instance initialization (apply only)"
    ),
    skip_preflight: bool = typer.Option(
        False,
        "--skip-preflight",
        help="Skip pre-flight checks (use with caution)",
    ),
) -> None:
    """Manage cloud infrastructure for benchmarks.

    Before apply/plan, validates:
    - SSH key exists and has correct permissions (600 or 400)
    - AWS credentials are configured
    - AWS key pair exists and matches local key
    """
    if action not in ["plan", "apply", "destroy"]:
        console.print(f"[red]Invalid action:[/] {action}. Use: plan, apply, destroy")
        raise typer.Exit(1)

    cfg = load_config(config) if config else {}

    # Filter systems if --systems parameter is provided
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        if "systems" in cfg:
            cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]
            console.print(
                f"[blue]Applying infrastructure for systems:[/] {system_names}"
            )
        else:
            console.print("[yellow]Warning: No systems found in config to filter[/]")

    # Run pre-flight validation for apply and plan
    if action in ["apply", "plan"] and not skip_preflight:
        from ..common.cli_helpers import is_any_system_cloud_mode
        from ..validation import PreflightChecker

        # Check if any system uses cloud mode (supports both env and environments)
        if is_any_system_cloud_mode(cfg):
            console.print("[bold blue]Running pre-flight checks...[/bold blue]\n")
            checker = PreflightChecker(cfg, console=console)
            report = checker.run_infra_deploy_validation()
            checker.display_report(report)

            if report.has_errors:
                console.print(
                    "\n[red bold]Pre-flight checks failed. "
                    "Fix the issues above before deploying.[/red bold]"
                )
                console.print(
                    "[dim]Use --skip-preflight to bypass (not recommended)[/dim]"
                )
                raise typer.Exit(1)

            if report.has_warnings:
                console.print(
                    "\n[yellow]Warnings detected. Proceeding anyway...[/yellow]"
                )
            else:
                console.print("\n[green]All pre-flight checks passed![/green]")
            console.print()

    # Display project isolation info
    project_id = cfg.get("project_id", "default")
    console.print("[bold blue]Infrastructure Management[/bold blue]")
    console.print(f"  Project: [cyan]{project_id}[/cyan]")
    if project_id == "default":
        console.print(
            "[yellow]  Warning: Using default project_id. "
            "Specify project_id in config for isolation.[/yellow]"
        )
    console.print()

    # For destroy action, use multi-environment handler
    if action == "destroy":
        console.print("[blue]Destroying infrastructure for all environments...[/blue]")
        all_success, errors = _destroy_all_environments(cfg)

        if all_success:
            console.print(
                "\n[green]✓ All infrastructure destroyed successfully[/green]"
            )
        else:
            console.print(
                "\n[red]✗ Infrastructure destroy completed with errors:[/red]"
            )
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            raise typer.Exit(1)
        return

    # Import managed systems helpers
    from ..common.cli_helpers import (
        is_any_system_cloud_mode,
        is_any_system_managed_mode,
    )

    has_cloud = is_any_system_cloud_mode(cfg)
    has_managed = is_any_system_managed_mode(cfg)

    # For plan and apply actions on cloud systems, use InfraManager
    if has_cloud:
        manager = InfraManager(provider, cfg)
        console.print(f"  State:   [cyan]{manager.project_state_dir}[/cyan]")
        console.print()

        console.print(f"[blue]Running infrastructure {action} on {provider}[/]")
        if action == "apply":
            result = manager.apply(wait_for_init=not no_wait)
        else:
            result = getattr(manager, action)()

        if result.success:
            console.print(f"[green]✓ Cloud infrastructure {action} completed[/]")

            # For plan command, show detailed output
            if action == "plan" and result.plan_output:
                console.print("\n[bold]Terraform Plan Details:[/bold]")
                # Display the plan output with some formatting
                for line in result.plan_output.split("\n"):
                    if line.strip():
                        # Color-code key terraform plan lines
                        if line.strip().startswith("+ "):
                            console.print(f"[green]{line}[/green]")
                        elif line.strip().startswith("- "):
                            console.print(f"[red]{line}[/red]")
                        elif line.strip().startswith("~ "):
                            console.print(f"[yellow]{line}[/yellow]")
                        elif "Plan:" in line:
                            console.print(f"[bold blue]{line}[/bold blue]")
                        else:
                            console.print(line)
        else:
            console.print(f"[red]✗ Infrastructure {action} failed:[/] {result.error}")
            raise typer.Exit(1)

    # For apply action, also deploy managed systems
    if action == "apply" and has_managed:
        console.print()
        console.print("[blue]Deploying self-managed systems...[/blue]")
        managed_success = _apply_managed_systems(cfg)
        if not managed_success:
            console.print("[red]✗ Managed systems deployment failed[/red]")
            raise typer.Exit(1)
        console.print("[green]✓ Managed systems deployed successfully[/green]")

    # If no cloud systems but has managed, we still succeed
    if not has_cloud and not has_managed:
        console.print(
            "[yellow]No cloud or managed systems found in config. Nothing to do.[/yellow]"
        )


@app.command()
def package(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory for package"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to include in package"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force creation even if already exists"
    ),
) -> None:
    """Create a portable benchmark package.

    By default, includes all systems from the config. Use --systems to create
    a minimal package with only specific systems and their dependencies.
    """
    cfg = load_config(config)
    output_path = Path(output_dir) if output_dir else None

    # Filter to specific systems if requested
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]
        if not cfg["systems"]:
            console.print(
                f"[red]Error: No matching systems found for: {system_names}[/]"
            )
            raise typer.Exit(1)

    console.print(f"[blue]Creating benchmark package for:[/] {cfg['project_id']}")
    if systems:
        console.print(f"[dim]Systems: {[s['name'] for s in cfg['systems']]}[/]")

    package_path = create_workload_zip(cfg, output_path, force)
    console.print(f"[green]✓ ZIP package created:[/] {package_path}")

    console.print(
        "[dim]Package contains all files needed to run the benchmark workload[/]"
    )


def _find_config_for_project(project_id: str, configs_dir: Path) -> Path | None:
    """Find config file for a given project ID."""
    if not configs_dir.exists():
        return None

    for config_file in configs_dir.glob("*.yaml"):
        try:
            cfg = load_config(str(config_file))
            if cfg.get("project_id") == project_id:
                return config_file
        except Exception:
            continue
    return None


def _collect_report_files(report_dir: Path) -> list[Path]:
    """Return available REPORT.md files for a generated benchmark report directory.

    Prefers the new multi-variant layout (3-full, 2-results, 1-short) but
    gracefully falls back to legacy single-report structures. Only immediate
    child directories are inspected to avoid expensive recursive searches.
    """
    if not report_dir.exists():
        return []

    report_files: list[Path] = []

    preferred_variants = ["3-full", "2-results", "1-short"]
    for variant in preferred_variants:
        candidate = report_dir / variant / "REPORT.md"
        if candidate.exists():
            report_files.append(candidate)

    direct_report = report_dir / "REPORT.md"
    if direct_report.exists() and direct_report not in report_files:
        report_files.append(direct_report)

    for child in sorted(report_dir.iterdir()):
        if not child.is_dir() or child.name in preferred_variants:
            continue
        candidate = child / "REPORT.md"
        if candidate.exists() and candidate not in report_files:
            report_files.append(candidate)

    return report_files


@app.command()
def verify(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to verify"
    ),
    generate: str | None = typer.Option(
        None,
        "--generate",
        "-g",
        help="Generate reference data from specified system instead of verifying",
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed execution tracing"
    ),
) -> None:
    """Verify query results against expected data.

    By default, verifies all systems in the config against reference data.
    Use --generate to create reference data from a trusted system.

    Examples:
        # Verify all systems
        benchkit verify -c config.yaml

        # Verify specific system
        benchkit verify -c config.yaml --systems exasol

        # Generate reference data from a system
        benchkit verify -c config.yaml --generate clickhouse
    """

    # Set global debug state
    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Handle reference data generation mode
    if generate:
        console.print(
            f"[blue]Generating reference data for project:[/] {cfg['project_id']}"
        )
        console.print(f"[blue]Source system:[/] {generate}")

        from ..verify import verify_results

        success = verify_results(cfg, outdir, generate_from=generate)

        if success:
            console.print("[green]✓ Reference data generated successfully[/green]")
        else:
            console.print("[red]✗ Failed to generate reference data[/red]")
            raise typer.Exit(1)
        return

    # Normal verification mode
    # Filter systems if --systems parameter is provided
    if systems:
        requested_systems = [s.strip() for s in systems.split(",")]
        original_count = len(cfg.get("systems", []))
        cfg["systems"] = [
            s for s in cfg.get("systems", []) if s["name"] in requested_systems
        ]
        if not cfg["systems"]:
            console.print(
                f"[red]No matching systems found. Available: {[s['name'] for s in cfg.get('systems', [])]}[/red]"
            )
            raise typer.Exit(1)
        console.print(
            f"[blue]Verifying {len(cfg['systems'])} of {original_count} systems: {', '.join(requested_systems)}[/blue]"
        )

    console.print(f"[blue]Verifying results for project:[/] {cfg['project_id']}")

    # Run verification
    from ..verify import verify_results

    success = verify_results(cfg, outdir)

    if success:
        console.print("[green]✓ All verifications passed[/green]")
    else:
        console.print("[red]✗ Some verifications failed[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup(
    config: str = typer.Option(
        ..., "--config", "-c", help="Path to config YAML file", envvar="BENCHKIT_CONFIG"
    ),
) -> None:
    """Clean up running systems after manual benchmark execution."""
    cfg = load_config(config)

    console.print(f"[blue]Cleaning up systems for project:[/] {cfg['project_id']}")

    # Temporarily disable preservation to force cleanup
    cfg["preserve_systems_for_rerun"] = False

    try:
        from ..run.runner import BenchmarkRunner

        # Create runner and set up infrastructure
        runner = BenchmarkRunner(cfg, Path("results") / cfg["project_id"])
        runner._setup_cloud_infrastructure()

        # For cloud environments, check if any systems were connected
        from ..common.cli_helpers import is_any_system_cloud_mode

        if is_any_system_cloud_mode(cfg) and not runner._cloud_instance_managers:
            console.print(
                "[yellow]No running systems found. Infrastructure may already be destroyed.[/yellow]"
            )
            console.print(
                "[yellow]Use 'benchkit infra destroy' to clean up any remaining infrastructure.[/yellow]"
            )
            return

        # Clean up each configured system
        for system_config in cfg["systems"]:
            console.print(f"[yellow]Cleaning up {system_config['name']}...[/yellow]")

            try:
                from ..systems import create_system

                system = create_system(system_config)

                # Set cloud instance manager if available
                system_instance_manager = runner._cloud_instance_managers.get(
                    system_config["name"]
                )
                if system_instance_manager and hasattr(
                    system, "set_cloud_instance_manager"
                ):
                    system.set_cloud_instance_manager(system_instance_manager)

                # Force teardown
                system.teardown()
                console.print(f"[green]✓ {system_config['name']} cleaned up[/green]")

            except Exception as e:
                console.print(
                    f"[red]✗ Failed to cleanup {system_config['name']}: {e}[/red]"
                )

        # Clean up infrastructure if using cloud
        if is_any_system_cloud_mode(cfg):
            console.print(
                "[yellow]Infrastructure cleanup available via: make infra-destroy[/yellow]"
            )
            console.print(
                f"[yellow]Or run: benchkit infra destroy --config {config}[/yellow]"
            )

        console.print("[green]✓ Cleanup completed[/green]")

    except Exception as e:
        console.print(f"[red]Cleanup failed: {e}[/red]")
        raise typer.Exit(code=1) from e


@app.command()
def combine(
    source: list[str] = typer.Option(
        ...,
        "--source",
        "-s",
        help=(
            "Source specification: config.yaml:system1,system2 or "
            "config.yaml:sys1:new_name,sys2 for renaming"
        ),
    ),
    output: str = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output project ID for combined results",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        "-t",
        help="Title for the combined benchmark report",
    ),
    author: str | None = typer.Option(
        None,
        "--author",
        "-a",
        help="Author for the combined benchmark report",
    ),
    no_report: bool = typer.Option(
        False,
        "--no-report",
        help="Skip automatic report regeneration after combining",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing output project if it exists",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug output for detailed tracing",
    ),
) -> None:
    """Combine results from multiple benchmark projects into one.

    Use this to create comparison reports from separately-run benchmarks.
    All source projects must have identical workload configurations
    (same scale factor, queries, runs_per_query, etc.).

    Examples:

        # Compare Exasol from one benchmark with ClickHouse from another
        benchkit combine \\
            --source configs/exasol_sf100.yaml:exasol \\
            --source configs/clickhouse_sf100.yaml:clickhouse \\
            --output exasol_vs_clickhouse

        # Compare two versions with rename to avoid conflicts
        benchkit combine \\
            --source configs/exasol_v8.yaml:exasol:exasol_v8 \\
            --source configs/exasol_v9.yaml:exasol:exasol_v9 \\
            --output exasol_version_comparison

        # Combine without auto-generating report
        benchkit combine \\
            --source proj1.yaml:sys1 \\
            --source proj2.yaml:sys2 \\
            --output combined \\
            --no-report
    """
    from ..combine import BenchmarkCombiner, parse_source_arg

    set_debug(debug)

    console.print("[bold blue]Combining benchmark results[/]")

    try:
        # Parse source arguments
        sources = [parse_source_arg(s) for s in source]

        # Create combiner and execute
        combiner = BenchmarkCombiner(
            sources=sources,
            output_project_id=output,
            title=title,
            author=author,
        )

        output_dir = combiner.combine(force=force)
        console.print(f"[green]✓ Combined results saved to:[/] {output_dir}")

        # Auto-generate report unless disabled
        if not no_report:
            console.print("[blue]Generating combined report...[/]")
            config_path = output_dir / "config.yaml"
            if config_path.exists():
                cfg = load_config(str(config_path))
                report_path = render_report(cfg)
                console.print(f"[green]✓ Report generated:[/] {report_path}")
            else:
                console.print(
                    "[yellow]Warning: Could not generate report - "
                    "config.yaml not found[/]"
                )

        console.print("[bold green]✓ Combine completed successfully![/]")

    except FileExistsError as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1) from e
    except Exception as e:
        console.print(f"[red]Error combining results:[/] {e}")
        if debug:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(code=1) from e


# =============================================================================
# Suite Commands
# =============================================================================

suite_app = typer.Typer(
    name="suite",
    help="Manage benchmark suites (collections of benchmarks)",
    no_args_is_help=True,
)
app.add_typer(suite_app)


@suite_app.command("run")
def suite_run(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    series: str | None = typer.Option(
        None, "--series", "-s", help="Run only this series"
    ),
    benchmark: str | None = typer.Option(
        None, "--benchmark", "-b", help="Run specific benchmark (series/config_name)"
    ),
    resume: bool = typer.Option(
        False, "--resume", "-r", help="Skip completed benchmarks"
    ),
    parallel: int = typer.Option(
        1, "--parallel", "-p", help="Number of concurrent benchmarks"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show plan without executing"
    ),
    no_cleanup: bool = typer.Option(
        False, "--no-cleanup", help="Keep infrastructure after each benchmark"
    ),
    tag: str = typer.Option("", "--tag", "-t", help="Tag for this run"),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to run"
    ),
    enable: list[str] = typer.Option(
        [], "--enable", help="Enable specific series (can be repeated)"
    ),
    disable: list[str] = typer.Option(
        [], "--disable", help="Disable specific series (can be repeated)"
    ),
    debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
) -> None:
    """Run benchmarks in a suite.

    Examples:
        # Run all enabled series
        benchkit suite run ./my-suite/

        # Dry run to see plan
        benchkit suite run ./my-suite/ --dry-run

        # Run specific series
        benchkit suite run ./my-suite/ --series 01_node_scaling

        # Run specific benchmark
        benchkit suite run ./my-suite/ --benchmark 01_node_scaling/nodes_04

        # Resume after interruption
        benchkit suite run ./my-suite/ --resume

        # Enable disabled series for this run
        benchkit suite run ./my-suite/ --enable 03_concurrency
    """
    from ..debug import set_debug
    from ..suite import SuiteRunner, load_suite_config

    set_debug(debug)

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        console.print("[dim]Use 'benchkit suite init' to create a new suite[/dim]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)

        # Apply enable/disable overrides
        for series_name in enable:
            if series_name in config.series:
                config.series[series_name].enabled = True
            else:
                # Create new series config if not defined
                from ..suite import SeriesConfig

                config.series[series_name] = SeriesConfig(
                    name=series_name, enabled=True
                )

        for series_name in disable:
            if series_name in config.series:
                config.series[series_name].enabled = False

        runner = SuiteRunner(path, config)

        # Use config execution settings when CLI --parallel is not explicitly set
        effective_parallel = parallel
        if parallel == 1 and config.execution.mode in ("parallel", "parallel_series"):
            effective_parallel = config.execution.max_parallel

        success = runner.run(
            series=series,
            benchmark=benchmark,
            resume=resume,
            parallel=effective_parallel,
            dry_run=dry_run,
            no_cleanup=no_cleanup,
            tag=tag,
            systems=systems,
        )

        if not success:
            raise typer.Exit(1)

    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Suite run failed: {e}[/red]")
        if debug:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1) from e


@suite_app.command("status")
def suite_status(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed per-system status"
    ),
) -> None:
    """Show status of all benchmarks in a suite.

    Displays actual benchmark progress by checking results directories.
    Shows phase completion (setup, load, run) for each benchmark.

    Use --verbose to see per-system details including query counts and errors.
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)
        runner.show_status(verbose=verbose)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("list")
def suite_list(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    hide_disabled: bool = typer.Option(
        False, "--hide-disabled", help="Hide disabled series from output"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show system kinds and instance types"
    ),
) -> None:
    """List all series and configs in a suite.

    Shows the structure of the suite including all series and their
    benchmark configurations with workload type, scale factor, and counts.

    Use --verbose to see detailed system kinds and instance types for each config.
    Use --hide-disabled to hide disabled series.
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)
        runner.list_configs(hide_disabled=hide_disabled, verbose=verbose)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("report")
def suite_report(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for reports"
    ),
    combined: bool = typer.Option(
        False,
        "--combined",
        "-c",
        help="Generate a single combined report instead of individual reports",
    ),
) -> None:
    """Generate reports for all completed benchmarks.

    By default, generates individual reports for each completed benchmark.
    Use --combined to merge all results into a single unified report.
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)
        result = runner.generate_report(output, combined=combined)
        if not result:
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("reset")
def suite_reset(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    confirm: bool = typer.Option(
        False, "--yes", "-y", help="Confirm reset without prompting"
    ),
) -> None:
    """Reset suite state (clear completion markers).

    This clears all recorded state, allowing benchmarks to be re-run.
    Does not delete result data.
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    if not confirm:
        console.print(
            "[yellow]This will clear all suite state. "
            "Result data will not be deleted.[/yellow]"
        )
        response = typer.prompt("Continue? [y/N]", default="n")
        if response.lower() != "y":
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)
        runner.reset_state()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("destroy")
def suite_destroy(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    series: str | None = typer.Option(
        None, "--series", "-s", help="Destroy only this series"
    ),
    benchmark: str | None = typer.Option(
        None,
        "--benchmark",
        "-b",
        help="Destroy specific benchmark (series/config_name)",
    ),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to destroy"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be destroyed without executing"
    ),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
) -> None:
    """Destroy infrastructure for benchmarks in a suite.

    Destroys cloud infrastructure (via Terraform) and managed deployments
    for matching benchmarks. Use filters to target specific benchmarks.

    Examples:
        # Destroy all infrastructure in suite
        benchkit suite destroy ./my-suite/ --yes

        # Dry run to see what would be destroyed
        benchkit suite destroy ./my-suite/ --dry-run

        # Destroy specific series
        benchkit suite destroy ./my-suite/ --series 01_node_scaling --yes

        # Destroy specific benchmark
        benchkit suite destroy ./my-suite/ --benchmark 01_node_scaling/nodes_04 --yes

        # Destroy only specific systems
        benchkit suite destroy ./my-suite/ --systems exasol,clickhouse --yes
    """
    from ..debug import set_debug
    from ..suite import SuiteRunner, load_suite_config

    set_debug(debug)

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)

        # Discover configs based on filters
        if benchmark:
            # Parse benchmark as series/config_name
            parts = benchmark.split("/")
            if len(parts) != 2:
                console.print(
                    f"[red]Invalid benchmark format: {benchmark}. "
                    f"Use 'series_name/config_name'[/red]"
                )
                raise typer.Exit(1)

            series_name, config_name = parts
            configs_by_series = runner.discover_configs(
                series_filter=series_name, include_disabled=True
            )

            # Find the specific config
            target_configs: list[tuple[str, Path]] = []
            for s_name, config_paths in configs_by_series.items():
                for cfg_path in config_paths:
                    if cfg_path.stem == config_name:
                        target_configs.append((s_name, cfg_path))

            if not target_configs:
                console.print(f"[red]Benchmark not found: {benchmark}[/red]")
                raise typer.Exit(1)
        else:
            # Use series filter if provided
            configs_by_series = runner.discover_configs(
                series_filter=series, include_disabled=True
            )
            target_configs = [
                (s_name, cfg_path)
                for s_name, config_paths in configs_by_series.items()
                for cfg_path in config_paths
            ]

        if not target_configs:
            console.print("[yellow]No matching benchmark configurations found[/yellow]")
            raise typer.Exit(0)

        # Parse systems filter
        system_names_filter: list[str] | None = None
        if systems:
            system_names_filter = [s.strip() for s in systems.split(",")]

        # Show what will be destroyed
        console.print()
        if dry_run:
            console.print(
                "[bold yellow]DRY RUN - Infrastructure to destroy:[/bold yellow]"
            )
        else:
            console.print("[bold red]Infrastructure to destroy:[/bold red]")
        console.print()

        for series_name, cfg_path in target_configs:
            benchmark_id = f"{series_name}/{cfg_path.stem}"
            cfg = load_config(cfg_path)

            # Filter systems if specified
            cfg_systems = cfg.get("systems", [])
            if system_names_filter:
                cfg_systems = [
                    s for s in cfg_systems if s.get("name") in system_names_filter
                ]

            if not cfg_systems:
                continue

            system_names_str = ", ".join(s.get("name", "unknown") for s in cfg_systems)
            console.print(f"  • [cyan]{benchmark_id}[/cyan]: {system_names_str}")

        console.print()

        if dry_run:
            console.print(
                "[dim]Dry run complete - no infrastructure was destroyed[/dim]"
            )
            return

        # Confirm destruction
        if not confirm:
            console.print(
                "[yellow]This will destroy cloud infrastructure and managed deployments.[/yellow]"
            )
            response = typer.prompt("Continue? [y/N]", default="n")
            if response.lower() != "y":
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        # Destroy infrastructure for each matching benchmark
        all_success = True
        for series_name, cfg_path in target_configs:
            benchmark_id = f"{series_name}/{cfg_path.stem}"
            cfg = load_config(cfg_path)

            # Filter systems if specified
            if system_names_filter:
                cfg["systems"] = [
                    s
                    for s in cfg.get("systems", [])
                    if s.get("name") in system_names_filter
                ]
                if not cfg["systems"]:
                    continue

            console.print(f"\n[bold]Destroying: {benchmark_id}[/bold]")

            success, errors = _destroy_all_environments(cfg)
            if success:
                console.print("  [green]✓ Destroyed successfully[/green]")
            else:
                console.print("  [red]✗ Errors during destruction:[/red]")
                for error in errors:
                    console.print(f"    - {error}")
                all_success = False

        console.print()
        if all_success:
            console.print("[green]✓ All infrastructure destroyed successfully[/green]")
        else:
            console.print(
                "[yellow]⚠ Some infrastructure could not be destroyed[/yellow]"
            )
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Suite destroy failed: {e}[/red]")
        if debug:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1) from e


@suite_app.command("sync")
def suite_sync(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would change without writing"
    ),
    force: bool = typer.Option(
        False, "--force", help="Overwrite existing state entirely"
    ),
    verbose: bool = typer.Option(
        False, "-v", "--verbose", help="Show detailed changes"
    ),
) -> None:
    """Synchronize suite state with actual results.

    Scans the results/ directory and updates .benchkit/state.json
    to reflect which benchmarks have actually been completed.

    Useful when:
    - Benchmarks were run outside the suite runner
    - State file was deleted or corrupted
    - Results were copied from another machine
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Error: {suite_yaml} not found[/red]")
        raise typer.Exit(1)

    try:
        config = load_suite_config(suite_yaml)
        runner = SuiteRunner(path, config)

        if dry_run:
            console.print("[yellow]Dry run - no changes will be made[/yellow]")

        summary = runner.sync_state(dry_run=dry_run, force=force)

        # Display results
        console.print()
        if verbose and summary["details"]:
            from rich.table import Table

            table = Table(title="State Changes")
            table.add_column("Benchmark")
            table.add_column("Old Status")
            table.add_column("New Status")

            for detail in summary["details"]:
                old = detail["old_status"] or "[dim]none[/dim]"
                new = detail["new_status"]
                color = "green" if new == "completed" else "yellow"
                table.add_row(detail["benchmark_id"], old, f"[{color}]{new}[/{color}]")

            console.print(table)
            console.print()

        # Summary line
        console.print(
            f"[bold]Summary:[/bold] {summary['updated']} updated, "
            f"{summary['unchanged']} unchanged"
        )

        if not dry_run and summary["updated"] > 0:
            state_file = path / ".benchkit" / "state.json"
            console.print(f"[green]✓ State file updated: {state_file}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("init")
def suite_init(
    path: Path = typer.Argument(..., help="Directory to create suite in"),
    name: str = typer.Option(
        "My Benchmark Suite", "--name", "-n", help="Name for the suite"
    ),
) -> None:
    """Initialize a new benchmark suite with scaffolding.

    Creates the basic structure for a benchmark suite including:
    - suite.yaml configuration
    - Example series directory
    - Example benchmark configuration
    - README and .gitignore
    """
    from ..suite import init_suite

    if path.exists() and any(path.iterdir()):
        console.print(f"[yellow]Warning: Directory {path} is not empty[/yellow]")
        response = typer.prompt("Continue? [y/N]", default="n")
        if response.lower() != "y":
            console.print("[dim]Cancelled[/dim]")
            raise typer.Exit(0)

    try:
        init_suite(path, name)
    except Exception as e:
        console.print(f"[red]Error creating suite: {e}[/red]")
        raise typer.Exit(1) from e


@suite_app.command("validate")
def suite_validate(
    path: Path = typer.Argument(..., help="Path to suite directory"),
) -> None:
    """Validate suite structure and configurations.

    Checks that:
    - suite.yaml exists and is valid
    - All referenced series directories exist
    - All benchmark configurations are valid
    """
    from ..suite import SuiteRunner, load_suite_config

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]✗ Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    errors = []
    warnings = []

    # Validate suite.yaml
    try:
        config = load_suite_config(suite_yaml)
        console.print(f"[green]✓ Suite configuration valid: {config.name}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Invalid suite.yaml: {e}[/red]")
        raise typer.Exit(1) from e

    # Check series directories
    runner = SuiteRunner(path, config)
    discovered = runner.discover_configs()

    if not discovered:
        warnings.append("No benchmark configurations found")

    # Validate each config
    total_configs = 0
    valid_configs = 0

    for series_name, configs in discovered.items():
        console.print(f"\n[bold]Series: {series_name}[/bold]")

        for config_path in configs:
            total_configs += 1
            try:
                load_config(str(config_path))  # Validate the config
                console.print(f"  [green]✓[/green] {config_path.name}")
                valid_configs += 1
            except Exception as e:
                console.print(f"  [red]✗[/red] {config_path.name}: {e}")
                errors.append(f"{config_path}: {e}")

    # Summary
    console.print()
    if errors:
        console.print(
            f"[red]Validation failed: {len(errors)} errors, "
            f"{valid_configs}/{total_configs} configs valid[/red]"
        )
        raise typer.Exit(1)
    elif warnings:
        console.print(
            f"[yellow]Validation passed with warnings: "
            f"{valid_configs}/{total_configs} configs valid[/yellow]"
        )
        for warning in warnings:
            console.print(f"  [yellow]⚠ {warning}[/yellow]")
    else:
        console.print(
            f"[green]✓ Suite valid: {valid_configs}/{total_configs} configs[/green]"
        )


@suite_app.command("publish")
def suite_publish(
    path: Path = typer.Argument(..., help="Path to suite directory"),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="Output directory for the website"
    ),
    title: str | None = typer.Option(
        None, "--title", help="Custom site title (default: suite name)"
    ),
    base_url: str = typer.Option("./", "--base-url", help="Base URL for assets"),
    include_reports: bool = typer.Option(
        True, "--include-reports/--no-reports", help="Copy individual benchmark reports"
    ),
    theme: str = typer.Option("auto", "--theme", help="Theme: light, dark, auto"),
    regenerate_stale: bool = typer.Option(
        False,
        "--regenerate-stale",
        help="Regenerate reports that are older than their data",
    ),
) -> None:
    """Generate a static benchmark comparison website from suite results.

    Creates an interactive dashboard with visualizations for comparing
    benchmark results across all benchmarks in the suite.

    Example:
        benchkit suite publish ./my-suite/
        benchkit suite publish ./my-suite/ -o docs/dashboard/
    """
    from ..suite.publisher import publish_suite

    suite_yaml = path / "suite.yaml"
    if not suite_yaml.exists():
        console.print(f"[red]Suite configuration not found: {suite_yaml}[/red]")
        raise typer.Exit(1)

    try:
        index_path = publish_suite(
            suite_path=path,
            output_dir=output,
            title=title,
            base_url=base_url,
            include_reports=include_reports,
            theme=theme,
            regenerate_stale=regenerate_stale,
        )
        console.print(f"\n[bold green]✓ Dashboard published: {index_path}[/bold green]")
    except Exception as e:
        console.print(f"[red]Publishing failed: {e}[/red]")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
