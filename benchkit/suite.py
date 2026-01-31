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
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, field_validator
from rich.console import Console
from rich.table import Table

from .config import load_config
from .run.runner import BenchmarkRunner

console = Console()


# =============================================================================
# Configuration Models
# =============================================================================


class SeriesConfig(BaseModel):
    """Configuration for a benchmark series within a suite."""

    name: str
    description: str = ""
    enabled: bool = True


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


class SuiteReportsConfig(BaseModel):
    """Report generation settings."""

    index_enabled: bool = True
    index_title: str = "Suite Results"
    series_reports_enabled: bool = True


class SuiteConfig(BaseModel):
    """Main suite configuration loaded from suite.yaml."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = ""
    homepage: str = ""
    keywords: list[str] = []

    series: dict[str, SeriesConfig] = {}
    execution: SuiteExecutionConfig = SuiteExecutionConfig()
    infrastructure: SuiteInfrastructureConfig = SuiteInfrastructureConfig()
    timeouts: SuiteTimeoutsConfig = SuiteTimeoutsConfig()
    reports: SuiteReportsConfig = SuiteReportsConfig()

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
        """Save state to disk.

        Args:
            state: State to save
        """
        self.ensure_state_dir()
        state.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

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

        # Look for series directories
        for entry in sorted(series_dir.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("."):
                continue

            series_name = entry.name

            # Skip if not in configured series or disabled (unless include_disabled)
            if series_name in self.config.series:
                series_config = self.config.series[series_name]
                if not series_config.enabled and not include_disabled:
                    continue
            elif self.config.series:
                # If series are explicitly configured, skip undeclared ones
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
                    streams = workload.get("multiuser", {}).get("num_streams", 1)
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

        Args:
            discovered: Discovered configurations
            resume: Whether to resume from existing state
            tag: Run tag

        Returns:
            SuiteState object
        """
        existing_state = self.state_manager.load_state() if resume else None

        if existing_state:
            # Update with any newly discovered benchmarks
            for series_name, configs in discovered.items():
                for config_path in configs:
                    benchmark_id = self.get_benchmark_id(series_name, config_path)
                    if benchmark_id not in existing_state.benchmarks:
                        # Load config to get project_id
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
            return existing_state

        # Create new state
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
                streams = workload.get("multiuser", {}).get("num_streams", 1)
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

    def _run_benchmark(
        self, config_path: Path, no_cleanup: bool = False, systems: str | None = None
    ) -> bool:
        """Execute a single benchmark using BenchmarkRunner.

        Args:
            config_path: Path to benchmark config
            no_cleanup: Keep infrastructure
            systems: Comma-separated systems to run

        Returns:
            True if successful
        """
        try:
            cfg = load_config(str(config_path))

            # Filter systems if specified
            if systems:
                system_names = [s.strip() for s in systems.split(",")]
                cfg["systems"] = [
                    s for s in cfg["systems"] if s["name"] in system_names
                ]
                if not cfg["systems"]:
                    console.print(
                        f"[red]No matching systems found for: {system_names}[/red]"
                    )
                    return False

            project_id = cfg.get("project_id", config_path.stem)
            outdir = Path("results") / project_id
            outdir.mkdir(parents=True, exist_ok=True)

            runner = BenchmarkRunner(cfg, outdir)

            # Run full benchmark workflow
            # This handles: infrastructure -> setup -> load -> run
            from .common.cli_helpers import (
                is_any_system_cloud_mode,
                is_any_system_managed_mode,
            )

            has_cloud = is_any_system_cloud_mode(cfg)
            has_managed = is_any_system_managed_mode(cfg)

            # Phase 0: Infrastructure
            if has_cloud or has_managed:
                if has_cloud:
                    if not runner.ensure_cloud_infrastructure():
                        return False
                # Managed infrastructure is handled in setup

            # Phase 1: Setup
            if not runner.run_setup(force=True):
                return False

            # Phase 2: Load
            if not runner.run_load(force=True):
                return False

            # Phase 3: Run queries
            if not runner.run_queries(force=True):
                return False

            # Cleanup if requested
            if not no_cleanup and self.config.infrastructure.cleanup_after_each:
                if has_cloud:
                    from .infra.manager import InfraManager

                    # Get provider from config
                    env = cfg.get("env") or {}
                    provider = env.get("mode", "aws")
                    if provider in ("aws", "gcp", "azure"):
                        manager = InfraManager(provider, cfg)
                        manager.destroy()

            return True

        except Exception as e:
            console.print(f"[red]Benchmark failed: {e}[/red]")
            return False

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

            console.print(
                f"\n[bold magenta]{series_config.name}[/bold magenta] {enabled_str}"
            )
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
                    description = f"{len(cfg.get('systems', []))} systems"
                    workload = cfg.get("workload", {})
                    if workload:
                        description += f" × SF{workload.get('scale_factor', '?')}"
                except Exception:
                    description = ""

                console.print(
                    f"    {status_icon}  {config_path.stem:20s}  {description}"
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

            console.print(
                f"\n[bold magenta]{series_config.name}[/bold magenta] {enabled_str}"
            )

            # Create table for this series
            table = Table(show_header=True, header_style="bold")
            table.add_column("Config", style="cyan", no_wrap=True)
            table.add_column("Setup", justify="center")
            table.add_column("Load", justify="center")
            table.add_column("Run", justify="center")
            table.add_column("Details", overflow="fold")

            for config_path in configs:
                total_configs += 1
                config_name = config_path.stem

                if is_disabled:
                    table.add_row(
                        config_name,
                        "[dim]-[/dim]",
                        "[dim]-[/dim]",
                        "[dim]-[/dim]",
                        "[dim]series disabled[/dim]",
                    )
                    continue

                # Get actual status from results directory
                status_info = self._get_benchmark_status(config_path, verbose)

                if status_info["all_complete"]:
                    total_completed += 1
                elif status_info["has_any_progress"]:
                    total_partial += 1
                else:
                    total_pending += 1

                total_failed_queries += status_info.get("failed_queries", 0)

                table.add_row(
                    config_name,
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
                            sys_detail["setup"],
                            sys_detail["load"],
                            sys_detail["run"],
                            sys_detail.get("error", ""),
                        )

            console.print(table)

        # Summary
        console.print()
        summary_parts = [f"{total_completed}/{total_configs} completed"]
        if total_partial > 0:
            summary_parts.append(f"{total_partial} partial")
        if total_pending > 0:
            summary_parts.append(f"{total_pending} pending")
        if total_failed_queries > 0:
            summary_parts.append(
                f"[yellow]{total_failed_queries} query failures[/yellow]"
            )

        console.print(f"[bold]Summary:[/bold] {' | '.join(summary_parts)}")

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
        results_dir = Path("results") / project_id
        systems = cfg.get("systems", [])
        system_names = [s["name"] for s in systems]

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
            # No runs yet, show config info
            workload = cfg.get("workload", {})
            result["details"] = (
                f"{workload.get('name', '?')} | "
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

            console.print(f"\n{series_name}/ ({len(configs)} configs) {enabled_str}")

            for i, config_path in enumerate(configs):
                prefix = "└──" if i == len(configs) - 1 else "├──"
                try:
                    cfg = load_config(str(config_path))

                    # Extract richer config details
                    systems_list = cfg.get("systems", [])
                    num_systems = len(systems_list)
                    workload = cfg.get("workload", {})
                    workload_name = workload.get("name", "?")
                    sf = workload.get("scale_factor", "?")
                    streams = workload.get("multiuser", {}).get("num_streams", 1)

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

                    console.print(f"  {prefix} {config_path.name:<20s}  {description}")

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

    def generate_report(self, output_dir: Path | None = None) -> Path | None:
        """Generate combined report for all completed benchmarks.

        Args:
            output_dir: Optional output directory for reports

        Returns:
            Path to generated report or None if no results
        """
        from .combine import BenchmarkCombiner
        from .combine.source_parser import SourceSpec, SystemSelection
        from .report.render import render_report

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

        # Build source specs for combiner
        sources: list[SourceSpec] = []
        for bench_state in completed_benchmarks:
            config_path = Path(bench_state.config_path)
            results_dir = Path("results") / bench_state.project_id

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
