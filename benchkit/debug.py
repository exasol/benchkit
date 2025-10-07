"""Debug utilities for the benchmark framework."""

import os
from typing import Any

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


def debug_print(message: str, **kwargs: Any) -> None:
    """Print debug message if debug mode is enabled."""
    if is_debug_enabled():
        print(f"[DEBUG] {message}", **kwargs)


def debug_log_command(command: str, timeout: int | None = None, **kwargs: Any) -> None:
    """Log command execution details if debug mode is enabled."""
    if is_debug_enabled():
        if timeout:
            print(f"[DEBUG] Command ({timeout}s): {command}")
        else:
            print(f"[DEBUG] Command: {command}")


def debug_log_result(
    success: bool, stdout: str | None = None, stderr: str | None = None, **kwargs: Any
) -> None:
    """Log command result details if debug mode is enabled."""
    if is_debug_enabled():
        print(f"[DEBUG] Command success: {success}")
        if stdout:
            print(f"[DEBUG] Stdout: {stdout}")
        if stderr:
            print(f"[DEBUG] Stderr: {stderr}")
