"""Result collection and statistics for benchmark runner.

This module handles saving benchmark results, system metrics, and creating
summary statistics.
"""

import time
from collections.abc import Callable
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

    def save_benchmark_results(
        self,
        results: list[dict[str, Any]],
        warmup_results: list[dict[str, Any]] | None = None,
    ) -> None:
        """Save benchmark results to files.

        Args:
            results: List of result dictionaries
            warmup_results: Optional list of warmup result dictionaries
        """
        from .parsers import normalize_runs

        if not results:
            console.print("[yellow]No results to save[/yellow]")
            return

        # Convert to DataFrame and save CSV
        df = normalize_runs(results)
        csv_path = self._output_dir / "runs.csv"
        df.to_csv(csv_path, index=False)

        console.print(f"Results saved to: {csv_path}")

        # Save warmup results if present
        warmup_df = None
        if warmup_results:
            warmup_df = normalize_runs(warmup_results)
            warmup_csv_path = self._output_dir / "runs_warmup.csv"
            warmup_df.to_csv(warmup_csv_path, index=False)
            console.print(f"Warmup results saved to: {warmup_csv_path}")

        # Save raw results as JSON
        json_path = self._output_dir / "raw_results.json"
        save_json(results, json_path)

        # Create summary statistics
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
