"""Base classes for database systems under test."""

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from benchkit.common import DataFormat, exclude_from_package

from ..util import safe_command

if TYPE_CHECKING:
    # avoid cyclic dependency problems
    from ..workloads import Workload


TableOperation = Literal[
    "DEFAULT",
    "OPTIMIZE TABLE",
    "MATERIALIZE STATISTICS",
]


class SystemUnderTest(ABC):
    """Abstract base class for database systems under test."""

    # Class attribute indicating if this system supports multinode clusters
    # Subclasses should override this to True if they support multinode
    SUPPORTS_MULTINODE: bool = False
    # attribute indicating capability (or implementation) of streaming data import
    SUPPORTS_STREAMLOAD: bool = False

    def __init__(
        self,
        config: dict[str, Any],
        output_callback: Callable[[str], None] | None = None,
        workload_config: dict[str, Any] | None = None,
    ):
        self.name = config["name"]
        self.kind = config["kind"]
        self.version = config["version"]

        # Defensive: Ensure setup is not None
        if "setup" not in config:
            raise ValueError(
                f"System config for '{self.name}' is missing 'setup' section"
            )
        if config["setup"] is None:
            raise ValueError(
                f"System config for '{self.name}' has None 'setup' section"
            )

        self.setup_config = config["setup"]
        self.data_dir: Path | None = Path(
            self.setup_config.get("data_dir", f"/data/{self.name}")
        )
        self.config = config
        self._connection = None
        self._is_running = False
        # Container name for Docker-based installations (can be overridden in subclasses)
        project_id = config.get("project_id", "")
        self.container_name = (
            f"{self.kind}_{project_id}_{self.name}"
            if project_id
            else f"{self.kind}_{self.name}"
        )

        # Output callback for thread-safe logging in parallel execution
        self._output_callback = output_callback

        # Workload configuration for dynamic tuning
        self.workload_config = workload_config or {}
        # default schema for queries
        self.schema: str | None = None

        # Command recording for report reproduction
        self.setup_commands: list[dict[str, Any]] = []
        self.installation_notes: list[str] = []

        # Multinode configuration
        self.node_count: int = self.setup_config.get("node_count", 1)
        assert self.node_count >= 1, "node_count must be positive"

        # Cloud instance management for remote execution
        self._cloud_instance_manager: Any = None
        self._cloud_instance_managers: list[Any] = []
        self._external_host: str | None = None

    def _log(self, message: str) -> None:
        """
        Thread-safe logging that respects parallel execution context.

        Use this method instead of print() to ensure correct system name tagging
        when systems are being installed/configured in parallel.

        When output_callback is set (e.g., by BenchmarkRunner during parallel execution),
        output is routed directly to the ParallelExecutor's task buffer, bypassing
        the thread-unsafe contextlib.redirect_stdout mechanism. This prevents the
        race condition where output from one system could get tagged with another
        system's name.

        Args:
            message: Message to log

        Note:
            - Always use _log() instead of print() in system implementations
            - When output_callback is None, falls back to print() (sequential execution)
            - The callback is automatically set by BenchmarkRunner._get_system_for_context()
              when running in parallel mode
        """
        if self._output_callback:
            self._output_callback(message)
        else:
            print(message)

    @exclude_from_package
    def get_install_marker_path(self) -> str | None:
        """Return the path to the installation marker file for this system."""
        return f"~/.{self.kind}_installed"

    @exclude_from_package
    def mark_installed(
        self, record: bool = False, category: str = "installation"
    ) -> bool:
        """Create or update the installation marker file."""
        marker = self.get_install_marker_path()
        if not marker:
            return True

        result = self.execute_command(
            f"touch {marker}",
            record=record,
            category=category,
        )

        if not isinstance(result, dict):
            return False

        return bool(result.get("success"))

    @exclude_from_package
    def has_install_marker(self) -> bool:
        """Check whether the installation marker is present."""
        marker = self.get_install_marker_path()
        if not marker:
            return False

        result = self.execute_command(
            f"test -f {marker} && echo 'installed'",
            record=False,
            category="installation_check",
        )

        if not isinstance(result, dict):
            return False

        stdout = result.get("stdout") or ""

        return bool(result.get("success")) and "installed" in stdout

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """
        Check if the system is already installed and configured.
        Override this method in subclasses for system-specific detection.

        Returns:
            True if system is already installed, False otherwise
        """
        return False

    @exclude_from_package
    def install(self) -> bool:
        """Install database system. Routes to _install_docker/_install_native/_verify_preinstalled."""
        self.prepare_data_directory()
        method = self.setup_config.get("method", "docker")
        handlers = {
            "docker": self._install_docker,
            "native": self._install_native,
            "installer": self._install_native,
            "preinstalled": self._verify_preinstalled,
            "managed": self._install_managed,
        }
        handler = handlers.get(method)
        if not handler:
            self._log(f"Unknown setup method: {method}")
            return False
        return handler()

    def _install_docker(self) -> bool:
        """Install using Docker. Override in subclasses or use _install_docker_common()."""
        raise NotImplementedError("Subclass must implement _install_docker()")

    def _install_native(self) -> bool:
        """Install natively. Override in subclasses."""
        raise NotImplementedError("Subclass must implement _install_native()")

    def _verify_preinstalled(self) -> bool:
        """Verify preinstalled system is accessible. Default: check health."""
        return self.is_healthy()

    @exclude_from_package
    def _install_managed(self) -> bool:
        """Configure connection for self-managed deployment (e.g., Exasol PE).

        Self-managed systems are deployed during 'infra apply', NOT during setup.
        This method loads connection info from the state file saved during deployment.

        If the system was not deployed via 'infra apply', this will FAIL.
        There is no backward compatibility - 'infra apply' must be run first.

        Returns:
            True if configuration succeeded, False otherwise
        """
        from benchkit.infra.managed_state import load_managed_state

        project_id = self.config.get("project_id", "default")

        self._log(f"Loading state for managed system: {self.name}")

        # Load state from managed_state.py (saved during infra apply)
        state = load_managed_state(project_id, self.name)

        if not state:
            self._log(
                f"ERROR: No state found for managed system '{self.name}'. "
                f"You must run 'infra apply' before 'setup' to deploy managed systems."
            )
            return False

        status = state.get("status", "unknown")
        if status not in ["running", "database_ready", "deployed"]:
            self._log(
                f"ERROR: Managed system '{self.name}' is not in a ready state. "
                f"Current status: {status}. Run 'infra apply' to deploy."
            )
            return False

        # Get connection info from state
        connection_info = state.get("connection_info", {})
        if not connection_info:
            self._log(
                f"ERROR: No connection info found in state for '{self.name}'. "
                f"The deployment may have failed. Run 'infra apply' again."
            )
            return False

        # Apply connection info to system attributes
        host = connection_info.get("host")
        port = connection_info.get("port")
        username = connection_info.get("username")
        # Note: password is not stored in state for security reasons
        # It should be loaded from config or environment

        self._log(f"Got connection info from state: host={host}, port={port}")

        if host and hasattr(self, "host"):
            self.host = host
        if port and hasattr(self, "port"):
            self.port = port
        if username and hasattr(self, "username"):
            self.username = username

        # Store extra info (like certificate fingerprint, SSH info) for later use
        extra = connection_info.get("extra", {})
        if extra:
            if not hasattr(self, "_managed_extra"):
                self._managed_extra: dict[str, Any] = {}
            self._managed_extra.update(extra)
            self._log(f"Loaded extra info: {list(extra.keys())}")

        self._log(f"Managed system '{self.name}' configured from state")
        return True

    @exclude_from_package
    def _install_docker_common(
        self,
        image: str,
        port_mappings: dict[int, int],
        volume_mappings: dict[str, str] | None = None,
        env_vars: dict[str, str] | None = None,
        extra_args: list[str] | None = None,
    ) -> bool:
        """Common Docker installation pattern. Call from subclass _install_docker()."""
        self.record_setup_note(f"Installing {self.kind} using Docker container")
        if self.data_dir:
            self.record_setup_command(
                f"sudo mkdir -p {self.data_dir}",
                f"Create {self.kind} data directory",
                "preparation",
            )
            self.record_setup_command(
                f"sudo chown $(whoami):$(whoami) {self.data_dir}",
                "Set data directory permissions",
                "preparation",
            )
        self.execute_command(f"docker rm -f {self.container_name} || true", record=True)
        docker_cmd = ["docker", "run", "-d", "--name", self.container_name]
        if volume_mappings:
            docker_cmd.extend(f"-v {h}:{c}" for h, c in volume_mappings.items())
        for host_port, container_port in port_mappings.items():
            docker_cmd.extend(["-p", f"{host_port}:{container_port}"])
        if env_vars:
            docker_cmd.extend(f"-e {k}={v}" for k, v in env_vars.items())
        if extra_args:
            docker_cmd.extend(extra_args)
        docker_cmd.append(image)
        result = self.execute_command(" ".join(docker_cmd))
        if not result["success"]:
            self._log(f"Failed to start {self.kind} container: {result['stderr']}")
            return False
        self._log(f"Waiting for {self.kind} to start...")
        return self.wait_for_health(max_attempts=60, delay=5.0)

    @exclude_from_package
    def _install_on_all_nodes(self, install_single_node_fn: Any) -> bool:
        """Execute installation on all nodes in a multinode cluster. Use for multinode native installs."""
        if not self._cloud_instance_managers or len(self._cloud_instance_managers) <= 1:
            return bool(install_single_node_fn())
        self._log(f"Installing on all {len(self._cloud_instance_managers)} nodes...")
        original_commands_count, all_success = len(self.setup_commands), True
        for idx, mgr in enumerate(self._cloud_instance_managers):
            self._log(f"\n[Node {idx}] Starting installation...")
            original_mgr, original_external_host = (
                self._cloud_instance_manager,
                getattr(self, "_external_host", None),
            )
            self._cloud_instance_manager, self._external_host = mgr, mgr.public_ip
            commands_before = len(self.setup_commands) if idx > 0 else None
            try:
                if not install_single_node_fn():
                    self._log(f"[Node {idx}] Installation failed")
                    all_success = False
                else:
                    self._log(f"[Node {idx}] Installation completed")
            finally:
                if idx > 0 and commands_before is not None:
                    self.setup_commands = self.setup_commands[:commands_before]
                self._cloud_instance_manager = original_mgr
                if original_external_host:
                    self._external_host = original_external_host
        node_info = f"all_nodes_{len(self._cloud_instance_managers)}"
        for i in range(original_commands_count, len(self.setup_commands)):
            self.setup_commands[i]["node_info"] = node_info
        return bool(all_success)

    @exclude_from_package
    def execute_command_on_all_nodes(
        self,
        command: str,
        description: str = "",
        timeout: int = 300,
        record: bool = True,
    ) -> bool:
        """Execute a command on all nodes. Returns True if all succeed."""
        managers = (
            self._cloud_instance_managers
            if self._cloud_instance_managers
            else (
                [self._cloud_instance_manager] if self._cloud_instance_manager else []
            )
        )
        if not managers:
            return bool(
                self.execute_command(
                    command, timeout=float(timeout), record=record
                ).get("success", False)
            )
        all_success = True
        for idx, mgr in enumerate(managers):
            result = mgr.run_remote_command(command, timeout=timeout)
            if not result.get("success", False):
                self._log(
                    f"[Node {idx}] Command failed: {result.get('stderr', 'Unknown error')}"
                )
                all_success = False
        if record and managers:
            node_info = f"all_nodes_{len(managers)}" if len(managers) > 1 else None
            self.record_setup_command(
                self._sanitize_command_for_report(command),
                description or "Execute on all nodes",
                "setup",
                node_info,
            )
        return bool(all_success)

    @exclude_from_package
    def _write_remote_config_file(
        self,
        path: str,
        content: str,
        description: str,
        category: str = "configuration",
        use_sudo: bool = True,
    ) -> bool:
        """Write a config file remotely using heredoc (no escaping needed)."""
        prefix = "sudo " if use_sudo else ""
        cmd = f"{prefix}tee {path} > /dev/null << 'EOF'\n{content}\nEOF"
        self.record_setup_command(cmd, description, category)
        return bool(self.execute_command(cmd).get("success", False))

    @abstractmethod
    @exclude_from_package
    def start(self) -> bool:
        """
        Start the database system.

        Returns:
            True if start successful, False otherwise
        """
        pass

    @abstractmethod
    def is_healthy(self, quiet: bool = False) -> bool:
        """
        Check if the database system is running and healthy.

        Returns:
            True if system is healthy, False otherwise
        """
        pass

    @abstractmethod
    def create_schema(self, schema_name: str) -> bool:
        """
        Create a database schema/database.

        Args:
            schema_name: Name of the schema to create

        Returns:
            True if creation successful, False otherwise
        """
        pass

    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """
        Get connection string for this database system.

        Args:
            public_ip: Public IP address of the system
            private_ip: Private IP address of the system

        Returns:
            Connection string with CLI command to connect to the database
        """
        # Default implementation - subclasses should override
        host = self.setup_config.get("host", public_ip)
        port = self.setup_config.get("port", "N/A")
        return f"{self.kind}://{host}:{port}"

    def get_data_generation_directory(self, workload: Any) -> Path | None:
        """Get directory for data generation. Uses /data/generated if use_additional_disk is set."""
        explicit_data_dir = self.setup_config.get("data_dir")
        if explicit_data_dir:
            return Path(
                str(explicit_data_dir), "generated", workload.safe_display_name()
            )
        if self.setup_config.get("use_additional_disk", False):
            tpch_gen_dir = "/data/generated"
            self.execute_command(
                f"sudo mkdir -p {tpch_gen_dir} && sudo chown -R $(whoami):$(whoami) {tpch_gen_dir}",
                record=False,
            )
            return Path(tpch_gen_dir, workload.safe_display_name())
        return None

    @abstractmethod
    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """
        Load data into a table.

        Args:
            table_name: Name of the target table
            data_path: Path to the data file
            **kwargs: Additional parameters for data loading

        Returns:
            True if loading successful, False otherwise
        """
        pass

    @abstractmethod
    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """
        Load data into a table.

        Args:
            table_name: Name of the target table
            data_source: An iterable containing row data (could be list[list[Any]] or list[str] or ...)
            data_format: Format of the data, from text-based CSV/TSV/... to structured list/dict/...
            **kwargs: Additional parameters for data loading

        Returns:
            True if loading successful, False otherwise
        """
        pass

    def load_data_from_url_with_download(
        self,
        schema_name: str,
        table_name: str,
        data_url: str | list[str],
        /,
        extension: str = ".csv",
        **kwargs: Any,
    ) -> bool:
        """
        Download given resources to host filesystem
        and then load files into database using `load_data()` above
        """
        from benchkit.common import download_file_to_storage

        local_storage: Path = self.data_dir or Path("/var/tmp")
        downloaded_files: list[Path] = []
        file_part: int = 0
        ## download files locally
        url_list: list[str] = [data_url] if isinstance(data_url, str) else data_url
        for url in url_list:
            file_name: str = f"{table_name}_{file_part}{extension}"
            target_path: Path = local_storage / file_name
            if target_path.exists():
                self._log(f"Download: reusing existing file {target_path}")
                downloaded_files.append(target_path)
                continue
            self._log(f"Downloading {file_name} from {url}")
            try:
                download_file_to_storage(url, target_path)
                downloaded_files.append(target_path)
            except Exception as e:
                self._log(f"Error downloading {file_name}: {e}")
                return False

        ## then, import files one by one
        for file in downloaded_files:
            if not self.load_data(table_name, file, schema=schema_name):
                return False
        return True

    def load_data_from_url(
        self,
        schema_name: str,
        table_name: str,
        data_url: str | list[str],
        /,
        extension: str = ".csv",
        **kwargs: Any,
    ) -> bool:
        """
        Load table data from a URL or a set of URLs.
        Default implementation downloads data to local storage and then imports the downloaded file(s) using load_data()
        """
        return self.load_data_from_url_with_download(
            schema_name, table_name, data_url, extension=extension, **kwargs
        )

    def set_active_schema(self, schema_name: str) -> None:
        """Set the active schema for all subsequent query executions.

        This ensures thread-safe schema handling in multi-stream workloads.
        When set, this schema takes precedence over the instance-level schema
        configuration for all new connections.

        Args:
            schema_name: Name of the schema/database to use for queries
        """
        self._active_schema = schema_name

    @abstractmethod
    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute a SQL query and return timing and result information.

        Args:
            query: SQL query to execute
            query_name: Optional name for the query (for logging)
            return_data: If True, include result data in response (default: False)
            timeout: Optional timeout in seconds for query execution

        Returns:
            Dictionary containing:
            - success: bool
            - elapsed_s: float (execution time in seconds)
            - rows_returned: int (number of rows returned)
            - error: str (error message if failed)
            - query_name: str (name of the query)
            - data: pd.DataFrame (only if return_data=True, query results as DataFrame)
        """
        pass

    @abstractmethod
    def get_system_metrics(self) -> dict[str, Any]:
        """
        Get system-specific performance metrics.

        Returns:
            Dictionary containing system metrics like:
            - memory_usage
            - cache_hit_ratio
            - active_connections
            - etc.
        """
        pass

    @abstractmethod
    def teardown(self) -> bool:
        """
        Clean up and remove the database system.

        Returns:
            True if teardown successful, False otherwise
        """
        pass

    def prepare_data_directory(self) -> bool:
        """Prepare data directory for the database."""
        if self.data_dir is None:
            return True
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self._log(f"Failed to create data directory {self.data_dir}: {e}")
            return False

    def cleanup_data_directory(self) -> bool:
        """Clean up data directory."""
        if self.data_dir is None:
            return True
        try:
            if self.data_dir.exists():
                import shutil

                shutil.rmtree(self.data_dir)
            return True
        except Exception as e:
            self._log(f"Failed to cleanup data directory {self.data_dir}: {e}")
            return False

    def execute_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
        node_info: str | None = None,
    ) -> dict[str, Any]:
        """Execute a system command safely and optionally record it.

        Commands are executed either locally or remotely depending on whether
        a cloud instance manager is set and _should_execute_remotely() returns True.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            record: Whether to record command for report reproduction
            category: Category for organizing commands in report
            node_info: Node information (e.g., "node0", "all nodes", "node1,node2")
        """
        # Check if should execute remotely (on cloud instance)
        if self._should_execute_remotely():
            return self._execute_remote_command(
                command, timeout, record, category, node_info
            )
        else:
            return self._execute_local_command(
                command, timeout, record, category, node_info
            )

    def _execute_local_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
        node_info: str | None = None,
    ) -> dict[str, Any]:
        """Execute a command locally using safe_command."""
        result = safe_command(command, timeout=timeout)

        # Record command for report reproduction
        if record:
            command_record = {
                "command": command,
                "success": result["success"],
                "description": f"Execute {command.split()[0]} command",
                "category": category,
            }
            if node_info:
                command_record["node_info"] = node_info

            self.setup_commands.append(command_record)

        return result

    def _execute_remote_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
        node_info: str | None = None,
    ) -> dict[str, Any]:
        """Execute a command on remote cloud instance via instance manager."""
        result = self._cloud_instance_manager.run_remote_command(
            command, timeout=int(timeout) if timeout else 300
        )

        # Record command for report reproduction if requested
        if record:
            command_record = {
                "command": self._sanitize_command_for_report(command),
                "success": result.get("success", False),
                "description": f"Execute {command.split()[0]} command on remote system",
                "category": category,
            }
            if node_info:
                command_record["node_info"] = node_info
            self.setup_commands.append(command_record)

        return dict(result)

    def wait_for_health(self, max_attempts: int = 30, delay: float = 2.0) -> bool:
        """
        Wait for the system to become healthy.

        Args:
            max_attempts: Maximum number of health check attempts
            delay: Delay between attempts in seconds

        Returns:
            True if system became healthy, False if timeout
        """
        import time

        for attempt in range(max_attempts):
            # Use quiet=True during waiting to avoid spamming error messages
            # But on the last attempt, show the error to help debug
            quiet = attempt < max_attempts - 1
            if self.is_healthy(quiet=quiet):
                return True

            if attempt < max_attempts - 1:
                time.sleep(delay)

        return False

    @exclude_from_package
    def record_setup_note(self, note: str) -> None:
        """Record a setup note for report reproduction."""
        self.installation_notes.append(note)

    @exclude_from_package
    def record_setup_command(
        self,
        command: str,
        description: str,
        category: str = "setup",
        node_info: str | None = None,
    ) -> None:
        """Record a setup command without executing it."""
        # Sanitize both command and description for report by replacing sensitive data with placeholders
        sanitized_command = self._sanitize_command_for_report(command)
        sanitized_description = self._sanitize_command_for_report(description)

        command_record = {
            "command": sanitized_command,
            "success": True,
            "description": sanitized_description,
            "category": category,
        }
        if node_info:
            command_record["node_info"] = node_info

        self.setup_commands.append(command_record)

    def _sanitize_command_for_report(self, command: str) -> str:
        """Replace sensitive information in commands with placeholders for reports."""
        import os

        # Get sensitive values from configuration
        sensitive_replacements = {}

        # Add password replacements from config
        if hasattr(self, "setup_config") and self.setup_config:
            if "image_password" in self.setup_config:
                sensitive_replacements[self.setup_config["image_password"]] = (
                    "<EXASOL_IMAGE_PASSWORD>"
                )
            if "db_password" in self.setup_config:
                sensitive_replacements[self.setup_config["db_password"]] = (
                    "<EXASOL_DB_PASSWORD>"
                )
            if "admin_password" in self.setup_config:
                sensitive_replacements[self.setup_config["admin_password"]] = (
                    "<EXASOL_ADMIN_PASSWORD>"
                )
            if "password" in self.setup_config:
                sensitive_replacements[self.setup_config["password"]] = (
                    "<DATABASE_PASSWORD>"
                )

        # Replace SSH key paths with placeholder
        sensitive_replacements[os.path.expanduser("~/.ssh/id_rsa")] = "~/.ssh/id_rsa"

        sanitized = command
        for actual_value, placeholder in sensitive_replacements.items():
            sanitized = sanitized.replace(str(actual_value), placeholder)

        # Replace IP addresses that look real (not localhost/127.0.0.1) with placeholders
        import re

        # Replace private IP patterns
        sanitized = re.sub(
            r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<PRIVATE_IP>", sanitized
        )
        sanitized = re.sub(
            r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b", "<PRIVATE_IP>", sanitized
        )
        sanitized = re.sub(r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "<PRIVATE_IP>", sanitized)

        # Replace public IP patterns (any remaining IP that's not localhost, not after = for version numbers)
        # Use negative lookbehind to avoid matching version numbers like clickhouse-server=25.9.2.1
        sanitized = re.sub(
            r"(?<![=:@])(?<![a-zA-Z0-9-])(?!127\.0\.0\.1\b)(?!localhost\b)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "<PUBLIC_IP>",
            sanitized,
        )

        return sanitized

    @exclude_from_package
    def _sanitize_value_for_report(self, value: Any) -> Any:
        """Recursively sanitize any value (string, dict, list) for reports."""
        if isinstance(value, str):
            return self._sanitize_command_for_report(value)
        elif isinstance(value, dict):
            return {k: self._sanitize_value_for_report(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._sanitize_value_for_report(item) for item in value]
        else:
            return value

    @exclude_from_package
    def get_setup_summary(self) -> dict[str, Any]:
        """Get summary of all setup commands and notes for report."""
        # Group commands by category
        commands_by_category: dict[str, list[dict[str, Any]]] = {}
        for cmd in self.setup_commands:
            category = cmd["category"]
            if category not in commands_by_category:
                commands_by_category[category] = []
            commands_by_category[category].append(cmd)

        # Extract configuration parameters that were actually used and sanitize them
        config_params = {}
        if hasattr(self, "setup_config"):
            for key, value in self.setup_config.items():
                if key != "method":  # Skip internal method field
                    # Sanitize the value before adding to config_params
                    config_params[key] = self._sanitize_value_for_report(value)

        # Sanitize installation notes as well
        sanitized_notes = [
            self._sanitize_command_for_report(note) if isinstance(note, str) else note
            for note in self.installation_notes
        ]

        return {
            "system_name": self.name,
            "system_kind": self.kind,
            "system_version": self.version,
            "commands": commands_by_category,
            "installation_notes": sanitized_notes,
            "config_parameters": config_params,
            "data_directory": str(self.data_dir),
        }

    def __str__(self) -> str:
        return f"{self.kind} {self.version} ({self.name})"

    def __repr__(self) -> str:
        return f"SystemUnderTest(name='{self.name}', kind='{self.kind}', version='{self.version}')"

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return list of Python packages required by this system."""
        return []

    @staticmethod
    def _resolve_env_var(value: str) -> str:
        """Resolve environment variable placeholders like $VAR_NAME."""
        import os

        if isinstance(value, str) and value.startswith("$"):
            return os.environ.get(value[1:], value)
        return value

    @classmethod
    def _get_connection_defaults(cls) -> dict[str, Any]:
        """Override in subclasses to provide system-specific connection defaults."""
        return {
            "port": None,
            "username": None,
            "password": "",
            "schema_key": "schema",
            "schema": None,
        }

    @classmethod
    def _get_password_key(cls, setup_config: dict[str, Any]) -> str:
        """Override in subclasses if password key varies (e.g., db_password vs password)."""
        return "password"

    @classmethod  # noqa: B027
    def _extend_connection_info(
        cls, conn_info: dict[str, Any], setup_config: dict[str, Any]
    ) -> None:
        """Override in subclasses to add system-specific connection info."""
        pass

    @classmethod
    def extract_workload_connection_info(
        cls, setup_config: dict[str, Any], for_local_execution: bool = False
    ) -> dict[str, Any]:
        """Extract connection info using template method pattern. Subclasses override hooks."""
        defaults = cls._get_connection_defaults()
        host = (
            "localhost"
            if for_local_execution
            else cls._resolve_env_var(setup_config.get("host", "localhost"))
        )
        password_key = cls._get_password_key(setup_config)
        schema_key = defaults.get("schema_key", "schema")

        conn_info = {
            "host": host,
            "port": setup_config.get("port", defaults["port"]),
            "username": setup_config.get("username", defaults["username"]),
            "password": setup_config.get(password_key, defaults["password"]),
            schema_key: setup_config.get(schema_key, defaults["schema"]),
        }
        if setup_config.get("use_additional_disk", False):
            conn_info["use_additional_disk"] = True
        # Include node_count for multinode support (critical for distributed table creation)
        if setup_config.get("node_count", 1) > 1:
            conn_info["node_count"] = setup_config["node_count"]
        cls._extend_connection_info(conn_info, setup_config)
        return conn_info

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """
        Return ports required by this system for AWS security group configuration.

        Returns:
            Dictionary with port descriptions as keys and port numbers as values
        """
        return {}

    # ===================================================================
    # Generic Storage Management Methods
    # ===================================================================

    @exclude_from_package
    def _detect_storage_devices(
        self, skip_root: bool = True, device_filter: str | None = None
    ) -> list[dict[str, str]]:
        """
        Detect available storage devices (NVMe, EBS, etc.).

        Args:
            skip_root: If True, skip the root disk (nvme0n1)
            device_filter: Filter devices by type ("local", "ebs", or None for all)

        Returns:
            List of dicts with 'name', 'path', 'size', 'type', 'mounted_at', 'storage_type'
            storage_type is either 'local' (instance store) or 'ebs'
        """
        result = self.execute_command(
            "lsblk -dn -o NAME,SIZE,TYPE | grep disk", record=False
        )

        if not result.get("success", False):
            self._log("Warning: Could not detect storage devices")
            return []

        devices = []
        lines = result.get("stdout", "").strip().split("\n")

        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                device_name = parts[0]
                device_size = parts[1]
                device_type = parts[2]
                device_path = f"/dev/{device_name}"

                # Skip root disk if requested
                if skip_root:
                    # Dynamically detect root disk by checking what's mounted as /
                    # Use findmnt which properly resolves /dev/root symlinks
                    root_check = self.execute_command(
                        "findmnt -n -o SOURCE /", record=False
                    )

                    # Fallback to df if findmnt not available
                    if not root_check.get("success", False):
                        root_check = self.execute_command(
                            "df / | tail -1 | awk '{print $1}'", record=False
                        )

                    if root_check.get("success", False):
                        root_device = root_check.get("stdout", "").strip()

                        # If we got /dev/root symlink, resolve it to actual device
                        if root_device == "/dev/root":
                            readlink_check = self.execute_command(
                                "readlink -f /dev/root", record=False
                            )
                            if readlink_check.get("success", False):
                                root_device = readlink_check.get("stdout", "").strip()

                        # Extract base device name (e.g., /dev/nvme1n1p1 -> nvme1n1)
                        if "/" in root_device:
                            # Use regex to remove partition suffix (p1, p15, or just digits)
                            # This correctly handles: nvme0n1p1 -> nvme0n1, sda1 -> sda
                            device_part = root_device.split("/")[-1]
                            root_base = re.sub(r"p?\d+$", "", device_part)
                            if device_name == root_base:
                                continue

                # Check if device exists
                check_result = self.execute_command(
                    f"test -b {device_path} && echo 'exists'", record=False
                )
                if not (
                    check_result.get("success", False)
                    and "exists" in check_result.get("stdout", "")
                ):
                    continue

                # Determine storage type (local instance store vs EBS)
                storage_type = "unknown"
                if device_name.startswith("nvme"):
                    # Use nvme id-ctrl to check if it's EBS or local instance store
                    nvme_result = self.execute_command(
                        f"nvme id-ctrl {device_path} 2>/dev/null | grep -q 'Amazon Elastic Block Store' && echo 'ebs' || echo 'local'",
                        record=False,
                    )
                    if nvme_result.get("success", False):
                        storage_type = nvme_result.get("stdout", "").strip()
                    else:
                        # Fallback: Check /dev/disk/by-id for EBS markers
                        # AWS EBS volumes attached as NVMe have Amazon_Elastic_Block_Store in by-id
                        by_id_check = self.execute_command(
                            f"ls -la /dev/disk/by-id/ 2>/dev/null | grep '{device_name}' | grep -q 'Amazon_Elastic_Block_Store' && echo 'ebs' || echo 'local'",
                            record=False,
                        )
                        if by_id_check.get("success", False):
                            storage_type = by_id_check.get("stdout", "").strip()
                elif device_name.startswith(("sd", "xvd")):
                    # Traditional block device names (sd*, xvd*) are typically EBS volumes
                    # on AWS. Instance store NVMe devices use nvme* prefix on modern instances.
                    storage_type = "ebs"

                # Apply device filter if specified
                if device_filter and storage_type != device_filter:
                    continue

                # Check mount status - use exact match to avoid matching partitions
                mount_result = self.execute_command(
                    f"mount | grep '^{device_path} '", record=False
                )
                mounted_at = None
                if (
                    mount_result.get("success", False)
                    and mount_result.get("stdout", "").strip()
                ):
                    # Extract mount point (3rd field in mount output)
                    mount_parts = mount_result.get("stdout", "").split()
                    if len(mount_parts) >= 3:
                        mounted_at = mount_parts[2]

                # Resolve to stable /dev/disk/by-id/ path for multinode consistency
                stable_path = device_path
                by_id_result = self.execute_command(
                    f"ls -l /dev/disk/by-id/ | grep '{device_name}$' | grep -v -- '-part' | grep -v '_[0-9]*$' | head -1 | awk '{{print \"/dev/disk/by-id/\" $9}}'",
                    record=False,
                )
                if (
                    by_id_result.get("success", False)
                    and by_id_result.get("stdout", "").strip()
                ):
                    # Ensure we only have a single line (no embedded newlines)
                    stable_path_raw = by_id_result.get("stdout", "").strip()
                    stable_path = (
                        stable_path_raw.split("\n")[0]
                        if stable_path_raw
                        else device_path
                    )

                devices.append(
                    {
                        "name": device_name,
                        "path": device_path,
                        "size": device_size,
                        "type": device_type,
                        "storage_type": storage_type,
                        "mounted_at": mounted_at,
                        "stable_path": stable_path,
                    }
                )

        # Sort devices by stable_path for deterministic ordering across nodes
        # This is critical for multinode consistency:
        # - Single disk: ensures same disk selected on all nodes
        # - RAID: ensures same device order → consistent RAID layout
        # - Multiple disks: ensures consistent device assignment
        devices.sort(key=lambda d: d["stable_path"])

        return devices

    @exclude_from_package
    def _unmount_disk(self, device_or_mount: str) -> bool:
        """
        Unmount a disk or mount point.

        Args:
            device_or_mount: Device path (e.g., /dev/nvme1n1) or mount point (e.g., /data)

        Returns:
            True if successful, False otherwise
        """
        self.record_setup_command(
            f"sudo umount {device_or_mount}",
            f"Unmount {device_or_mount}",
            "storage_setup",
        )

        result = self.execute_command(
            f"sudo umount {device_or_mount}", record=True, category="storage_setup"
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def _format_disk(self, device: str, filesystem: str = "ext4") -> bool:
        """
        Format a disk with specified filesystem.

        Args:
            device: Device path (e.g., /dev/nvme1n1)
            filesystem: Filesystem type (default: ext4)

        Returns:
            True if successful, False otherwise
        """
        self.record_setup_command(
            f"sudo mkfs.{filesystem} -F {device}",
            f"Format {device} with {filesystem} filesystem",
            "storage_setup",
        )

        result = self.execute_command(
            f"sudo mkfs.{filesystem} -F {device}",
            record=True,
            category="storage_setup",
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def _mount_disk(
        self, device: str, mount_point: str, create_mount_point: bool = True
    ) -> bool:
        """
        Mount a disk at specified mount point.

        Args:
            device: Device path (e.g., /dev/nvme1n1)
            mount_point: Where to mount (e.g., /data)
            create_mount_point: If True, create mount point directory if it doesn't exist

        Returns:
            True if successful, False otherwise
        """
        # Create mount point if needed
        if create_mount_point:
            self.record_setup_command(
                f"sudo mkdir -p {mount_point}",
                f"Create mount point {mount_point}",
                "storage_setup",
            )
            self.execute_command(
                f"sudo mkdir -p {mount_point}", record=True, category="storage_setup"
            )

        # Mount the disk
        self.record_setup_command(
            f"sudo mount {device} {mount_point}",
            f"Mount {device} to {mount_point}",
            "storage_setup",
        )

        result = self.execute_command(
            f"sudo mount {device} {mount_point}", record=True, category="storage_setup"
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def _set_ownership(self, path: str, owner: str = "ubuntu:ubuntu") -> bool:
        """
        Set directory/file ownership.

        Args:
            path: Path to set ownership for
            owner: Owner in format "user:group" (default: ubuntu:ubuntu)

        Returns:
            True if successful, False otherwise
        """
        # Check if owner exists (user:group format)
        user = owner.split(":")[0]
        check_user = self.execute_command(
            f"id {user} >/dev/null 2>&1 && echo 'exists'", record=False
        )

        # Distinguish between SSH failure and user not existing
        # If command failed but stderr contains connection errors, it's SSH failure
        stderr = check_user.get("stderr", "").lower()
        is_ssh_failure = any(
            err in stderr
            for err in [
                "connection",
                "broken pipe",
                "timeout",
                "no route",
                "refused",
            ]
        )

        if is_ssh_failure:
            # SSH failure - try chown anyway as the user might exist
            self._log(
                f"Warning: SSH connection issue while checking user {user}, attempting chown anyway"
            )
        elif not (
            check_user.get("success", False)
            and "exists" in check_user.get("stdout", "")
        ):
            # User genuinely doesn't exist
            self._log(
                f"Warning: User {user} does not exist yet, skipping ownership setting"
            )
            self._log("  Ownership will need to be set later during installation")
            return True

        self.record_setup_command(
            f"sudo chown -R {owner} {path}",
            f"Set ownership of {path} to {owner}",
            "storage_setup",
        )

        result = self.execute_command(
            f"sudo chown -R {owner} {path}", record=True, category="storage_setup"
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def _create_raid0(
        self, device_paths: list[str], raid_device: str = "/dev/md0"
    ) -> bool:
        """
        Create RAID0 array from multiple devices.

        Args:
            device_paths: List of device paths to combine (e.g., ['/dev/nvme1n1', '/dev/nvme2n1'])
            raid_device: Path for the RAID device (default: /dev/md0)

        Returns:
            True if successful, False otherwise
        """
        if len(device_paths) < 2:
            self._log(
                f"Warning: Need at least 2 devices for RAID0, got {len(device_paths)}"
            )
            return False

        devices_str = " ".join(device_paths)
        self._log(
            f"Creating RAID0 array from {len(device_paths)} device(s): {devices_str}"
        )

        # Step 1: Stop any existing RAID arrays on the target device
        self.record_setup_command(
            f"sudo mdadm --stop {raid_device} 2>/dev/null || true",
            f"Stop existing RAID array at {raid_device} if present",
            "storage_setup",
        )
        self.execute_command(
            f"sudo mdadm --stop {raid_device} 2>/dev/null || true",
            record=True,
            category="storage_setup",
        )

        # Step 2: Clean devices - unmount if needed and clear filesystem signatures
        for dev in device_paths:
            # Check if device is mounted
            mount_check = self.execute_command(f"mount | grep '^{dev} '", record=False)
            if (
                mount_check.get("success", False)
                and mount_check.get("stdout", "").strip()
            ):
                self._log(f"Device {dev} is mounted, unmounting...")
                self.record_setup_command(
                    f"sudo umount {dev}",
                    f"Unmount {dev} before RAID creation",
                    "storage_setup",
                )
                umount_result = self.execute_command(
                    f"sudo umount {dev}", record=True, category="storage_setup"
                )
                if not umount_result.get("success", False):
                    self._log(f"Warning: Failed to unmount {dev}, continuing anyway...")

            # Clear filesystem signatures
            self.record_setup_command(
                f"sudo wipefs -a {dev} 2>/dev/null || true",
                f"Clear filesystem signatures on {dev}",
                "storage_setup",
            )
            self.execute_command(
                f"sudo wipefs -a {dev} 2>/dev/null || true",
                record=True,
                category="storage_setup",
            )

        # Step 3: Zero superblocks on all devices
        for dev in device_paths:
            self.record_setup_command(
                f"sudo mdadm --zero-superblock {dev} 2>/dev/null || true",
                f"Clear RAID superblock on {dev}",
                "storage_setup",
            )
            self.execute_command(
                f"sudo mdadm --zero-superblock {dev} 2>/dev/null || true",
                record=True,
                category="storage_setup",
            )

        # Step 4: Create RAID0 array
        create_cmd = (
            f"yes | sudo mdadm --create {raid_device} "
            f"--level=0 --raid-devices={len(device_paths)} {devices_str}"
        )
        self.record_setup_command(
            create_cmd,
            f"Create RAID0 array from {len(device_paths)} devices",
            "storage_setup",
        )

        result = self.execute_command(create_cmd, record=True, category="storage_setup")
        if not result.get("success", False):
            self._log(
                f"Failed to create RAID0 array: {result.get('stderr', 'Unknown error')}"
            )
            return False

        # Step 5: Wait for array to be ready (non-fatal)
        self.record_setup_command(
            f"sudo mdadm --wait {raid_device} 2>/dev/null || true",
            f"Wait for RAID array {raid_device} to be ready",
            "storage_setup",
        )
        self.execute_command(
            f"sudo mdadm --wait {raid_device} 2>/dev/null || true",
            record=True,
            category="storage_setup",
        )

        # Step 5: Save RAID configuration
        self.record_setup_command(
            "sudo mkdir -p /etc/mdadm",
            "Create mdadm configuration directory",
            "storage_setup",
        )
        self.execute_command(
            "sudo mkdir -p /etc/mdadm", record=True, category="storage_setup"
        )

        self.record_setup_command(
            "sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf",
            "Save RAID configuration",
            "storage_setup",
        )
        self.execute_command(
            "sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf",
            record=True,
            category="storage_setup",
        )

        # Update initramfs (non-fatal on failure)
        self.execute_command(
            "sudo update-initramfs -u 2>/dev/null || true", record=False
        )

        self.record_setup_note(
            f"RAID0 array created: {raid_device} from {len(device_paths)} devices"
        )
        self._log(f"✓ RAID0 array created successfully: {raid_device}")

        return True

    @exclude_from_package
    def setup_storage(self, workload: "Workload") -> bool:
        """
        Setup storage based on configuration.

        This is the main entry point for storage setup. It checks the config
        and calls either system-specific storage setup or directory-based setup.

        Idempotent: Can be called multiple times safely. Returns immediately
        if storage was already set up successfully.

        Returns:
            True if successful, False otherwise
        """
        # Check if storage setup was already completed
        if getattr(self, "_storage_setup_complete", False):
            self._log(f"✓ Storage already configured for {self.name}, skipping setup")
            return True

        use_additional_disk = self.setup_config.get("use_additional_disk", False)

        result = False
        if use_additional_disk:
            self._log(f"Setting up additional disk storage for {self.name}...")
            result = self._setup_database_storage(workload)
        else:
            self._log(f"Setting up directory-based storage for {self.name}...")
            result = self._setup_directory_storage(workload)

        # Mark storage setup as complete if successful
        if result:
            self._storage_setup_complete = True

        return result

    @exclude_from_package
    def _setup_database_storage(self, workload: "Workload") -> bool:
        """
        System-specific storage setup for databases using additional disks.

        This default implementation:
        1. Detects local instance store devices
        2. Creates RAID0 if multiple local devices found
        3. Mounts single disk or RAID array

        Override this method in subclasses to implement system-specific
        storage requirements (e.g., partitioning, raw devices).

        Returns:
            True if successful, False otherwise
        """
        # Check if /data is already mounted - skip if so (idempotent)
        # Use space-padded grep to match exact mount point (not subdirectories)
        check_mount = self.execute_command("mount | grep ' /data '", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            self._log("✓ Storage already mounted at /data, skipping setup")
            self.data_dir = Path("/data")
            return True

        # First, try to detect local instance store devices
        local_devices = self._detect_storage_devices(
            skip_root=True, device_filter="local"
        )

        device_to_use = None
        # Mount at /data for shared access (data generation, databases)
        mount_point = "/data"

        if len(local_devices) > 1:
            # Multiple local instance store devices → create RAID0
            self._log(
                f"Detected {len(local_devices)} local instance store devices, creating RAID0..."
            )

            # Check if RAID already exists
            raid_device = "/dev/md0"
            raid_check = self.execute_command(
                f"test -b {raid_device} && echo 'exists'", record=False
            )

            if raid_check.get("success", False) and "exists" in raid_check.get(
                "stdout", ""
            ):
                self._log(f"✓ RAID array {raid_device} already exists")
                device_to_use = raid_device
            else:
                # Create RAID0 from all local devices
                # Use stable_path for consistent device identification across nodes
                device_paths = [d.get("stable_path", d["path"]) for d in local_devices]

                # Validate device paths - ensure no embedded newlines
                for idx, path in enumerate(device_paths):
                    if "\n" in path:
                        self._log(
                            f"[yellow]Warning: Device path {idx} contains newlines, using regular path instead[/yellow]"
                        )
                        # Fall back to regular path
                        device_paths[idx] = local_devices[idx]["path"]

                if self._create_raid0(device_paths, raid_device):
                    device_to_use = raid_device
                else:
                    self._log(
                        "Warning: RAID0 creation failed, falling back to first device"
                    )
                    # Prefer stable_path for multinode consistency
                    device_to_use = local_devices[0].get(
                        "stable_path", local_devices[0]["path"]
                    )

        elif len(local_devices) == 1:
            # Single local instance store device
            # Prefer stable_path for multinode consistency
            device_path = local_devices[0].get("stable_path", local_devices[0]["path"])
            self._log(f"Detected single local instance store device: {device_path}")
            device_to_use = device_path

        else:
            # No local devices, check for any additional devices (EBS, etc.)
            self._log(
                "No local instance store devices found, checking for EBS volumes..."
            )
            all_devices = self._detect_storage_devices(skip_root=True)

            if not all_devices:
                self._log(
                    f"Warning: No additional storage devices found for {self.name}, using directory storage"
                )
                return self._setup_directory_storage(workload)

            # Prefer stable_path for multinode consistency
            device_to_use = all_devices[0].get("stable_path", all_devices[0]["path"])
            self._log(f"Using EBS device: {device_to_use}")

        # Check if device is already mounted
        mount_check = self.execute_command(
            f"mount | grep {device_to_use}", record=False
        )
        if mount_check.get("success", False) and mount_check.get("stdout", "").strip():
            mount_parts = mount_check.get("stdout", "").split()
            if len(mount_parts) >= 3:
                current_mount = mount_parts[2]
                if current_mount == mount_point:
                    self._log(
                        f"✓ Device {device_to_use} already mounted at {mount_point}"
                    )
                    self.data_dir = Path(mount_point)
                    return True
                else:
                    # Mounted elsewhere, unmount first
                    self._log(
                        f"Device {device_to_use} mounted at {current_mount}, unmounting..."
                    )
                    if not self._unmount_disk(device_to_use):
                        self._log(f"Failed to unmount {device_to_use}")
                        return False

        # Format and mount
        if not self._format_disk(device_to_use):
            return False

        if not self._mount_disk(device_to_use, mount_point):
            return False

        # Set ownership
        self._set_ownership(mount_point)

        self.record_setup_note(
            f"Storage device {device_to_use} mounted at {mount_point}"
        )
        self._log(f"✓ Storage setup complete: {device_to_use} → {mount_point}")

        # Update data_dir to actual mount point
        self.data_dir = Path(mount_point)

        return True

    @exclude_from_package
    def _setup_directory_storage(self, workload: "Workload") -> bool:
        """
        Setup directory-based storage (no additional disks).

        Creates data_dir if specified in configuration.

        Returns:
            True if successful, False otherwise
        """
        if not self.data_dir:
            self._log(f"No data directory configured for {self.name}, skipping")
            return True

        # Create directory
        self.record_setup_command(
            f"sudo mkdir -p {self.data_dir}",
            f"Create data directory {self.data_dir}",
            "storage_setup",
        )
        result = self.execute_command(
            f"sudo mkdir -p {self.data_dir}", record=True, category="storage_setup"
        )

        if not result.get("success", False):
            self._log(f"Failed to create data directory {self.data_dir}")
            return False

        # Set ownership
        self._set_ownership(str(self.data_dir))

        self.record_setup_note(f"✓ Data directory created: {self.data_dir}")
        self._log(f"✓ Directory storage setup complete: {self.data_dir}")

        return True

    # ===================================================================
    # Cloud Instance Management Methods
    # ===================================================================

    @exclude_from_package
    def set_cloud_instance_manager(self, instance_manager: Any | list[Any]) -> None:
        """
        Set the cloud instance manager(s) for remote command execution.

        Args:
            instance_manager: Single CloudInstanceManager for single-node systems,
                            or list of CloudInstanceManagers for multinode systems
        """
        # Handle both single instance and list of instances
        if isinstance(instance_manager, list):
            # Multinode setup
            self._cloud_instance_managers = instance_manager
            self._cloud_instance_manager = (
                instance_manager[0] if instance_manager else None
            )
        else:
            # Single node setup
            self._cloud_instance_manager = instance_manager
            self._cloud_instance_managers = (
                [instance_manager] if instance_manager else []
            )

        # Set external host for health checks from local machine
        # This is critical for pre-existing installations where install() doesn't run
        if self._cloud_instance_manager and hasattr(
            self._cloud_instance_manager, "public_ip"
        ):
            self._external_host = self._cloud_instance_manager.public_ip
            # Keep self.host as localhost for remote execution
            if hasattr(self, "host"):
                self.host = "localhost"

            # Allow subclasses to update credentials from config
            self._update_credentials_from_config()

    @exclude_from_package  # noqa: B027
    def _update_credentials_from_config(self) -> None:
        """
        Hook for subclasses to update credentials after cloud manager is set.

        Override this method in subclasses to update system-specific credentials
        (e.g., password) from the setup_config when running on cloud instances.
        """
        pass  # Subclasses override if needed

    def _get_health_check_host(self) -> str:
        """
        Get the host to use for health checks, preferring external IP for remote systems.

        Priority:
        1. _external_host if explicitly set
        2. public_ip from cloud instance manager if available
        3. self.host as final fallback

        Returns:
            Host string to use for health checks
        """
        health_check_host: str | None = self._external_host

        if not health_check_host and self._cloud_instance_manager:
            health_check_host = getattr(self._cloud_instance_manager, "public_ip", None)

        if not health_check_host:
            health_check_host = getattr(self, "host", "localhost")

        return str(health_check_host) if health_check_host else "localhost"

    def _should_execute_remotely(self) -> bool:
        """
        Check if commands should be executed remotely.

        Override in subclasses if remote execution depends on additional conditions
        (e.g., ClickHouse checks setup_method == "native").

        Returns:
            True if commands should be executed on remote cloud instance
        """
        return self._cloud_instance_manager is not None

    @exclude_from_package
    def _setup_multinode_storage(self, workload: "Workload") -> bool:
        """
        Setup storage on all nodes in a multinode cluster.

        Each node gets its own storage setup via _setup_single_node_storage().
        Commands are recorded only for the first node to avoid duplicates in reports.

        Args:
            workload: Workload with scale factor for sizing calculations

        Returns:
            True if successful on all nodes, False otherwise
        """
        all_success = True

        # Store original setup_commands to prevent duplicate recording
        original_commands_count = len(self.setup_commands)

        for idx, mgr in enumerate(self._cloud_instance_managers):
            self._log(f"\n  [Node {idx}] Setting up storage...")

            # Temporarily override execute_command to use this specific node
            original_mgr = self._cloud_instance_manager
            self._cloud_instance_manager = mgr

            # For nodes after the first, temporarily disable recording to avoid duplicates
            if idx > 0:
                commands_before = len(self.setup_commands)

            try:
                # Run single-node storage setup on this node
                success = self._setup_single_node_storage(workload)
                if not success:
                    self._log(f"  [Node {idx}] ✗ Storage setup failed")
                    all_success = False
                else:
                    self._log(f"  [Node {idx}] ✓ Storage setup completed")
            finally:
                # For nodes after the first, remove any commands that were recorded
                if idx > 0:
                    self.setup_commands = self.setup_commands[:commands_before]

                # Restore primary manager
                self._cloud_instance_manager = original_mgr

        # Add node_info to all commands recorded during storage setup if multinode
        if len(self._cloud_instance_managers) > 1:
            node_info = f"all_nodes_{len(self._cloud_instance_managers)}"
            for i in range(original_commands_count, len(self.setup_commands)):
                self.setup_commands[i]["node_info"] = node_info

        return all_success

    @exclude_from_package
    def _setup_single_node_storage(self, workload: "Workload") -> bool:
        """
        Setup storage on a single node.

        Override this method in subclasses for system-specific storage setup.
        Called by _setup_multinode_storage() for each node in a cluster.

        Args:
            workload: Workload with scale factor for sizing calculations

        Returns:
            True if successful, False otherwise
        """
        # Default implementation uses the base class database storage setup
        # Subclasses should override this method for system-specific storage
        return self._setup_database_storage(workload)

    def _detect_hardware_specs(self) -> dict[str, int]:
        """
        Detect actual CPU cores and memory from the system.

        Returns:
            Dictionary with 'cpu_cores' and 'total_memory_bytes' keys
        """
        # Get CPU count
        cpu_result = self.execute_command("nproc", record=False)
        if cpu_result.get("success", False):
            try:
                cpu_cores = int(cpu_result["stdout"].strip())
                # Sanity check: CPU cores should be reasonable (between 1 and 512)
                if cpu_cores < 1 or cpu_cores > 512:
                    self._log(
                        f"⚠️  WARNING: Detected {cpu_cores} CPU cores - this seems wrong, using default 16"
                    )
                    cpu_cores = 16
            except (ValueError, KeyError):
                cpu_cores = 16  # Fallback default
        else:
            cpu_cores = 16  # Fallback default

        # Get total memory in bytes
        mem_result = self.execute_command(
            "grep MemTotal /proc/meminfo | awk '{print $2}'", record=False
        )
        if mem_result.get("success", False):
            try:
                mem_kb = int(mem_result["stdout"].strip())
                mem_bytes = mem_kb * 1024
            except (ValueError, KeyError):
                mem_bytes = 64 * 1024 * 1024 * 1024  # 64GB fallback
        else:
            mem_bytes = 64 * 1024 * 1024 * 1024  # 64GB fallback

        return {"cpu_cores": cpu_cores, "total_memory_bytes": mem_bytes}

    def _parse_memory_size(self, memory_str: str) -> int:
        """
        Parse memory size string like '32g', '1024m' to bytes.

        Args:
            memory_str: Memory size string with optional unit suffix (g, m, k)

        Returns:
            Memory size in bytes
        """
        memory_str = memory_str.lower().strip()

        if memory_str.endswith("g"):
            return int(memory_str[:-1]) * 1024 * 1024 * 1024
        elif memory_str.endswith("m"):
            return int(memory_str[:-1]) * 1024 * 1024
        elif memory_str.endswith("k"):
            return int(memory_str[:-1]) * 1024
        else:
            # Assume bytes
            return int(memory_str)

    def _get_int_config(self, config: dict[str, Any], key: str, default: int) -> int:
        """
        Safely get an integer value from config, handling both string and int inputs.

        Args:
            config: Configuration dictionary
            key: Key to look up
            default: Default value if key not present

        Returns:
            Integer value (converted from string if necessary)
        """
        value = config.get(key, default)
        if isinstance(value, str):
            return int(value)
        return int(value)

    def _resolve_ip_addresses(self, ip_config: str) -> str:
        """
        Resolve IP address placeholders with actual values from infrastructure.

        Handles environment variable substitution (e.g., $EXASOL_PUBLIC_IP)
        and InfraManager-based resolution.

        Args:
            ip_config: IP address string or environment variable placeholder

        Returns:
            Resolved IP address string
        """
        import os

        if not ip_config:
            return "localhost"

        # Handle environment variable substitution
        if ip_config.startswith("$"):
            env_var = ip_config[1:]  # Remove $ prefix

            # Try InfraManager first for infrastructure-managed IPs
            try:
                from benchkit.infra.manager import InfraManager

                project_id = self.config.get("project_id", "")
                resolved = InfraManager.resolve_ip_from_infrastructure(
                    env_var, self.name, project_id
                )
                if resolved:
                    return str(resolved)
            except ImportError:
                pass  # InfraManager not available, fall back to env var

            # Fall back to environment variable
            return os.environ.get(env_var, ip_config)

        # If it's already an IP address, return as-is
        return ip_config

    def estimate_execution_time(
        self, operation: TableOperation, data_size_gb: float
    ) -> timedelta:
        """
        Calculate an estimated (pessimistic) execution time for the given operation,
        based on system properties and table size.

        The default implementation returns a fixed value of 5 minutes

        Args:
            operation: The operation to take place
            data_size_gb: estimated size of data to operate on
        """
        return timedelta(minutes=5)

    # noinspection PyMethodMayBeStatic
    def split_sql_statements(self, sql: str) -> list[str]:
        """
        Split SQL script into individual statements.
        Method is not static in case some system uses different syntax for splitting

        Handles:
        - Semicolon-separated statements
        - SQL comments (-- and /* */)
        - Empty lines

        Returns:
            List of individual SQL statements
        """
        statements = []
        current_statement = []
        in_comment = False

        for line in sql.split("\n"):
            stripped = line.strip()

            # Skip SQL comments
            if stripped.startswith("--"):
                continue

            # Handle multi-line comments
            if "/*" in stripped:
                in_comment = True
            if "*/" in stripped:
                in_comment = False
                continue
            if in_comment:
                continue

            # Skip empty lines
            if not stripped:
                continue

            # Check if line ends with semicolon (statement terminator)
            if stripped.endswith(";"):
                # Add the line without semicolon to current statement
                current_statement.append(stripped[:-1])
                # Join and add to statements list
                statements.append("\n".join(current_statement))
                # Reset for next statement
                current_statement = []
            else:
                # Add line to current statement
                current_statement.append(stripped)

        # Add any remaining statement (for scripts without trailing semicolon)
        if current_statement:
            statements.append("\n".join(current_statement))

        return statements


def get_system_class(system_kind: str) -> type | None:
    """
    Dynamically import and return the system class for the given system kind.

    Args:
        system_kind: The system identifier (e.g., 'exasol', 'clickhouse', 'postgres')

    Returns:
        The system class if found, None otherwise
    """
    import importlib
    import inspect

    class_name = f"{system_kind.capitalize()}System"
    module_name = f"benchkit.systems.{system_kind}"

    try:
        module = importlib.import_module(module_name)

        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            return cls if isinstance(cls, type) else None
        else:
            # Try to find any class that inherits from SystemUnderTest
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, SystemUnderTest)
                    and attr != SystemUnderTest
                    and hasattr(attr, "get_python_dependencies")
                ):
                    return attr

            return None

    except ImportError:
        return None
