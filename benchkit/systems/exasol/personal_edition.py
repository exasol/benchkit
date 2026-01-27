"""Exasol Personal Edition - Self-Managed Deployment.

This module provides the ExasolPersonalEdition class for managing
Exasol Personal Edition deployments via the 'exasol' CLI tool.
"""

from __future__ import annotations

import glob
import json
import subprocess
from pathlib import Path
from typing import Any

import pyexasol  # type: ignore[import-untyped]

from benchkit.common import exclude_from_package
from benchkit.infra.self_managed import (
    SelfManagedConnectionInfo,
    SelfManagedDeployment,
    SelfManagedStatus,
)


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

    # Exasol downloads site (primary source)
    CLI_DOWNLOADS_PAGE = "https://downloads.exasol.com/"
    CLI_DEFAULT_VERSION = "1.0.0"

    # GitHub repository for CLI releases (fallback)
    CLI_REPO = "exasol/personal-edition"

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
        # Initialize base class (sets _deployment_dir, _output_callback,
        # recorded_commands, _deployment_timing_s)
        super().__init__(
            deployment_dir=deployment_dir,
            output_callback=output_callback,
        )
        # Also store as resolved Path for convenience (base class uses _deployment_dir as str)
        self.deployment_dir = Path(deployment_dir).expanduser().resolve()
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

        Downloads the Exasol Personal Edition CLI from the official Exasol
        downloads site (downloads.exasol.com). Falls back to GitHub releases
        if the Exasol site is unavailable.

        Returns:
            True if CLI is available (was found or successfully downloaded),
            False if download failed.
        """
        import os
        import platform

        from benchkit.common.file_management import (
            download_exasol_personal_cli,
            download_exasol_personal_cli_direct,
            download_github_release,
        )

        cli_path = Path(self.cli_path)

        # Check if CLI already exists
        if cli_path.exists() and cli_path.is_file():
            self._log(f"CLI already available at {cli_path}")
            return True

        # Ensure target directory exists
        cli_dir = cli_path.parent
        cli_dir.mkdir(parents=True, exist_ok=True)

        # Try direct S3 download first (for version 1.0.0+)
        self._log(f"Downloading Exasol PE CLI v{self._cli_version} from S3...")
        try:
            downloaded_path = download_exasol_personal_cli_direct(
                version=self._cli_version,
                target_dir=cli_dir,
                binary_name="exasol",
            )
            self._log(f"CLI downloaded to {downloaded_path}")
            return True
        except RuntimeError as e:
            self._log(f"Direct S3 download failed: {e}")
            self._log("Trying Exasol downloads page...")

        # Try Exasol downloads site (manifest-based)
        try:
            downloaded_path = download_exasol_personal_cli(
                downloads_page_url=self.CLI_DOWNLOADS_PAGE,
                version=self._cli_version,
                target_dir=cli_dir,
                binary_name="exasol",
            )
            self._log(f"CLI downloaded to {downloaded_path}")
            return True
        except RuntimeError as e:
            self._log(f"Exasol download failed: {e}")
            self._log("Falling back to GitHub...")

        # Fallback to GitHub releases
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

        gh_token = os.environ.get("GH_TOKEN")

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
            self._log(f"GitHub download failed: {e}")
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
        # Build command string for recording (will be sanitized automatically)
        cmd_parts = ["exasol", "init", "aws"]

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
                cmd_parts.extend([flag, str(value)])

        # Record the command before execution for report reproduction
        self.record_infrastructure_command(
            " ".join(cmd_parts),
            "Initialize Exasol Personal Edition deployment on AWS",
        )

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
        # Record the command before execution for report reproduction
        self.record_infrastructure_command(
            "exasol deploy",
            "Deploy Exasol infrastructure and database (10-20 minutes)",
        )

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
