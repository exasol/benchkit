"""Infrastructure setup and management for benchmark runner.

This module handles cloud infrastructure provisioning, system state checking,
and service management.
"""

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from rich.console import Console

from benchkit.common import exclude_from_package

if TYPE_CHECKING:
    from .runner import BenchmarkRunner

console = Console()


def _log(message: str, callback: Callable[[str], None] | None = None) -> None:
    """Route message through callback if provided, otherwise print to console.

    Args:
        message: Message to output (may contain Rich markup)
        callback: Optional callback function for logging
    """
    if callback:
        # Strip Rich markup for log files
        from benchkit.common.markup import strip_markup

        callback(strip_markup(message))
    else:
        console.print(message)


class InfrastructureHelper:
    """Handles infrastructure setup and system state management."""

    def __init__(self, runner: "BenchmarkRunner"):
        """Initialize the infrastructure helper.

        Args:
            runner: Parent BenchmarkRunner instance for shared state access
        """
        self._runner = runner

    def _log_output(
        self,
        message: str,
        executor: Any = None,
        system_name: str | None = None,
    ) -> None:
        """Route output through runner's log output."""
        self._runner._log_output(message, executor, system_name)

    @exclude_from_package
    def check_system_state(
        self,
        system: Any,
        instance_manager: Any,
        executor: Any = None,
    ) -> str:
        """
        Enhanced system state detection with comprehensive checks.

        Returns one of:
        - NEEDS_INSTALLATION: System not installed or broken installation
        - NEEDS_SERVICE_RESTART: System installed but services down
        - NEEDS_DB_RESTART: Services running but database not accessible
        - READY: System fully operational

        Args:
            system: System instance
            instance_manager: Cloud instance manager (or list for multinode)

        Returns:
            State string indicating system status
        """
        from ..systems import create_system

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
                        self._log_output(
                            f"🔍 {system_name}: Missing installation markers on node(s): {missing_markers}",
                            executor,
                            system_name,
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
                        self._log_output(
                            f"🔍 {system_name}: No installation marker ({marker_file})",
                            executor,
                            system_name,
                        )
                        return "NEEDS_INSTALLATION"

            # 2. System-specific checks based on system type
            system_config = None
            for cfg in self._runner.config["systems"]:
                if cfg["name"] == system_name:
                    system_config = cfg
                    break

            if not system_config:
                raise SystemError(f"System {system_name} not found")

            # Inject project_id so system can access it
            system_config["project_id"] = self._runner.project_id
            system = create_system(system_config)

            if system.is_healthy():
                return "READY"

            return "NEEDS_SERVICE_RESTART"

        except Exception as e:
            console.print(f"[yellow]⚠️ {system_name}: State check failed: {e}[/yellow]")
            return "NEEDS_INSTALLATION"

    @exclude_from_package
    def wait_for_exasol_ready(
        self, instance_manager: Any, max_attempts: int = 30
    ) -> bool:
        """Wait for Exasol cluster to be ready after restart.

        Args:
            instance_manager: Cloud instance manager
            max_attempts: Maximum number of attempts

        Returns:
            True if cluster is ready, False if timeout
        """
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
                time.sleep(10)

        return False

    @exclude_from_package
    def wait_for_clickhouse_ready(
        self, instance_manager: Any, max_attempts: int = 20
    ) -> bool:
        """Wait for ClickHouse to be ready after restart.

        Args:
            instance_manager: Cloud instance manager
            max_attempts: Maximum number of attempts

        Returns:
            True if ClickHouse is ready, False if timeout
        """
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
                time.sleep(5)

        return False

    @exclude_from_package
    def cleanup_exasol_services(self, system: Any, instance_manager: Any) -> bool:
        """Clean up interfering Exasol services after restart.

        Args:
            system: System instance
            instance_manager: Cloud instance manager

        Returns:
            True if cleanup succeeded, False otherwise
        """
        try:
            # Override the system's execute_command to use remote execution
            original_execute = system.execute_command

            def remote_execute_command(
                cmd: str,
                timeout: int = 300,
                record: bool = True,
                category: str = "installation",
                node_info: str | None = None,
                description: str | None = None,
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


@exclude_from_package
def setup_cloud_infrastructure(
    runner: "BenchmarkRunner",
    log_callback: Callable[[str], None] | None = None,
) -> bool:
    """Setup cloud infrastructure connection and managers.

    Args:
        runner: BenchmarkRunner instance
        log_callback: Optional callback for routing log messages (for parallel execution)

    Returns:
        True if setup succeeded, False otherwise
    """
    from ..common.cli_helpers import (
        get_cloud_ssh_key_path,
        get_first_cloud_provider,
    )
    from ..util import Timer

    try:
        from ..infra.manager import CloudInstanceManager, InfraManager

        cloud_provider = get_first_cloud_provider(runner.config)
        if not cloud_provider:
            _log("[red]❌ No cloud provider found in config[/red]", log_callback)
            return False

        _log(
            f"🔗 Connecting to {cloud_provider.upper()} infrastructure...", log_callback
        )

        # Initialize infrastructure manager
        infra_manager = InfraManager(cloud_provider, runner.config, log_callback)

        # Check if instances exist, provision if needed
        with Timer("Infrastructure provisioning") as provision_timer:
            instance_info = infra_manager.get_instance_info()

            # If no instances found, try to provision them
            if "error" in instance_info or not instance_info:
                _log(
                    "[yellow]⚠ No instances found, provisioning infrastructure...[/yellow]",
                    log_callback,
                )

                apply_result = infra_manager.apply(wait_for_init=True)
                if not apply_result.success:
                    _log(
                        f"[red]❌ Failed to provision infrastructure: {apply_result.error}[/red]",
                        log_callback,
                    )
                    return False

                instance_info = infra_manager.get_instance_info()
                runner.infrastructure_provisioning_time = provision_timer.elapsed
                _log(
                    f"[green]✅ Infrastructure provisioned in {provision_timer.elapsed:.2f}s[/green]",
                    log_callback,
                )
            else:
                runner.infrastructure_provisioning_time = (
                    runner._load_provisioning_timing()
                )
                _log(
                    f"[green]✅ Using existing infrastructure (provisioned in {runner.infrastructure_provisioning_time:.2f}s)[/green]",
                    log_callback,
                )

        if "error" in instance_info:
            # Retry once — terraform output can fail transiently under parallel load
            import time

            _log(
                f"[yellow]⚠ Instance info retrieval failed ({instance_info['error']}), retrying in 10s...[/yellow]",
                log_callback,
            )
            time.sleep(10)
            instance_info = infra_manager.get_instance_info()

        if "error" in instance_info:
            _log(
                f"[red]❌ Failed to get instance info: {instance_info['error']}[/red]",
                log_callback,
            )
            return False

        # Create cloud instance managers for each system
        ssh_private_key_path = get_cloud_ssh_key_path(runner.config)
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

                    runner._cloud_instance_managers[system_name] = node_managers
                    node_count = len(node_managers)
                    primary_ip = node_managers[0].public_ip
                    _log(
                        f"[green]✅ Connected to {system_name}: {node_count} nodes (primary: {primary_ip})[/green]",
                        log_callback,
                    )

                    # Set environment variables for IP resolution
                    import os

                    private_ips = ",".join(
                        [str(mgr.private_ip) for mgr in node_managers if mgr.private_ip]
                    )
                    public_ips = ",".join(
                        [str(mgr.public_ip) for mgr in node_managers if mgr.public_ip]
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
                    runner._cloud_instance_managers[system_name] = instance_manager
                    _log(
                        f"[green]✅ Connected to {system_name}: {system_info.get('public_ip', 'N/A')}[/green]",
                        log_callback,
                    )

                    # Set environment variables for IP resolution
                    import os

                    private_ip_var = f"{system_name.upper()}_PRIVATE_IP"
                    public_ip_var = f"{system_name.upper()}_PUBLIC_IP"
                    os.environ[private_ip_var] = system_info.get("private_ip", "")
                    os.environ[public_ip_var] = system_info.get("public_ip", "")

        if not runner._cloud_instance_managers:
            _log("[red]❌ No cloud instances found[/red]", log_callback)
            return False

        return True

    except Exception as e:
        _log(f"[red]❌ Infrastructure setup failed: {e}[/red]", log_callback)
        return False
