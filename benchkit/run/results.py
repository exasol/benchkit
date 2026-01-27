"""Result collection and statistics for benchmark runner.

This module handles saving benchmark results, system metrics, and creating
summary statistics.
"""

import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd
from rich.console import Console

from ..util import load_json, save_json

if TYPE_CHECKING:
    from .parallel_executor import ParallelExecutor
    from .runner import BenchmarkRunner

console = Console()


class ResultsManager:
    """Handles result collection and statistics generation."""

    def __init__(self, runner: "BenchmarkRunner"):
        """Initialize the results manager.

        Args:
            runner: Parent BenchmarkRunner instance for shared state access
        """
        self._runner = runner
        self._output_dir = runner.output_dir
        self._log_fn: Callable[[str], None] = console.print

    def _log_output(
        self,
        message: str,
        executor: "ParallelExecutor | None" = None,
        system_name: str | None = None,
    ) -> None:
        """Route output to either parallel executor buffer or console."""
        self._runner._log_output(message, executor, system_name)

    def _load_existing_csv(self, csv_path: Path) -> pd.DataFrame | None:
        """Load existing CSV file if it exists and is valid.

        Args:
            csv_path: Path to the CSV file

        Returns:
            DataFrame if file exists and is valid, None otherwise
        """
        if not csv_path.exists():
            return None

        try:
            df = pd.read_csv(csv_path)
            required_columns = {"system", "query", "run", "elapsed_s", "elapsed_ms"}
            if not required_columns.issubset(df.columns):
                console.print(
                    f"[yellow]Warning: Existing {csv_path.name} has missing columns, "
                    "will be replaced[/yellow]"
                )
                return None
            return df
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not read existing {csv_path.name}: {e}[/yellow]"
            )
            return None

    def _merge_results(
        self,
        existing_df: pd.DataFrame | None,
        new_df: pd.DataFrame,
        dedup_columns: list[str],
    ) -> pd.DataFrame:
        """Merge new results with existing, deduplicating by specified columns.

        New results take precedence over existing when duplicates found.

        Args:
            existing_df: Existing DataFrame (may be None)
            new_df: New results DataFrame
            dedup_columns: Columns to use for deduplication

        Returns:
            Merged and deduplicated DataFrame
        """
        if existing_df is None or existing_df.empty:
            return new_df
        if new_df.empty:
            return existing_df

        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=dedup_columns, keep="last")
        combined = combined.sort_values(by=dedup_columns).reset_index(drop=True)
        return combined

    def _merge_raw_results(
        self,
        existing_results: list[dict[str, Any]] | None,
        new_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Merge raw results JSON, deduplicating by (system, query_name, run_number).

        Args:
            existing_results: Existing raw results (may be None)
            new_results: New raw results

        Returns:
            Merged and deduplicated results list
        """
        if not existing_results:
            return new_results
        if not new_results:
            return existing_results

        result_map: dict[tuple[Any, Any, Any], dict[str, Any]] = {}
        for result in existing_results:
            key = (
                result.get("system"),
                result.get("query_name"),
                result.get("run_number"),
            )
            result_map[key] = result

        for result in new_results:
            key = (
                result.get("system"),
                result.get("query_name"),
                result.get("run_number"),
            )
            result_map[key] = result

        merged = list(result_map.values())
        merged.sort(
            key=lambda r: (
                r.get("system", ""),
                r.get("query_name", ""),
                r.get("run_number", 0),
            )
        )
        return merged

    def save_benchmark_results(
        self,
        results: list[dict[str, Any]],
        warmup_results: list[dict[str, Any]] | None = None,
    ) -> None:
        """Save benchmark results to files.

        Supports incremental runs: if results already exist, new results are
        merged with existing ones. New results take precedence when duplicates
        are found (based on system, query, run).

        Args:
            results: List of result dictionaries
            warmup_results: Optional list of warmup result dictionaries
        """
        from .parsers import normalize_runs

        if not results:
            console.print("[yellow]No results to save[/yellow]")
            return

        # Convert new results to DataFrame
        new_df = normalize_runs(results)
        csv_path = self._output_dir / "runs.csv"

        # Load existing results and merge
        existing_df = self._load_existing_csv(csv_path)
        if existing_df is not None:
            new_systems = new_df["system"].unique().tolist()
            console.print(
                f"[dim]Merging results with existing data "
                f"(new systems: {new_systems})[/dim]"
            )

        # Merge with deduplication by (system, query, run)
        df = self._merge_results(existing_df, new_df, ["system", "query", "run"])
        df.to_csv(csv_path, index=False)

        console.print(f"Results saved to: {csv_path}")

        # Save warmup results if present (merge with existing)
        warmup_df = None
        if warmup_results:
            new_warmup_df = normalize_runs(warmup_results)
            warmup_csv_path = self._output_dir / "runs_warmup.csv"

            existing_warmup_df = self._load_existing_csv(warmup_csv_path)

            # Warmup queries have run number in name (Q01_warmup_1), so
            # deduplicate by (system, query) only
            warmup_df = self._merge_results(
                existing_warmup_df, new_warmup_df, ["system", "query"]
            )
            warmup_df.to_csv(warmup_csv_path, index=False)
            console.print(f"Warmup results saved to: {warmup_csv_path}")

        # Merge raw results JSON
        json_path = self._output_dir / "raw_results.json"
        existing_raw: list[dict[str, Any]] | None = None
        if json_path.exists():
            try:
                existing_raw = load_json(json_path)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not read existing raw_results.json: "
                    f"{e}[/yellow]"
                )

        merged_raw = self._merge_raw_results(existing_raw, results)
        save_json(merged_raw, json_path)

        # Create summary statistics from merged data
        summary = self.create_summary_stats(df, warmup_df, self._runner.config)
        summary_path = self._output_dir / "summary.json"
        save_json(summary, summary_path)

    def save_system_metrics(self, system_name: str, metrics: dict[str, Any]) -> None:
        """Save system-specific metrics.

        Args:
            system_name: Name of the system
            metrics: Metrics dictionary
        """
        metrics_path = self._output_dir / f"metrics_{system_name}.json"
        save_json(metrics, metrics_path)

    def save_setup_summary(
        self, system_name: str, setup_summary: dict[str, Any]
    ) -> None:
        """Save system setup summary for report reproduction.

        Args:
            system_name: Name of the system
            setup_summary: Setup summary dictionary
        """
        setup_path = self._output_dir / f"setup_{system_name}.json"
        save_json(setup_summary, setup_path)

    def load_setup_summary_to_system(
        self,
        system: Any,
        system_name: str,
        executor: "ParallelExecutor | None" = None,
    ) -> None:
        """Load previously saved setup summary back into system object.

        Args:
            system: System instance
            system_name: Name of the system
            executor: ParallelExecutor for output routing
        """
        setup_path = self._output_dir / f"setup_{system_name}.json"
        if setup_path.exists():
            try:
                setup_summary = load_json(setup_path)

                # Restore setup commands to system
                if "commands" in setup_summary:
                    commands_by_category = setup_summary["commands"]

                    for _category, commands in commands_by_category.items():
                        for cmd in commands:
                            system.setup_commands.append(cmd)

                # Restore installation notes
                if "installation_notes" in setup_summary:
                    system.installation_notes = setup_summary["installation_notes"]

                self._log_output(
                    f"[dim]  Loaded {len(system.setup_commands)} setup commands from previous run[/dim]",
                    executor,
                    system_name,
                )
            except Exception as e:
                self._log_output(
                    f"[yellow]  Warning: Could not load setup summary: {e}[/yellow]",
                    executor,
                    system_name,
                )

    def create_summary_stats(
        self,
        df: pd.DataFrame,
        warmup_df: pd.DataFrame | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create summary statistics from results.

        Args:
            df: DataFrame of measured results
            warmup_df: Optional DataFrame of warmup results
            config: Optional configuration dictionary

        Returns:
            Summary statistics dictionary
        """
        summary: dict[str, Any] = {
            "total_queries": len(df),
            "systems": df["system"].unique().tolist(),
            "query_names": df["query"].unique().tolist(),
            "run_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Add variant information from config
        if config and "workload" in config:
            workload_config = config["workload"]
            summary["variant"] = workload_config.get("variant", "official")
            if (
                "system_variants" in workload_config
                and workload_config["system_variants"]
            ):
                summary["system_variants"] = workload_config["system_variants"]

            # Add multiuser configuration
            multiuser_config = workload_config.get("multiuser") or {}
            if multiuser_config.get("enabled", False):
                summary["execution_mode"] = "multiuser"
                summary["multiuser"] = {
                    "num_streams": multiuser_config.get("num_streams", 1),
                    "randomize": multiuser_config.get("randomize", False),
                    "random_seed": multiuser_config.get("random_seed"),
                }
            else:
                summary["execution_mode"] = "sequential"

        # Per-system statistics
        summary["per_system"] = {}
        for system in df["system"].unique():
            system_df = df[df["system"] == system]
            summary["per_system"][system] = {
                "total_queries": len(system_df),
                "avg_runtime_ms": float(system_df["elapsed_ms"].mean()),
                "median_runtime_ms": float(system_df["elapsed_ms"].median()),
                "min_runtime_ms": float(system_df["elapsed_ms"].min()),
                "max_runtime_ms": float(system_df["elapsed_ms"].max()),
            }

        # Per-query statistics
        summary["per_query"] = {}
        for query in df["query"].unique():
            query_df = df[df["query"] == query]
            systems = query_df["system"].unique().tolist()

            per_system_stats: dict[str, dict[str, float | int]] = {}
            for system in systems:
                system_query_df = query_df[query_df["system"] == system]
                per_system_stats[system] = {
                    "runs": int(len(system_query_df)),
                    "avg_runtime_ms": float(system_query_df["elapsed_ms"].mean()),
                    "median_runtime_ms": float(system_query_df["elapsed_ms"].median()),
                    "min_runtime_ms": float(system_query_df["elapsed_ms"].min()),
                    "max_runtime_ms": float(system_query_df["elapsed_ms"].max()),
                }

            summary["per_query"][query] = {
                "systems": systems,
                "per_system": per_system_stats,
            }

        # Add per-stream statistics if multiuser execution was used
        if "stream_id" in df.columns and df["stream_id"].notna().any():
            summary["per_stream"] = {}

            for system in df["system"].unique():
                system_df = df[df["system"] == system]
                summary["per_stream"][system] = {}

                for stream_id in sorted(system_df["stream_id"].dropna().unique()):
                    stream_df = system_df[system_df["stream_id"] == stream_id]
                    summary["per_stream"][system][int(stream_id)] = {
                        "queries_executed": len(stream_df),
                        "avg_runtime_ms": float(stream_df["elapsed_ms"].mean()),
                        "median_runtime_ms": float(stream_df["elapsed_ms"].median()),
                        "min_runtime_ms": float(stream_df["elapsed_ms"].min()),
                        "max_runtime_ms": float(stream_df["elapsed_ms"].max()),
                    }

        # Add warmup statistics if available
        if warmup_df is not None and len(warmup_df) > 0:
            summary["warmup_statistics"] = {
                "total_warmup_queries": len(warmup_df),
                "per_system": {},
                "per_query": {},
            }

            # Warmup per-system statistics
            for system in warmup_df["system"].unique():
                system_warmup_df = warmup_df[warmup_df["system"] == system]
                summary["warmup_statistics"]["per_system"][system] = {
                    "total_queries": len(system_warmup_df),
                    "avg_runtime_ms": float(system_warmup_df["elapsed_ms"].mean()),
                    "median_runtime_ms": float(system_warmup_df["elapsed_ms"].median()),
                    "min_runtime_ms": float(system_warmup_df["elapsed_ms"].min()),
                    "max_runtime_ms": float(system_warmup_df["elapsed_ms"].max()),
                }

            # Warmup per-query statistics (aggregated across warmup runs)
            normalized_warmup_df = warmup_df.copy()
            normalized_warmup_df["base_query"] = normalized_warmup_df["query"].apply(
                lambda name: (
                    name.rsplit("_warmup_", 1)[0] if "_warmup_" in name else name
                )
            )

            for base_query in normalized_warmup_df["base_query"].unique():
                query_warmup_df = normalized_warmup_df[
                    normalized_warmup_df["base_query"] == base_query
                ]
                summary["warmup_statistics"]["per_query"][base_query] = {}

                for system in query_warmup_df["system"].unique():
                    system_query_warmup_df = query_warmup_df[
                        query_warmup_df["system"] == system
                    ]
                    summary["warmup_statistics"]["per_query"][base_query][system] = {
                        "total_runs": int(len(system_query_warmup_df)),
                        "avg_runtime_ms": float(
                            system_query_warmup_df["elapsed_ms"].mean()
                        ),
                    }

        return summary
