"""Exasol database system implementation.

This module provides the ExasolSystem class and related helpers for
benchmarking Exasol databases.

Module structure:
- system.py: Main ExasolSystem class
- native.py: ExasolNativeInstaller for c4-based installations
- cluster.py: ExasolClusterManager for cluster operations
- data.py: ExasolDataLoader for data loading operations
- personal_edition.py: ExasolPersonalEdition for CLI-based deployments
- parallel_loader.py: Parallel partition loading utilities
"""

from benchkit.systems.exasol.personal_edition import ExasolPersonalEdition
from benchkit.systems.exasol.system import ExasolSystem

__all__ = ["ExasolSystem", "ExasolPersonalEdition"]
