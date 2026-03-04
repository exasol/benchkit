"""Benchmark suite management for orchestrating multiple benchmarks.

A suite is a collection of benchmark configurations organized into series,
designed to be publishable, extensible, and reproducible.

Example suite structure:
    my-benchmark-suite/
    ├── suite.yaml              # Suite definition
    ├── series/
    │   ├── 01_node_scaling/    # Series directory
    │   │   ├── nodes_01.yaml   # Individual benchmark configs
    │   │   ├── nodes_04.yaml
    │   │   └── nodes_08.yaml
    │   └── 02_scale_factor/
    │       ├── sf_025.yaml
    │       └── sf_100.yaml
    └── .benchkit/              # State directory (gitignored)
        └── state.json

Usage:
    benchkit suite run ./my-benchmark-suite/
    benchkit suite status ./my-benchmark-suite/
    benchkit suite report ./my-benchmark-suite/
"""

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, field_validator
from rich.console import Console
from rich.table import Table

from ..common import PROJECT_ROOT
from ..common.cli_helpers import is_any_system_cloud_mode, is_any_system_managed_mode
from ..config import load_config
from ..run.runner import BenchmarkRunner

console = Console()


# =============================================================================
# Configuration Models
# =============================================================================


class SeriesConfig(BaseModel):
    """Configuration for a benchmark series within a suite."""

    name: str
    description: str = ""
    enabled: bool = True
    path: str | None = None  # relative path to config dir (default: series key name)


class SuiteExecutionConfig(BaseModel):
    """Execution settings for suite runs."""

    mode: Literal["sequential", "parallel", "parallel_series"] = "sequential"
    max_parallel: int = 3
    continue_on_failure: bool = True
    pause_between: int = 30  # Seconds between benchmarks


class SuiteInfrastructureConfig(BaseModel):
    """Infrastructure settings for suite runs."""

    cleanup_after_each: bool = True
    cleanup_on_failure: bool = True


class SuiteTimeoutsConfig(BaseModel):
    """Timeout settings for suite operations."""

    infrastructure: int = 3600  # 1 hour
    benchmark: int = 14400  # 4 hours
    cleanup: int = 900  # 15 minutes


class SuitePublishChartsConfig(BaseModel):
    """Chart visibility for suite dashboard. None = auto-detect based on data."""

    scaling_by_nodes: bool | None = None
    scaling_by_streams: bool | None = None
    scaling_by_sf: bool | None = None
    comparison: bool | None = None
    heatmap: bool | None = None
    efficiency: bool | None = None
    query_scatter: bool | None = None
    stacked_series: bool | None = None


class SuitePublishConfig(BaseModel):
    """Configuration for suite dashboard publishing."""

    title: str | None = None
    description: str | None = None
    output_dir: str | None = None
    theme: str = "auto"
    base_url: str = "./"
    include_reports: bool = True
    template: str = "dashboard"  # "dashboard" (existing) or "leaderboard" (new)
    charts: SuitePublishChartsConfig = SuitePublishChartsConfig()


class SuiteConfig(BaseModel):
    """Main suite configuration loaded from suite.yaml."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    keywords: list[str] = []

    results_dir: str | None = None  # Path to results, relative to suite dir
    series: dict[str, SeriesConfig] = {}
    execution: SuiteExecutionConfig = SuiteExecutionConfig()
    infrastructure: SuiteInfrastructureConfig = SuiteInfrastructureConfig()
    timeouts: SuiteTimeoutsConfig = SuiteTimeoutsConfig()
    publish: SuitePublishConfig = SuitePublishConfig()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure suite name is provided."""
        if not v or not v.strip():
            raise ValueError("Suite name cannot be empty")
        return v


def load_suite_config(path: Path) -> SuiteConfig:
    """Load and validate suite configuration from suite.yaml.

    Args:
        path: Path to suite.yaml file

    Returns:
        Validated SuiteConfig object

    Raises:
        FileNotFoundError: If suite.yaml doesn't exist
        ValueError: If configuration is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Suite configuration not found: {path}")

    with open(path, encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    # Handle case where series might be a simple dict of names
    if "series" in raw_config:
        normalized_series = {}
        for key, value in raw_config["series"].items():
            if value is None:
                # Simple entry: series_name: null
                normalized_series[key] = {"name": key, "enabled": True}
            elif isinstance(value, dict):
                # Full entry with config
                if "name" not in value:
                    value["name"] = key
                normalized_series[key] = value
            else:
                raise ValueError(f"Invalid series config for '{key}': {value}")
        raw_config["series"] = normalized_series

    try:
        return SuiteConfig(**raw_config)
    except Exception as e:
        raise ValueError(f"Invalid suite configuration: {e}") from e


# =============================================================================
# State Management
# =============================================================================


@dataclass
class BenchmarkState:
    """State of a single benchmark within a suite."""

    benchmark_id: str  # e.g., "01_node_scaling/nodes_04"
    config_path: str
    project_id: str
    status: Literal[
        "pending", "running", "completed", "failed", "skipped", "interrupted"
    ] = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    error: str | None = None


@dataclass
class SuiteState:
    """Overall state of a suite run."""

    suite_name: str
    suite_version: str
    run_tag: str = ""
    started_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    status: Literal["pending", "running", "completed", "failed", "interrupted"] = (
        "pending"
    )
    current_benchmark: str | None = None
    benchmarks: dict[str, BenchmarkState] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for JSON serialization."""
        return {
            "suite_name": self.suite_name,
            "suite_version": self.suite_version,
            "run_tag": self.run_tag,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "current_benchmark": self.current_benchmark,
            "summary": {
                "total": len(self.benchmarks),
                "completed": sum(
                    1 for b in self.benchmarks.values() if b.status == "completed"
                ),
                "failed": sum(
                    1 for b in self.benchmarks.values() if b.status == "failed"
                ),
                "running": sum(
                    1 for b in self.benchmarks.values() if b.status == "running"
                ),
                "pending": sum(
                    1 for b in self.benchmarks.values() if b.status == "pending"
                ),
                "skipped": sum(
                    1 for b in self.benchmarks.values() if b.status == "skipped"
                ),
            },
            "benchmarks": {
                bid: {
                    "config_path": b.config_path,
                    "project_id": b.project_id,
                    "status": b.status,
                    "started_at": b.started_at,
                    "completed_at": b.completed_at,
                    "duration_seconds": b.duration_seconds,
                    "error": b.error,
                }
                for bid, b in self.benchmarks.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SuiteState":
        """Load state from dictionary."""
        benchmarks = {}
        for bid, bdata in data.get("benchmarks", {}).items():
            benchmarks[bid] = BenchmarkState(
                benchmark_id=bid,
                config_path=bdata.get("config_path", ""),
                project_id=bdata.get("project_id", ""),
                status=bdata.get("status", "pending"),
                started_at=bdata.get("started_at"),
                completed_at=bdata.get("completed_at"),
                duration_seconds=bdata.get("duration_seconds"),
                error=bdata.get("error"),
            )
        return cls(
            suite_name=data.get("suite_name", ""),
            suite_version=data.get("suite_version", ""),
            run_tag=data.get("run_tag", ""),
            started_at=data.get("started_at", ""),
            updated_at=data.get("updated_at", ""),
            completed_at=data.get("completed_at", ""),
            status=data.get("status", "pending"),
            current_benchmark=data.get("current_benchmark"),
            benchmarks=benchmarks,
        )


class SuiteStateManager:
    """Manages persistent state for suite runs."""

    def __init__(self, suite_path: Path):
        """Initialize state manager.

        Args:
            suite_path: Path to the suite directory
        """
        self.suite_path = suite_path
        self.state_dir = suite_path / ".benchkit"
        self.state_file = self.state_dir / "state.json"
        self._lock = threading.Lock()  # Thread-safe for parallel execution

    def ensure_state_dir(self) -> None:
        """Create state directory if it doesn't exist."""
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> SuiteState | None:
        """Load state from disk.

        Returns:
            SuiteState if exists, None otherwise
        """
        if not self.state_file.exists():
            return None
        try:
            with open(self.state_file, encoding="utf-8") as f:
                data = json.load(f)
            return SuiteState.from_dict(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load state: {e}[/yellow]")
            return None

    def save_state(self, state: SuiteState) -> None:
        """Save state to disk (thread-safe).

        Args:
            state: State to save
        """
        with self._lock:
            self._save_unlocked(state)

    def _save_unlocked(self, state: SuiteState) -> None:
        """Save state without acquiring lock (internal use only)."""
        self.ensure_state_dir()
        state.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

    def update_benchmark_status(
        self,
        state: SuiteState,
        benchmark_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Atomically update a single benchmark's status (thread-safe).

        Args:
            state: Suite state to update
            benchmark_id: ID of the benchmark to update
            status: New status (running, completed, failed, etc.)
            error: Optional error message if failed
        """
        with self._lock:
            if benchmark_id not in state.benchmarks:
                return

            bench = state.benchmarks[benchmark_id]
            bench.status = status  # type: ignore[assignment]

            if status == "running":
                bench.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            elif status in ("completed", "failed"):
                bench.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                # Calculate duration if started_at is set
                if bench.started_at:
                    try:
                        start = time.strptime(bench.started_at, "%Y-%m-%dT%H:%M:%SZ")
                        end = time.strptime(bench.completed_at, "%Y-%m-%dT%H:%M:%SZ")
                        bench.duration_seconds = time.mktime(end) - time.mktime(start)
                    except ValueError:
                        pass  # Skip duration calculation on parse errors

            if error:
                bench.error = error

            self._save_unlocked(state)

    def clear_state(self) -> None:
        """Clear all state files."""
        if self.state_file.exists():
            self.state_file.unlink()


# =============================================================================
# Suite Runner
# =============================================================================


class SuiteRunner:
    """Orchestrates execution of benchmark suites.

    This is a thin wrapper around BenchmarkRunner that handles:
    - Discovery of benchmark configs in series directories
    - State management for resume capability
    - Sequential or parallel execution of benchmarks
    - Report generation across all benchmarks
    """

    def __init__(self, suite_path: Path, config: SuiteConfig):
        """Initialize suite runner.

        Args:
            suite_path: Path to suite directory
            config: Loaded suite configuration
        """
        self.suite_path = suite_path
        self.config = config
        self.state_manager = SuiteStateManager(suite_path)
        self._discovered_configs: dict[str, list[Path]] = {}

    def _resolve_results_dir(self, project_id: str) -> Path:
        """Resolve results directory for a project.

        If results_dir is configured, resolves relative to suite directory.
        Otherwise falls back to CWD-relative ``results/`` for backward compatibility.
        """
        if self.config.results_dir:
            return self.suite_path / self.config.results_dir / project_id
        return Path("results") / project_id

    def discover_configs(
        self, series_filter: str | None = None, include_disabled: bool = False
    ) -> dict[str, list[Path]]:
        """Discover benchmark configurations in the suite.

        Args:
            series_filter: Optional series name to filter by
            include_disabled: Include disabled series in discovery

        Returns:
            Dict mapping series name to list of config paths, sorted alphabetically
        """
        if self._discovered_configs:
            if series_filter:
                return {
                    k: v
                    for k, v in self._discovered_configs.items()
                    if k == series_filter
                }
            return self._discovered_configs

        series_dir = self.suite_path / "series"
        if not series_dir.exists():
            # Check if configs are directly in suite directory
            series_dir = self.suite_path

        discovered: dict[str, list[Path]] = {}

        # If series have custom paths configured, use those directly
        if self.config.series:
            for series_key, series_config in sorted(self.config.series.items()):
                if not series_config.enabled and not include_disabled:
                    continue

                if series_config.path:
                    # Custom path: resolve relative to suite root
                    config_dir = self.suite_path / series_config.path
                else:
                    # Default: use series key as directory name under series_dir
                    config_dir = series_dir / series_key

                if config_dir.is_dir():
                    configs = sorted(config_dir.glob("*.yaml"))
                    if configs:
                        discovered[series_key] = configs

        # Also discover any series directories not explicitly configured
        if series_dir.is_dir():
            for entry in sorted(series_dir.iterdir()):
                if not entry.is_dir():
                    continue
                if entry.name.startswith("."):
                    continue

                series_name = entry.name

                # Skip already-discovered series
                if series_name in discovered:
                    continue

                # Skip if series are explicitly configured and this one isn't listed
                if self.config.series and series_name not in self.config.series:
                    continue

                # Skip disabled series (they were intentionally skipped above)
                if self.config.series and series_name in self.config.series:
                    series_cfg = self.config.series[series_name]
                    if not series_cfg.enabled and not include_disabled:
                        continue

                # Find yaml configs in series directory
                configs = sorted(entry.glob("*.yaml"))
                if configs:
                    discovered[series_name] = configs

        self._discovered_configs = discovered

        if series_filter:
            return {k: v for k, v in discovered.items() if k == series_filter}
        return discovered

    def get_benchmark_id(self, series_name: str, config_path: Path) -> str:
        """Generate benchmark ID from series and config path.

        Args:
            series_name: Name of the series
            config_path: Path to the config file

        Returns:
            Benchmark ID like "01_node_scaling/nodes_04"
        """
        return f"{series_name}/{config_path.stem}"

    def get_config_path(self, series_name: str, config_name: str) -> Path | None:
        """Get the config file path from series and config names.

        Args:
            series_name: Name of the series (e.g., "series_1_nodes")
            config_name: Name of the config file without extension (e.g., "nodes_1")

        Returns:
            Path to the config file, or None if not found
        """
        # Check if series has a custom path configured
        series_config = self.config.series.get(series_name)
        if series_config and series_config.path:
            config_path = self.suite_path / series_config.path / f"{config_name}.yaml"
            if config_path.exists():
                return config_path

        # Try series subdirectory first
        series_dir = self.suite_path / "series"
        if not series_dir.exists():
            series_dir = self.suite_path

        config_path = series_dir / series_name / f"{config_name}.yaml"
        if config_path.exists():
            return config_path

        return None

    def run(
        self,
        series: str | None = None,
        benchmark: str | None = None,
        resume: bool = False,
        parallel: int = 1,
        dry_run: bool = False,
        no_cleanup: bool = False,
        tag: str = "",
        systems: str | None = None,
    ) -> bool:
        """Execute benchmarks in the suite.

        Args:
            series: Run only this series
            benchmark: Run only this specific benchmark (format: "series/config_name")
            resume: Skip completed benchmarks
            parallel: Number of concurrent benchmarks (1 = sequential)
            dry_run: Show plan without executing
            no_cleanup: Keep infrastructure after each benchmark
            tag: Tag for this run (useful for contributing results)
            systems: Comma-separated list of systems to run

        Returns:
            True if all benchmarks succeeded, False otherwise
        """
        # Discover configs
        discovered = self.discover_configs(series)

        if not discovered:
            console.print("[yellow]No benchmark configurations found in suite[/yellow]")
            return False

        # Handle single benchmark
        if benchmark:
            return self._run_single_benchmark(
                benchmark, resume, dry_run, no_cleanup, tag, systems, parallel
            )

        # Initialize or load state
        state = self._init_state(discovered, resume, tag)

        # Auto-sync state from results on disk when resuming
        if resume and not dry_run:
            synced = self._sync_state_from_results(state, discovered)
            if synced > 0:
                console.print(
                    f"[green]Auto-synced {synced} benchmark(s) from results[/green]\n"
                )

        # Parse systems filter once for reuse
        system_names_filter: list[str] | None = None
        if systems:
            system_names_filter = [s.strip() for s in systems.split(",")]

        # Header
        if dry_run:
            console.print(
                f"\n[bold blue]DRY RUN - Suite: {self.config.name}[/bold blue]"
            )
            console.print("[dim]No benchmarks will be executed[/dim]")
        else:
            console.print(f"\n[bold blue]Running suite: {self.config.name}[/bold blue]")
        console.print(f"[dim]Version: {self.config.version}[/dim]")
        if tag:
            console.print(f"[dim]Tag: {tag}[/dim]")

        # Show active filters in dry-run mode
        if dry_run:
            filters = []
            if series:
                filters.append(f"series={series}")
            if systems:
                filters.append(f"systems={systems}")
            if resume:
                filters.append("resume=true")
            if parallel > 1:
                filters.append(f"parallel={parallel}")
            if filters:
                console.print(f"[dim]Filters: {', '.join(filters)}[/dim]")

        console.print()

        if not dry_run:
            state.status = "running"
            state.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.state_manager.save_state(state)

        # Branch for parallel execution
        if parallel > 1 and not dry_run:
            return self._run_parallel(
                discovered, state, parallel, no_cleanup, system_names_filter, resume
            )

        all_success = True
        total_benchmarks = sum(len(configs) for configs in discovered.values())
        completed_count = 0
        skipped_count = 0
        would_run_count = 0

        for series_name in sorted(discovered.keys()):
            configs = discovered[series_name]
            series_config = self.config.series.get(
                series_name, SeriesConfig(name=series_name)
            )

            console.print(
                f"\n[bold magenta]Series: {series_config.name}[/bold magenta]"
            )
            if series_config.description:
                console.print(f"[dim]{series_config.description}[/dim]")

            for config_path in configs:
                benchmark_id = self.get_benchmark_id(series_name, config_path)
                completed_count += 1

                # Check if should skip
                if resume and benchmark_id in state.benchmarks:
                    bench_state = state.benchmarks[benchmark_id]
                    if bench_state.status == "completed":
                        console.print(
                            f"  [dim]Skipping (completed): {benchmark_id}[/dim]"
                        )
                        skipped_count += 1
                        continue

                # Show what would run with config details
                cfg = None
                details = ""
                verbose_info = ""
                try:
                    cfg = load_config(str(config_path))
                    systems_list = cfg.get("systems", [])

                    # Filter systems if --systems is specified
                    if system_names_filter:
                        systems_list = [
                            s
                            for s in systems_list
                            if s.get("name") in system_names_filter
                        ]
                        if not systems_list:
                            # No matching systems, show as skipped
                            if dry_run:
                                console.print(
                                    f"  [dim]Skipping: {benchmark_id} "
                                    f"(no matching systems)[/dim]"
                                )
                            skipped_count += 1
                            continue

                    num_systems = len(systems_list)
                    workload = cfg.get("workload", {})
                    workload_name = workload.get("name", "?")
                    sf = workload.get("scale_factor", "?")
                    streams = (workload.get("multiuser") or {}).get("num_streams", 1)
                    node_count = 1
                    if systems_list:
                        node_count = (
                            systems_list[0].get("setup", {}).get("node_count", 1)
                        )

                    # Build details string
                    details = f"{workload_name} SF{sf}, {num_systems} systems"
                    if node_count > 1:
                        details += f", {node_count} nodes"
                    if streams > 1:
                        details += f", {streams} streams"

                    # Build verbose info (env, kinds, instances)
                    env_modes: set[str] = set()
                    instance_types: set[str] = set()

                    # Legacy format
                    env = cfg.get("env") or {}
                    if env.get("mode"):
                        env_modes.add(env["mode"])
                    instances_config = env.get("instances") or {}
                    for sys in systems_list:
                        sys_name = sys.get("name", "")
                        if sys_name in instances_config:
                            inst_type = instances_config[sys_name].get("instance_type")
                            if inst_type:
                                instance_types.add(inst_type)

                    # New environments format
                    environments = cfg.get("environments") or {}
                    for sys in systems_list:
                        sys_env_name = sys.get("environment")
                        if sys_env_name and sys_env_name in environments:
                            sys_env_cfg = environments[sys_env_name]
                            if isinstance(sys_env_cfg, dict):
                                if sys_env_cfg.get("mode"):
                                    env_modes.add(sys_env_cfg["mode"])
                                if sys_env_cfg.get("instance_type"):
                                    instance_types.add(sys_env_cfg["instance_type"])
                        # Also check setup.instance_type (managed systems)
                        setup = sys.get("setup") or {}
                        if setup.get("instance_type"):
                            instance_types.add(setup["instance_type"])

                    # System kinds
                    kinds = sorted({s.get("kind", "?") for s in systems_list})

                    env_str = ", ".join(sorted(env_modes)) if env_modes else "local"
                    kinds_str = ", ".join(kinds)
                    inst_str = (
                        ", ".join(sorted(instance_types)) if instance_types else "-"
                    )
                    verbose_info = (
                        f"env: {env_str} | kinds: {kinds_str} | instances: {inst_str}"
                    )
                except Exception:
                    pass

                if dry_run:
                    console.print(
                        f"\n  [{completed_count}/{total_benchmarks}] "
                        f"[cyan]Would run: {benchmark_id}[/cyan]"
                    )
                    if details:
                        console.print(f"    {details}")
                    if verbose_info:
                        console.print(f"    [dim]{verbose_info}[/dim]")
                    would_run_count += 1
                    continue

                console.print(
                    f"\n  [{completed_count}/{total_benchmarks}] "
                    f"[cyan]Running: {benchmark_id}[/cyan]"
                )

                # Update state
                state.current_benchmark = benchmark_id
                bench_state_opt = state.benchmarks.get(benchmark_id)
                if bench_state_opt:
                    bench_state_opt.status = "running"
                    bench_state_opt.started_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                self.state_manager.save_state(state)

                # Run benchmark
                success = self._run_benchmark(
                    config_path, no_cleanup=no_cleanup, systems=systems
                )

                # Update state
                if bench_state_opt:
                    bench_state_opt.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    if bench_state_opt.started_at:
                        start = time.strptime(
                            bench_state_opt.started_at, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        end = time.strptime(
                            bench_state_opt.completed_at, "%Y-%m-%dT%H:%M:%SZ"
                        )
                        bench_state_opt.duration_seconds = time.mktime(
                            end
                        ) - time.mktime(start)
                    bench_state_opt.status = "completed" if success else "failed"
                    if not success:
                        bench_state_opt.error = "Benchmark execution failed"
                self.state_manager.save_state(state)

                if success:
                    console.print(f"    [green]✓ Completed: {benchmark_id}[/green]")
                else:
                    console.print(f"    [red]✗ Failed: {benchmark_id}[/red]")
                    all_success = False
                    if not self.config.execution.continue_on_failure:
                        break

                # Pause between benchmarks
                if (
                    self.config.execution.pause_between > 0
                    and completed_count < total_benchmarks
                ):
                    console.print(
                        f"    [dim]Waiting {self.config.execution.pause_between}s...[/dim]"
                    )
                    time.sleep(self.config.execution.pause_between)

            if not dry_run and not all_success:
                if not self.config.execution.continue_on_failure:
                    break

        # Summary
        if dry_run:
            console.print()
            mode_str = (
                f"parallel ({parallel} workers)" if parallel > 1 else "sequential"
            )
            console.print(
                f"[bold]Dry run summary:[/bold] "
                f"{would_run_count} would run | {skipped_count} would skip"
            )
            console.print(f"[dim]Execution mode: {mode_str}[/dim]")
            return True

        # Final state update
        state.status = "completed" if all_success else "failed"
        state.current_benchmark = None
        self.state_manager.save_state(state)

        return all_success

    def _init_state(
        self, discovered: dict[str, list[Path]], resume: bool, tag: str
    ) -> SuiteState:
        """Initialize or load suite state.

        Always loads existing state to preserve entries for series not being
        run.  The ``resume`` flag controls only whether *discovered* benchmarks
        keep their previous status (resume=True → skip completed) or are reset
        to pending (resume=False → re-run).

        Args:
            discovered: Discovered configurations
            resume: Whether to resume from existing state
            tag: Run tag

        Returns:
            SuiteState object
        """
        # Always try to load existing state to preserve other series
        existing_state = self.state_manager.load_state()

        if existing_state:
            # Merge discovered benchmarks into the existing state
            for series_name, configs in discovered.items():
                for config_path in configs:
                    benchmark_id = self.get_benchmark_id(series_name, config_path)
                    if benchmark_id not in existing_state.benchmarks:
                        try:
                            cfg = load_config(str(config_path))
                            project_id = cfg.get("project_id", config_path.stem)
                        except Exception:
                            project_id = config_path.stem

                        existing_state.benchmarks[benchmark_id] = BenchmarkState(
                            benchmark_id=benchmark_id,
                            config_path=str(config_path),
                            project_id=project_id,
                            status="pending",
                        )
                    elif not resume:
                        # Not resuming: reset discovered benchmarks to pending
                        existing_state.benchmarks[benchmark_id].status = "pending"
                        existing_state.benchmarks[benchmark_id].started_at = None
                        existing_state.benchmarks[benchmark_id].completed_at = None
                        existing_state.benchmarks[benchmark_id].duration_seconds = None
                        existing_state.benchmarks[benchmark_id].error = None

            if tag:
                existing_state.run_tag = tag
            return existing_state

        # No existing state — create new (first run)
        state = SuiteState(
            suite_name=self.config.name,
            suite_version=self.config.version,
            run_tag=tag,
            status="pending",
        )

        for series_name, configs in discovered.items():
            for config_path in configs:
                benchmark_id = self.get_benchmark_id(series_name, config_path)
                try:
                    cfg = load_config(str(config_path))
                    project_id = cfg.get("project_id", config_path.stem)
                except Exception:
                    project_id = config_path.stem

                state.benchmarks[benchmark_id] = BenchmarkState(
                    benchmark_id=benchmark_id,
                    config_path=str(config_path),
                    project_id=project_id,
                    status="pending",
                )

        return state

    def _sync_state_from_results(
        self,
        state: SuiteState,
        discovered: dict[str, list[Path]],
    ) -> int:
        """Auto-sync benchmark states from results on disk.

        Checks each non-terminal benchmark for a runs.csv in its results
        directory. If found, upgrades the state to "completed" so that
        resume runs skip it and status displays reflect reality.

        Args:
            state: Current suite state (modified in place)
            discovered: Discovered configurations by series name

        Returns:
            Number of benchmarks that were upgraded to completed
        """
        synced = 0

        for series_name, configs in discovered.items():
            for config_path in configs:
                benchmark_id = self.get_benchmark_id(series_name, config_path)
                bench_state = state.benchmarks.get(benchmark_id)
                if bench_state is None:
                    continue

                # Only sync non-terminal states
                if bench_state.status in ("completed", "skipped"):
                    continue

                # Get project_id (already stored in state, fallback to config)
                project_id = bench_state.project_id
                if not project_id:
                    try:
                        cfg = load_config(str(config_path))
                        project_id = cfg.get("project_id", config_path.stem)
                    except Exception:
                        project_id = config_path.stem

                runs_csv = self._resolve_results_dir(project_id) / "runs.csv"
                if runs_csv.exists():
                    bench_state.status = "completed"
                    bench_state.error = None
                    bench_state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    console.print(f"  Auto-synced (results found): {benchmark_id}")
                    synced += 1

        if synced > 0:
            self.state_manager.save_state(state)

        return synced

    def _run_single_benchmark(
        self,
        benchmark: str,
        resume: bool,
        dry_run: bool,
        no_cleanup: bool,
        tag: str,
        systems: str | None,
        parallel: int = 1,
    ) -> bool:
        """Run a single specific benchmark.

        Args:
            benchmark: Benchmark ID in format "series/config_name"
            resume: Skip if already completed
            dry_run: Show plan only
            no_cleanup: Keep infrastructure
            tag: Run tag
            systems: Systems to run
            parallel: Number of parallel workers (for display only)

        Returns:
            True if successful
        """
        parts = benchmark.split("/")
        if len(parts) != 2:
            console.print(
                f"[red]Invalid benchmark format: {benchmark}. "
                f"Use 'series_name/config_name'[/red]"
            )
            return False

        series_name, config_name = parts
        discovered = self.discover_configs(series_name)

        if series_name not in discovered:
            console.print(f"[red]Series not found: {series_name}[/red]")
            return False

        config_path = None
        for path in discovered[series_name]:
            if path.stem == config_name:
                config_path = path
                break

        if not config_path:
            console.print(
                f"[red]Config not found: {config_name} in series {series_name}[/red]"
            )
            return False

        if dry_run:
            console.print(
                f"\n[bold blue]DRY RUN - Suite: {self.config.name}[/bold blue]"
            )
            console.print("[dim]No benchmarks will be executed[/dim]")
            console.print(f"[dim]Version: {self.config.version}[/dim]")

            # Show active filters
            filters = []
            filters.append(f"benchmark={benchmark}")
            if systems:
                filters.append(f"systems={systems}")
            if resume:
                filters.append("resume=true")
            console.print(f"[dim]Filters: {', '.join(filters)}[/dim]")
            console.print()

            # Load config and show details
            try:
                cfg = load_config(str(config_path))
                systems_list = cfg.get("systems", [])

                # Filter systems if --systems is specified
                if systems:
                    system_names_filter = [s.strip() for s in systems.split(",")]
                    systems_list = [
                        s for s in systems_list if s.get("name") in system_names_filter
                    ]
                    if not systems_list:
                        console.print(
                            f"  [dim]Skipping: {benchmark} (no matching systems)[/dim]"
                        )
                        console.print()
                        console.print(
                            "[bold]Dry run summary:[/bold] 0 would run | 1 would skip"
                        )
                        return True

                num_systems = len(systems_list)
                workload = cfg.get("workload", {})
                workload_name = workload.get("name", "?")
                sf = workload.get("scale_factor", "?")
                streams = (workload.get("multiuser") or {}).get("num_streams", 1)
                node_count = 1
                if systems_list:
                    node_count = systems_list[0].get("setup", {}).get("node_count", 1)

                # Build details string
                details = f"{workload_name} SF{sf}, {num_systems} systems"
                if node_count > 1:
                    details += f", {node_count} nodes"
                if streams > 1:
                    details += f", {streams} streams"

                # Build verbose info
                env_modes: set[str] = set()
                instance_types: set[str] = set()

                env = cfg.get("env") or {}
                if env.get("mode"):
                    env_modes.add(env["mode"])
                instances_config = env.get("instances") or {}
                for sys in systems_list:
                    sys_name = sys.get("name", "")
                    if sys_name in instances_config:
                        inst_type = instances_config[sys_name].get("instance_type")
                        if inst_type:
                            instance_types.add(inst_type)

                environments = cfg.get("environments") or {}
                for sys in systems_list:
                    sys_env_name = sys.get("environment")
                    if sys_env_name and sys_env_name in environments:
                        sys_env_cfg = environments[sys_env_name]
                        if isinstance(sys_env_cfg, dict):
                            if sys_env_cfg.get("mode"):
                                env_modes.add(sys_env_cfg["mode"])
                            if sys_env_cfg.get("instance_type"):
                                instance_types.add(sys_env_cfg["instance_type"])
                    setup = sys.get("setup") or {}
                    if setup.get("instance_type"):
                        instance_types.add(setup["instance_type"])

                kinds = sorted({s.get("kind", "?") for s in systems_list})
                env_str = ", ".join(sorted(env_modes)) if env_modes else "local"
                kinds_str = ", ".join(kinds)
                inst_str = ", ".join(sorted(instance_types)) if instance_types else "-"
                verbose_info = (
                    f"env: {env_str} | kinds: {kinds_str} | instances: {inst_str}"
                )

                console.print(f"  [1/1] [cyan]Would run: {benchmark}[/cyan]")
                console.print(f"    {details}")
                console.print(f"    [dim]{verbose_info}[/dim]")
            except Exception:
                console.print(f"  [1/1] [cyan]Would run: {benchmark}[/cyan]")
                console.print(f"    [dim]Config: {config_path}[/dim]")

            console.print()
            mode_str = (
                f"parallel ({parallel} workers)" if parallel > 1 else "sequential"
            )
            console.print("[bold]Dry run summary:[/bold] 1 would run | 0 would skip")
            console.print(f"[dim]Execution mode: {mode_str}[/dim]")
            return True

        console.print(f"\n[cyan]Running benchmark: {benchmark}[/cyan]")
        return self._run_benchmark(config_path, no_cleanup=no_cleanup, systems=systems)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to filesystem-safe slug.

        Args:
            text: Text to slugify

        Returns:
            Lowercase string with spaces/special chars replaced by underscores
        """
        import re

        # Lowercase and replace non-alphanumeric with underscores
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        # Remove leading/trailing underscores
        return slug.strip("_")

    def _build_parallel_tasks(
        self,
        discovered: dict[str, list[Path]],
        state: SuiteState,
        no_cleanup: bool,
        systems_filter: list[str] | None,
        resume: bool,
    ) -> list:
        """Build list of SuiteBenchmarkTask from discovered configs.

        Handles resume-skip, systems filtering, and absolute path resolution.
        Config paths are made absolute because InfraManager uses os.chdir()
        which is not thread-safe.

        Args:
            discovered: Discovered configurations by series
            state: Suite state for tracking progress
            no_cleanup: Keep infrastructure after each benchmark
            systems_filter: List of system names to filter
            resume: Whether to skip completed benchmarks

        Returns:
            List of SuiteBenchmarkTask ready for parallel execution
        """
        from .parallel_executor import SuiteBenchmarkTask

        tasks: list[SuiteBenchmarkTask] = []
        for series_name in sorted(discovered.keys()):
            for config_path in discovered[series_name]:
                config_path_abs = config_path.resolve()
                benchmark_id = self.get_benchmark_id(series_name, config_path)

                if resume and benchmark_id in state.benchmarks:
                    if state.benchmarks[benchmark_id].status == "completed":
                        console.print(
                            f"  [dim]Skipping (completed): {benchmark_id}[/dim]"
                        )
                        continue

                try:
                    cfg = load_config(str(config_path_abs))
                    project_id = cfg.get("project_id", config_path_abs.stem)

                    if systems_filter:
                        systems_list = cfg.get("systems", [])
                        matching = [
                            s for s in systems_list if s.get("name") in systems_filter
                        ]
                        if not matching:
                            console.print(
                                f"  [dim]Skipping (no matching systems): {benchmark_id}[/dim]"
                            )
                            continue
                except Exception:
                    project_id = config_path_abs.stem

                tasks.append(
                    SuiteBenchmarkTask(
                        benchmark_id=benchmark_id,
                        config_path=config_path_abs,
                        project_id=project_id,
                        no_cleanup=no_cleanup,
                        systems_filter=(
                            ",".join(systems_filter) if systems_filter else None
                        ),
                    )
                )
        return tasks

    def _make_run_with_state(self, state: SuiteState) -> Callable:
        """Create a run function that updates suite state on completion.

        Args:
            state: Suite state to update

        Returns:
            Function compatible with SuiteParallelExecutor.execute_benchmarks()
        """
        from .parallel_executor import SuiteBenchmarkTask

        def run_with_state(
            task: SuiteBenchmarkTask, log_callback: Callable[[str], None]
        ) -> bool:
            self.state_manager.update_benchmark_status(
                state, task.benchmark_id, "running"
            )
            log_callback(f"State updated: {task.benchmark_id} -> running")

            success = self._run_benchmark(
                task.config_path,
                no_cleanup=task.no_cleanup,
                systems=task.systems_filter,
                log_callback=log_callback,
            )

            status = "completed" if success else "failed"
            self.state_manager.update_benchmark_status(state, task.benchmark_id, status)
            log_callback(f"State updated: {task.benchmark_id} -> {status}")
            return success

        return run_with_state

    def _run_parallel(
        self,
        discovered: dict[str, list[Path]],
        state: SuiteState,
        parallel: int,
        no_cleanup: bool,
        systems_filter: list[str] | None,
        resume: bool,
    ) -> bool:
        """Execute all benchmarks in a flat parallel pool.

        Args:
            discovered: Discovered configurations by series
            state: Suite state for tracking progress
            parallel: Number of concurrent workers
            no_cleanup: Keep infrastructure after each benchmark
            systems_filter: List of system names to filter
            resume: Whether to skip completed benchmarks

        Returns:
            True if all benchmarks succeeded
        """
        # Dispatch to parallel_series mode if configured
        if self.config.execution.mode == "parallel_series":
            return self._run_parallel_series(
                discovered, state, parallel, no_cleanup, systems_filter, resume
            )

        from .parallel_executor import SuiteParallelExecutor

        tasks = self._build_parallel_tasks(
            discovered, state, no_cleanup, systems_filter, resume
        )

        if not tasks:
            console.print("[yellow]No benchmarks to run[/yellow]")
            state.status = "completed"
            state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.state_manager.save_state(state)
            return True

        console.print(
            f"\n[bold]Running {len(tasks)} benchmarks with {parallel} workers[/bold]\n"
        )

        run_timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
        suite_slug = self._slugify(self.config.name)
        log_dir = (
            self._resolve_results_dir(suite_slug) / "logs" / f"run_{run_timestamp}"
        ).resolve()

        executor = SuiteParallelExecutor(
            max_workers=parallel,
            log_dir=log_dir,
            console=console,
        )

        total_timeout = (
            self.config.timeouts.infrastructure
            + self.config.timeouts.benchmark
            + self.config.timeouts.cleanup
        )

        results = executor.execute_benchmarks(
            tasks=tasks,
            run_func=self._make_run_with_state(state),
            continue_on_failure=self.config.execution.continue_on_failure,
            benchmark_timeout=total_timeout,
        )

        # Final state update
        completed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)

        state.status = "completed" if failed == 0 else "failed"
        state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state_manager.save_state(state)

        console.print(
            f"\n[bold]Suite completed: {completed} succeeded, {failed} failed[/bold]"
        )

        return failed == 0

    def _run_parallel_series(
        self,
        discovered: dict[str, list[Path]],
        state: SuiteState,
        parallel: int,
        no_cleanup: bool,
        systems_filter: list[str] | None,
        resume: bool,
    ) -> bool:
        """Execute series sequentially, benchmarks within each series in parallel.

        Args:
            discovered: Discovered configurations by series
            state: Suite state for tracking progress
            parallel: Number of concurrent workers per series
            no_cleanup: Keep infrastructure after each benchmark
            systems_filter: List of system names to filter
            resume: Whether to skip completed benchmarks

        Returns:
            True if all benchmarks succeeded
        """
        from .parallel_executor import SuiteParallelExecutor

        all_success = True
        total_timeout = (
            self.config.timeouts.infrastructure
            + self.config.timeouts.benchmark
            + self.config.timeouts.cleanup
        )
        run_with_state = self._make_run_with_state(state)

        run_timestamp = time.strftime("%Y-%m-%dT%H-%M-%S")
        suite_slug = self._slugify(self.config.name)

        for series_name in sorted(discovered.keys()):
            console.print(f"\n[bold magenta]Series: {series_name}[/bold magenta]")

            # Build tasks for THIS series only
            series_discovered = {series_name: discovered[series_name]}
            tasks = self._build_parallel_tasks(
                series_discovered, state, no_cleanup, systems_filter, resume
            )
            if not tasks:
                console.print(f"  [dim]No benchmarks to run in {series_name}[/dim]")
                continue

            console.print(
                f"  [bold]Running {len(tasks)} benchmarks "
                f"with {parallel} workers[/bold]\n"
            )

            log_dir = (
                self._resolve_results_dir(suite_slug)
                / "logs"
                / f"run_{run_timestamp}"
                / series_name
            ).resolve()

            executor = SuiteParallelExecutor(
                max_workers=parallel,
                log_dir=log_dir,
                console=console,
            )

            results = executor.execute_benchmarks(
                tasks=tasks,
                run_func=run_with_state,
                continue_on_failure=self.config.execution.continue_on_failure,
                benchmark_timeout=total_timeout,
            )

            if any(not v for v in results.values()):
                all_success = False
                if not self.config.execution.continue_on_failure:
                    console.print(
                        f"[red]Series {series_name} had failures, stopping[/red]"
                    )
                    break

            # Pause between series
            if self.config.execution.pause_between > 0:
                remaining_series = sorted(discovered.keys())
                is_last = series_name == remaining_series[-1]
                if not is_last:
                    console.print(
                        f"[dim]Pausing {self.config.execution.pause_between}s "
                        f"between series...[/dim]"
                    )
                    time.sleep(self.config.execution.pause_between)

        # Final state update
        state.status = "completed" if all_success else "failed"
        state.completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state_manager.save_state(state)

        total = sum(len(configs) for configs in discovered.values())
        status_word = "succeeded" if all_success else "completed with failures"
        console.print(f"\n[bold]Suite {status_word} ({total} benchmarks)[/bold]")

        return all_success

    @staticmethod
    def _log(msg: str, log_callback: Callable[[str], None] | None) -> None:
        """Log a message via callback or console."""
        if log_callback:
            log_callback(msg)
        else:
            console.print(msg)

    def _run_benchmark(
        self,
        config_path: Path,
        no_cleanup: bool = False,
        systems: str | None = None,
        log_callback: Callable[[str], None] | None = None,
    ) -> bool:
        """Execute a single benchmark using BenchmarkRunner.

        Enforces suite-level timeouts between phases:
        - infrastructure timeout: max time for Phase 0 (cloud provisioning)
        - benchmark timeout: max time for Phases 1-3 combined (setup + load + queries)
        - cleanup timeout: max time for infrastructure teardown

        Timeouts are checked between phases (cooperative), not mid-phase.

        Args:
            config_path: Path to benchmark config
            no_cleanup: Keep infrastructure
            systems: Comma-separated systems to run
            log_callback: Optional callback for routing log messages (for parallel execution)

        Returns:
            True if successful
        """
        cfg = None
        has_cloud = False
        benchmark_success = False

        infra_timeout = self.config.timeouts.infrastructure
        benchmark_timeout = self.config.timeouts.benchmark
        cleanup_timeout = self.config.timeouts.cleanup

        try:
            cfg = load_config(str(config_path))

            # Filter systems if specified
            if systems:
                system_names = [s.strip() for s in systems.split(",")]
                cfg["systems"] = [
                    s for s in cfg["systems"] if s["name"] in system_names
                ]
                if not cfg["systems"]:
                    self._log(
                        f"[red]No matching systems found for: {system_names}[/red]",
                        log_callback,
                    )
                    return False

            project_id = cfg.get("project_id", config_path.stem)
            outdir = self._resolve_results_dir(project_id)
            outdir.mkdir(parents=True, exist_ok=True)

            runner = BenchmarkRunner(cfg, outdir, log_callback=log_callback)

            # Check if config uses sequential (per-system lifecycle) mode
            exec_config = cfg.get("execution", {})
            is_sequential = exec_config.get("sequential", False)

            if is_sequential:
                is_parallel_exec = exec_config.get("parallel", False)

                try:
                    from ..cli.workflows import run_probe_for_full

                    probe_fn = run_probe_for_full
                except ImportError:
                    probe_fn = None

                if is_parallel_exec:
                    benchmark_success = runner.run_parallel_sequential(
                        run_probe_fn=probe_fn,
                    )
                else:
                    benchmark_success = runner.run_sequential(
                        run_probe_fn=probe_fn,
                    )
                return benchmark_success

            has_cloud = is_any_system_cloud_mode(cfg)
            has_managed = is_any_system_managed_mode(cfg)

            # Phase 0: Infrastructure
            phase_start = time.monotonic()
            if has_cloud or has_managed:
                if has_cloud:
                    if not runner.ensure_cloud_infrastructure(log_callback):
                        return False
                # Managed infrastructure is handled in setup

            elapsed = time.monotonic() - phase_start
            if elapsed > infra_timeout:
                self._log(
                    f"[red]Infrastructure phase exceeded timeout "
                    f"({elapsed:.0f}s > {infra_timeout}s)[/red]",
                    log_callback,
                )
                return False

            # Probe phase (non-fatal, matches run --full behavior)
            self._log("[blue]Running system probe...[/blue]", log_callback)
            try:
                from ..cli.workflows import run_probe_for_full

                run_probe_for_full(cfg, outdir)
            except Exception as e:
                self._log(
                    f"[yellow]Warning: Probe failed (continuing): {e}[/yellow]",
                    log_callback,
                )

            # Phases 1-3 share the benchmark timeout
            benchmark_start = time.monotonic()

            # Phase 1: Setup
            if not runner.run_setup(force=True):
                return False
            elapsed = time.monotonic() - benchmark_start
            if elapsed > benchmark_timeout:
                self._log(
                    f"[red]Benchmark exceeded timeout after setup "
                    f"({elapsed:.0f}s > {benchmark_timeout}s)[/red]",
                    log_callback,
                )
                return False

            # Phase 2: Load
            if not runner.run_load(force=True):
                return False
            elapsed = time.monotonic() - benchmark_start
            if elapsed > benchmark_timeout:
                self._log(
                    f"[red]Benchmark exceeded timeout after load "
                    f"({elapsed:.0f}s > {benchmark_timeout}s)[/red]",
                    log_callback,
                )
                return False

            # Phase 3: Run queries
            if not runner.run_queries(force=True):
                return False

            benchmark_success = True
            return True

        except Exception as e:
            self._log(f"[red]Benchmark failed: {e}[/red]", log_callback)
            return False

        finally:
            # Infrastructure cleanup in finally block ensures it happens
            # regardless of success, failure, or exception
            if cfg is not None and not no_cleanup:
                should_cleanup = (
                    benchmark_success and self.config.infrastructure.cleanup_after_each
                ) or (
                    not benchmark_success
                    and self.config.infrastructure.cleanup_on_failure
                )
                if should_cleanup:
                    if has_cloud:
                        self._run_cleanup_with_timeout(
                            cfg, cleanup_timeout, log_callback
                        )
                    else:
                        # Local/Docker mode: teardown systems (stop containers)
                        self._teardown_local_systems(cfg, log_callback)

    def _run_cleanup_with_timeout(
        self,
        cfg: dict[str, Any],
        timeout: int,
        log_callback: Callable[[str], None] | None,
    ) -> None:
        """Run infrastructure cleanup with a timeout.

        Executes cleanup in a daemon thread so it can be abandoned if it hangs.
        """
        cleanup_error: list[str] = []

        def _do_cleanup() -> None:
            try:
                from ..common.cli_helpers import get_first_cloud_provider
                from ..common.enums import EnvironmentMode
                from ..infra.manager import InfraManager

                env = cfg.get("env") or {}
                provider = env.get("mode", "aws")
                if not EnvironmentMode.is_cloud_provider(provider):
                    provider = get_first_cloud_provider(cfg) or provider
                if EnvironmentMode.is_cloud_provider(provider):
                    manager = InfraManager(provider, cfg)
                    manager.destroy()
            except Exception as e:
                cleanup_error.append(str(e))

        cleanup_thread = threading.Thread(target=_do_cleanup, daemon=True)
        cleanup_thread.start()
        cleanup_thread.join(timeout=timeout)

        if cleanup_thread.is_alive():
            self._log(
                f"[yellow]Warning: infrastructure cleanup timed out "
                f"after {timeout}s — may need manual teardown[/yellow]",
                log_callback,
            )
        elif cleanup_error:
            self._log(
                f"[yellow]Warning: infrastructure cleanup failed: "
                f"{cleanup_error[0]}[/yellow]",
                log_callback,
            )

    def _teardown_local_systems(
        self,
        cfg: dict[str, Any],
        log_callback: Callable[[str], None] | None,
    ) -> None:
        """Teardown Docker containers for local-mode benchmarks."""
        from ..systems import create_system

        project_id = cfg.get("project_id", "")
        for system_config in cfg.get("systems", []):
            try:
                # Inject project_id so container_name matches the one used
                # during installation (e.g., "exasol_docker_cmp_full_exasol")
                system_config_copy = {**system_config, "project_id": project_id}
                system = create_system(system_config_copy)
                setup_method = system_config.get("setup", {}).get("method", "")
                if setup_method == "docker":
                    system.teardown()
            except Exception as e:
                self._log(
                    f"[yellow]Warning: cleanup failed for "
                    f"{system_config.get('name', '?')}: {e}[/yellow]",
                    log_callback,
                )

    def show_plan(
        self, discovered: dict[str, list[Path]], state: SuiteState | None = None
    ) -> None:
        """Display execution plan.

        Args:
            discovered: Discovered configurations
            state: Optional existing state for status display
        """
        console.print(
            f"\n[bold blue]Suite: {self.config.name} v{self.config.version}[/bold blue]"
        )
        if self.config.description:
            console.print(f"[dim]{self.config.description}[/dim]")
        console.print()

        total_configs = 0
        completed = 0
        pending = 0

        for series_name in sorted(discovered.keys()):
            configs = discovered[series_name]
            series_config = self.config.series.get(
                series_name, SeriesConfig(name=series_name)
            )

            enabled_str = "[green][ENABLED][/green]"
            if series_name in self.config.series and not series_config.enabled:
                enabled_str = "[yellow][DISABLED][/yellow]"

            # Show display name and series key (for CLI/filesystem reference)
            series_header = f"\n[bold magenta]{series_config.name}[/bold magenta]"
            if series_config.name != series_name:
                series_header += f" [dim]({series_name})[/dim]"
            series_header += f" {enabled_str}"
            console.print(series_header)
            if series_config.description:
                console.print(f"  [dim]{series_config.description}[/dim]")

            for config_path in configs:
                benchmark_id = self.get_benchmark_id(series_name, config_path)
                total_configs += 1

                status_icon = "[cyan]○ PENDING[/cyan]"
                if state and benchmark_id in state.benchmarks:
                    bench_state = state.benchmarks[benchmark_id]
                    if bench_state.status == "completed":
                        status_icon = "[green]✓ DONE[/green]"
                        completed += 1
                    elif bench_state.status == "running":
                        status_icon = "[yellow]▶ RUNNING[/yellow]"
                        pending += 1
                    elif bench_state.status == "failed":
                        status_icon = "[red]✗ FAILED[/red]"
                        pending += 1
                    else:
                        pending += 1
                else:
                    pending += 1

                # Try to load config for description
                try:
                    cfg = load_config(str(config_path))
                    project_id = cfg.get("project_id", config_path.stem)
                    description = f"{len(cfg.get('systems', []))} systems"
                    workload = cfg.get("workload", {})
                    if workload:
                        description += f" × SF{workload.get('scale_factor', '?')}"
                except Exception:
                    project_id = config_path.stem
                    description = ""

                project_suffix = ""
                if project_id != config_path.stem:
                    project_suffix = f"  [dim]→ {project_id}[/dim]"
                console.print(
                    f"    {status_icon}  {config_path.stem:20s}  "
                    f"{description}{project_suffix}"
                )

        console.print()
        console.print(
            f"[bold]Summary:[/bold] {completed}/{total_configs} completed | {pending} pending"
        )

    def show_status(self, verbose: bool = False) -> None:
        """Display current suite status with actual benchmark progress.

        Args:
            verbose: If True, show detailed per-system status for each benchmark
        """
        discovered = self.discover_configs(include_disabled=True)

        console.print(
            f"\n[bold blue]Suite: {self.config.name} v{self.config.version}[/bold blue]"
        )

        # Check suite state for run info
        state = self.state_manager.load_state()
        if state:
            synced = self._sync_state_from_results(state, discovered)
            if synced > 0:
                console.print(
                    f"[dim]Auto-synced {synced} benchmark(s) from results[/dim]"
                )
            console.print(f"[dim]Suite status: {state.status}[/dim]")
            if state.run_tag:
                console.print(f"[dim]Tag: {state.run_tag}[/dim]")
            if state.current_benchmark:
                console.print(f"[dim]Current: {state.current_benchmark}[/dim]")
        console.print()

        # Track totals
        total_configs = 0
        total_completed = 0
        total_partial = 0
        total_pending = 0
        total_failed_queries = 0

        for series_name in sorted(discovered.keys()):
            configs = discovered[series_name]
            series_config = self.config.series.get(
                series_name, SeriesConfig(name=series_name)
            )

            enabled_str = "[green][ENABLED][/green]"
            is_disabled = (
                series_name in self.config.series and not series_config.enabled
            )
            if is_disabled:
                enabled_str = "[yellow][DISABLED][/yellow]"

            # Show display name and series key (for CLI/filesystem reference)
            series_header = f"\n[bold magenta]{series_config.name}[/bold magenta]"
            if series_config.name != series_name:
                series_header += f" [dim]({series_name})[/dim]"
            series_header += f" {enabled_str}"
            console.print(series_header)

            # Create table for this series
            table = Table(show_header=True, header_style="bold")
            table.add_column("Config", style="cyan", no_wrap=True)
            table.add_column("Project", style="dim", no_wrap=True)
            table.add_column("State", justify="center")
            table.add_column("Infra", justify="center")
            table.add_column("Setup", justify="center")
            table.add_column("Load", justify="center")
            table.add_column("Run", justify="center")
            table.add_column("Details", overflow="fold")

            for config_path in configs:
                total_configs += 1
                config_name = config_path.stem
                benchmark_id = self.get_benchmark_id(series_name, config_path)

                # Get recorded state from state file
                state_cell = "[dim]-[/dim]"
                if state and benchmark_id in state.benchmarks:
                    bench_state = state.benchmarks[benchmark_id]
                    if bench_state.status == "completed":
                        state_cell = "[green]✓[/green]"
                    elif bench_state.status == "failed":
                        state_cell = "[red]✗[/red]"
                    elif bench_state.status == "skipped":
                        state_cell = "[dim]skip[/dim]"
                    elif bench_state.status == "running":
                        state_cell = "[yellow]▶[/yellow]"
                    else:
                        state_cell = "[dim]○[/dim]"

                # Load config to get project_id
                try:
                    cfg = load_config(str(config_path))
                    project_id = cfg.get("project_id", config_path.stem)
                except Exception:
                    project_id = config_path.stem

                if is_disabled:
                    table.add_row(
                        config_name,
                        project_id,
                        state_cell,
                        "[dim]-[/dim]",
                        "[dim]-[/dim]",
                        "[dim]-[/dim]",
                        "[dim]-[/dim]",
                        "[dim]series disabled[/dim]",
                    )
                    continue

                # Get actual status from results directory
                status_info = self._get_benchmark_status(config_path, verbose)
                results_dir = self._resolve_results_dir(project_id)
                has_run_results = (results_dir / "runs.csv").exists()

                if has_run_results:
                    # Benchmark completed its run (even if some queries failed)
                    total_completed += 1
                elif status_info["has_any_progress"]:
                    # Has results dir but no runs.csv - in progress
                    total_partial += 1
                else:
                    # No results at all
                    total_pending += 1

                total_failed_queries += status_info.get("failed_queries", 0)

                table.add_row(
                    config_name,
                    project_id,
                    state_cell,
                    status_info["infra_cell"],
                    status_info["setup_cell"],
                    status_info["load_cell"],
                    status_info["run_cell"],
                    status_info["details"],
                )

                # Verbose: show per-system details
                if verbose and status_info.get("system_details"):
                    for sys_detail in status_info["system_details"]:
                        table.add_row(
                            f"  └─ {sys_detail['name']}",
                            "",
                            "",
                            "",
                            sys_detail["setup"],
                            sys_detail["load"],
                            sys_detail["run"],
                            sys_detail.get("error", ""),
                        )

            console.print(table)

        # Summary
        console.print()
        summary_parts = [f"{total_completed}/{total_configs} ran"]
        if total_partial > 0:
            summary_parts.append(f"{total_partial} in progress")
        if total_pending > 0:
            summary_parts.append(f"{total_pending} pending")
        if total_failed_queries > 0:
            summary_parts.append(
                f"[yellow]{total_failed_queries} query failures[/yellow]"
            )

        console.print(f"[bold]Summary:[/bold] {' | '.join(summary_parts)}")

        # Show state file summary if it exists
        if state:
            state_completed = sum(
                1 for b in state.benchmarks.values() if b.status == "completed"
            )
            state_failed = sum(
                1 for b in state.benchmarks.values() if b.status == "failed"
            )
            state_pending = sum(
                1 for b in state.benchmarks.values() if b.status == "pending"
            )
            state_skipped = sum(
                1 for b in state.benchmarks.values() if b.status == "skipped"
            )
            state_parts = []
            if state_completed > 0:
                state_parts.append(f"[green]{state_completed} completed[/green]")
            if state_failed > 0:
                state_parts.append(f"[red]{state_failed} failed[/red]")
            if state_pending > 0:
                state_parts.append(f"{state_pending} pending")
            if state_skipped > 0:
                state_parts.append(f"[dim]{state_skipped} skipped[/dim]")
            if state_parts:
                console.print(f"[bold]State file:[/bold] {' | '.join(state_parts)}")
        else:
            console.print(
                "[dim]State file: not found (run 'suite sync' to create)[/dim]"
            )

    def _get_benchmark_status(
        self, config_path: Path, verbose: bool = False
    ) -> dict[str, Any]:
        """Get actual status of a benchmark from its results directory.

        Args:
            config_path: Path to benchmark config file
            verbose: Whether to include per-system details

        Returns:
            Dict with status information including phase cells and details
        """
        result: dict[str, Any] = {
            "infra_cell": "[dim]-[/dim]",
            "setup_cell": "[dim]-[/dim]",
            "load_cell": "[dim]-[/dim]",
            "run_cell": "[dim]-[/dim]",
            "details": "",
            "all_complete": False,
            "has_any_progress": False,
            "failed_queries": 0,
            "system_details": [],
        }

        try:
            cfg = load_config(str(config_path))
        except Exception:
            result["details"] = "[red]config error[/red]"
            return result

        project_id = cfg.get("project_id", config_path.stem)
        results_dir = self._resolve_results_dir(project_id)
        systems = cfg.get("systems", [])
        system_names = [s["name"] for s in systems]

        # Determine infrastructure status (fast, file-based check)
        try:
            has_cloud = is_any_system_cloud_mode(cfg)
            has_managed = is_any_system_managed_mode(cfg)

            if has_cloud:
                tf_base = results_dir / "terraform"

                # Collect all terraform state files:
                # - Shared state: terraform/terraform.tfstate (non-sequential mode)
                # - Per-system state: terraform/{system}/terraform.tfstate (sequential mode)
                tfstate_paths = []
                shared_state = tf_base / "terraform.tfstate"
                if shared_state.exists():
                    tfstate_paths.append(shared_state)
                for sname in system_names:
                    per_system_state = tf_base / sname / "terraform.tfstate"
                    if per_system_state.exists():
                        tfstate_paths.append(per_system_state)

                if tfstate_paths:
                    total_resources = 0
                    parse_error = False
                    for tfstate_path in tfstate_paths:
                        try:
                            with open(tfstate_path, encoding="utf-8") as f:
                                tfstate = json.load(f)
                            total_resources += len(tfstate.get("resources", []))
                        except (json.JSONDecodeError, OSError):
                            parse_error = True

                    if parse_error:
                        result["infra_cell"] = "[yellow]?[/yellow]"
                    elif total_resources > 0:
                        result["infra_cell"] = "[green]✓[/green]"
                    else:
                        result["infra_cell"] = "[dim]✗[/dim]"
            elif has_managed:
                result["infra_cell"] = "[dim]mgd[/dim]"
        except Exception:
            pass  # Keep default "-"

        if not results_dir.exists():
            result["details"] = "[dim]no results[/dim]"
            return result

        result["has_any_progress"] = True

        # Check setup status across systems
        setup_count = 0
        load_count = 0
        total_systems = len(system_names)

        for system_name in system_names:
            setup_path = results_dir / f"setup_complete_{system_name}.json"
            if setup_path.exists():
                setup_count += 1

            load_path = results_dir / f"load_complete_{system_name}.json"
            if load_path.exists():
                load_count += 1

        # Setup status
        if setup_count == total_systems:
            result["setup_cell"] = "[green]✓[/green]"
        elif setup_count > 0:
            result["setup_cell"] = f"[yellow]{setup_count}/{total_systems}[/yellow]"

        # Load status
        if load_count == total_systems:
            result["load_cell"] = "[green]✓[/green]"
        elif load_count > 0:
            result["load_cell"] = f"[yellow]{load_count}/{total_systems}[/yellow]"

        # Run status - check runs.csv
        runs_csv = results_dir / "runs.csv"
        if runs_csv.exists():
            try:
                import pandas as pd

                df = pd.read_csv(runs_csv)
                total_queries = len(df)
                successful = len(df[df["success"] == True])  # noqa: E712
                failed = total_queries - successful

                result["failed_queries"] = failed

                if failed == 0 and total_queries > 0:
                    result["run_cell"] = f"[green]✓ {total_queries}[/green]"
                    result["all_complete"] = (
                        setup_count == total_systems and load_count == total_systems
                    )
                elif failed > 0:
                    result["run_cell"] = (
                        f"[yellow]{successful}/{total_queries}[/yellow]"
                    )
                else:
                    result["run_cell"] = "[dim]-[/dim]"

                # Build details string
                workload = cfg.get("workload", {})
                details_parts = []
                details_parts.append(f"{workload.get('name', '?')}")
                details_parts.append(f"SF{workload.get('scale_factor', '?')}")
                details_parts.append(f"{total_systems} sys")
                if failed > 0:
                    details_parts.append(f"[red]{failed} failed[/red]")

                result["details"] = " | ".join(details_parts)

                # Verbose: per-system details
                if verbose:
                    result["system_details"] = self._get_per_system_status(
                        cfg, results_dir, df
                    )

            except Exception:
                result["run_cell"] = "[yellow]?[/yellow]"
        else:
            # No runs.csv yet — check for per-system CSV files
            # (sequential/parallel mode saves runs_{system}.csv incrementally)
            workload = cfg.get("workload", {})
            workload_name = workload.get("name", "?")

            done_systems = []
            total_rows = 0
            for sname in system_names:
                per_csv = results_dir / f"runs_{sname}.csv"
                if per_csv.exists():
                    try:
                        import pandas as pd

                        df = pd.read_csv(per_csv)
                        total_rows += len(df)
                        done_systems.append(sname)
                    except Exception:
                        pass

            if done_systems:
                # Estimate expected total rows
                workload_query_counts = {"tpch": 22, "clickbench": 43}
                num_queries = workload_query_counts.get(workload_name)

                queries_cfg = workload.get("queries", {}) or {}
                if num_queries is not None:
                    if queries_cfg.get("include"):
                        num_queries = len(queries_cfg["include"])
                    elif queries_cfg.get("exclude"):
                        num_queries -= len(queries_cfg["exclude"])

                runs_per_query = workload.get("runs_per_query", 3)

                if num_queries is not None:
                    expected = num_queries * runs_per_query * total_systems
                    result["run_cell"] = (
                        f"[yellow]~{total_rows}/{expected} "
                        f"({len(done_systems)}/{total_systems} sys)[/yellow]"
                    )
                else:
                    result["run_cell"] = (
                        f"[yellow]~{total_rows} "
                        f"({len(done_systems)}/{total_systems} sys)[/yellow]"
                    )

                details_parts = [workload_name]
                details_parts.append(f"SF{workload.get('scale_factor', '?')}")
                details_parts.append(f"{total_systems} sys")
                details_parts.append(f"done: {', '.join(done_systems)}")
                result["details"] = " | ".join(details_parts)
                result["has_partial_runs"] = True
            else:
                # No per-system CSVs either — show config info
                result["details"] = (
                    f"{workload_name} | "
                    f"SF{workload.get('scale_factor', '?')} | "
                    f"{total_systems} sys"
                )

        return result

    def _get_per_system_status(
        self, cfg: dict[str, Any], results_dir: Path, runs_df: Any
    ) -> list[dict[str, str]]:
        """Get per-system status details for verbose mode.

        Args:
            cfg: Benchmark configuration
            results_dir: Results directory path
            runs_df: Pandas DataFrame with runs data

        Returns:
            List of dicts with per-system status
        """
        systems = cfg.get("systems", [])
        details = []

        for system in systems:
            system_name = system["name"]
            sys_info: dict[str, str] = {"name": system_name}

            # Setup status
            setup_path = results_dir / f"setup_complete_{system_name}.json"
            sys_info["setup"] = (
                "[green]✓[/green]" if setup_path.exists() else "[dim]-[/dim]"
            )

            # Load status
            load_path = results_dir / f"load_complete_{system_name}.json"
            sys_info["load"] = (
                "[green]✓[/green]" if load_path.exists() else "[dim]-[/dim]"
            )

            # Run status from DataFrame
            if runs_df is not None and len(runs_df) > 0:
                sys_df = runs_df[runs_df["system"] == system_name]
                if len(sys_df) > 0:
                    total = len(sys_df)
                    success = len(sys_df[sys_df["success"] == True])  # noqa: E712
                    failed = total - success

                    if failed == 0:
                        sys_info["run"] = f"[green]✓ {total}[/green]"
                    else:
                        sys_info["run"] = f"[yellow]{success}/{total}[/yellow]"
                        # Get first error
                        failed_df = sys_df[sys_df["success"] == False]  # noqa: E712
                        if len(failed_df) > 0:
                            error = str(failed_df["error"].iloc[0])
                            if len(error) > 40:
                                error = error[:37] + "..."
                            sys_info["error"] = f"[red]{error}[/red]"
                else:
                    sys_info["run"] = "[dim]-[/dim]"
            else:
                sys_info["run"] = "[dim]-[/dim]"

            details.append(sys_info)

        return details

    def list_configs(self, hide_disabled: bool = False, verbose: bool = False) -> None:
        """List all configurations in the suite.

        Args:
            hide_disabled: If True, hide disabled series from output
            verbose: If True, show detailed system kinds and instance types
        """
        discovered = self.discover_configs(include_disabled=not hide_disabled)

        console.print(
            f"\n[bold blue]{self.config.name} v{self.config.version}[/bold blue]"
        )
        if self.config.homepage:
            console.print(f"[dim]{self.config.homepage}[/dim]")
        console.print()

        for series_name in sorted(discovered.keys()):
            configs = discovered[series_name]
            series_config = self.config.series.get(
                series_name, SeriesConfig(name=series_name)
            )

            enabled_str = "[green][ENABLED][/green]"
            if series_name in self.config.series and not series_config.enabled:
                enabled_str = "[yellow][DISABLED][/yellow]"

            list_header = f"\n{series_name}/ ({len(configs)} configs)"
            if series_config.name != series_name:
                list_header += f"  [bold magenta]{series_config.name}[/bold magenta]"
            list_header += f" {enabled_str}"
            console.print(list_header)

            for i, config_path in enumerate(configs):
                prefix = "└──" if i == len(configs) - 1 else "├──"
                try:
                    cfg = load_config(str(config_path))
                    project_id = cfg.get("project_id", config_path.stem)

                    # Extract richer config details
                    systems_list = cfg.get("systems", [])
                    num_systems = len(systems_list)
                    workload = cfg.get("workload", {})
                    workload_name = workload.get("name", "?")
                    sf = workload.get("scale_factor", "?")
                    streams = (workload.get("multiuser") or {}).get("num_streams", 1)

                    # Get node_count from first system (typically all same in a config)
                    node_count = 1
                    if systems_list:
                        node_count = (
                            systems_list[0].get("setup", {}).get("node_count", 1)
                        )

                    # Format: "tpch: 4 systems × SF50 × 4 nodes × 4 streams"
                    description = f"{workload_name}: {num_systems} systems × SF{sf}"
                    if node_count > 1:
                        description += f" × {node_count} nodes"
                    if streams > 1:
                        description += f" × {streams} streams"

                    project_suffix = ""
                    if project_id != config_path.stem:
                        project_suffix = f"  [dim]→ {project_id}[/dim]"
                    console.print(
                        f"  {prefix} {config_path.name:<20s}  "
                        f"{description}{project_suffix}"
                    )

                    # Verbose mode: show environment, system kinds, and instance types
                    if verbose and systems_list:
                        # Use correct tree character for continuation lines
                        is_last = i == len(configs) - 1
                        cont_char = " " if is_last else "│"

                        # Collect environment modes and instance types
                        env_modes: set[str] = set()
                        instance_types: set[str] = set()

                        # Legacy format: env.mode, env.instances.<sys>.instance_type
                        env = cfg.get("env") or {}
                        if env.get("mode"):
                            env_modes.add(env["mode"])
                        instances_config = env.get("instances") or {}
                        for sys in systems_list:
                            sys_name = sys.get("name", "")
                            if sys_name in instances_config:
                                inst_type = instances_config[sys_name].get(
                                    "instance_type"
                                )
                                if inst_type:
                                    instance_types.add(inst_type)

                        # New format: environments.<env_name>.mode/instance_type
                        environments = cfg.get("environments") or {}
                        for sys in systems_list:
                            # Check system.environment reference
                            sys_env_name = sys.get("environment")
                            if sys_env_name and sys_env_name in environments:
                                sys_env_cfg = environments[sys_env_name]
                                if isinstance(sys_env_cfg, dict):
                                    if sys_env_cfg.get("mode"):
                                        env_modes.add(sys_env_cfg["mode"])
                                    if sys_env_cfg.get("instance_type"):
                                        instance_types.add(sys_env_cfg["instance_type"])

                            # Also check setup.instance_type (for managed systems)
                            setup = sys.get("setup") or {}
                            if setup.get("instance_type"):
                                instance_types.add(setup["instance_type"])

                        # Collect unique system kinds
                        kinds = sorted({s.get("kind", "?") for s in systems_list})
                        kinds_str = ", ".join(kinds)

                        # Format displays
                        env_str = ", ".join(sorted(env_modes)) if env_modes else "local"
                        inst_str = (
                            ", ".join(sorted(instance_types)) if instance_types else "-"
                        )

                        console.print(
                            f"  {cont_char}     [dim]env: {env_str} | "
                            f"kinds: {kinds_str} | instances: {inst_str}[/dim]"
                        )
                except Exception:
                    console.print(f"  {prefix} {config_path.name}")

    def reset_state(self) -> None:
        """Clear all state files."""
        self.state_manager.clear_state()
        console.print("[green]Suite state reset[/green]")

    def sync_state(self, dry_run: bool = False, force: bool = False) -> dict[str, Any]:
        """Synchronize state with actual results in results/ directory.

        Scans discovered benchmark configs, checks their result directories,
        and updates the state file to reflect actual completion status.

        Args:
            dry_run: If True, don't write state file, just return what would change
            force: If True, replace state entirely; if False, merge with existing

        Returns:
            Dict with sync summary: {updated: int, unchanged: int, details: [...]}
        """
        discovered = self.discover_configs(include_disabled=True)
        existing_state = None if force else self.state_manager.load_state()

        # Create new state or use existing
        if existing_state:
            state = existing_state
        else:
            state = SuiteState(
                suite_name=self.config.name,
                suite_version=self.config.version,
                status="pending",
            )

        summary: dict[str, Any] = {
            "updated": 0,
            "unchanged": 0,
            "details": [],
        }

        for series_name, configs in discovered.items():
            # Check if series is disabled
            series_config = self.config.series.get(series_name)
            is_disabled = series_config and not series_config.enabled

            for config_path in configs:
                benchmark_id = self.get_benchmark_id(series_name, config_path)

                # Get project_id from config
                try:
                    cfg = load_config(str(config_path))
                    project_id = cfg.get("project_id", config_path.stem)
                except Exception:
                    project_id = config_path.stem

                # Determine new state based on actual results
                # - skipped: series is disabled
                # - completed: runs.csv exists (run phase happened, regardless of failures)
                # - pending: no runs.csv yet (not started or in progress)
                new_status: Literal[
                    "pending",
                    "running",
                    "completed",
                    "failed",
                    "skipped",
                    "interrupted",
                ]
                if is_disabled:
                    # Series is disabled - mark as skipped
                    new_status = "skipped"
                else:
                    # Check if runs.csv exists (indicates run phase completed)
                    results_dir = self._resolve_results_dir(project_id)
                    runs_csv = results_dir / "runs.csv"
                    has_run_results = runs_csv.exists()

                    # Get actual status from results directory
                    actual_status = self._get_benchmark_status(config_path)

                    if has_run_results:
                        # Run phase completed (even if some queries failed)
                        new_status = "completed"
                    elif actual_status.get("has_partial_runs"):
                        # Per-system CSVs exist but no final runs.csv — run in progress
                        new_status = "running"
                    elif actual_status["has_any_progress"]:
                        # Has results dir but no runs.csv - setup/load in progress
                        new_status = "pending"
                    else:
                        # No results at all
                        new_status = "pending"

                # Check if update needed
                current_state = state.benchmarks.get(benchmark_id)
                current_status = current_state.status if current_state else None

                if current_status == new_status:
                    summary["unchanged"] += 1
                else:
                    summary["updated"] += 1
                    summary["details"].append(
                        {
                            "benchmark_id": benchmark_id,
                            "old_status": current_status,
                            "new_status": new_status,
                        }
                    )

                # Update or create benchmark state
                completed_at = None
                if new_status == "completed":
                    completed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

                state.benchmarks[benchmark_id] = BenchmarkState(
                    benchmark_id=benchmark_id,
                    config_path=str(config_path),
                    project_id=project_id,
                    status=new_status,
                    completed_at=completed_at,
                )

        if not dry_run:
            # Determine overall suite status
            all_completed = all(
                b.status == "completed" for b in state.benchmarks.values()
            )
            any_failed = any(b.status == "failed" for b in state.benchmarks.values())

            if all_completed and state.benchmarks:
                state.status = "completed"
            elif any_failed:
                state.status = "failed"
            else:
                state.status = "pending"

            state.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.state_manager.save_state(state)

        return summary

    def generate_report(
        self, output_dir: Path | None = None, combined: bool = False
    ) -> Path | list[Path] | None:
        """Generate reports for completed benchmarks.

        Args:
            output_dir: Optional output directory for reports
            combined: If True, generate a single combined report for all benchmarks.
                     If False (default), generate individual reports for each benchmark.

        Returns:
            Path to generated report (combined mode), list of paths (individual mode),
            or None if no results.
        """
        from ..report.render import render_report

        state = self.state_manager.load_state()
        if not state:
            # Auto-sync state from results directory
            console.print(
                "[dim]No state file found. Syncing from results directory...[/dim]"
            )
            sync_result = self.sync_state()
            if sync_result["updated"] > 0:
                console.print(
                    f"[green]✓ Found {sync_result['updated']} benchmark(s) with results[/green]"
                )
            state = self.state_manager.load_state()

        if not state:
            console.print("[yellow]No runs recorded yet[/yellow]")
            return None

        # Collect completed benchmarks
        completed_benchmarks = [
            b for b in state.benchmarks.values() if b.status == "completed"
        ]

        if not completed_benchmarks:
            console.print("[yellow]No completed benchmarks to report[/yellow]")
            return None

        if combined:
            return self._generate_combined_report(completed_benchmarks)
        else:
            return self._generate_individual_reports(completed_benchmarks)

    def _generate_individual_reports(
        self, completed_benchmarks: list[BenchmarkState]
    ) -> list[Path] | None:
        """Generate individual reports for each completed benchmark.

        Args:
            completed_benchmarks: List of completed benchmark states.

        Returns:
            List of paths to generated reports, or None if no reports generated.
        """
        from ..report.render import render_report

        generated_reports: list[Path] = []
        failed_reports: list[str] = []

        console.print(
            f"[blue]Generating {len(completed_benchmarks)} individual reports...[/blue]"
        )

        for bench_state in completed_benchmarks:
            config_path = Path(bench_state.config_path)
            results_dir = self._resolve_results_dir(bench_state.project_id)

            if not results_dir.exists():
                console.print(
                    f"[yellow]  Skipping {bench_state.project_id}: "
                    f"results directory not found[/yellow]"
                )
                continue

            try:
                cfg = load_config(str(config_path))
                report_path = render_report(cfg)
                generated_reports.append(report_path)
                console.print(f"[green]  ✓ {bench_state.project_id}[/green]")
            except Exception as e:
                failed_reports.append(f"{bench_state.project_id}: {e}")
                console.print(f"[red]  ✗ {bench_state.project_id}: {e}[/red]")

        if generated_reports:
            console.print(
                f"\n[green]✓ Generated {len(generated_reports)} report(s)[/green]"
            )
            if failed_reports:
                console.print(f"[yellow]  ({len(failed_reports)} failed)[/yellow]")
            return generated_reports

        console.print("[yellow]No reports generated[/yellow]")
        return None

    def _generate_combined_report(
        self, completed_benchmarks: list[BenchmarkState]
    ) -> Path | None:
        """Generate a single combined report for all benchmarks.

        Args:
            completed_benchmarks: List of completed benchmark states.

        Returns:
            Path to generated report or None if failed.
        """
        from ..combine import BenchmarkCombiner
        from ..combine.source_parser import SourceSpec, SystemSelection
        from ..report.render import render_report

        # Build source specs for combiner
        sources: list[SourceSpec] = []
        for bench_state in completed_benchmarks:
            config_path = Path(bench_state.config_path)
            results_dir = self._resolve_results_dir(bench_state.project_id)

            if not results_dir.exists():
                continue

            try:
                cfg = load_config(str(config_path))
                system_names = [s["name"] for s in cfg.get("systems", [])]

                # Create system selections
                system_selections = [
                    SystemSelection(original_name=name) for name in system_names
                ]

                # Create source spec and set results_dir manually
                source = SourceSpec(
                    config_path=config_path,
                    systems=system_selections,
                )
                source.results_dir = results_dir
                source.config = cfg
                sources.append(source)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not load {config_path}: {e}[/yellow]"
                )

        if not sources:
            console.print("[yellow]No valid results to combine[/yellow]")
            return None

        # Create combined output
        output_project_id = f"{self.config.name.lower().replace(' ', '_')}_combined"

        try:
            combiner = BenchmarkCombiner(
                sources=sources,
                output_project_id=output_project_id,
                title=self.config.name,
                author=self.config.author,
                strict_workload=False,  # Relaxed mode: only require same workload name
            )
            combined_dir = combiner.combine(force=True)

            # Generate report from combined results
            combined_config_path = combined_dir / "config.yaml"
            if combined_config_path.exists():
                cfg = load_config(str(combined_config_path))
                report_path = render_report(cfg)
                console.print(f"[green]✓ Suite report generated: {report_path}[/green]")
                return report_path
            else:
                console.print(f"[green]✓ Combined results: {combined_dir}[/green]")
                return combined_dir

        except Exception as e:
            console.print(f"[red]Report generation failed: {e}[/red]")
            return None


def init_suite(path: Path, name: str = "My Benchmark Suite") -> Path:
    """Initialize a new benchmark suite with scaffolding.

    Args:
        path: Directory to create suite in
        name: Name for the suite

    Returns:
        Path to created suite directory
    """
    path.mkdir(parents=True, exist_ok=True)

    # Create suite.yaml
    suite_yaml = path / "suite.yaml"
    suite_config = f"""name: "{name}"
version: "1.0.0"
description: "Benchmark suite description"
author: "Your Name"

series:
  01_example:
    name: "Example Series"
    description: "Example benchmark series"
    enabled: true

execution:
  mode: sequential
  continue_on_failure: true
  pause_between: 30

infrastructure:
  cleanup_after_each: true
"""
    with open(suite_yaml, "w") as f:
        f.write(suite_config)

    # Create series directory
    series_dir = path / "series" / "01_example"
    series_dir.mkdir(parents=True, exist_ok=True)

    # Create example config
    example_config = series_dir / "example.yaml"
    example_yaml = """project_id: "suite_example"
title: "Example Benchmark"
author: "Your Name"

env:
  mode: "local"

systems:
  - name: "example_system"
    kind: "duckdb"
    version: "latest"
    setup:
      method: "native"

workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
"""
    with open(example_config, "w") as f:
        f.write(example_yaml)

    # Create README
    readme = path / "README.md"
    readme_content = f"""# {name}

This is a benchmark suite created with benchkit.

## Running the Suite

```bash
# View the execution plan
benchkit suite run ./ --dry-run

# Run all benchmarks
benchkit suite run ./

# Check status
benchkit suite status ./

# Generate report
benchkit suite report ./
```

## Structure

```
{path.name}/
├── suite.yaml              # Suite configuration
├── series/
│   └── 01_example/         # Series directory
│       └── example.yaml    # Benchmark configuration
└── .benchkit/              # State directory (gitignored)
```

## Contributing

Add new benchmark configurations to the appropriate series directory.
"""
    with open(readme, "w") as f:
        f.write(readme_content)

    # Create .gitignore
    gitignore = path / ".gitignore"
    gitignore_content = """.benchkit/
results/
*.log
"""
    with open(gitignore, "w") as f:
        f.write(gitignore_content)

    console.print(f"[green]✓ Created suite: {path}[/green]")
    console.print(f"  {suite_yaml}")
    console.print(f"  {series_dir}/")
    console.print(f"  {example_config}")
    console.print(f"  {readme}")
    console.print(f"  {gitignore}")

    return path
