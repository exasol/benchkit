"""Exasol database system implementation."""

from __future__ import annotations

import ssl
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pyexasol  # type: ignore

from benchkit.common import DataFormat, exclude_from_package

from ...util import Timer
from ..base import SystemUnderTest

if TYPE_CHECKING:
    # avoid cyclic dependency problems
    from ...workloads import Workload
    from .cluster import ExasolClusterManager
    from .data import ExasolDataLoader
    from .native import ExasolNativeInstaller


class ExasolSystem(SystemUnderTest):
    """Exasol database system implementation."""

    # Exasol supports multinode clusters via c4 tool
    SUPPORTS_MULTINODE = True
    # streaming import implemented using pyexasol
    SUPPORTS_STREAMLOAD = True
    # Efficient parallel loading - slightly faster than baseline
    LOAD_TIMEOUT_MULTIPLIER = 0.8

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by Exasol system."""
        return ["pyexasol>=0.25.0"]

    def get_storage_config(self) -> tuple[str | None, str]:
        """Return Exasol-specific storage configuration.

        Exasol manages its own storage via c4 tool using raw disk partitions.
        Returns None for subdirectory to skip subdirectory creation.
        """
        return None, "root:root"

    @classmethod
    def validate_setup(
        cls, setup_config: dict[str, Any], name: str, node_count: int = 1
    ) -> None:
        """Validate Exasol-specific setup configuration.

        Args:
            setup_config: Setup configuration dictionary
            name: System name (for error messages)
            node_count: Number of nodes (for multinode validation)

        Raises:
            ValueError: If validation fails
        """
        method = setup_config.get("method", "")

        # Installer method requires specific fields
        if method == "installer":
            required_fields = ["c4_version", "image_password", "db_password"]
            missing = [f for f in required_fields if not setup_config.get(f)]
            if missing:
                raise ValueError(
                    f"System '{name}': Exasol installer method requires: "
                    f"{', '.join(missing)}"
                )

            # Validate db_mem_size if provided
            db_mem_size = setup_config.get("db_mem_size")
            if db_mem_size is not None:
                if not isinstance(db_mem_size, int):
                    raise ValueError(
                        f"System '{name}': db_mem_size must be an integer "
                        f"(in MB), got {type(db_mem_size).__name__}"
                    )
                min_mem_per_node = 4000  # 4GB in MB
                min_total_mem = node_count * min_mem_per_node
                if db_mem_size < min_total_mem:
                    raise ValueError(
                        f"System '{name}': db_mem_size must be at least "
                        f"{min_mem_per_node}MB per node. With {node_count} node(s), "
                        f"minimum is {min_total_mem}MB (got {db_mem_size}MB)"
                    )

    @classmethod
    def _get_connection_defaults(cls) -> dict[str, Any]:
        return {
            "port": 8563,
            "username": "sys",
            "password": "exasol",
            "schema_key": "schema",
            "schema": "benchmark",
        }

    @classmethod
    def _get_password_key(cls, setup_config: dict[str, Any]) -> str:
        return (
            "db_password" if setup_config.get("method") == "installer" else "password"
        )

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """Return ports required by Exasol system."""
        return {
            "Exasol Database": 8563,
            "Exasol BucketFS": 6583,
            "Exasol Admin UI": 2443,
            "Exasol SSH": 20002,
        }

    @exclude_from_package
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

        # Include project_id in container name for parallel project isolation
        project_id = config.get("project_id", "")
        if project_id:
            self.container_name = f"exasol_{project_id}_{self.name}"
        else:
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
        self._certificate_fingerprint: str | None = (
            None  # Cache for TLS certificate fingerprint
        )

        # Storage for partitioned disk information
        self._data_generation_mount_point: str | None = None
        self._exasol_raw_partition: str | None = None
        self.data_device: str | None = None  # Storage device path for Exasol

        # Lazy-initialized helper classes for extracted functionality
        self._native_installer: ExasolNativeInstaller | None = None
        self._cluster_manager: ExasolClusterManager | None = None
        self._data_loader: ExasolDataLoader | None = None

    @property
    def native_installer(self) -> ExasolNativeInstaller:
        """Get or create the native installer helper."""
        if self._native_installer is None:
            from benchkit.systems.exasol.native import ExasolNativeInstaller

            self._native_installer = ExasolNativeInstaller(self)
        return self._native_installer

    @property
    def cluster_manager(self) -> ExasolClusterManager:
        """Get or create the cluster manager helper."""
        if self._cluster_manager is None:
            from benchkit.systems.exasol.cluster import ExasolClusterManager

            self._cluster_manager = ExasolClusterManager(self)
        return self._cluster_manager

    @property
    def data_loader(self) -> ExasolDataLoader:
        """Get or create the data loader helper."""
        if self._data_loader is None:
            from benchkit.systems.exasol.data import ExasolDataLoader

            self._data_loader = ExasolDataLoader(self)
        return self._data_loader

    def _resolve_ip_address(self, var_name: str) -> str | None:
        """Resolve IP address from configuration or infrastructure state."""
        try:
            from benchkit.infra.manager import InfraManager

            # Use infrastructure manager to resolve IP addresses
            project_id = self.config.get("project_id", "")
            result = InfraManager.resolve_ip_from_infrastructure(
                var_name, self.name, project_id
            )
            return cast(str | None, result)
        except ImportError:
            # In minimal packages, InfraManager isn't available
            # Return None to use fallback value
            return None

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

        # Check if this is a localhost connection
        is_localhost = dsn.startswith("localhost") or dsn.startswith("127.0.0.1")

        kwargs = {
            **kwargs,
            "autocommit": True,
            "websocket_sslopt": {"cert_reqs": ssl.CERT_NONE},
        }
        try:
            return pyexasol.connect(dsn=dsn, user=user, password=password, **kwargs)
        except Exception as e:
            error_msg = str(e)

            # For localhost, if SSL error persists, try without SSL completely
            if is_localhost and ("SSL" in error_msg or "certificate" in error_msg):
                self._log(
                    "SSL error on localhost, attempting connection without SSL verification"
                )
                kwargs["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}
                return pyexasol.connect(dsn=dsn, user=user, password=password, **kwargs)

            # Check for certificate/PKIX error and extract fingerprint
            if any(
                x in error_msg for x in ["PKIX", "certification path", "TLS connection"]
            ):
                for pattern in [
                    r"connection string: [^/]+/([A-F0-9]+)",
                    r"localhost/([A-F0-9]+)",
                    r"[^/]+:?\d*/([A-F0-9]+)",
                ]:
                    if m := re.search(pattern, error_msg):
                        self._certificate_fingerprint = m.group(1) or ""
                        return pyexasol.connect(
                            dsn=(
                                f"{dsn}/{self._certificate_fingerprint}"
                                if "/" not in dsn
                                else dsn
                            ),
                            user=user,
                            password=password,
                            **kwargs,
                        )
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
        self, workload: Workload
    ) -> tuple[str | None, str | None]:
        """
        Partition additional disk for workload data generation and Exasol storage.

        Creates two partitions:
        1. ext4 partition for workload data generation
        2. Raw partition for Exasol database storage (remaining space)

        Args:
            workload: The Workload reference for size estimation

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
                data_mount_point = "/data"
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
        data_partition_gb = workload.estimate_filesystem_usage_gb(self)
        exasol_partition_gb = disk_size_gb - data_partition_gb

        if exasol_partition_gb < 10:
            self._log(
                f"Error: Not enough space for Exasol partition (would be {exasol_partition_gb}GB)"
            )
            self._log("Minimum 10GB required for Exasol")
            return None, None

        self._log("Partition plan:")
        self._log(
            f"  - Data generation partition: {data_partition_gb} GB (for {workload.display_name()})"
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
        data_mount_point = "/data"
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
    def _setup_database_storage(self, workload: Workload) -> bool:
        """
        Override base class to set up partitioned disk for Exasol.

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
        # For multinode, we need to set up storage on ALL nodes
        if self._cloud_instance_managers and len(self._cloud_instance_managers) > 1:
            self._log(
                f"Setting up storage on all {len(self._cloud_instance_managers)} nodes..."
            )
            return self._setup_multinode_storage(workload)

        # Single node setup - use the same logic
        return self._setup_single_node_storage(workload)

    @exclude_from_package
    def _setup_single_node_storage(self, workload: Workload) -> bool:
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
        data_mount_point, exasol_partition = self._setup_partitioned_disk(workload)

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

    @exclude_from_package
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
# Determine storage device based on type
TARGET_DEV="%s"

# RAID devices: use directly (naming is consistent across nodes: /dev/md0, /dev/md0p2)
if [[ "$TARGET_DEV" =~ ^/dev/md[0-9]+ ]]; then
    INSTANCE_STORE="$TARGET_DEV"

# EBS/attached volumes: use directly (naming is consistent via Terraform)
elif [[ "$TARGET_DEV" =~ ^/dev/(xvd|sd)[a-z] ]]; then
    INSTANCE_STORE="$TARGET_DEV"

# Single local NVMe: need Instance_Storage detection (device naming may differ between nodes)
else
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
    # Fallback if detection fails
    if [ -z "$INSTANCE_STORE" ]; then
        INSTANCE_STORE="$TARGET_DEV"
    fi
fi

# Create symlink in /dev (no directory creation needed - /dev already exists)
sudo rm -f %s
sudo ln -sf "$INSTANCE_STORE" %s

echo "Symlink: %s -> $INSTANCE_STORE"
""" % (  # noqa: UP031
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
        """Get directory for TPC-H data generation (uses base class, adds caching)."""
        result = super().get_data_generation_directory(workload)
        if result and self._data_generation_mount_point is None:
            self._data_generation_mount_point = str(
                result.parent.parent.parent
            )  # Cache /data
        return result

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

    def _get_connection(
        self,
        compression: bool = True,
        skip_schema: bool = False,
        disable_query_cache: bool = True,
    ) -> Any:
        """Get a connection to Exasol database using pyexasol.

        Args:
            compression: Whether to enable compression (default True)
            skip_schema: If True, don't include schema in connection params.
                        Use this when creating schemas to avoid chicken-and-egg
                        problem where we try to connect TO the schema we're creating.
            disable_query_cache: If True, disable query result cache for accurate
                        benchmarking. Exasol's query cache can return cached results
                        instantly, making benchmark times invalid. Default True.
        """
        # Build extra kwargs for the connection
        extra_kwargs: dict[str, Any] = {"compression": compression}

        # Use active schema if set (from workload), else fall back to instance schema
        # _active_schema is set by workload.run_workload() for thread-safe multi-stream
        # Skip schema when creating schemas to avoid "schema not found" errors
        if not skip_schema:
            schema_to_use = getattr(self, "_active_schema", None) or self.schema
            if schema_to_use:
                extra_kwargs["schema"] = schema_to_use

        conn = self._connect_with_fingerprint_retry(
            dsn=self._build_dsn(self.host, self.port),
            user=self.username,
            password=self.password,
            **extra_kwargs,
        )

        # Disable query cache for accurate benchmarking
        # Exasol's query cache stores SELECT results and returns them instantly
        # on subsequent identical queries, making benchmark times invalid.
        # See: https://docs.exasol.com/db/latest/database_concepts/query_cache.htm
        if disable_query_cache:
            conn.execute("ALTER SESSION SET query_cache='off'")

        return conn

    @exclude_from_package
    def _install_docker(self) -> bool:
        """Install Exasol using Docker."""
        volumes = {str(self.data_dir): "/exa/data"} if self.data_dir else {}
        if self.license_file and Path(self.license_file).exists():
            volumes[self.license_file] = "/exa/etc/license.xml:ro"
            self.record_setup_note(f"Using license file: {self.license_file}")
        image = (
            f"exasol/docker-db:{self.version if self.version != 'latest' else 'latest'}"
        )
        return self._install_docker_common(
            image, {8563: 8563, 6583: 6583}, volumes, {"EXA_PRIVILEGED": "yes"}
        )

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install Exasol using c4 native installer.

        Delegates to ExasolNativeInstaller for the full installation flow.
        """
        return self.native_installer.install()

    @exclude_from_package
    def _verify_preinstalled(self) -> bool:
        """Verify that Exasol is already installed and accessible."""
        return self.is_healthy()

    @exclude_from_package
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
            health_check_host = self._get_health_check_host()

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
        """Create a schema in Exasol.

        Uses skip_schema=True to avoid chicken-and-egg problem where we try
        to connect TO the schema we're creating.
        """
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name};"
        conn = None

        try:
            # Connect WITHOUT schema to avoid "schema not found" error
            # when creating the schema for the first time
            conn = self._get_connection(skip_schema=True)
            if not conn:
                self._log(f"Failed to connect for schema creation: {schema_name}")
                return False

            conn.execute(sql)

            if self.schema and schema_name.upper() == self.schema.upper():
                self._schema_created = True

            return True

        except Exception as e:
            self._log(f"Failed to create schema '{schema_name}': {e}")
            return False

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into Exasol table using pyexasol import_from_file."""
        schema_name = kwargs.get("schema", "benchmark")
        columns = kwargs.get("columns", [])
        data_format = kwargs.get("format", "tbl")  # tbl (TPC-H pipe) or tsv or parquet
        # Column metadata from workload for SQL transformations
        timestamp_cols: set[str] = kwargs.get("timestamp_cols", set())
        date_cols: set[str] = kwargs.get("date_cols", set())

        conn = None

        try:
            conn = self._get_connection(compression=False)
            if not conn:
                return False
            if not self._schema_created:
                if self._schema_exists(conn, schema_name):
                    self._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            self._log(
                f"Loading {data_path} into {table_name} (format: {data_format})..."
            )

            if data_format == "parquet":
                # Parquet format - use pyarrow to read and stream to Exasol
                return self._load_parquet_data(
                    conn, table_name, data_path, columns, timestamp_cols, date_cols
                )
            elif data_format == "tsv":
                # TSV format - tab-separated
                import_params = {
                    "column_separator": "\t",
                    "columns": columns,
                    "csv_cols": [f"1..{len(columns)}"] if columns else None,
                }
            else:
                # TPC-H .tbl format (pipe-delimited)
                import_params = {
                    "column_separator": "|",
                    "columns": columns,
                    "csv_cols": [f"1..{len(columns)}"] if columns else None,
                }

            # Remove None values
            import_params = {k: v for k, v in import_params.items() if v is not None}

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

    def _load_parquet_data(
        self,
        conn: Any,
        table_name: str,
        data_path: Path,
        columns: list[str],
        timestamp_columns: set[str] | None = None,
        date_columns: set[str] | None = None,
    ) -> bool:
        """Load Parquet data into Exasol using SQL-based transformations."""
        return self.data_loader.load_parquet_data(
            conn, table_name, data_path, columns, timestamp_columns, date_columns
        )

    def _create_staging_table(
        self,
        conn: Any,
        source_table: str,
        staging_table: str,
        columns: list[str],
        timestamp_columns: set[str],
        date_columns: set[str],
    ) -> None:
        """Create staging table with raw integer types for timestamp/date columns."""
        self.data_loader._create_staging_table(
            conn, source_table, staging_table, columns, timestamp_columns, date_columns
        )

    def _build_transform_sql(
        self,
        target_table: str,
        staging_table: str,
        columns: list[str],
        timestamp_columns: set[str],
        date_columns: set[str],
    ) -> str:
        """Build INSERT SELECT with SQL transformations for timestamps/dates."""
        return self.data_loader._build_transform_sql(
            target_table, staging_table, columns, timestamp_columns, date_columns
        )

    def load_data_parallel(
        self,
        table_name: str,
        schema: str,
        columns: list[str],
        num_workers: int = 16,
        timestamp_cols: set[str] | None = None,
        date_cols: set[str] | None = None,
    ) -> bool:
        """Load data using parallel parquet partition loading."""
        return self.data_loader.load_data_parallel(
            table_name, schema, columns, num_workers, timestamp_cols, date_cols
        )

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """Load data from an iterable source."""
        return self.data_loader.load_data_from_iterable(
            table_name, data_source, data_format, **kwargs
        )

    def load_data_from_http_url(
        self,
        table_name: str,
        url: str,
        schema: str,
        format: str = "tsv",
        columns: list[str] | None = None,
        expected_rows: int | None = None,
    ) -> bool:
        """Load data directly from HTTP URL using Exasol IMPORT statement."""
        return self.data_loader.load_data_from_http_url(
            table_name, url, schema, format, columns, expected_rows
        )

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
        from benchkit.debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        timer_obj: Timer | None = None

        try:
            conn = None

            try:
                # Schema is set in connection params by _get_connection()
                conn = self._get_connection()

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

    @exclude_from_package
    def _get_cluster_play_id(self) -> str | None:
        """Get the cluster play_id from c4 ps command."""
        return self.cluster_manager.get_cluster_play_id()

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
        return self.cluster_manager.execute_confd_client_command(
            play_id, confd_command, description, category, silent
        )

    @exclude_from_package
    def _install_license_file(self, play_id: str, license_file_path: str) -> None:
        """Install Exasol license file using c4 connect."""
        self.cluster_manager.install_license_file(play_id, license_file_path)

    @exclude_from_package
    def _configure_database_parameters(
        self, play_id: str, db_params: list[str]
    ) -> bool:
        """Configure Exasol database parameters using c4 connect."""
        return self.cluster_manager.configure_database_parameters(play_id, db_params)

    @exclude_from_package
    def _wait_for_database_ready(
        self, play_id: str, max_attempts: int = 60, delay: int = 5
    ) -> bool:
        """Wait for database to be fully initialized and connectable."""
        return self.cluster_manager.wait_for_database_ready(
            play_id, max_attempts, delay
        )

    @exclude_from_package
    def _update_credentials_from_config(self) -> None:
        """Update Exasol credentials from config after cloud manager is set."""
        db_password = self.setup_config.get("db_password")
        if db_password:
            self.password = db_password

    @exclude_from_package
    def _cleanup_disturbing_services(self, play_id: str) -> bool:
        """Remove rapid, eventd, healthd services that interfere with benchmarks."""
        return self.cluster_manager.cleanup_disturbing_services(play_id)

    @exclude_from_package
    def load_data_from_url(
        self,
        schema_name: str,
        table_name: str,
        data_url: str | list[str],
        /,
        extension: str = ".csv",
        **kwargs: Any,
    ) -> bool:
        """Load data from URL(s) using Exasol CSV IMPORT."""
        return self.data_loader.load_data_from_url(
            schema_name, table_name, data_url, extension, **kwargs
        )
