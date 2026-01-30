"""Tail-f style monitoring for multiple log files."""

import threading
import time
from pathlib import Path

from rich.console import Console


class TailMonitor:
    """Monitor log files with simple tail-f style output.

    Prints new lines from log files as they appear, prefixed with system name.
    """

    LINES_PER_SYSTEM = 5
    REFRESH_RATE = 0.5

    def __init__(self, log_files: dict[str, Path], console: Console):
        """Initialize the tail monitor.

        Args:
            log_files: Mapping of system names to log file paths
            console: Rich console for display
        """
        self.log_files = log_files
        self.console = console
        self._positions: dict[str, int] = {}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the monitoring thread."""
        for name in self.log_files:
            self._positions[name] = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the monitoring thread."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _read_new_lines(self, name: str) -> list[str]:
        """Read new lines from a log file since last read.

        Args:
            name: System name (key in log_files)

        Returns:
            List of new lines read from the file
        """
        path = self.log_files[name]
        if not path.exists():
            return []
        try:
            with open(path, encoding="utf-8") as f:
                f.seek(self._positions[name])
                lines = [line.rstrip() for line in f if line.strip()]
                self._positions[name] = f.tell()
            return lines
        except OSError:
            return []

    def _run(self) -> None:
        """Main monitoring loop - prints lines as they appear."""
        while not self._stop.is_set():
            for name in self.log_files:
                new_lines = self._read_new_lines(name)
                if new_lines:
                    # Limit to last N lines per cycle
                    lines_to_print = new_lines[-self.LINES_PER_SYSTEM :]
                    for line in lines_to_print:
                        # Use markup=False to ensure prefix appears even in non-terminal output
                        self.console.print(f"[{name}] {line}", markup=False)
            time.sleep(self.REFRESH_RATE)
