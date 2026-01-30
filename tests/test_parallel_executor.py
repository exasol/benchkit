"""Tests for ParallelExecutor with file-based logging."""

from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "benchkit" / "run" / "parallel_executor.py"
)
spec = importlib.util.spec_from_file_location(
    "benchkit.run.parallel_executor", MODULE_PATH
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
ParallelExecutor = module.ParallelExecutor


def test_parallel_executor_basic_execution(tmp_path):
    """Test basic parallel execution with file logging."""
    executor = ParallelExecutor(max_workers=2)

    def task_a():
        return "A"

    def task_b():
        return "B"

    results = executor.execute_parallel(
        {"task-a": task_a, "task-b": task_b},
        "Test Phase",
        log_dir=tmp_path,
    )

    assert results["task-a"] == "A"
    assert results["task-b"] == "B"

    # Verify log files were created
    log_dir = tmp_path / "test-phase"
    assert (log_dir / "task-a.log").exists()
    assert (log_dir / "task-b.log").exists()


def test_parallel_executor_add_output(tmp_path):
    """Test add_output writes to log files."""
    executor = ParallelExecutor(max_workers=1)

    def task():
        executor.add_output("custom", "progress step")
        return "done"

    results = executor.execute_parallel(
        {"custom": task},
        "Another Phase",
        log_dir=tmp_path,
    )

    assert results["custom"] == "done"

    log_path = tmp_path / "another-phase" / "custom.log"
    content = log_path.read_text()
    assert "progress step" in content


def test_parallel_executor_failure_logs(tmp_path):
    """Test that failures are properly logged."""
    executor = ParallelExecutor(max_workers=1)

    def ok_task():
        return "ok"

    def failing_task():
        raise RuntimeError("boom")

    results = executor.execute_parallel(
        {"ok": ok_task, "fail": failing_task},
        "Failure Phase",
        log_dir=tmp_path,
    )

    assert results["ok"] == "ok"
    assert results["fail"] is None

    log_path = tmp_path / "failure-phase" / "fail.log"
    content = log_path.read_text()
    assert "RuntimeError" in content or "boom" in content


def test_parallel_executor_callback_routing(tmp_path):
    """Test that create_output_callback routes to correct log file."""
    executor = ParallelExecutor(max_workers=2)

    def make_task(name: str):
        def task():
            callback = executor.create_output_callback(name)
            for i in range(5):
                callback(f"MESSAGE_{name}_{i}")
            return f"{name}_done"

        return task

    tasks = {"alpha": make_task("alpha"), "beta": make_task("beta")}

    results = executor.execute_parallel(tasks, "Callback Test", log_dir=tmp_path)

    assert results["alpha"] == "alpha_done"
    assert results["beta"] == "beta_done"

    log_dir = tmp_path / "callback-test"
    alpha_log = (log_dir / "alpha.log").read_text()
    beta_log = (log_dir / "beta.log").read_text()

    # Alpha's log should have alpha's messages, not beta's
    assert "MESSAGE_alpha_0" in alpha_log
    assert "MESSAGE_beta_0" not in alpha_log

    # Beta's log should have beta's messages, not alpha's
    assert "MESSAGE_beta_0" in beta_log
    assert "MESSAGE_alpha_0" not in beta_log


def test_parallel_executor_no_log_dir():
    """Test execution without log directory."""
    executor = ParallelExecutor(max_workers=1)

    def task():
        return "result"

    results = executor.execute_parallel(
        {"test": task},
        "No Log Phase",
        log_dir=None,
    )

    assert results["test"] == "result"


def test_parallel_executor_empty_tasks():
    """Test with empty tasks dict."""
    executor = ParallelExecutor(max_workers=1)

    results = executor.execute_parallel({}, "Empty Phase", log_dir=None)

    assert results == {}


def test_parallel_executor_status_tracking(tmp_path):
    """Test that status is tracked correctly."""
    executor = ParallelExecutor(max_workers=1)

    def task():
        return "done"

    executor.execute_parallel({"test": task}, "Status Phase", log_dir=tmp_path)

    assert executor.status["test"] == "Completed"
    assert "test" in executor.finish_times
    assert "test" in executor.start_times
