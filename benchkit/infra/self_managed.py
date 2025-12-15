"""Self-managed deployment infrastructure for systems that handle their own infrastructure.

This module provides abstractions for systems like Exasol Personal Edition that
manage their own cloud infrastructure deployment, separate from benchkit's terraform.
"""

import glob
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SelfManagedStatus:
    """Status from a self-managed deployment."""

    status: str  # not_initialized, initialized, running, stopped, database_ready, etc.
    message: str | None = None
    error: str | None = None


@dataclass
class SelfManagedConnectionInfo:
    """Connection info from a self-managed deployment."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class SelfManagedDeployment(ABC):
    """Abstract base class for self-managed deployments.

    Systems that manage their own infrastructure (like Exasol Personal Edition)
    should implement this interface. This allows benchkit to orchestrate
    deployments without managing the underlying infrastructure directly.
    """

    # Common status constant for "not initialized" state
    # Subclasses may define additional status constants
    STATUS_NOT_INITIALIZED = "not_initialized"

    def __init__(
        self,
        deployment_dir: str,
        output_callback: Any | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize self-managed deployment.

        Args:
            deployment_dir: Directory where the deployment stores its state
            output_callback: Optional callback for logging output
            **kwargs: Additional arguments for specific implementations
        """
        # Store common parameters - subclasses can override or extend
        self._deployment_dir = deployment_dir
        self._output_callback = output_callback

    @abstractmethod
    def get_status(self) -> SelfManagedStatus:
        """Get deployment status."""

    @abstractmethod
    def init(self, options: dict[str, Any]) -> bool:
        """Initialize deployment with given options."""

    @abstractmethod
    def deploy(self) -> bool:
        """Deploy the system."""

    @abstractmethod
    def start(self) -> bool:
        """Start a stopped deployment."""

    @abstractmethod
    def stop(self) -> bool:
        """Stop a running deployment."""

    @abstractmethod
    def destroy(self) -> bool:
        """Destroy the deployment and all resources."""

    @abstractmethod
    def get_connection_info(self) -> SelfManagedConnectionInfo | None:
        """Get connection details."""

    def install(self, options: dict[str, Any] | None = None) -> bool:
        """Convenience method: init + deploy in one step.

        Subclasses may override this with custom logic.

        Args:
            options: Options to pass to init

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

        # Attempt to deploy
        return self.deploy()

    def ensure_running(self, options: dict[str, Any] | None = None) -> bool:
        """Ensure the deployment is running, installing/starting if needed.

        Subclasses may override this with custom logic.

        Args:
            options: Options for init if deployment doesn't exist

        Returns:
            True if deployment is now running
        """
        status = self.get_status()

        # If running, we're good
        if "running" in status.status.lower() or "ready" in status.status.lower():
            return True

        # If stopped, try to start
        if "stopped" in status.status.lower():
            return self.start()

        # If not initialized or initialized, try to install
        if (
            status.status == self.STATUS_NOT_INITIALIZED
            or "initialized" in status.status.lower()
        ):
            return self.install(options)

        # Unknown state
        if self._output_callback:
            self._output_callback(
                f"Deployment in unexpected state '{status.status}': {status.message}"
            )
        return False


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

    def __init__(
        self,
        deployment_dir: str,
        cli_path: str = "exasol",
        output_callback: Any | None = None,
    ):
        """Initialize ExasolPersonalEdition manager.

        Args:
            deployment_dir: Directory where personal edition stores state
            cli_path: Path to the 'exasol' CLI executable
            output_callback: Optional callback for logging output
        """
        self.deployment_dir = Path(deployment_dir).expanduser().resolve()
        self.cli_path = cli_path
        self._output_callback = output_callback

    def _log(self, message: str) -> None:
        """Log a message via callback or print."""
        if self._output_callback:
            self._output_callback(message)
        else:
            print(message)

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
        result = self._run_command(["destroy", "--force"], timeout=600)  # 10 minutes

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
        # The structure depends on the CLI version, handle both formats
        host = info_data.get("hostname") or info_data.get("publicIp", "")
        port_str = info_data.get("dbPort") or info_data.get("port", "8563")
        try:
            port = int(port_str)
        except (ValueError, TypeError):
            port = 8563

        # Get password from secrets file
        password = self._get_password()

        return SelfManagedConnectionInfo(
            host=host,
            port=port,
            username=info_data.get("username", "sys"),
            password=password,
            extra={
                "certificate_fingerprint": info_data.get(
                    "certFingerprint", info_data.get("certificateFingerprint")
                ),
                "ssh_command": info_data.get("sshCommand"),
                "ssh_port": info_data.get("sshPort"),
                "ui_port": info_data.get("uiPort"),
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


# Registry mapping system kinds to their self-managed deployment classes
# Add new self-managed deployment types here
SELF_MANAGED_DEPLOYMENTS: dict[str, type[SelfManagedDeployment]] = {
    "exasol": ExasolPersonalEdition,
}


def get_self_managed_deployment(
    system_kind: str,
    deployment_dir: str,
    output_callback: Any | None = None,
) -> SelfManagedDeployment | None:
    """Factory function to create a self-managed deployment handler.

    This function provides a clean abstraction for the CLI to use without
    directly importing specific implementation classes.

    Args:
        system_kind: The kind of system (e.g., "exasol", "clickhouse")
        deployment_dir: Directory where the deployment stores its state
        output_callback: Optional callback for logging output

    Returns:
        SelfManagedDeployment instance if the system kind supports self-managed
        deployments, None otherwise.

    Example:
        >>> deployment = get_self_managed_deployment("exasol", "/path/to/deploy")
        >>> if deployment:
        ...     deployment.destroy()
    """
    deployment_class = SELF_MANAGED_DEPLOYMENTS.get(system_kind)
    if deployment_class is None:
        return None

    return deployment_class(
        deployment_dir=deployment_dir,
        output_callback=output_callback,
    )
