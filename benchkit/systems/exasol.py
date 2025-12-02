"""Exasol database system implementation."""

import os
import ssl
from pathlib import Path
from typing import Any, Callable, cast

import pyexasol  # type: ignore

from ..package.markers import exclude_from_package
from ..util import Timer
from .base import SystemUnderTest


class ExasolSystem(SystemUnderTest):
    """Exasol database system implementation."""

    # Exasol supports multinode clusters via c4 tool
    SUPPORTS_MULTINODE = True

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by Exasol system."""
        return ["pyexasol>=0.25.0"]

    @classmethod
    def extract_workload_connection_info(
        cls, setup_config: dict[str, Any], for_local_execution: bool = False
    ) -> dict[str, Any]:
        """
        Extract Exasol connection info with proper defaults and password handling.

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

        setup_method = setup_config.get("method", "docker")

        # For installer method, password comes from db_password, not password
        if setup_method == "installer":
            password = setup_config.get("db_password", "exasol")
        else:
            password = setup_config.get("password", "exasol")

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
            "port": setup_config.get("port", 8563),
            "username": setup_config.get("username", "sys"),
            "password": password,
            "schema": setup_config.get("schema", "benchmark"),
        }

        # Preserve use_additional_disk setting for data generation on remote instances
        if setup_config.get("use_additional_disk", False):
            connection_info["use_additional_disk"] = True

        return connection_info

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """Return ports required by Exasol system."""
        return {
            "Exasol Database": 8563,
            "Exasol BucketFS": 6583,
            "Exasol Admin UI": 2443,
            "Exasol SSH": 20002,
        }

    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """Get Exasol connection string with full CLI command."""
        port = self.setup_config.get("port", 8563)
        username = self.setup_config.get("username", "sys")
        schema = self.setup_config.get("schema", "benchmark")
        return f"exaplus -c {public_ip}:{port} -u {username} -p <password> -s {schema}"

    def __init__(
        self,
        config: dict[str, Any],
        output_callback: Callable[[str], None] | None = None,
        workload_config: dict[str, Any] | None = None,
    ):
        super().__init__(config, output_callback, workload_config)
        self.setup_method = self.setup_config.get("method", "docker")
        self.container_name = f"exasol_{self.name}"
        self.license_file = self.setup_config.get("license_file")
        self.cluster_config = self.setup_config.get("cluster", {})

        # Override data_dir if using additional disk (no data dir needed)
        if self.setup_config.get("use_additional_disk", False):
            self.data_dir = None  # No data directory needed when using raw disk

        # Connection settings
        # For installer method, use external host and db_password
        if self.setup_method == "installer":
            # Resolve environment variables in host addresses
            host_external_addrs = self.setup_config.get("host_external_addrs")
            if host_external_addrs:
                # Resolve environment variable like $EXASOL_PUBLIC_IP
                if host_external_addrs.startswith("$"):
                    var_name = host_external_addrs[1:]
                    resolved_ip = self._resolve_ip_address(var_name)
                    host_external_addrs = (
                        resolved_ip if resolved_ip else host_external_addrs
                    )

                # Use first external IP (handle both comma and space-separated lists)
                self.host = host_external_addrs.replace(",", " ").split()[0]
            else:
                self.host = self.setup_config.get("host", "localhost")
            self.password = self.setup_config.get("db_password", "exasol")
        else:
            self.host = self.setup_config.get("host", "localhost")
            self.password = self.setup_config.get("password", "exasol")

        self.port = self.setup_config.get("port", 8563)
        self.username = self.setup_config.get("username", "sys")
        self.schema = self.setup_config.get("schema", "benchmark")

        self._connection = None
        self._schema_created = False
        self._cloud_instance_manager = (
            None  # Primary node (node 0) for single-node or multinode
        )
        self._cloud_instance_managers: list[Any] = (
            []
        )  # All nodes for multinode clusters
        self._external_host = None  # Initialize for cloud instance external IP
        self._certificate_fingerprint: str | None = (
            None  # Cache for TLS certificate fingerprint
        )

        # Storage for partitioned disk information
        self._data_generation_mount_point: str | None = None
        self._exasol_raw_partition: str | None = None
        self.data_device: str | None = None  # Storage device path for Exasol

    def _resolve_ip_address(self, var_name: str) -> str | None:
        """Resolve IP address from configuration or infrastructure state."""
        from typing import cast

        from benchkit.infra.manager import InfraManager

        # Use infrastructure manager to resolve IP addresses
        result = InfraManager.resolve_ip_from_infrastructure(var_name, self.name)
        return cast(str | None, result)

    def _connect_with_fingerprint_retry(
        self, dsn: str, user: str, password: str, **kwargs: Any
    ) -> pyexasol.ExaConnection:
        """
        Connect to Exasol with automatic TLS certificate fingerprint handling.

        For localhost connections, disables SSL verification.
        For remote connections, tries normal connection first, then extracts
        fingerprint from error and retries if certificate error occurs.
        """
        import re
        import ssl

        # Check if this is a localhost connection
        is_localhost = dsn.startswith("localhost") or dsn.startswith("127.0.0.1")

        try:
            # First attempt - normal connection
            connection_kwargs = kwargs.copy()
            connection_kwargs["autocommit"] = True

            # Disable SSL certificate verification for benchmarks (security not critical)
            connection_kwargs["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}

            return pyexasol.connect(
                dsn=dsn, user=user, password=password, **connection_kwargs
            )
        except Exception as e:
            error_msg = str(e)

            # For localhost, if SSL error persists, try without SSL completely
            if is_localhost and ("SSL" in error_msg or "certificate" in error_msg):
                self._log(
                    "SSL error on localhost, attempting connection without SSL verification"
                )
                connection_kwargs["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}
                return pyexasol.connect(
                    dsn=dsn, user=user, password=password, **connection_kwargs
                )

            # Check if this is a certificate/PKIX error for remote connections
            if (
                "PKIX path building failed" in error_msg
                or "unable to find valid certification path" in error_msg
                or "TLS connection to host" in error_msg
            ):
                # Extract fingerprint from error message
                # Patterns to try:
                # 1. "fingerprint in the connection string: hostname/FINGERPRINT"
                # 2. "localhost/FINGERPRINT"
                # 3. "hostname:port/FINGERPRINT"
                patterns = [
                    r"connection string: [^/]+/([A-F0-9]+)",  # Original pattern
                    r"localhost/([A-F0-9]+)",  # Direct localhost pattern
                    r"[^/]+:?\d*/([A-F0-9]+)",  # Host:port/fingerprint pattern
                ]

                fingerprint_match = None
                for pattern in patterns:
                    fingerprint_match = re.search(pattern, error_msg)
                    if fingerprint_match:
                        break

                if fingerprint_match:
                    fingerprint = fingerprint_match.group(1)
                    if fingerprint is None:
                        self._certificate_fingerprint = ""
                    else:
                        self._certificate_fingerprint = fingerprint

                    # Build DSN with fingerprint
                    if "/" in dsn:
                        # Already has fingerprint or other suffix
                        dsn_with_fingerprint = dsn
                    else:
                        dsn_with_fingerprint = f"{dsn}/{fingerprint}"

                    self._log(
                        f"TLS certificate issue detected, retrying with fingerprint: {dsn_with_fingerprint}"
                    )

                    # Retry with fingerprint
                    return pyexasol.connect(
                        dsn=dsn_with_fingerprint, user=user, password=password, **kwargs
                    )
                else:
                    # Certificate error but couldn't extract fingerprint
                    self._log(
                        f"Certificate error but couldn't extract fingerprint: {error_msg}"
                    )
                    raise
            else:
                # Some other error, re-raise
                raise

    def _build_dsn(self, host: str, port: int) -> str:
        """Build DSN with cached fingerprint if available."""
        dsn = f"{host}:{port}"
        if self._certificate_fingerprint:
            dsn = f"{dsn}/{self._certificate_fingerprint}"
        return dsn

    def _schema_exists(self, conn: Any, schema_name: str | None = None) -> bool:
        """Return True if the given schema exists."""
        target_schema = schema_name or self.schema
        if not target_schema:
            return False

        normalized = target_schema.upper()
        safe_schema = normalized.replace("'", "''")

        query = (
            "SELECT 1 FROM sys.exa_schemas "
            f"WHERE UPPER(schema_name) = '{safe_schema}' LIMIT 1"
        )

        try:
            result = conn.execute(query)
            row = result.fetchone() if result else None
            return row is not None
        except Exception:
            return False

    @exclude_from_package
    def _estimate_tpch_data_size_gb(self, scale_factor: int) -> int:
        """
        Estimate TPC-H data generation size in GB.

        TPC-H SF1 generates approximately 1GB of data.
        We add 20% safety margin and enforce minimum 3GB.

        Args:
            scale_factor: TPC-H scale factor

        Returns:
            Estimated data size in GB
        """

        # SF1 ≈ 1GB, add 20% safety margin
        # estimated_gb = max(int(scale_factor * 1.3), 3)
        def scale_multiplier(sf: float) -> float:
            # 2.0 at very small sf (≈1–10), ~1.6 at 30, →1.3 for sf ≥ 100
            # f(sf) = 1.3 + 0.7 / (1 + (sf/K)^p), with K≈26.8537, p≈2.5966
            if sf <= 10:
                return 2.0
            val = 1.3 + 0.7 / (1.0 + (sf / 26.853725639548) ** 2.5965770266157073)
            return float(max(1.3, min(val, 2.0)))

        def estimate_gb(sf: float) -> int:
            return int(max(sf * scale_multiplier(sf), 3.0))

        return estimate_gb(float(scale_factor))

    @exclude_from_package
    def _detect_exasol_disk(self, allow_mounted: bool = False) -> str | None:
        """
        Detect additional disk for Exasol using base class helper.

        If RAID was created in _setup_database_storage(), returns the RAID device.
        Otherwise detects available storage devices.

        Args:
            allow_mounted: If True, return disk even if already mounted

        Returns:
            Device path (e.g., '/dev/nvme1n1' or '/dev/md0') or None if not found
        """
        # If we already set up a base device (possibly RAID), use that
        if hasattr(self, "_exasol_base_device") and self._exasol_base_device:
            self._log(
                f"Using previously configured Exasol device: {self._exasol_base_device}"
            )
            return self._exasol_base_device

        # Otherwise detect available devices
        devices = self._detect_storage_devices(skip_root=True)

        if not devices:
            self._log("Warning: No additional disk found for Exasol")
            return None

        # Return first available device
        for device in devices:
            # If allow_mounted, or device is not mounted, return it
            if allow_mounted or not device["mounted_at"]:
                # Prefer stable_path for multinode consistency, fallback to path
                disk_path = device.get("stable_path", device["path"])
                self._log(f"Detected additional disk for Exasol: {disk_path}")
                return disk_path

        # All devices are mounted and allow_mounted is False
        if not allow_mounted:
            self._log("Warning: All additional disks are mounted")
            # Return first device anyway (caller will handle unmounting)
            # Prefer stable_path for multinode consistency, fallback to path
            return devices[0].get("stable_path", devices[0]["path"])

        return None

    @exclude_from_package
    def _setup_partitioned_disk(
        self, scale_factor: int
    ) -> tuple[str | None, str | None]:
        """
        Partition additional disk for TPC-H data generation and Exasol storage.

        Creates two partitions:
        1. ext4 partition for TPC-H data generation (sized based on scale factor)
        2. Raw partition for Exasol database storage (remaining space)

        Args:
            scale_factor: TPC-H scale factor for size estimation

        Returns:
            Tuple of (data_generation_mount_point, exasol_raw_partition_path)
            Returns (None, None) if partitioning fails
        """
        self._log(
            "Setting up partitioned disk for data generation and Exasol storage..."
        )

        # Step 1: Detect additional disk
        detected_disk = self._detect_exasol_disk(allow_mounted=True)
        if not detected_disk:
            self._log("No additional disk available for partitioning")
            return None, None

        # Step 1.5: Check if disk is already partitioned
        # If partitions exist, use them instead of re-partitioning
        check_partitions_result = self.execute_command(
            f"lsblk -ln -o NAME {detected_disk} | tail -n +2", record=False
        )

        if check_partitions_result.get("success", False):
            existing_partitions = (
                check_partitions_result.get("stdout", "").strip().split("\n")
            )
            # Filter out empty lines
            existing_partitions = [p.strip() for p in existing_partitions if p.strip()]

            if len(existing_partitions) >= 2:
                self._log(
                    f"✓ Disk {detected_disk} already has partitions, checking if they're usable..."
                )

                # Determine partition device names
                # NVMe and RAID (md) devices use 'p' notation
                if "nvme" in detected_disk or "md" in detected_disk:
                    data_partition_dev = f"{detected_disk}p1"
                    exasol_partition_dev = f"{detected_disk}p2"
                else:
                    data_partition_dev = f"{detected_disk}1"
                    exasol_partition_dev = f"{detected_disk}2"

                # Check if data partition is mounted
                data_mount_point = "/data/tpch_gen"
                check_mount_result = self.execute_command(
                    f"mount | grep {data_partition_dev}", record=False
                )

                if (
                    check_mount_result.get("success", False)
                    and check_mount_result.get("stdout", "").strip()
                ):
                    # Already mounted
                    self._log(
                        f"✓ Data partition {data_partition_dev} is already mounted at {data_mount_point}"
                    )
                    self._log(f"✓ Exasol partition {exasol_partition_dev} is ready")
                    self._log("✓ Skipping partitioning - using existing setup")
                    return data_mount_point, exasol_partition_dev
                else:
                    # Partitions exist but not mounted, try to mount
                    self._log(
                        f"✓ Partitions exist, attempting to mount {data_partition_dev}..."
                    )

                    # Create mount point if it doesn't exist
                    self.execute_command(
                        f"sudo mkdir -p {data_mount_point}", record=False
                    )

                    # Try to mount existing partition
                    mount_existing = self.execute_command(
                        f"sudo mount {data_partition_dev} {data_mount_point}",
                        record=False,
                    )

                    if mount_existing.get("success", False):
                        # Set ownership
                        self.execute_command(
                            f"sudo chown -R $(whoami):$(whoami) {data_mount_point}",
                            record=False,
                        )
                        self._log(
                            f"✓ Successfully mounted existing partition at {data_mount_point}"
                        )
                        self._log(f"✓ Exasol partition {exasol_partition_dev} is ready")
                        self._log("✓ Skipping partitioning - using existing setup")
                        return data_mount_point, exasol_partition_dev
                    else:
                        self._log(
                            "⚠ Could not mount existing partition, will repartition..."
                        )

        # Step 2: Unmount disk if mounted
        devices = self._detect_storage_devices(skip_root=True)
        device_info = next((d for d in devices if d["path"] == detected_disk), None)

        if device_info and device_info["mounted_at"]:
            self._log(
                f"Disk {detected_disk} is mounted at {device_info['mounted_at']}, unmounting..."
            )
            if not self._unmount_disk(detected_disk):
                self._log(f"Failed to unmount {detected_disk}")
                return None, None

        # Step 3: Get disk size
        disk_size_result = self.execute_command(
            f"lsblk -bdn -o SIZE {detected_disk}", record=False
        )
        if not disk_size_result.get("success", False):
            self._log(f"Failed to get disk size for {detected_disk}")
            return None, None

        disk_size_bytes = int(disk_size_result.get("stdout", "0").strip())
        disk_size_gb = disk_size_bytes // (1024**3)
        self._log(f"Detected disk size: {disk_size_gb} GB")

        # Step 4: Calculate partition sizes
        data_partition_gb = self._estimate_tpch_data_size_gb(scale_factor)
        exasol_partition_gb = disk_size_gb - data_partition_gb

        if exasol_partition_gb < 10:
            self._log(
                f"Error: Not enough space for Exasol partition (would be {exasol_partition_gb}GB)"
            )
            self._log("Minimum 10GB required for Exasol")
            return None, None

        self._log("Partition plan:")
        self._log(
            f"  - Data generation partition: {data_partition_gb} GB (for TPC-H SF{scale_factor})"
        )
        self._log(f"  - Exasol raw partition: {exasol_partition_gb} GB")

        # Step 5: Create partition table using parted
        self.record_setup_command(
            f"sudo parted {detected_disk} mklabel gpt",
            "Create GPT partition table",
            "storage_setup",
        )
        parted_result = self.execute_command(
            f"sudo parted -s {detected_disk} mklabel gpt",
            record=True,
            category="storage_setup",
        )
        if not parted_result.get("success", False):
            self._log("Failed to create partition table")
            return None, None

        # Step 6: Create data generation partition (partition 1)
        data_partition_end_gb = data_partition_gb
        self.record_setup_command(
            f"sudo parted {detected_disk} mkpart primary ext4 1MiB {data_partition_end_gb}GiB",
            f"Create {data_partition_gb}GB partition for data generation",
            "storage_setup",
        )
        data_part_result = self.execute_command(
            f"sudo parted -s {detected_disk} mkpart primary ext4 1MiB {data_partition_end_gb}GiB",
            record=True,
            category="storage_setup",
        )
        if not data_part_result.get("success", False):
            self._log("Failed to create data generation partition")
            return None, None

        # Step 7: Create Exasol raw partition (partition 2)
        self.record_setup_command(
            f"sudo parted {detected_disk} mkpart primary {data_partition_end_gb}GiB 100%",
            f"Create raw partition for Exasol ({exasol_partition_gb}GB)",
            "storage_setup",
        )
        exasol_part_result = self.execute_command(
            f"sudo parted -s {detected_disk} mkpart primary {data_partition_end_gb}GiB 100%",
            record=True,
            category="storage_setup",
        )
        if not exasol_part_result.get("success", False):
            self._log("Failed to create Exasol partition")
            return None, None

        # Step 8: Wait for partition devices to appear
        import time

        time.sleep(2)

        # Determine partition device names
        # NVMe and RAID (md) devices use 'p' prefix for partitions
        if "nvme" in detected_disk or "md" in detected_disk:
            data_partition_dev = f"{detected_disk}p1"
            exasol_partition_dev = f"{detected_disk}p2"
        else:
            data_partition_dev = f"{detected_disk}1"
            exasol_partition_dev = f"{detected_disk}2"

        # Step 9: Create filesystem on data generation partition
        if not self._format_disk(data_partition_dev, filesystem="ext4"):
            self._log("Failed to create filesystem on data generation partition")
            return None, None

        # Step 10: Mount data generation partition
        data_mount_point = "/data/tpch_gen"
        if not self._mount_disk(data_partition_dev, data_mount_point):
            self._log("Failed to mount data generation partition")
            return None, None

        # Step 11: Set ownership for data generation directory
        self._set_ownership(data_mount_point, owner="$(whoami):$(whoami)")

        self.record_setup_note(
            f"Partitioned disk {detected_disk}: "
            f"{data_partition_gb}GB for data generation, "
            f"{exasol_partition_gb}GB raw for Exasol"
        )

        self._log("✓ Successfully partitioned disk:")
        self._log(f"  - Data generation: {data_partition_dev} → {data_mount_point}")
        self._log(f"  - Exasol storage: {exasol_partition_dev} (raw)")

        return data_mount_point, exasol_partition_dev

    @exclude_from_package
    def _setup_database_storage(self, scale_factor: int) -> bool:
        """
        Override base class to setup partitioned disk for Exasol.

        This is called when use_additional_disk is True in the config.
        Exasol requires partitioned storage for data generation and raw disk.

        For Exasol, we:
        1. Detect local instance store devices
        2. Create RAID0 if multiple local devices
        3. Defer partitioning until workload scale factor is known

        For multinode clusters, this runs on ALL nodes.

        Returns:
            True if successful, False otherwise
        """
        # For multinode, we need to setup storage on ALL nodes
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            self._log(
                f"Setting up storage on all {len(self._cloud_instance_managers)} nodes..."
            )
            return self._setup_multinode_storage(scale_factor)

        # Single node setup - use the same logic
        return self._setup_single_node_storage(scale_factor)

    @exclude_from_package
    def _setup_multinode_storage(self, scale_factor: int) -> bool:
        """
        Setup storage on all nodes in a multinode cluster.
        Each node gets its own RAID0 and partitioned disk.
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
                success = self._setup_single_node_storage(scale_factor)
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
    def _setup_single_node_storage(self, scale_factor: int) -> bool:
        """
        Setup storage on a single node. Used by both single-node and multinode setups.
        This contains the actual storage setup logic.
        """
        # Check if /data is already mounted
        check_mount = self.execute_command("mount | grep ' /data '", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            self._log("    ✓ Storage already configured, skipping")
            return True

        # Detect local instance store devices first
        local_devices = self._detect_storage_devices(
            skip_root=True, device_filter="local"
        )

        device_to_use = None

        if len(local_devices) > 1:
            # Multiple local instance store devices → create RAID0
            self._log(
                f"    Detected {len(local_devices)} local instance store devices, creating RAID0..."
            )

            # Check if RAID already exists
            raid_device = "/dev/md0"
            raid_check = self.execute_command(
                f"test -b {raid_device} && echo 'exists'", record=False
            )

            if raid_check.get("success", False) and "exists" in raid_check.get(
                "stdout", ""
            ):
                self._log(f"    RAID array {raid_device} already exists")
                device_to_use = raid_device
            else:
                # Create RAID0 from all local devices
                device_paths = [d["path"] for d in local_devices]
                if self._create_raid0(device_paths, raid_device):
                    device_to_use = raid_device
                else:
                    self._log(
                        "    Warning: RAID0 creation failed, falling back to first device"
                    )
                    device_to_use = local_devices[0]["path"]

        elif len(local_devices) == 1:
            # Single local instance store device
            device_to_use = local_devices[0]["path"]
            self._log(
                f"    Detected single local instance store device: {device_to_use}"
            )

        else:
            # No local devices
            self._log("    No local instance store devices found")
            all_devices = self._detect_storage_devices(skip_root=True)

            if not all_devices:
                self._log("    Warning: No additional storage devices found")
                return False

            device_to_use = all_devices[0]["path"]
            self._log(f"    Using EBS device: {device_to_use}")

        # Store device for later use
        self._exasol_base_device = device_to_use

        # Partition the disk
        data_mount_point, exasol_partition = self._setup_partitioned_disk(scale_factor)

        # Store partition paths
        if data_mount_point:
            self._data_generation_mount_point = data_mount_point
        if exasol_partition:
            self._exasol_raw_partition = exasol_partition

        return True

    @exclude_from_package
    def prepare_data_directory(self) -> bool:
        """Prepare data directory for the database (skip if using additional disk)."""
        if self.data_dir is None:
            # Using additional disk, no data directory needed
            return True
        return super().prepare_data_directory()

    @exclude_from_package
    def get_setup_summary(self) -> dict[str, Any]:
        """Get setup summary with Exasol-specific data_device field."""
        summary = super().get_setup_summary()
        # Add data_device field if it was set during installation
        if hasattr(self, "data_device") and self.data_device:
            summary["data_device"] = str(self.data_device)
        return summary

    def _create_storage_symlink(self, target_device: str) -> str:
        """
        Create a consistent symlink for Exasol storage across all nodes.

        This solves the multinode problem where different nodes may have
        different device names (nvme0n1 vs nvme1n1) or different by-id paths.
        By creating a consistent symlink path in /dev, all nodes can use the same
        configuration in c4. The /dev directory is visible inside containers.

        Args:
            target_device: The actual device path (e.g., /dev/nvme1n1p2 or /dev/md0)
                         Note: Each node will have its own actual device, but this
                         is typically the path on the primary node used as reference.

        Returns:
            The symlink path to use in configuration

        Examples:
            Node 0: /dev/exasol.storage -> /dev/disk/by-id/nvme-...-part2
            Node 3: /dev/exasol.storage -> /dev/disk/by-id/nvme-...-part2
            Config: CCC_HOST_DATADISK=/dev/exasol.storage (same on all!)
        """
        symlink_path = "/dev/exasol.storage"

        # Determine if multinode and get list of nodes
        is_multinode = (
            self._cloud_instance_managers and len(self._cloud_instance_managers) > 1
        )

        if is_multinode:
            # Multinode: Create symlink on ALL nodes
            self._log(
                f"Creating storage symlink on {len(self._cloud_instance_managers)} nodes..."
            )

            for idx, mgr in enumerate(self._cloud_instance_managers):
                self._log(f"  Node {idx}: Setting up storage symlink...")

                # Detect the actual device on THIS node (may differ from primary node)
                # This detection happens remotely on each node
                detect_cmd = """
# Find the instance store device (not root disk) using stable by-id path
INSTANCE_STORE=$(
    # Find Instance_Storage devices (exclude _1 namespace variants, prefer shortest path)
    for byid in $(ls -1 /dev/disk/by-id/ 2>/dev/null | grep 'Instance_Storage' | grep -v '_1' | grep -v -- '-part'); do
        # Check if this device or its partition 2 exists
        if [ -b "/dev/disk/by-id/${byid}-part2" ]; then
            echo "/dev/disk/by-id/${byid}-part2"
            break
        elif [ -b "/dev/disk/by-id/${byid}" ]; then
            echo "/dev/disk/by-id/${byid}"
            break
        fi
    done | head -1
)

# If detection failed, fall back to provided device (shouldn't happen)
if [ -z "$INSTANCE_STORE" ]; then
    INSTANCE_STORE="%s"
fi

# Create symlink in /dev (no directory creation needed - /dev already exists)
sudo rm -f %s
sudo ln -sf "$INSTANCE_STORE" %s

echo "Symlink: %s -> $INSTANCE_STORE"
""" % (
                    target_device,
                    symlink_path,
                    symlink_path,
                    symlink_path,
                )

                result = mgr.run_remote_command(detect_cmd, debug=False)
                if result.get("success", False):
                    output = result.get("stdout", "").strip()
                    self._log(f"  Node {idx}: {output}")
                else:
                    self._log(
                        f"  Node {idx}: Warning - Failed to create symlink, may use direct path"
                    )

            self.record_setup_note(
                f"Created storage symlinks on all {len(self._cloud_instance_managers)} nodes: {symlink_path}"
            )
            return symlink_path

        else:
            # Single node: Create symlink locally in /dev
            # Remove existing symlink if present
            self.execute_command(
                f"sudo rm -f {symlink_path}",
                record=False,
            )

            # Create symlink in /dev (no directory creation needed - /dev already exists)
            self.record_setup_command(
                f"sudo ln -sf {target_device} {symlink_path}",
                f"Create storage symlink: {symlink_path} -> {target_device}",
                "storage_setup",
            )
            symlink_result = self.execute_command(
                f"sudo ln -sf {target_device} {symlink_path}",
                record=True,
                category="storage_setup",
            )

            if symlink_result.get("success", False):
                self._log(
                    f"✓ Created storage symlink: {symlink_path} -> {target_device}"
                )
                return symlink_path
            else:
                self._log(
                    f"Warning: Failed to create symlink, using direct path: {target_device}"
                )
                return target_device

    def get_data_generation_directory(self, workload: Any) -> Path | None:
        """
        Get directory for TPC-H data generation.

        Priority order:
        1. If data_dir explicitly specified in config → use that
        2. If use_additional_disk=true → use /data/tpch_gen for data generation
        3. Otherwise → use default local path (None)

        Args:
            workload: The workload object (for scale factor)

        Returns:
            Path to data generation directory, or None for default
        """
        # Priority 1: If data_dir is explicitly configured, use it for data generation
        explicit_data_dir = self.setup_config.get("data_dir")
        if explicit_data_dir:
            data_gen_path = (
                Path(str(explicit_data_dir))
                / "tpch_gen"
                / workload.name
                / f"sf{workload.scale_factor}"
            )
            self._log(
                f"Exasol: Using configured data_dir for data generation: {data_gen_path}"
            )
            return cast(Path, data_gen_path)

        # Priority 2: If use_additional_disk=true, use /data/tpch_gen for data generation
        use_additional_disk = self.setup_config.get("use_additional_disk", False)
        if use_additional_disk:
            # Use shared /data/tpch_gen for TPC-H data generation
            tpch_gen_dir = "/data/tpch_gen"

            # Create directory with proper ownership
            self.execute_command(
                f"sudo mkdir -p {tpch_gen_dir} && sudo chown -R $(whoami):$(whoami) {tpch_gen_dir}",
                record=False,
            )

            # Store for potential later use
            if self._data_generation_mount_point is None:
                self._data_generation_mount_point = tpch_gen_dir

            data_gen_path = (
                Path(tpch_gen_dir) / workload.name / f"sf{workload.scale_factor}"
            )
            self._log(
                f"Exasol: Using additional disk for data generation: {data_gen_path}"
            )
            return cast(Path, data_gen_path)

        # Priority 3: Use default local path
        return None

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """Check if Exasol is already installed and running."""
        if self.setup_method == "docker":
            raise ValueError("docker install method not implementd yet")
        elif self.setup_method == "installer":
            self._log("Checking if Exasol is already installed and running...")

            # First check for installation marker file
            if not self.has_install_marker():
                self._log("No existing Exasol installation marker found")
                return False

            self._log("Found existing Exasol installation marker")

            # Check if c4 is available and working
            c4_check = self.execute_command("which c4", record=False)
            if not c4_check.get("success", False):
                self._log(
                    "⚠ Installation marker found but c4 not available, will reinstall"
                )
                return False

            self._log("✓ c4 command available")

            # Check if c4 service is running
            service_check = self.execute_command(
                "systemctl is-active c4_cloud_command", record=False
            )
            if not service_check.get("success", False):
                self._log(
                    "⚠ c4_cloud_command service not running, will restart cluster"
                )
                return False

            self._log("✓ c4_cloud_command service is active")

            # Most importantly: Check if the database is actually accessible
            self._log("Checking if Exasol database is accessible...")
            if self.is_healthy(quiet=False):
                self._log("✓ Exasol database is accessible and healthy")
                return True
            else:
                self._log(
                    "⚠ Exasol installation exists but database not accessible, will restart"
                )
                return False

        return False

    def _get_connection(self) -> Any:
        """Get a connection to Exasol database using pyexasol."""
        connection_params = {
            "dsn": self._build_dsn(self.host, self.port),
            "user": self.username,
            "password": self.password,
            "compression": True,
        }

        # Only specify schema if it has been created
        if hasattr(self, "_schema_created") and self._schema_created and self.schema:
            connection_params["schema"] = self.schema

        return self._connect_with_fingerprint_retry(**connection_params)

    @exclude_from_package
    def install(self) -> bool:
        """Install Exasol using the configured method."""
        self.prepare_data_directory()

        if self.setup_method == "docker":
            return self._install_docker()
        elif self.setup_method == "installer":
            return self._install_native()
        elif self.setup_method == "preinstalled":
            return self._verify_preinstalled()
        else:
            self._log(f"Unknown setup method: {self.setup_method}")
            return False

    @exclude_from_package
    def _install_docker(self) -> bool:
        """Install Exasol using Docker."""
        # Record setup notes
        self.record_setup_note("Installing Exasol using Docker container")

        if self.data_dir:
            # Create data directory first
            self.record_setup_command(
                f"sudo mkdir -p {self.data_dir}",
                "Create Exasol data directory",
                "preparation",
            )
            self.record_setup_command(
                f"sudo chown $(whoami):$(whoami) {self.data_dir}",
                "Set data directory permissions",
                "preparation",
            )
        else:
            self.record_setup_note(
                "Using additional NVMe disk for storage (no data directory)"
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
        ]

        # Add data directory mount only if using file storage
        if self.data_dir:
            docker_cmd.extend(["-v", f"{self.data_dir}:/exa/data"])

        docker_cmd.extend(
            [
                "-p",
                "8563:8563",  # Database port
                "-p",
                "6583:6583",  # BucketFS port
            ]
        )

        # Add environment variables
        docker_cmd.extend(["-e", "EXA_PRIVILEGED=yes"])

        if self.license_file and Path(self.license_file).exists():
            docker_cmd.extend(["-v", f"{self.license_file}:/exa/etc/license.xml:ro"])
            self.record_setup_note(f"Using license file: {self.license_file}")

        # Use specified Docker image version
        image_tag = self.version if self.version != "latest" else "latest"
        docker_cmd.append(f"exasol/docker-db:{image_tag}")

        # Record and execute the docker run command
        full_cmd = " ".join(docker_cmd)
        result = self.execute_command(full_cmd)
        if not result["success"]:
            self._log(f"Failed to start Exasol container: {result['stderr']}")
            return False

        # Record configuration applied
        extra_config = self.setup_config.get("extra", {})
        if extra_config:
            self.record_setup_note("Exasol configuration applied:")
            for key, value in extra_config.items():
                self.record_setup_note(f"  {key}: {value}")

        # Wait for container to be ready
        self._log("Waiting for Exasol to start...")
        return self.wait_for_health(max_attempts=60, delay=5.0)

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install Exasol using c4 native installer."""
        assert (
            self.setup_method == "installer"
        ), f"Expected setup_method 'installer', got '{self.setup_method}'"

        self.record_setup_note("Installing Exasol using c4 native installer")

        # Get configuration from setup_config
        c4_version = self.setup_config.get("c4_version", "2025.1.4")

        # Build IP address lists for multinode support
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            # Multinode: build space-separated IP lists from instance managers (c4 expects spaces, not commas)
            private_ips = [mgr.private_ip for mgr in self._cloud_instance_managers]
            public_ips = [mgr.public_ip for mgr in self._cloud_instance_managers]
            host_addrs = " ".join(private_ips)
            host_external_addrs = " ".join(public_ips)
            self._log(
                f"Multinode setup with {len(self._cloud_instance_managers)} nodes:"
            )
            self._log(f"  Private IPs: {host_addrs}")
            self._log(f"  Public IPs: {host_external_addrs}")
        else:
            # Single node: use configured addresses or resolve from environment
            host_addrs = self._resolve_ip_addresses(
                self.setup_config.get("host_addrs", "localhost")
            )
            host_external_addrs = self._resolve_ip_addresses(
                self.setup_config.get("host_external_addrs", host_addrs)
            )

        image_password = self.setup_config.get("image_password", "exasol123")
        db_password = self.setup_config.get("db_password", "exasol456")
        admin_password = self.setup_config.get("admin_password", "exasol789")
        working_copy = self.setup_config.get("working_copy", f"@exasol-{self.version}")
        storage_disk_size = self.setup_config.get("storage_disk_size", "100GB")

        try:
            # Step 0: Handle license file if specified and copy to remote system
            remote_license_path = None
            if self.license_file and Path(self.license_file).exists():
                self.record_setup_note(
                    f"Using Exasol license file: {self.license_file}"
                )

                if self._cloud_instance_manager:
                    # Copy license file to remote system
                    remote_license_path = "/tmp/exasol.license"
                    self.record_setup_note(
                        f"Copying license file to remote system: {remote_license_path}"
                    )

                    if not self._cloud_instance_manager.copy_file_to_instance(
                        Path(self.license_file), remote_license_path
                    ):
                        self._log("Failed to copy license file to remote instance")
                        return False
                else:
                    remote_license_path = self.license_file

            # Step 1: Create exasol user on ALL nodes (for multinode)
            node_count = (
                len(self._cloud_instance_managers)
                if self._cloud_instance_managers
                else 1
            )
            node_info = f"all_nodes_{node_count}" if node_count > 1 else None

            self.record_setup_command(
                "sudo useradd -m exasol",
                "Create Exasol system user",
                "user_setup",
                node_info=node_info,
            )
            if not self.execute_command_on_all_nodes(
                "sudo useradd -m exasol || true",
                description="Creating exasol user on all nodes",
            ):
                self._log("Warning: Failed to create exasol user on some nodes")

            self.record_setup_command(
                "sudo usermod -aG sudo exasol",
                "Add exasol user to sudo group",
                "user_setup",
                node_info=node_info,
            )
            if not self.execute_command_on_all_nodes(
                "sudo usermod -aG sudo exasol || true",
                description="Adding exasol to sudo group on all nodes",
            ):
                self._log("Warning: Failed to add exasol to sudo group on some nodes")

            # Setup passwordless sudo on ALL nodes
            if not self.execute_command_on_all_nodes(
                'sudo sed -i "/%sudo/s/) ALL$/) NOPASSWD: ALL/" /etc/sudoers',
                description="Configuring passwordless sudo on all nodes",
            ):
                self._log(
                    "Warning: Failed to configure passwordless sudo on some nodes"
                )

            self.record_setup_command(
                "sudo passwd exasol",
                "Set password for exasol user (interactive)",
                "user_setup",
            )
            # Note: We don't actually execute passwd as it's interactive

            # Step 2: Setup storage disk
            use_additional_disk = self.setup_config.get("use_additional_disk", False)
            if use_additional_disk:
                # Check if disk was already partitioned by get_data_generation_directory
                if self._exasol_raw_partition:
                    # Use the partitioned raw disk
                    actual_device_path = self._exasol_raw_partition

                    # Create consistent symlink for multinode compatibility
                    storage_disk_path = self._create_storage_symlink(actual_device_path)
                    self.data_device = storage_disk_path  # Store for report display

                    # Note: lsblk is just for verification, not needed for reproduction
                    self.record_setup_note(
                        f"Using partitioned raw disk: {actual_device_path} (via {storage_disk_path})"
                    )
                    self._log(
                        f"✓ Using pre-partitioned raw disk for Exasol: {actual_device_path} (via {storage_disk_path})"
                    )
                else:
                    # Fall back to detecting and using full disk (old behavior)
                    detected_disk = self._detect_exasol_disk(allow_mounted=True)
                    if detected_disk:
                        # Get device info to check mount status
                        devices = self._detect_storage_devices(skip_root=True)
                        device_info = next(
                            (d for d in devices if d["path"] == detected_disk), None
                        )

                        # Check if disk is mounted and unmount it
                        if device_info and device_info["mounted_at"]:
                            self._log(
                                f"Disk {detected_disk} is mounted at {device_info['mounted_at']}, unmounting..."
                            )
                            if not self._unmount_disk(detected_disk):
                                self._log(
                                    f"Error: Could not unmount {detected_disk} from {device_info['mounted_at']}"
                                )
                                self._log("Falling back to file storage")
                                use_additional_disk = False

                        if (
                            use_additional_disk
                        ):  # Still using additional disk after potential unmount
                            # Create consistent symlink for multinode compatibility
                            # (works for both single disk and RAID device like /dev/md0)
                            storage_disk_path = self._create_storage_symlink(
                                detected_disk
                            )
                            self.data_device = (
                                storage_disk_path  # Store for report display
                            )

                            self.record_setup_command(
                                f"lsblk {detected_disk}",
                                f"Using additional disk: {detected_disk} (via {storage_disk_path})",
                                "storage_setup",
                            )
                            self.record_setup_note(
                                f"Using additional disk: {detected_disk} (via {storage_disk_path})"
                            )
                    else:
                        self._log(
                            "Warning: No suitable additional disk found, falling back to file storage"
                        )
                        use_additional_disk = False

            if not use_additional_disk:
                # Fallback: Create data directory and storage disk file with loopback device
                storage_disk_size = self.setup_config.get("storage_disk_size", "100GB")
                data_dir = self.setup_config.get("data_dir", "/tmp/exasol_storage")
                storage_file_path = f"{data_dir}/storage_disk1"

                # Determine if multinode
                is_multinode = (
                    self._cloud_instance_managers
                    and len(self._cloud_instance_managers) > 1
                )
                node_info = (
                    f"all_nodes_{len(self._cloud_instance_managers)}"
                    if is_multinode
                    else None
                )

                # Step 2a: Create data directory on all nodes
                self.record_setup_command(
                    f"sudo mkdir -p {data_dir}",
                    "Create Exasol data directory",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"sudo mkdir -p {data_dir}",
                    description="Creating data directory on all nodes",
                ):
                    self._log("Failed to create data directory on some nodes")
                    return False

                # Step 2b: Create storage file on all nodes
                self.record_setup_command(
                    f"sudo truncate -s {storage_disk_size} {storage_file_path}",
                    f"Create {storage_disk_size} storage disk file",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"sudo truncate -s {storage_disk_size} {storage_file_path}",
                    description="Creating storage file on all nodes",
                ):
                    self._log("Failed to create storage file on some nodes")
                    return False

                # Step 2c: Set ownership on all nodes
                self.record_setup_command(
                    f"sudo chown -R exasol:exasol {data_dir}",
                    "Set ownership of data directory to exasol user",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"sudo chown -R exasol:exasol {data_dir}",
                    description="Setting ownership on all nodes",
                ):
                    self._log(
                        "Warning: Failed to set ownership on some nodes, continuing..."
                    )

                # Step 2d: Setup loopback device on all nodes
                # Use losetup --find --show to find first available loop device
                # and create a consistent symlink for c4 config
                exasol_storage_link = "/dev/exasol.storage"

                # First, detach any existing setup for this storage file
                self.record_setup_command(
                    f"sudo losetup -d $(losetup -j {storage_file_path} | cut -d: -f1) 2>/dev/null || true",
                    "Detach existing loopback for storage file if present",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"sudo losetup -d $(losetup -j {storage_file_path} | cut -d: -f1) 2>/dev/null || true",
                    description="Detaching existing loopback on all nodes",
                ):
                    self._log("Warning: Failed to detach loopback on some nodes")

                # Remove old symlink if exists
                self.record_setup_command(
                    f"sudo rm -f {exasol_storage_link}",
                    "Remove old storage symlink if present",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"sudo rm -f {exasol_storage_link}",
                    description="Removing old symlink on all nodes",
                ):
                    self._log("Warning: Failed to remove old symlink on some nodes")

                # Setup loopback device using --find --show to get first available
                # Then create consistent symlink for c4 config
                losetup_cmd = (
                    f"LOOP_DEV=$(sudo losetup --find --show {storage_file_path}) && "
                    f"sudo ln -sf $LOOP_DEV {exasol_storage_link} && "
                    f"echo $LOOP_DEV"
                )
                self.record_setup_command(
                    f"sudo losetup --find --show {storage_file_path} && "
                    f"sudo ln -sf <loop_device> {exasol_storage_link}",
                    f"Setup loopback device for storage file with symlink {exasol_storage_link}",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    losetup_cmd,
                    description="Setting up loopback device on all nodes",
                ):
                    self._log("Failed to setup loopback device on some nodes")
                    return False

                # Verify loopback setup
                self.record_setup_command(
                    f"ls -la {exasol_storage_link} && sudo losetup -a | grep {storage_file_path}",
                    "Verify loopback device setup",
                    "storage_setup",
                    node_info=node_info,
                )
                if not self.execute_command_on_all_nodes(
                    f"ls -la {exasol_storage_link} && sudo losetup -a | grep {storage_file_path}",
                    description="Verifying loopback setup on all nodes",
                ):
                    self._log("Warning: Could not verify loopback setup on some nodes")

                # Use consistent symlink for c4 config
                storage_disk_path = exasol_storage_link
                self.data_device = f"{storage_file_path} (via {exasol_storage_link})"  # For report display

            # Step 3: Download c4 tool
            c4_url = f"https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/{c4_version}/c4"
            self.record_setup_command(
                f"wget {c4_url} -O c4 && chmod +x c4",
                f"Download c4 cluster management tool v{c4_version}",
                "tool_setup",
            )
            result = self.execute_command(f"wget {c4_url} -O c4 && chmod +x c4")
            if not result["success"]:
                self._log(f"Failed to download c4: {result['stderr']}")
                return False

            # Step 4: Generate SSH key on primary node and distribute to ALL nodes
            self.record_setup_command(
                'ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""',
                "Generate SSH key pair for cluster communication",
                "ssh_setup",
            )
            # Generate SSH key on primary node
            self.execute_command(
                'test -e ~/.ssh/id_rsa || ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""',
                record=False,
            )

            # Get the public key from primary node
            pub_key_result = self.execute_command("cat ~/.ssh/id_rsa.pub", record=False)
            if not pub_key_result["success"]:
                self._log("Failed to read SSH public key")
                return False
            pub_key = pub_key_result["stdout"].strip()

            # Distribute SSH public key to ALL nodes (including primary)
            self._log(
                f"Distributing SSH key to all {len(self._cloud_instance_managers)} nodes..."
            )
            for idx, mgr in enumerate(self._cloud_instance_managers):
                # Create .ssh directory and add authorized_keys for exasol user
                setup_cmd = f"sudo mkdir -p ~exasol/.ssh && echo '{pub_key}' | sudo tee ~exasol/.ssh/authorized_keys > /dev/null && sudo chown -R exasol:exasol ~exasol/.ssh && sudo chmod 700 ~exasol/.ssh && sudo chmod 600 ~exasol/.ssh/authorized_keys"
                result = mgr.run_remote_command(setup_cmd, timeout=60)
                if result.get("success"):
                    self._log(f"  ✓ SSH key installed on node {idx}")
                else:
                    self._log(f"  ✗ Failed to install SSH key on node {idx}")
                    return False

            # Test SSH connectivity from primary to all nodes
            self._log("Testing SSH connectivity to all nodes...")
            host_list = host_addrs.split()  # Split on whitespace
            for idx, host in enumerate(host_list):
                result = self.execute_command(
                    f"ssh -o StrictHostKeyChecking=no exasol@{host} sudo uptime",
                    record=False,
                )
                if result["success"]:
                    self._log(f"  ✓ SSH connectivity confirmed to node {idx} ({host})")
                else:
                    self._log(f"  ✗ Failed SSH connectivity to node {idx} ({host})")
                    return False

            # Step 5: Create c4 configuration file on remote system
            # Note: For multinode, IP addresses are space-separated lists,
            # and storage paths are the same on all nodes
            config_content = f"""CCC_HOST_ADDRS="{host_addrs}"
CCC_HOST_EXTERNAL_ADDRS="{host_external_addrs}"
CCC_HOST_DATADISK={storage_disk_path}
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD={image_password}
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY={working_copy}
CCC_PLAY_DB_PASSWORD={db_password}
CCC_PLAY_ADMIN_PASSWORD={admin_password}"""

            # Only add mounts when using file storage, not raw disk
            # Mount path is the same on all nodes (c4 applies it to each node)
            if not use_additional_disk:
                config_content += f"\nCCC_PLAY_MOUNTS={data_dir}:{data_dir}"

            config_content += "\nCCC_ADMINUI_START_SERVER=true"

            self.record_setup_note("C4 Configuration file content:")
            for line in config_content.split("\n"):
                # Sanitize sensitive values in configuration content
                sanitized_line = self._sanitize_command_for_report(line)
                self.record_setup_note(f"  {sanitized_line}")

            # Create config file on remote system using tee (more reliable over SSH than heredoc)
            remote_config_path = "/tmp/exasol_c4.conf"
            # Use tee with proper escaping for SSH transmission
            escaped_config = (
                config_content.replace("\\", "\\\\")
                .replace("$", "\\$")
                .replace("`", "\\`")
                .replace('"', '\\"')
            )
            create_config_cmd = (
                f'echo "{escaped_config}" | tee {remote_config_path} > /dev/null'
            )

            self.record_setup_command(
                f"cat > {remote_config_path} << 'EOF'\n{self._sanitize_command_for_report(config_content)}\nEOF",
                "Create c4 configuration file on remote system",
                "configuration",
            )
            result = self.execute_command(create_config_cmd)
            if not result["success"]:
                self._log(
                    f"Failed to create config file on remote system: {result.get('stderr', 'Unknown error')}"
                )
                return False

            # Step 6: Deploy Exasol cluster
            self.record_setup_command(
                f"./c4 host play -i {remote_config_path}",
                "Deploy Exasol cluster using c4",
                "cluster_deployment",
            )
            result = self.execute_command(
                f"./c4 host play -i {remote_config_path}", timeout=1800
            )  # 30 min timeout

            if not result["success"]:
                self._log(f"C4 cluster deployment failed: {result['stderr']}")
                return False

            self.record_setup_note("Exasol cluster deployment initiated")

            # Update connection parameters for deployed cluster
            if host_external_addrs and host_external_addrs != "localhost":
                external_host = host_external_addrs.split()[0]  # Use first external IP
            else:
                external_host = host_addrs.split()[0]  # Use first internal IP

            # Set host based on context:
            # - External IP for health checks from local machine
            # - localhost for benchmark execution on remote machine
            if self._cloud_instance_manager:
                self._external_host = (
                    external_host  # Store external IP for health checks
                )
                self.host = "localhost"  # Use localhost for benchmark execution
            else:
                self.host = external_host

            self.username = "sys"
            self.password = db_password
            self.port = 8563

            self.record_setup_note(
                f"Database will be accessible at: {self.host}:{self.port}"
            )
            self.record_setup_note("Admin UI will be available (if enabled)")

            # Step 7: Wait for cluster to be ready
            self.record_setup_note(
                "Waiting for Exasol cluster to be ready for connections..."
            )
            self._log("Waiting for Exasol cluster to be ready...")
            if not self.wait_for_health(
                max_attempts=120, delay=10.0
            ):  # Wait up to 20 minutes
                self._log("Exasol cluster failed to become ready within timeout")
                return False

            self.record_setup_note(
                "✓ Exasol cluster is ready and accepting connections"
            )

            # Step 8: Get cluster play_id for confd_client operations
            play_id = self._get_cluster_play_id()
            if not play_id:
                self._log("Could not get cluster play ID")
                return False
            self._log(f"Got play ID {play_id}")

            # Step 8a: Cleanup disturbing services (not recorded in report)
            self._log("Step 8a: Cleaning up interfering services...")
            cleanup_success = self._cleanup_disturbing_services(play_id)
            if cleanup_success:
                self._log("✓ Service cleanup completed successfully")
            else:
                self._log("⚠ Service cleanup failed or no services to remove")

            # Step 8b: Install license file if specified
            if remote_license_path:
                self._log("Installing license file...")
                self._install_license_file(play_id, remote_license_path)
                self._log("✓ License file installation completed")

            # Step 8b: Configure database parameters if specified
            extra_config = self.setup_config.get("extra", {})
            db_params = extra_config.get("db_params", [])
            if db_params:
                self._log(
                    f"Configuring database parameters ({len(db_params)} parameters)..."
                )
                self._configure_database_parameters(play_id, db_params)
                self._log("✓ Database parameter configuration completed")

            # Record other applied configuration parameters
            if extra_config:
                self.record_setup_note("Additional configuration parameters applied:")
                for key, value in extra_config.items():
                    if key != "db_params":  # Skip db_params as we handled them above
                        self.record_setup_note(f"  {key}: {value}")

            # Mark that system is installed
            self.mark_installed(record=False)
            self._log("✓ Exasol installation completed successfully")

            return True

        except Exception as e:
            self._log(f"Native Exasol installation failed: {e}")
            return False

    def _verify_preinstalled(self) -> bool:
        """Verify that Exasol is already installed and accessible."""
        return self.is_healthy()

    def start(self) -> bool:
        """Start the Exasol system."""
        self._log(f"Starting {self.name} system using {self.setup_method} method...")

        if self.setup_method == "docker":
            result = self.execute_command(f"docker start {self.container_name}")
            if result["success"]:
                self._log(
                    f"Docker container started, waiting for {self.name} to be healthy..."
                )
                return self.wait_for_health()
            self._log(f"Failed to start Docker container for {self.name}")
            return False
        else:
            # For native installations, check if already healthy first
            self._log(f"Connection details: {self.host}:{self.port} as {self.username}")
            self._log("Performing initial health check...")
            if self.is_healthy(quiet=False):
                self._log(f"✓ {self.name} is already healthy and ready")
                return True

            # If not healthy, check if c4 service is running
            self._log("Database not accessible, checking c4 service status...")
            service_check = self.execute_command(
                "systemctl is-active c4_cloud_command", record=False
            )
            if service_check.get("success", False):
                self._log(
                    "✓ c4_cloud_command service is running, waiting for database..."
                )
                # Service is running, just wait for health
                success = self.wait_for_health(max_attempts=60, delay=5.0)
                if success:
                    self._log(f"✓ {self.name} is healthy and ready")
                else:
                    self._log(f"✗ {self.name} failed to become healthy after 5 minutes")
                    # Try one final health check with verbose output to see the exact error
                    self._log("Final health check with detailed error:")
                    self.is_healthy(quiet=False)
                return success
            else:
                self._log(
                    "⚠ c4_cloud_command service not running, attempting to restart cluster..."
                )
                # Need to restart the cluster
                return self._restart_existing_cluster()

    def _restart_existing_cluster(self) -> bool:
        """Restart an existing Exasol cluster that has been installed but not running."""
        self._log("Attempting to restart existing Exasol cluster...")

        # Find the existing config file
        config_check = self.execute_command(
            "find /tmp -name 'exasol_c4.conf' -type f | head -1", record=False
        )
        if (
            not config_check.get("success", False)
            or not config_check.get("stdout", "").strip()
        ):
            self._log("⚠ No existing c4 config file found, cannot restart cluster")
            self._log("   This likely means the cluster was never fully deployed")
            return False

        config_path = config_check.get("stdout", "").strip()
        self._log(f"Found existing config file: {config_path}")

        # Try to restart using the existing config
        self._log("Restarting cluster with existing configuration...")
        result = self.execute_command(
            f"./c4 host play -i {config_path}",
            timeout=900,  # 15 min timeout for restart (shorter than full install)
        )

        if not result["success"]:
            self._log(
                f"Failed to restart cluster: {result.get('stderr', 'Unknown error')}"
            )
            return False

        self._log(
            "Cluster restart initiated, waiting for database to become healthy..."
        )
        success = self.wait_for_health(max_attempts=60, delay=5.0)
        if success:
            self._log(f"✓ {self.name} cluster restarted successfully")
        else:
            self._log(f"✗ {self.name} cluster restart failed - database not healthy")

        return success

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if Exasol is running and accepting connections."""
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

            dsn = self._build_dsn(health_check_host, self.port)
            if not quiet:
                self._log(f"Connecting to Exasol at {dsn} as {self.username}...")

            conn = self._connect_with_fingerprint_retry(
                dsn=dsn,
                user=self.username,
                password=self.password,
                compression=True,
            )

            if not quiet:
                self._log("Connection established, testing with SELECT 1...")

            # Test connection with simple query
            conn.execute("SELECT 1")
            conn.close()

            if not quiet:
                self._log("Health check successful")
            return True

        except Exception as e:
            if not quiet:
                self._log(f"Health check failed: {e}")
                self._log(
                    f"Connection details: host={self.host}, port={self.port}, user={self.username}"
                )
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a schema in Exasol."""
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        result = self.execute_query(sql, query_name=f"create_schema_{schema_name}")
        success = bool(result.get("success", False))

        if success and self.schema and schema_name.upper() == self.schema.upper():
            self._schema_created = True

        return success

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into Exasol table using pyexasol import_from_file."""
        schema_name = kwargs.get("schema", "benchmark")
        columns = kwargs.get("columns", None)

        conn = None

        try:
            conn = self._get_connection()
            if not conn:
                return False
            if not self._schema_created:
                if self._schema_exists(conn, schema_name):
                    self._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            # Import parameters for TPC-H .tbl format (pipe-delimited)
            import_params = {
                "column_separator": "|",
                "columns": columns,
                "csv_cols": [f"1..{len(columns)}"] if columns else None,
            }

            # Remove None values
            import_params = {k: v for k, v in import_params.items() if v is not None}

            self._log(f"Loading {data_path} into {table_name}...")
            conn.import_from_file(
                str(data_path), table=table_name, import_params=import_params
            )

            # Verify data was loaded
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a SQL query in Exasol using pyexasol.

        Note: timeout parameter is accepted for interface compatibility but not
        currently used by Exasol (pyexasol manages its own timeouts).
        """
        from ..debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        timer_obj: Timer | None = None

        try:
            conn = None
            schema_to_use = self.schema

            try:
                conn = self._get_connection()
                if schema_to_use:
                    if not self._schema_created:
                        if self._schema_exists(conn, schema_to_use):
                            self._schema_created = True
                            conn.execute(f"OPEN SCHEMA {schema_to_use}")

                debug_print(f"Executing query: {query_name}")
                if len(query) > 200:
                    debug_print(f"SQL: {query[:200]}...")
                else:
                    debug_print(f"SQL: {query}")

                with Timer(f"Query {query_name}") as timer:
                    timer_obj = timer

                    # Strip SQL comments and whitespace to detect query type
                    query_stripped = query.strip()
                    # Remove leading single-line comments
                    while query_stripped.startswith("--"):
                        # Find the end of the comment line
                        newline_pos = query_stripped.find("\n")
                        if newline_pos == -1:
                            query_stripped = ""
                            break
                        query_stripped = query_stripped[newline_pos + 1 :].strip()

                    is_select_query = query_stripped.upper().startswith(
                        ("SELECT", "WITH")
                    )
                    debug_print(f"Is SELECT/WITH: {is_select_query}")

                    if is_select_query:
                        if return_data:
                            # Export result data as pandas DataFrame
                            import pandas as pd

                            result = conn.execute(query)
                            data = result.fetchall() if result else []
                            columns = result.columns() if result else []
                            df = pd.DataFrame(data, columns=columns)
                            rows_returned = len(df)
                        else:
                            result = conn.execute(query)
                            rows_returned = len(result.fetchall()) if result else 0
                            df = None
                    else:
                        conn.execute(query)
                        rows_returned = (
                            conn.rowcount() if hasattr(conn, "rowcount") else 0
                        )
                        df = None

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
                elif return_data:
                    debug_print(f"return_data={return_data}, but df is None")

                return response

            finally:
                if conn:
                    if schema_to_use:
                        try:
                            self._schema_created = self._schema_exists(
                                conn, schema_to_use
                            )
                        except Exception:
                            pass
                    conn.close()

        except Exception as e:
            return {
                "success": False,
                "elapsed_s": timer_obj.elapsed if timer_obj else 0,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get Exasol-specific performance metrics using pyexasol."""
        metrics: dict[str, Any] = {}

        try:
            # Query system tables for metrics
            system_queries = {
                "sessions": "SELECT COUNT(*) FROM EXA_ALL_SESSIONS WHERE STATUS = 'EXECUTE'",
                "memory_usage": "SELECT * FROM EXA_SYSTEM_EVENTS WHERE EVENT_TYPE = 'MEMORY' ORDER BY MEASURE_TIME DESC LIMIT 1",
                "cache_stats": "SELECT * FROM EXA_STATISTICS.EXA_DB_SIZE_DAILY ORDER BY SNAPSHOT_ID DESC LIMIT 1",
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
        """Clean up Exasol installation."""
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

        # Clean up data directory if requested
        if self.setup_config.get("cleanup_data", False):
            success = success and self.cleanup_data_directory()

        return success

    def get_version_info(self) -> dict[str, str]:
        """Get detailed version information using pyexasol."""
        version_info = {"configured_version": self.version}

        try:
            # Get actual database version using pyexasol
            result = self.execute_query(
                "SELECT PARAM_VALUE FROM EXA_METADATA WHERE PARAM_NAME = 'databaseProductVersion'",
                query_name="get_version",
            )
            if result["success"]:
                version_info["actual_version"] = "version_retrieved_via_pyexasol"

            # Also get pyexasol version info
            version_info["pyexasol_version"] = getattr(
                pyexasol, "__version__", "unknown"
            )

        except Exception as e:
            version_info["version_error"] = str(e)

        return version_info

    @exclude_from_package
    def _resolve_ip_addresses(self, ip_config: str) -> str:
        """Resolve IP address placeholders with actual values from infrastructure."""
        if not ip_config:
            return "localhost"

        # Handle environment variable substitution
        if ip_config.startswith("$"):
            env_var = ip_config[1:]  # Remove $ prefix
            resolved = os.environ.get(env_var, ip_config)
            self.record_setup_note(f"Resolved {ip_config} to {resolved}")
            return resolved

        # If it's already an IP address, return as-is
        return ip_config

    @exclude_from_package
    def _get_cluster_play_id(self) -> str | None:
        """Get the cluster play_id from c4 ps command."""
        self.record_setup_command(
            "c4 ps",
            "Get cluster play ID for confd_client operations",
            "cluster_management",
        )

        ps_result = self.execute_command("c4 ps", timeout=30)
        if ps_result["success"]:
            # Parse the play_id from the first data line (skip header)
            lines = ps_result.get("stdout", "").strip().split("\n")
            if len(lines) >= 2:
                # Split the first data line and get the PLAY_ID (second column)
                play_id: str = lines[1].split()[1]
                self.record_setup_note(f"Found cluster play ID: {play_id}")
                return play_id
            else:
                self.record_setup_note(
                    "⚠ Warning: Could not parse play ID from c4 ps output"
                )
                return None
        else:
            self.record_setup_note(
                f"⚠ Warning: Failed to get cluster info: {ps_result.get('stderr', 'Unknown error')}"
            )
            return None

    @exclude_from_package
    def _execute_confd_client_command(
        self,
        play_id: str,
        confd_command: str,
        description: str,
        category: str = "configuration",
        silent: bool = False,
    ) -> bool:
        """Execute a confd_client command through c4 connect."""
        # Build the full c4 connect command
        full_cmd = f"c4 connect -s cos -i {play_id} -- {confd_command}"

        if not silent:
            self.record_setup_command(confd_command, description, category)

        result = self.execute_command(full_cmd, timeout=300)
        return bool(result.get("success", False))

    @exclude_from_package
    def _install_license_file(self, play_id: str, license_file_path: str) -> None:
        """Install Exasol license file using c4 connect."""
        self.record_setup_note("Installing Exasol license...")

        # Build the license upload command
        license_cmd = f"cat {license_file_path} | c4 connect -s cos -i {play_id} -- confd_client license_upload license: '\"{{< -}}\"'"

        # Record the license command for report
        self.record_setup_command(
            "confd_client license_upload license: <LICENSE_CONTENT>",
            "Install Exasol license file",
            "license_setup",
        )

        license_result = self.execute_command(license_cmd, timeout=120)
        if license_result["success"]:
            self.record_setup_note("Exasol license installed successfully")
        else:
            self.record_setup_note(
                f"Warning: License installation failed: {license_result.get('stderr', 'Unknown error')}"
            )

    @exclude_from_package
    def _configure_database_parameters(
        self, play_id: str, db_params: list[str]
    ) -> None:
        """Configure Exasol database parameters using c4 connect."""
        self.record_setup_note("Configuring Exasol database parameters...")
        self._log(f"Configuring {len(db_params)} database parameters: {db_params}")

        # Step 1: Stop the database before parameter configuration
        self.record_setup_note("Stopping database for parameter configuration...")
        stop_command = "confd_client db_stop db_name: Exasol"

        self.record_setup_command(
            stop_command,
            "Stop Exasol database for parameter configuration",
            "database_tuning",
        )

        self._log("Stopping database for parameter configuration...")
        if not self._execute_confd_client_command(
            play_id,
            stop_command,
            "Stop Exasol database for parameter configuration",
            "database_tuning",
        ):
            self.record_setup_note(
                "⚠ Warning: Failed to stop database for parameter configuration"
            )
            self._log("✗ Failed to stop database")
            return
        else:
            self._log("✓ Database stopped successfully")

        # Step 2: Configure database parameters
        params_with_quotes = ["'" + param + "'" for param in db_params]
        params_str = ",".join(params_with_quotes)
        # Need additional quotes when passing through c4 connect
        params_command = (
            f'confd_client db_configure db_name: Exasol params_add: "[{params_str}]"'
        )

        self.record_setup_command(
            params_command,
            "Configure Exasol database parameters for analytical workload optimization",
            "database_tuning",
        )

        self._log(f"Configuring database with parameters: {params_str}")
        if not self._execute_confd_client_command(
            play_id,
            params_command,
            "Configure Exasol database parameters for analytical workload optimization",
            "database_tuning",
        ):
            self.record_setup_note("Warning: Database parameter configuration failed")
            self._log("✗ Failed to configure database parameters")
            return
        else:
            self._log("✓ Database parameters configured successfully")

        # Step 3: Start the database (capture command in report for transparency)
        self.record_setup_note("Starting database with new parameters...")
        start_command = "confd_client db_start db_name: Exasol"

        self._log("Starting database with new parameters...")
        if not self._execute_confd_client_command(
            play_id,
            start_command,
            "Starting database with new parameters",
            "database_tuning",
        ):
            self.record_setup_note(
                "⚠ Warning: Failed to start database after parameter configuration"
            )
            self._log("✗ Failed to start database after parameter configuration")
            return
        else:
            self._log("✓ Database start command completed")

        # Step 4: Wait for database to be fully initialized
        self.record_setup_note("Waiting for database to be fully initialized...")
        self._log("Waiting for database to be fully initialized...")
        if self._wait_for_database_ready(play_id):
            self.record_setup_note(
                "✓ Database parameters configured and database started successfully"
            )
            self._log("✓ Database is fully ready after parameter configuration")
        else:
            self.record_setup_note(
                "⚠ Warning: Database started but initialization check failed"
            )
            self._log(
                "✗ Database initialization check failed after parameter configuration"
            )

    @exclude_from_package
    def _wait_for_database_ready(
        self, play_id: str, max_attempts: int = 60, delay: int = 5
    ) -> bool:
        """Wait for database to be fully initialized and connectable."""
        import time

        for attempt in range(max_attempts):
            # Check if stage6 is complete
            check_cmd = f'c4 connect -s cos -i {play_id} -- tail /exa/logs/cored/exainit.log | grep "stage6: All stages finished."'

            result = self.execute_command(check_cmd, timeout=30, record=False)
            stage6_complete = result.get(
                "success", False
            ) and "stage6: All stages finished." in result.get("stdout", "")

            # Check if database is connectable
            db_connectable = self.is_healthy(quiet=True)

            # Both conditions must be met
            if stage6_complete and db_connectable:
                return True

            if attempt < max_attempts - 1:
                time.sleep(delay)

        return False

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
            self.host = "localhost"

            # For preinstalled systems, update credentials from config
            # Use db_password if specified (what c4 installer uses), otherwise keep current password
            db_password = self.setup_config.get("db_password")
            if db_password:
                self.password = db_password

    def execute_command_on_all_nodes(
        self,
        command: str,
        timeout: float | None = None,
        description: str | None = None,
    ) -> bool:
        """
        Execute a command on all nodes in a multinode cluster.

        Args:
            command: Command to execute
            timeout: Timeout in seconds
            description: Description for logging

        Returns:
            True if command succeeded on all nodes, False otherwise
        """
        if not self._cloud_instance_managers:
            # Fallback to single node execution
            result = self.execute_command(command, timeout=timeout, record=False)
            return bool(result.get("success", False))

        if description:
            self._log(
                f"{description} (on {len(self._cloud_instance_managers)} nodes)..."
            )

        all_success = True
        for idx, mgr in enumerate(self._cloud_instance_managers):
            result = mgr.run_remote_command(
                command, timeout=int(timeout) if timeout else 300
            )
            if not result.get("success", False):
                self._log(
                    f"  ✗ Failed on node {idx}: {result.get('stderr', 'Unknown error')}"
                )
                all_success = False
            else:
                self._log(f"  ✓ Success on node {idx}")

        return all_success

    def execute_command(
        self,
        command: str,
        timeout: float | None = None,
        record: bool = True,
        category: str = "setup",
        node_info: str | None = None,
    ) -> dict[str, Any]:
        """Execute a command, either locally or remotely depending on setup."""
        if self._cloud_instance_manager:
            # Execute on remote instance (primary node for multinode)
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

    @exclude_from_package
    def _cleanup_disturbing_services(self, play_id: str) -> bool:
        """
        Cleanup services that could disturb benchmark execution.
        Removes rapid, eventd, and healthd services using cosrm command.
        This is not recorded in the report as it's internal cleanup.
        """
        self._log(
            "🧹 Cleaning up services that could interfere with benchmark performance..."
        )
        self._log("   Targeting services: rapid, eventd, healthd")

        try:
            # Step 1: Get list of running services with cosps
            cosps_result = self.execute_command(
                f"c4 connect -s cos -i {play_id} -- cosps", timeout=30, record=False
            )

            if not cosps_result.get("success", False):
                self._log(
                    f"⚠ Warning: Could not get service list: {cosps_result.get('stderr', '')}"
                )
                return False

            cosps_output = cosps_result.get("stdout", "")
            self._log("📝 Current Exasol services:")
            # Only show relevant lines to avoid clutter
            for line in cosps_output.split("\n")[:10]:  # Show first 10 lines
                if line.strip():
                    self._log(f"   {line}")
            if len(cosps_output.split("\n")) > 10:
                self._log("   ... (truncated)")
            self._log("")

            # Step 2: Parse output to find service IDs for rapid, eventd, healthd
            services_to_remove = ["rapid", "eventd", "healthd"]
            service_ids = {}

            for line in cosps_output.split("\n"):
                line = line.strip()
                if (
                    not line
                    or line.startswith("ROOT")
                    or line.startswith("--")
                    or line.startswith("ID")
                ):
                    continue

                parts = line.split()
                if len(parts) >= 7:  # Make sure line has enough parts
                    service_id = parts[0]
                    service_name = parts[6] if len(parts) > 6 else ""

                    for target_service in services_to_remove:
                        if target_service in service_name:
                            service_ids[target_service] = service_id
                            break

            if service_ids:
                self._log(
                    f"🎯 Found interfering services to remove: {list(service_ids.keys())}"
                )
            else:
                self._log("✓ No interfering services found (this is good!)")
                return True

            # Step 3: Remove each identified service
            removed_count = 0
            for service_name, service_id in service_ids.items():
                self._log(f"   🗑️  Removing {service_name} (ID: {service_id})...")
                remove_result = self.execute_command(
                    f"c4 connect -s cos -i {play_id} -- cosrm -a {service_id}",
                    timeout=30,
                    record=False,  # Don't record cleanup in report
                )

                if remove_result.get("success", False):
                    self._log(f"      ✅ Successfully removed {service_name}")
                    removed_count += 1
                else:
                    self._log(
                        f"      ❌ Failed to remove {service_name}: {remove_result.get('stderr', '')}"
                    )

            self._log(
                f"🧹 Service cleanup summary: {removed_count}/{len(service_ids)} services removed"
            )

            if removed_count == len(service_ids):
                self._log("✅ All interfering services successfully removed!")
                return True
            elif removed_count > 0:
                self._log("⚠️ Some services removed, but some failures occurred")
                return True
            else:
                self._log("❌ Failed to remove any interfering services")
                return False

        except Exception as e:
            self._log(f"❌ Service cleanup failed with exception: {e}")
            return False
