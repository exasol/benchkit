"""Dry-run tests for CLI validation - no infrastructure required.

These tests verify CLI commands work correctly without provisioning infrastructure.
They can be run without the --e2e flag.

Run with: pytest tests/e2e/test_cli_validation.py -v
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.mark.e2e_dryrun
class TestCLICheck:
    """Test the 'check' command validates configs correctly."""

    def test_check_valid_config(
        self, dryrun_config_path: Path, timeouts: dict[str, int]
    ) -> None:
        """Test that check command accepts valid config."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "check",
                "-c",
                str(dryrun_config_path),
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["check"],
        )
        # Check command should succeed
        assert result.returncode == 0, f"check failed: {result.stdout}\n{result.stderr}"

    def test_check_dump_outputs_yaml(
        self, dryrun_config_path: Path, timeouts: dict[str, int]
    ) -> None:
        """Test that check --dump outputs valid YAML config."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "check",
                "-c",
                str(dryrun_config_path),
                "--dump",
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["check"],
        )
        assert result.returncode == 0, f"check --dump failed: {result.stderr}"
        # Output should contain YAML config structure
        assert "systems:" in result.stdout
        assert "workload:" in result.stdout

    def test_check_verbose_shows_details(
        self, dryrun_config_path: Path, timeouts: dict[str, int]
    ) -> None:
        """Test that check --verbose shows configuration details."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "benchkit",
                "check",
                "-c",
                str(dryrun_config_path),
                "--verbose",
            ],
            capture_output=True,
            text=True,
            timeout=timeouts["check"],
        )
        assert result.returncode == 0, f"check --verbose failed: {result.stderr}"

    def test_check_invalid_config_fails(self, tmp_path: Path) -> None:
        """Test that check command rejects invalid config."""
        invalid_config = tmp_path / "invalid.yaml"
        # Empty systems list is invalid
        invalid_config.write_text(
            """
title: "Invalid Config"
author: "Test"
systems: []
workload:
  name: "tpch"
  scale_factor: 1
"""
        )

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(invalid_config)],
            capture_output=True,
            text=True,
        )
        # Should fail validation
        assert result.returncode != 0

    def test_check_missing_file_fails(self, tmp_path: Path) -> None:
        """Test that check command fails for missing config file."""
        missing_config = tmp_path / "nonexistent.yaml"

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(missing_config)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


@pytest.mark.e2e_dryrun
class TestCLIHelp:
    """Test that all CLI commands have proper help documentation."""

    @pytest.mark.parametrize(
        "command",
        [
            "probe",
            "setup",
            "load",
            "run",
            "report",
            "status",
            "check",
            "infra",
            "cleanup",
            "package",
        ],
    )
    def test_command_has_help(self, command: str) -> None:
        """Test that each command provides help."""
        result = subprocess.run(
            ["python", "-m", "benchkit", command, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"{command} --help failed: {result.stderr}"
        # Help should contain usage information
        assert "usage:" in result.stdout.lower() or "--" in result.stdout

    def test_main_help(self) -> None:
        """Test that main benchkit help works."""
        result = subprocess.run(
            ["python", "-m", "benchkit", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Main --help failed: {result.stderr}"
        # Should list available commands
        assert "probe" in result.stdout
        assert "run" in result.stdout


@pytest.mark.e2e_dryrun
class TestConfigValidation:
    """Test configuration validation logic."""

    def test_duplicate_system_names_rejected(self, tmp_path: Path) -> None:
        """Test that duplicate system names are rejected."""
        config_content = """
title: "Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "exasol"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
  - name: "exasol"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
workload:
  name: "tpch"
  scale_factor: 1
"""
        config_path = tmp_path / "duplicate_names.yaml"
        config_path.write_text(config_content)

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(config_path)],
            capture_output=True,
            text=True,
        )
        # Should fail due to duplicate names
        assert result.returncode != 0

    def test_invalid_system_kind_rejected(self, tmp_path: Path) -> None:
        """Test that invalid system kinds are rejected."""
        config_content = """
title: "Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "unknown_db"
    kind: "mongodb"
    version: "6.0"
    setup:
      method: "native"
workload:
  name: "tpch"
  scale_factor: 1
"""
        config_path = tmp_path / "invalid_kind.yaml"
        config_path.write_text(config_content)

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(config_path)],
            capture_output=True,
            text=True,
        )
        # Should fail due to unknown kind
        assert result.returncode != 0

    def test_invalid_workload_rejected(self, tmp_path: Path) -> None:
        """Test that invalid workload names are rejected."""
        config_content = """
title: "Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "exasol"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
workload:
  name: "invalid_workload"
  scale_factor: 1
"""
        config_path = tmp_path / "invalid_workload.yaml"
        config_path.write_text(config_content)

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(config_path)],
            capture_output=True,
            text=True,
        )
        # Should fail due to unknown workload
        assert result.returncode != 0

    def test_valid_local_config_accepted(self, tmp_path: Path) -> None:
        """Test that a valid local config is accepted."""
        config_content = """
title: "Valid Local Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "exasol_test"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
      username: "sys"
      password: "exasol"
      schema: "TEST"
workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
"""
        config_path = tmp_path / "valid_local.yaml"
        config_path.write_text(config_content)

        result = subprocess.run(
            ["python", "-m", "benchkit", "check", "-c", str(config_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Valid config rejected: {result.stderr}"


@pytest.mark.e2e_dryrun
class TestInfraCommands:
    """Test infra command validation (dry-run only)."""

    def test_infra_plan_dry_run_local_mode(self, tmp_path: Path) -> None:
        """Test that infra plan handles local mode config gracefully."""
        config_content = """
title: "Local Mode Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "test_system"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
workload:
  name: "tpch"
  scale_factor: 1
"""
        config_path = tmp_path / "local_mode.yaml"
        config_path.write_text(config_content)

        # infra plan on local mode should indicate no infrastructure needed
        result = subprocess.run(
            ["python", "-m", "benchkit", "infra", "plan", "-c", str(config_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Should succeed or gracefully indicate local mode
        assert result.returncode == 0 or "local" in result.stdout.lower()


@pytest.mark.e2e_dryrun
class TestStatusCommand:
    """Test status command validation."""

    def test_status_no_config(self) -> None:
        """Test that status command works without config (shows all projects)."""
        result = subprocess.run(
            ["python", "-m", "benchkit", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should succeed even with no projects
        assert result.returncode == 0

    def test_status_with_nonexistent_project(self, tmp_path: Path) -> None:
        """Test status with a config for non-existent project."""
        config_content = """
title: "Non-existent Project Test"
author: "Test"
env:
  mode: "local"
systems:
  - name: "test_system"
    kind: "exasol"
    version: "8.35.0"
    setup:
      method: "preinstalled"
      host: "localhost"
      port: 8563
workload:
  name: "tpch"
  scale_factor: 1
"""
        config_path = tmp_path / "nonexistent.yaml"
        config_path.write_text(config_content)

        result = subprocess.run(
            ["python", "-m", "benchkit", "status", "-c", str(config_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should succeed (just show no results)
        assert result.returncode == 0
