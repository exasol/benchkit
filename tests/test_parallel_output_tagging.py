"""
Comprehensive tests for parallel output tagging to detect and prevent race conditions.

These tests verify that when multiple systems run in parallel, their output is
correctly tagged with the appropriate system name (e.g., [exasol], [clickhouse]).

ARCHITECTURE:
The framework uses LOCAL tagging via stream_callback for SSH commands. When executing
commands on remote systems:

1. SSH output is captured line-by-line using subprocess with PIPE
2. Each line is passed to stream_callback(line, "stdout"|"stderr")
3. The callback adds the system tag prefix: f"[{system_name}] {line}"
4. Tagged output is routed through ParallelExecutor for thread-safe display

The ParallelExecutor's _consume_events() detects pre-tagged output and avoids
double-tagging. This prevents "[exasol] [exasol] message" when output already
has a tag prefix.

HISTORICAL NOTE:
A previous implementation tried remote-side tagging (wrapping commands with sed)
but this approach was fundamentally incompatible with heredocs and other complex
shell constructs. Local tagging via callbacks is simpler and works with any command.

THREAD SAFETY:
contextlib.redirect_stdout is NOT thread-safe - it modifies sys.stdout globally.
The stream_callback mechanism bypasses this issue by capturing subprocess output
in Python and routing it through thread-safe queues.
"""

from __future__ import annotations

import contextlib
import importlib.util
import re
import threading
import time
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
# Test 1: Demonstrate the race condition with raw redirect_stdout (documentation)
# ==============================================================================


def test_redirect_stdout_race_condition_demonstration():
    """
    Demonstrate that contextlib.redirect_stdout is NOT thread-safe.

    This test documents the race condition that can occur when multiple threads
    use redirect_stdout simultaneously. It's NOT expected to always fail - the
    race is timing-dependent. But it documents the fundamental issue.

    NOTE: This test is for documentation/demonstration purposes. It may pass
    or fail depending on thread timing. The important tests are the ones that
    verify our fix works.
    """
    import io

    barrier = threading.Barrier(2)  # Synchronize thread starts

    def thread_func(name: str, stream: io.StringIO, iterations: int = 100):
        barrier.wait()  # Start both threads at the same time
        with contextlib.redirect_stdout(stream):
            for i in range(iterations):
                # Print with unique identifier
                print(f"OUTPUT_FROM_{name}_{i}")

    stream_a = io.StringIO()
    stream_b = io.StringIO()

    thread_a = threading.Thread(target=thread_func, args=("THREAD_A", stream_a))
    thread_b = threading.Thread(target=thread_func, args=("THREAD_B", stream_b))

    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()

    output_a = stream_a.getvalue()
    output_b = stream_b.getvalue()

    # Count how many messages ended up in the "wrong" stream
    a_in_b = len(re.findall(r"OUTPUT_FROM_THREAD_A", output_b))
    b_in_a = len(re.findall(r"OUTPUT_FROM_THREAD_B", output_a))

    # This test documents that cross-contamination CAN happen.
    # We don't assert failure because it's timing-dependent.
    # Instead, we just print the results for documentation.
    print(f"\n[RACE CONDITION DEMO] Thread A messages in stream B: {a_in_b}")
    print(f"[RACE CONDITION DEMO] Thread B messages in stream A: {b_in_a}")
    print(
        f"[RACE CONDITION DEMO] Total output in A: {len(output_a.splitlines())} lines"
    )
    print(
        f"[RACE CONDITION DEMO] Total output in B: {len(output_b.splitlines())} lines"
    )

    # The test passes regardless - it's for documentation


# ==============================================================================
# Test 2: Output callback isolates correctly (bypasses redirect_stdout)
# ==============================================================================


def test_output_callback_isolates_parallel_output(tmp_path: Path):
    """
    Verify that using output_callback (bypassing redirect_stdout) correctly
    isolates output from parallel tasks with zero cross-contamination.

    This is the primary mechanism for fixing the race condition.
    """
    executor = ParallelExecutor(max_workers=4)

    def make_task_with_callback(name: str) -> Callable[[], str]:
        """Create a task that uses executor.add_output() instead of print()."""

        def task() -> str:
            # Use executor.add_output() directly - bypasses redirect_stdout
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
# Test 3: ParallelExecutor.create_output_callback() works correctly
# ==============================================================================


def test_create_output_callback_routes_correctly(tmp_path: Path):
    """
    Verify that create_output_callback() creates a callback that routes
    output to the correct task buffer.
    """
    executor = ParallelExecutor(max_workers=2)

    def make_task(name: str) -> Callable[[], str]:
        def task() -> str:
            # Get callback for this task
            callback = executor.create_output_callback(name)

            # Use callback to output messages
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

    # Verify completion
    assert results["alpha"] == "alpha_complete"
    assert results["beta"] == "beta_complete"

    # Verify correct routing
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
# Test 4: Stress test with many parallel systems
# ==============================================================================


def test_parallel_output_stress_test(tmp_path: Path):
    """
    Stress test with 8+ concurrent tasks to maximize race condition probability.
    Each task outputs hundreds of uniquely-identifiable messages.

    This test uses callback-based output to verify the fix works under load.
    """
    num_tasks = 8
    iterations_per_task = 500

    executor = ParallelExecutor(max_workers=num_tasks)

    def make_task(name: str) -> Callable[[], dict]:
        def task() -> dict:
            callback = executor.create_output_callback(name)
            for i in range(iterations_per_task):
                # Include task name in multiple places for robust detection
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

        # Count own messages (should be ~500)
        own_count = log_content.count(f"task_id={name}")

        # Check for contamination from other tasks
        for other_name in tasks:
            if other_name != name:
                other_count = log_content.count(f"task_id={other_name}")
                if other_count > 0:
                    contamination_found.append(
                        f"{name}'s log contains {other_count} messages from {other_name}"
                    )

        # Verify we got our own messages (allowing some tolerance for task overhead messages)
        assert (
            own_count >= iterations_per_task * 0.95
        ), f"{name} should have at least 95% of its {iterations_per_task} messages, got {own_count}"

    # Fail if any contamination was found
    assert not contamination_found, "Cross-contamination detected:\n" + "\n".join(
        contamination_found
    )


# ==============================================================================
# Test 5: SystemUnderTest._log() uses callback when provided
# ==============================================================================


def test_system_log_uses_callback_when_provided():
    """
    Verify that SystemUnderTest._log() uses the output_callback when provided,
    instead of falling back to print().
    """
    # Import SystemUnderTest base class
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

    # Create a concrete subclass for testing
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

    # Track callback invocations
    callback_messages: list[str] = []

    def test_callback(message: str) -> None:
        callback_messages.append(message)

    # Create system WITH callback
    config = {
        "name": "test_system",
        "kind": "mock",
        "version": "1.0",
        "setup": {"method": "docker"},
    }
    system_with_callback = MockSystem(config, output_callback=test_callback)

    # Call _log() multiple times
    system_with_callback._log("Message 1")
    system_with_callback._log("Message 2")
    system_with_callback._log("Message 3")

    # Verify callback was used
    assert len(callback_messages) == 3
    assert callback_messages[0] == "Message 1"
    assert callback_messages[1] == "Message 2"
    assert callback_messages[2] == "Message 3"

    # Create system WITHOUT callback - verify it falls back to print
    import io

    system_without_callback = MockSystem(config, output_callback=None)

    captured_output = io.StringIO()
    with contextlib.redirect_stdout(captured_output):
        system_without_callback._log("Fallback message")

    assert "Fallback message" in captured_output.getvalue()


# ==============================================================================
# Test 6: Integration test simulating actual parallel system setup
# ==============================================================================


def test_parallel_system_setup_simulation(tmp_path: Path):
    """
    Integration test simulating actual parallel system setup with correct callback passing.

    This simulates what happens in BenchmarkRunner when systems are set up in parallel,
    verifying that the output_callback mechanism works end-to-end.
    """
    # Import SystemUnderTest
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

    # Create concrete mock system class
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
            """Simulate system setup with multiple log messages."""
            self._log(f"Starting setup for {self.name}...")
            self._log(f"Checking if {self.name} is already installed...")
            for i in range(20):
                self._log(f"[{self.name}] Installation step {i}/20")
            self._log(f"Setup complete for {self.name}")
            return True

    executor = ParallelExecutor(max_workers=4)

    def make_system_setup_task(system_name: str) -> Callable[[], dict]:
        def task() -> dict:
            # Get callback from executor (this is what the fix enables)
            callback = executor.create_output_callback(system_name)

            # Create system with callback
            config = {
                "name": system_name,
                "kind": "simulated",
                "version": "1.0",
                "setup": {"method": "docker"},
            }
            system = SimulatedDatabaseSystem(config, output_callback=callback)

            # Run simulated setup
            success = system.simulate_setup()

            return {"system": system_name, "success": success}

        return task

    # Create tasks for multiple "database systems"
    system_names = ["exasol", "clickhouse", "postgres", "mysql"]
    tasks = {name: make_system_setup_task(name) for name in system_names}

    results = executor.execute_parallel(
        tasks, "System Setup Simulation", log_dir=tmp_path
    )

    # Verify all systems set up successfully
    for name, result in results.items():
        assert result["success"], f"System {name} setup should succeed"
        assert result["system"] == name

    # Verify output isolation
    log_dir = tmp_path / "system-setup-simulation"

    for name in system_names:
        log_path = log_dir / f"{name}.log"
        log_content = log_path.read_text()

        # Must contain own messages
        assert (
            f"Starting setup for {name}" in log_content
        ), f"Log for {name} should contain its setup messages"
        assert (
            f"[{name}] Installation step" in log_content
        ), f"Log for {name} should contain its installation steps"

        # Must NOT contain other systems' messages
        for other_name in system_names:
            if other_name != name:
                assert (
                    f"Starting setup for {other_name}" not in log_content
                ), f"Log for {name} should NOT contain {other_name}'s messages"
                assert (
                    f"[{other_name}] Installation step" not in log_content
                ), f"Log for {name} should NOT contain {other_name}'s installation steps"


# ==============================================================================
# Test 7: Thread-local context correctly identifies current task
# ==============================================================================


def test_thread_local_task_identification(tmp_path: Path):
    """
    Verify that thread-local storage correctly identifies the current task
    even when multiple threads are running simultaneously.
    """
    executor = ParallelExecutor(max_workers=4)

    # Track which thread ID was associated with which task
    thread_task_mapping: dict[int, str] = {}
    mapping_lock = threading.Lock()

    def make_task(name: str) -> Callable[[], dict]:
        def task() -> dict:
            thread_id = threading.get_ident()
            with mapping_lock:
                thread_task_mapping[thread_id] = name

            # Simulate some work
            for i in range(10):
                time.sleep(0.01)
                executor.add_output(
                    name, f"Thread {thread_id} working on {name}, step {i}"
                )

            return {"name": name, "thread_id": thread_id}

        return task

    tasks = {f"task_{i}": make_task(f"task_{i}") for i in range(4)}

    results = executor.execute_parallel(tasks, "Thread Local Test", log_dir=tmp_path)

    # Verify each task got a result with correct name
    for name, result in results.items():
        assert result["name"] == name

    # Verify logs don't have cross-contamination
    log_dir = tmp_path / "thread-local-test"
    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        log_content = log_path.read_text()

        # Own task name should appear
        assert f"working on {name}" in log_content

        # Other task names should NOT appear
        for other_name in tasks:
            if other_name != name:
                assert f"working on {other_name}" not in log_content


# ==============================================================================
# Test 8: Validate output isolation detection
# ==============================================================================


def test_validate_output_isolation_detects_contamination():
    """
    Verify that _validate_output_isolation() correctly detects cross-contamination
    when it occurs in output buffers.
    """
    executor = ParallelExecutor(max_workers=2)

    # Manually populate output buffers with contaminated data
    executor.output_buffers = {
        "system_a": [
            "Starting system_a setup...",
            "Processing system_a...",
            "[system_b] This is contamination!",  # Contamination: system_b tag in system_a buffer
            "Finishing system_a setup...",
        ],
        "system_b": [
            "Starting system_b setup...",
            "Processing system_b...",
            "Finishing system_b setup...",
        ],
    }

    # Run validation
    warnings = executor._validate_output_isolation()

    # Should detect the contamination
    assert len(warnings) > 0, "Should detect cross-contamination"
    assert any(
        "system_b" in w and "system_a" in w for w in warnings
    ), "Warning should mention both involved systems"

    # Now test with clean data
    executor.output_buffers = {
        "system_a": [
            "Starting system_a setup...",
            "Processing system_a...",
            "Finishing system_a setup...",
        ],
        "system_b": [
            "Starting system_b setup...",
            "Processing system_b...",
            "Finishing system_b setup...",
        ],
    }

    warnings = executor._validate_output_isolation()
    assert len(warnings) == 0, "Should not detect any contamination in clean data"


# ==============================================================================
# Test 9: High-frequency output doesn't cause data loss
# ==============================================================================


def test_high_frequency_output_no_data_loss(tmp_path: Path):
    """
    Verify that rapid output from multiple tasks doesn't cause data loss
    due to queue or buffer overflow.
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

    # Verify all tasks returned correct count
    for _name, count in results.items():
        assert count == messages_per_task

    # Verify all messages were captured
    log_dir = tmp_path / "high-frequency-test"
    for name in tasks:
        log_path = log_dir / f"{name.replace('_', '-')}.log"
        log_content = log_path.read_text()

        # Count how many messages we captured
        captured_count = log_content.count(f"MSG_{name}_")

        # We should have captured all messages (with some tolerance for overhead messages)
        assert (
            captured_count >= messages_per_task * 0.99
        ), f"Expected at least {messages_per_task * 0.99} messages for {name}, got {captured_count}"


# ==============================================================================
# Test 10: No double-tagging of pre-tagged output
# ==============================================================================


def test_no_double_tagging(tmp_path: Path):
    """
    Verify that output already tagged by stream_callback is not double-tagged
    by the ParallelExecutor's _consume_events().

    This simulates the scenario where:
    1. stream_callback adds [exasol] prefix to each line
    2. The tagged output goes through ParallelExecutor
    3. The executor should NOT add another [exasol] prefix
    """
    executor = ParallelExecutor(max_workers=2)

    def make_task(name: str) -> Callable[[], str]:
        """Create a task that simulates receiving pre-tagged output from stream_callback."""

        def task() -> str:
            # Simulate receiving pre-tagged output from stream_callback
            # This is what happens when stream_callback adds [name] prefix
            pre_tagged_messages = [
                f"[{name}] Query Q01 starting...",
                f"[{name}] Query Q01 completed in 1.5s",
                f"[{name}] Query Q02 starting...",
                f"[{name}] Query Q02 completed in 2.3s",
            ]
            for msg in pre_tagged_messages:
                executor.add_output(name, msg)

            # Also add some untagged messages (internal status updates)
            executor.add_output(name, "Internal checkpoint reached")

            return f"{name}_done"

        return task

    tasks = {
        "exasol": make_task("exasol"),
        "clickhouse": make_task("clickhouse"),
    }

    results = executor.execute_parallel(tasks, "Double Tag Test", log_dir=tmp_path)

    # Verify tasks completed
    assert results["exasol"] == "exasol_done"
    assert results["clickhouse"] == "clickhouse_done"

    # Verify NO double-tagging in logs
    log_dir = tmp_path / "double-tag-test"

    for name in ["exasol", "clickhouse"]:
        log_path = log_dir / f"{name}.log"
        log_content = log_path.read_text()

        # Should NOT have double tags like [exasol] [exasol]
        double_tag = f"[{name}] [{name}]"
        assert (
            double_tag not in log_content
        ), f"Found double-tag '{double_tag}' in {name}'s log"

        # Should have single tags (pre-tagged output passed through)
        assert f"[{name}] Query Q01" in log_content

        # Untagged messages should get tagged once
        # Either as "[name] Internal checkpoint" in log buffer or just "Internal checkpoint"
        # depending on where the check happens - the key is no double-tag


# ==============================================================================
# Test 11: Integration test simulating local tagging via stream_callback
# ==============================================================================


def test_local_tagging_simulation(tmp_path: Path):
    """
    Integration test simulating the full local tagging flow:
    1. SSH output is captured line-by-line
    2. stream_callback adds [system_name] prefix to each line
    3. ParallelExecutor processes without double-tagging
    4. Logs contain correctly tagged output
    """
    executor = ParallelExecutor(max_workers=4)

    def simulate_ssh_execution(system_name: str) -> Callable[[], dict]:
        """
        Simulate what happens when stream_callback adds tags locally.

        In real execution:
        - SSH command runs and output is captured line by line
        - stream_callback is called for each line: callback(line, "stdout")
        - Callback adds prefix: f"[{system_name}] {line}"
        - Tagged line is sent to executor.add_output()

        This test simulates that by adding pre-tagged output directly.
        """

        def task() -> dict:
            # Simulate output that's been tagged by stream_callback
            simulated_tagged_output = [
                f"[{system_name}] Starting database server...",
                f"[{system_name}] Loading configuration from /etc/db/config.yaml",
                f"[{system_name}] Binding to port 5432...",
                f"[{system_name}] Ready to accept connections",
                f"[{system_name}] Running query: SELECT count(*) FROM lineitem",
                f"[{system_name}] Query completed: 6001215 rows in 2.34s",
                f"[{system_name}] Running query: SELECT sum(l_quantity) FROM lineitem",
                f"[{system_name}] Query completed: 1.5e8 in 1.23s",
            ]

            for line in simulated_tagged_output:
                executor.add_output(system_name, line)

            return {
                "system": system_name,
                "queries_run": 2,
                "success": True,
            }

        return task

    # Run multiple systems in parallel
    system_names = ["exasol", "clickhouse", "postgres", "mysql"]
    tasks = {name: simulate_ssh_execution(name) for name in system_names}

    results = executor.execute_parallel(
        tasks, "Local Tagging Simulation", log_dir=tmp_path
    )

    # Verify all systems completed
    assert len(results) == 4
    for name, result in results.items():
        assert result["success"]
        assert result["system"] == name

    # Verify correct tagging in logs
    log_dir = tmp_path / "local-tagging-simulation"

    for name in system_names:
        log_path = log_dir / f"{name}.log"
        log_content = log_path.read_text()

        # Verify this system's output is present
        assert f"[{name}] Starting database server" in log_content
        assert f"[{name}] Query completed" in log_content

        # Verify no double-tagging
        assert f"[{name}] [{name}]" not in log_content

        # Verify no cross-contamination
        for other_name in system_names:
            if other_name != name:
                assert (
                    f"[{other_name}]" not in log_content
                ), f"Found [{other_name}] in {name}'s log"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
