"""Multinode operation helpers for managing cloud instance managers.

This module consolidates common patterns for working with both single-node
and multi-node cloud deployments:
- Normalizing instance managers (single or list)
- Extracting IP addresses from managers
- Getting primary/coordinator node
- Building connection info dictionaries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from ..infra.manager import CloudInstanceManager


class InstanceManagerProtocol(Protocol):
    """Protocol for cloud instance managers."""

    @property
    def public_ip(self) -> str: ...

    @property
    def private_ip(self) -> str: ...

    def run_remote_command(
        self, command: str, timeout: int = 300
    ) -> dict[str, Any]: ...


@dataclass
class NodeInfo:
    """Information about nodes in a deployment."""

    primary: CloudInstanceManager | None = None
    all_managers: list[CloudInstanceManager] = field(default_factory=list)
    is_multinode: bool = False
    node_count: int = 0

    @property
    def public_ips(self) -> list[str]:
        """Get public IPs from all managers."""
        return [mgr.public_ip for mgr in self.all_managers if mgr.public_ip]

    @property
    def private_ips(self) -> list[str]:
        """Get private IPs from all managers."""
        return [mgr.private_ip for mgr in self.all_managers if mgr.private_ip]

    @property
    def public_ip(self) -> str | None:
        """Get public IP of primary node."""
        return self.primary.public_ip if self.primary else None

    @property
    def private_ip(self) -> str | None:
        """Get private IP of primary node."""
        return self.primary.private_ip if self.primary else None


def normalize_instance_manager(
    instance_manager: Any | list[Any] | None,
) -> NodeInfo:
    """Normalize instance manager to a NodeInfo structure.

    Consolidates 10+ `isinstance(instance_manager, list)` checks across the codebase
    into a single normalized structure.

    Args:
        instance_manager: Single manager, list of managers, or None

    Returns:
        NodeInfo with normalized access to managers

    Examples:
        >>> info = normalize_instance_manager(single_mgr)
        >>> info.primary  # Returns single_mgr
        >>> info.is_multinode  # Returns False

        >>> info = normalize_instance_manager([mgr1, mgr2, mgr3])
        >>> info.primary  # Returns mgr1
        >>> info.is_multinode  # Returns True
        >>> info.all_managers  # Returns [mgr1, mgr2, mgr3]
    """
    if instance_manager is None:
        return NodeInfo()

    if isinstance(instance_manager, list):
        managers = instance_manager
        return NodeInfo(
            primary=managers[0] if managers else None,
            all_managers=managers,
            is_multinode=len(managers) > 1,
            node_count=len(managers),
        )

    # Single manager
    return NodeInfo(
        primary=instance_manager,
        all_managers=[instance_manager],
        is_multinode=False,
        node_count=1,
    )


def get_primary_manager(
    instance_manager: Any | list[Any] | None,
) -> Any | None:
    """Get the primary/coordinator node manager.

    Shorthand for normalize_instance_manager(instance_manager).primary

    Args:
        instance_manager: Single manager or list of managers

    Returns:
        The primary manager, or None if no managers
    """
    return normalize_instance_manager(instance_manager).primary


def is_multinode(instance_manager: Any | list[Any] | None) -> bool:
    """Check if this is a multinode configuration.

    Args:
        instance_manager: Single manager or list of managers

    Returns:
        True if more than one node
    """
    return normalize_instance_manager(instance_manager).is_multinode


def build_connection_info(
    instance_manager: Any | list[Any] | None,
) -> dict[str, Any]:
    """Build connection info dictionary from instance manager(s).

    Consolidates the pattern from runner.py:_build_connection_info()

    Args:
        instance_manager: Single manager or list of managers

    Returns:
        Dictionary with connection info:
        - For multinode: {"public_ips": [...], "private_ips": [...]}
        - For single: {"public_ip": str, "private_ip": str}
        - For None: {}
    """
    if instance_manager is None:
        return {}

    info = normalize_instance_manager(instance_manager)

    if info.is_multinode:
        return {
            "public_ips": info.public_ips,
            "private_ips": info.private_ips,
        }

    if info.primary:
        return {
            "public_ip": info.public_ip,
            "private_ip": info.private_ip,
        }

    return {}


def get_all_public_ips(
    instance_manager: Any | list[Any] | None,
) -> list[str]:
    """Get public IPs from all managers.

    Args:
        instance_manager: Single manager or list of managers

    Returns:
        List of public IP addresses
    """
    return normalize_instance_manager(instance_manager).public_ips


def get_all_private_ips(
    instance_manager: Any | list[Any] | None,
) -> list[str]:
    """Get private IPs from all managers.

    Args:
        instance_manager: Single manager or list of managers

    Returns:
        List of private IP addresses
    """
    return normalize_instance_manager(instance_manager).private_ips
