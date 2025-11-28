"""Database systems under test."""

from typing import Any

from .base import SystemUnderTest

# System factory mapping - use strings to avoid eager imports
SYSTEM_IMPLEMENTATIONS = {
    "exasol": "ExasolSystem",
    "clickhouse": "ClickHouseSystem",
}


def _lazy_import_system(kind: str) -> type[SystemUnderTest]:
    """
    Lazy import of system class to avoid importing dependencies for unused systems.

    Args:
        kind: System type (e.g., "exasol", "clickhouse")

    Returns:
        System class

    Raises:
        ImportError: If the system module or class cannot be imported
    """
    if kind == "exasol":
        from .exasol import ExasolSystem

        return ExasolSystem
    if kind == "clickhouse":
        from .clickhouse import ClickHouseSystem

        return ClickHouseSystem
    raise ValueError(f"Unknown system kind: {kind}")


def create_system(
    config: dict, output_callback: Any = None, workload_config: dict | None = None
) -> SystemUnderTest:
    """
    Factory function to create a system under test.

    Args:
        config: System configuration dictionary
        output_callback: Optional callback for thread-safe logging during parallel execution
        workload_config: Optional workload configuration for dynamic tuning

    Returns:
        SystemUnderTest instance

    Raises:
        ValueError: If system kind is not supported
    """
    import copy
    import os

    kind = config.get("kind")
    if kind not in SYSTEM_IMPLEMENTATIONS:
        available = ", ".join(SYSTEM_IMPLEMENTATIONS.keys())
        raise ValueError(f"Unsupported system kind: {kind}. Available: {available}")

    # Deep copy config to avoid modifying the original
    config_copy = copy.deepcopy(config)

    # Expand environment variables in config strings
    def expand_env_vars(obj: Any) -> Any:
        """Recursively expand environment variables in config."""
        if isinstance(obj, dict):
            return {k: expand_env_vars(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [expand_env_vars(item) for item in obj]
        if isinstance(obj, str):
            return os.path.expandvars(obj)
        return obj

    config_expanded = expand_env_vars(config_copy)

    # Lazy import the system class only when needed
    system_class = _lazy_import_system(kind)

    return system_class(
        config_expanded,
        output_callback=output_callback,
        workload_config=workload_config,
    )


__all__ = [
    "SystemUnderTest",
    "create_system",
    "SYSTEM_IMPLEMENTATIONS",
]
