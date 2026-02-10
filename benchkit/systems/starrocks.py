"""StarRocks database system implementation."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from datetime import timedelta
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any

from benchkit.common import DataFormat, exclude_from_package

from ..util import Timer
from .base import SystemUnderTest, TableOperation

if TYPE_CHECKING:
    from ..workloads import Workload

# Optional dependencies - use import_module for proper typing without type: ignore
pymysql: ModuleType | None
try:
    pymysql = import_module("pymysql")
except ModuleNotFoundError:
    pymysql = None

requests: ModuleType | None
try:
    requests = import_module("requests")
except ModuleNotFoundError:
    requests = None


class StarrocksSystem(SystemUnderTest):
    """StarRocks database system implementation.

    StarRocks is a next-generation sub-second MPP database for full analytics scenarios.
    It uses a MySQL-compatible protocol for queries and HTTP Stream Load for data ingestion.

    Architecture:
    - FE (Frontend): Query parsing, planning, and coordination
    - BE (Backend): Data storage and query execution

    Multinode Support:
    - All nodes run both FE and BE
    - Node 0: FE Leader + BE
    - Nodes 1+: FE Followers + BEs
    - FE cluster uses BDBJE for metadata replication
    - BEs are registered via ALTER SYSTEM ADD BACKEND
    """

    # StarRocks supports multinode clusters
    SUPPORTS_MULTINODE = True
    # StarRocks uses HTTP Stream Load for data ingestion
    SUPPORTS_STREAMLOAD = True
    # Stream Load is slightly slower than direct inserts
    LOAD_TIMEOUT_MULTIPLIER = 1.2

    # StarRocks ports
    FE_MYSQL_PORT = 9030  # MySQL protocol (queries)
    FE_HTTP_PORT = 8030  # HTTP port (Stream Load, web UI)
    FE_RPC_PORT = 9020  # Thrift RPC port
    FE_EDIT_LOG_PORT = 9010  # BDBJE replication port
    BE_THRIFT_PORT = 9060  # BE Thrift port
    BE_HTTP_PORT = 8040  # BE HTTP port
    BE_HEARTBEAT_PORT = 9050  # BE heartbeat port
    BE_BRPC_PORT = 8060  # BE BRPC port

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by StarRocks system."""
        return ["pymysql>=1.0.0", "requests>=2.28.0"]

    def get_storage_config(self) -> tuple[str | None, str]:
        """Return StarRocks-specific storage configuration.

        StarRocks uses /data/starrocks subdirectory with ubuntu user ownership.
        """
        return "/data/starrocks", "ubuntu:ubuntu"

    @classmethod
    def _get_connection_defaults(cls) -> dict[str, Any]:
        return {
            "port": 9030,
            "username": "root",
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
        """Return ports required by StarRocks system."""
        return {
            "StarRocks FE MySQL": cls.FE_MYSQL_PORT,
            "StarRocks FE HTTP": cls.FE_HTTP_PORT,
            "StarRocks FE RPC": cls.FE_RPC_PORT,
            "StarRocks FE Edit Log": cls.FE_EDIT_LOG_PORT,
            "StarRocks BE Thrift": cls.BE_THRIFT_PORT,
            "StarRocks BE HTTP": cls.BE_HTTP_PORT,
            "StarRocks BE Heartbeat": cls.BE_HEARTBEAT_PORT,
            "StarRocks BE BRPC": cls.BE_BRPC_PORT,
        }

    @exclude_from_package
    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """Get StarRocks connection string with full CLI command."""
        port = self.setup_config.get("port", self.FE_MYSQL_PORT)
        username = self.setup_config.get("username", "root")
        database = self.setup_config.get("database", "benchmark")

        cmd = f"mysql -h {public_ip} -P {port} -u {username}"

        if database and database != "default":
            cmd += f" -D {database}"

        if self.password:
            cmd += " -p"

        return cmd

    def __init__(
        self,
        config: dict[str, Any],
        output_callback: Callable[[str], None] | None = None,
        workload_config: dict[str, Any] | None = None,
    ):
        super().__init__(config, output_callback, workload_config)
        self.setup_method = self.setup_config.get("method", "native")

        # Connection settings
        raw_host = self.setup_config.get("host", "localhost")
        resolved_host = self._resolve_ip_addresses(raw_host)

        # For multinode, use first IP for connection
        if "," in resolved_host:
            self.host = resolved_host.split(",")[0].strip()
        else:
            self.host = resolved_host

        self.port = self.setup_config.get("port", self.FE_MYSQL_PORT)
        self.http_port = self.setup_config.get("http_port", self.FE_HTTP_PORT)
        self.username = self.setup_config.get("username", "root")
        self.password = self.setup_config.get("password", "")
        self.database = self.setup_config.get("database", "benchmark")

        # StarRocks installation directory
        self.install_dir = "/opt/starrocks"
        self.fe_dir = f"{self.install_dir}/fe"
        self.be_dir = f"{self.install_dir}/be"

        # Cluster configuration
        self.cluster_name = "benchmark_cluster"

        # Determine Java version based on StarRocks version
        # StarRocks 4.x requires JDK 17+, 3.x works with JDK 11
        major_version = int(self.version.split(".")[0])
        if major_version >= 4:
            self._java_home = "/usr/lib/jvm/java-17-openjdk-amd64"
        else:
            self._java_home = "/usr/lib/jvm/java-11-openjdk-amd64"

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """Check if StarRocks is already installed."""
        if self.setup_method != "native":
            return False

        # Check for installation marker
        if not self.has_install_marker():
            self._log("No existing StarRocks installation marker found")
            return False

        self._log("Found existing StarRocks installation marker")

        # Check if FE binary exists
        fe_check = self.execute_command(
            f"test -f {self.fe_dir}/bin/start_fe.sh && echo 'exists'", record=False
        )
        if not (
            fe_check.get("success", False) and "exists" in fe_check.get("stdout", "")
        ):
            self._log(
                "⚠ Installation marker found but FE not available, will reinstall"
            )
            return False

        self._log("✓ StarRocks FE binary available")

        # Check if FE process is running
        fe_running = self.execute_command(
            "pgrep -f 'StarRocksFE' || pgrep -f 'com.starrocks.StarRocksFE'",
            record=False,
        )
        if not fe_running.get("success", False):
            self._log("⚠ StarRocks FE not running, will restart")
            return False

        self._log("✓ StarRocks FE process is running")

        # Check database connectivity
        if self.is_healthy(quiet=False):
            self._log("✓ StarRocks database is accessible and healthy")
            return True
        else:
            self._log("⚠ StarRocks installation exists but database not accessible")
            return False

    def _get_connection(self) -> Any:
        """Get a MySQL connection to StarRocks."""
        if pymysql is None:
            raise ImportError("pymysql is required for StarRocks connections")

        # Use centralized timeout calculator for query operations
        query_timeout = int(self._get_query_execution_timeout())
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            database=self.database if self.database else None,
            connect_timeout=30,
            read_timeout=query_timeout,
            write_timeout=query_timeout,
        )

    @exclude_from_package
    def _install_docker(self) -> bool:
        """Docker installation not supported for StarRocks."""
        self._log(
            "Docker installation not supported for StarRocks. Use native installation."
        )
        return False

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install StarRocks using official tarball."""
        self.record_setup_note("Installing StarRocks using official tarball")

        is_multinode = (
            self._cloud_instance_managers and len(self._cloud_instance_managers) > 1
        )

        # For multinode: download tarball in parallel on all nodes first
        # This avoids sequential 3GB downloads (saves ~15min per node)
        if is_multinode:
            if not self._download_tarball_parallel():
                return False

        # Install on all nodes (will skip download if tarball already exists)
        if not self._install_on_all_nodes(self._install_native_on_node):
            return False

        # For multinode, configure cluster
        if is_multinode:
            if not self._configure_multinode_cluster():
                return False

        return True

    @exclude_from_package
    def _download_tarball_parallel(self) -> bool:
        """Download StarRocks tarball on all nodes in parallel.

        This optimization reduces download time from O(n * download_time) to
        O(download_time), saving significant time for large clusters.
        """
        if not self._cloud_instance_managers:
            return True

        import concurrent.futures

        download_url = f"https://releases.starrocks.io/starrocks/StarRocks-{self.version}-ubuntu-amd64.tar.gz"
        tarball = f"/tmp/starrocks-{self.version}.tar.gz"
        node_count = len(self._cloud_instance_managers)

        self._log(
            f"📦 Downloading StarRocks {self.version} on {node_count} nodes in parallel..."
        )

        def download_on_node(idx_mgr: tuple) -> tuple[int, bool, str]:
            idx, mgr = idx_mgr
            try:
                # Check if already downloaded
                check_result = mgr.run_remote_command(
                    f"test -f {tarball} && echo exists", timeout=10
                )
                if "exists" in check_result.get("stdout", ""):
                    return (idx, True, "already exists")

                # Download with retries for transient network failures
                result = mgr.run_remote_command(
                    f"wget -q --tries=3 --retry-connrefused --waitretry=5 -O {tarball} {download_url}",
                    timeout=900,  # 15 minutes for ~3GB
                )
                if result.get("success", False):
                    return (idx, True, "downloaded")
                else:
                    return (idx, False, result.get("stderr", "unknown error")[:100])
            except Exception as e:
                return (idx, False, str(e)[:100])

        # Run downloads in parallel on all nodes
        with concurrent.futures.ThreadPoolExecutor(max_workers=node_count) as executor:
            futures = list(
                executor.map(download_on_node, enumerate(self._cloud_instance_managers))
            )

        # Check results
        all_success = True
        for node_idx, success, msg in futures:
            if success:
                self._log(f"  ✓ Node {node_idx}: {msg}")
            else:
                self._log(f"  ✗ Node {node_idx}: failed - {msg}")
                all_success = False

        if all_success:
            self._log(f"✅ Tarball ready on all {node_count} nodes")

        return all_success

    def _is_follower_node(self) -> bool:
        """Check if current node is a follower (not the leader) in multinode setup."""
        if not self._cloud_instance_managers or len(self._cloud_instance_managers) <= 1:
            return False
        # Current node is a follower if it's not the first node (node 0 is leader)
        if self._cloud_instance_manager is not None:
            is_follower: bool = (
                self._cloud_instance_manager != self._cloud_instance_managers[0]
            )
            return is_follower
        return False

    @exclude_from_package
    def _install_native_on_node(self) -> bool:
        """Install StarRocks on the current node."""
        try:
            is_follower = self._is_follower_node()
            is_multinode = (
                self._cloud_instance_managers and len(self._cloud_instance_managers) > 1
            )

            # Step 1: Install prerequisites
            # StarRocks 4.x requires JDK 17+, 3.x works with JDK 11
            major_version = int(self.version.split(".")[0])
            if major_version >= 4:
                jdk_package = "openjdk-17-jdk"
                java_home = "/usr/lib/jvm/java-17-openjdk-amd64"
            else:
                jdk_package = "openjdk-11-jdk"
                java_home = "/usr/lib/jvm/java-11-openjdk-amd64"

            self._log(
                f"Installing prerequisites (JDK for StarRocks {major_version}.x)..."
            )
            result = self.execute_command(
                f"sudo apt-get update && sudo apt-get install -y {jdk_package} curl wget mysql-client",
                timeout=300.0,
                description="Install Java, MySQL client, and utilities",
                category="prerequisites",
            )
            if not result.get("success", False):
                self._log(
                    f"Failed to install prerequisites: {result.get('stderr', '')}"
                )
                return False

            # Set JAVA_HOME
            self.execute_command(
                f'echo "export JAVA_HOME={java_home}" | sudo tee -a /etc/profile.d/java.sh',
                description="Set JAVA_HOME environment variable",
                category="prerequisites",
            )
            self._java_home = java_home

            # Step 2: Download StarRocks (skip if already downloaded by parallel download)
            # StarRocks binary releases use format: StarRocks-{version}-{os}-amd64.tar.gz
            download_url = f"https://releases.starrocks.io/starrocks/StarRocks-{self.version}-ubuntu-amd64.tar.gz"
            tarball = f"/tmp/starrocks-{self.version}.tar.gz"

            # Check if tarball already exists (from parallel download)
            check_result = self.execute_command(
                f"test -f {tarball} && echo exists", timeout=10.0
            )
            tarball_exists = "exists" in check_result.get("stdout", "")

            if tarball_exists:
                self._log(
                    f"StarRocks {self.version} tarball already downloaded, skipping..."
                )
            else:
                self._log(f"Downloading StarRocks {self.version}...")
                result = self.execute_command(
                    f"wget -q --tries=3 --retry-connrefused --waitretry=5 -O {tarball} {download_url}",
                    timeout=900.0,  # 15 minutes for ~3GB
                    description=f"Download StarRocks {self.version}",
                    category="installation",
                )
                if not result.get("success", False):
                    self._log(
                        f"Failed to download StarRocks: {result.get('stderr', '')}"
                    )
                    return False

            # Step 3: Extract and install
            self._log("Extracting StarRocks...")
            result = self.execute_command(
                f"sudo mkdir -p {self.install_dir} && sudo tar -xzf {tarball} -C {self.install_dir} --strip-components=1",
                timeout=120.0,
                description="Extract StarRocks to installation directory",
                category="installation",
            )
            if not result.get("success", False):
                self._log(f"Failed to extract StarRocks: {result.get('stderr', '')}")
                return False

            # Step 4: Configure FE
            self._log("Configuring FE...")
            fe_conf = self._generate_fe_config()
            self._write_remote_config_file(
                f"{self.fe_dir}/conf/fe.conf",
                fe_conf,
                "Configure StarRocks FE",
                "configuration",
            )

            # Step 5: Configure BE
            self._log("Configuring BE...")
            be_conf = self._generate_be_config()
            self._write_remote_config_file(
                f"{self.be_dir}/conf/be.conf",
                be_conf,
                "Configure StarRocks BE",
                "configuration",
            )

            # Step 6: Set permissions
            self.execute_command(
                f"sudo chown -R $(whoami):$(whoami) {self.install_dir}",
                description="Set StarRocks directory ownership",
                category="installation",
            )

            # Step 7: Start FE (skip on follower nodes - they'll be started with --helper)
            if is_multinode and is_follower:
                self._log(
                    "Skipping FE startup on follower node (will join cluster later)"
                )
            else:
                self._log("Starting FE...")
                result = self.execute_command(
                    f"export JAVA_HOME={self._java_home} && cd {self.fe_dir} && ./bin/start_fe.sh --daemon",
                    description="Start StarRocks FE",
                    category="service_management",
                )
                if not result.get("success", False):
                    self._log(f"Failed to start FE: {result.get('stderr', '')}")
                    return False

                # Wait for FE to be ready
                self._log("Waiting for FE to be ready...")
                if not self._wait_for_fe_ready(timeout=120):
                    self._log("FE failed to become ready")
                    return False

            # Step 8: Start BE (skip on follower nodes - they'll be started after cluster config)
            if is_multinode and is_follower:
                self._log(
                    "Skipping BE startup on follower node (will start after cluster config)"
                )
            else:
                self._log("Starting BE...")
                result = self.execute_command(
                    f"export JAVA_HOME={self._java_home} && cd {self.be_dir} && ./bin/start_be.sh --daemon",
                    description="Start StarRocks BE",
                    category="service_management",
                )
                if not result.get("success", False):
                    self._log(f"Failed to start BE: {result.get('stderr', '')}")
                    return False

            # Step 9: Register BE with FE (single node only)
            if not is_multinode:
                self._log("Registering BE with FE...")
                time.sleep(5)  # Give BE time to start
                if not self._register_local_backend():
                    self._log("Warning: Failed to register BE, continuing anyway...")

            # Step 10: Wait for system to be healthy (skip on follower nodes)
            if is_multinode and is_follower:
                self._log("Skipping health check on follower node")
            else:
                self._log("Waiting for StarRocks to be healthy...")
                if not self.wait_for_health(max_attempts=30, delay=3.0):
                    self._log("StarRocks failed to become healthy")
                    return False

            # Update connection parameters
            if self._cloud_instance_manager:
                self._external_host = self._cloud_instance_manager.public_ip
                self.host = "localhost"

            return True

        except Exception as e:
            self._log(f"StarRocks installation failed: {e}")
            import traceback

            self._log(f"Traceback:\n{traceback.format_exc()}")
            return False

    def _generate_fe_config(self) -> str:
        """Generate FE configuration."""
        # Get private IP for this node
        if self._cloud_instance_manager:
            priority_networks = self._cloud_instance_manager.private_ip
        else:
            priority_networks = "127.0.0.1"

        # Extract network prefix (e.g., 10.0.1.0/24 from 10.0.1.5)
        if "." in priority_networks:
            parts = priority_networks.split(".")
            priority_networks = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

        config = f"""# StarRocks FE Configuration
LOG_DIR = {self.fe_dir}/log
meta_dir = {self.fe_dir}/meta
http_port = {self.FE_HTTP_PORT}
rpc_port = {self.FE_RPC_PORT}
query_port = {self.FE_MYSQL_PORT}
edit_log_port = {self.FE_EDIT_LOG_PORT}
priority_networks = {priority_networks}
# Performance tuning
qe_max_connection = 1024
# Memory settings
metadata_memory_limit = 8G
"""
        return config

    def _generate_be_config(self) -> str:
        """Generate BE configuration."""
        # Get private IP for this node
        if self._cloud_instance_manager:
            priority_networks = self._cloud_instance_manager.private_ip
        else:
            priority_networks = "127.0.0.1"

        # Extract network prefix
        if "." in priority_networks:
            parts = priority_networks.split(".")
            priority_networks = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

        # Use data directory from setup or default
        storage_root = str(self.data_dir) if self.data_dir else f"{self.be_dir}/storage"

        config = f"""# StarRocks BE Configuration
LOG_DIR = {self.be_dir}/log
be_port = {self.BE_THRIFT_PORT}
be_http_port = {self.BE_HTTP_PORT}
heartbeat_service_port = {self.BE_HEARTBEAT_PORT}
brpc_port = {self.BE_BRPC_PORT}
priority_networks = {priority_networks}
storage_root_path = {storage_root}
# Performance tuning - aggressive memory use with spill fallback
mem_limit = 90%
# Parallel execution
parallel_fragment_exec_instance_num = 16
# Spill-to-disk for memory-intensive queries (safety net)
spill_local_storage_dir = {storage_root}/spill
enable_spill = true
spill_mode = auto
"""
        return config

    def _wait_for_fe_ready(self, timeout: int = 60) -> bool:
        """Wait for FE to be ready to accept connections."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to connect via MySQL protocol
                result = self.execute_command(
                    f"mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e 'SELECT 1' 2>/dev/null",
                    timeout=10.0,
                    record=False,
                )
                if result.get("success", False):
                    return True
            except Exception:
                pass
            time.sleep(2)
        return False

    def _register_local_backend(self) -> bool:
        """Register the local BE with FE."""
        # Get private IP
        if self._cloud_instance_manager:
            be_host = self._cloud_instance_manager.private_ip
        else:
            be_host = "127.0.0.1"

        sql = f"ALTER SYSTEM ADD BACKEND '{be_host}:{self.BE_HEARTBEAT_PORT}'"
        result = self.execute_command(
            f'mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e "{sql}" 2>/dev/null || true',
            timeout=30.0,
            record=False,
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def _configure_multinode_cluster(self) -> bool:
        """Configure StarRocks cluster for multinode deployment."""
        if not self._cloud_instance_managers or len(self._cloud_instance_managers) < 2:
            return True

        self._log(
            f"Configuring cluster with {len(self._cloud_instance_managers)} nodes..."
        )

        node_ips = [mgr.private_ip for mgr in self._cloud_instance_managers]
        leader_ip = node_ips[0]

        # Step 1: Add FE followers (nodes 1+)
        self._log("Adding FE followers...")
        for idx in range(1, len(self._cloud_instance_managers)):
            follower_ip = node_ips[idx]
            sql = f"ALTER SYSTEM ADD FOLLOWER '{follower_ip}:{self.FE_EDIT_LOG_PORT}'"
            self.record_setup_command(
                f'mysql -h {leader_ip} -P {self.FE_MYSQL_PORT} -u root -e "{sql}"',
                f"Add FE follower node {idx}",
                "cluster_configuration",
            )
            # Execute on leader
            result = self._cloud_instance_managers[0].run_remote_command(
                f'mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e "{sql}"',
                timeout=30,
            )
            if result.get("success"):
                self._log(f"  ✓ Added FE follower {idx}: {follower_ip}")
            else:
                self._log(f"  ⚠ Failed to add FE follower {idx}, continuing...")

        # Step 2: Start FE on follower nodes with --helper flag
        self._log("Starting FE on follower nodes...")
        for idx in range(1, len(self._cloud_instance_managers)):
            mgr = self._cloud_instance_managers[idx]
            start_cmd = (
                f"export JAVA_HOME={self._java_home} && "
                f"cd {self.fe_dir} && ./bin/start_fe.sh --helper {leader_ip}:{self.FE_EDIT_LOG_PORT} --daemon"
            )
            result = mgr.run_remote_command(start_cmd, timeout=60)
            if result.get("success"):
                self._log(f"  ✓ Started FE on node {idx}")
            else:
                self._log(f"  ✗ Failed to start FE on node {idx}")
                return False

        self.record_setup_command(
            f"export JAVA_HOME={self._java_home} && "
            f"cd {self.fe_dir} && ./bin/start_fe.sh --helper {leader_ip}:{self.FE_EDIT_LOG_PORT} --daemon",
            "Start FE on follower nodes to join cluster",
            "service_management",
        )

        # Wait for FE cluster to sync
        time.sleep(10)

        # Step 3: Register all BEs
        self._log("Registering all BEs...")
        for idx, ip in enumerate(node_ips):
            sql = f"ALTER SYSTEM ADD BACKEND '{ip}:{self.BE_HEARTBEAT_PORT}'"
            self.record_setup_command(
                f'mysql -h {leader_ip} -P {self.FE_MYSQL_PORT} -u root -e "{sql}"',
                f"Register BE on node {idx}",
                "cluster_configuration",
            )
            result = self._cloud_instance_managers[0].run_remote_command(
                f'mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e "{sql}" 2>/dev/null || true',
                timeout=30,
            )
            if result.get("success"):
                self._log(f"  ✓ Registered BE on node {idx}: {ip}")
            else:
                self._log(f"  ⚠ Failed to register BE on node {idx}, continuing...")

        # Step 4: Start BEs on all nodes (node 0's BE is already running, followers need to start)
        self._log("Starting BEs on all nodes...")
        for idx, mgr in enumerate(self._cloud_instance_managers):
            # Check if BE process is actually running
            # Use pidof for exact binary match to avoid pgrep -f matching the SSH command itself
            check_result = mgr.run_remote_command(
                "pidof -s starrocks_be > /dev/null 2>&1 && echo 'running' || echo 'stopped'",
                timeout=10,
            )
            if check_result.get("stdout", "").strip() == "running":
                self._log(f"  ✓ BE already running on node {idx}")
                continue

            start_cmd = (
                f"export JAVA_HOME={self._java_home} && "
                f"cd {self.be_dir} && ./bin/start_be.sh --daemon"
            )
            result = mgr.run_remote_command(start_cmd, timeout=60)
            if result.get("success"):
                self._log(f"  ✓ Started BE on node {idx}")
            else:
                self._log(f"  ⚠ Failed to start BE on node {idx}")

        self.record_setup_command(
            f"export JAVA_HOME={self._java_home} && "
            f"cd {self.be_dir} && ./bin/start_be.sh --daemon",
            "Start BE on all cluster nodes",
            "service_management",
        )

        # Wait for cluster to stabilize
        time.sleep(15)

        # Verify cluster status
        self._log("Verifying cluster status...")
        verify_result = self._cloud_instance_managers[0].run_remote_command(
            f"mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e \"SHOW PROC '/frontends'\"",
            timeout=30,
        )
        if verify_result.get("success"):
            self._log(f"FE cluster status:\n{verify_result.get('stdout', '')}")

        be_result = self._cloud_instance_managers[0].run_remote_command(
            f"mysql -h 127.0.0.1 -P {self.FE_MYSQL_PORT} -u root -e \"SHOW PROC '/backends'\"",
            timeout=30,
        )
        if be_result.get("success"):
            self._log(f"BE cluster status:\n{be_result.get('stdout', '')}")

        self.record_setup_note(
            f"StarRocks cluster configured with {len(node_ips)} nodes"
        )

        # Final health check
        self._log("Waiting for cluster to be healthy...")
        if not self.wait_for_health(max_attempts=30, delay=3.0):
            self._log("⚠ Cluster health check failed, but continuing...")

        # Mark all nodes as installed
        self._log("Marking all nodes as installed...")
        for mgr in self._cloud_instance_managers:
            mgr.run_remote_command(
                "echo 'installed' > ~/.starrocks_installed",
                timeout=10,
            )

        return True

    @exclude_from_package
    def start(self) -> bool:
        """Start the StarRocks system."""
        # Start FE
        result = self.execute_command(
            f"export JAVA_HOME={self._java_home} && cd {self.fe_dir} && ./bin/start_fe.sh --daemon"
        )
        if not result.get("success", False):
            return False

        # Wait for FE
        if not self._wait_for_fe_ready(timeout=60):
            return False

        # Start BE
        result = self.execute_command(
            f"export JAVA_HOME={self._java_home} && cd {self.be_dir} && ./bin/start_be.sh --daemon"
        )
        if not result.get("success", False):
            return False

        return self.wait_for_health()

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if StarRocks is running and accepting connections."""
        try:
            health_check_host = self._get_health_check_host()

            if pymysql is None:
                if not quiet:
                    self._log("Warning: pymysql not available")
                return False

            conn = pymysql.connect(
                host=health_check_host,
                port=self.port,
                user=self.username,
                password=self.password,
                connect_timeout=10,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            if not quiet:
                self._log(f"Health check failed: {e}")
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a database in StarRocks."""
        try:
            if pymysql is None:
                self._log("✗ Failed to create database: pymysql not available")
                return False

            # Connect without specifying a database to create the new one
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=None,  # Don't specify database for CREATE DATABASE
                connect_timeout=30,
            )

            try:
                cursor = conn.cursor()
                sql = f"CREATE DATABASE IF NOT EXISTS {schema_name}"
                cursor.execute(sql)
                conn.commit()
                cursor.close()
            finally:
                conn.close()

            self.database = schema_name
            self._log(f"✓ Created database: {schema_name}")
            return True

        except Exception as e:
            self._log(f"✗ Failed to create database: {e}")
            return False

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into StarRocks table using Stream Load."""
        schema_name = kwargs.get("schema", self.database)

        try:
            self._log(f"Loading {data_path} into {table_name}...")

            # Use Stream Load via curl for bulk loading
            load_host = self._get_health_check_host()

            # Get column separator from kwargs or default to pipe
            column_separator = kwargs.get("column_separator", "|")

            # Get columns for explicit mapping (important when DDL column order
            # differs from data file column order, e.g., date columns moved first)
            columns = kwargs.get("columns", [])

            # Build Stream Load command
            # StarRocks Stream Load expects HTTP PUT to /api/{db}/{table}/_stream_load
            headers = [
                f'-H "column_separator:{column_separator}"',
                '-H "Expect:100-continue"',
            ]

            # Add explicit column mapping if provided
            if columns:
                columns_str = ",".join(columns)
                headers.append(f'-H "columns:{columns_str}"')

            curl_cmd = (
                f"curl --location-trusted -u {self.username}:{self.password} "
                f"{' '.join(headers)} "
                f"-T {data_path} "
                f"http://{load_host}:{self.http_port}/api/{schema_name}/{table_name}/_stream_load"
            )

            result = self.execute_command(
                curl_cmd, timeout=self._get_data_loading_timeout(), record=False
            )

            if not result.get("success", False):
                self._log(f"Stream Load failed: {result.get('stderr', '')}")
                return False

            # Check response for success
            stdout = result.get("stdout", "")
            if '"Status": "Success"' in stdout or '"Status":"Success"' in stdout:
                self._log(f"✓ Successfully loaded data into {table_name}")
                return True
            elif '"Status": "Fail"' in stdout or '"Status":"Fail"' in stdout:
                self._log(f"Stream Load reported failure: {stdout}")
                return False
            else:
                # Try to verify by counting rows
                count_result = self.execute_query(
                    f"SELECT COUNT(*) FROM {schema_name}.{table_name}",
                    query_name=f"count_{table_name}",
                )
                if count_result.get("success", False):
                    self._log(f"✓ Data loaded into {table_name}")
                    return True
                self._log(f"Could not verify data load: {stdout}")
                return False

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """Load data from iterable - not implemented for StarRocks."""
        raise NotImplementedError("StarRocks.load_data_from_iterable not implemented")

    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a SQL query in StarRocks using pymysql."""
        from ..debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        if timeout is None:
            timeout = 300

        try:
            debug_print(f"Executing query: {query_name}")
            if len(query) > 200:
                debug_print(f"SQL: {query[:200]}...")
            else:
                debug_print(f"SQL: {query}")

            with Timer(f"Query {query_name}") as timer:
                if pymysql is None:
                    return {
                        "success": False,
                        "elapsed_s": 0,
                        "rows_returned": 0,
                        "query_name": query_name,
                        "error": "pymysql not available",
                    }

                # Use active schema if set
                database_to_use = getattr(self, "_active_schema", None) or self.database

                conn = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.username,
                    password=self.password,
                    database=database_to_use,
                    connect_timeout=30,
                    read_timeout=timeout,
                    write_timeout=timeout,
                )

                try:
                    cursor = conn.cursor()

                    # Strip comments and detect query type
                    query_stripped = query.strip()
                    while query_stripped.startswith("--"):
                        newline_pos = query_stripped.find("\n")
                        if newline_pos == -1:
                            query_stripped = ""
                            break
                        query_stripped = query_stripped[newline_pos + 1 :].strip()

                    cursor.execute(query)

                    if query_stripped.upper().startswith(
                        ("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN")
                    ):
                        rows = cursor.fetchall()
                        rows_returned = len(rows)

                        if return_data:
                            import pandas as pd

                            columns = [desc[0] for desc in cursor.description]
                            df = pd.DataFrame(rows, columns=columns)
                        else:
                            df = None
                    else:
                        conn.commit()
                        rows_returned = cursor.rowcount if cursor.rowcount >= 0 else 0
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
                    cursor.close()
                    conn.close()

        except Exception as e:
            return {
                "success": False,
                "elapsed_s": timer.elapsed if "timer" in locals() else 0,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get StarRocks-specific performance metrics."""
        metrics: dict[str, Any] = {}

        try:
            # Query system tables
            system_queries = {
                "be_count": "SELECT COUNT(*) FROM information_schema.be_bvars",
                "fe_count": "SHOW PROC '/frontends'",
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

    def get_table_sizes(
        self, schema: str, table_names: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Query StarRocks for table storage sizes.

        Uses information_schema.tables_config and SHOW DATA to get storage sizes.

        Args:
            schema: Database name containing the tables
            table_names: List of table names to query

        Returns:
            Dict mapping table names to size info with raw_bytes, stored_bytes,
            row_count, and compression_ratio.
        """
        sizes: dict[str, dict[str, Any]] = {}

        try:
            for table_name in table_names:
                try:
                    # Get row count
                    count_query = (
                        f"SELECT COUNT(*) as cnt FROM `{schema}`.`{table_name}`"
                    )
                    count_result = self.execute_query(
                        count_query, query_name=f"count_{table_name}", return_data=True
                    )
                    row_count = 0
                    if count_result.get("success") and "data" in count_result:
                        df = count_result["data"]
                        if not df.empty:
                            row_count = int(df.iloc[0, 0])

                    # Get table size using SHOW DATA
                    # This returns size in bytes for the table
                    show_data_query = f"SHOW DATA FROM `{schema}`.`{table_name}`"
                    size_result = self.execute_query(
                        show_data_query,
                        query_name=f"size_{table_name}",
                        return_data=True,
                    )

                    stored_bytes = 0
                    raw_bytes = 0

                    if size_result.get("success") and "data" in size_result:
                        df = size_result["data"]
                        if not df.empty:
                            # SHOW DATA returns columns: TableName, Size, ReplicaCount
                            # Size is the stored/compressed size
                            size_str = (
                                str(df.iloc[0]["Size"]) if "Size" in df.columns else "0"
                            )
                            # Parse size string (could be "10.5 GB", "100 MB", etc.)
                            stored_bytes = self._parse_size_string(size_str)
                            # StarRocks doesn't expose raw size directly
                            # Use stored_bytes as approximation
                            raw_bytes = stored_bytes

                    sizes[table_name.lower()] = {
                        "raw_bytes": raw_bytes,
                        "stored_bytes": stored_bytes,
                        "row_count": row_count,
                        "compression_ratio": (
                            raw_bytes / stored_bytes if stored_bytes > 0 else 0.0
                        ),
                    }

                except Exception as e:
                    self._log(
                        f"Warning: Failed to get size for table {table_name}: {e}"
                    )

        except Exception as e:
            self._log(f"Warning: Failed to get table sizes: {e}")

        return sizes

    def _parse_size_string(self, size_str: str) -> int:
        """Parse size string like '10.5 GB' or '100 MB' to bytes."""
        import re

        if not size_str:
            return 0

        # Try to parse numeric value with optional unit
        match = re.match(r"([\d.]+)\s*([KMGTP]?B?)", size_str.strip(), re.IGNORECASE)
        if not match:
            return 0

        value = float(match.group(1))
        unit = match.group(2).upper()

        multipliers = {
            "": 1,
            "B": 1,
            "K": 1024,
            "KB": 1024,
            "M": 1024**2,
            "MB": 1024**2,
            "G": 1024**3,
            "GB": 1024**3,
            "T": 1024**4,
            "TB": 1024**4,
            "P": 1024**5,
            "PB": 1024**5,
        }

        return int(value * multipliers.get(unit, 1))

    def get_template_variables(self) -> dict[str, Any]:
        """Return StarRocks-specific template variables for SQL rendering.

        Unpacks extra config values (bucket_count, replication_num) so templates
        can use them directly as {{ bucket_count }} instead of {{ system_extra.bucket_count }}.

        Returns:
            Dictionary with bucket_count and replication_num
        """
        variables = super().get_template_variables()

        # Unpack extra config for template access
        extra = self.setup_config.get("extra", {})
        if "bucket_count" in extra:
            variables["bucket_count"] = extra["bucket_count"]
        if "replication_num" in extra:
            variables["replication_num"] = extra["replication_num"]

        return variables

    def teardown(self) -> bool:
        """Clean up StarRocks installation."""
        success = True

        # Stop BE
        stop_be = self.execute_command(f"cd {self.be_dir} && ./bin/stop_be.sh || true")

        # Stop FE
        stop_fe = self.execute_command(f"cd {self.fe_dir} && ./bin/stop_fe.sh || true")

        success = stop_be.get("success", False) and stop_fe.get("success", False)

        # Clean up data if requested
        if self.setup_config.get("cleanup_data", False):
            success = success and self.cleanup_data_directory()

        return success

    @exclude_from_package
    def _setup_database_storage(self, workload: Workload) -> bool:
        """Setup storage for StarRocks.

        For multinode, setup on all nodes.
        Subdirectory and ownership are handled via get_storage_config() hook.
        """
        # For multinode, setup on all nodes
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            self._log(
                f"Setting up storage on all {len(self._cloud_instance_managers)} nodes..."
            )
            return self._setup_multinode_storage(workload)

        # Single node - use base class with hook
        return super()._setup_database_storage(workload)

    def _should_execute_remotely(self) -> bool:
        """StarRocks only executes remotely for native installations."""
        return (
            self._cloud_instance_manager is not None and self.setup_method == "native"
        )

    def estimate_execution_time(
        self, operation: TableOperation, data_size_gb: float
    ) -> timedelta:
        """Estimate execution time for operations."""
        if operation == "OPTIMIZE TABLE":
            # StarRocks doesn't have OPTIMIZE, but ANALYZE is similar
            estimate = timedelta(minutes=0.5 * data_size_gb / self.node_count)
            return max(timedelta(minutes=5), min(timedelta(hours=1), estimate))

        return super().estimate_execution_time(operation, data_size_gb)
