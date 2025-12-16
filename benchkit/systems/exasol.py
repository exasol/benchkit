"""Exasol database system implementation."""

from __future__ import annotations

import glob
import json
import ssl
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pyexasol  # type: ignore

from benchkit.common import DataFormat, exclude_from_package
from benchkit.infra.self_managed import (
    SelfManagedConnectionInfo,
    SelfManagedDeployment,
    SelfManagedStatus,
)

from ..util import Timer
from .base import SystemUnderTest

if TYPE_CHECKING:
    # avoid cyclic dependency problems
    from ..workloads import Workload


class ExasolSystem(SystemUnderTest):
    """Exasol database system implementation."""

    # Exasol supports multinode clusters via c4 tool
    SUPPORTS_MULTINODE = True
    # streaming import implemented using pyexasol
    SUPPORTS_STREAMLOAD = True

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by Exasol system."""
        return ["pyexasol>=0.25.0"]

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
        self, compression: bool = True, skip_schema: bool = False
    ) -> Any:
        """Get a connection to Exasol database using pyexasol.

        Args:
            compression: Whether to enable compression (default True)
            skip_schema: If True, don't include schema in connection params.
                        Use this when creating schemas to avoid chicken-and-egg
                        problem where we try to connect TO the schema we're creating.
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

        return self._connect_with_fingerprint_retry(
            dsn=self._build_dsn(self.host, self.port),
            user=self.username,
            password=self.password,
            **extra_kwargs,
        )

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
        db_mem_size = self.setup_config.get("db_mem_size")  # In MB, optional

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
                "sudo useradd -m -s /bin/bash exasol",
                "Create Exasol system user",
                "user_setup",
                node_info=node_info,
            )
            if not self.execute_command_on_all_nodes(
                "sudo useradd -m -s /bin/bash exasol || true",
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
            # Use -q to suppress verbose progress output (~3700 lines)
            result = self.execute_command(f"wget -q {c4_url} -O c4 && chmod +x c4")
            if not result["success"]:
                self._log(f"Failed to download c4: {result['stderr']}")
                return False
            self._log(f"✓ Downloaded c4 v{c4_version}")

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

            # Setup ubuntu→exasol@localhost passwordless SSH on each node
            self._log("Setting up ubuntu→exasol@localhost SSH access on all nodes...")
            for idx, mgr in enumerate(self._cloud_instance_managers):
                # Configure SSH to skip host key checking for localhost
                localhost_ssh_cmd = """
# Add localhost to known_hosts to avoid prompts
ssh-keyscan -H localhost >> ~/.ssh/known_hosts 2>/dev/null || true
ssh-keyscan -H 127.0.0.1 >> ~/.ssh/known_hosts 2>/dev/null || true

# Create SSH config for localhost if not exists
mkdir -p ~/.ssh
touch ~/.ssh/config
grep -q "Host localhost" ~/.ssh/config 2>/dev/null || cat >> ~/.ssh/config << 'SSHEOF'

Host localhost 127.0.0.1
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
chmod 600 ~/.ssh/config
"""
                result = mgr.run_remote_command(localhost_ssh_cmd, timeout=60)
                if result.get("success"):
                    self._log(f"  ✓ localhost SSH configured on node {idx}")
                else:
                    self._log(f"  ⚠ Failed to configure localhost SSH on node {idx}")

                # Verify ubuntu can SSH to exasol@localhost
                test_result = mgr.run_remote_command(
                    "ssh -o BatchMode=yes exasol@localhost 'echo ok' 2>/dev/null",
                    timeout=30,
                )
                if test_result.get("success") and "ok" in test_result.get("stdout", ""):
                    self._log(f"  ✓ SSH ubuntu→exasol@localhost verified on node {idx}")
                else:
                    self._log(
                        f"  ⚠ SSH ubuntu→exasol@localhost verification failed on node {idx}"
                    )

            # Setup exasol→exasol SSH access (for exasol user to SSH to itself and other nodes)
            self._log("Setting up exasol→exasol SSH access on all nodes...")

            # Step 4a: Generate SSH keys for exasol user on all nodes
            for idx, mgr in enumerate(self._cloud_instance_managers):
                keygen_cmd = """
sudo -u exasol bash -c '
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    if [ ! -f ~/.ssh/id_rsa ]; then
        ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N "" -q
    fi
'
"""
                result = mgr.run_remote_command(keygen_cmd, timeout=60)
                if result.get("success"):
                    self._log(f"  ✓ SSH key generated for exasol user on node {idx}")
                else:
                    self._log(
                        f"  ⚠ Failed to generate SSH key for exasol on node {idx}"
                    )

            # Step 4b: Collect all exasol public keys
            exasol_pub_keys = []
            for _idx, mgr in enumerate(self._cloud_instance_managers):
                result = mgr.run_remote_command(
                    "sudo cat ~exasol/.ssh/id_rsa.pub", timeout=30
                )
                if result.get("success"):
                    key = result.get("stdout", "").strip()
                    if key:
                        exasol_pub_keys.append(key)

            # Step 4c: Distribute all exasol public keys to all nodes
            self._log(
                f"Distributing {len(exasol_pub_keys)} exasol keys to all nodes..."
            )
            for _idx, mgr in enumerate(self._cloud_instance_managers):
                for pub_key in exasol_pub_keys:
                    add_key_cmd = f"echo '{pub_key}' | sudo tee -a ~exasol/.ssh/authorized_keys > /dev/null"
                    mgr.run_remote_command(add_key_cmd, timeout=30)
                # Fix permissions after adding keys
                mgr.run_remote_command(
                    "sudo chown exasol:exasol ~exasol/.ssh/authorized_keys && sudo chmod 600 ~exasol/.ssh/authorized_keys",
                    timeout=30,
                )

            # Step 4d: Build list of all hosts for SSH config
            all_hosts = ["localhost", "127.0.0.1"]
            all_hosts.extend(host_addrs.split())  # private IPs
            all_hosts.extend(host_external_addrs.split())  # public IPs
            hosts_pattern = " ".join(all_hosts)

            # Step 4e: Configure exasol's SSH config for all hosts
            for idx, mgr in enumerate(self._cloud_instance_managers):
                exasol_ssh_config_cmd = f"""
sudo -u exasol bash -c '
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/config
chmod 600 ~/.ssh/config

# Add SSH config for all cluster hosts
grep -q "Host localhost" ~/.ssh/config 2>/dev/null || cat >> ~/.ssh/config << SSHEOF

Host {hosts_pattern}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
'
"""
                result = mgr.run_remote_command(exasol_ssh_config_cmd, timeout=60)
                if result.get("success"):
                    self._log(f"  ✓ exasol SSH config set on node {idx}")
                else:
                    self._log(f"  ⚠ Failed to set exasol SSH config on node {idx}")

            # Step 4f: Verify exasol can SSH to exasol@localhost
            for idx, mgr in enumerate(self._cloud_instance_managers):
                test_result = mgr.run_remote_command(
                    "sudo -u exasol ssh -o BatchMode=yes exasol@localhost 'echo ok' 2>/dev/null",
                    timeout=30,
                )
                if test_result.get("success") and "ok" in test_result.get("stdout", ""):
                    self._log(f"  ✓ SSH exasol→exasol@localhost verified on node {idx}")
                else:
                    self._log(
                        f"  ⚠ SSH exasol→exasol@localhost verification failed on node {idx}"
                    )

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

            # Add database memory size if specified (in MB)
            if db_mem_size:
                config_content += f"\nCCC_PLAY_DB_MEM_SIZE={db_mem_size}"

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

            self._log(f"✓ Schema '{schema_name}' created successfully")
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

        conn = None

        try:
            conn = self._get_connection(compression=False)
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

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        schema_name: str = kwargs.get("schema", "benchmark")
        conn: pyexasol.ExaConnection | None = None

        try:
            conn = self._get_connection(compression=False)
            if not conn:
                return False
            if not self._schema_created:
                if self._schema_exists(conn, schema_name):
                    self._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            self._log(f"Loading ({data_format}) into {schema_name}.{table_name}...")
            if data_format == DataFormat.DATA_LIST:
                conn.import_from_iterable(data_source, table=table_name)
            else:
                conn.import_from_file(data_source, table_name, import_params={})

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

    @exclude_from_package
    def _update_credentials_from_config(self) -> None:
        """Update Exasol credentials from config after cloud manager is set."""
        db_password = self.setup_config.get("db_password")
        if db_password:
            self.password = db_password

    @exclude_from_package
    def _cleanup_disturbing_services(self, play_id: str) -> bool:
        """Remove rapid, eventd, healthd services that interfere with benchmarks."""
        try:
            cosps_result = self.execute_command(
                f"c4 connect -s cos -i {play_id} -- cosps", timeout=30, record=False
            )
            if not cosps_result.get("success", False):
                return False
            service_ids = {}
            for line in cosps_result.get("stdout", "").split("\n"):
                parts = line.split()
                if len(parts) >= 7 and not line.strip().startswith(
                    ("ROOT", "--", "ID")
                ):
                    for target in ["rapid", "eventd", "healthd"]:
                        if target in parts[6]:
                            service_ids[target] = parts[0]
                            break
            if not service_ids:
                return True
            removed = sum(
                1
                for sid in service_ids.values()
                if self.execute_command(
                    f"c4 connect -s cos -i {play_id} -- cosrm -a {sid}",
                    timeout=30,
                    record=False,
                ).get("success", False)
            )
            return removed > 0
        except Exception:
            return False

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
        conn = None

        # split URL into bases and file names
        data_sources: dict[Path, list[str]] = {}
        for url in [data_url] if isinstance(data_url, str) else data_url:
            p = Path(url)
            prefix: Path = p.parent
            if prefix not in data_sources:
                data_sources[prefix] = [p.name]
            else:
                data_sources[prefix].append(p.name)

        try:
            conn = self._get_connection()
            if not conn:
                return False
            if not self._schema_created:
                if self._schema_exists(conn, schema_name):
                    self._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            self._log(f"Loading {data_url} into {table_name}...")
            base_sql = f"IMPORT INTO {schema_name}.{table_name} FROM CSV AT "
            for host, files in data_sources.items():
                base_sql += f"'{host}' " + " ".join([f"FILE '{f}'" for f in files])

            conn.execute(base_sql)

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


# =============================================================================
# Exasol Personal Edition - Self-Managed Deployment
# =============================================================================


@exclude_from_package
class ExasolPersonalEdition(SelfManagedDeployment):
    """Exasol Personal Edition - self-managed deployment via 'exasol' CLI.

    This class wraps the Exasol Personal Edition launcher CLI to provide
    infrastructure management for benchkit. The personal edition handles
    its own AWS infrastructure via OpenTofu/Terraform internally.

    Status values from CLI:
    - not_initialized: No deployment exists
    - initialized: Ready for deploy
    - running: Database started but not verified
    - database_ready: Database running and accepting connections
    - stopped: EC2 instances stopped, data preserved
    - interrupted: Operation was interrupted
    - deployment_failed: Deployment failed
    """

    # Status constants matching the CLI
    STATUS_NOT_INITIALIZED = "not_initialized"
    STATUS_INITIALIZED = "initialized"
    STATUS_RUNNING = "running"
    STATUS_DATABASE_READY = "database_ready"
    STATUS_STOPPED = "stopped"
    STATUS_INTERRUPTED = "interrupted"
    STATUS_DEPLOYMENT_FAILED = "deployment_failed"

    # GitHub repository for CLI releases
    CLI_REPO = "exasol/personal-edition"
    CLI_DEFAULT_VERSION = "0.5.1"

    # Enable remote execution support for load/run phases
    SUPPORTS_REMOTE_EXECUTION = True

    def __init__(
        self,
        deployment_dir: str,
        output_callback: Any | None = None,
        setup_config: dict[str, Any] | None = None,
    ):
        """Initialize ExasolPersonalEdition manager.

        Args:
            deployment_dir: Directory where personal edition stores state
            output_callback: Optional callback for logging output
            setup_config: Setup configuration with exasol_pe_version and other options
        """
        self.deployment_dir = Path(deployment_dir).expanduser().resolve()
        self._output_callback = output_callback
        self._setup_config = setup_config or {}

        # Extract CLI version from setup_config
        self._cli_version = self._setup_config.get(
            "exasol_pe_version", self.CLI_DEFAULT_VERSION
        )

        # CLI path: in parent of deployment_dir (deployment_dir is typically state subdir)
        cli_dir = self.deployment_dir.parent
        self.cli_path = str(cli_dir / "exasol")

    def prepare_remote_environment(
        self, instance_manager: Any, system: Any | None = None
    ) -> bool:
        """Prepare remote environment for package execution.

        Installs required packages (python3, pip, venv, unzip) on the Exasol PE
        instance to support package deployment during load/run phases.

        Args:
            instance_manager: CloudInstanceManager for remote execution
            system: Optional SystemUnderTest instance for recording setup commands

        Returns:
            True if preparation succeeded
        """
        self._log("Preparing remote environment for package execution...")

        # Install required packages: python3, pip, venv, unzip
        packages = ["python3", "python3-pip", "python3-venv", "unzip"]
        install_cmd = (
            "sudo apt-get update && " f"sudo apt-get install -y {' '.join(packages)}"
        )

        # Record the command for reproducibility if system is provided
        if system and hasattr(system, "record_setup_command"):
            system.record_setup_command(
                install_cmd,
                "Install Python and utilities for package execution",
                "prerequisites",
            )

        result = instance_manager.run_remote_command(install_cmd, debug=False)
        if not result.get("success"):
            self._log(
                f"Failed to install packages: {result.get('stderr', 'unknown error')}"
            )
            return False

        self._log("Remote environment ready for package execution")
        return True

    def _log(self, message: str) -> None:
        """Log a message via callback or print."""
        if self._output_callback:
            self._output_callback(message)
        else:
            print(message)

    def ensure_cli_available(self) -> bool:
        """Ensure the CLI binary is available, downloading if necessary.

        Downloads the Exasol Personal Edition CLI from GitHub releases if
        it's not already present at cli_path.

        Returns:
            True if CLI is available (was found or successfully downloaded),
            False if download failed.
        """
        import os
        import platform

        from benchkit.common.file_management import download_github_release

        cli_path = Path(self.cli_path)

        # Check if CLI already exists
        if cli_path.exists() and cli_path.is_file():
            self._log(f"CLI already available at {cli_path}")
            return True

        # Determine the correct asset for the platform
        system = platform.system()
        machine = platform.machine()

        if system == "Linux":
            if machine == "x86_64":
                asset_pattern = "exasol-personal-edition_Linux_x86_64.tar.gz"
            elif machine == "aarch64":
                asset_pattern = "exasol-personal-edition_Linux_arm64.tar.gz"
            else:
                self._log(f"Unsupported Linux architecture: {machine}")
                return False
        elif system == "Darwin":
            if machine == "x86_64":
                asset_pattern = "exasol-personal-edition_macOS_x86_64.tar.gz"
            elif machine == "arm64":
                asset_pattern = "exasol-personal-edition_macOS_arm64.tar.gz"
            else:
                self._log(f"Unsupported macOS architecture: {machine}")
                return False
        else:
            self._log(f"Unsupported platform: {system}")
            return False

        self._log(f"Downloading Exasol PE CLI v{self._cli_version}...")

        # Get GH_TOKEN for private repo access
        gh_token = os.environ.get("GH_TOKEN")

        # Ensure target directory exists
        cli_dir = cli_path.parent
        cli_dir.mkdir(parents=True, exist_ok=True)

        try:
            downloaded_path = download_github_release(
                repo=self.CLI_REPO,
                version=self._cli_version,
                asset_pattern=asset_pattern,
                target_dir=cli_dir,
                gh_token=gh_token,
                binary_name="exasol",
            )
            self._log(f"CLI downloaded to {downloaded_path}")
            return True
        except RuntimeError as e:
            self._log(f"Failed to download CLI: {e}")
            return False

    def _run_command(
        self, args: list[str], timeout: int = 1800
    ) -> subprocess.CompletedProcess[str]:
        """Run personal edition CLI command.

        Args:
            args: Command arguments (without the base 'exasol' command)
            timeout: Timeout in seconds (default: 30 minutes for deploy operations)

        Returns:
            CompletedProcess with stdout, stderr, returncode
        """
        # Ensure deployment directory exists for commands that need it
        if args[0] not in ["help", "version"]:
            self.deployment_dir.mkdir(parents=True, exist_ok=True)

        cmd = [self.cli_path] + args
        self._log(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.deployment_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result
        except subprocess.TimeoutExpired as e:
            self._log(f"Command timed out after {timeout}s")
            stdout_val = e.stdout if isinstance(e.stdout, str) else ""
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout=stdout_val,
                stderr=f"Command timed out after {timeout}s",
            )
        except FileNotFoundError:
            self._log(f"CLI not found: {self.cli_path}")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout="",
                stderr=f"CLI executable not found: {self.cli_path}",
            )

    def get_status(self) -> SelfManagedStatus:
        """Get deployment status via 'exasol status'."""
        result = self._run_command(["status"], timeout=60)

        if result.returncode != 0:
            # Check if it's just not initialized
            if "no workflow state" in result.stderr.lower():
                return SelfManagedStatus(
                    status=self.STATUS_NOT_INITIALIZED,
                    message="No deployment exists in this directory",
                )
            return SelfManagedStatus(
                status="error",
                message="Failed to get status",
                error=result.stderr,
            )

        # Parse JSON output from status command
        try:
            status_data = json.loads(result.stdout)
            return SelfManagedStatus(
                status=status_data.get("status", "unknown"),
                message=status_data.get("message"),
                error=status_data.get("error"),
            )
        except json.JSONDecodeError:
            # Status might not be JSON in some cases
            return SelfManagedStatus(
                status="unknown",
                message=result.stdout,
                error=result.stderr if result.stderr else None,
            )

    def init(self, options: dict[str, Any]) -> bool:
        """Initialize deployment via 'exasol init aws [options]'.

        Args:
            options: Dictionary of options to pass to init command:
                - cluster_size: Number of nodes
                - instance_type: EC2 instance type
                - data_volume_size: Size of data volume in GB
                - db_password: Database password
                - etc.

        Returns:
            True if initialization succeeded
        """
        args = ["init", "aws"]

        # Map options to CLI flags (convert snake_case to kebab-case)
        option_mapping = {
            "cluster_size": "--cluster-size",
            "instance_type": "--instance-type",
            "data_volume_size": "--data-volume-size",
            "os_volume_size": "--os-volume-size",
            "volume_type": "--volume-type",
            "db_password": "--db-password",
            "adminui_password": "--adminui-password",
            "allowed_cidr": "--allowed-cidr",
            "vpc_cidr": "--vpc-cidr",
            "subnet_cidr": "--subnet-cidr",
        }

        for key, flag in option_mapping.items():
            value = options.get(key)
            if value is not None:
                args.extend([flag, str(value)])

        result = self._run_command(args, timeout=120)
        if result.returncode != 0:
            self._log(f"Init failed: {result.stderr}")
            return False

        self._log("Personal edition initialized successfully")
        return True

    def deploy(self) -> bool:
        """Deploy via 'exasol deploy'.

        This provisions AWS infrastructure and installs Exasol.
        Can take 10-20 minutes.

        Returns:
            True if deployment succeeded
        """
        self._log("Deploying Exasol Personal Edition (this may take 10-20 minutes)...")
        result = self._run_command(["deploy"], timeout=2400)  # 40 minutes timeout

        if result.returncode != 0:
            self._log(f"Deploy failed: {result.stderr}")
            return False

        self._log("Personal edition deployed successfully")
        return True

    @exclude_from_package
    def start(self) -> bool:
        """Start stopped deployment via 'exasol start'.

        Returns:
            True if start succeeded
        """
        self._log("Starting Exasol Personal Edition...")
        result = self._run_command(["start"], timeout=600)  # 10 minutes

        if result.returncode != 0:
            self._log(f"Start failed: {result.stderr}")
            return False

        self._log("Personal edition started successfully")
        return True

    def stop(self) -> bool:
        """Stop running deployment via 'exasol stop'.

        Returns:
            True if stop succeeded
        """
        self._log("Stopping Exasol Personal Edition...")
        result = self._run_command(["stop"], timeout=300)  # 5 minutes

        if result.returncode != 0:
            self._log(f"Stop failed: {result.stderr}")
            return False

        self._log("Personal edition stopped successfully")
        return True

    def destroy(self) -> bool:
        """Destroy deployment via 'exasol destroy'.

        This removes all AWS resources created by the deployment.

        Returns:
            True if destroy succeeded
        """
        self._log("Destroying Exasol Personal Edition...")
        result = self._run_command(["destroy"], timeout=600)  # 10 minutes

        if result.returncode != 0:
            self._log(f"Destroy failed: {result.stderr}")
            return False

        self._log("Personal edition destroyed successfully")
        return True

    def get_connection_info(self) -> SelfManagedConnectionInfo | None:
        """Get connection details via 'exasol info --json'.

        Returns:
            SelfManagedConnectionInfo with host, port, username, password,
            and extra info (certificate fingerprint, ssh command, etc.)
        """
        result = self._run_command(["info", "--json"], timeout=60)

        if result.returncode != 0:
            self._log(f"Failed to get connection info: {result.stderr}")
            return None

        try:
            info_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            self._log(f"Failed to parse connection info JSON: {result.stdout}")
            return None

        # Extract connection details from the JSON output
        # New CLI format has nodes nested: nodes.n11.publicIp, nodes.n11.database.dbPort
        # Old format had: hostname, publicIp, dbPort at top level
        host = ""
        port = 8563
        ssh_command = None
        ssh_port = None
        ui_port = None
        cert_fingerprint = None

        # Try new format first (nodes dict)
        nodes = info_data.get("nodes", {})
        if nodes:
            # Get the first node (usually n11 for single-node clusters)
            first_node: dict[str, Any] = next(iter(nodes.values()), {})
            host = first_node.get("publicIp") or first_node.get("dnsName", "")

            # Get database port from nested structure
            database_info = first_node.get("database", {})
            port_str = database_info.get("dbPort", "8563")
            try:
                port = int(port_str)
            except (ValueError, TypeError):
                port = 8563

            ui_port_str = database_info.get("uiPort")
            if ui_port_str:
                try:
                    ui_port = int(ui_port_str)
                except (ValueError, TypeError):
                    pass

            # Get SSH info from nested structure
            ssh_info = first_node.get("ssh", {})
            ssh_command = ssh_info.get("command")
            ssh_port_str = ssh_info.get("port")
            if ssh_port_str:
                try:
                    ssh_port = int(ssh_port_str)
                except (ValueError, TypeError):
                    pass

            # Get certificate from node
            tls_cert = first_node.get("tlsCert")
            if tls_cert:
                cert_fingerprint = tls_cert[:50] + "..."  # Truncate for storage

        # Fall back to old format if no nodes found
        if not host:
            host = info_data.get("hostname") or info_data.get("publicIp", "")
            port_str = info_data.get("dbPort") or info_data.get("port", "8563")
            try:
                port = int(port_str)
            except (ValueError, TypeError):
                port = 8563
            ssh_command = info_data.get("sshCommand")
            ssh_port = info_data.get("sshPort")
            ui_port = info_data.get("uiPort")
            cert_fingerprint = info_data.get(
                "certFingerprint", info_data.get("certificateFingerprint")
            )

        # Get password from secrets file
        password = self._get_password()

        return SelfManagedConnectionInfo(
            host=host,
            port=port,
            username=info_data.get("username", "sys"),
            password=password,
            extra={
                "certificate_fingerprint": cert_fingerprint,
                "ssh_command": ssh_command,
                "ssh_port": ssh_port,
                "ui_port": ui_port,
                "cluster_size": info_data.get("clusterSize"),
                "cluster_state": info_data.get("clusterState"),
                "deployment_id": info_data.get("deploymentId"),
                "deployment_state": info_data.get("deploymentState"),
            },
        )

    def _get_password(self) -> str | None:
        """Read database password from secrets file in deployment directory.

        The secrets file is named 'secrets-exasol-*.json' and contains:
        {"dbPassword": "...", "adminUiPassword": "..."}
        """
        # Find secrets file using glob pattern
        secrets_pattern = str(self.deployment_dir / "secrets-exasol-*.json")
        secrets_files = glob.glob(secrets_pattern)

        if not secrets_files:
            self._log("No secrets file found in deployment directory")
            return None

        secrets_file = Path(secrets_files[0])
        try:
            with open(secrets_file) as f:
                secrets = json.load(f)
            db_password = secrets.get("dbPassword")
            return str(db_password) if db_password is not None else None
        except (OSError, json.JSONDecodeError) as e:
            self._log(f"Failed to read secrets file: {e}")
            return None

    def get_system_info(self) -> dict[str, Any] | None:
        """Query Exasol system info via database connection.

        This provides system information when SSH probing is not available
        or as supplementary info. Queries Exasol's system tables.

        Returns:
            Dictionary with system info, or None if unavailable.
        """
        conn_info = self.get_connection_info()
        if not conn_info or not conn_info.host:
            return None

        try:
            conn = pyexasol.connect(
                dsn=f"{conn_info.host}:{conn_info.port}",
                user=conn_info.username or "sys",
                password=conn_info.password or "",
                encryption=True,
                compression=True,
            )

            system_info: dict[str, Any] = {
                "probe_timestamp": None,
                "hostname": conn_info.host,
                "source": "exasol_api",
            }

            # Query system info from EXA_SYSTEM_PROPERTIES
            try:
                props = conn.execute(
                    "SELECT PROPERTY_NAME, PROPERTY_VALUE FROM EXA_SYSTEM_PROPERTIES"
                ).fetchall()
                system_info["exasol_properties"] = {row[0]: row[1] for row in props}
            except Exception as e:
                self._log(f"Failed to query system properties: {e}")

            # Query cluster info
            try:
                nodes = conn.execute(
                    "SELECT NODE_NAME, NODE_STATE, ACTIVE_SESSIONS "
                    "FROM EXA_STATISTICS.EXA_MONITOR_LAST_DAY "
                    "WHERE MEASURE_TIME = (SELECT MAX(MEASURE_TIME) FROM EXA_STATISTICS.EXA_MONITOR_LAST_DAY)"
                ).fetchall()
                system_info["cluster_nodes"] = [
                    {"name": row[0], "state": row[1], "sessions": row[2]}
                    for row in nodes
                ]
            except Exception:
                # Table might not exist or be accessible
                pass

            # Get database version
            try:
                version = conn.execute(
                    "SELECT PARAM_VALUE FROM SYS.EXA_METADATA "
                    "WHERE PARAM_NAME = 'databaseProductVersion'"
                ).fetchone()
                if version:
                    system_info["database_version"] = version[0]
            except Exception:
                pass

            conn.close()
            return system_info

        except Exception as e:
            self._log(f"Failed to query system info: {e}")
            return None

    def install(self, options: dict[str, Any] | None = None) -> bool:
        """Convenience method: init + deploy in one step.

        Equivalent to 'exasol install' command.

        Args:
            options: Options to pass to init (cluster_size, instance_type, etc.)

        Returns:
            True if install succeeded
        """
        options = options or {}

        # Check current status
        status = self.get_status()

        if status.status == self.STATUS_NOT_INITIALIZED:
            # Need to initialize first
            if not self.init(options):
                return False

        status = self.get_status()
        if status.status == self.STATUS_INITIALIZED:
            # Ready to deploy
            return self.deploy()
        elif status.status in [self.STATUS_RUNNING, self.STATUS_DATABASE_READY]:
            # Already running
            self._log("Personal edition is already running")
            return True
        elif status.status == self.STATUS_STOPPED:
            # Just need to start
            return self.start()
        else:
            self._log(f"Cannot install: deployment is in state '{status.status}'")
            return False

    def ensure_running(self, options: dict[str, Any] | None = None) -> bool:
        """Ensure the deployment is running, installing/starting if needed.

        Args:
            options: Options for init if deployment doesn't exist

        Returns:
            True if deployment is now running
        """
        status = self.get_status()

        if status.status in [self.STATUS_RUNNING, self.STATUS_DATABASE_READY]:
            return True
        elif status.status == self.STATUS_STOPPED:
            return self.start()
        elif status.status in [self.STATUS_NOT_INITIALIZED, self.STATUS_INITIALIZED]:
            return self.install(options)
        else:
            self._log(
                f"Deployment in unexpected state '{status.status}': {status.message}"
            )
            return False
