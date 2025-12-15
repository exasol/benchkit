"""Benchmark execution runner."""

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pandas as pd
from rich.console import Console

from benchkit.common import exclude_from_package
from benchkit.util import ensure_directory, load_json, save_json

from ..debug import is_debug_enabled
from ..systems import create_system
from ..workloads import create_workload
from .parallel_executor import ParallelExecutor
from .parsers import normalize_runs

if TYPE_CHECKING:
    from benchkit.systems import SystemUnderTest
    from benchkit.workloads import Workload


console = Console()


# =============================================================================
# Dataclasses for Unified Phase Execution
# =============================================================================


@dataclass
class ExecutionContext:
    """Encapsulates execution environment details for benchmark phases."""

    mode: Literal["local", "cloud", "local_to_remote"]
    use_parallel: bool
    max_workers: int
    cloud_managers: dict[str, Any] | None = None
    executor: ParallelExecutor | None = (
        None  # Reference to executor for output callbacks
    )

    @property
    def is_remote(self) -> bool:
        """Check if this context involves remote execution."""
        return self.mode in ("cloud", "local_to_remote")

    @property
    def needs_package(self) -> bool:
        """Check if this context requires deploying a package to remote."""
        return self.mode == "cloud"

    @property
    def effective_max_workers(self) -> int:
        """Return 1 for sequential execution, otherwise configured max_workers."""
        return self.max_workers if self.use_parallel else 1


@dataclass
class PhaseConfig:
    """Configuration for a benchmark phase (setup, load, or queries)."""

    name: str
    header_emoji: str
    header_text: str
    prerequisite_phase: (
        str | None
    )  # Phase that must complete first (e.g., "setup" for load)
    completion_check: Callable[[str], bool]  # Check if system completed this phase
    completion_save: Callable[[str, dict[str, Any]], None]  # Save completion marker
    operation: Callable[..., tuple[bool, Any]]  # Execute phase for single system
    collects_results: bool = False  # True if phase collects results (queries phase)
    creates_package: bool = False  # True if phase needs to create/deploy package


@dataclass
class TaskResult:
    """Result from executing a phase task on a single system."""

    success: bool
    data: Any = None
    error: str | None = None
    timings: dict[str, float] = field(default_factory=dict)


class BenchmarkRunner:
    """Orchestrates benchmark execution across multiple systems."""

    def __init__(self, config: dict[str, Any], output_dir: Path):
        self.config = config
        self.output_dir = Path(output_dir)
        self.project_id = config["project_id"]
        ensure_directory(self.output_dir)
        self.parallel_log_dir = self.output_dir / "logs"
        self._cloud_instance_managers: dict[str, Any] = {}
        self.infrastructure_provisioning_time: float = 0.0

        # Parallel execution configuration
        exec_config = config.get("execution", {})
        self.use_parallel = exec_config.get("parallel", False)
        self.max_workers = exec_config.get(
            "max_workers", len(config.get("systems", []))
        )

        # Thread-safe locks for shared state (not needed if we don't modify shared state during parallel execution)
        # But kept for future safety
        self._timings_lock = threading.Lock()
        self._results_lock = threading.Lock()

    def _load_provisioning_timing(self) -> float:
        """Load infrastructure provisioning timing from saved file."""
        timing_file = self.output_dir / "infrastructure_provisioning.json"
        if timing_file.exists():
            try:
                with open(timing_file) as f:
                    data = json.load(f)
                value = data.get("infrastructure_provisioning_s", 0.0)
                return float(value) if value is not None else 0.0
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to load provisioning timing: {e}[/yellow]"
                )
                return 0.0
        return 0.0

    def _save_installation_timing(
        self, system_name: str, elapsed_seconds: float
    ) -> None:
        """Save installation timing for a system to a dedicated file."""
        timing_file = self.output_dir / f"installation_{system_name}.json"
        timing_data = {
            "system_name": system_name,
            "installation_s": elapsed_seconds,
            "timestamp": self._get_timestamp(),
        }

        try:
            with open(timing_file, "w") as f:
                json.dump(timing_data, f, indent=2)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to save installation timing for {system_name}: {e}[/yellow]"
            )

    def _load_installation_timing(self, system_name: str) -> float:
        """Load installation timing for a system from saved file."""
        timing_file = self.output_dir / f"installation_{system_name}.json"
        if timing_file.exists():
            try:
                with open(timing_file) as f:
                    data = json.load(f)
                value = data.get("installation_s", 0.0)
                return float(value) if value is not None else 0.0
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Failed to load installation timing for {system_name}: {e}[/yellow]"
                )
                return 0.0
        return 0.0

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _log_output(
        self,
        message: str,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> None:
        """
        Route output to either parallel executor buffer or console.

        Args:
            message: Message to log
            executor: ParallelExecutor instance (if in parallel mode)
            system_name: System name (if in parallel mode)
        """
        if executor and system_name:
            # Parallel mode - add to executor buffer
            # Strip Rich markup for cleaner buffer output
            clean_message = message.replace("[dim]", "").replace("[/dim]", "")
            clean_message = clean_message.replace("[green]", "").replace("[/green]", "")
            clean_message = clean_message.replace("[red]", "").replace("[/red]", "")
            clean_message = clean_message.replace("[yellow]", "").replace(
                "[/yellow]", ""
            )
            clean_message = clean_message.replace("[bold]", "").replace("[/bold]", "")
            clean_message = clean_message.replace("[blue]", "").replace("[/blue]", "")
            executor.add_output(system_name, clean_message)
        else:
            # Sequential mode - print to console
            console.print(message)

    # ========================================================================
    # State Management for Phase Tracking
    # ========================================================================

    def _get_setup_complete_path(self, system_name: str) -> Path:
        """Get path to setup completion marker file."""
        return self.output_dir / f"setup_complete_{system_name}.json"

    def _get_load_complete_path(self, system_name: str) -> Path:
        """Get path to load completion marker file."""
        return self.output_dir / f"load_complete_{system_name}.json"

    def _is_setup_complete(self, system_name: str) -> bool:
        """Check if setup phase is complete for a system.

        This method validates not just that a marker file exists, but also that
        the IP address in the marker matches the current infrastructure. This
        prevents stale markers from causing installations to be skipped after
        infrastructure is re-provisioned with new IP addresses.
        """
        marker_path = self._get_setup_complete_path(system_name)
        if not marker_path.exists():
            return False

        # Validate that marker IP matches current infrastructure IP
        try:
            marker_data = load_json(marker_path)
            marker_ip = marker_data.get("connection_info", {}).get("public_ip")

            # Early exit: no cloud managers to validate against
            if not self._cloud_instance_managers:
                return True

            current_mgr = self._cloud_instance_managers.get(system_name)

            # Early exit: no manager for this specific system
            if not current_mgr:
                return True

            # Handle both single manager and list of managers (multinode)
            if isinstance(current_mgr, list):
                current_ip = current_mgr[0].public_ip if current_mgr else None
            else:
                current_ip = current_mgr.public_ip

            if marker_ip and current_ip and marker_ip != current_ip:
                console.print(
                    f"[yellow]⚠ {system_name} setup marker has stale IP "
                    f"({marker_ip} != {current_ip}), will reinstall[/yellow]"
                )
                return False
        except Exception:
            pass  # If marker can't be read, treat as still valid to avoid blocking

        return True

    def _is_load_complete(self, system_name: str) -> bool:
        """Check if load phase is complete for a system."""
        return self._get_load_complete_path(system_name).exists()

    def _save_setup_complete(
        self, system_name: str, connection_info: dict[str, Any]
    ) -> None:
        """Save setup completion marker with connection info."""
        marker_data = {
            "system_name": system_name,
            "connection_info": connection_info,
            "installation_s": self._load_installation_timing(system_name),
            "timestamp": self._get_timestamp(),
        }
        save_json(marker_data, self._get_setup_complete_path(system_name))

    def _save_load_complete(
        self,
        system_name: str,
        data_generation_s: float = 0.0,
        schema_creation_s: float = 0.0,
        data_loading_s: float = 0.0,
    ) -> None:
        """Save load completion marker with timing info."""
        marker_data = {
            "system_name": system_name,
            "data_generation_s": data_generation_s,
            "schema_creation_s": schema_creation_s,
            "data_loading_s": data_loading_s,
            "timestamp": self._get_timestamp(),
        }
        save_json(marker_data, self._get_load_complete_path(system_name))

    def _load_setup_info(self, system_name: str) -> dict[str, Any] | None:
        """Load setup completion info for a system."""
        path = self._get_setup_complete_path(system_name)
        if path.exists():
            data: dict[str, Any] = load_json(path)
            return data
        return None

    def _load_load_info(self, system_name: str) -> dict[str, Any] | None:
        """Load load completion info for a system."""
        path = self._get_load_complete_path(system_name)
        if path.exists():
            data: dict[str, Any] = load_json(path)
            return data
        return None

    def _check_setup_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if setup prerequisites are met for all systems."""
        missing_systems = []
        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            if not self._is_setup_complete(system_name):
                missing_systems.append(system_name)
        return len(missing_systems) == 0, missing_systems

    def _check_load_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if load prerequisites are met for all systems."""
        missing_systems = []
        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            if not self._is_load_complete(system_name):
                missing_systems.append(system_name)
        return len(missing_systems) == 0, missing_systems

    # ========================================================================
    # Unified Phase Execution Architecture
    # ========================================================================

    @exclude_from_package
    def _create_execution_context(
        self, local_override: bool = False
    ) -> ExecutionContext:
        """
        Create execution context based on config and overrides.

        Args:
            local_override: If True, use local-to-remote mode for cloud configs

        Returns:
            ExecutionContext with appropriate mode and settings
        """
        from ..common.cli_helpers import is_any_system_cloud_mode

        if is_any_system_cloud_mode(self.config):
            mode: Literal["local", "cloud", "local_to_remote"] = (
                "local_to_remote" if local_override else "cloud"
            )
        else:
            mode = "local"

        return ExecutionContext(
            mode=mode,
            use_parallel=self.use_parallel,
            max_workers=self.max_workers,
            cloud_managers=self._cloud_instance_managers or None,
        )

    @exclude_from_package
    def _setup_phase_config(self) -> PhaseConfig:
        """Create configuration for setup phase."""
        return PhaseConfig(
            name="setup",
            header_emoji="🏗️",
            header_text="Phase 1: System Setup",
            prerequisite_phase=None,
            completion_check=self._is_setup_complete,
            completion_save=lambda name, data: self._save_setup_complete(
                name, data.get("connection_info", {})
            ),
            operation=self._setup_operation,
            collects_results=False,
            creates_package=False,
        )

    @exclude_from_package
    def _load_phase_config(self) -> PhaseConfig:
        """Create configuration for load phase."""
        return PhaseConfig(
            name="load",
            header_emoji="📦",
            header_text="Phase 2: Data Loading",
            prerequisite_phase="setup",
            completion_check=self._is_load_complete,
            completion_save=lambda name, data: self._save_load_complete(
                name,
                data_generation_s=data.get("data_generation_s", 0.0),
                schema_creation_s=data.get("schema_creation_s", 0.0),
                data_loading_s=data.get("data_loading_s", 0.0),
            ),
            operation=self._load_operation,
            collects_results=False,
            creates_package=True,
        )

    @exclude_from_package
    def _query_phase_config(self) -> PhaseConfig:
        """Create configuration for query execution phase."""
        return PhaseConfig(
            name="queries",
            header_emoji="🚀",
            header_text="Phase 3: Query Execution",
            prerequisite_phase="load",
            completion_check=lambda _: False,  # Queries can always be re-run
            completion_save=lambda _name, _data: None,  # No completion marker for queries
            operation=self._query_operation,
            collects_results=True,
            creates_package=True,
        )

    @exclude_from_package
    def _execute_phase(
        self,
        phase: PhaseConfig,
        context: ExecutionContext,
        force: bool = False,
        workload: "Workload | None" = None,
    ) -> bool | list[dict[str, Any]]:
        """
        Universal phase executor handling setup, load, and query phases.

        This method provides unified execution flow for all benchmark phases,
        supporting both parallel and sequential execution modes.

        Args:
            phase: Phase configuration specifying behavior
            context: Execution context (local/cloud/local_to_remote)
            force: If True, re-run even if already complete
            workload: Workload instance (required for load/query phases)

        Returns:
            bool for setup/load phases, list of results for query phase
        """
        # 1. Print header
        mode_label = {
            "local": "Local",
            "cloud": "Cloud",
            "local_to_remote": "Local-to-Remote",
        }[context.mode]
        console.print(
            f"[bold blue]{phase.header_emoji}  {phase.header_text} ({mode_label})[/bold blue]"
        )

        # 2. Establish cloud connections if needed
        if context.is_remote and not self._cloud_instance_managers:
            if not self._setup_cloud_infrastructure():
                return False if not phase.collects_results else []
            context.cloud_managers = self._cloud_instance_managers

        # 3. Check prerequisites
        if phase.prerequisite_phase:
            prereq_method_name = f"_check_{phase.prerequisite_phase}_prerequisites"
            prereq_check = getattr(self, prereq_method_name, None)
            if prereq_check:
                ok, missing = prereq_check()
                if not ok:
                    console.print(
                        f"[red]Error: {phase.prerequisite_phase} phase not complete "
                        f"for system(s): {', '.join(missing)}[/red]"
                    )
                    console.print(
                        f"[yellow]Run 'benchkit {phase.prerequisite_phase} --config <config.yaml>' first, "
                        "or use 'benchkit run --full' to run all phases.[/yellow]"
                    )
                    return False if not phase.collects_results else []

        # 4. Create package if needed (cloud mode only)
        package_path: Path | None = None
        if phase.creates_package and context.needs_package:
            console.print("📦 Creating package...")
            package_path = self._create_package()
            if not package_path:
                console.print("[red]❌ Failed to create package[/red]")
                return False if not phase.collects_results else []
            console.print(f"✅ Package created: {package_path}")

        # 5. Build and execute tasks
        tasks = self._build_phase_tasks(phase, context, force, package_path, workload)

        if not tasks:
            console.print(
                f"[bold green]✅ All systems already completed {phase.name}![/bold green]"
            )
            return True if not phase.collects_results else []

        # 6. Execute with unified executor
        # Pass context so executor can be stored for thread-safe output callbacks
        results = self._execute_tasks(
            tasks, phase.header_text, context.effective_max_workers, context
        )

        # 7. Process results
        all_success = all(r.success for r in results.values())

        if phase.collects_results:
            all_data: list[dict[str, Any]] = []
            for r in results.values():
                if r.data:
                    if isinstance(r.data, list):
                        all_data.extend(r.data)
                    else:
                        all_data.append(r.data)
            return all_data

        # 8. Print completion
        status = "completed successfully" if all_success else "failed for some systems"
        color = "green" if all_success else "red"
        icon = "✅" if all_success else "❌"
        console.print(
            f"[bold {color}]{icon} {phase.name.capitalize()} phase {status}![/bold {color}]"
        )

        return all_success

    @exclude_from_package
    def _build_phase_tasks(
        self,
        phase: PhaseConfig,
        context: ExecutionContext,
        force: bool,
        package_path: Path | None,
        workload: "Workload|None",
    ) -> dict[str, Callable[[], TaskResult]]:
        """
        Build task callables for each system in the benchmark.

        Args:
            phase: Phase configuration
            context: Execution context
            force: If True, ignore completion markers
            package_path: Path to deployment package (for cloud mode)
            workload: Workload instance

        Returns:
            Dictionary mapping system names to task callables
        """
        tasks: dict[str, Callable[[], TaskResult]] = {}

        for system_config in self.config["systems"]:
            system_name = system_config["name"]

            # Skip if already complete (unless force)
            if not force and phase.completion_check(system_name):
                console.print(
                    f"[green]✅ {system_name} {phase.name} already complete, skipping[/green]"
                )
                continue

            # Create task closure with captured variables
            def make_task(cfg: dict[str, Any], name: str) -> Callable[[], TaskResult]:
                def task() -> TaskResult:
                    try:
                        console.print(f"\n🔧 Processing [bold]{name}[/bold]...")

                        # Get system for this execution context
                        system = self._get_system_for_context(cfg, context)
                        instance_mgr = (
                            context.cloud_managers.get(name)
                            if context.cloud_managers
                            else None
                        )

                        # Execute phase operation
                        success, data = phase.operation(
                            system, cfg, instance_mgr, package_path, workload
                        )

                        # Save completion marker on success
                        if success and phase.completion_save is not None:
                            phase.completion_save(
                                name, data if isinstance(data, dict) else {}
                            )

                        return TaskResult(success=success, data=data)

                    except Exception as e:
                        console.print(f"[red]{name} {phase.name} failed: {e}[/red]")
                        if is_debug_enabled():
                            import traceback

                            console.print(f"[dim]{traceback.format_exc()}[/dim]")
                        return TaskResult(success=False, error=str(e))

                return task

            tasks[system_name] = make_task(system_config, system_name)

        return tasks

    @exclude_from_package
    def _execute_tasks(
        self,
        tasks: dict[str, Callable[[], TaskResult]],
        phase_name: str,
        max_workers: int,
        context: ExecutionContext | None = None,
    ) -> dict[str, TaskResult]:
        """
        Execute tasks, using parallel execution when max_workers > 1.

        Args:
            tasks: Dictionary mapping system names to task callables
            phase_name: Name of the phase (for logging)
            max_workers: Maximum concurrent workers
            context: Execution context (used to pass executor reference for output callbacks)

        Returns:
            Dictionary mapping system names to TaskResults
        """
        if max_workers > 1 and len(tasks) > 1:
            # Parallel execution
            executor = ParallelExecutor(max_workers=max_workers)

            # Store executor in context so task closures can access it for output callbacks
            # This enables thread-safe output tagging by allowing systems to use
            # executor.create_output_callback() instead of relying on redirect_stdout
            if context is not None:
                context.executor = executor

            # Wrap tasks to return TaskResult-compatible format
            wrapped_tasks: dict[str, Callable[[], Any]] = {}
            for name, task_fn in tasks.items():
                wrapped_tasks[name] = task_fn

            raw_results = executor.execute_parallel(
                wrapped_tasks, phase_name, log_dir=self.parallel_log_dir
            )

            # Convert to TaskResult
            results: dict[str, TaskResult] = {}
            for name, result in raw_results.items():
                if isinstance(result, TaskResult):
                    results[name] = result
                elif isinstance(result, tuple) and len(result) >= 1:
                    results[name] = TaskResult(
                        success=bool(result[0]),
                        data=result[1] if len(result) > 1 else None,
                    )
                elif result is None:
                    results[name] = TaskResult(
                        success=False, error="Task returned None"
                    )
                else:
                    results[name] = TaskResult(success=bool(result), data=result)
            return results
        else:
            # Sequential execution
            results = {}
            for name, task_fn in tasks.items():
                results[name] = task_fn()
            return results

    @exclude_from_package
    def _get_system_for_context(
        self,
        system_config: dict[str, Any],
        context: ExecutionContext,
    ) -> "SystemUnderTest":
        """
        Create system instance configured for the execution context.

        Args:
            system_config: System configuration dictionary
            context: Execution context determining how to connect

        Returns:
            SystemUnderTest instance configured for the context
        """
        system_name = system_config["name"]

        # Create output callback for thread-safe logging in parallel execution
        # This callback routes _log() output to the correct task buffer,
        # avoiding the race condition in redirect_stdout
        output_callback = None
        if context.executor is not None:
            output_callback = context.executor.create_output_callback(system_name)

        if context.mode == "local":
            # Local mode - simple system creation
            # Check for prepared system first (preserves partition info)
            if (
                hasattr(self, "_prepared_systems")
                and system_name in self._prepared_systems
            ):
                system = self._prepared_systems[system_name]
                # Update callback on existing system if possible
                if output_callback is not None:
                    system._output_callback = output_callback
                return system
            return create_system(
                system_config,
                output_callback=output_callback,
                workload_config=self.config.get("workload", {}),
            )

        elif context.mode == "local_to_remote":
            # Local-to-remote mode - need public IP for connection
            instance_manager = (
                context.cloud_managers.get(system_name)
                if context.cloud_managers
                else None
            )
            if not instance_manager:
                raise ValueError(f"No instance manager for {system_name}")
            return self._create_system_for_local_execution(
                system_config, instance_manager, output_callback=output_callback
            )

        else:  # cloud
            # Cloud mode - system runs on remote, use prepared system if available
            if (
                hasattr(self, "_prepared_systems")
                and system_name in self._prepared_systems
            ):
                system = self._prepared_systems[system_name]
                # Update callback on existing system if possible
                if output_callback is not None:
                    system._output_callback = output_callback
            else:
                system = create_system(
                    system_config,
                    output_callback=output_callback,
                    workload_config=self.config.get("workload", {}),
                )

            # Set cloud instance manager
            instance_manager = (
                context.cloud_managers.get(system_name)
                if context.cloud_managers
                else None
            )
            if instance_manager and hasattr(system, "set_cloud_instance_manager"):
                system.set_cloud_instance_manager(instance_manager)

            return system

    # ========================================================================
    # Phase Operations (Setup, Load, Query)
    # ========================================================================

    @exclude_from_package
    def _setup_operation(
        self,
        system: "SystemUnderTest",
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path | None,  # unused for setup
        workload: "Workload",  # unused for setup
    ) -> tuple[bool, dict[str, Any]]:
        """
        Execute setup operation for a single system.

        Handles both local installation and remote state machine (install/restart).

        Args:
            system: System instance to set up
            system_config: System configuration
            instance_manager: Cloud instance manager (None for local)
            package_path: Unused for setup
            workload: Unused for setup

        Returns:
            Tuple of (success, data_dict with connection_info and timings)
        """
        from ..util import Timer

        system_name = system_config["name"]
        timings: dict[str, float] = {}

        # Local mode - simple install flow
        if instance_manager is None:
            if system.is_already_installed():
                console.print(f"  [green]✓ {system_name} already installed[/green]")
                return True, {
                    "status": "already_installed",
                    "connection_info": {
                        "host": system_config.get("setup", {}).get("host", "localhost"),
                        "port": system_config.get("setup", {}).get("port"),
                    },
                }

            console.print(f"  Installing {system_name}...")
            if not system.install():
                return False, {"error": "installation_failed"}

            if not system.start():
                return False, {"error": "start_failed"}

            console.print(f"  Waiting for {system_name} to be ready...")
            if not system.wait_for_health():
                return False, {"error": "health_check_failed"}

            setup_summary = system.get_setup_summary()
            self._save_setup_summary(system_name, setup_summary)

            return True, {
                "status": "installed",
                "connection_info": {
                    "host": system_config.get("setup", {}).get("host", "localhost"),
                    "port": system_config.get("setup", {}).get("port"),
                },
            }

        # Cloud/remote mode - use state machine
        state = self._check_system_state(system, instance_manager)
        console.print(f"📊 System state: [blue]{state}[/blue]")

        if state == "NEEDS_INSTALLATION":
            console.print(f"🚀 Installing {system_name}...")
            with Timer(f"Installation for {system_name}") as timer:
                if not self._install_system_remotely(
                    system, instance_manager, system_name=system_name
                ):
                    return False, {"error": "installation_failed"}
            timings["installation_s"] = timer.elapsed
            self._save_installation_timing(system_name, timer.elapsed)
            console.print(
                f"[dim]✓ Installation completed in {timer.elapsed:.2f}s[/dim]"
            )

            setup_summary = system.get_setup_summary()
            self._save_setup_summary(system_name, setup_summary)

        elif state in ["NEEDS_SERVICE_RESTART", "NEEDS_DB_RESTART"]:
            console.print(f"🔄 Restarting {system_name}...")
            self._load_setup_summary_to_system(system, system_name)

            with Timer(f"Restart for {system_name}") as timer:
                if not self._restart_system_remotely(
                    system, instance_manager, system_name=system_name
                ):
                    return False, {"error": "restart_failed"}
            timings["restart_s"] = timer.elapsed
            timings["installation_s"] = self._load_installation_timing(system_name)
            console.print(f"[dim]✓ Restart completed in {timer.elapsed:.2f}s[/dim]")

            setup_summary = system.get_setup_summary()
            if setup_summary.get("commands"):
                self._save_setup_summary(system_name, setup_summary)

        elif state == "READY":
            timings["installation_s"] = self._load_installation_timing(system_name)
            self._load_setup_summary_to_system(system, system_name)
            if timings["installation_s"] > 0:
                console.print(
                    f"[green]✅ {system_name} already ready (installed in {timings['installation_s']:.2f}s)[/green]"
                )
            else:
                console.print(f"[green]✅ {system_name} already ready[/green]")

        # Build connection info
        connection_info = self._build_connection_info(instance_manager)
        return True, {"timings": timings, "connection_info": connection_info}

    def _load_operation(
        self,
        system: "SystemUnderTest",
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path | None,
        workload: "Workload",
    ) -> tuple[bool, dict[str, Any]]:
        """
        Execute load operation for a single system.

        Handles local workload preparation and remote package deployment.

        Args:
            system: System instance
            system_config: System configuration
            instance_manager: Cloud instance manager (None for local)
            package_path: Path to deployment package (for cloud mode)
            workload: Workload instance

        Returns:
            Tuple of (success, data_dict with timing info)
        """
        system_name = system_config["name"]

        # Cloud mode - deploy package and run remotely
        if package_path and instance_manager:
            success = self._execute_load_remotely(
                system_config, instance_manager, package_path
            )
            return success, {}

        # Local/local-to-remote mode - run directly
        if not system.is_healthy():
            console.print(f"  Starting {system_name}...")
            if not system.start():
                return False, {"error": "start_failed"}
            if not system.wait_for_health():
                return False, {"error": "health_check_failed"}

        console.print("  Preparing workload...")
        if not workload.prepare(system):
            return False, {"error": "workload_preparation_failed"}

        prep_timings = getattr(workload, "preparation_timings", {})
        console.print(f"  [green]✓ Data loaded for {system_name}[/green]")

        return True, {
            "data_generation_s": prep_timings.get("data_generation_s", 0.0),
            "schema_creation_s": prep_timings.get("schema_creation_s", 0.0),
            "data_loading_s": prep_timings.get("data_loading_s", 0.0),
        }

    def _query_operation(
        self,
        system: "SystemUnderTest",
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path | None,
        workload: "Workload",
    ) -> tuple[bool, list[dict[str, Any]]]:
        """
        Execute query operation for a single system.

        Handles local query execution and remote package deployment.

        Args:
            system: System instance
            system_config: System configuration
            instance_manager: Cloud instance manager (None for local)
            package_path: Path to deployment package (for cloud mode)
            workload: Workload instance

        Returns:
            Tuple of (success, list of result dicts)
        """
        system_name = system_config["name"]

        # Cloud mode - deploy package and run remotely
        if package_path and instance_manager:
            results = self._execute_workload_remotely(
                system_config, instance_manager, package_path
            )
            return bool(results), results or []

        # Local/local-to-remote mode - run directly
        if not system.is_healthy():
            console.print(f"  Starting {system_name}...")
            if not system.start():
                return False, []
            if not system.wait_for_health():
                return False, []

        console.print("  Executing queries...")
        measured, warmup = self._execute_queries(system, workload)

        # Store warmup results for later aggregation
        if warmup:
            if not hasattr(self, "_all_warmup_results"):
                self._all_warmup_results = []
            self._all_warmup_results.extend(warmup)

        console.print(f"  [green]✓ Queries completed for {system_name}[/green]")
        return bool(measured), measured

    @exclude_from_package
    def _build_connection_info(self, instance_manager: Any) -> dict[str, Any]:
        """Build connection info dictionary from instance manager."""
        if instance_manager is None:
            return {}

        if isinstance(instance_manager, list):
            # Multinode
            return {
                "public_ips": [mgr.public_ip for mgr in instance_manager],
                "private_ips": [mgr.private_ip for mgr in instance_manager],
            }
        else:
            return {
                "public_ip": instance_manager.public_ip,
                "private_ip": instance_manager.private_ip,
            }

    # ========================================================================
    # Phase-Separated Benchmark Execution
    # ========================================================================

    def run_setup(self) -> bool:
        """
        Phase 1: Setup infrastructure and install database systems.

        This phase handles:
        - Cloud infrastructure provisioning (if cloud mode)
        - Storage preparation (disk partitioning, RAID setup)
        - Database system installation and configuration

        Returns:
            True if setup completed successfully, False otherwise
        """
        console.print(f"[bold blue]Starting setup phase: {self.project_id}[/bold blue]")

        context = self._create_execution_context()

        # Cloud mode requires storage preparation before setup
        if context.is_remote:
            # Setup cloud infrastructure first
            if not self._setup_cloud_infrastructure():
                return False
            context.cloud_managers = self._cloud_instance_managers

            # Prepare storage (partition disks) before system installation
            if not self._prepare_storage_phase():
                console.print("[red]❌ Storage preparation phase failed[/red]")
                return False

        # Run setup phase using unified executor
        phase = self._setup_phase_config()
        result = self._execute_phase(phase, context)
        # Setup phase always returns bool (collects_results=False)
        assert isinstance(result, bool)
        return result

    def run_load(self, force: bool = False, local: bool = False) -> bool:
        """
        Phase 2: Generate data, create schema, and load data into databases.

        This phase handles:
        - Data generation (TPC-H data files)
        - Schema creation (tables, indexes)
        - Data loading (bulk insert)

        Args:
            force: If True, re-run load even if already complete
            local: If True, execute locally against remote databases (using public IPs)

        Returns:
            True if load completed successfully, False otherwise
        """
        console.print(f"[bold blue]Starting load phase: {self.project_id}[/bold blue]")

        context = self._create_execution_context(local_override=local)

        # Create workload instance for data generation
        workload = create_workload(self.config["workload"])

        # Run load phase using unified executor
        phase = self._load_phase_config()
        result = self._execute_phase(phase, context, force=force, workload=workload)
        # Load phase always returns bool (collects_results=False)
        assert isinstance(result, bool)
        return result

    def _create_system_for_local_execution(
        self,
        system_config: dict[str, Any],
        instance_manager: Any,
        output_callback: Callable[[str], None] | None = None,
    ) -> "SystemUnderTest":
        """Create system object configured for local-to-remote execution.

        IMPORTANT: Uses the PUBLIC IP from the cloud instance manager to enable
        connection from local machine to remote database. This is different from
        remote execution which uses private IPs (for package running ON the instance).

        IP Selection:
        - Local-to-remote (--local): Use PUBLIC IP (accessible from internet)
        - Remote execution (default): Use localhost or private IP (on instance)

        Args:
            system_config: System configuration dictionary
            instance_manager: Cloud instance manager (or list for multinode)
            output_callback: Optional callback for thread-safe logging in parallel execution

        Returns:
            SystemUnderTest instance configured with public IP
        """
        import copy

        kind = system_config["kind"]
        name = system_config["name"]
        setup = system_config.get("setup", {})

        # CRITICAL: Use PUBLIC IP for local-to-remote execution
        # (private IP is only accessible from within the VPC)
        if isinstance(instance_manager, list):
            # Multinode: use first/coordinator node's PUBLIC IP
            public_ip = instance_manager[0].public_ip
            console.print(
                f"[dim]  Using public IP for {name}: {public_ip} (coordinator node)[/dim]"
            )
        else:
            public_ip = instance_manager.public_ip
            console.print(f"[dim]  Using public IP for {name}: {public_ip}[/dim]")

        if not public_ip:
            raise ValueError(
                f"No public IP available for {name}. "
                "Ensure instances have public IPs assigned in infrastructure config."
            )

        # Create modified setup config with public IP as host
        modified_setup = copy.deepcopy(setup)
        modified_setup["host"] = public_ip

        # For Exasol installer method, also set host_external_addrs
        if kind == "exasol" and setup.get("method") == "installer":
            modified_setup["host_external_addrs"] = public_ip

        # For local-to-remote execution, use local data directory instead of remote /data
        # This avoids trying to create directories on remote systems
        modified_setup["use_additional_disk"] = False
        modified_setup["data_dir"] = "./data"

        # Create modified config for system instantiation
        modified_config = copy.deepcopy(system_config)
        modified_config["setup"] = modified_setup

        return create_system(
            modified_config,
            output_callback=output_callback,
            workload_config=self.config.get("workload", {}),
        )

    def run_queries(self, force: bool = False, local: bool = False) -> bool:
        """
        Phase 3: Execute benchmark queries only.

        This phase handles:
        - Warmup query execution
        - Measured query execution
        - Result collection and saving

        Args:
            force: If True, re-run queries even if results exist
            local: If True, execute locally against remote databases (using public IPs)

        Returns:
            True if queries completed successfully, False otherwise
        """
        console.print(
            f"[bold blue]Starting query execution: {self.project_id}[/bold blue]"
        )

        # Check if results already exist
        runs_file = self.output_dir / "runs.csv"
        if runs_file.exists() and not force:
            console.print(
                f"[yellow]Skipping benchmark - results already exist:[/] {runs_file}"
            )
            console.print("[dim]Use --force to overwrite existing results[/dim]")
            return True

        context = self._create_execution_context(local_override=local)

        # Create workload instance for query execution
        workload = create_workload(self.config["workload"])

        # Run query phase using unified executor
        phase = self._query_phase_config()
        results = self._execute_phase(phase, context, force=force, workload=workload)

        # Save results if we got any
        if isinstance(results, list) and results:
            warmup = getattr(self, "_all_warmup_results", [])
            self._save_benchmark_results(results, warmup)
            console.print(f"[green]✅ Results saved to: {self.output_dir}[/green]")
            return True
        elif isinstance(results, bool):
            return results
        else:
            console.print("[red]❌ No results collected[/red]")
            return False

    def _execute_load_remotely(
        self,
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path,
        executor: "ParallelExecutor | None" = None,
    ) -> bool:
        """Deploy load package and execute data loading remotely.

        Args:
            system_config: System configuration dictionary
            instance_manager: Cloud instance manager (or list for multinode)
            package_path: Path to the package to deploy
            executor: ParallelExecutor instance for parallel output (optional)

        Returns:
            True if load succeeded, False otherwise
        """
        try:
            # Handle multinode case: use primary node
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            project_id = self.config["project_id"]
            system_name = system_config["name"]

            # Deploy package
            self._log_output(
                f"📦 Deploying load package to {system_name}...",
                executor,
                system_name,
            )
            if not self._deploy_minimal_package(
                primary_manager, package_path, project_id
            ):
                return False

            # Calculate timeout based on scale factor
            execution_timeout = self._get_workload_execution_timeout()
            timeout_hours = execution_timeout / 3600

            # Execute load
            self._log_output(
                f"📤 Loading data on {system_name} (timeout: {timeout_hours:.1f}h)...",
                executor,
                system_name,
            )

            # Create streaming callback for remote output with local tagging
            def stream_remote_output(line: str, stream_name: str) -> None:
                # Add system tag prefix for parallel output identification
                tagged_line = f"[{system_name}] {line}"
                if stream_name == "stderr":
                    tagged_line = f"[{system_name}] [stderr] {line}"
                self._log_output(tagged_line, executor, system_name)

            load_result = primary_manager.run_remote_command(
                f"cd /home/ubuntu/{project_id} && ./load_data.sh {system_name}",
                timeout=execution_timeout,
                debug=True,
                stream_callback=stream_remote_output,
            )

            if load_result.get("success"):
                # Collect load completion info
                remote_load_complete = f"/home/ubuntu/{project_id}/results/{project_id}/load_complete_{system_name}.json"
                local_load_complete = self._get_load_complete_path(system_name)

                if primary_manager.copy_file_from_instance(
                    remote_load_complete, local_load_complete
                ):
                    self._log_output(
                        f"✅ Load completion info collected from {system_name}",
                        executor,
                        system_name,
                    )
                else:
                    # Create local marker if remote collection failed
                    self._save_load_complete(system_name)
                    self._log_output(
                        f"✅ Load completed for {system_name}",
                        executor,
                        system_name,
                    )

                return True
            else:
                self._log_output(
                    f"[red]Data loading failed on {system_name}[/red]",
                    executor,
                    system_name,
                )
                return False

        except Exception as e:
            self._log_output(
                f"[red]Remote data loading failed: {e}[/red]",
                executor,
                system_name if "system_name" in dir() else None,
            )
            return False

    def run_full_benchmark(self) -> bool:
        """Run the complete benchmark with all three phases."""
        console.print(f"[bold blue]Starting benchmark: {self.project_id}[/bold blue]")

        # Phase 1: Setup
        if not self.run_setup():
            console.print("[red]❌ Setup phase failed[/red]")
            return False

        # Phase 2: Load data
        if not self.run_load():
            console.print("[red]❌ Load phase failed[/red]")
            return False

        # Phase 3: Execute queries
        if not self.run_queries():
            console.print("[red]❌ Query execution failed[/red]")
            return False

        console.print("[bold green]✅ Benchmark completed successfully![/bold green]")
        return True

    def _setup_cloud_infrastructure(self) -> bool:
        """Setup cloud infrastructure connection and managers."""
        from ..common.cli_helpers import (
            get_cloud_ssh_key_path,
            get_first_cloud_provider,
        )
        from ..util import Timer

        try:
            from ..infra.manager import CloudInstanceManager, InfraManager

            cloud_provider = get_first_cloud_provider(self.config)
            if not cloud_provider:
                console.print("[red]❌ No cloud provider found in config[/red]")
                return False

            console.print(
                f"🔗 Connecting to {cloud_provider.upper()} infrastructure..."
            )

            # Initialize infrastructure manager
            infra_manager = InfraManager(cloud_provider, self.config)

            # Check if instances exist, provision if needed
            with Timer("Infrastructure provisioning") as provision_timer:
                instance_info = infra_manager.get_instance_info()

                # If no instances found, try to provision them
                if "error" in instance_info or not instance_info:
                    console.print(
                        "[yellow]⚠ No instances found, provisioning infrastructure...[/yellow]"
                    )

                    # Apply infrastructure
                    apply_result = infra_manager.apply(wait_for_init=True)
                    if not apply_result.success:
                        console.print(
                            f"[red]❌ Failed to provision infrastructure: {apply_result.error}[/red]"
                        )
                        return False

                    # Get instance info after provisioning
                    instance_info = infra_manager.get_instance_info()
                    self.infrastructure_provisioning_time = provision_timer.elapsed
                    console.print(
                        f"[green]✅ Infrastructure provisioned in {provision_timer.elapsed:.2f}s[/green]"
                    )
                else:
                    # Instances already exist - load provisioning time from saved file
                    self.infrastructure_provisioning_time = (
                        self._load_provisioning_timing()
                    )
                    console.print(
                        f"[green]✅ Using existing infrastructure (provisioned in {self.infrastructure_provisioning_time:.2f}s)[/green]"
                    )

            if "error" in instance_info:
                console.print(
                    f"[red]❌ Failed to get instance info: {instance_info['error']}[/red]"
                )
                return False

            # Create cloud instance managers for each system
            ssh_private_key_path = get_cloud_ssh_key_path(self.config)
            for system_name, system_info in instance_info.items():
                if system_name != "error" and system_info:
                    # Check if this is a multinode system
                    if system_info.get("multinode", False):
                        # Create a list of instance managers for multinode
                        node_managers = []
                        for node_info in system_info["nodes"]:
                            node_manager = CloudInstanceManager(
                                node_info, ssh_private_key_path
                            )
                            node_managers.append(node_manager)

                        self._cloud_instance_managers[system_name] = node_managers
                        node_count = len(node_managers)
                        primary_ip = node_managers[0].public_ip
                        console.print(
                            f"[green]✅ Connected to {system_name}: {node_count} nodes (primary: {primary_ip})[/green]"
                        )

                        # Set environment variables for IP resolution (use comma-separated lists for multinode)
                        import os

                        private_ips = ",".join(
                            [
                                str(mgr.private_ip)
                                for mgr in node_managers
                                if mgr.private_ip
                            ]
                        )
                        public_ips = ",".join(
                            [
                                str(mgr.public_ip)
                                for mgr in node_managers
                                if mgr.public_ip
                            ]
                        )
                        private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                        public_ip_var = f"{system_name.upper()}_PUBLIC_IP"
                        os.environ[private_ip_var] = private_ips
                        os.environ[public_ip_var] = public_ips
                    else:
                        # Single node system
                        instance_manager = CloudInstanceManager(
                            system_info, ssh_private_key_path
                        )
                        self._cloud_instance_managers[system_name] = instance_manager
                        console.print(
                            f"[green]✅ Connected to {system_name}: {system_info.get('public_ip', 'N/A')}[/green]"
                        )

                        # Set environment variables for IP resolution
                        import os

                        private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                        public_ip_var = f"{system_name.upper()}_PUBLIC_IP"
                        os.environ[private_ip_var] = system_info.get("private_ip", "")
                        os.environ[public_ip_var] = system_info.get("public_ip", "")

            if not self._cloud_instance_managers:
                console.print("[red]❌ No cloud instances found[/red]")
                return False

            return True

        except Exception as e:
            console.print(f"[red]❌ Infrastructure setup failed: {e}[/red]")
            return False

    def _prepare_storage_phase(self) -> bool:
        """Phase 0.5: Prepare storage (partition disks) before system installation."""
        console.print("\n[bold blue]💾 Preparing Storage for Systems[/bold blue]")

        # Create workload instance to determine storage needs
        from ..workloads import create_workload

        workload_config = self.config.get("workload", {})

        try:
            workload = create_workload(workload_config)
        except Exception as e:
            console.print(
                f"[yellow]⚠️  Could not create workload for storage prep: {e}[/yellow]"
            )
            console.print("[dim]Systems will use default storage configuration[/dim]")
            return True  # Non-critical, continue with defaults

        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            console.print(f"\n🔧 Preparing storage for: [bold]{system_name}[/bold]")

            try:
                system = create_system(
                    system_config, workload_config=self.config.get("workload", {})
                )
                instance_manager = self._cloud_instance_managers.get(system_name)

                if not instance_manager:
                    console.print(
                        f"[yellow]⚠️  No instance manager for {system_name}, skipping storage prep[/yellow]"
                    )
                    continue

                # Set cloud instance manager on the system
                if hasattr(system, "set_cloud_instance_manager"):
                    system.set_cloud_instance_manager(instance_manager)

                # First setup storage (RAID0 if multiple disks)
                # This must happen BEFORE get_data_generation_directory which partitions the disk
                system.setup_storage(workload)

                # Then partition the disk/RAID and get data generation directory
                # This will partition disks if needed and store partition info in system instance
                data_dir = system.get_data_generation_directory(workload)

                if data_dir:
                    console.print(f"[green]✅ Storage prepared: {data_dir}[/green]")
                else:
                    console.print(
                        f"[dim]✅ Using default storage for {system_name}[/dim]"
                    )

                # Save the system instance with partition info for later use
                # Store it temporarily so installation phase can use the same instance
                if not hasattr(self, "_prepared_systems"):
                    self._prepared_systems = {}
                self._prepared_systems[system_name] = system

            except Exception as e:
                console.print(
                    f"[yellow]⚠️  Storage preparation warning for {system_name}: {e}[/yellow]"
                )
                console.print(
                    "[dim]System will use default storage configuration[/dim]"
                )
                # Continue with other systems

        console.print("[green]✅ Storage preparation phase completed[/green]")
        return True

    def _execute_queries(
        self, system: "SystemUnderTest", workload: "Workload"
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Execute benchmark queries with timing and monitoring."""
        runs_per_query = self.config["workload"]["runs_per_query"]
        warmup_runs = self.config["workload"]["warmup_runs"]

        # Extract multiuser configuration
        multiuser_config = self.config["workload"].get("multiuser") or {}
        num_streams = 1
        randomize = False
        random_seed = None

        if multiuser_config.get("enabled", False):
            num_streams = multiuser_config.get("num_streams", 1)
            randomize = multiuser_config.get("randomize", False)
            random_seed = multiuser_config.get("random_seed", None)

        # Execute queries
        result_dict = workload.run_workload(
            system=system,
            query_names=workload.get_included_queries(),
            runs_per_query=runs_per_query,
            warmup_runs=warmup_runs,
            num_streams=num_streams,
            randomize=randomize,
            random_seed=random_seed,
        )

        # Extract measured and warmup results
        measured_results = result_dict.get("measured", [])
        warmup_results = result_dict.get("warmup", [])

        return measured_results, warmup_results

    def _save_benchmark_results(
        self,
        results: list[dict[str, Any]],
        warmup_results: list[dict[str, Any]] | None = None,
    ) -> None:
        """Save benchmark results to files."""
        if not results:
            console.print("[yellow]No results to save[/yellow]")
            return

        # Convert to DataFrame and save CSV
        df = normalize_runs(results)
        csv_path = self.output_dir / "runs.csv"
        df.to_csv(csv_path, index=False)

        console.print(f"Results saved to: {csv_path}")

        # Save warmup results if present
        warmup_df = None
        if warmup_results:
            warmup_df = normalize_runs(warmup_results)
            warmup_csv_path = self.output_dir / "runs_warmup.csv"
            warmup_df.to_csv(warmup_csv_path, index=False)
            console.print(f"Warmup results saved to: {warmup_csv_path}")

        # Save raw results as JSON
        json_path = self.output_dir / "raw_results.json"
        save_json(results, json_path)

        # Create summary statistics (pass warmup_df and config)
        summary = self._create_summary_stats(df, warmup_df, self.config)
        summary_path = self.output_dir / "summary.json"
        save_json(summary, summary_path)

    def _save_system_metrics(self, system_name: str, metrics: dict[str, Any]) -> None:
        """Save system-specific metrics."""
        metrics_path = self.output_dir / f"metrics_{system_name}.json"
        save_json(metrics, metrics_path)

    def _save_setup_summary(
        self, system_name: str, setup_summary: dict[str, Any]
    ) -> None:
        """Save system setup summary for report reproduction."""
        setup_path = self.output_dir / f"setup_{system_name}.json"
        save_json(setup_summary, setup_path)

    def _load_setup_summary_to_system(
        self,
        system: "SystemUnderTest",
        system_name: str,
        executor: "ParallelExecutor | None" = None,
    ) -> None:
        """Load previously saved setup summary back into system object."""
        setup_path = self.output_dir / f"setup_{system_name}.json"
        if setup_path.exists():
            try:
                setup_summary = load_json(setup_path)

                # Restore setup commands to system
                if "commands" in setup_summary:
                    # Get commands grouped by category
                    commands_by_category = setup_summary["commands"]

                    # Flatten all commands back into setup_commands list
                    for _category, commands in commands_by_category.items():
                        for cmd in commands:
                            system.setup_commands.append(cmd)

                # Restore installation notes
                if "installation_notes" in setup_summary:
                    system.installation_notes = setup_summary["installation_notes"]

                self._log_output(
                    f"[dim]  Loaded {len(system.setup_commands)} setup commands from previous run[/dim]",
                    executor,
                    system_name,
                )
            except Exception as e:
                self._log_output(
                    f"[yellow]  Warning: Could not load setup summary: {e}[/yellow]",
                    executor,
                    system_name,
                )

    def _create_summary_stats(
        self,
        df: pd.DataFrame,
        warmup_df: pd.DataFrame | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create summary statistics from results."""
        summary = {
            "total_queries": len(df),
            "systems": df["system"].unique().tolist(),
            "query_names": df["query"].unique().tolist(),
            "run_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Add variant information from config
        if config and "workload" in config:
            workload_config = config["workload"]
            summary["variant"] = workload_config.get("variant", "official")
            if (
                "system_variants" in workload_config
                and workload_config["system_variants"]
            ):
                summary["system_variants"] = workload_config["system_variants"]

            # Add multiuser configuration
            multiuser_config = workload_config.get("multiuser") or {}
            if multiuser_config.get("enabled", False):
                summary["execution_mode"] = "multiuser"
                summary["multiuser"] = {
                    "num_streams": multiuser_config.get("num_streams", 1),
                    "randomize": multiuser_config.get("randomize", False),
                    "random_seed": multiuser_config.get("random_seed"),
                }
            else:
                summary["execution_mode"] = "sequential"

        # Per-system statistics
        summary["per_system"] = {}
        for system in df["system"].unique():
            system_df = df[df["system"] == system]
            summary["per_system"][system] = {
                "total_queries": len(system_df),
                "avg_runtime_ms": float(system_df["elapsed_ms"].mean()),
                "median_runtime_ms": float(system_df["elapsed_ms"].median()),
                "min_runtime_ms": float(system_df["elapsed_ms"].min()),
                "max_runtime_ms": float(system_df["elapsed_ms"].max()),
            }

        # Per-query statistics
        summary["per_query"] = {}
        for query in df["query"].unique():
            query_df = df[df["query"] == query]
            systems = query_df["system"].unique().tolist()

            per_system_stats: dict[str, dict[str, float | int]] = {}
            for system in systems:
                system_query_df = query_df[query_df["system"] == system]
                per_system_stats[system] = {
                    "runs": int(len(system_query_df)),
                    "avg_runtime_ms": float(system_query_df["elapsed_ms"].mean()),
                    "median_runtime_ms": float(system_query_df["elapsed_ms"].median()),
                    "min_runtime_ms": float(system_query_df["elapsed_ms"].min()),
                    "max_runtime_ms": float(system_query_df["elapsed_ms"].max()),
                }

            summary["per_query"][query] = {
                "systems": systems,
                "per_system": per_system_stats,
            }

        # Add per-stream statistics if multiuser execution was used
        # Calculate per-stream stats for each system separately
        if "stream_id" in df.columns and df["stream_id"].notna().any():
            summary["per_stream"] = {}

            for system in df["system"].unique():
                system_df = df[df["system"] == system]
                summary["per_stream"][system] = {}

                for stream_id in sorted(system_df["stream_id"].dropna().unique()):
                    stream_df = system_df[system_df["stream_id"] == stream_id]
                    summary["per_stream"][system][int(stream_id)] = {
                        "queries_executed": len(stream_df),
                        "avg_runtime_ms": float(stream_df["elapsed_ms"].mean()),
                        "median_runtime_ms": float(stream_df["elapsed_ms"].median()),
                        "min_runtime_ms": float(stream_df["elapsed_ms"].min()),
                        "max_runtime_ms": float(stream_df["elapsed_ms"].max()),
                    }

        # Add warmup statistics if available
        if warmup_df is not None and len(warmup_df) > 0:
            summary["warmup_statistics"] = {
                "total_warmup_queries": len(warmup_df),
                "per_system": {},
                "per_query": {},
            }

            # Warmup per-system statistics
            for system in warmup_df["system"].unique():
                system_warmup_df = warmup_df[warmup_df["system"] == system]
                summary["warmup_statistics"]["per_system"][system] = {
                    "total_queries": len(system_warmup_df),
                    "avg_runtime_ms": float(system_warmup_df["elapsed_ms"].mean()),
                    "median_runtime_ms": float(system_warmup_df["elapsed_ms"].median()),
                    "min_runtime_ms": float(system_warmup_df["elapsed_ms"].min()),
                    "max_runtime_ms": float(system_warmup_df["elapsed_ms"].max()),
                }

            # Warmup per-query statistics (aggregated across warmup runs)
            normalized_warmup_df = warmup_df.copy()
            normalized_warmup_df["base_query"] = normalized_warmup_df["query"].apply(
                lambda name: (
                    name.rsplit("_warmup_", 1)[0] if "_warmup_" in name else name
                )
            )

            for base_query in normalized_warmup_df["base_query"].unique():
                query_warmup_df = normalized_warmup_df[
                    normalized_warmup_df["base_query"] == base_query
                ]
                summary["warmup_statistics"]["per_query"][base_query] = {}

                for system in query_warmup_df["system"].unique():
                    system_query_warmup_df = query_warmup_df[
                        query_warmup_df["system"] == system
                    ]
                    summary["warmup_statistics"]["per_query"][base_query][system] = {
                        "total_runs": int(len(system_query_warmup_df)),
                        "avg_runtime_ms": float(
                            system_query_warmup_df["elapsed_ms"].mean()
                        ),
                    }

        return summary

    def _setup_infrastructure(self) -> None:
        """Set up cloud infrastructure if environment mode requires it."""
        from ..common.cli_helpers import (
            get_cloud_ssh_key_path,
            get_first_cloud_provider,
            is_any_system_cloud_mode,
        )

        if not is_any_system_cloud_mode(self.config):
            return

        cloud_provider = get_first_cloud_provider(self.config)
        if not cloud_provider:
            console.print(
                "[yellow]Warning: Cloud mode detected but no provider found[/yellow]"
            )
            return

        try:
            from ..infra.manager import CloudInstanceManager, InfraManager

            console.print(
                f"[blue]Setting up {cloud_provider.upper()} infrastructure...[/blue]"
            )

            # Initialize infrastructure manager
            infra_manager = InfraManager(cloud_provider, self.config)

            # Get instance information (assumes infrastructure is already deployed)
            instance_info = infra_manager.get_instance_info()

            if "error" not in instance_info:
                # Create separate cloud instance managers for each system
                ssh_private_key_path = get_cloud_ssh_key_path(self.config)
                for system_name, system_info in instance_info.items():
                    if system_name != "error" and system_info:
                        # Check if this is a multinode system
                        is_multinode = system_info.get("multinode", False)

                        if is_multinode:
                            # Multinode: validate nodes have IPs and create managers
                            nodes = system_info.get("nodes", [])
                            if not nodes:
                                console.print(
                                    f"[yellow]Warning: {system_name} has no node info (infrastructure may be destroyed)[/yellow]"
                                )
                                continue

                            # Check first node has valid IP
                            if not nodes[0].get("public_ip"):
                                console.print(
                                    f"[yellow]Warning: {system_name} nodes have no public IPs (infrastructure may be destroyed)[/yellow]"
                                )
                                continue

                            # Create list of managers for each node
                            node_managers = []
                            for node_info in nodes:
                                if node_info.get("public_ip"):
                                    node_managers.append(
                                        CloudInstanceManager(
                                            node_info, ssh_private_key_path
                                        )
                                    )

                            if not node_managers:
                                console.print(
                                    f"[yellow]Warning: {system_name} has no reachable nodes[/yellow]"
                                )
                                continue

                            self._cloud_instance_managers[system_name] = node_managers
                            primary_ip = node_managers[0].public_ip
                            console.print(
                                f"[green]✓ Connected to {system_name}: {len(node_managers)} nodes (primary: {primary_ip})[/green]"
                            )

                            # Set environment variables (comma-separated for multinode)
                            import os

                            private_ips = ",".join(
                                str(mgr.private_ip)
                                for mgr in node_managers
                                if mgr.private_ip
                            )
                            public_ips = ",".join(
                                str(mgr.public_ip)
                                for mgr in node_managers
                                if mgr.public_ip
                            )
                            private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                            public_ip_var = f"{system_name.upper()}_PUBLIC_IP"
                            os.environ[private_ip_var] = private_ips
                            os.environ[public_ip_var] = public_ips

                            console.print(
                                f"[blue]Set {private_ip_var}={private_ips}[/blue]"
                            )
                            console.print(
                                f"[blue]Set {public_ip_var}={public_ips}[/blue]"
                            )

                            # Wait for SSH on primary node
                            console.print(
                                f"Waiting for {system_name} SSH access (primary node)..."
                            )
                            if node_managers[0].wait_for_ssh():
                                console.print(
                                    f"[green]✓ {system_name} SSH access ready[/green]"
                                )
                            else:
                                console.print(
                                    f"[yellow]Warning: {system_name} SSH access not confirmed[/yellow]"
                                )
                        else:
                            # Single-node: validate public_ip exists
                            public_ip = system_info.get("public_ip", "")
                            if not public_ip:
                                console.print(
                                    f"[yellow]Warning: {system_name} has no public IP (infrastructure may be destroyed)[/yellow]"
                                )
                                continue

                            instance_manager = CloudInstanceManager(
                                system_info, ssh_private_key_path
                            )
                            self._cloud_instance_managers[system_name] = (
                                instance_manager
                            )
                            console.print(
                                f"[green]✓ Connected to {system_name} instance: {public_ip}[/green]"
                            )

                            # Set environment variables for IP resolution
                            import os

                            private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                            public_ip_var = f"{system_name.upper()}_PUBLIC_IP"

                            os.environ[private_ip_var] = system_info.get(
                                "private_ip", ""
                            )
                            os.environ[public_ip_var] = public_ip

                            console.print(
                                f"[blue]Set {private_ip_var}={os.environ[private_ip_var]}[/blue]"
                            )
                            console.print(
                                f"[blue]Set {public_ip_var}={os.environ[public_ip_var]}[/blue]"
                            )

                            # Wait for SSH to be ready
                            console.print(f"Waiting for {system_name} SSH access...")
                            if instance_manager.wait_for_ssh():
                                console.print(
                                    f"[green]✓ {system_name} SSH access ready[/green]"
                                )
                            else:
                                console.print(
                                    f"[yellow]Warning: {system_name} SSH access not confirmed[/yellow]"
                                )
            else:
                console.print(
                    f"[yellow]Warning: Could not get instance info: {instance_info['error']}[/yellow]"
                )

        except ImportError as e:
            console.print(
                f"[yellow]Warning: Infrastructure management not available: {e}[/yellow]"
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Infrastructure setup failed: {e}[/yellow]")

    def _check_system_state(self, system: Any, instance_manager: Any) -> str:
        """
        Enhanced system state detection with comprehensive checks.

        Returns one of:
        - NEEDS_INSTALLATION: System not installed or broken installation
        - NEEDS_SERVICE_RESTART: System installed but services down
        - NEEDS_DB_RESTART: Services running but database not accessible
        - READY: System fully operational
        """
        system_name = system.name

        try:
            # Handle multinode case: check ALL nodes for multinode systems
            is_multinode = (
                isinstance(instance_manager, list) and len(instance_manager) > 1
            )

            # 1. Check system-specific installation marker
            marker_file = system.get_install_marker_path()
            if marker_file:
                if is_multinode:
                    # For multinode, check markers on ALL nodes
                    # If ANY node is missing the marker, we need to install
                    missing_markers = []
                    for idx, node_manager in enumerate(instance_manager):
                        marker_result = node_manager.run_remote_command(
                            f"test -f {marker_file} && echo 'marker_found' || echo 'no_marker'",
                            debug=False,
                        )

                        if not (
                            marker_result.get("success")
                            and "marker_found" in marker_result.get("stdout", "")
                        ):
                            missing_markers.append(idx)

                    if missing_markers:
                        console.print(
                            f"🔍 {system_name}: Missing installation markers on node(s): {missing_markers}"
                        )
                        return "NEEDS_INSTALLATION"
                else:
                    # Single node check
                    primary_manager = (
                        instance_manager[0]
                        if isinstance(instance_manager, list)
                        else instance_manager
                    )
                    marker_result = primary_manager.run_remote_command(
                        f"test -f {marker_file} && echo 'marker_found' || echo 'no_marker'",
                        debug=False,
                    )

                    if not (
                        marker_result.get("success")
                        and "marker_found" in marker_result.get("stdout", "")
                    ):
                        console.print(
                            f"🔍 {system_name}: No installation marker ({marker_file})"
                        )
                        return "NEEDS_INSTALLATION"

            # 2. System-specific checks based on system type
            for system_config in self.config["systems"]:
                if system_config["name"] == system_name:
                    break
                else:
                    system_config = None
            if not system_config:
                raise SystemError(f"System {system_name} not found")
            system = create_system(system_config)

            if system.is_healthy():
                return "READY"

            return "NEEDS_SERVICE_RESTART"

        except Exception as e:
            console.print(f"[yellow]⚠️ {system_name}: State check failed: {e}[/yellow]")
            return "NEEDS_INSTALLATION"

    def _install_system_remotely(
        self,
        system: Any,
        instance_manager: Any,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> bool:
        """Install system via remote commands (recorded for reports)."""
        try:
            # Check if this is a multinode system
            is_multinode = (
                isinstance(instance_manager, list) and len(instance_manager) > 1
            )

            # For multinode systems, DON'T override execute_command
            # Let the system handle its own multinode installation logic
            if is_multinode:
                # Multinode systems handle their own remote execution
                self._log_output(
                    f"Installing on multinode cluster ({len(instance_manager)} nodes)...",
                    executor,
                    system_name,
                )
                success: bool = system.install()

                if success:
                    marker_path = system.get_install_marker_path()
                    if marker_path:
                        # For multinode, create markers on ALL nodes
                        markers_created = 0
                        for idx, node_manager in enumerate(instance_manager):
                            # Check if marker exists on this node
                            check_result = node_manager.run_remote_command(
                                f"test -f {marker_path} && echo 'exists' || echo 'missing'",
                                debug=False,
                            )

                            if check_result.get(
                                "success"
                            ) and "missing" in check_result.get("stdout", ""):
                                # Create marker on this node
                                marker_result = node_manager.run_remote_command(
                                    f"touch {marker_path}",
                                    debug=False,
                                )
                                if marker_result.get("success"):
                                    markers_created += 1
                                    self._log_output(
                                        f"✅ Node {idx}: Installation marker created: {marker_path}",
                                        executor,
                                        system_name,
                                    )
                                else:
                                    self._log_output(
                                        f"[yellow]⚠️ Node {idx}: Failed to create installation marker[/yellow]",
                                        executor,
                                        system_name,
                                    )
                            elif "exists" in check_result.get("stdout", ""):
                                self._log_output(
                                    f"✓ Node {idx}: Installation marker already exists",
                                    executor,
                                    system_name,
                                )

                        if markers_created > 0:
                            self._log_output(
                                f"✅ Created installation markers on {markers_created} node(s)",
                                executor,
                                system_name,
                            )

                return success

            # Single node: override execute_command to use remote execution
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            # Override the system's execute_command to use remote execution
            original_execute = system.execute_command

            def remote_execute_command(
                cmd: str,
                timeout: int = 300,
                record: bool = True,
                category: str = "installation",
            ) -> dict[str, Any]:
                # Show command being executed
                self._log_output(f"[dim]$ {cmd}[/dim]", executor, system_name)

                # Create streaming callback for local tagging
                def tag_output(line: str, stream_name: str) -> None:
                    tagged_line = f"[{system_name}] {line}"
                    if stream_name == "stderr":
                        tagged_line = f"[{system_name}] [stderr] {line}"
                    self._log_output(tagged_line, executor, system_name)

                result = primary_manager.run_remote_command(
                    cmd,
                    timeout=timeout,
                    debug=is_debug_enabled(),  # Use global debug state
                    stream_callback=tag_output,  # Local tagging via callback
                )

                # Show command result status
                if result.get("success"):
                    self._log_output(
                        "[green]✓ Command completed successfully[/green]",
                        executor,
                        system_name,
                    )
                else:
                    self._log_output(
                        "[red]✗ Command failed[/red]", executor, system_name
                    )
                    if result.get("stderr"):
                        self._log_output(
                            f"[red]Error: {result.get('stderr')}[/red]",
                            executor,
                            system_name,
                        )

                return dict(result) if result else {}

            system.execute_command = remote_execute_command

            try:
                success = system.install()

                if success:
                    marker_path = system.get_install_marker_path()
                    if marker_path and not system.has_install_marker():
                        if system.mark_installed(record=False):
                            self._log_output(
                                f"✅ Installation marker created: {marker_path}",
                                executor,
                                system_name,
                            )
                        else:
                            self._log_output(
                                f"[yellow]⚠️ Failed to create installation marker: {marker_path}[/yellow]",
                                executor,
                                system_name,
                            )

                return success
            finally:
                system.execute_command = original_execute

        except Exception as e:
            self._log_output(
                f"[red]Installation failed: {e}[/red]", executor, system_name
            )
            return False

    def _restart_system_remotely(
        self,
        system: Any,
        instance_manager: Any,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> bool:
        """Restart system via remote commands."""
        try:
            # Handle multinode case: use primary node for command execution
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            system_kind = system.kind

            if system_kind == "exasol":
                # For Exasol, restart the c4_cloud_command service
                self._log_output(
                    "[dim]$ sudo systemctl restart c4_cloud_command[/dim]",
                    executor,
                    system_name,
                )
                restart_result = primary_manager.run_remote_command(
                    "sudo systemctl restart c4_cloud_command", debug=True
                )
                if not restart_result.get("success"):
                    self._log_output(
                        "[red]❌ Failed to restart c4_cloud_command service[/red]",
                        executor,
                        system_name,
                    )
                    if restart_result.get("stderr"):
                        self._log_output(
                            f"[red]Error: {restart_result.get('stderr')}[/red]",
                            executor,
                            system_name,
                        )
                    return False

                self._log_output(
                    f"✅ Restarted c4_cloud_command service for {system.name}",
                    executor,
                    system_name,
                )

                # Wait for Exasol cluster to be ready again
                self._log_output(
                    "⏳ Waiting for Exasol cluster to be ready...",
                    executor,
                    system_name,
                )
                if not self._wait_for_exasol_ready(primary_manager):
                    self._log_output(
                        "[red]❌ Exasol cluster failed to become ready after restart[/red]",
                        executor,
                        system_name,
                    )
                    return False

                self._log_output("✅ Exasol cluster is ready", executor, system_name)

                # Clean up interfering services again (restart may bring them back)
                self._log_output(
                    "🧹 Cleaning up interfering services after restart...",
                    executor,
                    system_name,
                )
                cleanup_success = self._cleanup_exasol_services(system, primary_manager)
                if cleanup_success:
                    self._log_output(
                        "✅ Service cleanup completed after restart",
                        executor,
                        system_name,
                    )
                else:
                    self._log_output(
                        "[yellow]⚠️ Service cleanup had issues, but continuing[/yellow]",
                        executor,
                        system_name,
                    )

                return True

            elif system_kind == "clickhouse":
                # For ClickHouse, restart the clickhouse-server service
                self._log_output(
                    "[dim]$ sudo systemctl restart clickhouse-server[/dim]",
                    executor,
                    system_name,
                )
                restart_result = primary_manager.run_remote_command(
                    "sudo systemctl restart clickhouse-server", debug=True
                )
                if not restart_result.get("success"):
                    self._log_output(
                        "[red]❌ Failed to restart clickhouse-server service[/red]",
                        executor,
                        system_name,
                    )
                    if restart_result.get("stderr"):
                        self._log_output(
                            f"[red]Error: {restart_result.get('stderr')}[/red]",
                            executor,
                            system_name,
                        )
                    return False

                self._log_output(
                    f"✅ Restarted clickhouse-server service for {system.name}",
                    executor,
                    system_name,
                )

                # Wait for ClickHouse to be ready again
                self._log_output(
                    "⏳ Waiting for ClickHouse to be ready...", executor, system_name
                )
                if not self._wait_for_clickhouse_ready(instance_manager):
                    self._log_output(
                        "[red]❌ ClickHouse failed to become ready after restart[/red]",
                        executor,
                        system_name,
                    )
                    return False

                self._log_output("✅ ClickHouse is ready", executor, system_name)
                return True

            else:
                # Generic system restart - try common service restart
                self._log_output(
                    f"[yellow]⚠️ Unknown system type '{system_kind}', skipping restart[/yellow]",
                    executor,
                    system_name,
                )
                return True

        except Exception as e:
            self._log_output(f"[red]Restart failed: {e}[/red]", executor, system_name)
            return False

    def _wait_for_exasol_ready(
        self, instance_manager: Any, max_attempts: int = 30
    ) -> bool:
        """Wait for Exasol cluster to be ready after restart."""
        import time

        for attempt in range(max_attempts):
            # Check if database port is accessible
            db_result = instance_manager.run_remote_command(
                "timeout 5 bash -c '</dev/tcp/localhost/8563' 2>/dev/null && echo 'db_accessible' || echo 'db_not_accessible'",
                debug=False,
            )

            db_accessible = db_result.get(
                "success"
            ) and "db_accessible" in db_result.get("stdout", "")

            if db_accessible:
                # Get the play_id to check init status
                play_id_result = instance_manager.run_remote_command(
                    "c4 ps | tail -n +2 | head -1 | awk '{print $2}'",
                    debug=False,
                )

                if (
                    play_id_result.get("success")
                    and play_id_result.get("stdout", "").strip()
                ):
                    play_id = play_id_result.get("stdout", "").strip()

                    # Check if initialization is complete
                    init_result = instance_manager.run_remote_command(
                        f"c4 connect -s cos -i {play_id} -- cat /exa/etc/init_done",
                        debug=False,
                    )

                    if (
                        init_result.get("success")
                        and init_result.get("stdout", "").strip()
                    ):
                        init_timestamp = init_result.get("stdout", "").strip()
                        console.print(
                            f"[green]✓ Exasol ready - init timestamp: {init_timestamp}[/green]"
                        )
                        return True

            # Debug info every 3rd attempt
            if attempt % 3 == 0:
                console.print(f"[dim]Debug: DB port accessible: {db_accessible}[/dim]")

            if attempt < max_attempts - 1:
                console.print(
                    f"⏳ Cluster not ready yet, waiting... ({max_attempts - attempt - 1} attempts remaining)"
                )
                time.sleep(10)  # Wait 10 seconds between checks

        return False

    def _wait_for_clickhouse_ready(
        self, instance_manager: Any, max_attempts: int = 20
    ) -> bool:
        """Wait for ClickHouse to be ready after restart."""
        import time

        for attempt in range(max_attempts):
            # Check if ClickHouse process is running and ports are accessible
            process_result = instance_manager.run_remote_command(
                "pgrep -f 'clickhouse-server' >/dev/null && echo 'process_running' || echo 'process_not_running'",
                debug=False,
            )

            if process_result.get(
                "success"
            ) and "process_running" in process_result.get("stdout", ""):
                # Check database port accessibility
                db_result = instance_manager.run_remote_command(
                    "timeout 5 bash -c '</dev/tcp/localhost/9000' 2>/dev/null && echo 'db_accessible' || timeout 5 bash -c '</dev/tcp/localhost/8123' 2>/dev/null && echo 'db_accessible' || echo 'db_not_accessible'",
                    debug=False,
                )
                if db_result.get("success") and "db_accessible" in db_result.get(
                    "stdout", ""
                ):
                    return True

            if attempt < max_attempts - 1:
                console.print(
                    f"⏳ ClickHouse not ready yet, waiting... ({max_attempts - attempt - 1} attempts remaining)"
                )
                time.sleep(5)  # Wait 5 seconds between checks

        return False

    def _cleanup_exasol_services(self, system: Any, instance_manager: Any) -> bool:
        """Clean up interfering Exasol services after restart."""
        try:
            # Override the system's execute_command to use remote execution
            original_execute = system.execute_command

            def remote_execute_command(
                cmd: str,
                timeout: int = 300,
                record: bool = True,
                category: str = "installation",
            ) -> dict[str, Any]:
                result = instance_manager.run_remote_command(
                    cmd, timeout=timeout, debug=False
                )
                return dict(result) if result else {}

            system.execute_command = remote_execute_command

            # Call the service cleanup method if it exists
            if hasattr(system, "_cleanup_disturbing_services"):
                success: bool = system._cleanup_disturbing_services()
                system.execute_command = original_execute
                return success
            else:
                console.print(
                    "[yellow]⚠️ No service cleanup method available for this system[/yellow]"
                )
                system.execute_command = original_execute
                return True

        except Exception as e:
            console.print(f"[yellow]⚠️ Service cleanup failed: {e}[/yellow]")
            return False

    def _get_workload_execution_timeout(self) -> int:
        """
        Calculate appropriate timeout for workload execution based on scale factor.

        Returns timeout in seconds. Can be overridden via config.

        Default timeouts based on scale factor:
        - SF <= 10: 3600s (1 hour)
        - SF 30: 7200s (2 hours)
        - SF 100: 14400s (4 hours)
        - SF 300+: 21600s (6 hours)
        """
        # Check if timeout explicitly configured
        workload_config = self.config.get("workload", {})
        if "execution_timeout" in workload_config:
            return int(workload_config["execution_timeout"])

        # Calculate based on scale factor
        scale_factor = workload_config.get("scale_factor", 1)

        if scale_factor <= 10:
            return 3600  # 1 hour
        elif scale_factor <= 30:
            return 7200  # 2 hours
        elif scale_factor <= 100:
            return 14400  # 4 hours
        else:
            return 21600  # 6 hours

    def _create_package(self) -> Path | None:
        """Create a package containing workload execution components."""
        try:
            from ..package.creator import create_workload_zip

            return create_workload_zip(self.config)
        except Exception as e:
            console.print(f"[red]Package creation failed: {e}[/red]")
            return None

    def _execute_workload_remotely(
        self,
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path,
        executor: "ParallelExecutor | None" = None,
    ) -> list[dict[str, Any]] | None:
        """Deploy minimal package and execute workload remotely."""
        try:
            # Handle multinode case: use primary node for workload execution
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            project_id = self.config["project_id"]
            system_name = system_config["name"]

            # Deploy package
            self._log_output(
                f"📦 Deploying workload package to {system_name}...",
                executor,
                system_name,
            )
            if not self._deploy_minimal_package(
                primary_manager, package_path, project_id
            ):
                return None

            # Calculate appropriate timeout based on scale factor
            execution_timeout = self._get_workload_execution_timeout()
            timeout_hours = execution_timeout / 3600

            # Execute workload
            self._log_output(
                f"🚀 Executing workload on {system_name} (timeout: {timeout_hours:.1f}h)...",
                executor,
                system_name,
            )

            # Create streaming callback for remote output with local tagging
            def stream_remote_output(line: str, stream_name: str) -> None:
                # Add system tag prefix for parallel output identification
                tagged_line = f"[{system_name}] {line}"
                if stream_name == "stderr":
                    tagged_line = f"[{system_name}] [stderr] {line}"
                self._log_output(tagged_line, executor, system_name)

            workload_result = primary_manager.run_remote_command(
                f"cd /home/ubuntu/{project_id} && ./run_queries.sh {system_name}",
                timeout=execution_timeout,
                debug=True,
                stream_callback=stream_remote_output,
            )

            command_success = workload_result.get("success")
            returncode = workload_result.get("returncode", -1)

            # Check if command timed out
            timed_out = returncode == -1 and not command_success

            if command_success:
                # Normal successful completion
                return self._collect_workload_results(
                    primary_manager, project_id, system_name, executor
                )
            elif timed_out:
                # Command timed out, but workload may have completed successfully
                # Check the output for completion marker
                stdout = workload_result.get("stdout", "")
                if (
                    "Completed workload" in stdout
                    or "✓ Workload execution completed" in stdout
                ):
                    self._log_output(
                        f"[yellow]⚠️ SSH command timed out after {timeout_hours:.1f}h, but workload appears to have completed[/yellow]",
                        executor,
                        system_name,
                    )
                    self._log_output(
                        f"[yellow]Attempting to collect results from {system_name}...[/yellow]",
                        executor,
                        system_name,
                    )
                    # Attempt to collect results despite timeout
                    results = self._collect_workload_results(
                        primary_manager, project_id, system_name, executor
                    )
                    if results:
                        self._log_output(
                            f"[green]✅ Successfully recovered results from {system_name} after timeout[/green]",
                            executor,
                            system_name,
                        )
                        return results
                    else:
                        self._log_output(
                            f"[red]❌ Failed to collect results from {system_name} after timeout[/red]",
                            executor,
                            system_name,
                        )
                        return None
                else:
                    self._log_output(
                        f"[red]❌ Workload execution timed out on {system_name} after {timeout_hours:.1f}h[/red]",
                        executor,
                        system_name,
                    )
                    return None
            else:
                # Command failed for reasons other than timeout
                self._log_output(
                    f"[red]Workload execution failed on {system_name}[/red]",
                    executor,
                    system_name,
                )
                return None

        except Exception as e:
            self._log_output(
                f"[red]Remote workload execution failed: {e}[/red]",
                executor,
                system_name,
            )
            return None

    def _deploy_minimal_package(
        self, instance_manager: Any, package_path: Path, project_id: str
    ) -> bool:
        """Deploy minimal package to remote instance."""
        try:
            # Copy package
            remote_path = f"/home/ubuntu/{package_path.name}"
            if not instance_manager.copy_file_to_instance(package_path, remote_path):
                return False

            # Extract package
            extract_commands = [
                f"rm -rf /home/ubuntu/{project_id}",
                f"mkdir -p /home/ubuntu/{project_id}",
                f"cd /home/ubuntu && unzip -o -q {package_path.name} -d {project_id}",
                f"cd /home/ubuntu/{project_id} && python3 -m pip install -r requirements.txt",
            ]

            for cmd in extract_commands:
                result = instance_manager.run_remote_command(cmd, debug=False)
                if not result.get("success"):
                    console.print(f"[red]Deploy command failed: {cmd}[/red]")
                    return False

            return True

        except Exception as e:
            console.print(f"[red]Package deployment failed: {e}[/red]")
            return False

    def _collect_workload_results(
        self,
        instance_manager: Any,
        project_id: str,
        system_name: str,
        executor: "ParallelExecutor | None" = None,
    ) -> list[dict[str, Any]] | None:
        """Collect workload results from remote instance."""
        try:
            # Copy results file
            remote_results = f"/home/ubuntu/{project_id}/results/{project_id}/runs.csv"
            local_results = self.output_dir / f"runs_{system_name}.csv"
            remote_warmup = (
                f"/home/ubuntu/{project_id}/results/{project_id}/runs_warmup.csv"
            )
            local_warmup = self.output_dir / f"runs_{system_name}_warmup.csv"

            # Also collect preparation timings
            remote_prep = f"/home/ubuntu/{project_id}/results/{project_id}/preparation_{system_name}.json"
            local_prep = self.output_dir / f"preparation_{system_name}.json"

            if instance_manager.copy_file_from_instance(remote_results, local_results):
                # Load CSV results and convert to list of dicts
                df = pd.read_csv(local_results)
                results = []
                for res in df.to_dict("records"):
                    dat = {}
                    for k, v in res.items():
                        dat[str(k)] = v
                    results.append(dat)

                # Try to collect warmup results (optional)
                warmup_records: list[dict[str, Any]] = []
                if instance_manager.copy_file_from_instance(
                    remote_warmup, local_warmup
                ):
                    warmup_df = pd.read_csv(local_warmup)
                    for rec in warmup_df.to_dict("records"):
                        warmup_records.append({str(k): v for k, v in rec.items()})

                    if warmup_records:
                        if not hasattr(self, "_all_warmup_results"):
                            self._all_warmup_results = []
                        self._all_warmup_results.extend(warmup_records)
                        self._log_output(
                            f"✅ Warmup results collected from {system_name}",
                            executor,
                            system_name,
                        )
                else:
                    self._log_output(
                        f"[dim]No warmup results from {system_name}[/dim]",
                        executor,
                        system_name,
                    )

                # Try to collect preparation timings (may not exist if skipped)
                if instance_manager.copy_file_from_instance(remote_prep, local_prep):
                    self._log_output(
                        f"✅ Results and preparation timings collected from {system_name}",
                        executor,
                        system_name,
                    )
                else:
                    self._log_output(
                        f"✅ Results collected from {system_name} (no preparation timings)",
                        executor,
                        system_name,
                    )

                return results
            else:
                self._log_output(
                    f"[red]Failed to collect results from {system_name}[/red]",
                    executor,
                    system_name,
                )
                return None

        except Exception as e:
            self._log_output(
                f"[red]Result collection failed: {e}[/red]",
                executor,
                system_name,
            )
            return None


def run_benchmark(config: dict[str, Any], output_dir: Path) -> bool:
    """
    Main entry point for running benchmarks.

    Args:
        config: Benchmark configuration
        output_dir: Directory to save results

    Returns:
        True if benchmark completed successfully, False otherwise
    """
    runner = BenchmarkRunner(config, output_dir)
    return runner.run_full_benchmark()
