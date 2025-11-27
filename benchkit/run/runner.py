"""Benchmark execution runner."""

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console

from ..debug import is_debug_enabled
from ..systems import create_system
from ..systems.base import SystemUnderTest
from ..util import ensure_directory, load_json, save_json
from ..workloads import create_workload
from .parallel_executor import ParallelExecutor
from .parsers import normalize_runs

console = Console()


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
        import json

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
        import json

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
        import json

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

    def run_full_benchmark(self) -> bool:
        """Run the complete benchmark with new two-phase architecture."""
        console.print(f"[bold blue]Starting benchmark: {self.project_id}[/bold blue]")

        # Determine execution mode
        env_config = self.config.get("env", {})
        env_mode = env_config.get("mode", "local")

        if env_mode in ["aws", "gcp", "azure"]:
            console.print(f"[blue]Cloud mode detected: {env_mode.upper()}[/blue]")
            return self._run_cloud_benchmark()
        else:
            console.print("[blue]Local mode detected[/blue]")
            return self._run_local_benchmark()

    def _run_cloud_benchmark(self) -> bool:
        """Run benchmark on cloud infrastructure with two-phase approach."""
        console.print("[bold blue]🏗️  Phase 1: System Setup[/bold blue]")

        # Setup cloud infrastructure connection
        if not self._setup_cloud_infrastructure():
            return False

        # Phase 0.5: Prepare storage (partition disks) before system installation
        if not self._prepare_storage_phase():
            console.print("[red]❌ Storage preparation phase failed[/red]")
            return False

        # Phase 1: Setup all systems via remote commands
        if not self._setup_phase():
            console.print("[red]❌ Setup phase failed[/red]")
            return False

        console.print(
            "[bold blue]🚀 Phase 2: Workload Execution (Minimal Package)[/bold blue]"
        )

        # Phase 2: Execute workload with minimal package
        if not self._workload_execution_phase():
            console.print("[red]❌ Workload execution phase failed[/red]")
            return False

        console.print("[bold green]✅ Benchmark completed successfully![/bold green]")
        return True

    def _setup_cloud_infrastructure(self) -> bool:
        """Setup cloud infrastructure connection and managers."""
        from ..util import Timer

        try:
            from ..infra.manager import CloudInstanceManager, InfraManager

            env_config = self.config.get("env", {})
            env_mode = env_config.get("mode", "local")

            console.print(f"🔗 Connecting to {env_mode.upper()} infrastructure...")

            # Initialize infrastructure manager
            infra_manager = InfraManager(env_mode, self.config)

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
            ssh_private_key_path = env_config.get("ssh_private_key_path")
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
                system.setup_storage(workload.scale_factor)

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

                # Save setup commands recorded during storage prep
                # This ensures commands are preserved even if system is already installed
                setup_summary = system.get_setup_summary()
                if setup_summary.get("commands"):
                    self._save_setup_summary(system_name, setup_summary)

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

    def _setup_phase(self) -> bool:
        """Phase 1: Setup all systems via remote commands."""
        # Only parallelize if enabled AND multiple systems exist
        if self.use_parallel and len(self.config["systems"]) > 1:
            console.print("[dim]Using parallel execution mode[/dim]")
            return self._setup_phase_parallel()
        else:
            return self._setup_phase_sequential()

    def _setup_phase_sequential(self) -> bool:
        """Phase 1: Setup all systems sequentially (original implementation)."""
        from ..util import Timer

        console.print("📋 Setting up and probing systems via remote commands...")

        # Initialize setup timings
        self.setup_timings = {}

        all_systems_ready = True

        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            console.print(f"\n🔧 Processing system: [bold]{system_name}[/bold]")

            # Initialize per-system timings
            system_timings = {}

            # Use prepared system instance if available (to preserve partition info)
            # Otherwise create new system instance
            if (
                hasattr(self, "_prepared_systems")
                and system_name in self._prepared_systems
            ):
                system = self._prepared_systems[system_name]
                console.print(
                    "[dim]Using prepared system instance with storage configuration[/dim]"
                )
            else:
                system = create_system(
                    system_config, workload_config=self.config.get("workload", {})
                )

            # Get cloud instance manager for this system
            if system_name not in self._cloud_instance_managers:
                console.print(
                    f"[red]❌ No cloud instance manager for {system_name}[/red]"
                )
                all_systems_ready = False
                continue

            instance_manager = self._cloud_instance_managers[system_name]

            # Set cloud instance manager on the system object
            if hasattr(system, "set_cloud_instance_manager"):
                system.set_cloud_instance_manager(instance_manager)

            # Check system state and decide action
            state = self._check_system_state(system, instance_manager)
            console.print(f"📊 System state: [blue]{state}[/blue]")

            if state == "NEEDS_INSTALLATION":
                console.print(f"🚀 Installing {system_name}...")
                with Timer(f"Installation for {system_name}") as timer:
                    install_success = self._install_system_remotely(
                        system, instance_manager
                    )

                system_timings["installation_s"] = timer.elapsed

                if not install_success:
                    console.print(
                        f"[red]❌ Installation failed for {system_name}[/red]"
                    )
                    all_systems_ready = False
                    continue
                else:
                    console.print(
                        f"[dim]✓ Installation completed in {timer.elapsed:.2f}s[/dim]"
                    )
                    # Save installation timing for future runs
                    self._save_installation_timing(system_name, timer.elapsed)

                    # Save setup summary for report reproduction
                    setup_summary = system.get_setup_summary()
                    self._save_setup_summary(system_name, setup_summary)

            elif state in ["NEEDS_SERVICE_RESTART", "NEEDS_DB_RESTART"]:
                console.print(f"🔄 Restarting {system_name}...")

                # Load previously saved setup summary if available (before restart)
                self._load_setup_summary_to_system(system, system_name)

                with Timer(f"Restart for {system_name}") as timer:
                    restart_success = self._restart_system_remotely(
                        system, instance_manager
                    )

                system_timings["restart_s"] = timer.elapsed
                # Also load previous installation timing if available
                system_timings["installation_s"] = self._load_installation_timing(
                    system_name
                )

                if not restart_success:
                    console.print(f"[red]❌ Restart failed for {system_name}[/red]")
                    all_systems_ready = False
                    continue
                else:
                    console.print(
                        f"[dim]✓ Restart completed in {timer.elapsed:.2f}s[/dim]"
                    )

                    # Save setup summary (includes previously loaded + any new commands)
                    setup_summary = system.get_setup_summary()
                    if setup_summary.get("commands"):
                        self._save_setup_summary(system_name, setup_summary)

            elif state == "READY":
                # Load previously saved installation timing
                saved_timing = self._load_installation_timing(system_name)
                system_timings["installation_s"] = saved_timing
                if saved_timing > 0:
                    console.print(
                        f"[green]✅ {system_name} already ready (installed in {saved_timing:.2f}s)[/green]"
                    )
                else:
                    console.print(f"[green]✅ {system_name} already ready[/green]")

                # Load previously saved setup summary if available
                self._load_setup_summary_to_system(system, system_name)

            # Store timings for this system
            self.setup_timings[system_name] = system_timings

        # Save setup timings to JSON file (including provisioning time)
        if self.setup_timings or hasattr(self, "infrastructure_provisioning_time"):
            import json

            infra_timings = {
                "infrastructure_provisioning_s": getattr(
                    self, "infrastructure_provisioning_time", 0.0
                ),
                "systems": self.setup_timings,
            }

            setup_timings_file = self.output_dir / "infrastructure_setup.json"
            with open(setup_timings_file, "w") as f:
                json.dump(infra_timings, f, indent=2)
            console.print(
                f"[dim]✓ Infrastructure setup timings saved to {setup_timings_file}[/dim]"
            )

        return all_systems_ready

    def _setup_phase_parallel(self) -> bool:
        """
        Phase 1: Setup all systems in parallel.

        Thread Safety:
        - Each system operates on separate AWS instance
        - System objects are independent (no shared mutable state)
        - File writes use unique filenames (system_name prefix)
        - Timing collection happens after parallel execution completes

        Returns:
            True if all systems ready, False otherwise
        """
        console.print("📋 Setting up and probing systems via remote commands...")

        # Initialize setup timings (single-threaded before parallel execution)
        self.setup_timings = {}

        # Create parallel executor
        executor = ParallelExecutor(max_workers=self.max_workers)

        # Build tasks dictionary
        tasks = {}
        for system_config in self.config["systems"]:
            system_name = system_config["name"]

            # Create lambda with system_config captured in default arg
            # This avoids closure issues with loop variable
            def make_task(
                cfg: dict[str, Any], ex: ParallelExecutor
            ) -> Callable[[], tuple[bool, dict[str, Any]] | None]:
                return lambda: self._setup_single_system(cfg, ex)

            tasks[system_name] = make_task(system_config, executor)

        # Execute in parallel with live display
        results = executor.execute_parallel(
            tasks, "Installing Systems", log_dir=self.parallel_log_dir
        )

        # Collect results (thread-safe: all parallel work is done)
        all_systems_ready = True
        for system_name, result in results.items():
            if result is None:
                all_systems_ready = False
                continue

            success, timings = result
            if not success:
                all_systems_ready = False

            # Write timings (no lock needed, parallel phase complete)
            self.setup_timings[system_name] = timings

        # Save setup timings to JSON file
        if self.setup_timings or hasattr(self, "infrastructure_provisioning_time"):
            infra_timings = {
                "infrastructure_provisioning_s": getattr(
                    self, "infrastructure_provisioning_time", 0.0
                ),
                "systems": self.setup_timings,
            }

            setup_timings_file = self.output_dir / "infrastructure_setup.json"
            with open(setup_timings_file, "w") as f:
                json.dump(infra_timings, f, indent=2)
            console.print(
                f"[dim]✓ Infrastructure setup timings saved to {setup_timings_file}[/dim]"
            )

        return all_systems_ready

    def _setup_single_system(
        self, system_config: dict, executor: ParallelExecutor
    ) -> tuple[bool, dict] | None:
        """
        Setup single system (called in parallel thread).

        Thread Safety:
        - Operates on separate AWS instance (no resource sharing)
        - No shared mutable state with other systems
        - All file writes use system_name prefix (unique)
        - Returns result instead of modifying shared state directly

        Args:
            system_config: Configuration for this system
            executor: ParallelExecutor for status updates

        Returns:
            Tuple of (success: bool, timings: dict) or None on error
        """
        from ..util import Timer

        system_name = system_config["name"]
        system_timings: dict[str, Any] = {}

        try:
            # Create output callback for thread-safe logging
            def output_callback(msg: str) -> None:
                executor.add_output(system_name, msg)

            # Get prepared system instance (read-only access, thread-safe)
            if (
                hasattr(self, "_prepared_systems")
                and system_name in self._prepared_systems
            ):
                system = self._prepared_systems[system_name]
                # Set output callback on prepared system for parallel execution
                system._output_callback = output_callback
                executor.add_output(system_name, "Using prepared system instance")
            else:
                system = create_system(
                    system_config,
                    output_callback=output_callback,
                    workload_config=self.config.get("workload", {}),
                )

            # Get cloud instance manager (read-only access, thread-safe)
            instance_manager = self._cloud_instance_managers.get(system_name)
            if not instance_manager:
                executor.update_status(system_name, "❌ No instance manager")
                return (False, system_timings)

            # Set cloud instance manager
            if hasattr(system, "set_cloud_instance_manager"):
                system.set_cloud_instance_manager(instance_manager)

            # Check system state
            state = self._check_system_state(system, instance_manager)
            executor.update_status(system_name, f"State: {state}")

            if state == "NEEDS_INSTALLATION":
                executor.update_status(system_name, "⏳ Installing...")

                with Timer(f"Installation for {system_name}") as timer:
                    install_success = self._install_system_remotely(
                        system, instance_manager, executor, system_name
                    )

                system_timings["installation_s"] = timer.elapsed

                if not install_success:
                    executor.update_status(system_name, "❌ Installation failed")
                    return (False, system_timings)

                # Save installation timing (unique filename, thread-safe)
                self._save_installation_timing(system_name, timer.elapsed)

                # Save setup summary (unique filename, thread-safe)
                setup_summary = system.get_setup_summary()
                self._save_setup_summary(system_name, setup_summary)

                executor.update_status(
                    system_name, f"✅ Installed ({timer.elapsed:.0f}s)"
                )

            elif state in ["NEEDS_SERVICE_RESTART", "NEEDS_DB_RESTART"]:
                executor.update_status(system_name, "⏳ Restarting...")

                # Load previously saved setup summary
                self._load_setup_summary_to_system(system, system_name, executor)

                with Timer(f"Restart for {system_name}") as timer:
                    restart_success = self._restart_system_remotely(
                        system, instance_manager, executor, system_name
                    )

                system_timings["restart_s"] = timer.elapsed

                if not restart_success:
                    executor.update_status(system_name, "❌ Restart failed")
                    return (False, system_timings)

                # Save setup summary
                setup_summary = system.get_setup_summary()
                if setup_summary.get("commands"):
                    self._save_setup_summary(system_name, setup_summary)

                executor.update_status(system_name, "✅ Restarted")

            elif state == "READY":
                # Load previously saved installation timing
                saved_timing = self._load_installation_timing(system_name)
                system_timings["installation_s"] = saved_timing

                # Load previously saved setup summary
                self._load_setup_summary_to_system(system, system_name, executor)

                if saved_timing > 0:
                    executor.update_status(
                        system_name, f"✅ Ready ({saved_timing:.0f}s)"
                    )
                else:
                    executor.update_status(system_name, "✅ Ready")

            return (True, system_timings)

        except Exception as e:
            executor.update_status(system_name, f"❌ Error: {str(e)[:30]}")
            # Log error to executor buffer instead of console
            executor.add_output(system_name, f"Error: {e}")
            import traceback

            error_trace = traceback.format_exc()
            executor.add_output(system_name, error_trace)
            return (False, system_timings)

    def _workload_execution_phase(self) -> bool:
        """Phase 2: Execute workload."""
        # Only parallelize if enabled AND multiple systems exist
        if self.use_parallel and len(self.config["systems"]) > 1:
            return self._workload_execution_parallel()
        else:
            return self._workload_execution_sequential()

    def _workload_execution_sequential(self) -> bool:
        """Phase 2: Execute workload sequentially (original implementation)."""
        console.print("📦 Creating workload package...")

        # Create minimal package (workload code only)
        package_path = self._create_workload_package()
        if not package_path:
            console.print("[red]❌ Failed to create workload package[/red]")
            return False

        console.print(f"✅ Package created: {package_path}")

        # Execute workload on each system
        all_results = []
        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            console.print(f"\n🚀 Executing workload on [bold]{system_name}[/bold]")

            instance_manager = self._cloud_instance_managers.get(system_name)
            if not instance_manager:
                console.print(f"[red]❌ No instance manager for {system_name}[/red]")
                continue

            # Deploy and execute minimal package
            results = self._execute_workload_remotely(
                system_config, instance_manager, package_path
            )
            if results:
                all_results.extend(results)
                console.print(f"[green]✅ {system_name} workload completed[/green]")
            else:
                console.print(f"[red]❌ {system_name} workload failed[/red]")

        if all_results:
            warmup_results = getattr(self, "_all_warmup_results", [])
            self._save_benchmark_results(all_results, warmup_results)
            console.print(f"[green]✅ Results saved to: {self.output_dir}[/green]")
            return True
        else:
            console.print("[red]❌ No results to save[/red]")
            return False

    def _workload_execution_parallel(self) -> bool:
        """
        Phase 2: Execute workload in parallel.

        Thread Safety:
        - Each system executes on separate AWS instance
        - Workload package deployed independently
        - Results collected with thread-safe operations
        - No shared mutable state during parallel execution
        """
        console.print("📦 Creating workload package...")

        # Create minimal package (single-threaded, before parallel execution)
        package_path = self._create_workload_package()
        if not package_path:
            console.print("[red]❌ Failed to create workload package[/red]")
            return False

        console.print(f"✅ Package created: {package_path}")

        # Create parallel executor
        executor = ParallelExecutor(max_workers=self.max_workers)

        # Build tasks dictionary
        tasks = {}
        for system_config in self.config["systems"]:
            system_name = system_config["name"]
            instance_manager = self._cloud_instance_managers.get(system_name)

            if not instance_manager:
                console.print(f"[red]❌ No instance manager for {system_name}[/red]")
                continue

            # Capture variables in default args to avoid closure issues
            def make_workload_task(
                cfg: dict[str, Any], mgr: Any, pkg: Path, exec_ref: ParallelExecutor
            ) -> Callable[[], list[dict[str, Any]] | None]:
                return lambda: self._execute_workload_remotely(
                    cfg, mgr, pkg, executor=exec_ref
                )

            tasks[system_name] = make_workload_task(
                system_config, instance_manager, package_path, executor
            )

        # Execute in parallel with live display
        results = executor.execute_parallel(
            tasks, "Executing Workloads", log_dir=self.parallel_log_dir
        )

        # Collect results (thread-safe: parallel execution complete)
        all_results = []
        for system_name, system_results in results.items():
            if system_results:
                all_results.extend(system_results)
                console.print(f"[green]✅ {system_name} workload completed[/green]")
            else:
                console.print(f"[red]❌ {system_name} workload failed[/red]")

        if all_results:
            warmup_results = getattr(self, "_all_warmup_results", [])
            self._save_benchmark_results(all_results, warmup_results)
            console.print(f"[green]✅ Results saved to: {self.output_dir}[/green]")
            return True
        else:
            console.print("[red]❌ No results to save[/red]")
            return False

    def _run_local_benchmark(self) -> bool:
        """Run benchmark locally (original workflow)."""
        # Create workload
        workload = create_workload(self.config["workload"])
        console.print(f"Workload: {workload.name} (SF={workload.scale_factor})")

        all_results = []
        failed_systems = []

        for system_config in self.config["systems"]:
            console.print(
                f"\n[yellow]Running benchmark on {system_config['name']}...[/yellow]"
            )

            try:
                system_results = self._run_system_benchmark(system_config, workload)
                if system_results:
                    all_results.extend(system_results)
                    console.print(f"[green]✓ {system_config['name']} completed[/green]")
                else:
                    failed_systems.append(system_config["name"])
                    console.print(f"[red]✗ {system_config['name']} failed[/red]")

            except Exception as e:
                console.print(f"[red]✗ {system_config['name']} failed: {e}[/red]")
                failed_systems.append(system_config["name"])

        # Save results (including warmup results if any were collected)
        warmup_results = getattr(self, "_all_warmup_results", [])
        self._save_benchmark_results(all_results, warmup_results)

        # Summary
        success_count = len(self.config["systems"]) - len(failed_systems)
        console.print("\n[bold]Benchmark Summary:[/bold]")
        console.print(
            f"Successful systems: {success_count}/{len(self.config['systems'])}"
        )
        if failed_systems:
            console.print(f"Failed systems: {', '.join(failed_systems)}")

        return len(failed_systems) == 0

    def _run_system_benchmark(
        self, system_config: dict[str, Any], workload: Any
    ) -> list[dict[str, Any]]:
        """Run benchmark on a single system (local execution only)."""
        system_name = system_config["name"]

        # Use prepared system instance if available (preserves partition info)
        if hasattr(self, "_prepared_systems") and system_name in self._prepared_systems:
            system = self._prepared_systems[system_name]
            console.print(
                "  [dim]Using prepared system instance with storage configuration[/dim]"
            )
        else:
            system = create_system(system_config)

        # For local execution, we don't use cloud instance managers
        # Remote execution is handled separately by _run_remote_benchmark()

        try:
            # Check if system is already installed to avoid redundant work
            if system.is_already_installed():
                console.print(
                    f"  [green]✓ {system.name} already installed, skipping installation[/green]"
                )
            else:
                # Install and start system
                console.print(f"  Installing {system.name}...")
                if not system.install():
                    console.print("  [red]Installation failed[/red]")
                    return []

            if not system.start():
                console.print("  [red]Failed to start[/red]")
                return []

            # Wait for system to be healthy
            console.print(f"  Waiting for {system.name} to be ready...")
            if not system.wait_for_health():
                console.print("  [red]System not healthy[/red]")
                return []

            # Prepare workload
            console.print("  Preparing workload...")
            if not workload.prepare(system):
                console.print("  [red]Workload preparation failed[/red]")
                return []

            # Run benchmark queries
            console.print("  Executing queries...")
            measured_results, warmup_results = self._execute_queries(system, workload)

            # Store warmup results for later saving (use instance variable to preserve across systems)
            if not hasattr(self, "_all_warmup_results"):
                self._all_warmup_results = []
            self._all_warmup_results.extend(warmup_results)

            # Get system metrics
            console.print("  Collecting system metrics...")
            metrics = system.get_system_metrics()
            self._save_system_metrics(system.name, metrics)

            # Save setup summary for report reproduction
            setup_summary = system.get_setup_summary()
            self._save_setup_summary(system.name, setup_summary)

            return measured_results

        finally:
            # Cleanup only if not preserving systems for manual rerun
            preserve_systems = self.config.get("preserve_systems_for_rerun", False)

            if preserve_systems:
                console.print(
                    f"  Preserving {system.name} for manual rerun (no cleanup)"
                )
                console.print(f"  {system.name} is still running and accessible")
            else:
                try:
                    console.print(f"  Cleaning up {system.name}...")
                    system.teardown()
                except Exception as e:
                    console.print(f"  [yellow]Warning: cleanup failed: {e}[/yellow]")

    def _execute_queries(
        self, system: Any, workload: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Execute benchmark queries with timing and monitoring."""
        query_names = self.config["workload"]["queries"]["include"]
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
            query_names=query_names,
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
        system: SystemUnderTest,
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
        env_config = self.config.get("env", {})
        env_mode = env_config.get("mode", "local")

        if env_mode in ["aws", "gcp", "azure"]:
            try:
                from ..infra.manager import CloudInstanceManager, InfraManager

                console.print(
                    f"[blue]Setting up {env_mode.upper()} infrastructure...[/blue]"
                )

                # Initialize infrastructure manager
                infra_manager = InfraManager(env_mode, self.config)

                # Get instance information (assumes infrastructure is already deployed)
                instance_info = infra_manager.get_instance_info()

                if "error" not in instance_info:
                    # Create separate cloud instance managers for each system
                    ssh_private_key_path = env_config.get("ssh_private_key_path")
                    for system_name, system_info in instance_info.items():
                        if system_name != "error" and system_info:
                            instance_manager = CloudInstanceManager(
                                system_info, ssh_private_key_path
                            )
                            self._cloud_instance_managers[system_name] = (
                                instance_manager
                            )
                            console.print(
                                f"[green]✓ Connected to {system_name} instance: {system_info.get('public_ip', 'N/A')}[/green]"
                            )

                            # Set environment variables for IP resolution
                            import os

                            private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                            public_ip_var = f"{system_name.upper()}_PUBLIC_IP"

                            os.environ[private_ip_var] = system_info.get(
                                "private_ip", ""
                            )
                            os.environ[public_ip_var] = system_info.get("public_ip", "")

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
                console.print(
                    f"[yellow]Warning: Infrastructure setup failed: {e}[/yellow]"
                )
        else:
            console.print("[blue]Using local environment[/blue]")

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

                result = primary_manager.run_remote_command(
                    cmd,
                    timeout=timeout,
                    debug=is_debug_enabled(),  # Use global debug state
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

    def _create_workload_package(self) -> Path | None:
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

            def stream_remote_output(line: str, stream_name: str) -> None:
                prefix = "STDERR" if stream_name == "stderr" else "STDOUT"
                message = prefix if not line else f"{prefix}: {line}"
                self._log_output(message, executor, system_name)

            workload_result = primary_manager.run_remote_command(
                f"cd /home/ubuntu/{project_id} && ./execute_workload.sh {system_name}",
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

    def set_cloud_instance_managers(self, instance_managers: dict[str, Any]) -> None:
        """Set cloud instance managers directly (useful for testing)."""
        self._cloud_instance_managers = instance_managers


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
