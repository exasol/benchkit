"""File-based logging with real-time writing."""

import threading
from collections.abc import Callable
from io import TextIOWrapper
from pathlib import Path
from typing import Any

from benchkit.common.markup import strip_markup


class FileLogger:
    """Thread-safe file writer for system logs.

    Provides real-time file-based logging with Rich markup stripping
    for clean, parseable log files.
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._lock = threading.Lock()
        self._file: TextIOWrapper | None = None

    def open(self) -> None:
        """Open the log file for writing."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = open(self.log_path, "w", encoding="utf-8", buffering=1)

    def write(self, message: str) -> None:
        """Write message to log file (thread-safe).

        Strips Rich markup tags and normalizes whitespace for clean log files.
        Leading/trailing whitespace is removed to ensure consistent tag formatting
        when TailMonitor prepends [task_name] prefixes.

        Args:
            message: Message to write (may contain Rich markup)
        """
        with self._lock:
            if self._file:
                # Strip markup and normalize whitespace for consistent tag formatting
                clean = strip_markup(message).strip()
                if clean:  # Only write non-empty lines
                    self._file.write(clean + "\n")

    def close(self) -> None:
        """Close the log file."""
        with self._lock:
            if self._file:
                self._file.close()
                self._file = None

    def create_callback(self) -> Callable[[str], None]:
        """Create callback for output routing.

        Returns:
            Callable that writes messages to this logger
        """
        return self.write

    def __enter__(self) -> "FileLogger":
        self.open()
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
