"""Debug utilities for the benchmark framework."""

import os
from typing import Any

from .common.markers import exclude_from_package

# Global debug state
_debug_enabled = False


def set_debug(enabled: bool) -> None:
    """Set global debug state."""
    global _debug_enabled
    _debug_enabled = enabled

    # Also set environment variable for child processes
    if enabled:
        os.environ["BENCHKIT_DEBUG"] = "1"
    else:
        os.environ.pop("BENCHKIT_DEBUG", None)


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    global _debug_enabled

    # Check environment variable if not set via set_debug()
    if not _debug_enabled and os.getenv("BENCHKIT_DEBUG", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        _debug_enabled = True

    return _debug_enabled


def _get_task_prefix() -> str:
    """
    Get the task name prefix for output tagging during parallel execution.

    This function provides defense-in-depth for debug output. When running
    in parallel mode, debug output needs to be tagged with the correct
    system name to avoid race conditions with redirect_stdout.

    Returns:
        "[task_name] " prefix if running in a parallel task, empty string otherwise.
    """
    try:
        # Import here to avoid circular import at module load time
        from .run.parallel_executor import get_current_task_name

        task_name = get_current_task_name()
        if task_name:
            return f"[{task_name}] "
    except ImportError:
        # parallel_executor not available (e.g., minimal package installation)
        pass
    return ""


def debug_print(message: str, **kwargs: Any) -> None:
    """Print debug message if debug mode is enabled."""
    if is_debug_enabled():
        prefix = _get_task_prefix()
        print(f"{prefix}[DEBUG] {message}", **kwargs)


@exclude_from_package
def debug_log_command(command: str, timeout: int | None = None, **kwargs: Any) -> None:
    """Log command execution details if debug mode is enabled."""
    if is_debug_enabled():
        prefix = _get_task_prefix()
        if timeout:
            print(f"{prefix}[DEBUG] Command ({timeout}s): {command}")
        else:
            print(f"{prefix}[DEBUG] Command: {command}")


@exclude_from_package
def debug_log_result(
    success: bool, stdout: str | None = None, stderr: str | None = None, **kwargs: Any
) -> None:
    """Log command result details if debug mode is enabled."""
    if is_debug_enabled():
        prefix = _get_task_prefix()
        print(f"{prefix}[DEBUG] Command success: {success}")
        if stdout:
            print(f"{prefix}[DEBUG] Stdout: {stdout}")
        if stderr:
            print(f"{prefix}[DEBUG] Stderr: {stderr}")
