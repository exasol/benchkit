"""ClickHouse database system implementation."""

from pathlib import Path
from typing import Any, cast

import clickhouse_connect

from ..package.markers import exclude_from_package
from ..util import Timer
from .base import SystemUnderTest


class ClickHouseSystem(SystemUnderTest):
    """ClickHouse database system implementation."""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by ClickHouse system."""
        return ["clickhouse-connect>=0.6.0"]

    @classmethod
    def extract_workload_connection_info(
        cls, setup_config: dict[str, Any], for_local_execution: bool = False
    ) -> dict[str, Any]:
        """
        Extract ClickHouse connection info with proper defaults.

        Args:
            setup_config: The setup section from system config
            for_local_execution: If True, use localhost (for packages running on DB machine).
                                If False, preserve configured host with env var resolution (for remote execution).
        """
        import os

        def resolve_env_var(value: str) -> str:
            """Resolve environment variable placeholders like $VAR_NAME."""
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]  # Remove $ prefix
                return os.environ.get(var_name, value)
            return value

        # Determine host based on execution context
        if for_local_execution:
            # Workload packages run ON the remote machine, so always use localhost
            host = "localhost"
        else:
            # For external/remote execution, resolve env vars and use configured host
            host = resolve_env_var(setup_config.get("host", "localhost"))

        # Return connection info with defaults matching __init__ (lines 71-80)
        # ClickHouse uses 'database' not 'schema'
        connection_info = {
            "host": host,
            "port": setup_config.get("port", 8123),
            "username": setup_config.get("username", "default"),
            "password": setup_config.get("password", ""),
            "database": setup_config.get(
                "database", "benchmark"
            ),  # Default to benchmark for workload compatibility
        }

        # Preserve use_additional_disk setting for data generation on remote instances
        if setup_config.get("use_additional_disk", False):
            connection_info["use_additional_disk"] = True

        # Preserve extra configuration (includes settings like allow_statistics_optimize)
        # This is needed for conditional features in workload setup scripts
        if "extra" in setup_config:
            connection_info["extra"] = setup_config["extra"]

        return connection_info

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

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.setup_method = self.setup_config.get("method", "docker")
        self.container_name = f"clickhouse_{self.name}"
        self.config_profile = self.setup_config.get("extra", {}).get(
            "config_profile", "default"
        )
        self.http_port = 8123
        self.native_port = 9000

        # Connection settings - resolve host IP addresses from config or infrastructure
        raw_host = self.setup_config.get("host", "localhost")
        self.host = self._resolve_ip_addresses(raw_host)
        self.port = self.setup_config.get(
            "port", 8123
        )  # HTTP port for clickhouse-connect
        self.username = self.setup_config.get("username", "default")
        self.password = self.setup_config.get("password", "")
        # Use 'benchmark' as default database for workload compatibility
        self.database = self.setup_config.get("database", "benchmark")

        self._client = None
        self._cloud_instance_manager: Any = None
        self._external_host: str | None = (
            None  # Initialize for cloud instance external IP
        )

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
                print("No existing ClickHouse installation marker found")
                return False

            print("Found existing ClickHouse installation marker")

            # Level 2: Check if clickhouse-server binary is available
            binary_check = self.execute_command("which clickhouse-server", record=False)
            if not binary_check.get("success", False):
                print(
                    "⚠ Installation marker found but clickhouse-server not available, will reinstall"
                )
                return False

            print("✓ clickhouse-server binary available")

            # Level 3: Check if service is running
            service_check = self.execute_command(
                "systemctl is-active clickhouse-server", record=False
            )
            if not service_check.get("success", False):
                print("⚠ clickhouse-server service not running, will restart")
                return False

            print("✓ clickhouse-server service is active")

            # Level 4: Most importantly - check if database is accessible
            print("Checking if ClickHouse database is accessible...")
            if self.is_healthy(quiet=False):
                print("✓ ClickHouse database is accessible and healthy")
                return True
            else:
                print(
                    "⚠ ClickHouse installation exists but database not accessible, will restart"
                )
                return False

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
    def install(self) -> bool:
        """Install ClickHouse using the configured method."""
        self.prepare_data_directory()

        if self.setup_method == "docker":
            return self._install_docker()
        elif self.setup_method == "native":
            return self._install_native()
        elif self.setup_method == "preinstalled":
            return self._verify_preinstalled()
        else:
            print(f"Unknown setup method: {self.setup_method}")
            return False

    @exclude_from_package
    def _install_docker(self) -> bool:
        """Install ClickHouse using Docker."""
        # Record setup notes
        self.record_setup_note("Installing ClickHouse using Docker container")

        # Create data directory first
        self.record_setup_command(
            f"sudo mkdir -p {self.data_dir}",
            "Create ClickHouse data directory",
            "preparation",
        )
        self.record_setup_command(
            f"sudo chown $(whoami):$(whoami) {self.data_dir}",
            "Set data directory permissions",
            "preparation",
        )

        # Remove existing container if it exists
        self.execute_command(f"docker rm -f {self.container_name} || true", record=True)

        # Prepare Docker command
        docker_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            self.container_name,
            "-v",
            f"{self.data_dir}:/var/lib/clickhouse",
            "-p",
            f"{self.http_port}:8123",
            "-p",
            f"{self.native_port}:9000",
        ]

        # Add memory limits for consistent benchmarking
        memory_limit = self.setup_config.get("extra", {}).get("memory_limit", "32g")
        docker_cmd.extend(["--memory", memory_limit])

        # Use specified Docker image version
        image_tag = self.version if self.version != "latest" else "latest"
        docker_cmd.append(f"clickhouse/clickhouse-server:{image_tag}")

        # Record and execute the docker run command
        full_cmd = " ".join(docker_cmd)
        result = self.execute_command(full_cmd)
        if not result["success"]:
            print(f"Failed to start ClickHouse container: {result['stderr']}")
            return False

        # Record configuration applied
        extra_config = self.setup_config.get("extra", {})
        if extra_config:
            self.record_setup_note("ClickHouse configuration applied:")
            for key, value in extra_config.items():
                self.record_setup_note(f"  {key}: {value}")

        # Wait for container to be ready
        print("Waiting for ClickHouse to start...")
        return self.wait_for_health(max_attempts=30, delay=2.0)

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install ClickHouse using official APT repository."""
        self.record_setup_note("Installing ClickHouse using official APT repository")

        # Resolve IP addresses from configuration
        resolved_host = self._resolve_ip_addresses(
            self.setup_config.get("host", "localhost")
        )

        try:
            # Step 1: Install prerequisite packages
            self.record_setup_command(
                "sudo apt-get update", "Update package lists", "prerequisites"
            )
            result = self.execute_command("sudo apt-get update")
            if not result["success"]:
                print(f"Failed to update package lists: {result['stderr']}")
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
                print(f"Failed to install prerequisites: {result['stderr']}")
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
                print(f"Failed to add ClickHouse GPG key: {result['stderr']}")
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
                print(f"Failed to add ClickHouse repository: {result['stderr']}")
                return False

            # Step 4: Update package lists with new repository
            self.record_setup_command(
                "sudo apt-get update",
                "Update package lists with ClickHouse repository",
                "repository_setup",
            )
            result = self.execute_command("sudo apt-get update")
            if not result["success"]:
                print(
                    f"Failed to update package lists after adding repository: {result['stderr']}"
                )
                return False

            # Step 5: Install ClickHouse packages (non-interactive)
            # Set DEBIAN_FRONTEND to noninteractive to avoid password prompts
            install_env = "DEBIAN_FRONTEND=noninteractive"

            if self.version and self.version != "latest":
                # Try to install specific version first
                version_suffix = f"={self.version}"
                install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-server{version_suffix} clickhouse-client{version_suffix}"
                description = (
                    f"Install ClickHouse server and client version {self.version}"
                )
                print(f"Attempting to install ClickHouse {self.version}...")

                self.record_setup_command(
                    f"sudo apt-get install -y clickhouse-server{version_suffix} clickhouse-client{version_suffix}",
                    description,
                    "installation",
                )
                result = self.execute_command(
                    install_cmd, timeout=300
                )  # 5 min timeout for installation

                if not result["success"]:
                    print(
                        f"Version {self.version} not available, falling back to latest..."
                    )
                    # Fallback to latest version
                    install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-server clickhouse-client"
                    description = (
                        "Install latest ClickHouse server and client (fallback)"
                    )

                    self.record_setup_command(
                        "sudo apt-get install -y clickhouse-server clickhouse-client",
                        description,
                        "installation",
                    )
                    result = self.execute_command(install_cmd, timeout=300)

                    if not result["success"]:
                        print(
                            f"Failed to install ClickHouse (even latest): {result['stderr']}"
                        )
                        return False
                    else:
                        print("✓ Successfully installed latest ClickHouse version")
                else:
                    print(f"✓ Successfully installed ClickHouse {self.version}")
            else:
                # Install latest version
                install_cmd = f"{install_env} sudo -E apt-get install -y clickhouse-server clickhouse-client"
                description = "Install latest ClickHouse server and client"
                print("Installing latest ClickHouse version...")

                self.record_setup_command(
                    "sudo apt-get install -y clickhouse-server clickhouse-client",
                    description,
                    "installation",
                )
                result = self.execute_command(install_cmd, timeout=300)

                if not result["success"]:
                    print(f"Failed to install ClickHouse: {result['stderr']}")
                    return False
                else:
                    print("✓ Successfully installed ClickHouse")

            # Step 6: Detect hardware specs for optimal configuration
            print("📊 Detecting hardware specifications...")
            hw_specs = self._detect_hardware_specs()
            cpu_cores = hw_specs["cpu_cores"]
            total_mem_gb = hw_specs["total_memory_bytes"] / (1024**3)
            print(f"✓ Detected: {cpu_cores} CPU cores, {total_mem_gb:.1f}GB RAM")

            # Step 7: Calculate optimal settings based on hardware
            extra_config = self.setup_config.get("extra", {})
            settings = self._calculate_optimal_settings(hw_specs, extra_config)
            print("⚙️  Calculated optimal settings:")
            print(f"   - max_threads: {settings['max_threads']}")
            print(
                f"   - max_memory_usage: {settings['max_memory_usage'] / 1e9:.1f}GB (per query)"
            )
            print(
                f"   - max_server_memory_usage: {settings['max_server_memory_usage'] / 1e9:.1f}GB (total)"
            )
            print(f"   - max_concurrent_queries: {settings['max_concurrent_queries']}")

            # Step 8: Configure ClickHouse server (server-level settings)
            self._configure_clickhouse_server(settings)

            # Step 9: Configure user profile (query-level settings + password)
            if self.password:
                self._configure_user_profile(settings)

            # Step 10: Start and enable ClickHouse service
            self.record_setup_command(
                "sudo systemctl start clickhouse-server",
                "Start ClickHouse server service",
                "service_management",
            )
            result = self.execute_command("sudo systemctl start clickhouse-server")
            if not result["success"]:
                print(f"Failed to start ClickHouse service: {result['stderr']}")
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
            print("Waiting for ClickHouse server to be ready...")
            if not self.wait_for_health(max_attempts=30, delay=2.0):
                print("ClickHouse server failed to become ready within timeout")
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
            print("✓ ClickHouse installation completed successfully")

            return True

        except Exception as e:
            print(f"Native ClickHouse installation failed: {e}")
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
                print(
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
        extra_config = self.setup_config.get("extra", {})
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
            print(
                f"Warning: Failed to configure user profile: {result.get('stderr', 'Unknown error')}"
            )
        else:
            self.record_setup_note(
                "ClickHouse user profile configured with optimized settings"
            )

    @exclude_from_package
    def _parse_memory_size(self, memory_str: str) -> int:
        """Parse memory size string like '32g', '1024m' to bytes."""
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

    @exclude_from_package
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

    @exclude_from_package
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
                extra_config, "max_concurrent_queries", max(4, cpu_cores // 2)
            ),
            "background_pool_size": self._get_int_config(
                extra_config, "background_pool_size", cpu_cores
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
    def _setup_database_storage(self, scale_factor: int) -> bool:
        """
        Override base class to setup ClickHouse storage on additional disk.

        ClickHouse uses a subdirectory under /data for its data.
        The base class mounts the disk/RAID at /data.

        Returns:
            True if successful, False otherwise
        """
        # Check if /data is already mounted
        check_mount = self.execute_command("mount | grep '/data'", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            print("Storage already mounted at /data, creating ClickHouse subdirectory")
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
        if not super()._setup_database_storage(scale_factor):
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
        print(f"ClickHouse data directory configured: {clickhouse_dir}")

        return True

    @exclude_from_package
    def _setup_directory_storage(self, scale_factor: int) -> bool:
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
                print(f"Failed to create data directory {self.data_dir}")
                return False

            # Set ownership to clickhouse user
            self._set_ownership(str(self.data_dir), owner="clickhouse:clickhouse")

            self.record_setup_note(f"✓ Data directory created: {self.data_dir}")
            print(f"✓ Directory storage setup complete: {self.data_dir}")

        return True

    def get_data_generation_directory(self, workload: Any) -> Path | None:
        """
        Get directory for TPC-H data generation on additional disk.

        Returns:
            Path to data generation directory on additional disk, or None for default
        """
        use_additional_disk = self.setup_config.get("use_additional_disk", False)

        if use_additional_disk:
            # Use shared /data/tpch_gen for TPC-H data generation (same as Exasol)
            tpch_gen_dir = "/data/tpch_gen"

            # Create directory with proper ownership
            self.execute_command(
                f"sudo mkdir -p {tpch_gen_dir} && sudo chown -R $(whoami):$(whoami) {tpch_gen_dir}",
                record=False,
            )

            data_gen_dir = (
                Path(tpch_gen_dir) / workload.name / f"sf{workload.scale_factor}"
            )
            print(
                f"ClickHouse: Using additional disk for data generation: {data_gen_dir}"
            )
            return cast(Path, data_gen_dir)

        # Use default local path
        return None

    def set_cloud_instance_manager(self, instance_manager: Any) -> None:
        """Set cloud instance manager for remote execution."""
        self._cloud_instance_manager = instance_manager

        # Set external host for health checks from local machine
        # This is critical for pre-existing installations where install() doesn't run
        if instance_manager and hasattr(instance_manager, "public_ip"):
            self._external_host = instance_manager.public_ip
            # Keep self.host as localhost for remote execution
            self.host = "localhost"

            # For preinstalled systems, ensure we have the correct password from config
            # (ClickHouse uses setup_config password directly)
            password = self.setup_config.get("password")
            if password is not None:  # Allow empty string password
                self.password = password

    def execute_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
    ) -> dict[str, Any]:
        """Execute command with remote execution support if cloud instance manager is available."""
        if self._cloud_instance_manager and self.setup_method == "native":
            # Execute on remote instance
            result = self._cloud_instance_manager.run_remote_command(
                command, timeout=int(timeout) if timeout else 300
            )

            # Record command for report reproduction if requested
            if record:
                self.setup_commands.append(
                    {
                        "command": self._sanitize_command_for_report(command),
                        "success": result.get("success", False),
                        "description": f"Execute {command.split()[0]} command on remote system",
                        "category": category,
                    }
                )

            return dict(result)
        else:
            return super().execute_command(command, timeout, record, category)

    def _resolve_ip_addresses(self, ip_config: str) -> str:
        """Resolve IP address placeholders with actual values from infrastructure."""
        if not ip_config:
            return "localhost"

        # Handle environment variable substitution
        if ip_config.startswith("$"):
            from typing import cast

            from benchkit.infra.manager import InfraManager

            env_var = ip_config[1:]  # Remove $ prefix
            resolved = InfraManager.resolve_ip_from_infrastructure(env_var, self.name)

            if resolved:
                return cast(str, resolved)
            else:
                return ip_config

        # If it's already an IP address, return as-is
        return ip_config

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
            # Determine health check host with priority:
            # 1. _external_host if explicitly set
            # 2. public_ip from cloud instance manager if available
            # 3. self.host as final fallback
            health_check_host = getattr(self, "_external_host", None)

            if not health_check_host and self._cloud_instance_manager:
                health_check_host = getattr(
                    self._cloud_instance_manager, "public_ip", None
                )

            if not health_check_host:
                health_check_host = self.host

            if clickhouse_connect is None:
                print(
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

                print(f"Health check failed: {type(e).__name__}: {e}")
                print(f"Full traceback:\n{traceback.format_exc()}")
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
                print(f"✓ Using database: {schema_name}")
            else:
                # Print the actual error to help with debugging
                error = result.get("error", "Unknown error")
                print(f"✗ Failed to create database '{schema_name}': {error}")
        except Exception as e:
            # Restore original database on exception
            self.database = original_database
            print(f"✗ Failed to create database '{schema_name}': {e}")
            return False
        return success

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into ClickHouse table using native clickhouse-client for optimal performance."""
        schema_name = kwargs.get("schema", "default")

        try:
            print(f"Loading {data_path} into {table_name}...")

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
                print(f"Failed to load data: {result.get('stderr', 'Unknown error')}")
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
                    print("Warning: Could not verify row count")
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
                    print("Warning: Could not verify row count")
                    return True  # Assume success if import succeeded

            print(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            print(f"Failed to load data into {table_name}: {e}")
            return False

    def execute_query(
        self, query: str, query_name: str | None = None, return_data: bool = False
    ) -> dict[str, Any]:
        """Execute a SQL query in ClickHouse using clickhouse-connect."""
        from ..debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        # ClickHouse HTTP interface doesn't allow trailing semicolons
        query = query.rstrip().rstrip(";")

        try:
            # Debug output
            debug_print(f"Executing query: {query_name}")
            if len(query) > 200:
                debug_print(f"SQL: {query[:200]}...")
            else:
                debug_print(f"SQL: {query}")

            with Timer(f"Query {query_name}") as timer:
                if clickhouse_connect is None:
                    print(
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
            print(
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

    def get_version_info(self) -> dict[str, str]:
        """Get detailed version information using clickhouse-connect."""
        version_info = {"configured_version": self.version}

        try:
            result = self.execute_query("SELECT version()", query_name="get_version")
            if result["success"]:
                version_info["actual_version"] = (
                    "version_retrieved_via_clickhouse_connect"
                )

            # Also get clickhouse-connect version info
            if clickhouse_connect is not None:
                version_info["clickhouse_connect_available"] = "yes"
                version_info["clickhouse_connect_version"] = getattr(
                    clickhouse_connect, "__version__", "unknown"
                )
            else:
                version_info["clickhouse_connect_available"] = "no"

        except Exception as e:
            version_info["version_error"] = str(e)

        return version_info
