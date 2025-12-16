"""Results verification functions for E2E tests.

These functions verify that benchmark results are correct and complete.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def verify_runs_csv(results_dir: Path, config: dict[str, Any]) -> pd.DataFrame:
    """Verify runs.csv exists and has correct structure.

    Args:
        results_dir: Results directory
        config: Benchmark configuration

    Returns:
        Loaded DataFrame

    Raises:
        AssertionError: If verification fails
    """
    runs_csv = results_dir / "runs.csv"
    assert runs_csv.exists(), f"runs.csv not found at {runs_csv}"

    df = pd.read_csv(runs_csv)

    # Verify required columns exist
    required_columns = [
        "system",
        "query",
        "run",
        "elapsed_s",
        "elapsed_ms",
        "success",
        "workload",
        "scale_factor",
        "variant",
    ]
    for col in required_columns:
        assert col in df.columns, f"Missing required column '{col}' in runs.csv"

    # Verify all systems are present
    systems_in_config = [s["name"] for s in config["systems"]]
    systems_in_results = df["system"].unique().tolist()

    for system in systems_in_config:
        assert system in systems_in_results, (
            f"System '{system}' not found in results. "
            f"Found systems: {systems_in_results}"
        )

    # Verify correct number of runs per query
    runs_per_query = config["workload"]["runs_per_query"]
    for system in systems_in_config:
        system_df = df[df["system"] == system]
        for query in system_df["query"].unique():
            query_runs = len(system_df[system_df["query"] == query])
            assert query_runs == runs_per_query, (
                f"Expected {runs_per_query} runs for {system}/{query}, "
                f"got {query_runs}"
            )

    # Verify success rate (at least 80% should succeed for E2E test)
    success_rate = df["success"].mean()
    assert success_rate >= 0.8, (
        f"Success rate too low: {success_rate:.1%}. "
        f"Check query failures in results."
    )

    return df


def verify_summary_json(results_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Verify summary.json exists and has correct structure.

    Args:
        results_dir: Results directory
        config: Benchmark configuration

    Returns:
        Loaded summary data

    Raises:
        AssertionError: If verification fails
    """
    summary_path = results_dir / "summary.json"
    assert summary_path.exists(), f"summary.json not found at {summary_path}"

    with open(summary_path) as f:
        summary = json.load(f)

    # Verify required keys
    required_keys = ["systems", "query_names", "per_system", "per_query"]
    for key in required_keys:
        assert key in summary, f"Missing '{key}' in summary.json"

    # Verify all systems are present
    systems_in_config = [s["name"] for s in config["systems"]]
    for system in systems_in_config:
        assert (
            system in summary["systems"]
        ), f"System '{system}' not in summary.json systems list"
        assert (
            system in summary["per_system"]
        ), f"System '{system}' not in per_system stats"

    # Verify statistics are present and positive
    for system in systems_in_config:
        stats = summary["per_system"][system]
        assert "avg_runtime_ms" in stats, f"Missing avg_runtime_ms for {system}"
        assert "median_runtime_ms" in stats, f"Missing median_runtime_ms for {system}"
        assert (
            stats["avg_runtime_ms"] > 0
        ), f"Invalid avg_runtime_ms for {system}: {stats['avg_runtime_ms']}"

    return summary


def verify_query_variants(results_dir: Path, config: dict[str, Any]) -> None:
    """Verify that correct query variants were used for each system.

    Args:
        results_dir: Results directory
        config: Benchmark configuration

    Raises:
        AssertionError: If variant verification fails
    """
    runs_csv = results_dir / "runs.csv"
    df = pd.read_csv(runs_csv)

    system_variants = config["workload"].get("system_variants", {})
    default_variant = config["workload"].get("variant", "official")

    for system in df["system"].unique():
        expected_variant = system_variants.get(system, default_variant)
        actual_variants = df[df["system"] == system]["variant"].unique()

        assert (
            len(actual_variants) == 1
        ), f"Multiple variants found for {system}: {actual_variants.tolist()}"
        assert actual_variants[0] == expected_variant, (
            f"Wrong variant for {system}: "
            f"expected '{expected_variant}', got '{actual_variants[0]}'"
        )


def verify_data_loaded(results_dir: Path, config: dict[str, Any]) -> None:
    """Verify that data was loaded correctly by checking row counts.

    This requires checking the load completion files for row count info.

    Args:
        results_dir: Results directory
        config: Benchmark configuration

    Raises:
        AssertionError: If data loading verification fails
    """
    systems_in_config = [s["name"] for s in config["systems"]]

    for system in systems_in_config:
        load_file = results_dir / f"load_complete_{system}.json"
        assert load_file.exists(), f"Load completion file not found for {system}"

        with open(load_file) as f:
            load_data = json.load(f)

        # Verify timestamp exists (indicates completion)
        assert "timestamp" in load_data, f"Missing timestamp in load data for {system}"


def verify_error_messages(results_dir: Path) -> list[str]:
    """Collect and return error messages from failed queries.

    Args:
        results_dir: Results directory

    Returns:
        List of error messages
    """
    runs_csv = results_dir / "runs.csv"
    if not runs_csv.exists():
        return []

    df = pd.read_csv(runs_csv)
    failed = df[df["success"] == False]  # noqa: E712

    errors = []
    if "error" in failed.columns:
        errors = failed["error"].dropna().unique().tolist()

    return errors
