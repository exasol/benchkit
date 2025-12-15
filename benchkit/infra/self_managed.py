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
