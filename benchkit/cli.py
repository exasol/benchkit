"""Command line interface for the benchmark framework."""

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer

if TYPE_CHECKING:
    import pandas as pd
from rich.console import Console
from rich.table import Table

# Load .env file if it exists - this must be done early before other imports
try:
    from dotenv import load_dotenv

    load_dotenv(
        override=True
    )  # override=True makes .env vars take precedence over existing env vars
except ImportError:
    pass  # python-dotenv not installed, continue without .env support

from .config import load_config
from .debug import set_debug
from .gather.system_probe import probe_all
from .infra.manager import InfraManager
from .package.creator import create_workload_zip
from .report.render import render_global_report_index, render_report
from .run.runner import run_benchmark

app = typer.Typer(
    name="benchkit",
    help="Database benchmark framework for generating reproducible reports",
    no_args_is_help=True,
)

console = Console()


@app.command()
def probe(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
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

    # Check if this is a cloud benchmark with multiple systems
    env_mode = cfg.get("env", {}).get("mode", "local")

    if env_mode in ["aws", "gcp", "azure"]:
        console.print("[blue]Multi-system cloud benchmark detected[/]")
        console.print("[blue]Collecting system information from all instances...[/]")

        # Probe each remote instance
        success = _probe_remote_systems(cfg, outdir)
        if success:
            console.print("[green]✓ Remote system probes completed[/]")
        else:
            console.print("[red]✗ Some remote system probes failed[/]")
    else:
        # Local benchmark - probe current system
        meta = probe_all(outdir)
        console.print(f"[green]✓ System probe saved to:[/] {outdir / 'system.json'}")
        console.print(
            f"[dim]Found {meta['cpu_count_logical']} logical CPUs, "
            f"{meta['memory_total_gb']}GB RAM[/]"
        )


@app.command()
def setup(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to setup"
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
    from .run.runner import BenchmarkRunner

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

    runner = BenchmarkRunner(cfg, outdir)
    success = runner.run_setup()

    if success:
        console.print("[green]✓ Setup phase completed successfully[/]")
    else:
        console.print("[red]✗ Setup phase failed[/]")
        raise typer.Exit(1)


@app.command()
def load(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
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
    from .run.runner import BenchmarkRunner

    set_debug(debug)

    cfg = load_config(config)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)

    # Override config with CLI options
    if systems:
        system_names = [s.strip() for s in systems.split(",")]
        cfg["systems"] = [s for s in cfg["systems"] if s["name"] in system_names]

    console.print(f"[blue]Loading data for project:[/] {cfg['project_id']}")
    console.print(f"[dim]Systems: {[s['name'] for s in cfg['systems']]}[/]")
    console.print(
        f"[dim]Workload: {cfg['workload']['name']} (SF={cfg['workload']['scale_factor']})[/]"
    )
    if local:
        console.print("[cyan]Mode: Local-to-remote (connecting to remote DBs)[/]")

    runner = BenchmarkRunner(cfg, outdir)
    success = runner.run_load(force=force, local=local)

    if success:
        console.print("[green]✓ Load phase completed successfully[/]")
    else:
        console.print("[red]✗ Load phase failed[/]")
        raise typer.Exit(1)


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
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
        False, "--full", help="Run full benchmark (setup + load + run)"
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

    Use --full flag to run the complete benchmark (setup + load + run).

    Use --local to execute queries from your local machine directly
    against remote databases (using their public IPs). This is useful for
    faster iteration during workload development and debugging.
    """
    from .run.runner import BenchmarkRunner

    set_debug(debug)

    cfg = load_config(config)
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

    runner = BenchmarkRunner(cfg, outdir)

    if full:
        # Run all phases: setup -> load -> run
        console.print(
            "[bold blue]Running full benchmark (setup + load + run)[/bold blue]"
        )

        if not runner.run_setup():
            console.print("[red]✗ Setup phase failed[/]")
            raise typer.Exit(1)

        if not runner.run_load(local=local):
            console.print("[red]✗ Load phase failed[/]")
            raise typer.Exit(1)

        if not runner.run_queries(force=force, local=local):
            console.print("[red]✗ Query execution failed[/]")
            raise typer.Exit(1)
    else:
        # Run queries only (strict mode - check prerequisites)
        if not runner.run_queries(force=force, local=local):
            raise typer.Exit(1)

    console.print(f"[green]✓ Benchmark completed:[/] {outdir / 'runs.csv'}")


@app.command()
def execute(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
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
        None, "--config", "-c", help="Path to config YAML file"
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
        None, "--config", "-c", help="Config file(s) to check status for"
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
            _show_detailed_status(cfg, config_file)
        else:
            # Fallback to basic status if no config found
            console.print(
                f"[yellow]No config found for project {project}, showing basic status[/yellow]"
            )
            project_dir = results_dir / project
            if not project_dir.exists():
                console.print(f"[red]Project not found:[/] {project}")
                raise typer.Exit(1)
            _show_project_status_basic(project, project_dir)
    elif config:
        # Show status for specific config(s)
        for config_path in config:
            cfg = load_config(config_path)
            _show_detailed_status(cfg, Path(config_path))
            console.print()  # Empty line between configs
    else:
        # Show status for all configs in configs directory
        if not configs_dir.exists():
            console.print(
                "[yellow]No configs directory found. Showing all projects in results.[/]"
            )
            _show_all_projects(results_dir)
            return

        config_files = sorted(configs_dir.glob("*.yaml"))
        if not config_files:
            console.print("[yellow]No config files found in configs directory.[/]")
            return

        console.print("[bold blue]Benchmark Status Summary[/bold blue]\n")
        _show_configs_summary(config_files)


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
    env = cfg.get("env", {})
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
    print("# Parallel execution settings")
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
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show all configuration details"
    ),
    dump: bool = typer.Option(
        False,
        "--dump",
        "-d",
        help="Dump full config with defaults as YAML (for redirection)",
    ),
) -> None:
    """Check and display configuration file contents.

    With --dump, outputs the expanded configuration as commented YAML that can be
    redirected to a file. This shows all default values that were auto-filled.
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
    env = cfg.get("env", {})
    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column("Key", style="bold")
    env_table.add_column("Value")
    env_table.add_row("Mode", env.get("mode", "local"))
    if env.get("region"):
        env_table.add_row("Region", env.get("region"))
    env_table.add_row(
        "External DB Access",
        "Yes" if env.get("allow_external_database_access") else "No",
    )
    if env.get("ssh_key_name"):
        env_table.add_row("SSH Key", env.get("ssh_key_name"))
    console.print(Panel(env_table, title="Environment", border_style="blue"))

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

    console.print("\n[green]Configuration is valid and ready to use.[/green]")


@app.command()
def infra(
    action: str = typer.Argument(..., help="Action: plan, apply, destroy"),
    provider: str = typer.Option("aws", "--provider", "-p", help="Cloud provider"),
    config: str | None = typer.Option(
        None, "--config", "-c", help="Config file for infrastructure settings"
    ),
    systems: str | None = typer.Option(
        None,
        "--systems",
        help="Comma-separated list of systems to apply infrastructure for",
    ),
    no_wait: bool = typer.Option(
        False, "--no-wait", help="Don't wait for instance initialization (apply only)"
    ),
) -> None:
    """Manage cloud infrastructure for benchmarks."""
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

    manager = InfraManager(provider, cfg)

    # Display project isolation info
    project_id = cfg.get("project_id", "default")
    console.print("[bold blue]Infrastructure Management[/bold blue]")
    console.print(f"  Project: [cyan]{project_id}[/cyan]")
    console.print(f"  State:   [cyan]{manager.project_state_dir}[/cyan]")
    if project_id == "default":
        console.print(
            "[yellow]  Warning: Using default project_id. "
            "Specify project_id in config for isolation.[/yellow]"
        )
    console.print()

    console.print(f"[blue]Running infrastructure {action} on {provider}[/]")
    if action == "apply":
        result = manager.apply(wait_for_init=not no_wait)
    else:
        result = getattr(manager, action)()

    if result.success:
        console.print(f"[green]✓ Infrastructure {action} completed[/]")

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


@app.command()
def package(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
    output_dir: str | None = typer.Option(
        None, "--output", "-o", help="Output directory for package"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force creation even if already exists"
    ),
) -> None:
    """Create a portable benchmark package."""
    cfg = load_config(config)
    output_path = Path(output_dir) if output_dir else None

    console.print(f"[blue]Creating benchmark package for:[/] {cfg['project_id']}")

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
    """
    Return available REPORT.md files for a generated benchmark report directory.

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


# =============================================================================
# Status Command Helper Functions
# =============================================================================


def _extract_error_summary(error_msg: str | None) -> str:
    """
    Extract key error type from verbose error messages.

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
        import re

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
        import re

        match = re.search(r"error code:\s*(\w+)", error_msg, re.IGNORECASE)
        if match:
            return f"Exasol: {match.group(1)}"

    # Generic truncation for unknown errors
    if len(error_msg) > 50:
        return error_msg[:47] + "..."
    return error_msg


def _load_phase_data(
    results_dir: Path, system_names: list[str]
) -> dict[str, dict[str, Any]]:
    """
    Load phase completion data for all systems.

    Returns dict: {system_name: {'setup': {...}, 'load': {...}}}
    """
    from .util import load_json

    phase_data: dict[str, dict[str, Any]] = {}

    for system_name in system_names:
        phase_data[system_name] = {"setup": None, "load": None}

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


def _load_runs_data(results_dir: Path) -> "pd.DataFrame | None":
    """Load runs.csv and return as DataFrame, or None if not found."""
    import pandas as pd

    runs_csv = results_dir / "runs.csv"
    if not runs_csv.exists():
        return None

    try:
        return pd.read_csv(runs_csv)
    except Exception:
        return None


def _get_query_stats_per_system(
    df: "pd.DataFrame",
) -> dict[str, dict[str, Any]]:
    """
    Compute query statistics per system.

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
                error_summary = _extract_error_summary(first_error)
                errors.append((query, query_failed, query_total, error_summary))

        stats[system] = {
            "total": total,
            "success": success,
            "failed": failed,
            "avg_ms": avg_ms,
            "errors": errors,
        }

    return stats


def _check_infra_available(
    cfg: dict[str, Any], system_name: str, infra_ips: dict[str, Any] | None
) -> tuple[str, str]:
    """
    Check if infrastructure for system is still running.

    Returns (status, display):
    - ('up', '[green]✓ up[/]') - SSH connectivity confirmed
    - ('down', '[red]✗ down[/]') - Cannot reach instance
    - ('na', '[dim]-[/]') - Local mode, N/A
    - ('unknown', '[yellow]?[/]') - No IP info available
    """
    import subprocess

    env_mode = cfg.get("env", {}).get("mode", "local")

    # Local mode - infrastructure N/A
    if env_mode == "local":
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

    # Get SSH key
    ssh_key = cfg.get("env", {}).get("ssh_private_key_path", "")
    if ssh_key:
        ssh_key = os.path.expanduser(ssh_key)

    # Quick SSH connectivity check (5 second timeout)
    ssh_opts = "-o ConnectTimeout=5 -o StrictHostKeyChecking=no -o BatchMode=yes"
    if ssh_key and os.path.exists(ssh_key):
        ssh_opts += f" -i {ssh_key}"

    cmd = f'ssh {ssh_opts} ubuntu@{ip} "echo ok" 2>/dev/null'

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return ("up", "[green]✓ up[/]")
        else:
            return ("down", "[red]✗ down[/]")
    except subprocess.TimeoutExpired:
        return ("down", "[red]✗ down[/]")
    except Exception:
        return ("unknown", "[yellow]?[/]")


def _format_timing(seconds: float | None) -> str:
    """Format timing value for display."""
    if seconds is None or seconds == 0:
        return ""
    if seconds < 60:
        return f"({seconds:.1f}s)"
    minutes = seconds / 60
    return f"({minutes:.1f}m)"


def _show_project_status_basic(project: str, project_dir: Path) -> None:
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


def _show_detailed_status(cfg: dict[str, Any], config_file: Path) -> None:
    """Show detailed status for a benchmark including config information."""
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
    info_table.add_row("Environment", cfg.get("env", {}).get("mode", "local"))

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
    phase_data = _load_phase_data(results_dir, system_names)
    runs_df = _load_runs_data(results_dir)
    query_stats = _get_query_stats_per_system(runs_df) if runs_df is not None else {}

    # Get infrastructure IPs for availability check (cloud mode only)
    env_mode = cfg.get("env", {}).get("mode", "local")
    infra_ips: dict[str, Any] | None = None
    if env_mode in ["aws", "gcp", "azure"]:
        try:
            infra_manager = InfraManager(env_mode, cfg)
            infra_ips = infra_manager.get_infrastructure_ips()
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
    if env_mode in ["aws", "gcp", "azure"]:
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
            setup_cell = f"[green]✓[/] {_format_timing(timing)}"
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
            load_cell = f"[green]✓[/] {_format_timing(load_timing)}"
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

        # Infrastructure availability (cloud only)
        if env_mode in ["aws", "gcp", "azure"]:
            _, infra_cell = _check_infra_available(cfg, system_name, infra_ips)
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
    report_files = _collect_report_files(report_dir)
    if report_files:
        console.print(f"[dim]Report: {report_files[0]}[/dim]")

    # Show infrastructure details (IPs and connection strings) for cloud environments
    if env_mode in ["aws", "gcp", "azure"]:
        console.print()
        _show_infrastructure_details(cfg, systems)


def _show_infrastructure_details(
    cfg: dict[str, Any], systems: list[dict[str, Any]]
) -> None:
    """Show infrastructure details including IPs and connection strings."""
    from .infra.manager import InfraManager
    from .systems import SYSTEM_IMPLEMENTATIONS, _lazy_import_system

    try:
        provider = cfg.get("env", {}).get("mode", "aws")
        infra_manager = InfraManager(provider, cfg)

        # Get infrastructure IPs using InfraManager
        infra_ips = infra_manager.get_infrastructure_ips()
        if not infra_ips:
            console.print("[yellow]Infrastructure details not available[/yellow]")
            return

        # Create infrastructure table
        infra_table = Table(
            show_header=True,
            header_style="bold magenta",
            title="Infrastructure Details",
        )
        infra_table.add_column("System", style="bold")
        infra_table.add_column("Public IP")
        infra_table.add_column("Private IP")
        infra_table.add_column("Connection String")

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

            infra_table.add_row(system_name, public_ip, private_ip, connection_str)

        console.print(infra_table)

    except Exception as e:
        console.print(
            f"[yellow]Could not retrieve infrastructure details: {e}[/yellow]"
        )


def _show_configs_summary(config_files: list[Path]) -> None:
    """Show summary table of all configs."""
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
            cfg = load_config(str(config_file))
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
            report_files = _collect_report_files(report_dir)
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


def _probe_remote_systems(config: dict[str, Any], outdir: Path) -> bool:
    """Probe system information on remote cloud instances."""

    from .infra.manager import InfraManager

    try:
        # Get cloud provider from config
        provider = config.get("env", {}).get("mode", "aws")

        # Create infrastructure manager to get instance information
        infra_manager = InfraManager(provider, config)

        # Get terraform outputs to find instances
        result = infra_manager._run_terraform_command("output", ["-json"])
        if not result.success:
            console.print(f"[red]Failed to get terraform outputs: {result.error}[/red]")
            return False

        outputs = result.outputs or {}

        # Extract instance information from new terraform output format
        # After Terraform fix, IPs are always lists: ["ip"] for single-node, ["ip1", "ip2"] for multinode
        instances_to_probe = (
            []
        )  # List of (system_name, node_idx, public_ip, private_ip)

        # New format: system_public_ips = {"exasol": ["ip"], "clickhouse": ["ip1", "ip2"]}
        # Note: _parse_terraform_outputs already extracted the "value" field
        if "system_public_ips" in outputs:
            public_ips = outputs["system_public_ips"] or {}
            private_ips = outputs.get("system_private_ips", {}) or {}

            for system_name, public_ip_list in public_ips.items():
                private_ip_list = private_ips.get(system_name)

                # Handle both list and single IP (backward compatibility)
                if isinstance(public_ip_list, list):
                    for idx, public_ip in enumerate(public_ip_list):
                        private_ip = (
                            private_ip_list[idx]
                            if isinstance(private_ip_list, list)
                            else private_ip_list
                        )
                        instances_to_probe.append(
                            (system_name, idx, public_ip, private_ip)
                        )
                else:
                    # Backward compatibility: single IP (not a list)
                    instances_to_probe.append(
                        (system_name, 0, public_ip_list, private_ip_list)
                    )

        if not instances_to_probe:
            console.print("[yellow]No instances found in terraform outputs[/yellow]")
            return False

        # SSH configuration
        ssh_config = config.get("env", {})
        ssh_key_path = ssh_config.get("ssh_private_key_path", "~/.ssh/id_rsa")
        ssh_user = ssh_config.get("ssh_user", "ubuntu")

        # Expand tilde in SSH key path
        import os

        ssh_key_path = os.path.expanduser(ssh_key_path)

        success_count = 0
        total_instances = len(instances_to_probe)

        for system_name, node_idx, public_ip, _private_ip in instances_to_probe:
            # Show node index for multinode systems
            node_label = (
                f"-node{node_idx}"
                if any(
                    s == system_name and i != node_idx
                    for s, i, _, _ in instances_to_probe
                )
                else ""
            )
            console.print(
                f"[blue]Probing {system_name}{node_label} ([{public_ip}])...[/blue]"
            )

            if _probe_single_remote_system(
                f"{system_name}{node_label}", public_ip, ssh_key_path, ssh_user, outdir
            ):
                console.print(
                    f"[green]✓ {system_name}{node_label} probe completed[/green]"
                )
                success_count += 1
            else:
                console.print(f"[red]✗ {system_name}{node_label} probe failed[/red]")

        console.print(
            f"[blue]Completed {success_count}/{total_instances} system probes[/blue]"
        )
        return success_count == total_instances

    except Exception as e:
        console.print(f"[red]Error during remote system probing: {e}[/red]")
        return False


def _probe_single_remote_system(
    system_name: str, public_ip: str, ssh_key_path: str, ssh_user: str, outdir: Path
) -> bool:
    """Probe a single remote system and save results."""
    import tempfile

    from .debug import debug_log_command, debug_log_result
    from .util import safe_command

    try:
        # Create a temporary Python script for remote execution
        probe_script = '''
import json
import subprocess
import platform
import os
import time

def get_cpu_info():
    """Get detailed CPU information."""
    cpu_info = {}

    # Basic info from platform
    cpu_info["architecture"] = platform.machine()

    try:
        # Try to get detailed CPU info from /proc/cpuinfo
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        lines = cpuinfo.strip().split("\\n")
        cpu_data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "model name":
                    cpu_info["model_name"] = value
                elif key == "vendor_id":
                    cpu_info["vendor_id"] = value
                elif key == "cpu family":
                    cpu_info["cpu_family"] = int(value) if value.isdigit() else value
                elif key == "model":
                    cpu_info["model"] = int(value) if value.isdigit() else value
                elif key == "stepping":
                    cpu_info["stepping"] = int(value) if value.isdigit() else value
                elif key == "microcode":
                    cpu_info["microcode"] = value
                elif key == "cpu MHz":
                    cpu_info["cpu_mhz"] = float(value) if value.replace(".", "").isdigit() else value
                elif key == "cache size":
                    cpu_info["cache_size"] = value
                elif key == "physical id":
                    cpu_data["physical_id"] = value
                elif key == "siblings":
                    cpu_data["siblings"] = int(value) if value.isdigit() else value
                elif key == "core id":
                    cpu_data["core_id"] = value
                elif key == "cpu cores":
                    cpu_data["cpu_cores"] = int(value) if value.isdigit() else value

        # Count logical and physical CPUs
        try:
            cpu_info["count_logical"] = int(subprocess.check_output("nproc", shell=True).decode().strip())
        except:
            cpu_info["count_logical"] = os.cpu_count() or 1

        # Get physical CPU count
        try:
            cpu_info["count_physical"] = len(set([line.split(":")[1].strip() for line in cpuinfo.split("\\n") if line.startswith("physical id")]))
        except:
            cpu_info["count_physical"] = 1

    except Exception as e:
        cpu_info["error"] = str(e)

    return cpu_info

def get_memory_info():
    """Get detailed memory information."""
    memory_info = {}

    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()

        for line in meminfo.split("\\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "MemTotal":
                    memory_kb = int(value.split()[0])
                    memory_info["total_kb"] = memory_kb
                    memory_info["total_gb"] = round(memory_kb / 1024 / 1024, 1)
                elif key == "MemAvailable":
                    memory_info["available_kb"] = int(value.split()[0])
                elif key == "MemFree":
                    memory_info["free_kb"] = int(value.split()[0])
                elif key == "Buffers":
                    memory_info["buffers_kb"] = int(value.split()[0])
                elif key == "Cached":
                    memory_info["cached_kb"] = int(value.split()[0])
    except Exception as e:
        memory_info["error"] = str(e)

    return memory_info

def get_disk_info():
    """Get disk information."""
    disk_info = {}

    try:
        # Get disk usage for root filesystem
        result = subprocess.check_output("df -h /", shell=True).decode()
        lines = result.strip().split("\\n")
        if len(lines) > 1:
            parts = lines[1].split()
            disk_info["root_filesystem"] = {
                "total": parts[1],
                "used": parts[2],
                "available": parts[3],
                "usage_percent": parts[4]
            }

        # Get block device information
        try:
            result = subprocess.check_output("lsblk -J", shell=True).decode()
            disk_info["block_devices"] = json.loads(result)
        except:
            pass

    except Exception as e:
        disk_info["error"] = str(e)

    return disk_info

def get_network_info():
    """Get network information."""
    network_info = {}

    try:
        # Get network interfaces
        result = subprocess.check_output("ip -j addr show", shell=True).decode()
        network_info["interfaces"] = json.loads(result)
    except Exception as e:
        network_info["error"] = str(e)

    return network_info

def get_system_info():
    """Get general system information."""
    system_info = {}

    system_info["hostname"] = platform.node()
    system_info["system"] = platform.system()
    system_info["release"] = platform.release()
    system_info["version"] = platform.version()
    system_info["machine"] = platform.machine()
    system_info["processor"] = platform.processor()

    # Get uptime
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
            system_info["uptime_seconds"] = uptime_seconds
    except:
        pass

    # Get load average
    try:
        system_info["load_average"] = os.getloadavg()
    except:
        pass

    return system_info

# Collect all system information
probe_data = {
    "timestamp": time.time(),
    "cpu": get_cpu_info(),
    "memory": get_memory_info(),
    "disk": get_disk_info(),
    "network": get_network_info(),
    "system": get_system_info()
}

# Convert to the expected format
result = {
    "timestamp": probe_data["timestamp"],
    "hostname": probe_data["system"].get("hostname", "unknown"),
    "cpu_model": probe_data["cpu"].get("model_name", "unknown"),
    "cpu_vendor": probe_data["cpu"].get("vendor_id", "unknown"),
    "cpu_count_logical": probe_data["cpu"].get("count_logical", 1),
    "cpu_count_physical": probe_data["cpu"].get("count_physical", 1),
    "cpu_mhz": probe_data["cpu"].get("cpu_mhz", 0),
    "memory_total_kb": probe_data["memory"].get("total_kb", 0),
    "memory_total_gb": probe_data["memory"].get("total_gb", 0),
    "system_info": probe_data["system"],
    "cpu_info": probe_data["cpu"],
    "memory_info": probe_data["memory"],
    "disk_info": probe_data["disk"],
    "network_info": probe_data["network"]
}

print(json.dumps(result))
'''

        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(probe_script)
            temp_script_path = f.name

        try:
            # Copy script to remote system
            scp_cmd = (
                f'scp -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f"{temp_script_path} {ssh_user}@{public_ip}:/tmp/probe_system.py"
            )
            debug_log_command(scp_cmd, timeout=30)
            scp_result = safe_command(scp_cmd, timeout=30)
            debug_log_result(
                scp_result.get("success", False),
                scp_result.get("stdout"),
                scp_result.get("stderr"),
            )

            if not scp_result.get("success", False):
                console.print(
                    f"[red]Failed to copy probe script to {system_name}[/red]"
                )
                return False

            # Execute probe script on remote system
            ssh_cmd = (
                f'ssh -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "python3 /tmp/probe_system.py"'
            )
            debug_log_command(ssh_cmd, timeout=60)
            probe_result = safe_command(ssh_cmd, timeout=60)
            debug_log_result(
                probe_result.get("success", False),
                probe_result.get("stdout"),
                probe_result.get("stderr"),
            )

            if not probe_result.get("success", False):
                console.print(
                    f"[red]Failed to execute probe script on {system_name}[/red]"
                )
                return False

            # Parse the result
            probe_output = probe_result.get("stdout", "")
            system_data = json.loads(probe_output)

            # Save system-specific probe result
            system_probe_file = outdir / f"system_{system_name}.json"
            with open(system_probe_file, "w") as f:
                json.dump(system_data, f, indent=2)

            # Clean up remote script
            safe_command(
                f'ssh -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "rm -f /tmp/probe_system.py"',
                timeout=10,
            )

            return True

        finally:
            # Clean up local temporary file
            os.unlink(temp_script_path)

    except Exception as e:
        console.print(f"[red]Error probing {system_name}: {e}[/red]")
        return False


def _show_all_projects(results_dir: Path) -> None:
    """Show overview of all projects."""
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
                cfg = load_config(str(config_file))
                report_config = cfg.get("report", {})
                output_path = Path(
                    report_config.get("output_path", f"results/{project_name}/reports")
                )
                report_dir = output_path.parent / output_path.stem
                report_files = _collect_report_files(report_dir)
                report_status = "[green]✓[/]" if report_files else "[red]✗[/]"
            except Exception:
                # Fallback to checking default location
                report_dir = Path("results") / project_name / "reports"
                report_files = _collect_report_files(report_dir)
                report_status = "[green]✓[/]" if report_files else "[red]✗[/]"
        else:
            # No config found, check default location
            report_dir = Path("results") / project_name / "reports"
            report_files = _collect_report_files(report_dir)
            report_status = "[green]✓[/]" if report_files else "[red]✗[/]"

        table.add_row(project_name, system_status, runs_status, report_status)

    console.print(table)


@app.command()
def verify(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
    systems: str | None = typer.Option(
        None, "--systems", help="Comma-separated list of systems to verify"
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Enable debug output for detailed execution tracing"
    ),
) -> None:
    """Verify query results against expected data."""

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
            f"[blue]Verifying {len(cfg['systems'])} of {original_count} systems: {', '.join(requested_systems)}[/blue]"
        )

    console.print(f"[blue]Verifying results for project:[/] {cfg['project_id']}")

    # Run verification
    from .verify import verify_results

    success = verify_results(cfg, outdir)

    if success:
        console.print("[green]✓ All verifications passed[/green]")
    else:
        console.print("[red]✗ Some verifications failed[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup(
    config: str = typer.Option(..., "--config", "-c", help="Path to config YAML file"),
) -> None:
    """Clean up running systems after manual benchmark execution."""
    cfg = load_config(config)

    console.print(f"[blue]Cleaning up systems for project:[/] {cfg['project_id']}")

    # Temporarily disable preservation to force cleanup
    cfg["preserve_systems_for_rerun"] = False

    try:
        from .run.runner import BenchmarkRunner

        # Create runner and set up infrastructure
        runner = BenchmarkRunner(cfg, Path("results") / cfg["project_id"])
        runner._setup_infrastructure()

        # For cloud environments, check if any systems were connected
        env_mode = cfg.get("env", {}).get("mode", "local")
        if env_mode in ["aws", "gcp", "azure"] and not runner._cloud_instance_managers:
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
                from .systems import create_system

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
        env_mode = cfg.get("env", {}).get("mode", "local")
        if env_mode in ["aws", "gcp", "azure"]:
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


if __name__ == "__main__":
    app()
