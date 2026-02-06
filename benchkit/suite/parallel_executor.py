"""Parallel executor for suite benchmark execution.

Orchestrates concurrent execution of multiple benchmarks with:
- Per-benchmark file-based logging
- Real-time progress display via TailMonitor
- Thread-safe state updates
"""

import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from ..run.file_logger import FileLogger
from ..run.tail_monitor import TailMonitor


@dataclass
class SuiteBenchmarkTask:
    """Represents a benchmark to execute within a suite."""

    benchmark_id: str  # e.g., "series1/benchmark_name"
    config_path: Path
    project_id: str
    no_cleanup: bool
    systems_filter: str | None


class SuiteParallelExecutor:
    """Parallel executor for suite benchmarks with file-based logging.

    Uses ThreadPoolExecutor to run multiple benchmarks concurrently,
    with each benchmark writing to its own log file. TailMonitor
    displays real-time progress from all running benchmarks.
    """

    def __init__(self, max_workers: int, log_dir: Path, console: Console | None = None):
        """Initialize the parallel executor.

        Args:
            max_workers: Maximum concurrent benchmarks
            log_dir: Directory for per-benchmark log files
            console: Rich console for display (uses default if not provided)
        """
        self.max_workers = max_workers
        self.log_dir = log_dir
        self.console = console or Console()
        self._file_loggers: dict[str, FileLogger] = {}
        self._log_paths: dict[str, Path] = {}
        self._results_lock = threading.Lock()

    def execute_benchmarks(
        self,
        tasks: list[SuiteBenchmarkTask],
        run_func: Callable[[SuiteBenchmarkTask, Callable[[str], None]], bool],
        continue_on_failure: bool = True,
        benchmark_timeout: int = 0,
    ) -> dict[str, bool]:
        """Execute benchmarks in parallel with progress tracking.

        Args:
            tasks: List of benchmark tasks to execute
            run_func: Function that executes a single benchmark.
                      Takes (task, log_callback) and returns success boolean.
            continue_on_failure: If False, stop all benchmarks on first failure
            benchmark_timeout: Max seconds to wait for each benchmark result.
                             0 means no timeout (wait indefinitely).

        Returns:
            Dictionary mapping benchmark_id to success boolean
        """
        if not tasks:
            return {}

        # Setup log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create file loggers for each benchmark
        for task in tasks:
            # Replace / with _ for filesystem-safe log names
            log_name = task.benchmark_id.replace("/", "_")
            log_path = self.log_dir / f"{log_name}.log"
            self._log_paths[task.benchmark_id] = log_path
            logger = FileLogger(log_path)
            logger.open()
            self._file_loggers[task.benchmark_id] = logger

        # Start tail monitor for real-time display
        monitor = TailMonitor(self._log_paths, self.console)
        monitor.start()

        results: dict[str, bool] = {}
        start_time = time.time()

        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
                future_to_task = {
                    pool.submit(
                        self._wrap_task, task, run_func, continue_on_failure
                    ): task
                    for task in tasks
                }

                # Use timeout if set (0 = no timeout)
                result_timeout = benchmark_timeout if benchmark_timeout > 0 else None

                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        success = future.result(timeout=result_timeout)
                        with self._results_lock:
                            results[task.benchmark_id] = success
                    except TimeoutError:
                        with self._results_lock:
                            results[task.benchmark_id] = False
                        self._file_loggers[task.benchmark_id].write(
                            f"[error] Benchmark timed out after {benchmark_timeout}s"
                        )
                    except Exception as e:
                        with self._results_lock:
                            results[task.benchmark_id] = False
                        self._file_loggers[task.benchmark_id].write(
                            f"[error] Fatal exception: {e}"
                        )
        finally:
            # Stop monitor and close loggers
            monitor.stop()
            for logger in self._file_loggers.values():
                logger.close()

        # Print summary
        elapsed = time.time() - start_time
        self._print_summary(results, elapsed)

        return results

    def _wrap_task(
        self,
        task: SuiteBenchmarkTask,
        run_func: Callable[[SuiteBenchmarkTask, Callable[[str], None]], bool],
        continue_on_failure: bool,
    ) -> bool:
        """Wrap benchmark execution with logging.

        Args:
            task: Benchmark task to execute
            run_func: Function that executes the benchmark
            continue_on_failure: Whether to continue on failure

        Returns:
            True if benchmark succeeded
        """
        logger = self._file_loggers[task.benchmark_id]
        log_callback = logger.create_callback()

        log_callback(f"Starting benchmark: {task.benchmark_id}")
        log_callback(f"Config: {task.config_path}")
        log_callback(f"Project ID: {task.project_id}")
        if task.systems_filter:
            log_callback(f"Systems filter: {task.systems_filter}")

        try:
            success = run_func(task, log_callback)
            status = "completed" if success else "failed"
            log_callback(f"[status] Benchmark {status}")
            return success
        except Exception as e:
            log_callback(f"[error] Benchmark failed with exception: {e}")
            if not continue_on_failure:
                raise
            return False

    def _print_summary(self, results: dict[str, bool], elapsed: float) -> None:
        """Print execution summary.

        Args:
            results: Mapping of benchmark_id to success boolean
            elapsed: Total elapsed time in seconds
        """
        completed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        total = len(results)

        self.console.print()
        self.console.print(
            f"[bold]Parallel execution complete[/bold] " f"({elapsed:.1f}s total)"
        )
        self.console.print(f"  {completed}/{total} succeeded, {failed}/{total} failed")

        if failed > 0:
            self.console.print()
            self.console.print("[bold red]Failed benchmarks:[/bold red]")
            for benchmark_id, success in results.items():
                if not success:
                    log_path = self._log_paths.get(benchmark_id, "")
                    self.console.print(f"  - {benchmark_id}")
                    if log_path:
                        self.console.print(f"    Log: {log_path}")
