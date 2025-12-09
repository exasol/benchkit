"""ClickHouse database system implementation."""

from collections.abc import Callable, Iterable
from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import clickhouse_connect
except ModuleNotFoundError:
    # optional for most part
    pass

from benchkit.common.markers import exclude_from_package

from .base import SystemUnderTest, TableOperation

if TYPE_CHECKING:
    # avoid cyclic dependency problems
    from ..util import Timer
    from ..workloads import Workload


class ClickHouseSystem(SystemUnderTest):
    """ClickHouse database system implementation."""

    # ClickHouse supports multinode clusters via sharding
    SUPPORTS_MULTINODE = True

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by ClickHouse system."""
        return ["clickhouse-connect>=0.6.0"]

    @classmethod
    def _get_connection_defaults(cls) -> dict[str, Any]:
        return {
            "port": 8123,
            "username": "default",
            "password": "",
            "schema_key": "database",
            "schema": "benchmark",
        }

    @classmethod
    def _extend_connection_info(
        cls, conn_info: dict[str, Any], setup_config: dict[str, Any]
    ) -> None:
        if "extra" in setup_config:
            conn_info["extra"] = setup_config["extra"]

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """Return ports required by ClickHouse system."""
        return {
            "ClickHouse HTTP": 8123,
            "ClickHouse Native": 9000,
            "ClickHouse MySQL": 9004,
            "ClickHouse PostgreSQL": 9005,
        }

    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """Get ClickHouse connection string with full CLI command."""
        port = self.setup_config.get("port", 8123)
        username = self.setup_config.get("username", "default")
        database = self.setup_config.get("database", "benchmark")
        password = self.setup_config.get("password", "")

        # Check if using HTTP or native protocol (port 8123 is HTTP, use native port 9000 for CLI)
        if port == 8123:
            cmd = f"clickhouse-client --host {public_ip} --port 9000 --user {username}"
        else:
            cmd = (
                f"clickhouse-client --host {public_ip} --port {port} --user {username}"
            )

        # Add database if not default
        if database and database != "default":
            cmd += f" --database {database}"

        # Add password prompt if password is set
        if password:
            cmd += " --password"

        return cmd

    def __init__(
        self,
        config: dict[str, Any],
        output_callback: Callable[[str], None] | None = None,
        workload_config: dict[str, Any] | None = None,
    ):
        super().__init__(config, output_callback, workload_config)
        self.setup_method = self.setup_config.get("method", "docker")

        # Include project_id in container name for parallel project isolation
        project_id = config.get("project_id", "")
        if project_id:
            self.container_name = f"clickhouse_{project_id}_{self.name}"
        else:
            self.container_name = f"clickhouse_{self.name}"

        # Use 'or {}' to handle case where 'extra' exists but is None
        self.config_profile = (self.setup_config.get("extra") or {}).get(
            "config_profile", "default"
        )
        self.http_port = 8123
        self.native_port = 9000

        # Connection settings - resolve host IP addresses from config or infrastructure
        raw_host = self.setup_config.get("host", "localhost")
        resolved_host = self._resolve_ip_addresses(raw_host)

        # For multinode, resolved_host may contain comma-separated IPs
        # Use first IP only for connection
        if "," in resolved_host:
            self.host = resolved_host.split(",")[0].strip()
        else:
            self.host = resolved_host

        self.port = self.setup_config.get(
            "port", 8123
        )  # HTTP port for clickhouse-connect
        self.username = self.setup_config.get("username", "default")
        self.password = self.setup_config.get("password", "")
        # Use 'benchmark' as default database for workload compatibility
        self.database = self.setup_config.get("database", "benchmark")

        self._client = None

        # Cluster configuration for multinode
        self.cluster_name = "benchmark_cluster"  # Default cluster name

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """Check if ClickHouse is already installed by checking for the service or binary."""
        if self.setup_method == "docker":
            # Check if container exists and is running
            result = self.execute_command(
                f"docker ps -q -f name={self.container_name}", record=False
            )
            return result.get("success", False) and bool(
                result.get("stdout", "").strip()
            )
        else:  # native installation
            # Multi-level verification similar to Exasol approach
            # Level 1: Check for installation marker file
            if not self.has_install_marker():
                self._log("No existing ClickHouse installation marker found")
                return False

            self._log("Found existing ClickHouse installation marker")

            # Level 2: Check if clickhouse-server binary is available
            binary_check = self.execute_command("which clickhouse-server", record=False)
            if not binary_check.get("success", False):
                self._log(
                    "⚠ Installation marker found but clickhouse-server not available, will reinstall"
                )
                return False

            self._log("✓ clickhouse-server binary available")

            # Level 3: Check if service is running
            service_check = self.execute_command(
                "systemctl is-active clickhouse-server", record=False
            )
            if not service_check.get("success", False):
                self._log("⚠ clickhouse-server service not running, will restart")
                return False

            self._log("✓ clickhouse-server service is active")

            # Level 4: Most importantly - check if database is accessible
            self._log("Checking if ClickHouse database is accessible...")
            if self.is_healthy(quiet=False):
                self._log("✓ ClickHouse database is accessible and healthy")
                return True
            else:
                self._log(
                    "⚠ ClickHouse installation exists but database not accessible, will restart"
                )
                return False

    def _get_client(self) -> Any:
        """Get a client connection to ClickHouse database using clickhouse-connect."""
        if clickhouse_connect is None:
            return None

        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
            interface="http",
            secure=False,
        )

    @exclude_from_package
    def _install_docker(self) -> bool:
        """Install ClickHouse using Docker."""
        memory_limit = (self.setup_config.get("extra") or {}).get("memory_limit", "32g")
        image = f"clickhouse/clickhouse-server:{self.version if self.version != 'latest' else 'latest'}"
        return self._install_docker_common(
            image,
            {self.http_port: 8123, self.native_port: 9000},
            {str(self.data_dir): "/var/lib/clickhouse"},
            extra_args=["--memory", memory_limit],
        )

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install ClickHouse using official APT repository."""
        self.record_setup_note("Installing ClickHouse using official APT repository")
        is_multinode = (
            self._cloud_instance_managers and len(self._cloud_instance_managers) > 1
        )
        if not self._install_on_all_nodes(self._install_native_on_node):
            return False
        if is_multinode:
            if not self._configure_multinode_cluster():
                return False
            self.execute_command_on_all_nodes(
                "sudo systemctl restart clickhouse-server",
                "Restart ClickHouse on all nodes",
            )
        return True

    def _install_native_on_node(self) -> bool:
        """Install ClickHouse on the current node (works for both single and multinode)."""
        # Defensive: ensure setup_config is not None (can happen in parallel execution)
        if self.setup_config is None:
            self._log(
                "ERROR: setup_config is None, attempting to recover from self.config"
            )
            if hasattr(self, "config") and self.config and "setup" in self.config:
                self.setup_config = self.config["setup"]
                self._log("✓ Recovered setup_config from self.config")
            else:
                raise RuntimeError("setup_config is None and cannot be recovered")

        # Resolve IP addresses from configuration
        resolved_host = self._resolve_ip_addresses(
            self.setup_config.get("host", "localhost")
        )

        # For multinode, resolved_host may contain comma-separated IPs
        # Use first IP only for connection
        if "," in resolved_host:
            resolved_host = resolved_host.split(",")[0].strip()

        try:
            # Step 1: Install prerequisite packages
            self.record_setup_command(
                "sudo apt-get update", "Update package lists", "prerequisites"
            )
            result = self.execute_command("sudo apt-get update")
            if not result["success"]:
                self._log(f"Failed to update package lists: {result['stderr']}")
                return False

            self.record_setup_command(
                "sudo apt-get install -y apt-transport-https ca-certificates curl gnupg",
                "Install prerequisite packages for secure repository access",
                "prerequisites",
            )
            result = self.execute_command(
                "sudo apt-get install -y apt-transport-https ca-certificates curl gnupg"
            )
            if not result["success"]:
                self._log(f"Failed to install prerequisites: {result['stderr']}")
                return False

            # Step 2: Add ClickHouse GPG key
            # Remove existing keyring file to avoid GPG interactive prompt
            self.execute_command(
                "sudo rm -f /usr/share/keyrings/clickhouse-keyring.gpg", record=False
            )

            self.record_setup_command(
                "curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg",
                "Add ClickHouse GPG key to system keyring",
                "repository_setup",
            )
            result = self.execute_command(
                "curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg"
            )
            if not result["success"]:
                self._log(f"Failed to add ClickHouse GPG key: {result['stderr']}")
                return False

            # Step 3: Add ClickHouse repository
            self.record_setup_command(
                'ARCH=$(dpkg --print-architecture) && echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list',
                "Add ClickHouse official repository to APT sources",
                "repository_setup",
            )
            result = self.execute_command(
                'ARCH=$(dpkg --print-architecture) && echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main" | sudo tee /etc/apt/sources.list.d/clickhouse.list'
            )
            if not result["success"]:
                self._log(f"Failed to add ClickHouse repository: {result['stderr']}")
                return False

            # Step 4: Update package lists with new repository
            self.record_setup_command(
                "sudo apt-get update",
                "Update package lists with ClickHouse repository",
                "repository_setup",
            )
            result = self.execute_command("sudo apt-get update")
            if not result["success"]:
                self._log(
                    f"Failed to update package lists after adding repository: {result['stderr']}"
                )
                return False

            # Step 5: Install ClickHouse packages (non-interactive)
            # Set DEBIAN_FRONTEND to noninteractive to avoid password prompts
            install_env = "DEBIAN_FRONTEND=noninteractive"

            if self.version and self.version != "latest":
                # Try to install specific version first
                version_suffix = f"={self.version}"
                # Install all three packages with same version to avoid dependency conflicts
                install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-common-static{version_suffix} clickhouse-server{version_suffix} clickhouse-client{version_suffix}"
                description = (
                    f"Install ClickHouse server and client version {self.version}"
                )
                self._log(f"Attempting to install ClickHouse {self.version}...")

                self.record_setup_command(
                    f"sudo apt-get install -y clickhouse-common-static{version_suffix} clickhouse-server{version_suffix} clickhouse-client{version_suffix}",
                    description,
                    "installation",
                )
                result = self.execute_command(
                    install_cmd, timeout=300
                )  # 5 min timeout for installation

                if not result["success"]:
                    self._log(
                        f"Version {self.version} not available, falling back to latest..."
                    )
                    # Fallback to latest version - install all packages together
                    install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-common-static clickhouse-server clickhouse-client"
                    description = (
                        "Install latest ClickHouse server and client (fallback)"
                    )

                    self.record_setup_command(
                        "sudo apt-get install -y clickhouse-common-static clickhouse-server clickhouse-client",
                        description,
                        "installation",
                    )
                    result = self.execute_command(install_cmd, timeout=300)

                    if not result["success"]:
                        self._log(
                            f"Failed to install ClickHouse (even latest): {result['stderr']}"
                        )
                        return False
                    else:
                        self._log("✓ Successfully installed latest ClickHouse version")
                else:
                    self._log(f"✓ Successfully installed ClickHouse {self.version}")
            else:
                # Install latest version - install all packages together to avoid conflicts
                install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-common-static clickhouse-server clickhouse-client"
                description = "Install latest ClickHouse server and client"
                self._log("Installing latest ClickHouse version...")

                self.record_setup_command(
                    "sudo apt-get install -y clickhouse-common-static clickhouse-server clickhouse-client",
                    description,
                    "installation",
                )
                result = self.execute_command(install_cmd, timeout=300)

                if not result["success"]:
                    self._log(f"Failed to install ClickHouse: {result['stderr']}")
                    return False
                else:
                    self._log("✓ Successfully installed ClickHouse")

            # Step 6: Detect hardware specs for optimal configuration
            self._log("📊 Detecting hardware specifications...")
            hw_specs = self._detect_hardware_specs()
            cpu_cores = hw_specs["cpu_cores"]
            total_mem_gb = hw_specs["total_memory_bytes"] / (1024**3)
            self._log(f"✓ Detected: {cpu_cores} CPU cores, {total_mem_gb:.1f}GB RAM")

            # Step 7: Calculate optimal settings based on hardware
            # Defensive: ensure setup_config is still not None
            if self.setup_config is None:
                self._log(
                    "ERROR: setup_config is None, attempting to recover from self.config"
                )
                if hasattr(self, "config") and self.config and "setup" in self.config:
                    self.setup_config = self.config["setup"]
                    self._log("✓ Recovered setup_config from self.config")
                else:
                    raise RuntimeError("setup_config is None and cannot be recovered")

            # Use 'or {}' to handle case where 'extra' exists but is None
            extra_config = self.setup_config.get("extra") or {}
            settings = self._calculate_optimal_settings(hw_specs, extra_config)
            self._log("⚙️  Calculated optimal settings:")
            self._log(f"   - max_threads: {settings['max_threads']}")
            self._log(
                f"   - max_memory_usage: {settings['max_memory_usage'] / 1e9:.1f}GB (per query)"
            )
            self._log(
                f"   - max_server_memory_usage: {settings['max_server_memory_usage'] / 1e9:.1f}GB (total)"
            )
            self._log(
                f"   - max_concurrent_queries: {settings['max_concurrent_queries']}"
            )

            # Step 8: Configure ClickHouse server (server-level settings)
            self._configure_clickhouse_server(settings)

            # Step 9: Configure user profile (query-level settings + password)
            if self.password:
                self._configure_user_profile(settings)

            # Note: Cluster configuration is handled at higher level for multinode

            # Step 10: Start and enable ClickHouse service
            self.record_setup_command(
                "sudo systemctl start clickhouse-server",
                "Start ClickHouse server service",
                "service_management",
            )
            result = self.execute_command("sudo systemctl start clickhouse-server")
            if not result["success"]:
                self._log(f"Failed to start ClickHouse service: {result['stderr']}")
                return False

            self.record_setup_command(
                "sudo systemctl enable clickhouse-server",
                "Enable ClickHouse server to start on boot",
                "service_management",
            )
            self.execute_command("sudo systemctl enable clickhouse-server")

            # Step 11: Wait for ClickHouse to be ready
            self.record_setup_note(
                "Waiting for ClickHouse server to be ready for connections..."
            )
            self._log("Waiting for ClickHouse server to be ready...")
            if not self.wait_for_health(max_attempts=30, delay=2.0):
                self._log("ClickHouse server failed to become ready within timeout")
                return False

            self.record_setup_note(
                "ClickHouse server is ready and accepting connections"
            )

            # Update connection parameters for deployed server
            # Set host based on context:
            # - External IP for health checks from local machine
            # - localhost for benchmark execution on remote machine
            if self._cloud_instance_manager:
                self._external_host = (
                    resolved_host  # Store external IP for health checks
                )
                self.host = "localhost"  # Use localhost for benchmark execution
            else:
                self.host = resolved_host

            # Record applied configuration
            self.record_setup_note("ClickHouse configuration applied:")
            self.record_setup_note(
                f"  Hardware-detected settings (CPU cores: {cpu_cores}, RAM: {total_mem_gb:.1f}GB)"
            )
            for key, value in settings.items():
                if (
                    isinstance(value, int) and value > 1000000
                ):  # Format large byte values
                    self.record_setup_note(f"  {key}: {value / 1e9:.1f}GB")
                else:
                    self.record_setup_note(f"  {key}: {value}")

            # Mark that system is installed
            self.mark_installed(record=False)
            self._log("✓ ClickHouse installation completed successfully")

            return True

        except Exception as e:
            self._log(f"Native ClickHouse installation failed: {e}")
            # Log full traceback for debugging
            import traceback

            self._log(f"Traceback:\n{traceback.format_exc()}")
            return False

    @exclude_from_package
    def _configure_clickhouse_server(self, settings: dict[str, Any]) -> None:
        """
        Configure ClickHouse server with server-level settings only.

        This configures infrastructure-level settings in config.d/benchmark.xml.
        User-level query settings are configured separately in users.xml.

        Args:
            settings: Dictionary of calculated optimal settings
        """
        config_changes = []

        # Configure network listening (listen on all interfaces for remote access)
        config_changes.append("    <listen_host>::</listen_host>")

        # Handle custom data directory
        if str(self.data_dir) != "/var/lib/clickhouse":
            config_changes.append(f"    <path>{self.data_dir}</path>")
            # CRITICAL: Also set tmp_path to use the same fast storage
            # This is where external sorts/aggregations spill when exceeding memory limits
            config_changes.append(f"    <tmp_path>{self.data_dir}/tmp</tmp_path>")

        # Make sure the ownership is set correctly
        self._set_ownership(str(self.data_dir), owner="clickhouse:clickhouse")

        # Server-level memory limit (total server memory usage)
        if "max_server_memory_usage" in settings:
            config_changes.append(
                f"    <max_server_memory_usage>{settings['max_server_memory_usage']}</max_server_memory_usage>"
            )

        # Concurrent query limit
        if "max_concurrent_queries" in settings:
            config_changes.append(
                f"    <max_concurrent_queries>{settings['max_concurrent_queries']}</max_concurrent_queries>"
            )

        # Background operation pool sizes (match CPU cores)
        if "background_pool_size" in settings:
            config_changes.append(
                f"    <background_pool_size>{settings['background_pool_size']}</background_pool_size>"
            )

        if "background_schedule_pool_size" in settings:
            config_changes.append(
                f"    <background_schedule_pool_size>{settings['background_schedule_pool_size']}</background_schedule_pool_size>"
            )

        # Safety limits
        if "max_table_size_to_drop" in settings:
            config_changes.append(
                f"    <max_table_size_to_drop>{settings['max_table_size_to_drop']}</max_table_size_to_drop>"
            )

        if config_changes:
            # Create custom configuration file with proper indentation
            config_lines = "\n".join(config_changes)
            config_content = f"""<clickhouse>
{config_lines}
</clickhouse>"""

            config_file_path = "/etc/clickhouse-server/config.d/benchmark.xml"
            self.record_setup_command(
                f"sudo tee {config_file_path} > /dev/null << 'EOF'\n{config_content}\nEOF",
                "Create custom ClickHouse configuration file",
                "configuration",
            )

            # Create the config file
            create_config_cmd = f"sudo tee {config_file_path} > /dev/null << 'EOF'\n{config_content}\nEOF"
            result = self.execute_command(create_config_cmd)
            if not result["success"]:
                self._log(
                    f"Warning: Failed to create ClickHouse config file: {result.get('stderr', 'Unknown error')}"
                )

            self.record_setup_note(
                f"ClickHouse configuration file created: {config_file_path}"
            )

    @exclude_from_package
    def _configure_user_profile(self, settings: dict[str, Any]) -> None:
        """
        Configure ClickHouse user profile with query-level settings and password.

        This configures user-level settings in users.d/benchmark.xml, including:
        - Password authentication
        - Query execution limits (max_threads, max_memory_usage, etc.)
        - TPC-H specific settings

        Args:
            settings: Dictionary of calculated optimal settings
        """
        # Create password hash (single SHA256 for password_sha256_hex)
        import hashlib

        password_hash = hashlib.sha256(self.password.encode()).hexdigest()

        # Build user profile settings (query-level limits)
        profile_settings = []

        # Query execution settings
        if "max_threads" in settings:
            profile_settings.append(
                f"            <max_threads>{settings['max_threads']}</max_threads>"
            )

        if "max_memory_usage" in settings:
            profile_settings.append(
                f"            <max_memory_usage>{settings['max_memory_usage']}</max_memory_usage>"
            )

        if "max_bytes_before_external_sort" in settings:
            profile_settings.append(
                f"            <max_bytes_before_external_sort>{settings['max_bytes_before_external_sort']}</max_bytes_before_external_sort>"
            )

        if "max_bytes_before_external_group_by" in settings:
            profile_settings.append(
                f"            <max_bytes_before_external_group_by>{settings['max_bytes_before_external_group_by']}</max_bytes_before_external_group_by>"
            )

        if "optimize_move_to_prewhere" in settings:
            profile_settings.append(
                f"            <optimize_move_to_prewhere>{settings['optimize_move_to_prewhere']}</optimize_move_to_prewhere>"
            )

        # TPC-H specific settings
        profile_settings.append("            <join_use_nulls>1</join_use_nulls>")
        profile_settings.append(
            "            <allow_experimental_correlated_subqueries>1</allow_experimental_correlated_subqueries>"
        )

        # Performance optimizations
        profile_settings.append(
            "            <optimize_read_in_order>1</optimize_read_in_order>"
        )
        profile_settings.append(
            "            <max_insert_threads>8</max_insert_threads>"
        )

        # Statistics for query optimization (ClickHouse 24.6+)
        # Only enable if explicitly requested in extra config
        # Use 'or {}' to handle case where 'extra' exists but is None
        extra_config = self.setup_config.get("extra") or {}
        if extra_config.get("allow_statistics_optimize", 0) == 1:
            profile_settings.append(
                "            <allow_experimental_statistics>1</allow_experimental_statistics>"
            )
            profile_settings.append(
                "            <allow_statistics_optimize>1</allow_statistics_optimize>"
            )

        # Create users configuration file with profile settings
        profile_lines = "\n".join(profile_settings)
        profile_section = f"""
    <profiles>
        <default>
{profile_lines}
        </default>
    </profiles>"""

        users_config = f"""<clickhouse>
    <users>
        <default replace="true">
            <password_sha256_hex>{password_hash}</password_sha256_hex>
            <networks>
                <ip>::/0</ip>
            </networks>
        </default>
    </users>{profile_section}
</clickhouse>"""

        users_file_path = "/etc/clickhouse-server/users.d/benchmark.xml"
        self.record_setup_command(
            f"sudo tee {users_file_path} > /dev/null << 'EOF'\n{users_config}\nEOF",
            "Configure ClickHouse user profile with password and query settings",
            "user_configuration",
        )

        # Create the users config file
        create_users_cmd = (
            f"sudo tee {users_file_path} > /dev/null << 'EOF'\n{users_config}\nEOF"
        )
        result = self.execute_command(create_users_cmd)
        if not result["success"]:
            self._log(
                f"Warning: Failed to configure user profile: {result.get('stderr', 'Unknown error')}"
            )
        else:
            self.record_setup_note(
                "ClickHouse user profile configured with optimized settings"
            )

    @exclude_from_package
    def _configure_multinode_cluster(self) -> bool:
        """
        Configure ClickHouse cluster for multinode deployment.

        Generates and distributes:
        1. remote_servers.xml - cluster topology (same on all nodes)
        2. macros.xml - node-specific shard/replica info (unique per node)

        For benchmarking, we use sharding WITHOUT replication (no Keeper needed).
        """
        if not self._cloud_instance_managers or len(self._cloud_instance_managers) < 2:
            self._log("Skipping cluster configuration: not multinode")
            return True

        self._log(
            f"Configuring cluster with {len(self._cloud_instance_managers)} nodes..."
        )

        # Build list of node IPs
        node_ips = [mgr.private_ip for mgr in self._cloud_instance_managers]

        # Generate remote_servers.xml content (same on all nodes)
        remote_servers_xml = self._generate_remote_servers_xml(node_ips)

        # Distribute remote_servers.xml to ALL nodes
        remote_servers_path = "/etc/clickhouse-server/config.d/remote_servers.xml"
        self.record_setup_command(
            f"sudo tee {remote_servers_path} > /dev/null << 'EOF'\n{remote_servers_xml}\nEOF",
            "Create cluster configuration (remote_servers.xml) on all nodes",
            "cluster_configuration",
        )

        self._log("Distributing remote_servers.xml to all nodes...")
        for idx, mgr in enumerate(self._cloud_instance_managers):
            create_config_cmd = f"sudo tee {remote_servers_path} > /dev/null << 'EOF'\n{remote_servers_xml}\nEOF"
            result = mgr.run_remote_command(create_config_cmd, timeout=60)
            if result.get("success"):
                self._log(f"  ✓ remote_servers.xml created on node {idx}")
            else:
                self._log(f"  ✗ Failed to create remote_servers.xml on node {idx}")
                return False

        # Generate and distribute unique macros.xml for each node
        self._log("Distributing unique macros.xml to each node...")
        for idx, mgr in enumerate(self._cloud_instance_managers):
            # Generate node-specific macros
            macros_xml = self._generate_macros_xml(idx + 1, node_ips[idx])
            macros_path = "/etc/clickhouse-server/config.d/macros.xml"

            # Record for first node as example
            if idx == 0:
                self.record_setup_command(
                    f"sudo tee {macros_path} > /dev/null << 'EOF'\n{macros_xml}\nEOF",
                    "Create node-specific macros (example for node 0)",
                    "cluster_configuration",
                )

            create_macros_cmd = (
                f"sudo tee {macros_path} > /dev/null << 'EOF'\n{macros_xml}\nEOF"
            )
            result = mgr.run_remote_command(create_macros_cmd, timeout=60)
            if result.get("success"):
                self._log(f"  ✓ macros.xml created on node {idx} (shard={idx+1})")
            else:
                self._log(f"  ✗ Failed to create macros.xml on node {idx}")
                return False

        self.record_setup_note(
            f"ClickHouse cluster configured with {len(node_ips)} nodes (sharding without replication)"
        )
        self.record_setup_note(f"Cluster name: {self.cluster_name}")

        return True

    @exclude_from_package
    def _generate_remote_servers_xml(self, node_ips: list[str]) -> str:
        """
        Generate remote_servers.xml content for cluster configuration.

        Creates a cluster with N shards (one per node), without replication.
        Each shard has only 1 replica.
        """
        shard_entries = []
        for _idx, ip in enumerate(node_ips):
            shard_entry = f"""        <shard>
            <replica>
                <host>{ip}</host>
                <port>9000</port>
            </replica>
        </shard>"""
            shard_entries.append(shard_entry)

        shards_xml = "\n".join(shard_entries)

        return f"""<clickhouse>
    <remote_servers>
        <{self.cluster_name}>
{shards_xml}
        </{self.cluster_name}>
    </remote_servers>
</clickhouse>"""

    @exclude_from_package
    def _generate_macros_xml(self, shard_num: int, replica_name: str) -> str:
        """
        Generate macros.xml content for a specific node.

        Args:
            shard_num: Shard number (1-indexed)
            replica_name: Unique replica identifier (usually the node's IP)
        """
        return f"""<clickhouse>
    <macros>
        <cluster>{self.cluster_name}</cluster>
        <shard>{shard_num}</shard>
        <replica>node{shard_num}</replica>
    </macros>
</clickhouse>"""

    def _calculate_max_concurrent_queries(self, cpu_cores: int) -> int:
        """
        Calculate max_concurrent_queries based on workload configuration.

        Uses num_streams from multiuser config if available, otherwise falls back
        to a reasonable default based on CPU cores.

        Args:
            cpu_cores: Number of CPU cores available

        Returns:
            Calculated max_concurrent_queries value
        """
        # Get num_streams from workload multiuser config
        # Use 'or {}' to handle case where multiuser exists but is None
        multiuser_config = (self.workload_config or {}).get("multiuser") or {}
        num_streams: int = int(multiuser_config.get("num_streams", 1))

        # Base value on CPU cores
        base_value = max(4, cpu_cores)

        # If multiuser is enabled, ensure we have enough capacity
        # Add buffer for system queries and overhead
        if num_streams > 1:
            return max(base_value, num_streams + 10)

        return base_value

    @exclude_from_package
    def _calculate_optimal_settings(
        self, hw_specs: dict[str, int], extra_config: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate optimal ClickHouse settings based on hardware.

        This method calculates sensible defaults based on detected hardware,
        but allows explicit overrides from extra_config.

        Args:
            hw_specs: Hardware specifications (cpu_cores, total_memory_bytes)
            extra_config: User-provided configuration overrides

        Returns:
            Dictionary of optimized settings for ClickHouse
        """
        cpu_cores = hw_specs["cpu_cores"]
        total_mem = hw_specs["total_memory_bytes"]

        # Calculate settings with intelligent defaults
        # Allow overrides from extra_config, otherwise use calculated values
        # Use _get_int_config to handle both string and int config values
        settings = {
            # User-level settings (per query limits)
            "max_threads": self._get_int_config(extra_config, "max_threads", cpu_cores),
            "max_memory_usage": self._get_int_config(
                extra_config, "max_memory_usage", int(total_mem * 0.75)
            ),
            "max_bytes_before_external_sort": self._get_int_config(
                extra_config, "max_bytes_before_external_sort", int(total_mem * 0.55)
            ),
            "max_bytes_before_external_group_by": self._get_int_config(
                extra_config,
                "max_bytes_before_external_group_by",
                int(total_mem * 0.55),
            ),
            # Server-level settings
            "max_server_memory_usage": self._get_int_config(
                extra_config, "max_server_memory_usage", int(total_mem * 0.80)
            ),
            "max_concurrent_queries": self._get_int_config(
                extra_config,
                "max_concurrent_queries",
                self._calculate_max_concurrent_queries(cpu_cores),
            ),
            "background_pool_size": self._get_int_config(
                extra_config, "background_pool_size", max(16, cpu_cores)
            ),
            "background_schedule_pool_size": self._get_int_config(
                extra_config, "background_schedule_pool_size", cpu_cores
            ),
            # Safety limits
            "max_table_size_to_drop": self._get_int_config(
                extra_config, "max_table_size_to_drop", 50000000000
            ),
        }

        # Handle legacy memory_limit parameter (convert to max_memory_usage)
        if "memory_limit" in extra_config and "max_memory_usage" not in extra_config:
            settings["max_memory_usage"] = self._parse_memory_size(
                extra_config["memory_limit"]
            )

        # Gather rest of configs
        for k in extra_config.keys():
            if k not in settings:
                settings[k] = extra_config[k]

        return settings

    @exclude_from_package
    def _setup_database_storage(self, workload: Workload) -> bool:
        """
        Override base class to setup ClickHouse storage on additional disk.

        ClickHouse uses a subdirectory under /data for its data.
        The base class mounts the disk/RAID at /data.

        For multinode clusters, this runs on ALL nodes.

        Returns:
            True if successful, False otherwise
        """
        # For multinode, we need to setup storage on ALL nodes
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            self._log(
                f"Setting up storage on all {len(self._cloud_instance_managers)} nodes..."
            )
            return self._setup_multinode_storage(workload)

        # Single node setup
        return self._setup_single_node_storage(workload)

    @exclude_from_package
    def _setup_single_node_storage(self, workload: Workload) -> bool:
        """
        Setup storage on a single node. Used by both single-node and multinode setups.
        """
        # Check if /data is already mounted
        check_mount = self.execute_command("mount | grep '/data'", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            self._log(
                "    Storage already mounted at /data, creating ClickHouse subdirectory"
            )
            # Create clickhouse subdirectory
            clickhouse_dir = "/data/clickhouse"
            self.record_setup_command(
                f"sudo mkdir -p {clickhouse_dir}",
                "Create ClickHouse data directory under /data",
                "storage_setup",
            )
            self.execute_command(
                f"sudo mkdir -p {clickhouse_dir}", record=True, category="storage_setup"
            )
            self._set_ownership(clickhouse_dir, owner="clickhouse:clickhouse")
            self.data_dir = Path(clickhouse_dir)
            return True

        # Use base class to mount disk/RAID at /data
        if not super()._setup_database_storage(workload):
            return False

        # Create clickhouse subdirectory under /data
        clickhouse_dir = "/data/clickhouse"
        self.record_setup_command(
            f"sudo mkdir -p {clickhouse_dir}",
            "Create ClickHouse data directory under /data",
            "storage_setup",
        )
        self.execute_command(
            f"sudo mkdir -p {clickhouse_dir}", record=True, category="storage_setup"
        )
        self._set_ownership(clickhouse_dir, owner="clickhouse:clickhouse")

        # Update data_dir to point to clickhouse subdirectory
        self.data_dir = Path(clickhouse_dir)

        self.record_setup_note(f"ClickHouse data directory: {clickhouse_dir}")
        self._log(f"    ClickHouse data directory configured: {clickhouse_dir}")

        return True

    @exclude_from_package
    def _setup_directory_storage(self, workload: Workload) -> bool:
        """
        Override to use clickhouse user ownership instead of ubuntu.

        Returns:
            True if successful, False otherwise
        """
        # Use configured data_dir or default
        if not self.data_dir:
            self.data_dir = Path(
                self.setup_config.get("data_dir", "/var/lib/clickhouse")
            )

        # Only create if non-default directory
        if str(self.data_dir) != "/var/lib/clickhouse":
            self.record_setup_command(
                f"sudo mkdir -p {self.data_dir}",
                f"Create ClickHouse data directory: {self.data_dir}",
                "storage_setup",
            )
            result = self.execute_command(
                f"sudo mkdir -p {self.data_dir}",
                record=True,
                category="storage_setup",
            )

            if not result.get("success", False):
                self._log(f"Failed to create data directory {self.data_dir}")
                return False

            # Set ownership to clickhouse user
            self._set_ownership(str(self.data_dir), owner="clickhouse:clickhouse")

            self.record_setup_note(f"✓ Data directory created: {self.data_dir}")
            self._log(f"✓ Directory storage setup complete: {self.data_dir}")

        return True

    @exclude_from_package
    def _update_credentials_from_config(self) -> None:
        """Update ClickHouse credentials from config after cloud manager is set."""
        password = self.setup_config.get("password")
        if password is not None:  # Allow empty string password
            self.password = password

    def _should_execute_remotely(self) -> bool:
        """ClickHouse only executes remotely for native installations."""
        return (
            self._cloud_instance_manager is not None and self.setup_method == "native"
        )

    def _verify_preinstalled(self) -> bool:
        """Verify that ClickHouse is already installed and accessible."""
        return self.is_healthy()

    def start(self) -> bool:
        """Start the ClickHouse system."""
        if self.setup_method == "docker":
            result = self.execute_command(f"docker start {self.container_name}")
            if result["success"]:
                return self.wait_for_health()
            return False
        else:
            result = self.execute_command("sudo systemctl start clickhouse-server")
            return bool(result.get("success", False)) and self.wait_for_health()

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if ClickHouse is running and accepting connections."""
        try:
            health_check_host = self._get_health_check_host()

            if clickhouse_connect is None:
                self._log(
                    "Warning: clickhouse-connect not available, falling back to curl/client"
                )
                if self.setup_method == "docker":
                    result = self.execute_command(
                        f"curl -s http://localhost:{self.http_port}/ --max-time 5",
                        timeout=10.0,
                    )
                    return (
                        bool(result.get("success", False)) and "Ok." in result["stdout"]
                    )
                else:
                    result = self.execute_command(
                        f"clickhouse-client --user={self.username} --password={self.password} --query 'SELECT 1' --format TSV",
                        timeout=10.0,
                    )
                    return (
                        bool(result.get("success", False)) and "1" in result["stdout"]
                    )

            # Use clickhouse-connect for connection test
            client = clickhouse_connect.get_client(
                host=health_check_host,
                port=self.port,
                username=self.username,
                password=self.password,
                database="default",  # use default for health check
                interface="http",
                secure=False,
            )

            # Test connection with simple query
            result = client.query("SELECT 1")
            client.close()
            return True

        except Exception as e:
            if not quiet:
                import traceback

                self._log(f"Health check failed: {type(e).__name__}: {e}")
                self._log(f"Full traceback:\n{traceback.format_exc()}")
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a database in ClickHouse."""
        original_database = self.database
        self.database = "default"
        try:
            sql = f"CREATE DATABASE IF NOT EXISTS {schema_name}"
            result = self.execute_query(
                sql, query_name=f"create_database_{schema_name}"
            )
            success = bool(result.get("success", False))

            # Update current database context after successful creation
            if success:
                self.database = schema_name
                self._log(f"✓ Using database: {schema_name}")
            else:
                # Print the actual error to help with debugging
                error = result.get("error", "Unknown error")
                self._log(f"✗ Failed to create database '{schema_name}': {error}")
        except Exception as e:
            # Restore original database on exception
            self.database = original_database
            self._log(f"✗ Failed to create database '{schema_name}': {e}")
            return False
        return success

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into ClickHouse table using native clickhouse-client for optimal performance."""
        schema_name = kwargs.get("schema", "default")

        try:
            self._log(f"Loading {data_path} into {table_name}...")

            # Use native clickhouse-client for bulk loading
            # TPC-H .tbl files have trailing pipe delimiter - remove it with sed
            # ClickHouse will handle date parsing natively (much faster than Python)
            # Using FORMAT CSV with custom delimiter for pipe-delimited files

            # Build the import command with authentication
            # sed removes trailing pipe from each line, then pipe to clickhouse-client
            import_cmd = (
                f"sed 's/|$//' {data_path} | "
                f"clickhouse-client "
                f"--user={self.username} "
                f"--password={self.password} "
                f'--query="INSERT INTO {schema_name}.{table_name} FORMAT CSV" '
                f"--format_csv_delimiter='|'"
            )

            # Execute the import
            result = self.execute_command(import_cmd, timeout=3600.0, record=False)

            if not result.get("success", False):
                self._log(
                    f"Failed to load data: {result.get('stderr', 'Unknown error')}"
                )
                return False

            # Verify data was loaded by counting rows
            if clickhouse_connect is None:
                # Use clickhouse-client for verification if connect not available
                count_cmd = (
                    f"clickhouse-client "
                    f"--user={self.username} "
                    f"--password={self.password} "
                    f'--query="SELECT COUNT(*) FROM {schema_name}.{table_name} FORMAT TSV"'
                )
                count_result = self.execute_command(
                    count_cmd, timeout=60.0, record=False
                )
                if count_result.get("success", False):
                    row_count = int(count_result.get("stdout", "0").strip())
                else:
                    self._log("Warning: Could not verify row count")
                    return True  # Assume success if import succeeded
            else:
                # Use clickhouse-connect for verification
                client = self._get_client()
                if client:
                    count_result = client.query(
                        f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
                    )
                    row_count = count_result.result_rows[0][0]
                else:
                    self._log("Warning: Could not verify row count")
                    return True  # Assume success if import succeeded

            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False

    def load_data_from_iterable(
        self, table_name: str, data_source: Iterable[Any], **kwargs: Any
    ) -> bool:
        raise NotImplementedError("clickhouse.load_data_from_iterable")

    def load_data_from_url(
        self,
        schema_name: str,
        table_name: str,
        data_url: str | list[str],
        /,
        extension: str = ".csv",
        **kwargs: Any,
    ) -> bool:
        if isinstance(data_url, list):
            raise NotImplementedError("Loading multiple URLs into clickhouse")

        try:
            self._log(f"Loading {data_url} into {table_name}...")

            import_query: str = (
                f"INSERT INTO {schema_name}.{table_name} SELECT * FROM url('{data_url}', CSV)"
            )

            if clickhouse_connect:
                # Use clickhouse-connect for verification
                client = self._get_client()
                if not client:
                    self._log("Error: failed to connect to clickhouse system")
                    return False

                import_res = client.query(import_query)
                self._log(f"{import_res}")
                count_result = client.query(
                    f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
                )
                row_count = count_result.result_rows[0][0]

            else:
                import_cmd = (
                    f"clickhouse-client "
                    f"--user={self.username} "
                    f"--password={self.password} "
                    f"--query='{import_query}'"
                )

                # Execute the import
                result = self.execute_command(import_cmd, timeout=3600.0, record=False)

                if not result.get("success", False):
                    self._log(
                        f"Failed to load data: {result.get('stderr', 'Unknown error')}"
                    )
                    return False

                # Verify data was loaded by counting rows
                count_cmd = (
                    f"clickhouse-client "
                    f"--user={self.username} "
                    f"--password={self.password} "
                    f'--query="SELECT COUNT(*) FROM {schema_name}.{table_name} FORMAT TSV"'
                )
                count_result = self.execute_command(
                    count_cmd, timeout=60.0, record=False
                )
                if count_result.get("success", False):
                    row_count = int(count_result.get("stdout", "0").strip())
                else:
                    self._log("Warning: Could not verify row count")
                    return True  # Assume success if import succeeded

            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False

    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a SQL query in ClickHouse using clickhouse-connect.

        Args:
            query: SQL query to execute
            query_name: Optional name for the query (for logging)
            return_data: If True, return query results as DataFrame
            timeout: Optional timeout in seconds (default: 300 for regular queries,
                    uses dynamic calculation for OPTIMIZE operations)
        """
        from ..debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        # ClickHouse HTTP interface doesn't allow trailing semicolons
        query = query.rstrip().rstrip(";")

        # Determine timeout - use provided value or calculate based on query type
        if timeout is None:
            timeout = 300  # Default 5 minutes

        # Convert timeout to milliseconds for clickhouse-connect
        send_receive_timeout = timeout

        try:
            # Debug output
            debug_print(f"Executing query: {query_name}")
            if len(query) > 200:
                debug_print(f"SQL: {query[:200]}...")
            else:
                debug_print(f"SQL: {query}")

            with Timer(f"Query {query_name}") as timer:
                if clickhouse_connect is None:
                    self._log(
                        "Warning: clickhouse-connect not available, falling back to client"
                    )
                    return self._execute_query_fallback(
                        query, query_name, timer, return_data
                    )

                # Use clickhouse-connect for query execution
                client = clickhouse_connect.get_client(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    database=self.database,
                    interface="http",
                    secure=False,
                    send_receive_timeout=send_receive_timeout,
                )

                try:
                    # Strip SQL comments from the beginning to detect query type
                    query_stripped = query.strip()
                    while query_stripped.startswith("--"):
                        # Remove comment line
                        newline_pos = query_stripped.find("\n")
                        if newline_pos == -1:
                            query_stripped = ""
                            break
                        query_stripped = query_stripped[newline_pos + 1 :].strip()

                    # Execute the query - check stripped version for query type detection
                    if query_stripped.upper().startswith(
                        ("SELECT", "WITH", "SHOW", "DESCRIBE")
                    ):
                        # For SELECT queries, fetch results
                        result = client.query(query)
                        rows_returned = (
                            result.row_count
                            if hasattr(result, "row_count")
                            else len(result.result_rows)
                        )

                        # Convert to DataFrame if requested
                        if return_data:
                            import pandas as pd

                            # clickhouse-connect result has result_rows and column_names
                            df = pd.DataFrame(
                                result.result_rows, columns=result.column_names
                            )
                        else:
                            df = None
                    else:
                        # For DDL/DML queries, just execute
                        client.command(query)
                        rows_returned = 0  # DDL/DML don't return row counts in same way
                        df = None

                    response: dict[str, Any] = {
                        "success": True,
                        "elapsed_s": timer.elapsed,
                        "rows_returned": rows_returned,
                        "query_name": query_name,
                        "error": None,
                    }

                    if return_data and df is not None:
                        response["data"] = df

                    return response

                finally:
                    client.close()

        except Exception as e:
            return {
                "success": False,
                "elapsed_s": timer.elapsed if "timer" in locals() else 0,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def _execute_query_fallback(
        self, query: str, query_name: str, timer: Any, return_data: bool = False
    ) -> dict[str, Any]:
        """Fallback query execution using clickhouse-client when clickhouse-connect is not available."""
        if return_data:
            self._log(
                "Warning: return_data not supported in fallback mode, data will not be returned"
            )

        try:
            if self.setup_method == "docker":
                cmd = (
                    f"docker exec {self.container_name} clickhouse-client "
                    f"--user={self.username} --password={self.password} "
                    f"--database={self.database} "
                    f"--query='{query}' --format=TabSeparated"
                )
            else:
                cmd = (
                    f"clickhouse-client "
                    f"--user={self.username} --password={self.password} "
                    f"--database={self.database} "
                    f"--query='{query}' --format=TabSeparated"
                )

            result = self.execute_command(cmd, timeout=3600.0)

            if result["success"]:
                rows_returned = self._count_result_rows(result["stdout"])
                return {
                    "success": True,
                    "elapsed_s": timer.elapsed,
                    "rows_returned": rows_returned,
                    "query_name": query_name,
                    "error": None,
                }
            else:
                return {
                    "success": False,
                    "elapsed_s": timer.elapsed,
                    "rows_returned": 0,
                    "query_name": query_name,
                    "error": result["stderr"],
                }

        except Exception as e:
            return {
                "success": False,
                "elapsed_s": timer.elapsed,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def _count_result_rows(self, output: str) -> int:
        """Count number of rows in query result."""
        if not output.strip():
            return 0
        return len([line for line in output.strip().split("\n") if line.strip()])

    def get_system_metrics(self) -> dict[str, Any]:
        """Get ClickHouse-specific performance metrics using clickhouse-connect."""
        metrics: dict[str, Any] = {}

        try:
            if clickhouse_connect is None:
                metrics["warning"] = "clickhouse-connect not available, limited metrics"
                return metrics

            # Query system tables for metrics
            system_queries = {
                "query_count": "SELECT count() FROM system.processes",
                "memory_usage": "SELECT formatReadableSize(sum(memory_usage)) FROM system.processes",
                "disk_usage": "SELECT formatReadableSize(sum(bytes_on_disk)) FROM system.parts",
                "cache_stats": "SELECT * FROM system.events WHERE event LIKE '%Cache%'",
            }

            for metric_name, query in system_queries.items():
                result = self.execute_query(query, query_name=f"metrics_{metric_name}")
                if result["success"]:
                    metrics[metric_name] = {
                        "query_time": result["elapsed_s"],
                        "rows": result["rows_returned"],
                    }

        except Exception as e:
            metrics["error"] = str(e)

        return metrics

    def teardown(self) -> bool:
        """Clean up ClickHouse installation."""
        success = True

        if self.setup_method == "docker":
            # Stop and remove container
            stop_result = self.execute_command(
                f"docker stop {self.container_name} || true"
            )
            remove_result = self.execute_command(
                f"docker rm {self.container_name} || true"
            )
            success = stop_result["success"] and remove_result["success"]
        else:
            # For native installation, optionally stop service
            if self.setup_config.get("stop_service_on_teardown", False):
                self.execute_command("sudo systemctl stop clickhouse-server")

        # Clean up data directory if requested
        if self.setup_config.get("cleanup_data", False):
            success = success and self.cleanup_data_directory()

        return success

    def estimate_execution_time(
        self, operation: TableOperation, data_size_gb: float
    ) -> timedelta:
        estimate: timedelta
        if operation == "OPTIMIZE TABLE":
            # Calculate timeout:
            # - Base: one minute per gb
            # - Divided by node_count (parallel processing)
            # - Minimum 5 min, maximum 2 hours
            estimate = timedelta(minutes=data_size_gb / self.node_count)

            return max(timedelta(minutes=5), min(timedelta(hours=2), estimate))
        elif operation == "MATERIALIZE STATISTICS":
            # Similar to OPTIMIZE but typically faster
            estimate = timedelta(minutes=0.5 * data_size_gb / self.node_count)
            return max(timedelta(minutes=5), min(timedelta(hours=1), estimate))

        return super().estimate_execution_time(operation, data_size_gb)
