"""Trino database system implementation."""

import uuid
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from benchkit.common import DataFormat, exclude_from_package

from ..util import Timer
from .base import SystemUnderTest

if TYPE_CHECKING:
    from ..workloads import Workload


class TrinoSystem(SystemUnderTest):
    """Trino database system implementation."""

    # Trino supports multinode clusters (coordinator + workers)
    SUPPORTS_MULTINODE = True

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by Trino system."""
        return ["trino>=0.336.0"]

    @classmethod
    def extract_workload_connection_info(
        cls, setup_config: dict[str, Any], for_local_execution: bool = False
    ) -> dict[str, Any]:
        """
        Extract Trino connection info with proper defaults.

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

        # Return connection info with defaults matching __init__
        connection_info = {
            "host": host,
            "port": setup_config.get("port", 8080),
            "username": setup_config.get("username", "admin"),
            "catalog": setup_config.get("catalog", "hive"),
            "schema": setup_config.get("schema", "tpch"),
        }

        # Preserve use_additional_disk setting for data generation on remote instances
        if setup_config.get("use_additional_disk", False):
            connection_info["use_additional_disk"] = True

        return connection_info

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """Return ports required by Trino system."""
        return {
            "Trino HTTP": 8080,
            "Trino HTTPS": 8443,
            "Hive Metastore": 9083,
        }

    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """Get Trino connection string with full CLI command."""
        port = self.setup_config.get("port", 8080)
        catalog = self.setup_config.get("catalog", "hive")
        schema = self.setup_config.get("schema", "tpch")
        return f"trino --server http://{public_ip}:{port} --catalog {catalog} --schema {schema}"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.setup_method = self.setup_config.get("method", "native")

        # Connection settings
        self.host = self.setup_config.get("host", "localhost")
        self.port = self.setup_config.get("port", 8080)
        self.username = self.setup_config.get("username", "admin")
        self.catalog = self.setup_config.get("catalog", "hive")
        self.schema = self.setup_config.get("schema", "tpch")

        # Installation paths
        self.trino_home = "/opt/trino-server"
        self.hive_metastore_home = "/opt/hive-metastore"
        self.data_dir: Path | None = Path("/data/trino")
        self.hive_data_dir = Path("/data/trino/hive-data")

        self._client = None
        self._cloud_instance_manager: Any = None  # Primary node (node 0)
        self._cloud_instance_managers: list[Any] = []  # All nodes for multinode
        self._external_host: str | None = None  # For cloud instance external IP

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """Check if Trino is already installed and running."""
        # Level 1: Check for installation marker
        if not self.has_install_marker():
            print("No existing Trino installation marker found")
            return False

        print("Found existing Trino installation marker")

        # Level 2: Check if Trino directory exists
        dir_check = self.execute_command(
            f"test -d {self.trino_home} && echo 'exists'", record=False
        )
        if not (
            dir_check.get("success", False) and "exists" in dir_check.get("stdout", "")
        ):
            print(
                "⚠ Installation marker found but Trino directory not found, will reinstall"
            )
            return False

        print(f"✓ Trino directory exists: {self.trino_home}")

        # Level 3: Check if service is running
        service_check = self.execute_command("systemctl is-active trino", record=False)
        if not service_check.get("success", False):
            print("⚠ Trino service not running, will restart")
            return False

        print("✓ Trino service is active")

        # Level 4: Check if database is accessible
        print("Checking if Trino database is accessible...")
        if self.is_healthy(quiet=False):
            print("✓ Trino database is accessible and healthy")
            return True
        else:
            print(
                "⚠ Trino installation exists but database not accessible, will restart"
            )
            return False

    def _get_connection(self) -> Any:
        """Get a connection to Trino database using Python client."""
        try:
            import trino  # type: ignore[import-not-found]
        except ImportError:
            print("Warning: trino package not available")
            return None

        return trino.dbapi.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            catalog=self.catalog,
            schema=self.schema,
        )

    @exclude_from_package
    def install(self) -> bool:
        """Install Trino using the configured method."""
        self.prepare_data_directory()

        if self.setup_method == "docker":
            print(
                "Docker installation is not supported for Trino. "
                "Please use 'native' or 'preinstalled' method instead."
            )
            return False
        elif self.setup_method == "native":
            return self._install_native()
        elif self.setup_method == "preinstalled":
            return self._verify_preinstalled()
        else:
            print(f"Unknown setup method: {self.setup_method}")
            return False

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install Trino natively - handles both single and multinode."""
        is_multinode = (
            self._cloud_instance_managers and len(self._cloud_instance_managers) > 1
        )

        if is_multinode:
            print(
                f"Installing Trino multinode cluster ({len(self._cloud_instance_managers)} nodes)..."
            )
            return self._install_multinode_cluster()
        else:
            print("Installing Trino single-node...")
            return self._install_single_node()

    @exclude_from_package
    def _install_single_node(self) -> bool:
        """Install Trino on single node (coordinator only)."""
        self.record_setup_note("Installing Trino single-node (coordinator only)")

        try:
            # Step 1: Install Java 17+
            if not self._install_java():
                return False

            # Step 2: Download and install Trino
            if not self._download_and_install_trino():
                return False

            # Step 3: Setup Hive Metastore
            if not self._setup_hive_metastore():
                return False

            # Step 4: Configure Trino as coordinator
            coordinator_ip = "localhost"
            self._configure_node_properties()
            self._configure_jvm_settings()
            self._configure_config_properties(
                is_coordinator=True,
                coordinator_ip=coordinator_ip,
                include_coordinator_worker=True,
            )
            self._configure_hive_catalog()

            # Step 5: Create systemd service
            self._create_systemd_service()

            # Step 6: Start Trino
            self.record_setup_command(
                "sudo systemctl start trino",
                "Start Trino server service",
                "service_management",
            )
            result = self.execute_command("sudo systemctl start trino")
            if not result["success"]:
                print(
                    f"Failed to start Trino service: {result.get('stderr', 'Unknown error')}"
                )
                return False

            self.record_setup_command(
                "sudo systemctl enable trino",
                "Enable Trino server to start on boot",
                "service_management",
            )
            self.execute_command("sudo systemctl enable trino")

            # Step 7: Wait for health
            self.record_setup_note("Waiting for Trino to be ready for connections...")
            print("Waiting for Trino to be ready...")
            if not self.wait_for_health(max_attempts=60, delay=5.0):
                print("Trino failed to become ready within timeout")
                return False

            self.record_setup_note("✓ Trino is ready and accepting connections")

            # Update connection parameters
            if self._cloud_instance_manager:
                self._external_host = self._cloud_instance_manager.public_ip
                self.host = "localhost"
            else:
                self.host = "localhost"

            # Mark installed
            self.mark_installed(record=False)
            print("✓ Trino installation completed successfully")

            return True

        except Exception as e:
            print(f"Trino installation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    @exclude_from_package
    def _install_multinode_cluster(self) -> bool:
        """Install Trino cluster with coordinator and workers."""
        self.record_setup_note(
            f"Installing Trino multinode cluster ({len(self._cloud_instance_managers)} nodes)"
        )

        coordinator_ip = self._cloud_instance_managers[0].private_ip
        print(f"Coordinator will be at: {coordinator_ip}")

        # Step 1: Install Trino on ALL nodes
        print(
            f"\nInstalling Trino on all {len(self._cloud_instance_managers)} nodes..."
        )
        original_commands_count = len(self.setup_commands)

        for idx, mgr in enumerate(self._cloud_instance_managers):
            role = "Coordinator" if idx == 0 else "Worker"
            print(f"\n[Node {idx} - {role}] Installing Trino...")

            # Temporarily switch to this node
            original_mgr = self._cloud_instance_manager
            self._cloud_instance_manager = mgr

            # Disable command recording for nodes after first
            if idx > 0:
                commands_before = len(self.setup_commands)

            try:
                # Install base packages (same on all nodes)
                if not self._install_java():
                    print(f"[Node {idx}] ✗ Java installation failed")
                    return False

                if not self._download_and_install_trino():
                    print(f"[Node {idx}] ✗ Trino installation failed")
                    return False

                # Only install Hive Metastore on coordinator (node 0)
                # Workers will connect to coordinator's Hive Metastore
                is_coordinator = idx == 0
                if is_coordinator:
                    if not self._setup_hive_metastore():
                        print(f"[Node {idx}] ✗ Hive Metastore setup failed")
                        return False
                else:
                    print(f"[Node {idx}] Skipping Hive Metastore (using coordinator's)")

                # Configure based on role
                self._configure_node_properties()
                self._configure_jvm_settings()
                self._configure_config_properties(
                    is_coordinator=is_coordinator,
                    coordinator_ip=coordinator_ip,
                    include_coordinator_worker=False,  # Don't include coordinator as worker in multinode
                )
                # For workers, point to coordinator's Hive Metastore
                hive_metastore_ip = None if is_coordinator else coordinator_ip
                self._configure_hive_catalog(coordinator_ip=hive_metastore_ip)

                # Create systemd service (workers don't have local Hive Metastore)
                self._create_systemd_service(has_local_metastore=is_coordinator)

                print(f"[Node {idx} - {role}] ✓ Installation complete")

            finally:
                # Remove duplicate commands
                if idx > 0:
                    self.setup_commands = self.setup_commands[:commands_before]

                # Restore primary manager
                self._cloud_instance_manager = original_mgr

        # Add node info to all commands
        if len(self._cloud_instance_managers) > 1:
            node_info = f"all_nodes_{len(self._cloud_instance_managers)}"
            for i in range(original_commands_count, len(self.setup_commands)):
                self.setup_commands[i]["node_info"] = node_info

        # Step 2: Start all nodes
        print("\n🚀 Starting Trino cluster...")
        for idx, mgr in enumerate(self._cloud_instance_managers):
            role = "Coordinator" if idx == 0 else "Worker"
            print(f"[Node {idx} - {role}] Starting Trino...")
            result = mgr.run_remote_command(
                "sudo systemctl start trino && sudo systemctl enable trino"
            )
            if not result.get("success"):
                print(f"[Node {idx}] ✗ Failed to start Trino")
                return False
            print(f"[Node {idx}] ✓ Trino started")

        # Step 3: Wait for coordinator health
        print("\n⏳ Waiting for coordinator to be ready...")
        self._external_host = self._cloud_instance_managers[0].public_ip
        self.host = "localhost"

        if not self.wait_for_health(max_attempts=60, delay=5.0):
            print("Coordinator failed to become ready within timeout")
            return False

        print("✓ Trino cluster is ready!")
        self.record_setup_note(
            f"✓ Trino cluster ready with {len(self._cloud_instance_managers)} nodes"
        )

        # Mark installed
        self.mark_installed(record=False)

        return True

    @exclude_from_package
    def _install_java(self) -> bool:
        """Install Java 17+ (required by Trino)."""
        print("Installing Java 17...")
        self.record_setup_command(
            "sudo apt-get update && sudo apt-get install -y openjdk-17-jdk",
            "Install Java 17 (required by Trino)",
            "prerequisites",
        )

        result = self.execute_command(
            "sudo apt-get update && sudo apt-get install -y openjdk-17-jdk", timeout=300
        )

        if not result.get("success", False):
            print(f"Failed to install Java: {result.get('stderr', 'Unknown error')}")
            return False

        print("✓ Java 17 installed")
        return True

    @exclude_from_package
    def _download_and_install_trino(self) -> bool:
        """Download and install Trino server."""
        version = self.version if self.version and self.version != "latest" else "478"
        download_url = f"https://repo1.maven.org/maven2/io/trino/trino-server/{version}/trino-server-{version}.tar.gz"

        print(f"Downloading Trino {version}...")

        # Download
        self.record_setup_command(
            f"wget {download_url} -O /tmp/trino-server.tar.gz",
            f"Download Trino server version {version}",
            "installation",
        )
        result = self.execute_command(
            f"wget {download_url} -O /tmp/trino-server.tar.gz", timeout=300
        )
        if not result.get("success", False):
            print(f"Failed to download Trino: {result.get('stderr', 'Unknown error')}")
            return False

        # Extract
        self.record_setup_command(
            "sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/",
            "Extract Trino server to /opt",
            "installation",
        )
        result = self.execute_command("sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/")
        if not result.get("success", False):
            print(f"Failed to extract Trino: {result.get('stderr', 'Unknown error')}")
            return False

        # Create symlink
        self.record_setup_command(
            f"sudo ln -sf /opt/trino-server-{version} {self.trino_home}",
            f"Create symlink {self.trino_home}",
            "installation",
        )
        self.execute_command(
            f"sudo ln -sf /opt/trino-server-{version} {self.trino_home}"
        )

        # Create trino user
        self.record_setup_command(
            "sudo useradd -r -s /bin/false trino",
            "Create Trino system user",
            "user_setup",
        )
        self.execute_command("sudo useradd -r -s /bin/false trino || true")

        # Create directories
        self.record_setup_command(
            "sudo mkdir -p /var/trino/data /etc/trino /var/log/trino",
            "Create Trino directories",
            "installation",
        )
        for dir_path in ["/var/trino/data", "/etc/trino", "/var/log/trino"]:
            self.execute_command(f"sudo mkdir -p {dir_path}")
            self.execute_command(f"sudo chown -R trino:trino {dir_path}")

        print("✓ Trino server installed")
        return True

    @exclude_from_package
    def _setup_hive_metastore(self) -> bool:
        """Set up Hive Metastore for Trino."""
        print("Setting up Hive Metastore...")

        # Download Hive Standalone Metastore
        metastore_version = "3.1.3"
        download_url = f"https://repo1.maven.org/maven2/org/apache/hive/hive-standalone-metastore/{metastore_version}/hive-standalone-metastore-{metastore_version}-bin.tar.gz"

        self.record_setup_command(
            f"wget {download_url} -O /tmp/hive-metastore.tar.gz",
            f"Download Hive Standalone Metastore {metastore_version}",
            "hive_setup",
        )
        result = self.execute_command(
            f"wget {download_url} -O /tmp/hive-metastore.tar.gz", timeout=300
        )
        if not result.get("success", False):
            print(
                f"Failed to download Hive Metastore: {result.get('stderr', 'Unknown error')}"
            )
            return False

        # Extract
        self.record_setup_command(
            "sudo tar -xzf /tmp/hive-metastore.tar.gz -C /opt/",
            "Extract Hive Metastore to /opt",
            "hive_setup",
        )
        self.execute_command("sudo tar -xzf /tmp/hive-metastore.tar.gz -C /opt/")

        # Create symlink
        self.record_setup_command(
            f"sudo ln -sf /opt/apache-hive-metastore-{metastore_version}-bin {self.hive_metastore_home}",
            "Create Hive Metastore symlink",
            "hive_setup",
        )
        self.execute_command(
            f"sudo ln -sf /opt/apache-hive-metastore-{metastore_version}-bin {self.hive_metastore_home}"
        )

        # Create Hive data directory
        self.record_setup_command(
            f"sudo mkdir -p {self.hive_data_dir}",
            f"Create Hive data directory at {self.hive_data_dir}",
            "hive_setup",
        )
        self.execute_command(f"sudo mkdir -p {self.hive_data_dir}")
        self.execute_command(f"sudo chown -R trino:trino {self.hive_data_dir}")

        # Configure metastore (use embedded Derby database)
        metastore_config = f"""<?xml version="1.0"?>
<configuration>
    <property>
        <name>metastore.warehouse.dir</name>
        <value>file://{self.hive_data_dir}</value>
    </property>
    <property>
        <name>metastore.task.threads.always</name>
        <value>org.apache.hadoop.hive.metastore.events.EventCleanerTask</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionURL</name>
        <value>jdbc:derby:;databaseName=/var/trino/metastore_db;create=true</value>
    </property>
    <property>
        <name>javax.jdo.option.ConnectionDriverName</name>
        <value>org.apache.derby.jdbc.EmbeddedDriver</value>
    </property>
</configuration>"""

        self.record_setup_command(
            f"sudo tee {self.hive_metastore_home}/conf/metastore-site.xml > /dev/null",
            "Configure Hive Metastore with embedded Derby database",
            "hive_setup",
        )

        create_config_cmd = f"sudo tee {self.hive_metastore_home}/conf/metastore-site.xml > /dev/null << 'EOF'\n{metastore_config}\nEOF"
        result = self.execute_command(create_config_cmd)
        if not result.get("success", False):
            print(
                f"Failed to create Hive Metastore config: {result.get('stderr', 'Unknown error')}"
            )
            return False

        # Create metastore directory
        self.execute_command("sudo mkdir -p /var/trino")
        self.execute_command("sudo chown -R trino:trino /var/trino")

        # Initialize metastore schema
        self.record_setup_command(
            f"{self.hive_metastore_home}/bin/schematool -dbType derby -initSchema",
            "Initialize Hive Metastore schema",
            "hive_setup",
        )
        init_result = self.execute_command(
            f"sudo -u trino {self.hive_metastore_home}/bin/schematool -dbType derby -initSchema",
            timeout=120,
        )
        # Schema init may fail if already initialized, which is okay
        if not init_result.get(
            "success", False
        ) and "already exists" not in init_result.get("stderr", ""):
            print(
                f"Warning: Schema initialization had issues: {init_result.get('stderr', '')}"
            )

        # Create systemd service for metastore
        self._create_metastore_service()

        # Start metastore
        self.record_setup_command(
            "sudo systemctl start hive-metastore",
            "Start Hive Metastore service",
            "service_management",
        )
        result = self.execute_command("sudo systemctl start hive-metastore")
        if not result.get("success", False):
            print(
                f"Failed to start Hive Metastore: {result.get('stderr', 'Unknown error')}"
            )
            return False

        self.record_setup_command(
            "sudo systemctl enable hive-metastore",
            "Enable Hive Metastore to start on boot",
            "service_management",
        )
        self.execute_command("sudo systemctl enable hive-metastore")

        print("✓ Hive Metastore setup complete")
        return True

    @exclude_from_package
    def _configure_node_properties(self) -> None:
        """Configure node.properties."""
        node_id = str(uuid.uuid4())

        node_properties = f"""node.environment=production
node.id={node_id}
node.data-dir=/var/trino/data"""

        self._write_config_file(
            "/etc/trino/node.properties",
            node_properties,
            "Configure Trino node properties",
        )

    @exclude_from_package
    def _configure_jvm_settings(self) -> None:
        """Configure JVM settings based on hardware."""
        hw_specs = self._detect_hardware_specs()
        total_mem_gb = hw_specs["total_memory_bytes"] / (1024**3)

        # Allocate 80% of memory to JVM heap
        heap_size_gb = int(total_mem_gb * 0.8)

        jvm_config = f"""-server
-Xmx{heap_size_gb}G
-Xms{heap_size_gb}G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
-XX:ReservedCodeCacheSize=512M
-Djdk.attach.allowAttachSelf=true
-Djdk.nio.maxCachedBufferSize=2000000"""

        self._write_config_file(
            "/etc/trino/jvm.config",
            jvm_config,
            f"Configure JVM with {heap_size_gb}G heap (80% of {total_mem_gb:.1f}G total RAM)",
        )

    @exclude_from_package
    def _configure_config_properties(
        self,
        is_coordinator: bool,
        coordinator_ip: str,
        include_coordinator_worker: bool,
    ) -> None:
        """Configure config.properties based on node role."""
        # Get hardware specs for memory settings
        hw_specs = self._detect_hardware_specs()
        total_mem_gb = hw_specs["total_memory_bytes"] / (1024**3)

        # Calculate memory settings
        query_max_memory_gb = int(total_mem_gb * 0.8)
        query_max_memory_per_node_gb = int(total_mem_gb * 0.7)

        # Allow user overrides from extra config
        extra_config = self.setup_config.get("extra", {})
        if "query_max_memory" in extra_config:
            query_max_memory_gb = self._parse_memory_to_gb(
                extra_config["query_max_memory"]
            )
        if "query_max_memory_per_node" in extra_config:
            query_max_memory_per_node_gb = self._parse_memory_to_gb(
                extra_config["query_max_memory_per_node"]
            )

        if is_coordinator:
            config = f"""coordinator=true
node-scheduler.include-coordinator={str(include_coordinator_worker).lower()}
http-server.http.port=8080
discovery.uri=http://{coordinator_ip}:8080
query.max-memory={query_max_memory_gb}GB
query.max-memory-per-node={query_max_memory_per_node_gb}GB
query.max-total-memory-per-node={query_max_memory_per_node_gb}GB"""
        else:
            config = f"""coordinator=false
http-server.http.port=8080
discovery.uri=http://{coordinator_ip}:8080
query.max-memory-per-node={query_max_memory_per_node_gb}GB
query.max-total-memory-per-node={query_max_memory_per_node_gb}GB"""

        role = "coordinator" if is_coordinator else "worker"
        self._write_config_file(
            "/etc/trino/config.properties", config, f"Configure Trino as {role}"
        )

    @exclude_from_package
    def _configure_hive_catalog(self, coordinator_ip: str | None = None) -> None:
        """
        Configure Hive catalog for Trino.

        Args:
            coordinator_ip: For multinode clusters, the coordinator's private IP.
                          Workers use this to connect to the shared Hive Metastore.
                          For coordinator or single-node, pass None to use localhost.
        """
        # Determine metastore URI based on node role
        if coordinator_ip:
            # Worker node: connect to coordinator's Hive Metastore
            metastore_uri = f"thrift://{coordinator_ip}:9083"
        else:
            # Coordinator or single-node: use local Hive Metastore
            metastore_uri = "thrift://localhost:9083"

        hive_catalog = f"""connector.name=hive
hive.metastore.uri={metastore_uri}
hive.storage-format=PARQUET
hive.compression-codec=SNAPPY
hive.allow-drop-table=true
hive.non-managed-table-writes-enabled=true
hive.non-managed-table-creates-enabled=true"""

        self.execute_command("sudo mkdir -p /etc/trino/catalog")
        self._write_config_file(
            "/etc/trino/catalog/hive.properties",
            hive_catalog,
            f"Configure Hive catalog with metastore at {metastore_uri}",
        )

    @exclude_from_package
    def _write_config_file(self, path: str, content: str, description: str) -> None:
        """Helper to write configuration files."""
        self.record_setup_command(
            f"sudo tee {path} > /dev/null << 'EOF'\n{content}\nEOF",
            description,
            "configuration",
        )
        cmd = f"sudo tee {path} > /dev/null << 'EOF'\n{content}\nEOF"
        result = self.execute_command(cmd)
        if not result.get("success", False):
            print(
                f"Warning: Failed to create {path}: {result.get('stderr', 'Unknown error')}"
            )

    @exclude_from_package
    def _create_systemd_service(self, has_local_metastore: bool = True) -> None:
        """
        Create systemd service for Trino.

        Args:
            has_local_metastore: If True, the service depends on local hive-metastore.service.
                               Set to False for worker nodes in multinode clusters.
        """
        if has_local_metastore:
            # Coordinator or single-node: depend on local Hive Metastore
            service_content = f"""[Unit]
Description=Trino Server
After=network.target hive-metastore.service
Requires=hive-metastore.service

[Service]
Type=forking
User=trino
Group=trino
ExecStart={self.trino_home}/bin/launcher start
ExecStop={self.trino_home}/bin/launcher stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        else:
            # Worker node: no local Hive Metastore dependency
            service_content = f"""[Unit]
Description=Trino Server
After=network.target

[Service]
Type=forking
User=trino
Group=trino
ExecStart={self.trino_home}/bin/launcher start
ExecStop={self.trino_home}/bin/launcher stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target"""

        self._write_config_file(
            "/etc/systemd/system/trino.service",
            service_content,
            "Create Trino systemd service",
        )
        self.record_setup_command(
            "sudo systemctl daemon-reload",
            "Reload systemd daemon",
            "service_management",
        )
        self.execute_command("sudo systemctl daemon-reload")

    @exclude_from_package
    def _create_metastore_service(self) -> None:
        """Create systemd service for Hive Metastore."""
        service_content = f"""[Unit]
Description=Hive Metastore
After=network.target

[Service]
Type=simple
User=trino
Group=trino
Environment="JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64"
ExecStart={self.hive_metastore_home}/bin/start-metastore
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target"""

        self._write_config_file(
            "/etc/systemd/system/hive-metastore.service",
            service_content,
            "Create Hive Metastore systemd service",
        )
        self.execute_command("sudo systemctl daemon-reload")

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
    def _parse_memory_to_gb(self, memory_str: str) -> int:
        """Parse memory string like '50GB', '20G' to integer GB."""
        memory_str = memory_str.upper().strip()
        if memory_str.endswith("GB"):
            return int(memory_str[:-2])
        elif memory_str.endswith("G"):
            return int(memory_str[:-1])
        elif memory_str.endswith("MB"):
            return int(memory_str[:-2]) // 1024
        elif memory_str.endswith("M"):
            return int(memory_str[:-1]) // 1024
        else:
            # Assume GB
            return int(memory_str)

    def _verify_preinstalled(self) -> bool:
        """Verify that Trino is already installed and accessible."""
        return self.is_healthy()

    def start(self) -> bool:
        """Start the Trino system."""
        print(f"Starting {self.name} system...")

        # Check if already healthy
        if self.is_healthy(quiet=False):
            print(f"✓ {self.name} is already healthy and ready")
            return True

        # Try to start service
        result = self.execute_command("sudo systemctl start trino", record=False)
        if not result.get("success", False):
            print("Failed to start Trino service")
            return False

        # Wait for health
        success = self.wait_for_health(max_attempts=60, delay=5.0)
        if success:
            print(f"✓ {self.name} is healthy and ready")
        else:
            print(f"✗ {self.name} failed to become healthy")

        return success

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if Trino is running and accepting connections."""
        try:
            # Determine health check host
            health_check_host = getattr(self, "_external_host", None)

            if not health_check_host and self._cloud_instance_manager:
                health_check_host = getattr(
                    self._cloud_instance_manager, "public_ip", None
                )

            if not health_check_host:
                health_check_host = self.host

            if not quiet:
                print(f"Connecting to Trino at {health_check_host}:{self.port}...")

            try:
                import trino
            except ImportError:
                if not quiet:
                    print("Warning: trino package not available")
                return False

            # Connect and test
            conn = trino.dbapi.connect(
                host=health_check_host,
                port=self.port,
                user=self.username,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()

            if not quiet:
                print("Health check successful")

            return result is not None

        except Exception as e:
            if not quiet:
                print(f"Health check failed: {e}")
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a schema in Trino."""
        # Trino schemas are created within a catalog
        sql = f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{schema_name}"
        result = self.execute_query(sql, query_name=f"create_schema_{schema_name}")
        success = bool(result.get("success", False))

        if success:
            # Update current schema
            self.schema = schema_name
            print(f"✓ Using schema: {self.catalog}.{schema_name}")
        else:
            error = result.get("error", "Unknown error")
            print(f"✗ Failed to create schema '{schema_name}': {error}")

        return success

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into Trino table using INSERT."""
        schema_name = kwargs.get("schema", self.schema)
        columns = kwargs.get("columns", None)

        try:
            print(f"Loading {data_path} into {table_name}...")

            # For Trino/Hive, we'll use clickhouse-style approach:
            # Read file and INSERT via Python client
            # This is slower but works universally

            conn = self._get_connection()
            if not conn:
                print("Failed to get Trino connection")
                return False

            cursor = conn.cursor()

            # Read data file and insert
            # TPC-H files are pipe-delimited with trailing pipe
            import csv

            with open(data_path) as f:
                reader = csv.reader(f, delimiter="|")

                # Build INSERT statement
                placeholders = ",".join(["?" for _ in columns]) if columns else ""
                insert_sql = (
                    f"INSERT INTO {schema_name}.{table_name} VALUES ({placeholders})"
                )

                # Batch insert for performance
                batch_size = 10000
                batch = []
                total_rows = 0

                for row in reader:
                    # Remove trailing empty field (from trailing pipe)
                    if row and row[-1] == "":
                        row = row[:-1]

                    # Skip empty rows
                    if not row or all(x == "" for x in row):
                        continue

                    # Convert empty strings to None for NULL values
                    processed_row: list[str | None] = [
                        None if x == "" else x for x in row
                    ]

                    batch.append(processed_row)
                    total_rows += 1

                    if len(batch) >= batch_size:
                        cursor.executemany(insert_sql, batch)
                        batch = []
                        if total_rows % 50000 == 0:
                            print(f"  Loaded {total_rows:,} rows...")

                # Insert remaining batch
                if batch:
                    cursor.executemany(insert_sql, batch)

            conn.close()
            print(f"Successfully loaded {total_rows:,} rows into {table_name}")
            return True

        except Exception as e:
            print(f"Failed to load data into {table_name}: {e}")
            import traceback

            traceback.print_exc()
            return False

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """
        Streaming load not supported for Trino.

        Trino/Hive connector does not have efficient streaming insert capabilities.
        Use load_data() with file-based loading instead.

        Raises:
            NotImplementedError: Always raised as streaming load is not supported
        """
        raise NotImplementedError(
            "Trino does not support streaming data load. "
            "Use load_data() with file-based loading instead."
        )

    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a SQL query in Trino using Python client."""
        from ..debug import debug_print

        # Note: timeout parameter is accepted for API compatibility but not currently used
        _ = timeout

        if not query_name:
            query_name = "unnamed_query"

        timer_obj: Timer | None = None

        try:
            import trino  # type: ignore[import-not-found]
        except ImportError:
            return {
                "success": False,
                "elapsed_s": 0,
                "rows_returned": 0,
                "query_name": query_name,
                "error": "trino package not available",
            }

        try:
            debug_print(f"Executing query: {query_name}")
            if len(query) > 200:
                debug_print(f"SQL: {query[:200]}...")
            else:
                debug_print(f"SQL: {query}")

            with Timer(f"Query {query_name}") as timer:
                timer_obj = timer

                # Connect to Trino
                conn = trino.dbapi.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    catalog=self.catalog,
                    schema=self.schema,
                )
                cursor = conn.cursor()

                # Execute query
                cursor.execute(query)

                # Check if this is a query that returns results
                query_stripped = query.strip().upper()
                # Remove leading comments
                while query_stripped.startswith("--"):
                    newline_pos = query_stripped.find("\n")
                    if newline_pos == -1:
                        query_stripped = ""
                        break
                    query_stripped = query_stripped[newline_pos + 1 :].strip()

                is_select_query = query_stripped.startswith(
                    ("SELECT", "WITH", "SHOW", "DESCRIBE")
                )

                if is_select_query:
                    if return_data:
                        # Fetch all rows and convert to DataFrame
                        import pandas as pd

                        rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        df = pd.DataFrame(rows, columns=columns)
                        rows_returned = len(df)
                    else:
                        rows = cursor.fetchall()
                        rows_returned = len(rows)
                        df = None
                else:
                    # DDL/DML queries don't return rows
                    rows_returned = 0
                    df = None

                conn.close()

                response: dict[str, Any] = {
                    "success": True,
                    "elapsed_s": timer_obj.elapsed if timer_obj else 0,
                    "rows_returned": rows_returned,
                    "query_name": query_name,
                    "error": None,
                }

                if return_data and df is not None:
                    response["data"] = df
                    debug_print(f"Added data to response, df shape: {df.shape}")

                return response

        except Exception as e:
            return {
                "success": False,
                "elapsed_s": timer_obj.elapsed if timer_obj else 0,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get Trino-specific performance metrics."""
        metrics: dict[str, Any] = {}

        try:
            # Query system tables for metrics
            system_queries = {
                "active_queries": "SELECT COUNT(*) FROM system.runtime.queries WHERE state = 'RUNNING'",
                "completed_queries": "SELECT COUNT(*) FROM system.runtime.queries WHERE state = 'FINISHED'",
                "failed_queries": "SELECT COUNT(*) FROM system.runtime.queries WHERE state = 'FAILED'",
                "worker_nodes": "SELECT COUNT(*) FROM system.runtime.nodes WHERE coordinator = false",
                "total_nodes": "SELECT COUNT(*) FROM system.runtime.nodes",
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
        """Clean up Trino installation."""
        success = True

        # Stop services
        self.execute_command("sudo systemctl stop trino || true", record=False)
        self.execute_command("sudo systemctl stop hive-metastore || true", record=False)

        # Clean up data directory if requested
        if self.setup_config.get("cleanup_data", False):
            success = success and self.cleanup_data_directory()

        return success

    def get_version_info(self) -> dict[str, str]:
        """Get detailed version information."""
        version_info = {"configured_version": self.version}

        try:
            # Get actual Trino version
            result = self.execute_query("SELECT version()", query_name="get_version")
            if result["success"]:
                version_info["actual_version"] = "version_retrieved_via_trino_client"

            # Get Python client version
            try:
                import trino

                version_info["trino_client_version"] = getattr(
                    trino, "__version__", "unknown"
                )
            except ImportError:
                version_info["trino_client_version"] = "not_available"

        except Exception as e:
            version_info["version_error"] = str(e)

        return version_info

    @exclude_from_package
    def _setup_database_storage(self, workload: "Workload") -> bool:
        """
        Override base class to setup Trino storage on additional disk.

        For multinode clusters, this runs on ALL nodes.

        Returns:
            True if successful, False otherwise
        """
        # For multinode, we need to setup storage on ALL nodes
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            print(
                f"Setting up storage on all {len(self._cloud_instance_managers)} nodes..."
            )
            return self._setup_multinode_storage(workload)

        # Single node setup
        return self._setup_single_node_storage(workload)

    @exclude_from_package
    def _setup_multinode_storage(self, workload: "Workload") -> bool:
        """
        Setup storage on all nodes in a multinode cluster.
        Each node gets its own RAID0 and Trino data directory.
        """
        all_success = True

        # Store original setup_commands to prevent duplicate recording
        original_commands_count = len(self.setup_commands)

        for idx, mgr in enumerate(self._cloud_instance_managers):
            print(f"\n  [Node {idx}] Setting up storage...")

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
                    print(f"  [Node {idx}] ✗ Storage setup failed")
                    all_success = False
                else:
                    print(f"  [Node {idx}] ✓ Storage setup completed")
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
        Setup storage on a single node. Used by both single-node and multinode setups.
        """
        # Check if /data is already mounted
        check_mount = self.execute_command("mount | grep ' /data '", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            print("    Storage already mounted at /data, creating Trino subdirectory")
            # Create Trino subdirectories
            trino_dir = "/data/trino"
            self.record_setup_command(
                f"sudo mkdir -p {trino_dir}",
                "Create Trino data directory under /data",
                "storage_setup",
            )
            self.execute_command(
                f"sudo mkdir -p {trino_dir}", record=True, category="storage_setup"
            )
            self.execute_command(f"sudo mkdir -p {trino_dir}/hive-data")
            self._set_ownership(trino_dir, owner="trino:trino")
            self.data_dir = Path(trino_dir)
            self.hive_data_dir = Path(f"{trino_dir}/hive-data")
            return True

        # Use base class to mount disk/RAID at /data
        if not super()._setup_database_storage(workload):
            return False

        # Create Trino subdirectories under /data
        trino_dir = "/data/trino"
        self.record_setup_command(
            f"sudo mkdir -p {trino_dir}",
            "Create Trino data directory under /data",
            "storage_setup",
        )
        self.execute_command(
            f"sudo mkdir -p {trino_dir}", record=True, category="storage_setup"
        )
        self.execute_command(f"sudo mkdir -p {trino_dir}/hive-data")
        self._set_ownership(trino_dir, owner="trino:trino")

        # Update data_dir to point to Trino subdirectory
        self.data_dir = Path(trino_dir)
        self.hive_data_dir = Path(f"{trino_dir}/hive-data")

        self.record_setup_note(f"Trino data directory: {trino_dir}")
        print(f"    Trino data directory configured: {trino_dir}")

        return True

    def get_data_generation_directory(self, workload: Any) -> Path | None:
        """
        Get directory for TPC-H data generation on additional disk.

        Returns:
            Path to data generation directory on additional disk, or None for default
        """
        use_additional_disk = self.setup_config.get("use_additional_disk", False)

        if use_additional_disk:
            # Use shared /data/tpch_gen for TPC-H data generation
            tpch_gen_dir = "/data/tpch_gen"

            # Create directory with proper ownership
            self.execute_command(
                f"sudo mkdir -p {tpch_gen_dir} && sudo chown -R $(whoami):$(whoami) {tpch_gen_dir}",
                record=False,
            )

            data_gen_dir = (
                Path(tpch_gen_dir) / workload.name / f"sf{workload.scale_factor}"
            )
            print(f"Trino: Using additional disk for data generation: {data_gen_dir}")
            return cast(Path, data_gen_dir)

        # Use default local path
        return None

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
        if self._cloud_instance_manager and hasattr(
            self._cloud_instance_manager, "public_ip"
        ):
            self._external_host = self._cloud_instance_manager.public_ip
            # Keep self.host as localhost for remote execution
            self.host = "localhost"

    def execute_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
        node_info: str | None = None,
    ) -> dict[str, Any]:
        """Execute command with remote execution support if cloud instance manager is available."""
        if self._cloud_instance_manager and self.setup_method == "native":
            # Execute on remote instance
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
        else:
            return super().execute_command(
                command, timeout, record, category, node_info
            )
