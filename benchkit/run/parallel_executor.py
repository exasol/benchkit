"""Thread-safe parallel execution manager for benchmark systems."""

from __future__ import annotations

import contextlib
import queue
import re
import sys
import threading
import time
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

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


class _TaskStream:
    """Capture stdout/stderr for a single task and forward lines to the executor."""

    def __init__(self, executor: ParallelExecutor, task_name: str, stream_label: str):
        self._executor = executor
        self._task_name = task_name
        self._stream_label = stream_label
        self._pending: str = ""
        self._lock = threading.Lock()

    def write(self, data: str) -> int:
        if not data:
            return 0

        with self._lock:
            text = self._pending + data
            parts = text.split("\n")
            self._pending = parts.pop()  # Remainder without newline

        for line in parts:
            content = line.rstrip("\r")
            if self._stream_label == "stderr" and content:
                content = f"[stderr] {content}"
            self._executor._record_line(self._task_name, content)

        return len(data)

    def flush(self) -> None:
        with self._lock:
            if not self._pending:
                return
            content = self._pending.rstrip("\r")
            if self._stream_label == "stderr" and content:
                content = f"[stderr] {content}"
            self._executor._record_line(self._task_name, content)
            self._pending = ""


class ParallelExecutor:
    """Thread-safe parallel execution manager with per-task logging."""

    # Maximum number of lines to keep in memory per task buffer
    # This prevents memory exhaustion from tasks with excessive output
    MAX_BUFFER_LINES = 50000

    def __init__(self, max_workers: int = 2):
        self.max_workers = max_workers

        self.output_buffers: dict[str, list[str]] = {}
        self.status: dict[str, str] = {}
        self.start_times: dict[str, float] = {}
        self.finish_times: dict[str, float] = {}
        self.results: dict[str, Any] = {}

        self._state_lock = threading.Lock()
        self._print_lock = threading.Lock()
        self._output_locks: dict[str, threading.Lock] = {}
        self._queue: queue.Queue[tuple[str, str] | None] | None = None
        self._consumer_thread: threading.Thread | None = None
        self._log_paths: dict[str, Path] = {}
        self._buffer_overflow: dict[str, bool] = {}

        # Remember original process streams so the consumer can bypass redirection
        self._stdout_original = sys.stdout
        self._stderr_original = sys.stderr

        # Thread-local storage for current task identification
        # This provides defense-in-depth for output attribution
        self._thread_local = threading.local()

    def execute_parallel(
        self,
        tasks: dict[str, Callable[[], Any]],
        phase_name: str,
        log_dir: Path | str | None = None,
    ) -> dict[str, Any]:
        """Execute tasks in parallel while capturing all output per task."""
        global _current_executor

        if not tasks:
            return {}

        # Set module-level executor reference so get_current_task_name() works
        _current_executor = self

        self._reset_state(tasks)
        self._start_consumer(phase_name)

        for name in tasks:
            self._record_line(name, "Task queued")

        future_to_name = {}

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                for name, task in tasks.items():
                    future = pool.submit(self._wrap_task, name, task)
                    future_to_name[future] = name

                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        result = future.result()
                        with self._state_lock:
                            self.results[name] = result
                            self.status[name] = "✅ Completed"
                            self.finish_times[name] = time.time()
                        self._record_line(name, "[status] ✅ Completed")
                    except Exception as exc:  # pragma: no cover - defensive
                        with self._state_lock:
                            self.results[name] = None
                            self.status[name] = f"❌ Failed: {exc}"[:200]
                            self.finish_times[name] = time.time()
                        self._record_line(name, f"[status] ❌ Failed: {exc}")
        finally:
            self._stop_consumer()
            # Clear module-level executor reference
            _current_executor = None

        log_paths = self._write_logs(phase_name, log_dir)
        self._print_summary(phase_name, log_paths)

        return dict(self.results)

    def _wrap_task(self, name: str, task: Callable[[], Any]) -> Any:
        """Run a single task with stdout/stderr capture.

        Sets thread-local task name for defense-in-depth output attribution.
        Even if redirect_stdout races with another thread, we can still identify
        which task this thread is running via get_current_task_name().
        """
        # Set thread-local task name for defense-in-depth
        self._thread_local.current_task = name

        with self._state_lock:
            self.start_times[name] = time.time()
        self.update_status(name, "🔄 Running...")

        stdout_stream = _TaskStream(self, name, "stdout")
        stderr_stream = _TaskStream(self, name, "stderr")

        with (
            contextlib.redirect_stdout(stdout_stream),  # type: ignore[type-var]
            contextlib.redirect_stderr(stderr_stream),  # type: ignore[type-var]
        ):
            try:
                self._record_line(name, "Task started")
                result = task()
            except Exception:  # pragma: no cover - ensures trace logged
                self._record_line(name, "[stderr] Task raised an exception")
                tb = traceback.format_exc().strip().splitlines()
                for line in tb:
                    self._record_line(name, f"[stderr] {line}")
                raise
            finally:
                stdout_stream.flush()
                stderr_stream.flush()
                # Clear thread-local task name
                self._thread_local.current_task = None

        return result

    def add_output(self, name: str, message: str) -> None:
        """Record a log line for a task."""
        self._record_line(name, message)

    def create_output_callback(self, task_name: str) -> Callable[[str], None]:
        """
        Create a thread-safe output callback for a specific task.

        This callback routes output directly to _record_line(), bypassing
        the thread-unsafe redirect_stdout mechanism. Use this when creating
        SystemUnderTest instances during parallel execution to ensure output
        is correctly attributed to the right task.

        Args:
            task_name: Name of the task this callback is for

        Returns:
            A callable that takes a message string and records it for the task

        Example:
            callback = executor.create_output_callback("exasol")
            system = create_system(config, output_callback=callback)
            # Now system._log() will route to the correct task buffer
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

    def _validate_output_isolation(self) -> list[str]:
        """
        Validate that no output cross-contamination occurred.

        Checks output buffers for obvious signs of contamination, such as
        one task's output appearing in another task's buffer.

        Returns:
            List of warning messages if contamination detected, empty list if clean
        """
        warnings: list[str] = []

        for name, lines in self.output_buffers.items():
            for other_name in self.output_buffers:
                if other_name != name:
                    # Check for obvious contamination patterns:
                    # 1. Other task's tag appearing in this buffer
                    # 2. "Processing {other_name}" appearing in this buffer
                    for line in lines:
                        if f"[{other_name}]" in line:
                            warnings.append(
                                f"Possible contamination: [{other_name}] tag found in {name}'s buffer"
                            )
                            break
                        if f"Processing {other_name}" in line:
                            warnings.append(
                                f"Possible contamination: '{other_name}' processing message in {name}'s buffer"
                            )
                            break

        return warnings

    def update_status(self, name: str, status: str) -> None:
        """Update task status and record it."""
        with self._state_lock:
            self.status[name] = status
        self._record_line(name, f"[status] {status}")

    # Internal helpers -------------------------------------------------

    def _reset_state(self, tasks: dict[str, Callable[[], Any]]) -> None:
        current = time.time()
        self.output_buffers = {name: [] for name in tasks}
        self.status = dict.fromkeys(tasks, "⏳ Pending")
        self.start_times = dict.fromkeys(tasks, current)
        self.finish_times = {}
        self.results = {}
        self._output_locks = {name: threading.Lock() for name in tasks}
        self._log_paths = {}
        self._buffer_overflow = dict.fromkeys(tasks, False)

    def _start_consumer(self, phase_name: str) -> None:
        # Bounded queue to prevent unbounded memory growth
        # 10000 items should be sufficient for typical workloads while preventing memory exhaustion
        self._queue = queue.Queue(maxsize=10000)
        self._consumer_thread = threading.Thread(
            target=self._consume_events,
            name=f"parallel-logger-{self._slugify(phase_name)}",
            daemon=True,
        )
        self._consumer_thread.start()
        self._print_line("", use_original=True)
        self._print_line(f"== {phase_name} ==", use_original=True)

    def _stop_consumer(self) -> None:
        if not self._queue:
            return
        try:
            # Send sentinel to stop consumer
            self._queue.put(None, timeout=5.0)
        except queue.Full:
            # Queue is full, consumer might be stuck
            self._write_direct(
                "Warning: Queue full, consumer may be stuck\n",
                stream="stderr",
            )

        # Wait for queue to be processed with timeout
        # Use a loop to check periodically instead of blocking indefinitely
        timeout = 30.0  # 30 seconds total timeout
        start_time = time.time()
        while self._queue.unfinished_tasks > 0:
            if time.time() - start_time > timeout:
                self._write_direct(
                    "Warning: Queue processing timeout, some messages may be lost\n",
                    stream="stderr",
                )
                break
            time.sleep(0.1)

        # Wait for consumer thread to finish with timeout
        if self._consumer_thread:
            self._consumer_thread.join(timeout=5.0)
            if self._consumer_thread.is_alive():
                self._write_direct(
                    "Warning: Consumer thread did not stop cleanly\n",
                    stream="stderr",
                )

        self._consumer_thread = None
        self._queue = None

    def _consume_events(self) -> None:
        assert self._queue is not None
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    self._queue.task_done()
                    break
                name, message = item
                # Check if message is already tagged from remote side
                # to avoid double-tagging (e.g., "[exasol] [exasol] message")
                expected_prefix = f"[{name}]"
                if message and message.startswith(expected_prefix):
                    # Message already has the correct tag, pass through
                    line = message
                elif message:
                    # Add tag prefix for untagged messages
                    line = f"{expected_prefix} {message}"
                else:
                    line = expected_prefix
                self._print_line(line, use_original=True)
            except Exception:
                # Ensure task_done is always called even if printing fails
                # to prevent deadlock in queue.join()
                pass
            finally:
                if item is not None:
                    self._queue.task_done()

    def _record_line(self, name: str, message: str) -> None:
        clean = message.rstrip("\n\r")

        lock = self._output_locks.get(name)
        if lock is None:
            lock = self._output_locks.setdefault(name, threading.Lock())
            self.output_buffers.setdefault(name, [])
            self._buffer_overflow.setdefault(name, False)

        with lock:
            buffer = self.output_buffers.setdefault(name, [])

            # Enforce buffer size limit to prevent memory exhaustion
            if len(buffer) < self.MAX_BUFFER_LINES:
                buffer.append(clean)
            elif not self._buffer_overflow.get(name, False):
                # First time hitting limit, add warning message
                buffer.append(
                    f"[WARNING: Output buffer limit reached ({self.MAX_BUFFER_LINES} lines), truncating further output]"
                )
                self._buffer_overflow[name] = True

        if self._queue:
            try:
                # Use timeout to prevent blocking indefinitely if queue is full
                self._queue.put((name, clean), timeout=1.0)
            except queue.Full:
                # Queue is full, skip this message to prevent blocking
                # Message is still in output_buffers for file logging (if not truncated)
                pass

    def _write_logs(
        self, phase_name: str, base_log_dir: Path | str | None
    ) -> dict[str, Path]:
        if not base_log_dir:
            return {}

        log_paths: dict[str, Path] = {}
        try:
            phase_dir = Path(base_log_dir) / self._slugify(phase_name)
            phase_dir.mkdir(parents=True, exist_ok=True)

            for name, lines in self.output_buffers.items():
                try:
                    filename = f"{self._slugify(name)}.log"
                    path = phase_dir / filename
                    with open(path, "w", encoding="utf-8") as handle:
                        if lines:
                            handle.write("\n".join(lines) + "\n")
                        else:
                            handle.write("")
                    log_paths[name] = path
                except OSError as e:
                    # Log write failed for this task, continue with others
                    # Print error to stderr so it's visible
                    self._write_direct(
                        f"Warning: Failed to write log for {name}: {e}\n",
                        stream="stderr",
                    )

        except OSError as e:
            # Failed to create log directory, return empty dict
            self._write_direct(
                f"Warning: Failed to create log directory: {e}\n",
                stream="stderr",
            )
            return {}

        self._log_paths = log_paths
        return log_paths

    def _print_summary(self, phase_name: str, log_paths: dict[str, Path]) -> None:
        self._print_line(f"== {phase_name} Summary ==", use_original=True)
        for name in sorted(self.status.keys()):
            status = self.status[name]
            finish = self.finish_times.get(name, time.time())
            elapsed = finish - self.start_times.get(name, finish)
            self._print_line(f"- {name}: {status} ({elapsed:.1f}s)", use_original=True)
            path = log_paths.get(name)
            if path:
                self._print_line(f"  log: {path}", use_original=True)
        self._print_line("", use_original=True)

    def _write_direct(self, text: str, stream: str = "stdout") -> None:
        target = self._stdout_original if stream == "stdout" else self._stderr_original
        if target is None:
            return
        target.write(text)
        target.flush()

    def _print_line(self, text: str, use_original: bool = False) -> None:
        with self._print_lock:
            if use_original:
                self._write_direct(text + "\n", stream="stdout")
            else:
                sys.stdout.write(text + "\n")
                sys.stdout.flush()

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
        return slug or "task"
