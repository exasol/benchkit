"""Benchmark workloads."""

from .base import Workload
from .tpch import TPCH

# Workload factory mapping
WORKLOAD_IMPLEMENTATIONS = {
    "tpch": TPCH,
}


def create_workload(config: dict) -> Workload:
    """
    Factory function to create a workload.

    Args:
        config: Workload configuration dictionary

    Returns:
        Workload instance

    Raises:
        ValueError: If workload name is not supported
    """
    name = config.get("name")
    if name not in WORKLOAD_IMPLEMENTATIONS:
        available = ", ".join(WORKLOAD_IMPLEMENTATIONS.keys())
        raise ValueError(f"Unsupported workload: {name}. Available: {available}")

    return WORKLOAD_IMPLEMENTATIONS[name](config)


__all__ = ["Workload", "TPCH", "create_workload", "WORKLOAD_IMPLEMENTATIONS"]
