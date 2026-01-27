"""Centralized timeout calculation for benchmark operations.

This module provides a unified approach to timeout calculations across the framework,
supporting:
- Scale-factor-based scaling with logarithmic growth
- Per-system multipliers (different databases load at different speeds)
- Config overrides for explicit control
- Backward compatibility with existing execution_timeout config
"""

from __future__ import annotations

import math
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..systems.base import SystemUnderTest


class OperationType(Enum):
    """Types of operations that require timeout configuration."""

    DATA_GENERATION = "data_generation"
    DATA_LOADING = "data_loading"
    QUERY_EXECUTION = "query_execution"
    INFRASTRUCTURE = "infrastructure"


class TimeoutCalculator:
    """Centralized timeout calculator for benchmark operations.

    Provides consistent timeout calculations across all benchmark components
    using logarithmic scaling based on scale factor and per-system multipliers.

    The formula for scale-factor-based timeouts is:
        timeout = base_timeout * (1 + log10(scale_factor)) * system_multiplier

    This provides smooth, intuitive scaling:
    - SF=1:   base * 1.0  (e.g., 1h for query execution)
    - SF=10:  base * 2.0  (e.g., 2h)
    - SF=100: base * 3.0  (e.g., 3h)
    - SF=300: base * 3.5  (e.g., ~3.5h, capped at max)
    - SF=1000: base * 4.0

    Timeouts are bounded by MIN_TIMEOUTS and MAX_TIMEOUTS to prevent
    unreasonably short or long waits.

    Usage:
        calculator = TimeoutCalculator(config)
        timeout = calculator.get_data_loading_timeout("clickhouse")
    """

    # Base timeouts in seconds for SF=1
    # These are designed to produce reasonable timeouts at common scale factors:
    # SF=1: ~base, SF=10: ~2x base, SF=100: ~3x base
    BASE_TIMEOUTS = {
        OperationType.DATA_GENERATION: 600,  # 10 minutes base
        OperationType.DATA_LOADING: 3600,  # 1 hour base (scales to ~3h at SF=100)
        OperationType.QUERY_EXECUTION: 3600,  # 1 hour base (scales to ~3h at SF=100)
        OperationType.INFRASTRUCTURE: 3600,  # 1 hour (fixed, no scaling)
    }

    # Maximum timeouts in seconds (caps)
    MAX_TIMEOUTS = {
        OperationType.DATA_GENERATION: 7200,  # 2 hours max
        OperationType.DATA_LOADING: 28800,  # 8 hours max
        OperationType.QUERY_EXECUTION: 21600,  # 6 hours max (matches old SF>100 cap)
        OperationType.INFRASTRUCTURE: 3600,  # 1 hour (fixed)
    }

    # Minimum timeouts in seconds (floors)
    MIN_TIMEOUTS = {
        OperationType.DATA_GENERATION: 300,  # 5 minutes min
        OperationType.DATA_LOADING: 1800,  # 30 minutes min
        OperationType.QUERY_EXECUTION: 1800,  # 30 minutes min
        OperationType.INFRASTRUCTURE: 600,  # 10 minutes min
    }

    # Config keys for each operation type (for override lookup)
    CONFIG_KEYS = {
        OperationType.DATA_GENERATION: "data_generation_timeout",
        OperationType.DATA_LOADING: "data_loading_timeout",
        OperationType.QUERY_EXECUTION: "execution_timeout",  # backward compat
        OperationType.INFRASTRUCTURE: "infrastructure_timeout",
    }

    def __init__(self, config: dict[str, Any]):
        """Initialize timeout calculator with benchmark configuration.

        Args:
            config: Full benchmark configuration dictionary
        """
        self.config = config
        self.workload_config = config.get("workload", {})
        self.scale_factor = self.workload_config.get("scale_factor", 1)

    def _get_scale_multiplier(self) -> float:
        """Calculate timeout multiplier based on scale factor using logarithmic scaling.

        Uses log10 for gentler scaling that better matches real-world data loading times:
        - SF=1:   1.0x (base timeout)
        - SF=10:  2.0x
        - SF=100: 3.0x
        - SF=1000: 4.0x

        Returns:
            Multiplier value (1.0 for SF=1, increases logarithmically)
        """
        if self.scale_factor <= 1:
            return 1.0
        # log10 scaling for gentler growth
        return 1.0 + math.log10(self.scale_factor)

    def _get_system_multiplier(
        self, system_kind: str | None, operation: OperationType
    ) -> float:
        """Get per-system timeout multiplier.

        Different databases have different loading/execution speeds.
        This method retrieves the LOAD_TIMEOUT_MULTIPLIER from the system class.

        Args:
            system_kind: System type (e.g., "clickhouse", "exasol")
            operation: Type of operation

        Returns:
            System-specific multiplier (default 1.0)
        """
        if system_kind is None:
            return 1.0

        # Only apply system multiplier for data loading operations
        if operation != OperationType.DATA_LOADING:
            return 1.0

        try:
            from ..systems import _lazy_import_system

            system_class = _lazy_import_system(system_kind)
            return getattr(system_class, "LOAD_TIMEOUT_MULTIPLIER", 1.0)
        except (ImportError, ValueError):
            return 1.0

    def _get_config_override(self, operation: OperationType) -> int | None:
        """Check for config override for the given operation type.

        Args:
            operation: Type of operation

        Returns:
            Override value in seconds, or None if not configured
        """
        config_key = self.CONFIG_KEYS.get(operation)
        if config_key and config_key in self.workload_config:
            return int(self.workload_config[config_key])
        return None

    def get_timeout(
        self,
        operation: OperationType,
        system_kind: str | None = None,
    ) -> int:
        """Calculate timeout for the given operation type.

        Args:
            operation: Type of operation (DATA_GENERATION, DATA_LOADING, etc.)
            system_kind: Optional system type for system-specific multipliers

        Returns:
            Timeout in seconds
        """
        # Check for config override first
        override = self._get_config_override(operation)
        if override is not None:
            return override

        # Infrastructure timeout is fixed (no scaling)
        if operation == OperationType.INFRASTRUCTURE:
            return self.BASE_TIMEOUTS[operation]

        # Calculate scaled timeout
        base = self.BASE_TIMEOUTS[operation]
        scale_mult = self._get_scale_multiplier()
        system_mult = self._get_system_multiplier(system_kind, operation)

        calculated = base * scale_mult * system_mult

        # Apply min/max bounds
        min_timeout = self.MIN_TIMEOUTS[operation]
        max_timeout = self.MAX_TIMEOUTS[operation]

        return int(max(min_timeout, min(max_timeout, calculated)))

    def get_data_generation_timeout(self) -> int:
        """Get timeout for data generation operations.

        Returns:
            Timeout in seconds
        """
        return self.get_timeout(OperationType.DATA_GENERATION)

    def get_data_loading_timeout(self, system_kind: str | None = None) -> int:
        """Get timeout for data loading operations.

        Args:
            system_kind: System type for system-specific multiplier

        Returns:
            Timeout in seconds
        """
        return self.get_timeout(OperationType.DATA_LOADING, system_kind)

    def get_query_execution_timeout(self) -> int:
        """Get timeout for query execution operations.

        This method maintains backward compatibility with the existing
        execution_timeout config key.

        Returns:
            Timeout in seconds
        """
        return self.get_timeout(OperationType.QUERY_EXECUTION)

    def get_infrastructure_timeout(self) -> int:
        """Get timeout for infrastructure operations (fixed, no scaling).

        Returns:
            Timeout in seconds
        """
        return self.get_timeout(OperationType.INFRASTRUCTURE)

    @classmethod
    def get_timeout_from_system(
        cls,
        system: SystemUnderTest,
        operation: OperationType,
    ) -> int:
        """Convenience method to get timeout using system's workload config.

        Args:
            system: System under test instance
            operation: Type of operation

        Returns:
            Timeout in seconds
        """
        # Build minimal config from system's workload_config
        config = {"workload": system.workload_config}
        calculator = cls(config)
        return calculator.get_timeout(operation, system.kind)
