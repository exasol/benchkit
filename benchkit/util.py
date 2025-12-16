"""Utility functions for the benchmark framework."""

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from .common.markers import exclude_from_package


class Timer:
    """Context manager for timing operations."""

    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        """Return elapsed time in seconds."""
        if self.end_time == 0.0 and self.start_time > 0.0:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time


def safe_command(cmd: str | list[str], timeout: float | None = None) -> dict[str, Any]:
    """
    Execute a command safely and return structured result.

    Returns:
        Dict with keys: success, stdout, stderr, returncode, elapsed_s
    """
    start_time = time.perf_counter()

    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,  # nosec B602
            )
        else:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )

        elapsed = time.perf_counter() - start_time

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "elapsed_s": elapsed,
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
        }

    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start_time
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "returncode": -1,
            "elapsed_s": elapsed,
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
        }
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "elapsed_s": elapsed,
            "command": cmd if isinstance(cmd, str) else " ".join(cmd),
        }


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


@exclude_from_package
def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Save data as JSON file."""
    filepath = Path(path)
    ensure_directory(filepath.parent)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


@exclude_from_package
def load_json(path: str | Path) -> Any:
    """Load data from JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)
