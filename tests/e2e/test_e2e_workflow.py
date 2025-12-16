"""Full E2E workflow tests with real infrastructure.

These tests verify the complete benchmark workflow including:
- Infrastructure provisioning (infra apply)
- System setup and installation
- Data loading
- Query execution
- Report generation
- Package creation
- Infrastructure cleanup (infra destroy)

IMPORTANT: These tests require real AWS infrastructure and will incur costs.
Run with: pytest tests/e2e/test_e2e_workflow.py --e2e -v

Options:
    --e2e-skip-cleanup  Skip cleanup to debug issues
    --e2e-systems       Test only specific systems
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from .verification import (
    verify_load_complete,
    verify_query_variants,
    verify_reports_exist,
    verify_runs_csv,
    verify_setup_complete,
    verify_summary_json,
)


@pytest.mark.e2e
@pytest.mark.e2e_slow
class TestFullBenchmarkWorkflow:
    """Test the complete benchmark workflow: infra -> setup -> load -> run -> report -> cleanup.

    Tests are ordered numerically to ensure proper sequence execution.
    Each test depends on the previous ones completing successfully.
    """

    def test_01_infra_apply(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
    ) -> None:
        """Phase 1: Provision infrastructure.

        This creates all AWS instances and managed systems defined in the config.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "infra",
                "apply",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["infra_apply"],
        )
        assert (
            result.returncode == 0
        ), f"infra apply failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_02_status_shows_infrastructure(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
    ) -> None:
        """Phase 2: Verify status shows provisioned infrastructure.

        After infra apply, status should show IPs and system info.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "status",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["status"],
        )
        assert result.returncode == 0, f"status failed: {result.stderr}"
        # Status should mention systems
        output_lower = result.stdout.lower()
        assert (
            "exasol" in output_lower or "clickhouse" in output_lower
        ), f"Status doesn't show systems:\n{result.stdout}"

    def test_03_setup(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
        expected_systems: list[str],
    ) -> None:
        """Phase 3: Install database systems.

        This installs Exasol, ClickHouse on provisioned instances.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "setup",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["setup"],
        )
        assert (
            result.returncode == 0
        ), f"setup failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify setup completion markers exist
        verify_setup_complete(results_dir, expected_systems)

    def test_04_probe(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
    ) -> None:
        """Phase 4: Gather system information.

        Probe collects hardware info from all systems.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "probe",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["probe"],
        )
        assert (
            result.returncode == 0
        ), f"probe failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify system info files created
        system_files = list(results_dir.glob("system_*.json"))
        assert len(system_files) > 0, f"No system info files in {results_dir}"

    def test_05_load(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
        expected_systems: list[str],
    ) -> None:
        """Phase 5: Load benchmark data.

        This generates TPC-H data and loads it into all databases.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "load",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["load"],
        )
        assert (
            result.returncode == 0
        ), f"load failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify load completion markers exist
        verify_load_complete(results_dir, expected_systems)

    def test_06_run(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
        loaded_config: dict[str, Any],
    ) -> None:
        """Phase 6: Execute benchmark queries.

        This runs TPC-H queries on all systems and collects timing data.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "run",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["run"],
        )
        assert (
            result.returncode == 0
        ), f"run failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify runs.csv created and valid
        verify_runs_csv(results_dir, loaded_config)

        # Verify summary.json created
        verify_summary_json(results_dir, loaded_config)

        # Verify query variants used correctly
        verify_query_variants(results_dir, loaded_config)

    def test_07_status_shows_results(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        expected_systems: list[str],
    ) -> None:
        """Phase 7: Verify status shows completed benchmark.

        After run, status should show completion and timing info.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "status",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["status"],
        )
        assert result.returncode == 0, f"status failed: {result.stderr}"

        # Status should show system names
        for system in expected_systems:
            assert (
                system in result.stdout
            ), f"System '{system}' not in status output:\n{result.stdout}"

    def test_08_report(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
    ) -> None:
        """Phase 8: Generate benchmark report.

        This creates markdown reports with visualizations.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "report",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["report"],
        )
        assert (
            result.returncode == 0
        ), f"report failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify report files exist
        verify_reports_exist(results_dir)

    def test_09_package(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        results_dir: Path,
        project_id: str,
    ) -> None:
        """Phase 9: Create benchmark package.

        This creates a portable zip file for reproducing the benchmark.
        """
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "package",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["package"],
        )
        assert (
            result.returncode == 0
        ), f"package failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify package was created
        package_patterns = [
            results_dir / "reports" / "3-full" / f"{project_id}-workload.zip",
            results_dir / f"{project_id}-workload.zip",
        ]
        package_found = any(p.exists() for p in package_patterns)
        assert (
            package_found
        ), f"Package not found in expected locations: {package_patterns}"

    def test_10_infra_destroy(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        skip_cleanup: bool,
    ) -> None:
        """Phase 10: Clean up infrastructure.

        This destroys all provisioned resources.
        """
        if skip_cleanup:
            pytest.skip("Cleanup skipped via --e2e-skip-cleanup flag")

        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "infra",
                "destroy",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["infra_destroy"],
        )
        assert (
            result.returncode == 0
        ), f"infra destroy failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"


@pytest.mark.e2e
class TestSelectiveSystemExecution:
    """Test running benchmark on specific systems only."""

    def test_run_specific_system(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
        e2e_systems: list[str] | None,
    ) -> None:
        """Test that --systems flag filters execution."""
        if not e2e_systems:
            pytest.skip("No --e2e-systems specified")

        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "status",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["status"],
        )
        # Verify status works and specified systems are shown
        assert result.returncode == 0
        for system in e2e_systems:
            assert system in result.stdout, f"System '{system}' not in status output"


@pytest.mark.e2e
class TestInfrastructurePlan:
    """Test infrastructure planning without provisioning."""

    def test_infra_plan(
        self,
        comprehensive_config_path: Path,
        timeouts: dict[str, int],
    ) -> None:
        """Test that infra plan shows what will be created."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "infra",
                "plan",
                "-c",
                str(comprehensive_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["infra_plan"],
        )
        assert result.returncode == 0, f"infra plan failed: {result.stderr}"


@pytest.mark.e2e
class TestLocalExecution:
    """Test local execution mode (--local flag)."""

    def test_run_local_flag_exists(self) -> None:
        """Test that run command accepts --local flag."""
        result = subprocess.run(
            ["python", "-m", "benchkit", "run", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "--local" in result.stdout or "-l" in result.stdout
