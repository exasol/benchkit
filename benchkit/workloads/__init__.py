"""Benchmark workloads."""

from .base import Workload
from .estuary import Estuary
from .tpch import TPCH

# Workload factory mapping
WORKLOAD_IMPLEMENTATIONS: dict[str, type[Workload]] = {
    "tpch": TPCH,
    "estuary": Estuary,
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


__all__ = [
    "Workload",
    "TPCH",
    "Estuary",
    "create_workload",
    "WORKLOAD_IMPLEMENTATIONS",
]
