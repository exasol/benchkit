"""Decorators to mark code for workload package inclusion/exclusion.

This module provides decorators to explicitly mark which code should be
included in minimal workload execution packages vs. full framework code.

Usage:
    @exclude_from_package - Mark as excluded from workload packages
"""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T", bound=Callable)


def exclude_from_package(obj: T) -> T:
    """Mark function/method to exclude from workload packages.

    Use this decorator on methods that are NOT needed for workload execution:
    - install, setup_storage, teardown
    - Infrastructure management (_detect_storage_devices, _format_disk, etc.)
    - Report generation (get_setup_summary, record_setup_command, etc.)
    - Command recording and sanitization

    Examples:
        >>> @exclude_from_package
        ... def install(self) -> bool:
        ...     return self._install_database()
    """
    setattr(obj, "_exclude_from_package", True)
    return obj
