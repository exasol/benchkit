"""
Tests for parallel output tagging to detect and prevent cross-contamination.

These tests verify that when multiple systems run in parallel, their output is
correctly isolated to their own log files without cross-contamination.

ARCHITECTURE:
The framework uses file-based logging with explicit callbacks:

1. Each task gets its own FileLogger that writes to a dedicated log file
2. Output goes through explicit callbacks (create_output_callback)
3. FileLogger handles markup stripping for clean log files
4. TailMonitor displays real-time progress by reading log files

This approach avoids the race conditions inherent in redirect_stdout.
"""

from __future__ import annotations

import importlib.util
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

# Import ParallelExecutor from the module
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


# ==============================================================================
# Test 1: Output callback isolates correctly
# ==============================================================================


def test_output_callback_isolates_parallel_output(tmp_path: Path):
    """
    Verify that using output_callback correctly isolates output from parallel
    tasks with zero cross-contamination in log files.
    """
    executor = ParallelExecutor(max_workers=4)

    def make_task_with_callback(name: str) -> Callable[[], str]:
        """Create a task that uses executor.add_output()."""

        def task() -> str:
            for i in range(100):
                executor.add_output(name, f"CALLBACK_OUTPUT_{name}_{i}")
            return f"{name}_done"

        return task

    tasks = {f"system_{i}": make_task_with_callback(f"system_{i}") for i in range(4)}

    results = executor.execute_parallel(tasks, "Callback Test", log_dir=tmp_path)

    # Verify all tasks completed
    assert all(r == f"{name}_done" for name, r in results.items())

    # Verify ZERO cross-contamination in log files
    log_dir = tmp_path / "callback-test"
    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        assert log_path.exists(), f"Log file for {name} should exist"

        log_content = log_path.read_text()

        # This task's output MUST be present
        assert (
            f"CALLBACK_OUTPUT_{name}_0" in log_content
        ), f"Log for {name} should contain its own output"

        # Other tasks' output MUST NOT be present
        for other_name in tasks:
            if other_name != name:
                assert (
                    f"CALLBACK_OUTPUT_{other_name}" not in log_content
                ), f"Log for {name} should NOT contain output from {other_name}"


# ==============================================================================
# Test 2: create_output_callback() works correctly
# ==============================================================================


def test_create_output_callback_routes_correctly(tmp_path: Path):
    """
    Verify that create_output_callback() creates a callback that routes
    output to the correct task's log file.
    """
    executor = ParallelExecutor(max_workers=2)

    def make_task(name: str) -> Callable[[], str]:
        def task() -> str:
            callback = executor.create_output_callback(name)
            for i in range(50):
                callback(f"MESSAGE_VIA_CALLBACK_{name}_{i}")
            return f"{name}_complete"

        return task

    tasks = {
        "alpha": make_task("alpha"),
        "beta": make_task("beta"),
    }

    results = executor.execute_parallel(
        tasks, "Callback Factory Test", log_dir=tmp_path
    )

    assert results["alpha"] == "alpha_complete"
    assert results["beta"] == "beta_complete"

    log_dir = tmp_path / "callback-factory-test"

    alpha_log = (log_dir / "alpha.log").read_text()
    beta_log = (log_dir / "beta.log").read_text()

    # Alpha's log should have alpha's messages, not beta's
    assert "MESSAGE_VIA_CALLBACK_alpha_0" in alpha_log
    assert "MESSAGE_VIA_CALLBACK_beta_0" not in alpha_log

    # Beta's log should have beta's messages, not alpha's
    assert "MESSAGE_VIA_CALLBACK_beta_0" in beta_log
    assert "MESSAGE_VIA_CALLBACK_alpha_0" not in beta_log


# ==============================================================================
# Test 3: Stress test with many parallel systems
# ==============================================================================


def test_parallel_output_stress_test(tmp_path: Path):
    """
    Stress test with 8 concurrent tasks to verify no cross-contamination
    under high load.
    """
    num_tasks = 8
    iterations_per_task = 500

    executor = ParallelExecutor(max_workers=num_tasks)

    def make_task(name: str) -> Callable[[], dict]:
        def task() -> dict:
            callback = executor.create_output_callback(name)
            for i in range(iterations_per_task):
                callback(
                    f"[STRESS:{name}] iteration={i} task_id={name} marker=UNIQUE_{name}_{i}"
                )
            return {"task": name, "iterations": iterations_per_task}

        return task

    tasks = {f"task_{i:02d}": make_task(f"task_{i:02d}") for i in range(num_tasks)}

    results = executor.execute_parallel(tasks, "Stress Test", log_dir=tmp_path)

    # Verify all tasks completed
    assert len(results) == num_tasks
    for name, result in results.items():
        assert result["task"] == name
        assert result["iterations"] == iterations_per_task

    # Verify ZERO cross-contamination
    log_dir = tmp_path / "stress-test"
    contamination_found = []

    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        log_content = log_path.read_text()

        # Count own messages
        own_count = log_content.count(f"task_id={name}")

        # Check for contamination from other tasks
        for other_name in tasks:
            if other_name != name:
                other_count = log_content.count(f"task_id={other_name}")
                if other_count > 0:
                    contamination_found.append(
                        f"{name}'s log contains {other_count} messages from {other_name}"
                    )

        # Verify we got our own messages
        assert (
            own_count >= iterations_per_task * 0.95
        ), f"{name} should have at least 95% of its {iterations_per_task} messages, got {own_count}"

    assert not contamination_found, "Cross-contamination detected:\n" + "\n".join(
        contamination_found
    )


# ==============================================================================
# Test 4: SystemUnderTest._log() uses callback when provided
# ==============================================================================


def test_system_log_uses_callback_when_provided():
    """
    Verify that SystemUnderTest._log() uses the output_callback when provided.
    """
    base_module_path = (
        Path(__file__).resolve().parents[1] / "benchkit" / "systems" / "base.py"
    )
    spec = importlib.util.spec_from_file_location(
        "benchkit.systems.base", base_module_path
    )
    base_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(base_module)
    SystemUnderTest = base_module.SystemUnderTest

    class MockSystem(SystemUnderTest):
        def start(self) -> bool:
            return True

        def is_healthy(self, quiet: bool = False) -> bool:
            return True

        def create_schema(self, schema_name: str) -> bool:
            return True

        def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
            return True

        def load_data_from_iterable(
            self, table_name: str, data_source: Any, **kwargs: Any
        ) -> bool:
            return True

        def execute_query(
            self,
            query: str,
            query_name: str | None = None,
            return_data: bool = False,
            timeout: int | None = None,
        ) -> dict:
            return {"success": True}

        def get_system_metrics(self) -> dict:
            return {}

        def teardown(self) -> bool:
            return True

    callback_messages: list[str] = []

    def test_callback(message: str) -> None:
        callback_messages.append(message)

    config = {
        "name": "test_system",
        "kind": "mock",
        "version": "1.0",
        "setup": {"method": "docker"},
    }
    system_with_callback = MockSystem(config, output_callback=test_callback)

    system_with_callback._log("Message 1")
    system_with_callback._log("Message 2")
    system_with_callback._log("Message 3")

    assert len(callback_messages) == 3
    assert callback_messages[0] == "Message 1"
    assert callback_messages[1] == "Message 2"
    assert callback_messages[2] == "Message 3"


# ==============================================================================
# Test 5: Integration test simulating parallel system setup
# ==============================================================================


def test_parallel_system_setup_simulation(tmp_path: Path):
    """
    Integration test simulating actual parallel system setup.
    """
    base_module_path = (
        Path(__file__).resolve().parents[1] / "benchkit" / "systems" / "base.py"
    )
    spec = importlib.util.spec_from_file_location(
        "benchkit.systems.base", base_module_path
    )
    base_module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(base_module)
    SystemUnderTest = base_module.SystemUnderTest

    class SimulatedDatabaseSystem(SystemUnderTest):
        def start(self) -> bool:
            return True

        def is_healthy(self, quiet: bool = False) -> bool:
            return True

        def create_schema(self, schema_name: str) -> bool:
            return True

        def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
            return True

        def load_data_from_iterable(
            self, table_name: str, data_source: Any, **kwargs: Any
        ) -> bool:
            return True

        def execute_query(
            self,
            query: str,
            query_name: str | None = None,
            return_data: bool = False,
            timeout: int | None = None,
        ) -> dict:
            return {"success": True}

        def get_system_metrics(self) -> dict:
            return {}

        def teardown(self) -> bool:
            return True

        def simulate_setup(self) -> bool:
            self._log(f"Starting setup for {self.name}...")
            self._log(f"Checking if {self.name} is already installed...")
            for i in range(20):
                self._log(f"[{self.name}] Installation step {i}/20")
            self._log(f"Setup complete for {self.name}")
            return True

    executor = ParallelExecutor(max_workers=4)

    def make_system_setup_task(system_name: str) -> Callable[[], dict]:
        def task() -> dict:
            callback = executor.create_output_callback(system_name)
            config = {
                "name": system_name,
                "kind": "simulated",
                "version": "1.0",
                "setup": {"method": "docker"},
            }
            system = SimulatedDatabaseSystem(config, output_callback=callback)
            success = system.simulate_setup()
            return {"system": system_name, "success": success}

        return task

    system_names = ["exasol", "clickhouse", "postgres", "mysql"]
    tasks = {name: make_system_setup_task(name) for name in system_names}

    results = executor.execute_parallel(
        tasks, "System Setup Simulation", log_dir=tmp_path
    )

    for name, result in results.items():
        assert result["success"], f"System {name} setup should succeed"
        assert result["system"] == name

    log_dir = tmp_path / "system-setup-simulation"

    for name in system_names:
        log_path = log_dir / f"{name}.log"
        log_content = log_path.read_text()

        assert f"Starting setup for {name}" in log_content
        assert f"[{name}] Installation step" in log_content

        for other_name in system_names:
            if other_name != name:
                assert f"Starting setup for {other_name}" not in log_content
                assert f"[{other_name}] Installation step" not in log_content


# ==============================================================================
# Test 6: High-frequency output doesn't cause data loss
# ==============================================================================


def test_high_frequency_output_no_data_loss(tmp_path: Path):
    """
    Verify that rapid output from multiple tasks doesn't cause data loss.
    """
    executor = ParallelExecutor(max_workers=4)

    messages_per_task = 1000
    num_tasks = 4

    def make_task(name: str) -> Callable[[], int]:
        def task() -> int:
            callback = executor.create_output_callback(name)
            for i in range(messages_per_task):
                callback(f"MSG_{name}_{i:04d}")
            return messages_per_task

        return task

    tasks = {f"task_{i}": make_task(f"task_{i}") for i in range(num_tasks)}

    results = executor.execute_parallel(tasks, "High Frequency Test", log_dir=tmp_path)

    for _name, count in results.items():
        assert count == messages_per_task

    log_dir = tmp_path / "high-frequency-test"
    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        log_content = log_path.read_text()

        captured_count = log_content.count(f"MSG_{name}_")

        assert (
            captured_count >= messages_per_task * 0.99
        ), f"Expected at least {messages_per_task * 0.99} messages for {name}, got {captured_count}"


# ==============================================================================
# Test 7: No double-tagging of pre-tagged output
# ==============================================================================


def test_no_double_tagging(tmp_path: Path):
    """
    Verify that output already tagged is not double-tagged.
    """
    executor = ParallelExecutor(max_workers=2)

    def make_task(name: str) -> Callable[[], str]:
        def task() -> str:
            # Simulate receiving pre-tagged output
            pre_tagged_messages = [
                f"[{name}] Query Q01 starting...",
                f"[{name}] Query Q01 completed in 1.5s",
                f"[{name}] Query Q02 starting...",
                f"[{name}] Query Q02 completed in 2.3s",
            ]
            for msg in pre_tagged_messages:
                executor.add_output(name, msg)

            executor.add_output(name, "Internal checkpoint reached")

            return f"{name}_done"

        return task

    tasks = {
        "exasol": make_task("exasol"),
        "clickhouse": make_task("clickhouse"),
    }

    results = executor.execute_parallel(tasks, "Double Tag Test", log_dir=tmp_path)

    assert results["exasol"] == "exasol_done"
    assert results["clickhouse"] == "clickhouse_done"

    log_dir = tmp_path / "double-tag-test"

    for name in ["exasol", "clickhouse"]:
        log_path = log_dir / f"{name}.log"
        log_content = log_path.read_text()

        # Should NOT have double tags
        double_tag = f"[{name}] [{name}]"
        assert double_tag not in log_content, f"Found double-tag in {name}'s log"

        # Should have query messages
        assert f"[{name}] Query Q01" in log_content


# ==============================================================================
# Test 8: Thread-local context correctly identifies current task
# ==============================================================================


def test_thread_local_task_identification(tmp_path: Path):
    """
    Verify that thread-local storage correctly identifies the current task.
    """
    import time

    executor = ParallelExecutor(max_workers=4)

    thread_task_mapping: dict[int, str] = {}
    mapping_lock = threading.Lock()

    def make_task(name: str) -> Callable[[], dict]:
        def task() -> dict:
            thread_id = threading.get_ident()
            with mapping_lock:
                thread_task_mapping[thread_id] = name

            for i in range(10):
                time.sleep(0.01)
                executor.add_output(
                    name, f"Thread {thread_id} working on {name}, step {i}"
                )

            return {"name": name, "thread_id": thread_id}

        return task

    tasks = {f"task_{i}": make_task(f"task_{i}") for i in range(4)}

    results = executor.execute_parallel(tasks, "Thread Local Test", log_dir=tmp_path)

    for name, result in results.items():
        assert result["name"] == name

    log_dir = tmp_path / "thread-local-test"
    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        log_content = log_path.read_text()

        assert f"working on {name}" in log_content

        for other_name in tasks:
            if other_name != name:
                assert f"working on {other_name}" not in log_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
