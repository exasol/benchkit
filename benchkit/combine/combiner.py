"""Core logic for combining benchmark results."""

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rich.console import Console

from .source_parser import SourceSpec
from .validation import (
    get_system_config,
    validate_no_name_conflicts,
    validate_results_exist,
    validate_workloads_compatible,
)

console = Console()


class BenchmarkCombiner:
    """Combines benchmark results from multiple source projects."""

    def __init__(
        self,
        sources: list[SourceSpec],
        output_project_id: str,
        title: str | None = None,
        author: str | None = None,
    ):
        """Initialize the combiner.

        Args:
            sources: List of parsed SourceSpec objects.
            output_project_id: Project ID for the combined output.
            title: Optional title for the combined benchmark.
            author: Optional author for the combined benchmark.
        """
        self.sources = sources
        self.output_project_id = output_project_id
        self.title = title
        self.author = author
        self.output_dir = Path("results") / output_project_id

        # Will be populated during combine
        self._workload: dict[str, Any] = {}
        self._name_mapping: dict[tuple[str, str], str] = {}
        self._source_configs: list[dict[str, Any]] = []

    def combine(self, force: bool = False) -> Path:
        """Execute the full combining workflow.

        Args:
            force: If True, overwrite existing output directory.

        Returns:
            Path to the combined output directory.

        Raises:
            FileExistsError: If output directory exists and force is False.
            Various validation errors from validation module.
        """
        # 1. Check output doesn't exist (or force)
        self._check_output_exists(force)

        # 2. Load all configs
        console.print("[blue]Loading source configurations...[/]")
        self._load_configs()

        # 3. Validate workloads match
        console.print("[blue]Validating workload compatibility...[/]")
        self._workload = validate_workloads_compatible(self.sources)

        # 4. Validate no name conflicts
        console.print("[blue]Checking for system name conflicts...[/]")
        self._name_mapping = validate_no_name_conflicts(self.sources)

        # 5. Validate results exist
        console.print("[blue]Validating result files exist...[/]")
        validate_results_exist(self.sources)

        # 6. Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[blue]Created output directory:[/] {self.output_dir}")

        # 7. Copy per-system files
        console.print("[blue]Copying per-system files...[/]")
        self._copy_system_files()

        # 8. Merge combined CSVs
        console.print("[blue]Merging result files...[/]")
        runs_df, warmup_df = self._merge_csv_files()

        # 9. Regenerate summary
        console.print("[blue]Regenerating summary statistics...[/]")
        self._regenerate_summary(runs_df, warmup_df)

        # 10. Merge raw results if available
        self._merge_raw_results()

        # 11. Generate combined config
        console.print("[blue]Generating combined configuration...[/]")
        self._generate_combined_config()

        return self.output_dir

    def _check_output_exists(self, force: bool) -> None:
        """Check if output directory exists.

        Args:
            force: If True, remove existing directory.

        Raises:
            FileExistsError: If directory exists and force is False.
        """
        if self.output_dir.exists():
            if force:
                console.print(
                    f"[yellow]Removing existing output directory:[/] {self.output_dir}"
                )
                shutil.rmtree(self.output_dir)
            else:
                raise FileExistsError(
                    f"Output directory already exists: {self.output_dir}. "
                    "Use --force to overwrite."
                )

    def _load_configs(self) -> None:
        """Load all source configurations."""
        for source in self.sources:
            config = source.load_config()
            self._source_configs.append(config)
            console.print(
                f"  Loaded {source.config_path} "
                f"(project: {source.project_id}, "
                f"systems: {[s.original_name for s in source.systems]})"
            )

    def _copy_system_files(self) -> None:
        """Copy all per-system files with optional renaming."""
        # File patterns to copy (with system name substitution)
        # Pattern: (source_pattern, is_required)
        file_patterns = [
            ("runs_{system}.csv", True),
            ("runs_{system}_warmup.csv", False),
            ("system_{system}.json", False),
            ("setup_{system}.json", False),
            ("installation_{system}.json", False),
            ("load_complete_{system}.json", False),
            ("setup_complete_{system}.json", False),
            ("preparation_{system}.json", False),
        ]

        for source in self.sources:
            for system in source.systems:
                original_name = system.original_name
                final_name = system.final_name

                # Copy standard files
                for pattern, is_required in file_patterns:
                    src_file = source.results_dir / pattern.format(system=original_name)
                    dst_file = self.output_dir / pattern.format(system=final_name)

                    if src_file.exists():
                        self._copy_file(src_file, dst_file, original_name, final_name)
                    elif is_required:
                        console.print(f"  [red]Missing required file:[/] {src_file}")
                    else:
                        pass  # Optional file, skip silently

                # Copy multinode system files (system_{system}-node{N}.json)
                self._copy_multinode_files(source, original_name, final_name)

    def _copy_file(
        self,
        src: Path,
        dst: Path,
        original_name: str,
        final_name: str,
    ) -> None:
        """Copy a file, updating system names if needed.

        For CSV files, also updates the 'system' column.
        For JSON files, copies as-is.
        """
        if src.suffix == ".csv" and original_name != final_name:
            # Read CSV, update system column, write
            df = pd.read_csv(src)
            if "system" in df.columns:
                df["system"] = df["system"].replace(original_name, final_name)
            df.to_csv(dst, index=False)
        else:
            # Copy file directly
            shutil.copy2(src, dst)

    def _copy_multinode_files(
        self,
        source: SourceSpec,
        original_name: str,
        final_name: str,
    ) -> None:
        """Copy multinode system files (system_{system}-node{N}.json)."""
        # Find all node files for this system
        pattern = re.compile(rf"^system_{re.escape(original_name)}-node(\d+)\.json$")

        for file_path in source.results_dir.glob(f"system_{original_name}-node*.json"):
            match = pattern.match(file_path.name)
            if match:
                node_num = match.group(1)
                dst_file = self.output_dir / f"system_{final_name}-node{node_num}.json"
                shutil.copy2(file_path, dst_file)

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame column names to match expected format.

        This handles the case where per-system CSVs use different column names
        (e.g., query_name vs query, run_number vs run).
        """
        # Column renaming for consistency
        column_mapping = {
            "query_name": "query",
            "run_number": "run",
        }

        # Apply renaming
        df = df.rename(columns=column_mapping)

        # Add elapsed_ms if missing but elapsed_s exists
        if "elapsed_ms" not in df.columns and "elapsed_s" in df.columns:
            df["elapsed_ms"] = (df["elapsed_s"] * 1000).round(1)

        return df

    def _merge_csv_files(self) -> tuple[pd.DataFrame, pd.DataFrame | None]:
        """Merge all per-system CSV files into combined files.

        Returns:
            Tuple of (runs_df, warmup_df). warmup_df may be None.
        """
        # Collect all per-system runs
        runs_dfs = []
        warmup_dfs = []

        for source in self.sources:
            for system in source.systems:
                final_name = system.final_name

                # Main runs
                runs_file = self.output_dir / f"runs_{final_name}.csv"
                if runs_file.exists():
                    df = pd.read_csv(runs_file)
                    df = self._normalize_df(df)
                    runs_dfs.append(df)

                # Warmup runs
                warmup_file = self.output_dir / f"runs_{final_name}_warmup.csv"
                if warmup_file.exists():
                    df = pd.read_csv(warmup_file)
                    df = self._normalize_df(df)
                    warmup_dfs.append(df)

        # Combine runs
        if runs_dfs:
            runs_df = pd.concat(runs_dfs, ignore_index=True)
            runs_df.to_csv(self.output_dir / "runs.csv", index=False)
            console.print(
                f"  Combined {len(runs_dfs)} system results into runs.csv "
                f"({len(runs_df)} rows)"
            )
        else:
            runs_df = pd.DataFrame()
            console.print("[yellow]  Warning: No runs data found[/]")

        # Combine warmup
        warmup_df = None
        if warmup_dfs:
            warmup_df = pd.concat(warmup_dfs, ignore_index=True)
            warmup_df.to_csv(self.output_dir / "runs_warmup.csv", index=False)
            console.print(
                f"  Combined {len(warmup_dfs)} warmup results into runs_warmup.csv "
                f"({len(warmup_df)} rows)"
            )

        return runs_df, warmup_df

    def _regenerate_summary(
        self,
        runs_df: pd.DataFrame,
        warmup_df: pd.DataFrame | None,
    ) -> None:
        """Regenerate summary.json from merged results."""
        if runs_df.empty:
            console.print("[yellow]  Warning: Cannot generate summary - no data[/]")
            return

        summary = self._create_summary_stats(runs_df, warmup_df)

        # Save summary
        summary_path = self.output_dir / "summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        console.print("  Generated summary.json")

    def _create_summary_stats(
        self,
        df: pd.DataFrame,
        warmup_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """Create summary statistics from results.

        This mirrors the logic in BenchmarkRunner._create_summary_stats()
        but operates on merged data.
        """
        summary: dict[str, Any] = {
            "total_queries": len(df),
            "systems": df["system"].unique().tolist(),
            "query_names": df["query"].unique().tolist(),
            "run_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "combined_from": [str(s.config_path) for s in self.sources],
        }

        # Add variant information from workload
        summary["variant"] = self._workload.get("variant", "official")
        if self._workload.get("system_variants"):
            summary["system_variants"] = self._workload["system_variants"]

        # Add multiuser configuration
        multiuser_config = self._workload.get("multiuser") or {}
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

            # Warmup per-query statistics
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

    def _merge_raw_results(self) -> None:
        """Merge raw_results.json files from all sources."""
        all_raw_results = []

        for source in self.sources:
            raw_results_file = source.results_dir / "raw_results.json"
            if raw_results_file.exists():
                try:
                    with open(raw_results_file) as f:
                        raw_results = json.load(f)

                    # Filter to only selected systems and update names
                    selected_originals = {s.original_name for s in source.systems}
                    name_map = {s.original_name: s.final_name for s in source.systems}

                    for result in raw_results:
                        system = result.get("system")
                        if system in selected_originals:
                            # Update system name if renamed
                            result["system"] = name_map.get(system, system)
                            all_raw_results.append(result)
                except (json.JSONDecodeError, KeyError) as e:
                    console.print(
                        f"[yellow]  Warning: Could not parse {raw_results_file}: {e}[/]"
                    )

        if all_raw_results:
            raw_results_path = self.output_dir / "raw_results.json"
            with open(raw_results_path, "w") as f:
                json.dump(all_raw_results, f, indent=2)
            console.print(f"  Merged raw_results.json ({len(all_raw_results)} results)")

    def _generate_combined_config(self) -> None:
        """Generate a combined config.yaml for the new project."""
        # Collect system configs from all sources
        combined_systems = []

        for source in self.sources:
            for system in source.systems:
                system_config = get_system_config(source, system.original_name)
                if system_config:
                    # Create a copy with the final name
                    new_config = dict(system_config)
                    new_config["name"] = system.final_name

                    # Simplify setup to preinstalled mode (results already exist)
                    if "setup" in new_config:
                        new_config["setup"]["method"] = "preinstalled"

                    combined_systems.append(new_config)
                else:
                    # Create minimal config for systems not in config
                    combined_systems.append(
                        {
                            "name": system.final_name,
                            "kind": "unknown",
                            "version": "unknown",
                            "setup": {"method": "preinstalled"},
                        }
                    )

        # Build combined config
        combined_config = {
            "project_id": self.output_project_id,
            "title": self.title or f"Combined benchmark: {self.output_project_id}",
            "author": self.author or "Combined",
            "systems": combined_systems,
            "workload": self._workload,
            "env": {"mode": "local"},
            "report": {
                "output_path": f"results/{self.output_project_id}/reports",
                "figures_dir": f"results/{self.output_project_id}/figures",
            },
        }

        # Save config
        config_path = self.output_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(combined_config, f, default_flow_style=False, sort_keys=False)

        console.print("  Generated config.yaml")
