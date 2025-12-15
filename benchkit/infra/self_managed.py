"""Self-managed deployment infrastructure for systems that handle their own infrastructure.

This module provides abstractions for systems like Exasol Personal Edition that
manage their own cloud infrastructure deployment, separate from benchkit's terraform.

System-specific implementations (like ExasolPersonalEdition) are located in their
respective system modules (e.g., benchkit/systems/exasol.py) to avoid import cycles
and keep domain logic together.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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


@dataclass
class InfrastructureInfo:
    """Infrastructure information for status display.

    This provides a consistent format for displaying infrastructure details
    across both cloud-managed (Terraform) and self-managed deployments.
    """

    public_ip: str
    private_ip: str
    ssh_command: str | None = None
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

    # Whether this deployment supports remote package execution (load/run on remote)
    # Subclasses should set to True if they have SSH access for remote execution
    SUPPORTS_REMOTE_EXECUTION: bool = False

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

    def get_system_info(self) -> dict[str, Any] | None:
        """Get system information for probing (optional, for systems without SSH).

        This method allows self-managed systems to provide system information
        via their native API (e.g., database queries) when SSH access is not
        available.

        Returns:
            Dictionary with system info (similar to system_probe.py output),
            or None if not available.
        """
        return None  # Default: not implemented, subclasses can override

    def get_infrastructure_info(self) -> InfrastructureInfo | None:
        """Get infrastructure information for status display.

        Returns infrastructure details (IPs, SSH command, etc.) in a standard
        format that can be displayed alongside cloud-managed infrastructure.

        The default implementation transforms get_connection_info() output.
        Subclasses may override for custom behavior.

        Returns:
            InfrastructureInfo with public/private IPs and SSH details,
            or None if infrastructure is not available.
        """
        conn_info = self.get_connection_info()
        if not conn_info or not conn_info.host:
            return None

        extra = conn_info.extra or {}
        return InfrastructureInfo(
            public_ip=conn_info.host,
            private_ip=extra.get("private_ip", conn_info.host),
            ssh_command=extra.get("ssh_command"),
            extra=extra,
        )

    def prepare_remote_environment(self, instance_manager: Any) -> bool:
        """Prepare remote environment for package execution.

        Called during setup phase to install required packages (unzip, etc.)
        on the remote instance before load/run phases.

        Default implementation does nothing. Subclasses override for specific needs.

        Args:
            instance_manager: CloudInstanceManager for remote execution

        Returns:
            True if preparation succeeded
        """
        return True  # Default: nothing to prepare

    def get_instance_manager(self) -> Any | None:
        """Get a CloudInstanceManager for remote execution.

        Parses SSH info from connection info and returns a CloudInstanceManager
        that can be used for remote package deployment and execution.

        Returns:
            CloudInstanceManager if SSH access is available, None otherwise.
        """
        if not self.SUPPORTS_REMOTE_EXECUTION:
            return None

        conn_info = self.get_connection_info()
        if not conn_info:
            return None

        ssh_command = conn_info.extra.get("ssh_command") if conn_info.extra else None
        if not ssh_command:
            return None

        # Parse SSH command: "ssh -i key.pem user@host" or "ssh -i key.pem user@host -p 22"
        import os
        import re

        # Extract key path (if present)
        key_match = re.search(r"-i\s+([^\s]+)", ssh_command)
        key_path = key_match.group(1) if key_match else None

        # Extract user@host
        user_host_match = re.search(r"(\w+)@([\w\.\-]+)", ssh_command)
        if not user_host_match:
            return None

        ssh_user = user_host_match.group(1)
        host = user_host_match.group(2)

        # Extract port (if present)
        port_match = re.search(r"-p\s+(\d+)", ssh_command)
        ssh_port = int(port_match.group(1)) if port_match else 22

        # Resolve relative key paths against deployment directory
        if key_path:
            key_path = os.path.expanduser(key_path)
            if not os.path.isabs(key_path):
                # Get deployment dir - handle both _deployment_dir (str) and deployment_dir (Path)
                deploy_dir = getattr(self, "_deployment_dir", None) or getattr(
                    self, "deployment_dir", None
                )
                if deploy_dir:
                    deploy_dir = str(deploy_dir)
                    # Check if key is in deployment dir or state subdirectory
                    candidate = os.path.join(deploy_dir, key_path)
                    state_candidate = os.path.join(deploy_dir, "state", key_path)
                    if os.path.exists(state_candidate):
                        key_path = state_candidate
                    elif os.path.exists(candidate):
                        key_path = candidate
                    else:
                        # Default to state subdirectory (common for managed deployments)
                        key_path = state_candidate

        # Create CloudInstanceManager
        from benchkit.infra.manager import CloudInstanceManager

        instance_info = {"public_ip": host, "private_ip": host}
        return CloudInstanceManager(
            instance_info=instance_info,
            ssh_private_key_path=key_path,
            ssh_user=ssh_user,
            ssh_port=ssh_port,
        )

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


def _get_deployment_class(system_kind: str) -> type[SelfManagedDeployment] | None:
    """Lazily import and return the deployment class for a system kind.

    Uses lazy imports to avoid circular dependencies between this module
    and system-specific modules.

    Args:
        system_kind: The kind of system (e.g., "exasol")

    Returns:
        The deployment class or None if not supported
    """
    if system_kind == "exasol":
        from benchkit.systems.exasol import ExasolPersonalEdition

        return ExasolPersonalEdition

    return None


def get_self_managed_deployment(
    system_kind: str,
    deployment_dir: str,
    output_callback: Any | None = None,
    setup_config: dict[str, Any] | None = None,
) -> SelfManagedDeployment | None:
    """Factory function to create a self-managed deployment handler.

    This function provides a clean abstraction for the CLI to use without
    directly importing specific implementation classes.

    Args:
        system_kind: The kind of system (e.g., "exasol", "clickhouse")
        deployment_dir: Directory where the deployment stores its state
        output_callback: Optional callback for logging output
        setup_config: System setup configuration (passed to deployment class)

    Returns:
        SelfManagedDeployment instance if the system kind supports self-managed
        deployments, None otherwise.

    Example:
        >>> deployment = get_self_managed_deployment("exasol", "/path/to/deploy")
        >>> if deployment:
        ...     deployment.destroy()
    """
    deployment_class = _get_deployment_class(system_kind)
    if deployment_class is None:
        return None

    return deployment_class(
        deployment_dir=deployment_dir,
        output_callback=output_callback,
        setup_config=setup_config,
    )
