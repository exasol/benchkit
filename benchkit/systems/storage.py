"""Shared storage management for database systems.

This module provides a centralized StorageManager class that handles
storage setup operations across all database systems. It uses a hook
pattern to allow system-specific configuration while centralizing
the common logic.

The module extracts storage-related code from base.py to:
1. Reduce base.py line count
2. Provide reusable storage utilities
3. Enable consistent storage handling across systems
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchkit.common import exclude_from_package

if TYPE_CHECKING:
    from .base import SystemUnderTest


class StorageManager:
    """Handles storage setup operations for database systems.

    This class encapsulates storage detection, RAID creation, mounting,
    and directory setup. It uses a hook pattern where systems provide
    their storage configuration via `get_storage_config()`.

    Attributes:
        system: Parent SystemUnderTest instance for command execution
    """

    def __init__(self, system: SystemUnderTest):
        """Initialize the storage manager.

        Args:
            system: Parent SystemUnderTest instance for shared state access
        """
        self._system = system

    def _log(self, message: str) -> None:
        """Log a message using the parent system's logger."""
        self._system._log(message)

    @exclude_from_package
    def detect_storage_devices(
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
        system = self._system
        result = system.execute_command(
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
                    if self._is_root_device(device_name):
                        continue

                # Check if device exists
                check_result = system.execute_command(
                    f"test -b {device_path} && echo 'exists'", record=False
                )
                if not (
                    check_result.get("success", False)
                    and "exists" in check_result.get("stdout", "")
                ):
                    continue

                # Determine storage type (local instance store vs EBS)
                storage_type = self._detect_storage_type(device_name, device_path)

                # Apply device filter if specified
                if device_filter and storage_type != device_filter:
                    continue

                # Check mount status
                mounted_at = self._get_mount_point(device_path)

                # Resolve to stable /dev/disk/by-id/ path for multinode consistency
                stable_path = self._get_stable_path(device_name, device_path)

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
        devices.sort(key=lambda d: d["stable_path"])

        return devices

    def _is_root_device(self, device_name: str) -> bool:
        """Check if a device is the root disk."""
        system = self._system

        # Dynamically detect root disk by checking what's mounted as /
        root_check = system.execute_command("findmnt -n -o SOURCE /", record=False)

        # Fallback to df if findmnt not available
        if not root_check.get("success", False):
            root_check = system.execute_command(
                "df / | tail -1 | awk '{print $1}'", record=False
            )

        if root_check.get("success", False):
            root_device = root_check.get("stdout", "").strip()

            # If we got /dev/root symlink, resolve it to actual device
            if root_device == "/dev/root":
                readlink_check = system.execute_command(
                    "readlink -f /dev/root", record=False
                )
                if readlink_check.get("success", False):
                    root_device = readlink_check.get("stdout", "").strip()

            # Extract base device name (e.g., /dev/nvme1n1p1 -> nvme1n1)
            if "/" in root_device:
                # Use regex to remove partition suffix (p1, p15, or just digits)
                device_part = root_device.split("/")[-1]
                root_base = re.sub(r"p?\d+$", "", device_part)
                if device_name == root_base:
                    return True

        return False

    def _detect_storage_type(self, device_name: str, device_path: str) -> str:
        """Detect if device is local instance store or EBS."""
        system = self._system
        storage_type = "unknown"

        if device_name.startswith("nvme"):
            # Use nvme id-ctrl to check if it's EBS or local instance store
            nvme_result = system.execute_command(
                f"nvme id-ctrl {device_path} 2>/dev/null | grep -q 'Amazon Elastic Block Store' && echo 'ebs' || echo 'local'",
                record=False,
            )
            if nvme_result.get("success", False):
                storage_type = nvme_result.get("stdout", "").strip()
            else:
                # Fallback: Check /dev/disk/by-id for EBS markers
                by_id_check = system.execute_command(
                    f"ls -la /dev/disk/by-id/ 2>/dev/null | grep '{device_name}' | grep -q 'Amazon_Elastic_Block_Store' && echo 'ebs' || echo 'local'",
                    record=False,
                )
                if by_id_check.get("success", False):
                    storage_type = by_id_check.get("stdout", "").strip()
        elif device_name.startswith(("sd", "xvd")):
            # Traditional block device names are typically EBS volumes on AWS
            storage_type = "ebs"

        return storage_type

    def _get_mount_point(self, device_path: str) -> str | None:
        """Get the mount point for a device, if mounted."""
        system = self._system
        mount_result = system.execute_command(
            f"mount | grep '^{device_path} '", record=False
        )
        if (
            mount_result.get("success", False)
            and mount_result.get("stdout", "").strip()
        ):
            mount_parts = mount_result.get("stdout", "").split()
            if len(mount_parts) >= 3:
                return str(mount_parts[2])
        return None

    def _get_stable_path(self, device_name: str, device_path: str) -> str:
        """Get stable /dev/disk/by-id/ path for multinode consistency."""
        system = self._system
        by_id_result = system.execute_command(
            f"ls -l /dev/disk/by-id/ | grep '{device_name}$' | grep -v -- '-part' | grep -v '_[0-9]*$' | head -1 | awk '{{print \"/dev/disk/by-id/\" $9}}'",
            record=False,
        )
        if (
            by_id_result.get("success", False)
            and by_id_result.get("stdout", "").strip()
        ):
            stable_path_raw = by_id_result.get("stdout", "").strip()
            return stable_path_raw.split("\n")[0] if stable_path_raw else device_path
        return device_path

    @exclude_from_package
    def unmount_disk(self, device_or_mount: str) -> bool:
        """
        Unmount a disk or mount point.

        Args:
            device_or_mount: Device path (e.g., /dev/nvme1n1) or mount point (e.g., /data)

        Returns:
            True if successful, False otherwise
        """
        system = self._system
        result = system.execute_command(
            f"sudo umount {device_or_mount}",
            description=f"Unmount {device_or_mount}",
            category="storage_setup",
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def format_disk(self, device: str, filesystem: str = "ext4") -> bool:
        """
        Format a disk with specified filesystem.

        Args:
            device: Device path (e.g., /dev/nvme1n1)
            filesystem: Filesystem type (default: ext4)

        Returns:
            True if successful, False otherwise
        """
        system = self._system
        result = system.execute_command(
            f"sudo mkfs.{filesystem} -F {device}",
            description=f"Format {device} with {filesystem} filesystem",
            category="storage_setup",
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def mount_disk(
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
        system = self._system

        # Create mount point if needed
        if create_mount_point:
            system.execute_command(
                f"sudo mkdir -p {mount_point}",
                description=f"Create mount point {mount_point}",
                category="storage_setup",
            )

        # Mount the disk
        result = system.execute_command(
            f"sudo mount {device} {mount_point}",
            description=f"Mount {device} to {mount_point}",
            category="storage_setup",
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def set_ownership(self, path: str, owner: str = "ubuntu:ubuntu") -> bool:
        """
        Set directory/file ownership.

        Args:
            path: Path to set ownership for
            owner: Owner in format "user:group" (default: ubuntu:ubuntu)

        Returns:
            True if successful, False otherwise
        """
        system = self._system

        # Check if owner exists (user:group format)
        user = owner.split(":")[0]
        check_user = system.execute_command(
            f"id {user} >/dev/null 2>&1 && echo 'exists'", record=False
        )

        # Distinguish between SSH failure and user not existing
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
            self._log(
                f"Warning: SSH connection issue while checking user {user}, attempting chown anyway"
            )
        elif not (
            check_user.get("success", False)
            and "exists" in check_user.get("stdout", "")
        ):
            self._log(
                f"Warning: User {user} does not exist yet, skipping ownership setting"
            )
            self._log("  Ownership will need to be set later during installation")
            return True

        result = system.execute_command(
            f"sudo chown -R {owner} {path}",
            description=f"Set ownership of {path} to {owner}",
            category="storage_setup",
        )
        return bool(result.get("success", False))

    @exclude_from_package
    def create_raid0(
        self, device_paths: list[str], raid_device: str = "/dev/md0"
    ) -> bool:
        """
        Create RAID0 array from multiple devices.

        Args:
            device_paths: List of device paths to combine
            raid_device: Path for the RAID device (default: /dev/md0)

        Returns:
            True if successful, False otherwise
        """
        system = self._system

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
        system.execute_command(
            f"sudo mdadm --stop {raid_device} 2>/dev/null || true",
            description=f"Stop existing RAID array at {raid_device} if present",
            category="storage_setup",
        )

        # Step 2: Clean devices - unmount if needed and clear filesystem signatures
        for dev in device_paths:
            self._clean_device_for_raid(dev)

        # Step 3: Zero superblocks on all devices
        for dev in device_paths:
            system.execute_command(
                f"sudo mdadm --zero-superblock {dev} 2>/dev/null || true",
                description=f"Clear RAID superblock on {dev}",
                category="storage_setup",
            )

        # Step 4: Create RAID0 array
        create_cmd = (
            f"yes | sudo mdadm --create {raid_device} "
            f"--level=0 --raid-devices={len(device_paths)} {devices_str}"
        )
        result = system.execute_command(
            create_cmd,
            description=f"Create RAID0 array from {len(device_paths)} devices",
            category="storage_setup",
        )
        if not result.get("success", False):
            self._log(
                f"Failed to create RAID0 array: {result.get('stderr', 'Unknown error')}"
            )
            return False

        # Step 5: Wait for array to be ready and save configuration
        self._finalize_raid(raid_device, len(device_paths))

        return True

    def _clean_device_for_raid(self, device: str) -> None:
        """Clean a device before adding to RAID array."""
        system = self._system

        # Check if device is mounted
        mount_check = system.execute_command(f"mount | grep '^{device} '", record=False)
        if mount_check.get("success", False) and mount_check.get("stdout", "").strip():
            self._log(f"Device {device} is mounted, unmounting...")
            system.execute_command(
                f"sudo umount {device}",
                description=f"Unmount {device} before RAID creation",
                category="storage_setup",
            )

        # Clear filesystem signatures
        system.execute_command(
            f"sudo wipefs -a {device} 2>/dev/null || true",
            description=f"Clear filesystem signatures on {device}",
            category="storage_setup",
        )

    def _finalize_raid(self, raid_device: str, num_devices: int) -> None:
        """Finalize RAID setup with wait and config save."""
        system = self._system

        # Wait for array to be ready (non-fatal)
        system.execute_command(
            f"sudo mdadm --wait {raid_device} 2>/dev/null || true",
            description=f"Wait for RAID array {raid_device} to be ready",
            category="storage_setup",
        )

        # Save RAID configuration
        system.execute_command(
            "sudo mkdir -p /etc/mdadm",
            description="Create mdadm configuration directory",
            category="storage_setup",
        )

        system.execute_command(
            "sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf",
            description="Save RAID configuration",
            category="storage_setup",
        )

        # Update initramfs (non-fatal on failure)
        system.execute_command(
            "sudo update-initramfs -u 2>/dev/null || true", record=False
        )

        system.record_setup_note(
            f"RAID0 array created: {raid_device} from {num_devices} devices"
        )
        self._log(f"RAID0 array created successfully: {raid_device}")

    @exclude_from_package
    def setup_storage(self, workload: Any) -> bool:
        """
        Setup storage based on configuration.

        This is the main entry point for storage setup. It uses the system's
        get_storage_config() hook to determine system-specific paths and ownership.

        Idempotent: Can be called multiple times safely. Returns immediately
        if storage was already set up successfully.

        Args:
            workload: Workload instance (for scale factor calculations)

        Returns:
            True if successful, False otherwise
        """
        system = self._system

        # Check if storage setup was already completed
        if getattr(system, "_storage_setup_complete", False):
            self._log(f"Storage already configured for {system.name}, skipping setup")
            return True

        use_additional_disk = system.setup_config.get("use_additional_disk", False)

        # Check for multinode cluster - need to setup storage on ALL nodes
        is_multinode = (
            hasattr(system, "_cloud_instance_managers")
            and system._cloud_instance_managers
            and len(system._cloud_instance_managers) > 1
        )

        result = False
        if use_additional_disk:
            self._log(f"Setting up additional disk storage for {system.name}...")
            if is_multinode:
                self._log(
                    f"Multinode cluster detected ({len(system._cloud_instance_managers)} nodes)"
                )
                result = self.setup_multinode_storage(workload)
            else:
                result = self.setup_database_storage(workload)
        else:
            self._log(f"Setting up directory-based storage for {system.name}...")
            result = self.setup_directory_storage(workload)

        # Mark storage setup as complete if successful
        if result:
            system._storage_setup_complete = True

        return result

    @exclude_from_package
    def setup_database_storage(self, workload: Any) -> bool:
        """
        Setup storage for databases using additional disks.

        This implementation:
        1. Detects local instance store devices (or EBS)
        2. Creates RAID0 if multiple local devices found
        3. Mounts single disk or RAID array at /data
        4. Creates system-specific subdirectory using get_storage_config() hook

        Args:
            workload: Workload instance

        Returns:
            True if successful, False otherwise
        """
        system = self._system

        # Check if /data is already mounted - skip if so (idempotent)
        check_mount = system.execute_command("mount | grep ' /data '", record=False)
        if check_mount.get("success", False) and check_mount.get("stdout", "").strip():
            self._log("Storage already mounted at /data")
            return self._setup_system_subdirectory()

        # First, try to detect local instance store devices
        local_devices = self.detect_storage_devices(
            skip_root=True, device_filter="local"
        )

        device_to_use = None
        mount_point = "/data"

        if len(local_devices) > 1:
            # Multiple local instance store devices → create RAID0
            device_to_use = self._setup_raid_or_single(local_devices)
        elif len(local_devices) == 1:
            # Single local instance store device
            device_path = local_devices[0].get("stable_path", local_devices[0]["path"])
            self._log(f"Detected single local instance store device: {device_path}")
            device_to_use = device_path
        else:
            # No local devices, check for any additional devices (EBS, etc.)
            self._log(
                "No local instance store devices found, checking for EBS volumes..."
            )
            all_devices = self.detect_storage_devices(skip_root=True)

            if not all_devices:
                self._log(
                    f"Warning: No additional storage devices found for {system.name}, using directory storage"
                )
                return self.setup_directory_storage(workload)

            device_to_use = all_devices[0].get("stable_path", all_devices[0]["path"])
            self._log(f"Using EBS device: {device_to_use}")

        # Check if device is already mounted
        if not self._handle_existing_mount(device_to_use, mount_point):
            return False

        # Format and mount
        if not self.format_disk(device_to_use):
            return False

        if not self.mount_disk(device_to_use, mount_point):
            return False

        # Set base ownership for /data
        self.set_ownership(mount_point)

        system.record_setup_note(
            f"Storage device {device_to_use} mounted at {mount_point}"
        )
        self._log(f"Storage setup complete: {device_to_use} -> {mount_point}")

        # Update data_dir to actual mount point
        system.data_dir = Path(mount_point)

        # Create system-specific subdirectory
        return self._setup_system_subdirectory()

    def _setup_raid_or_single(self, local_devices: list[dict[str, Any]]) -> str:
        """Setup RAID0 from multiple devices or return single device."""
        system = self._system

        self._log(
            f"Detected {len(local_devices)} local instance store devices, creating RAID0..."
        )

        # Check if RAID already exists
        raid_device = "/dev/md0"
        raid_check = system.execute_command(
            f"test -b {raid_device} && echo 'exists'", record=False
        )

        if raid_check.get("success", False) and "exists" in raid_check.get(
            "stdout", ""
        ):
            self._log(f"RAID array {raid_device} already exists")
            return raid_device

        # Create RAID0 from all local devices
        device_paths = [d.get("stable_path", d["path"]) for d in local_devices]

        # Validate device paths - ensure no embedded newlines
        for idx, path in enumerate(device_paths):
            if "\n" in path:
                self._log(
                    f"Warning: Device path {idx} contains newlines, using regular path instead"
                )
                device_paths[idx] = local_devices[idx]["path"]

        if self.create_raid0(device_paths, raid_device):
            return raid_device
        else:
            self._log("Warning: RAID0 creation failed, falling back to first device")
            return str(local_devices[0].get("stable_path", local_devices[0]["path"]))

    def _handle_existing_mount(self, device_to_use: str, mount_point: str) -> bool:
        """Handle case where device is already mounted."""
        system = self._system

        mount_check = system.execute_command(
            f"mount | grep {device_to_use}", record=False
        )
        if mount_check.get("success", False) and mount_check.get("stdout", "").strip():
            mount_parts = mount_check.get("stdout", "").split()
            if len(mount_parts) >= 3:
                current_mount = mount_parts[2]
                if current_mount == mount_point:
                    self._log(
                        f"Device {device_to_use} already mounted at {mount_point}"
                    )
                    system.data_dir = Path(mount_point)
                    return True
                else:
                    # Mounted elsewhere, unmount first
                    self._log(
                        f"Device {device_to_use} mounted at {current_mount}, unmounting..."
                    )
                    if not self.unmount_disk(device_to_use):
                        self._log(f"Failed to unmount {device_to_use}")
                        return False
        return True

    def _setup_system_subdirectory(self) -> bool:
        """Create system-specific subdirectory with correct ownership.

        Uses the system's get_storage_config() hook to get the subdirectory
        path and ownership configuration.

        Returns:
            True if successful, False otherwise
        """
        system = self._system

        # Get system-specific storage configuration via hook
        subdir, owner = system.get_storage_config()

        if not subdir:
            # No subdirectory needed (e.g., Exasol manages its own storage)
            return True

        self._log(f"Creating system subdirectory: {subdir} with owner {owner}")

        system.execute_command(
            f"sudo mkdir -p {subdir}",
            description=f"Create {system.kind} data directory",
            category="storage_setup",
        )
        self.set_ownership(subdir, owner=owner)

        # Update data_dir to point to subdirectory
        system.data_dir = Path(subdir)

        system.record_setup_note(f"{system.kind} data directory: {subdir}")
        self._log(f"{system.kind} data directory configured: {subdir}")

        return True

    @exclude_from_package
    def setup_directory_storage(self, workload: Any) -> bool:
        """
        Setup directory-based storage (no additional disks).

        Creates data_dir if specified in configuration, using the
        system's get_storage_config() hook for ownership.

        Args:
            workload: Workload instance (unused, for API consistency)

        Returns:
            True if successful, False otherwise
        """
        system = self._system

        if not system.data_dir:
            self._log(f"No data directory configured for {system.name}, skipping")
            return True

        # Get system-specific ownership from hook
        _, owner = system.get_storage_config()

        # Create directory
        result = system.execute_command(
            f"sudo mkdir -p {system.data_dir}",
            description=f"Create data directory {system.data_dir}",
            category="storage_setup",
        )

        if not result.get("success", False):
            self._log(f"Failed to create data directory {system.data_dir}")
            return False

        # Set ownership using system-specific owner
        self.set_ownership(str(system.data_dir), owner=owner)

        system.record_setup_note(f"Data directory created: {system.data_dir}")
        self._log(f"Directory storage setup complete: {system.data_dir}")

        return True

    @exclude_from_package
    def setup_multinode_storage(self, workload: Any) -> bool:
        """
        Setup storage on all nodes in a multinode cluster.

        Each node gets its own storage setup via setup_single_node_storage().
        Commands are recorded only for the first node to avoid duplicates in reports.

        Args:
            workload: Workload with scale factor for sizing calculations

        Returns:
            True if successful on all nodes, False otherwise
        """
        system = self._system
        all_success = True

        # Store original setup_commands to prevent duplicate recording
        original_commands_count = len(system.setup_commands)

        for idx, mgr in enumerate(system._cloud_instance_managers):
            self._log(f"\n  [Node {idx}] Setting up storage...")

            # Temporarily override execute_command to use this specific node
            original_mgr = system._cloud_instance_manager
            system._cloud_instance_manager = mgr

            # For nodes after the first, temporarily disable recording to avoid duplicates
            if idx > 0:
                commands_before = len(system.setup_commands)

            try:
                # Run single-node storage setup on this node
                success = self.setup_single_node_storage(workload)
                if not success:
                    self._log(f"  [Node {idx}] Storage setup failed")
                    all_success = False
                else:
                    self._log(f"  [Node {idx}] Storage setup completed")
            finally:
                # For nodes after the first, remove any commands that were recorded
                if idx > 0:
                    system.setup_commands = system.setup_commands[:commands_before]

                # Restore primary manager
                system._cloud_instance_manager = original_mgr

        # Add node_info to all commands recorded during storage setup if multinode
        if len(system._cloud_instance_managers) > 1:
            node_info = f"all_nodes_{len(system._cloud_instance_managers)}"
            for i in range(original_commands_count, len(system.setup_commands)):
                system.setup_commands[i]["node_info"] = node_info

        return all_success

    @exclude_from_package
    def setup_single_node_storage(self, workload: Any) -> bool:
        """
        Setup storage on a single node.

        This method handles the common pattern:
        1. Check if /data is already mounted
        2. If yes, create system subdirectory
        3. If no, setup database storage (mount disk/RAID)

        Systems can override this for custom behavior.

        Args:
            workload: Workload with scale factor for sizing calculations

        Returns:
            True if successful, False otherwise
        """
        return self.setup_database_storage(workload)
