"""Thread-safe parallel execution manager for benchmark systems.

This module provides parallel task execution with file-based logging.
Output from each task is written to individual log files, avoiding
race conditions that occur with stdout redirection approaches.

Architecture:
- Each task gets a FileLogger that writes to its own log file
- Output goes through explicit callbacks, not stdout redirection
- TailMonitor can display real-time progress from log files
- Thread-local storage tracks current task for debugging
"""

from __future__ import annotations

import re
import sys
import threading
import time
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .file_logger import FileLogger
from .tail_monitor import TailMonitor

# Module-level executor reference for thread-local task identification
# Used by debug.py to get the current task name for proper output tagging
_current_executor: ParallelExecutor | None = None


def get_current_task_name() -> str | None:
    """
    Get the current task name from thread-local storage.

    This function allows code outside the ParallelExecutor (like debug.py)
    to identify which task is currently running in the calling thread.
    This enables thread-safe output tagging when using raw print() statements.

    Returns:
        The current task name if running within a ParallelExecutor task,
        None otherwise (sequential execution or not within a task).
    """
    if _current_executor is None:
        return None
    return getattr(_current_executor._thread_local, "current_task", None)


class ParallelExecutor:
    """Thread-safe parallel execution manager with file-based logging.

    Uses FileLogger for real-time file writes and explicit callbacks
    for output routing. This avoids race conditions inherent in
    redirect_stdout approaches.
    """

    def __init__(
        self,
        max_workers: int = 2,
        console: Any = None,
        log_callback: Callable[[str], None] | None = None,
    ):
        """Initialize the parallel executor.

        Args:
            max_workers: Maximum concurrent tasks
            console: Rich console for display (optional, uses default if not provided)
            log_callback: Optional callback for routing summary output (for suite-level
                parallel execution). If provided, summary output goes through this
                callback instead of directly to stdout.
        """
        self.max_workers = max_workers

        # Status tracking
        self.status: dict[str, str] = {}
        self.start_times: dict[str, float] = {}
        self.finish_times: dict[str, float] = {}
        self.results: dict[str, Any] = {}

        # Threading synchronization
        self._state_lock = threading.Lock()
        self._thread_local = threading.local()

        # File loggers for each task
        self._file_loggers: dict[str, FileLogger] = {}
        self._log_paths: dict[str, Path] = {}

        # Console for display
        if console is None:
            from rich.console import Console

            console = Console()
        self._console = console

        # Log callback for suite-level output routing
        self._log_callback = log_callback

        # Remember original streams for direct output
        self._stdout_original = sys.stdout
        self._stderr_original = sys.stderr

    def execute_parallel(
        self,
        tasks: dict[str, Callable[[], Any]],
        phase_name: str,
        log_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        """Execute tasks in parallel with file-based logging.

        Args:
            tasks: Dictionary mapping task names to callables
            phase_name: Name of the phase (for logging)
            log_dir: Base directory for log files

        Returns:
            Dictionary mapping task names to results
        """
        global _current_executor

        if not tasks:
            return {}

        # Set module-level executor reference
        _current_executor = self

        self._reset_state(tasks)

        # Setup file logging if directory provided
        phase_log_dir: Path | None = None
        if log_dir:
            phase_log_dir = Path(log_dir) / self._slugify(phase_name)
            phase_log_dir.mkdir(parents=True, exist_ok=True)
            self._setup_loggers(tasks.keys(), phase_log_dir)

        # Start tail monitor for real-time display
        monitor: TailMonitor | None = None
        if phase_log_dir and self._log_paths:
            monitor = TailMonitor(self._log_paths, self._console)
            monitor.start()

        future_to_name = {}

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                for name, task in tasks.items():
                    self._record_line(name, "Task queued")
                    future = pool.submit(self._wrap_task, name, task)
                    future_to_name[future] = name

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        result = future.result()
                        with self._state_lock:
                            self.results[name] = result
                            self.status[name] = "Completed"
                            self.finish_times[name] = time.time()
                        self._record_line(name, "[status] Completed")
                    except Exception as exc:
                        with self._state_lock:
                            self.results[name] = None
                            self.status[name] = f"Failed: {exc}"[:200]
                            self.finish_times[name] = time.time()
                        self._record_line(name, f"[status] Failed: {exc}")
        finally:
            # Stop monitor
            if monitor:
                monitor.stop()

            # Close loggers
            self._close_loggers()

            # Clear module-level executor reference
            _current_executor = None

        # Print summary
        self._print_summary(phase_name)

        return dict(self.results)

    def _wrap_task(self, name: str, task: Callable[[], Any]) -> Any:
        """Run a single task with logging callback.

        Sets thread-local task name for task identification.
        """
        # Set thread-local task name
        self._thread_local.current_task = name

        with self._state_lock:
            self.start_times[name] = time.time()
        self.update_status(name, "Running...")

        try:
            self._record_line(name, "Task started")
            result = task()
            return result
        except Exception:
            self._record_line(name, "[stderr] Task raised an exception")
            tb = traceback.format_exc().strip().splitlines()
            for line in tb:
                self._record_line(name, f"[stderr] {line}")
            raise
        finally:
            # Clear thread-local task name
            self._thread_local.current_task = None

    def add_output(self, name: str, message: str) -> None:
        """Record a log line for a task.

        Args:
            name: Task name
            message: Message to log
        """
        self._record_line(name, message)

    def create_output_callback(self, task_name: str) -> Callable[[str], None]:
        """
        Create a thread-safe output callback for a specific task.

        This callback routes output directly to the task's file logger,
        providing thread-safe logging without race conditions.

        Args:
            task_name: Name of the task this callback is for

        Returns:
            A callable that takes a message string and records it for the task

        Example:
            callback = executor.create_output_callback("exasol")
            system = create_system(config, output_callback=callback)
            # Now system._log() will route to the correct task log file
        """

        def callback(message: str) -> None:
            self._record_line(task_name, message)

        return callback

    def get_current_task_name(self) -> str | None:
        """
        Get the name of the task currently executing in this thread.

        Returns:
            Task name if in a task context, None otherwise
        """
        return getattr(self._thread_local, "current_task", None)

    def update_status(self, name: str, status: str) -> None:
        """Update task status and record it."""
        with self._state_lock:
            self.status[name] = status
        self._record_line(name, f"[status] {status}")

    # Internal helpers -------------------------------------------------

    def _reset_state(self, tasks: dict[str, Callable[[], Any]]) -> None:
        """Reset internal state for a new execution run."""
        current = time.time()
        self.status = dict.fromkeys(tasks, "Pending")
        self.start_times = dict.fromkeys(tasks, current)
        self.finish_times = {}
        self.results = {}
        self._file_loggers = {}
        self._log_paths = {}

    def _setup_loggers(self, task_names: Any, log_dir: Path) -> None:
        """Create file loggers for each task."""
        for name in task_names:
            filename = f"{self._slugify(name)}.log"
            log_path = log_dir / filename
            logger = FileLogger(log_path)
            logger.open()
            self._file_loggers[name] = logger
            self._log_paths[name] = log_path

    def _close_loggers(self) -> None:
        """Close all file loggers."""
        for logger in self._file_loggers.values():
            logger.close()

    def _record_line(self, name: str, message: str) -> None:
        """Record a line to the task's file logger.

        TailMonitor handles displaying the output from log files with proper
        prefixes, so we only write to the file logger here.
        """
        clean = message.rstrip("\n\r")

        # Write to file logger - TailMonitor will display it
        logger = self._file_loggers.get(name)
        if logger:
            logger.write(clean)

    def _print_summary(self, phase_name: str) -> None:
        """Print execution summary."""
        self._print_line(f"{phase_name} Summary:")
        for name in sorted(self.status.keys()):
            status = self.status[name]
            finish = self.finish_times.get(name, time.time())
            elapsed = finish - self.start_times.get(name, finish)
            self._print_line(f"- {name}: {status} ({elapsed:.1f}s)")
            path = self._log_paths.get(name)
            if path:
                self._print_line(f"  log: {path}")
        self._print_line("")

    def _print_line(self, text: str) -> None:
        """Print a line, routing through log callback if available."""
        if self._log_callback:
            self._log_callback(text)
        elif self._stdout_original:
            self._stdout_original.write(text + "\n")
            self._stdout_original.flush()

    @staticmethod
    def _slugify(value: str) -> str:
        """Convert a string to a slug suitable for filenames."""
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return slug or "task"
