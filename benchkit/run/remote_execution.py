"""Remote execution functionality for benchmark runner.

This module handles deploying packages and executing workloads on remote instances.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from rich.console import Console

from benchkit.common import exclude_from_package

if TYPE_CHECKING:
    from .parallel_executor import ParallelExecutor
    from .runner import BenchmarkRunner

console = Console()


class RemoteExecutor:
    """Handles remote workload execution on cloud instances."""

    def __init__(self, runner: "BenchmarkRunner"):
        """Initialize the remote executor.

        Args:
            runner: Parent BenchmarkRunner instance for shared state access
        """
        self._runner = runner

    def _log_output(
        self,
        message: str,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> None:
        """Route output to either parallel executor buffer or console."""
        self._runner._log_output(message, executor, system_name)

    @exclude_from_package
    def execute_workload(
        self,
        system_config: dict[str, Any],
        instance_manager: Any,
        package_path: Path,
        executor: "ParallelExecutor | None" = None,
    ) -> list[dict[str, Any]] | None:
        """Deploy minimal package and execute workload remotely.

        Args:
            system_config: System configuration dictionary
            instance_manager: Cloud instance manager (or list for multinode)
            package_path: Path to the package to deploy
            executor: ParallelExecutor instance for parallel output (optional)

        Returns:
            List of result dicts if successful, None otherwise
        """
        try:
            # Handle multinode case: use primary node for workload execution
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            project_id = self._runner.config["project_id"]
            system_name = system_config["name"]

            # Deploy package
            self._log_output(
                f"📦 Deploying workload package to {system_name}...",
                executor,
                system_name,
            )
            if not self.deploy_package(primary_manager, package_path, project_id):
                return None

            # Calculate appropriate timeout based on scale factor
            execution_timeout = self._runner._get_workload_execution_timeout()
            timeout_hours = execution_timeout / 3600

            # Execute workload
            self._log_output(
                f"🚀 Executing workload on {system_name} (timeout: {timeout_hours:.1f}h)...",
                executor,
                system_name,
            )

            # Create streaming callback for remote output
            # TailMonitor adds the [system_name] prefix, so we only mark stderr
            def stream_remote_output(line: str, stream_name: str) -> None:
                if stream_name == "stderr":
                    line = f"[stderr] {line}"
                self._log_output(line, executor, system_name)

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
                return self.collect_results(
                    primary_manager, project_id, system_name, executor
                )
            elif timed_out:
                # Command timed out, but workload may have completed successfully
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
                    results = self.collect_results(
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
                system_name if "system_name" in dir() else None,
            )
            return None

    @exclude_from_package
    def execute_load(
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

            project_id = self._runner.config["project_id"]
            system_name = system_config["name"]

            # Deploy package
            self._log_output(
                f"📦 Deploying load package to {system_name}...",
                executor,
                system_name,
            )
            if not self.deploy_package(primary_manager, package_path, project_id):
                return False

            # Calculate timeout based on scale factor and system type
            system_kind = system_config.get("kind")
            execution_timeout = self._runner._get_data_loading_timeout(system_kind)
            timeout_hours = execution_timeout / 3600

            # Execute load
            self._log_output(
                f"📤 Loading data on {system_name} (timeout: {timeout_hours:.1f}h)...",
                executor,
                system_name,
            )

            # Create streaming callback for remote output
            # TailMonitor adds the [system_name] prefix, so we only mark stderr
            def stream_remote_output(line: str, stream_name: str) -> None:
                if stream_name == "stderr":
                    line = f"[stderr] {line}"
                self._log_output(line, executor, system_name)

            load_result = primary_manager.run_remote_command(
                f"cd /home/ubuntu/{project_id} && ./load_data.sh {system_name}",
                timeout=execution_timeout,
                debug=False,
                stream_callback=stream_remote_output,
            )

            command_success = load_result.get("success")
            returncode = load_result.get("returncode", -1)

            # Check if command timed out
            timed_out = returncode == -1 and not command_success

            # Helper to collect load completion info
            def collect_load_completion() -> bool:
                remote_load_complete = f"/home/ubuntu/{project_id}/results/{project_id}/load_complete_{system_name}.json"
                local_load_complete = (
                    self._runner.output_dir / f"load_complete_{system_name}.json"
                )

                if primary_manager.copy_file_from_instance(
                    remote_load_complete, local_load_complete
                ):
                    self._log_output(
                        f"✅ Load completion info collected from {system_name}",
                        executor,
                        system_name,
                    )
                    return True
                else:
                    # Create local marker if remote collection failed
                    self._runner._save_load_complete(system_name)
                    self._log_output(
                        f"✅ Load completed for {system_name}",
                        executor,
                        system_name,
                    )
                    return True

            if command_success:
                collect_load_completion()
                return True
            elif timed_out:
                # Command timed out, but load may have completed successfully
                stdout = load_result.get("stdout", "")
                load_completed = (
                    "✓ Data loading completed" in stdout
                    or "Load completion marker saved" in stdout
                    or "✓ Load completion marker saved" in stdout
                    or "✓ Workload preparation completed" in stdout
                )

                if load_completed:
                    self._log_output(
                        f"[yellow]⚠️ SSH command timed out after {timeout_hours:.1f}h, "
                        f"but data loading appears to have completed[/yellow]",
                        executor,
                        system_name,
                    )
                    if collect_load_completion():
                        self._log_output(
                            f"[green]✅ Successfully recovered load status from {system_name} after timeout[/green]",
                            executor,
                            system_name,
                        )
                        return True
                    else:
                        self._log_output(
                            f"[red]❌ Failed to collect load completion from {system_name} after timeout[/red]",
                            executor,
                            system_name,
                        )
                        return False
                else:
                    self._log_output(
                        f"[red]❌ Data loading timed out on {system_name} after {timeout_hours:.1f}h[/red]",
                        executor,
                        system_name,
                    )
                    return False
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

    @exclude_from_package
    def deploy_package(
        self, instance_manager: Any, package_path: Path, project_id: str
    ) -> bool:
        """Deploy minimal package to remote instance.

        Copies the package zip, extracts it, and installs dependencies.
        Retries once on failure to handle transient transfer/extraction issues.

        Args:
            instance_manager: Cloud instance manager
            package_path: Path to the package zip file
            project_id: Project ID for destination directory

        Returns:
            True if deployment succeeded, False otherwise
        """
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            try:
                # Copy package
                remote_path = f"/home/ubuntu/{package_path.name}"
                if not instance_manager.copy_file_to_instance(
                    package_path, remote_path
                ):
                    console.print(
                        f"[red]Failed to copy package to instance: "
                        f"{package_path.name}[/red]"
                    )
                    if attempt < max_attempts:
                        console.print("[yellow]Retrying package deployment...[/yellow]")
                        continue
                    return False

                # Extract package
                extract_commands = [
                    f"rm -rf /home/ubuntu/{project_id}",
                    f"mkdir -p /home/ubuntu/{project_id}",
                    f"cd /home/ubuntu && unzip -o -q {package_path.name} -d {project_id}",
                    f"cd /home/ubuntu/{project_id} && python3 -m pip install -r requirements.txt",
                ]

                all_ok = True
                for cmd in extract_commands:
                    result = instance_manager.run_remote_command(cmd, debug=False)
                    if not result.get("success"):
                        stderr = result.get("stderr", "").strip()
                        stdout = result.get("stdout", "").strip()
                        error_detail = stderr or stdout or "no output"
                        console.print(
                            f"[red]Deploy command failed: {cmd}[/red]\n"
                            f"[red]  Error: {error_detail}[/red]"
                        )
                        all_ok = False
                        break

                if all_ok:
                    return True

                if attempt < max_attempts:
                    console.print("[yellow]Retrying package deployment...[/yellow]")

            except Exception as e:
                console.print(f"[red]Package deployment failed: {e}[/red]")
                if attempt < max_attempts:
                    console.print("[yellow]Retrying package deployment...[/yellow]")
                    continue
                return False

        return False

    @exclude_from_package
    def collect_results(
        self,
        instance_manager: Any,
        project_id: str,
        system_name: str,
        executor: "ParallelExecutor | None" = None,
    ) -> list[dict[str, Any]] | None:
        """Collect workload results from remote instance.

        Args:
            instance_manager: Cloud instance manager
            project_id: Project ID
            system_name: System name
            executor: ParallelExecutor for output routing

        Returns:
            List of result dicts if successful, None otherwise
        """
        try:
            # Copy results file
            remote_results = f"/home/ubuntu/{project_id}/results/{project_id}/runs.csv"
            local_results = self._runner.output_dir / f"runs_{system_name}.csv"
            remote_warmup = (
                f"/home/ubuntu/{project_id}/results/{project_id}/runs_warmup.csv"
            )
            local_warmup = self._runner.output_dir / f"runs_{system_name}_warmup.csv"

            # Also collect preparation timings from load_complete file
            # (load_complete_*.json contains full timing data including table sizes)
            remote_prep = f"/home/ubuntu/{project_id}/results/{project_id}/load_complete_{system_name}.json"
            local_prep = self._runner.output_dir / f"load_complete_{system_name}.json"

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
                        if not hasattr(self._runner, "_all_warmup_results"):
                            self._runner._all_warmup_results = []
                        self._runner._all_warmup_results.extend(warmup_records)
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

                # Try to collect preparation timings
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

    @exclude_from_package
    def install_system(
        self,
        system: Any,
        instance_manager: Any,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> bool:
        """Install system via remote commands (recorded for reports).

        Args:
            system: System instance
            instance_manager: Cloud instance manager (or list for multinode)
            executor: ParallelExecutor for output routing
            system_name: System name for logging

        Returns:
            True if installation succeeded, False otherwise
        """
        try:
            # Check if this is a multinode system
            is_multinode = (
                isinstance(instance_manager, list) and len(instance_manager) > 1
            )

            if is_multinode:
                # Multinode systems handle their own remote execution
                self._log_output(
                    f"Installing on multinode cluster ({len(instance_manager)} nodes)...",
                    executor,
                    system_name,
                )
                success: bool = system.install()

                if success:
                    self._log_output(
                        f"✓ {system.kind.title()} installation completed successfully",
                        executor,
                        system_name,
                    )
                    marker_path = system.get_install_marker_path()
                    if marker_path:
                        # Create installation markers on ALL nodes
                        markers_created = 0
                        for idx, node_manager in enumerate(instance_manager):
                            marker_result = node_manager.run_remote_command(
                                f"touch {marker_path}",
                                debug=False,
                            )
                            if marker_result.get("success"):
                                markers_created += 1
                            else:
                                self._log_output(
                                    f"[yellow]⚠️ Node {idx}: Failed to create installation marker[/yellow]",
                                    executor,
                                    system_name,
                                )

                        self._log_output(
                            f"✅ Installation markers created on {markers_created}/{len(instance_manager)} node(s)",
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

            original_execute = system.execute_command

            def remote_execute_command(
                cmd: str,
                timeout: int = 300,
                record: bool = True,
                category: str = "installation",
                node_info: str | None = None,
                description: str | None = None,
            ) -> dict[str, Any]:
                self._log_output(f"[dim]$ {cmd}[/dim]", executor, system_name)

                def tag_output(line: str, stream_name: str) -> None:
                    # TailMonitor adds the [system_name] prefix, so we only mark stderr
                    if stream_name == "stderr":
                        line = f"[stderr] {line}"
                    self._log_output(line, executor, system_name)

                # Use runner's explicit debug flag, not is_debug_enabled() which
                # checks env var and causes debug spam during parallel execution
                result = primary_manager.run_remote_command(
                    cmd,
                    timeout=timeout,
                    debug=self._runner._debug,
                    stream_callback=tag_output,
                )

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
                    self._log_output(
                        f"✓ {system.kind.title()} installation completed successfully",
                        executor,
                        system_name,
                    )
                    marker_path = system.get_install_marker_path()
                    if marker_path:
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

    @exclude_from_package
    def restart_system(
        self,
        system: Any,
        instance_manager: Any,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> bool:
        """Restart system via remote commands.

        Args:
            system: System instance
            instance_manager: Cloud instance manager (or list for multinode)
            executor: ParallelExecutor for output routing
            system_name: System name for logging

        Returns:
            True if restart succeeded, False otherwise
        """
        from .infrastructure import InfrastructureHelper

        try:
            primary_manager = (
                instance_manager[0]
                if isinstance(instance_manager, list)
                else instance_manager
            )

            system_kind = system.kind
            infra_helper = InfrastructureHelper(self._runner)

            if system_kind == "exasol":
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

                self._log_output(
                    "⏳ Waiting for Exasol cluster to be ready...",
                    executor,
                    system_name,
                )
                if not infra_helper.wait_for_exasol_ready(primary_manager):
                    self._log_output(
                        "[red]❌ Exasol cluster failed to become ready after restart[/red]",
                        executor,
                        system_name,
                    )
                    return False

                self._log_output("✅ Exasol cluster is ready", executor, system_name)

                self._log_output(
                    "🧹 Cleaning up interfering services after restart...",
                    executor,
                    system_name,
                )
                cleanup_success = infra_helper.cleanup_exasol_services(
                    system, primary_manager
                )
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

                self._log_output(
                    "⏳ Waiting for ClickHouse to be ready...", executor, system_name
                )
                if not infra_helper.wait_for_clickhouse_ready(instance_manager):
                    self._log_output(
                        "[red]❌ ClickHouse failed to become ready after restart[/red]",
                        executor,
                        system_name,
                    )
                    return False

                self._log_output("✅ ClickHouse is ready", executor, system_name)
                return True

            else:
                self._log_output(
                    f"[yellow]⚠️ Unknown system type '{system_kind}', skipping restart[/yellow]",
                    executor,
                    system_name,
                )
                return True

        except Exception as e:
            self._log_output(f"[red]Restart failed: {e}[/red]", executor, system_name)
            return False
