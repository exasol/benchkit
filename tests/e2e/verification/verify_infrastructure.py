"""Infrastructure verification functions for E2E tests.

These functions verify that infrastructure provisioning and setup completed correctly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def verify_infrastructure_state(results_dir: Path, phase: str) -> None:
    """Verify that infrastructure phase completed successfully.

    Args:
        results_dir: Results directory path
        phase: Phase to verify ("setup" or "load")

    Raises:
        AssertionError: If verification fails
    """
    if phase == "setup":
        pattern = "setup_complete_*.json"
    elif phase == "load":
        pattern = "load_complete_*.json"
    else:
        raise ValueError(f"Unknown phase: {phase}")

    completion_files = list(results_dir.glob(pattern))
    assert (
        len(completion_files) > 0
    ), f"No {phase} completion markers found in {results_dir}"

    # Verify each completion marker is valid JSON
    for completion_file in completion_files:
        with open(completion_file) as f:
            data = json.load(f)
        assert (
            "system_name" in data or "timestamp" in data
        ), f"Invalid completion marker: {completion_file}"


def verify_setup_complete(results_dir: Path, expected_systems: list[str]) -> None:
    """Verify that setup completed for all expected systems.

    Args:
        results_dir: Results directory path
        expected_systems: List of expected system names

    Raises:
        AssertionError: If setup verification fails
    """
    for system in expected_systems:
        setup_file = results_dir / f"setup_complete_{system}.json"
        assert (
            setup_file.exists()
        ), f"Setup completion file not found for system '{system}': {setup_file}"

        with open(setup_file) as f:
            data = json.load(f)

        # Verify timestamp exists (indicates completion)
        assert (
            "timestamp" in data
        ), f"Missing timestamp in setup completion for {system}"


def verify_load_complete(results_dir: Path, expected_systems: list[str]) -> None:
    """Verify that data loading completed for all expected systems.

    Args:
        results_dir: Results directory path
        expected_systems: List of expected system names

    Raises:
        AssertionError: If load verification fails
    """
    for system in expected_systems:
        load_file = results_dir / f"load_complete_{system}.json"
        assert (
            load_file.exists()
        ), f"Load completion file not found for system '{system}': {load_file}"

        with open(load_file) as f:
            data = json.load(f)

        # Verify timestamp exists
        assert "timestamp" in data, f"Missing timestamp in load completion for {system}"


def verify_terraform_state_exists(results_dir: Path) -> dict[str, Any]:
    """Verify terraform state exists and return outputs.

    Args:
        results_dir: Results directory path

    Returns:
        Dict of terraform outputs

    Raises:
        AssertionError: If terraform state not found
    """
    terraform_dir = results_dir / "terraform"
    assert terraform_dir.exists(), f"Terraform directory not found: {terraform_dir}"

    state_file = terraform_dir / "terraform.tfstate"
    assert state_file.exists(), f"Terraform state file not found: {state_file}"

    with open(state_file) as f:
        state = json.load(f)

    return state.get("outputs", {})


def verify_system_ips_available(
    results_dir: Path, expected_systems: list[str]
) -> dict[str, str]:
    """Verify that IPs are available for all expected systems.

    Args:
        results_dir: Results directory
        expected_systems: List of expected system names

    Returns:
        Dict mapping system names to their public IPs

    Raises:
        AssertionError: If IPs not found
    """
    outputs = verify_terraform_state_exists(results_dir)

    public_ips = outputs.get("system_public_ips", {}).get("value", {})

    ips: dict[str, str] = {}
    for system in expected_systems:
        if system in public_ips:
            ip_value = public_ips[system]
            # Handle both single IP and list of IPs (multinode)
            if isinstance(ip_value, list):
                ips[system] = ip_value[0]
            else:
                ips[system] = ip_value

    return ips
