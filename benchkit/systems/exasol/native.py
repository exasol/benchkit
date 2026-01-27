"""Exasol native installer using c4 tool.

This module handles native installation of Exasol clusters using the c4 tool.
It is excluded from benchmark packages as it's only needed for infrastructure setup.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from benchkit.common import exclude_from_package

if TYPE_CHECKING:
    from .system import ExasolSystem


class ExasolNativeInstaller:
    """Handles native Exasol installation via c4 cluster tool.

    This class encapsulates the complex c4-based installation process,
    including multinode cluster setup, SSH key distribution, and storage
    configuration.
    """

    def __init__(self, system: ExasolSystem):
        """Initialize the native installer.

        Args:
            system: Parent ExasolSystem instance for shared state access
        """
        self._system = system

    def _log(self, message: str) -> None:
        """Log a message using the parent system's logger."""
        self._system._log(message)

    @exclude_from_package
    def install(self) -> bool:
        """Install Exasol using c4 native installer.

        This is a comprehensive installation process that:
        1. Creates the exasol user on all nodes
        2. Sets up storage (raw disk or loopback device)
        3. Downloads and configures the c4 tool
        4. Distributes SSH keys to all cluster nodes
        5. Creates c4 configuration and deploys the cluster
        6. Waits for the cluster to become healthy
        7. Configures database parameters and installs license

        Returns:
            True if installation succeeded, False otherwise
        """
        system = self._system

        assert (
            system.setup_method == "installer"
        ), f"Expected setup_method 'installer', got '{system.setup_method}'"

        system.record_setup_note("Installing Exasol using c4 native installer")

        # Get configuration from setup_config
        c4_version = system.setup_config.get("c4_version", "2025.1.4")

        # Build IP address lists for multinode support
        if system._cloud_instance_managers and len(system._cloud_instance_managers) > 1:
            # Multinode: build space-separated IP lists
            private_ips = [mgr.private_ip for mgr in system._cloud_instance_managers]
            public_ips = [mgr.public_ip for mgr in system._cloud_instance_managers]
            host_addrs = " ".join(private_ips)
            host_external_addrs = " ".join(public_ips)
            self._log(
                f"Multinode setup with {len(system._cloud_instance_managers)} nodes:"
            )
            self._log(f"  Private IPs: {host_addrs}")
            self._log(f"  Public IPs: {host_external_addrs}")
        else:
            # Single node: use configured addresses or resolve from environment
            host_addrs = system._resolve_ip_addresses(
                system.setup_config.get("host_addrs", "localhost")
            )
            host_external_addrs = system._resolve_ip_addresses(
                system.setup_config.get("host_external_addrs", host_addrs)
            )

        image_password = system.setup_config.get("image_password", "exasol123")
        db_password = system.setup_config.get("db_password", "exasol456")
        admin_password = system.setup_config.get("admin_password", "exasol789")
        working_copy = system.setup_config.get(
            "working_copy", f"@exasol-{system.version}"
        )
        storage_disk_size = system.setup_config.get("storage_disk_size", "100GB")
        db_mem_size = system.setup_config.get("db_mem_size")  # In MB, optional

        try:
            # Step 0: Handle license file
            remote_license_path = self._handle_license_file()

            # Step 1: Create exasol user on all nodes
            if not self._setup_exasol_user():
                return False

            # Step 2: Setup storage
            use_additional_disk, storage_disk_path, data_dir = self._setup_storage(
                storage_disk_size
            )

            # Step 3: Download c4 tool
            if not self._download_c4(c4_version):
                return False

            # Step 4: Setup SSH keys
            if not self._setup_ssh_keys(host_addrs, host_external_addrs):
                return False

            # Step 5: Create c4 configuration
            remote_config_path = self._create_c4_config(
                host_addrs,
                host_external_addrs,
                storage_disk_path,
                image_password,
                db_password,
                admin_password,
                working_copy,
                db_mem_size,
                use_additional_disk,
                data_dir,
            )
            if not remote_config_path:
                return False

            # Step 6: Deploy cluster
            if not self._deploy_cluster(remote_config_path):
                return False

            # Update connection parameters
            self._update_connection_params(host_addrs, host_external_addrs, db_password)

            # Step 7: Wait for cluster to be ready
            system.record_setup_note(
                "Waiting for Exasol cluster to be ready for connections..."
            )
            self._log("Waiting for Exasol cluster to be ready...")
            if not system.wait_for_health(max_attempts=120, delay=10.0):
                self._log("Exasol cluster failed to become ready within timeout")
                return False

            system.record_setup_note(
                "✓ Exasol cluster is ready and accepting connections"
            )

            # Step 8: Post-deployment configuration
            if not self._post_deployment_config(remote_license_path):
                return False

            # Mark that system is installed
            system.mark_installed(record=False)
            self._log("✓ Exasol installation completed successfully")

            return True

        except Exception as e:
            self._log(f"Native Exasol installation failed: {e}")
            return False

    def _handle_license_file(self) -> str | None:
        """Handle license file if specified.

        Returns:
            Remote path to license file, or None if not specified
        """
        system = self._system

        if not system.license_file or not Path(system.license_file).exists():
            return None

        system.record_setup_note(f"Using Exasol license file: {system.license_file}")

        if system._cloud_instance_manager:
            remote_license_path = "/tmp/exasol.license"
            system.record_setup_note(
                f"Copying license file to remote system: {remote_license_path}"
            )

            if not system._cloud_instance_manager.copy_file_to_instance(
                Path(system.license_file), remote_license_path
            ):
                self._log("Failed to copy license file to remote instance")
                return None
            return remote_license_path
        else:
            return str(system.license_file)

    def _setup_exasol_user(self) -> bool:
        """Create exasol user on all nodes.

        Returns:
            True if successful
        """
        system = self._system
        node_count = (
            len(system._cloud_instance_managers)
            if system._cloud_instance_managers
            else 1
        )
        node_info = f"all_nodes_{node_count}" if node_count > 1 else None

        system.record_setup_command(
            "sudo useradd -m -s /bin/bash exasol",
            "Create Exasol system user",
            "user_setup",
            node_info=node_info,
        )
        if not system.execute_command_on_all_nodes(
            "sudo useradd -m -s /bin/bash exasol || true",
            description="Creating exasol user on all nodes",
        ):
            self._log("Warning: Failed to create exasol user on some nodes")

        system.record_setup_command(
            "sudo usermod -aG sudo exasol",
            "Add exasol user to sudo group",
            "user_setup",
            node_info=node_info,
        )
        if not system.execute_command_on_all_nodes(
            "sudo usermod -aG sudo exasol || true",
            description="Adding exasol to sudo group on all nodes",
        ):
            self._log("Warning: Failed to add exasol to sudo group on some nodes")

        # Setup passwordless sudo on ALL nodes
        if not system.execute_command_on_all_nodes(
            'sudo sed -i "/%sudo/s/) ALL$/) NOPASSWD: ALL/" /etc/sudoers',
            description="Configuring passwordless sudo on all nodes",
        ):
            self._log("Warning: Failed to configure passwordless sudo on some nodes")

        system.record_setup_command(
            "sudo passwd exasol",
            "Set password for exasol user (interactive)",
            "user_setup",
        )

        return True

    def _setup_storage(self, storage_disk_size: str) -> tuple[bool, str, str | None]:
        """Setup storage disk for Exasol.

        Args:
            storage_disk_size: Size of storage disk

        Returns:
            Tuple of (use_additional_disk, storage_disk_path, data_dir)
        """
        system = self._system
        use_additional_disk = system.setup_config.get("use_additional_disk", False)

        if use_additional_disk:
            # Check if disk was already partitioned
            if system._exasol_raw_partition:
                actual_device_path = system._exasol_raw_partition
                storage_disk_path = system._create_storage_symlink(actual_device_path)
                system.data_device = storage_disk_path

                system.record_setup_note(
                    f"Using partitioned raw disk: {actual_device_path} (via {storage_disk_path})"
                )
                self._log(
                    f"✓ Using pre-partitioned raw disk for Exasol: {actual_device_path} (via {storage_disk_path})"
                )
                return True, storage_disk_path, None
            else:
                # Fall back to detecting and using full disk
                detected_disk = system._detect_exasol_disk(allow_mounted=True)
                if detected_disk:
                    devices = system._detect_storage_devices(skip_root=True)
                    device_info = next(
                        (d for d in devices if d["path"] == detected_disk), None
                    )

                    if device_info and device_info["mounted_at"]:
                        self._log(
                            f"Disk {detected_disk} is mounted at {device_info['mounted_at']}, unmounting..."
                        )
                        if not system._unmount_disk(detected_disk):
                            self._log(f"Error: Could not unmount {detected_disk}")
                            use_additional_disk = False

                    if use_additional_disk:
                        storage_disk_path = system._create_storage_symlink(
                            detected_disk
                        )
                        system.data_device = storage_disk_path

                        system.record_setup_command(
                            f"lsblk {detected_disk}",
                            f"Using additional disk: {detected_disk} (via {storage_disk_path})",
                            "storage_setup",
                        )
                        system.record_setup_note(
                            f"Using additional disk: {detected_disk} (via {storage_disk_path})"
                        )
                        return True, storage_disk_path, None
                else:
                    self._log(
                        "Warning: No suitable additional disk found, falling back to file storage"
                    )
                    use_additional_disk = False

        # Fallback: Create loopback storage
        return self._setup_loopback_storage(storage_disk_size)

    def _setup_loopback_storage(
        self, storage_disk_size: str
    ) -> tuple[bool, str, str | None]:
        """Setup loopback device storage as fallback.

        Args:
            storage_disk_size: Size of storage file

        Returns:
            Tuple of (use_additional_disk=False, storage_disk_path, data_dir)
        """
        system = self._system
        data_dir = system.setup_config.get("data_dir", "/tmp/exasol_storage")
        storage_file_path = f"{data_dir}/storage_disk1"
        exasol_storage_link = "/dev/exasol.storage"

        is_multinode = (
            system._cloud_instance_managers and len(system._cloud_instance_managers) > 1
        )
        node_info = (
            f"all_nodes_{len(system._cloud_instance_managers)}"
            if is_multinode
            else None
        )

        # Create data directory
        system.record_setup_command(
            f"sudo mkdir -p {data_dir}",
            "Create Exasol data directory",
            "storage_setup",
            node_info=node_info,
        )
        if not system.execute_command_on_all_nodes(
            f"sudo mkdir -p {data_dir}",
            description="Creating data directory on all nodes",
        ):
            self._log("Failed to create data directory on some nodes")
            return False, "", None

        # Create storage file
        system.record_setup_command(
            f"sudo truncate -s {storage_disk_size} {storage_file_path}",
            f"Create {storage_disk_size} storage disk file",
            "storage_setup",
            node_info=node_info,
        )
        if not system.execute_command_on_all_nodes(
            f"sudo truncate -s {storage_disk_size} {storage_file_path}",
            description="Creating storage file on all nodes",
        ):
            self._log("Failed to create storage file on some nodes")
            return False, "", None

        # Set ownership
        system.record_setup_command(
            f"sudo chown -R exasol:exasol {data_dir}",
            "Set ownership of data directory to exasol user",
            "storage_setup",
            node_info=node_info,
        )
        system.execute_command_on_all_nodes(
            f"sudo chown -R exasol:exasol {data_dir}",
            description="Setting ownership on all nodes",
        )

        # Detach existing loopback
        system.execute_command_on_all_nodes(
            f"sudo losetup -d $(losetup -j {storage_file_path} | cut -d: -f1) 2>/dev/null || true",
            description="Detaching existing loopback on all nodes",
        )

        # Remove old symlink
        system.execute_command_on_all_nodes(
            f"sudo rm -f {exasol_storage_link}",
            description="Removing old symlink on all nodes",
        )

        # Setup loopback device
        losetup_cmd = (
            f"LOOP_DEV=$(sudo losetup --find --show {storage_file_path}) && "
            f"sudo ln -sf $LOOP_DEV {exasol_storage_link} && "
            f"echo $LOOP_DEV"
        )
        system.record_setup_command(
            f"sudo losetup --find --show {storage_file_path} && "
            f"sudo ln -sf <loop_device> {exasol_storage_link}",
            f"Setup loopback device for storage file with symlink {exasol_storage_link}",
            "storage_setup",
            node_info=node_info,
        )
        if not system.execute_command_on_all_nodes(
            losetup_cmd,
            description="Setting up loopback device on all nodes",
        ):
            self._log("Failed to setup loopback device on some nodes")
            return False, "", None

        # Verify loopback setup
        system.execute_command_on_all_nodes(
            f"ls -la {exasol_storage_link} && sudo losetup -a | grep {storage_file_path}",
            description="Verifying loopback setup on all nodes",
        )

        system.data_device = f"{storage_file_path} (via {exasol_storage_link})"
        return False, exasol_storage_link, data_dir

    def _download_c4(self, c4_version: str) -> bool:
        """Download the c4 tool.

        Args:
            c4_version: Version of c4 to download

        Returns:
            True if successful
        """
        system = self._system
        c4_url = (
            f"https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/{c4_version}/c4"
        )

        system.record_setup_command(
            f"wget {c4_url} -O c4 && chmod +x c4",
            f"Download c4 cluster management tool v{c4_version}",
            "tool_setup",
        )
        result = system.execute_command(f"wget -q {c4_url} -O c4 && chmod +x c4")
        if not result["success"]:
            self._log(f"Failed to download c4: {result['stderr']}")
            return False
        self._log(f"✓ Downloaded c4 v{c4_version}")
        return True

    def _setup_ssh_keys(self, host_addrs: str, host_external_addrs: str) -> bool:
        """Setup SSH keys for cluster communication.

        Args:
            host_addrs: Space-separated list of private IPs
            host_external_addrs: Space-separated list of public IPs

        Returns:
            True if successful
        """
        system = self._system

        # Generate SSH key on primary node
        system.record_setup_command(
            'ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""',
            "Generate SSH key pair for cluster communication",
            "ssh_setup",
        )
        system.execute_command(
            'test -e ~/.ssh/id_rsa || ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""',
            record=False,
        )

        # Get public key from primary node
        pub_key_result = system.execute_command("cat ~/.ssh/id_rsa.pub", record=False)
        if not pub_key_result["success"]:
            self._log("Failed to read SSH public key")
            return False
        pub_key = pub_key_result["stdout"].strip()

        # Distribute SSH public key to ALL nodes
        self._log(
            f"Distributing SSH key to all {len(system._cloud_instance_managers)} nodes..."
        )
        for idx, mgr in enumerate(system._cloud_instance_managers):
            setup_cmd = f"sudo mkdir -p ~exasol/.ssh && echo '{pub_key}' | sudo tee ~exasol/.ssh/authorized_keys > /dev/null && sudo chown -R exasol:exasol ~exasol/.ssh && sudo chmod 700 ~exasol/.ssh && sudo chmod 600 ~exasol/.ssh/authorized_keys"
            result = mgr.run_remote_command(setup_cmd, timeout=60)
            if result.get("success"):
                self._log(f"  ✓ SSH key installed on node {idx}")
            else:
                self._log(f"  ✗ Failed to install SSH key on node {idx}")
                return False

        # Test SSH connectivity
        self._log("Testing SSH connectivity to all nodes...")
        host_list = host_addrs.split()
        for idx, host in enumerate(host_list):
            result = system.execute_command(
                f"ssh -o StrictHostKeyChecking=no exasol@{host} sudo uptime",
                record=False,
            )
            if result["success"]:
                self._log(f"  ✓ SSH connectivity confirmed to node {idx} ({host})")
            else:
                self._log(f"  ✗ Failed SSH connectivity to node {idx} ({host})")
                return False

        # Setup localhost SSH on all nodes
        self._setup_localhost_ssh()

        # Setup exasol→exasol SSH access
        self._setup_exasol_ssh(host_addrs, host_external_addrs)

        return True

    def _setup_localhost_ssh(self) -> None:
        """Setup ubuntu→exasol@localhost SSH access on all nodes."""
        system = self._system
        self._log("Setting up ubuntu→exasol@localhost SSH access on all nodes...")

        for idx, mgr in enumerate(system._cloud_instance_managers):
            localhost_ssh_cmd = """
ssh-keyscan -H localhost >> ~/.ssh/known_hosts 2>/dev/null || true
ssh-keyscan -H 127.0.0.1 >> ~/.ssh/known_hosts 2>/dev/null || true
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

    def _setup_exasol_ssh(self, host_addrs: str, host_external_addrs: str) -> None:
        """Setup exasol→exasol SSH access on all nodes."""
        system = self._system
        self._log("Setting up exasol→exasol SSH access on all nodes...")

        # Generate SSH keys for exasol user on all nodes
        for idx, mgr in enumerate(system._cloud_instance_managers):
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
                self._log(f"  ⚠ Failed to generate SSH key for exasol on node {idx}")

        # Collect all exasol public keys
        exasol_pub_keys = []
        for _idx, mgr in enumerate(system._cloud_instance_managers):
            result = mgr.run_remote_command(
                "sudo cat ~exasol/.ssh/id_rsa.pub", timeout=30
            )
            if result.get("success"):
                key = result.get("stdout", "").strip()
                if key:
                    exasol_pub_keys.append(key)

        # Distribute all exasol public keys to all nodes
        self._log(f"Distributing {len(exasol_pub_keys)} exasol keys to all nodes...")
        for _idx, mgr in enumerate(system._cloud_instance_managers):
            for pub_key in exasol_pub_keys:
                add_key_cmd = f"echo '{pub_key}' | sudo tee -a ~exasol/.ssh/authorized_keys > /dev/null"
                mgr.run_remote_command(add_key_cmd, timeout=30)
            mgr.run_remote_command(
                "sudo chown exasol:exasol ~exasol/.ssh/authorized_keys && sudo chmod 600 ~exasol/.ssh/authorized_keys",
                timeout=30,
            )

        # Build list of all hosts for SSH config
        all_hosts = ["localhost", "127.0.0.1"]
        all_hosts.extend(host_addrs.split())
        all_hosts.extend(host_external_addrs.split())
        hosts_pattern = " ".join(all_hosts)

        # Configure exasol's SSH config for all hosts
        for idx, mgr in enumerate(system._cloud_instance_managers):
            exasol_ssh_config_cmd = f"""
sudo -u exasol bash -c '
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/config
chmod 600 ~/.ssh/config

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

        # Verify exasol can SSH to exasol@localhost
        for idx, mgr in enumerate(system._cloud_instance_managers):
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

    def _create_c4_config(
        self,
        host_addrs: str,
        host_external_addrs: str,
        storage_disk_path: str,
        image_password: str,
        db_password: str,
        admin_password: str,
        working_copy: str,
        db_mem_size: int | None,
        use_additional_disk: bool,
        data_dir: str | None,
    ) -> str | None:
        """Create c4 configuration file.

        Returns:
            Remote path to config file, or None on failure
        """
        system = self._system

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

        if not use_additional_disk and data_dir:
            config_content += f"\nCCC_PLAY_MOUNTS={data_dir}:{data_dir}"

        if db_mem_size:
            config_content += f"\nCCC_PLAY_DB_MEM_SIZE={db_mem_size}"

        config_content += "\nCCC_ADMINUI_START_SERVER=true"

        system.record_setup_note("C4 Configuration file content:")
        for line in config_content.split("\n"):
            sanitized_line = system._sanitize_command_for_report(line)
            system.record_setup_note(f"  {sanitized_line}")

        # Create config file on remote system
        remote_config_path = "/tmp/exasol_c4.conf"
        escaped_config = (
            config_content.replace("\\", "\\\\")
            .replace("$", "\\$")
            .replace("`", "\\`")
            .replace('"', '\\"')
        )
        create_config_cmd = (
            f'echo "{escaped_config}" | tee {remote_config_path} > /dev/null'
        )

        system.record_setup_command(
            f"cat > {remote_config_path} << 'EOF'\n{system._sanitize_command_for_report(config_content)}\nEOF",
            "Create c4 configuration file on remote system",
            "configuration",
        )
        result = system.execute_command(create_config_cmd)
        if not result["success"]:
            self._log(
                f"Failed to create config file on remote system: {result.get('stderr', 'Unknown error')}"
            )
            return None

        return remote_config_path

    def _deploy_cluster(self, remote_config_path: str) -> bool:
        """Deploy Exasol cluster using c4.

        Args:
            remote_config_path: Path to c4 config file

        Returns:
            True if successful
        """
        system = self._system

        system.record_setup_command(
            f"./c4 host play -i {remote_config_path}",
            "Deploy Exasol cluster using c4",
            "cluster_deployment",
        )
        result = system.execute_command(
            f"./c4 host play -i {remote_config_path}", timeout=1800
        )

        if not result["success"]:
            self._log(f"C4 cluster deployment failed: {result['stderr']}")
            return False

        system.record_setup_note("Exasol cluster deployment initiated")
        return True

    def _update_connection_params(
        self, host_addrs: str, host_external_addrs: str, db_password: str
    ) -> None:
        """Update connection parameters for deployed cluster."""
        system = self._system

        if host_external_addrs and host_external_addrs != "localhost":
            external_host = host_external_addrs.split()[0]
        else:
            external_host = host_addrs.split()[0]

        if system._cloud_instance_manager:
            system._external_host = external_host
            system.host = "localhost"
        else:
            system.host = external_host

        system.username = "sys"
        system.password = db_password
        system.port = 8563

        system.record_setup_note(
            f"Database will be accessible at: {system.host}:{system.port}"
        )
        system.record_setup_note("Admin UI will be available (if enabled)")

    def _post_deployment_config(self, remote_license_path: str | None) -> bool:
        """Perform post-deployment configuration.

        Args:
            remote_license_path: Path to license file if specified

        Returns:
            True if successful
        """
        system = self._system

        # Get cluster play_id
        play_id = system._get_cluster_play_id()
        if not play_id:
            self._log("Could not get cluster play ID")
            return False
        self._log(f"Got play ID {play_id}")

        # Cleanup disturbing services
        self._log("Cleaning up interfering services...")
        cleanup_success = system._cleanup_disturbing_services(play_id)
        if cleanup_success:
            self._log("✓ Service cleanup completed successfully")
        else:
            self._log("⚠ Service cleanup failed or no services to remove")

        # Install license file if specified
        if remote_license_path:
            self._log("Installing license file...")
            system._install_license_file(play_id, remote_license_path)
            self._log("✓ License file installation completed")

        # Configure database parameters if specified
        extra_config = system.setup_config.get("extra", {})
        db_params = extra_config.get("db_params", [])
        if db_params:
            self._log(
                f"Configuring database parameters ({len(db_params)} parameters)..."
            )
            if not system._configure_database_parameters(play_id, db_params):
                self._log(
                    "✗ Database parameter configuration failed - installation incomplete"
                )
                return False
            self._log("✓ Database parameter configuration completed")

        # Record other applied configuration parameters
        if extra_config:
            system.record_setup_note("Additional configuration parameters applied:")
            for key, value in extra_config.items():
                if key != "db_params":
                    system.record_setup_note(f"  {key}: {value}")

        return True
