from __future__ import annotations

import importlib.util
import sys
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


def test_parallel_executor_captures_prints(tmp_path):
    executor = ParallelExecutor(max_workers=2)

    def task_a():
        print("hello from a")
        return "A"

    def task_b():
        sys.stderr.write("error from b\n")
        return "B"

    results = executor.execute_parallel(
        {"task-a": task_a, "task-b": task_b},
        "Test Phase",
        log_dir=tmp_path,
    )

    assert results["task-a"] == "A"
    assert results["task-b"] == "B"

    log_dir = tmp_path / "test-phase"
    log_a = (log_dir / "task-a.log").read_text()
    log_b = (log_dir / "task-b.log").read_text()

    assert "hello from a" in log_a
    assert "[stderr] error from b" in log_b


def test_parallel_executor_add_output(tmp_path):
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
