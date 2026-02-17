"""Suite publish command implementation.

Generates a static website for viewing benchmark suite results with interactive
visualizations, similar to benchmark.clickhouse.com.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console

from ..config import load_config
from ..util import ensure_directory, get_templates_dir, get_workloads_dir, load_json
from . import SuiteConfig, SuiteRunner, SuiteStateManager

console = Console()

# Expected query counts per workload (used in BenchScore denominator to prevent cherry-picking)
WORKLOAD_EXPECTED_QUERIES: dict[str, int] = {
    "tpch": 22,
    "clickbench": 43,
}


@dataclass
class QueryStats:
    """Statistics for a single query."""

    median: float
    avg: float
    min: float
    max: float
    std: float = 0.0
    count: int = 0
    success_rate: float = 100.0


@dataclass
class SystemDataEntry:
    """Aggregated data for a system within a benchmark."""

    name: str
    kind: str
    version: str
    median_ms: float
    avg_ms: float
    geomean_ms: float
    total_ms: float
    min_ms: float
    max_ms: float
    query_count: int
    bench_score: float = 0.0
    speed_score: float = 0.0
    scale_score: float = 0.0
    sum_medians_ms: float = 0.0
    success_rate: float = 100.0
    node_count: int = 1


@dataclass
class BenchmarkDataEntry:
    """Aggregated data for a single benchmark."""

    benchmark_id: str  # e.g., "series_1_nodes/nodes_04"
    series_name: str
    config_name: str
    project_id: str
    workload: str  # "tpch" or "clickbench"
    scale_factor: int | float | None
    node_count: int
    stream_count: int  # num_streams from workload config
    environment: str  # "aws", "local", etc.
    instance_type: str | None
    run_date: str | None
    report_url: str | None
    systems: list[SystemDataEntry] = field(default_factory=list)
    queries: dict[str, dict[str, QueryStats]] = field(
        default_factory=dict
    )  # query -> system -> stats
    warmup_queries: dict[str, dict[str, dict[str, float]]] = field(
        default_factory=dict
    )  # query -> system -> {median, avg, min, max}
    query_errors: dict[str, dict[str, str]] = field(
        default_factory=dict
    )  # query -> system -> error_message


class SuitePublisher:
    """Generates a static website from suite benchmark results."""

    def __init__(
        self,
        suite_path: Path,
        config: SuiteConfig,
        output_dir: Path | None = None,
        title: str | None = None,
        base_url: str | None = None,
        include_reports: bool | None = None,
        theme: str | None = None,
        regenerate_stale: bool = False,
    ):
        """Initialize the publisher.

        Args:
            suite_path: Path to the suite directory
            config: Loaded suite configuration
            output_dir: Output directory (overrides suite.yaml publish.output_dir)
            title: Custom site title (overrides suite.yaml publish.title)
            base_url: Base URL for assets (overrides suite.yaml publish.base_url)
            include_reports: Whether to copy reports (overrides suite.yaml)
            theme: Theme (overrides suite.yaml publish.theme)
            regenerate_stale: Whether to regenerate reports older than their data
        """
        self.suite_path = suite_path
        self.config = config
        pub = config.publish

        # Resolve output_dir: CLI arg > suite.yaml > default
        if output_dir is not None:
            self.output_dir = output_dir
        elif pub.output_dir:
            self.output_dir = Path(pub.output_dir)
        else:
            self.output_dir = self.suite_path

        # Resolve title: CLI arg > suite.yaml > suite name
        self.title = title or pub.title or config.name

        # Resolve other settings: CLI arg > suite.yaml defaults
        self.base_url = base_url if base_url is not None else pub.base_url
        self.include_reports = (
            include_reports if include_reports is not None else pub.include_reports
        )
        self.theme = theme if theme is not None else pub.theme
        self.regenerate_stale = regenerate_stale

        # Build series display names mapping (series key -> display name)
        self.series_display_names: dict[str, str] = {}
        for key, series_cfg in config.series.items():
            self.series_display_names[key] = series_cfg.name

        self.state_manager = SuiteStateManager(suite_path)
        self.runner = SuiteRunner(suite_path, config)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(get_templates_dir())),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.jinja_env.filters["format_number"] = self._format_number
        self.jinja_env.filters["format_duration"] = self._format_duration

    @staticmethod
    def _compute_bench_scores(
        success_df: pd.DataFrame,
        workload_name: str,
        scale_factor: int | float | None,
        stream_count: int,
    ) -> dict[str, float]:
        """Compute BenchScore as a composite of speed and scale.

        BenchScore = sqrt(SpeedScore * ScaleScore)
        SpeedScore = SF / geomean_s
        ScaleScore = SF * S * Q / sum_medians_s

        Returns dict with bench_score, speed_score, scale_score,
        geomean_ms, sum_medians_ms.
        """
        query_medians = success_df.groupby("query")["elapsed_ms"].median()
        if len(query_medians) == 0 or not (query_medians > 0).all():
            return {
                "bench_score": 0.0,
                "speed_score": 0.0,
                "scale_score": 0.0,
                "geomean_ms": 0.0,
                "sum_medians_ms": 0.0,
            }

        log_medians: np.ndarray = np.log(query_medians.to_numpy())  # type: ignore[assignment]
        geomean_ms = float(np.exp(log_medians.mean()))
        sum_medians_ms = float(query_medians.sum())

        sf = float(scale_factor) if scale_factor else 1.0
        s = max(stream_count, 1)
        q = WORKLOAD_EXPECTED_QUERIES.get(workload_name, len(query_medians))

        geomean_s = geomean_ms / 1000.0
        sum_medians_s = sum_medians_ms / 1000.0

        speed_score = sf / geomean_s if geomean_s > 0 else 0.0
        scale_score = sf * s * q / sum_medians_s if sum_medians_s > 0 else 0.0
        bench_score = float(np.sqrt(speed_score * scale_score))

        return {
            "bench_score": bench_score,
            "speed_score": speed_score,
            "scale_score": scale_score,
            "geomean_ms": geomean_ms,
            "sum_medians_ms": sum_medians_ms,
        }

    def publish(self) -> Path:
        """Generate the static website.

        Returns:
            Path to the generated index.html
        """
        console.print(f"[bold blue]Publishing suite: {self.config.name}[/bold blue]")

        # Collect benchmark data
        benchmarks = self._collect_benchmarks()
        if not benchmarks:
            console.print("[yellow]No completed benchmarks found[/yellow]")
            return self.output_dir / "index.html"

        console.print(f"  Found {len(benchmarks)} benchmarks")

        # Regenerate stale reports if requested
        if self.regenerate_stale:
            regenerated = self._regenerate_stale_reports(benchmarks)
            if regenerated > 0:
                console.print(f"  Regenerated {regenerated} stale reports")

        # Build site data structure based on template type
        template = self.config.publish.template
        if template == "leaderboard":
            site_data = self._build_leaderboard_data(benchmarks)
            # Generate downloadable packages for leaderboard entries
            self._generate_packages(site_data["entries"], self.output_dir)
        else:
            site_data = self._build_site_data(benchmarks)

        # Create output directory
        ensure_directory(self.output_dir)

        # Copy individual reports if requested
        if self.include_reports:
            self._copy_reports(benchmarks)

        # Render the site
        self._render_site(site_data)

        index_path = self.output_dir / "index.html"
        console.print(f"[green]✓ Published to {index_path}[/green]")

        return index_path

    def _collect_benchmarks(self) -> list[BenchmarkDataEntry]:
        """Collect data from all completed benchmarks."""
        benchmarks: list[BenchmarkDataEntry] = []

        # Discover all configs
        discovered = self.runner.discover_configs(include_disabled=False)

        for series_name in sorted(discovered.keys()):
            configs = discovered[series_name]

            for config_path in configs:
                benchmark_id = self.runner.get_benchmark_id(series_name, config_path)

                try:
                    benchmark = self._load_benchmark_data(
                        config_path, series_name, benchmark_id
                    )
                    if benchmark:
                        benchmarks.append(benchmark)
                except Exception as e:
                    console.print(
                        f"  [yellow]Warning: Could not load {benchmark_id}: {e}[/yellow]"
                    )

        return benchmarks

    def _load_benchmark_data(
        self, config_path: Path, series_name: str, benchmark_id: str
    ) -> BenchmarkDataEntry | None:
        """Load data for a single benchmark."""
        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            if not cfg or not isinstance(cfg, dict):
                return None
        except Exception:
            return None

        project_id = cfg.get("project_id", config_path.stem)
        results_dir = Path("results") / project_id

        # Check if results exist
        runs_csv = results_dir / "runs.csv"
        if not runs_csv.exists():
            return None

        # Load runs data
        try:
            runs_df = pd.read_csv(runs_csv)
        except Exception:
            return None

        if runs_df.empty:
            return None

        # Load summary if available
        summary_file = results_dir / "summary.json"
        summary: dict[str, Any] = {}
        if summary_file.exists():
            try:
                summary = load_json(summary_file)
            except Exception:
                pass

        # Extract workload info
        workload_config = cfg.get("workload", {})
        workload_name = workload_config.get("name", "unknown")
        scale_factor = workload_config.get("scale_factor")
        # num_streams can be at workload level or nested under multiuser
        multiuser_config = workload_config.get("multiuser") or {}
        stream_count = (
            multiuser_config.get("num_streams")
            or workload_config.get("num_streams")
            or 1
        )

        # Extract environment info
        env_config = cfg.get("env", {})
        environment = env_config.get("mode", "local")

        # Get node count and instance type from systems
        systems_config = cfg.get("systems", [])
        instance_type = None
        if systems_config:
            first_system = systems_config[0]
            system_name = first_system.get("name", "")
            # Fallback 1: env.instances.<system>.instance_type (per-system format)
            instances = env_config.get("instances", {})
            if system_name in instances:
                instance_type = instances[system_name].get("instance_type")
            # Fallback 2: env.instance_type (direct format)
            if not instance_type:
                instance_type = env_config.get("instance_type")
            # Fallback 3: system.json cloud metadata
            if not instance_type:
                system_json_path = results_dir / "system.json"
                if system_json_path.exists():
                    try:
                        sys_info = load_json(system_json_path)
                        instance_type = sys_info.get("aws", {}).get(
                            "instance_type"
                        ) or sys_info.get("gcp", {}).get("machine_type")
                    except Exception:
                        pass
        # Benchmark-level node_count = max across all systems
        node_count = max(
            (s.get("setup", {}).get("node_count", 1) for s in systems_config),
            default=1,
        )

        # Build system data
        systems: list[SystemDataEntry] = []
        for system_config in systems_config:
            system_name = system_config["name"]
            system_df = runs_df[runs_df["system"] == system_name]

            if system_df.empty:
                continue

            # Calculate statistics
            success_df = system_df[system_df["success"] == True]  # noqa: E712
            total_count = len(system_df)
            success_count = len(success_df)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0

            if not success_df.empty:
                scores = self._compute_bench_scores(
                    success_df, workload_name, scale_factor, stream_count
                )

                systems.append(
                    SystemDataEntry(
                        name=system_name,
                        kind=system_config.get("kind", system_name),
                        version=system_config.get("version", "unknown"),
                        median_ms=float(success_df["elapsed_ms"].median()),
                        avg_ms=float(success_df["elapsed_ms"].mean()),
                        geomean_ms=scores["geomean_ms"],
                        total_ms=float(success_df["elapsed_ms"].sum()),
                        min_ms=float(success_df["elapsed_ms"].min()),
                        max_ms=float(success_df["elapsed_ms"].max()),
                        query_count=len(success_df["query"].unique()),
                        bench_score=scores["bench_score"],
                        speed_score=scores["speed_score"],
                        scale_score=scores["scale_score"],
                        sum_medians_ms=scores["sum_medians_ms"],
                        success_rate=success_rate,
                        node_count=system_config.get("setup", {}).get("node_count", 1),
                    )
                )

        if not systems:
            return None

        # Build per-query statistics
        queries: dict[str, dict[str, QueryStats]] = {}
        for query_name in runs_df["query"].unique():
            queries[query_name] = {}
            for system_config in systems_config:
                system_name = system_config["name"]
                query_df = runs_df[
                    (runs_df["query"] == query_name)
                    & (runs_df["system"] == system_name)
                    & (runs_df["success"] == True)  # noqa: E712
                ]

                if not query_df.empty:
                    total_query_runs = len(
                        runs_df[
                            (runs_df["query"] == query_name)
                            & (runs_df["system"] == system_name)
                        ]
                    )
                    queries[query_name][system_name] = QueryStats(
                        median=float(query_df["elapsed_ms"].median()),
                        avg=float(query_df["elapsed_ms"].mean()),
                        min=float(query_df["elapsed_ms"].min()),
                        max=float(query_df["elapsed_ms"].max()),
                        std=(
                            float(query_df["elapsed_ms"].std())
                            if len(query_df) > 1
                            else 0.0
                        ),
                        count=len(query_df),
                        success_rate=(
                            (len(query_df) / total_query_runs * 100)
                            if total_query_runs > 0
                            else 0
                        ),
                    )

        # Collect error messages for failed queries
        query_errors: dict[str, dict[str, str]] = {}
        for query_name in runs_df["query"].unique():
            for system_config in systems_config:
                system_name = system_config["name"]
                if query_name not in queries or system_name not in queries.get(
                    query_name, {}
                ):
                    fail_df = runs_df[
                        (runs_df["query"] == query_name)
                        & (runs_df["system"] == system_name)
                        & (runs_df["success"] == False)  # noqa: E712
                    ]
                    if not fail_df.empty and "error" in fail_df.columns:
                        error_msgs = fail_df["error"].dropna()
                        if not error_msgs.empty:
                            if query_name not in query_errors:
                                query_errors[query_name] = {}
                            query_errors[query_name][system_name] = str(
                                error_msgs.iloc[0]
                            )

        # Parse warmup data if available
        warmup_queries: dict[str, dict[str, dict[str, float]]] = {}
        warmup_csv = results_dir / "runs_warmup.csv"
        if warmup_csv.exists():
            try:
                warmup_df = pd.read_csv(warmup_csv)
                if not warmup_df.empty and "query" in warmup_df.columns:
                    warmup_df["base_query"] = warmup_df["query"].str.replace(
                        r"_warmup_\d+$", "", regex=True
                    )
                    for qname in warmup_df["base_query"].unique():
                        warmup_queries[qname] = {}
                        for sys_cfg in systems_config:
                            sname = sys_cfg["name"]
                            qdf = warmup_df[
                                (warmup_df["base_query"] == qname)
                                & (warmup_df["system"] == sname)
                                & (warmup_df["success"] == True)  # noqa: E712
                            ]
                            if not qdf.empty:
                                warmup_queries[qname][sname] = {
                                    "median": round(
                                        float(qdf["elapsed_ms"].median()), 2
                                    ),
                                    "avg": round(float(qdf["elapsed_ms"].mean()), 2),
                                    "min": round(float(qdf["elapsed_ms"].min()), 2),
                                    "max": round(float(qdf["elapsed_ms"].max()), 2),
                                }
            except Exception:
                pass

        # Get run date
        run_date = summary.get("run_date")

        # Determine report URL
        report_url = None
        if self.include_reports:
            report_path = (
                Path("reports") / series_name / config_path.stem / "REPORT.html"
            )
            report_url = str(report_path)

        return BenchmarkDataEntry(
            benchmark_id=benchmark_id,
            series_name=series_name,
            config_name=config_path.stem,
            project_id=project_id,
            workload=workload_name,
            scale_factor=scale_factor,
            node_count=node_count,
            stream_count=stream_count,
            environment=environment,
            instance_type=instance_type,
            run_date=run_date,
            report_url=report_url,
            systems=systems,
            queries=queries,
            warmup_queries=warmup_queries,
            query_errors=query_errors,
        )

    def _build_site_data(self, benchmarks: list[BenchmarkDataEntry]) -> dict[str, Any]:
        """Build the complete site data structure."""
        # Collect filter options
        series_set: set[str] = set()
        systems_set: set[str] = set()
        workloads_set: set[str] = set()
        scale_factors_set: set[int | float] = set()
        node_counts_set: set[int] = set()
        stream_counts_set: set[int] = set()

        for benchmark in benchmarks:
            # Use display name for the series filter/label
            display_name = self.series_display_names.get(
                benchmark.series_name, benchmark.series_name
            )
            series_set.add(display_name)
            workloads_set.add(benchmark.workload)
            if benchmark.scale_factor is not None:
                scale_factors_set.add(benchmark.scale_factor)
            node_counts_set.add(benchmark.node_count)
            stream_counts_set.add(benchmark.stream_count)
            for system in benchmark.systems:
                systems_set.add(system.name)
                node_counts_set.add(system.node_count)

        # Build benchmark entries for JSON
        benchmark_entries = []
        for benchmark in benchmarks:
            systems_data = [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "version": s.version,
                    "node_count": s.node_count,
                    "median_ms": round(s.median_ms, 2),
                    "avg_ms": round(s.avg_ms, 2),
                    "geomean_ms": round(s.geomean_ms, 2),
                    "total_ms": round(s.total_ms, 2),
                    "min_ms": round(s.min_ms, 2),
                    "max_ms": round(s.max_ms, 2),
                    "query_count": s.query_count,
                    "bench_score": round(s.bench_score, 1),
                    "success_rate": round(s.success_rate, 1),
                }
                for s in benchmark.systems
            ]

            queries_data = {}
            for query_name, system_stats in benchmark.queries.items():
                queries_data[query_name] = {
                    sys_name: {
                        "median": round(stats.median, 2),
                        "avg": round(stats.avg, 2),
                        "min": round(stats.min, 2),
                        "max": round(stats.max, 2),
                        "std": round(stats.std, 2),
                        "count": stats.count,
                        "success_rate": round(stats.success_rate, 1),
                    }
                    for sys_name, stats in system_stats.items()
                }

            series_display = self.series_display_names.get(
                benchmark.series_name, benchmark.series_name
            )
            benchmark_entries.append(
                {
                    "id": benchmark.benchmark_id,
                    "series": series_display,
                    "config": benchmark.config_name,
                    "project_id": benchmark.project_id,
                    "workload": benchmark.workload,
                    "scale_factor": benchmark.scale_factor,
                    "node_count": benchmark.node_count,
                    "stream_count": benchmark.stream_count,
                    "environment": benchmark.environment,
                    "instance_type": benchmark.instance_type,
                    "run_date": benchmark.run_date,
                    "report_url": benchmark.report_url,
                    "systems": systems_data,
                    "queries": queries_data,
                }
            )

        return {
            "meta": {
                "suite_name": self.config.name,
                "suite_version": self.config.version,
                "suite_description": self.config.description,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_benchmarks": len(benchmarks),
            },
            "filters": {
                "series": sorted(series_set),
                "systems": sorted(systems_set),
                "workloads": sorted(workloads_set),
                "scale_factors": sorted(scale_factors_set),
                "node_counts": sorted(node_counts_set),
                "stream_counts": sorted(stream_counts_set),
            },
            "benchmarks": benchmark_entries,
        }

    def _resolve_chart_visibility(self, site_data: dict[str, Any]) -> dict[str, bool]:
        """Auto-detect which charts are relevant, then apply explicit overrides."""
        filters = site_data["filters"]
        benchmarks = site_data["benchmarks"]
        has_queries = any(len(b.get("queries", {})) > 0 for b in benchmarks)

        # Auto-detect based on data
        auto = {
            "scaling_by_nodes": len(filters["node_counts"]) > 1,
            "scaling_by_streams": len(filters["stream_counts"]) > 1,
            "scaling_by_sf": len(filters["scale_factors"]) > 1,
            "comparison": len(benchmarks) > 0,
            "heatmap": has_queries,
            "efficiency": len(filters["node_counts"]) > 1,
            "query_scatter": has_queries,
            "stacked_series": len(filters["series"]) > 1,
        }

        # Apply explicit overrides from config (non-None values win)
        charts_config = self.config.publish.charts
        for chart_name in auto:
            override = getattr(charts_config, chart_name, None)
            if override is not None:
                auto[chart_name] = override

        return auto

    def _resolve_table_columns(self, site_data: dict[str, Any]) -> list[dict[str, str]]:
        """Auto-detect which table columns are relevant."""
        filters = site_data["filters"]

        # Always-present columns
        columns = [{"key": "benchmark", "label": "Benchmark"}]

        # Conditional columns
        if len(filters["series"]) > 1:
            columns.append({"key": "series", "label": "Series"})
        if len(filters["node_counts"]) > 1:
            columns.append({"key": "nodes", "label": "Nodes"})
        if len(filters["scale_factors"]) > 1:
            columns.append({"key": "scale_factor", "label": "Scale Factor"})
        if len(filters["stream_counts"]) > 1:
            columns.append({"key": "streams", "label": "Streams"})

        # Always-present columns
        columns.extend(
            [
                {"key": "systems", "label": "Systems"},
                {"key": "winner", "label": "Winner"},
                {"key": "speedup", "label": "Speedup"},
            ]
        )

        if self.include_reports:
            columns.append({"key": "report", "label": "Report"})

        return columns

    def _copy_reports(self, benchmarks: list[BenchmarkDataEntry]) -> None:
        """Copy individual benchmark reports to the output directory."""
        reports_dir = self.output_dir / "reports"
        ensure_directory(reports_dir)

        copied_count = 0
        for benchmark in benchmarks:
            # Source: results/{project_id}/reports/3-full/
            src_dir = Path("results") / benchmark.project_id / "reports" / "3-full"

            if not src_dir.exists():
                # Try alternative path structure
                src_dir = Path("results") / benchmark.project_id / "reports"
                if not src_dir.exists():
                    continue

            # Destination: reports/{series}/{config}/
            dst_dir = reports_dir / benchmark.series_name / benchmark.config_name

            try:
                if dst_dir.exists():
                    shutil.rmtree(dst_dir)
                shutil.copytree(src_dir, dst_dir)
                copied_count += 1
            except Exception as e:
                console.print(
                    f"  [yellow]Warning: Could not copy report for "
                    f"{benchmark.benchmark_id}: {e}[/yellow]"
                )

        if copied_count > 0:
            console.print(f"  Copied {copied_count} reports")

    def _render_site(self, site_data: dict[str, Any]) -> None:
        """Render the HTML site."""
        template_type = self.config.publish.template
        if template_type == "leaderboard":
            self._render_leaderboard_site(site_data)
        else:
            self._render_dashboard_site(site_data)

    def _render_dashboard_site(self, site_data: dict[str, Any]) -> None:
        """Render the dashboard-style HTML site."""
        # Create assets directory
        assets_dir = self.output_dir / "assets"
        ensure_directory(assets_dir)

        # Resolve chart visibility and table columns
        charts = self._resolve_chart_visibility(site_data)
        table_columns = self._resolve_table_columns(site_data)

        # Embed table_columns in site_data so JS can use them
        site_data["table_columns"] = table_columns

        # Prepare context
        context = {
            "title": self.title,
            "theme": self.theme,
            "base_url": self.base_url,
            "data": site_data,
            "data_json": json.dumps(site_data, indent=2),
            "include_reports": self.include_reports,
            "charts": charts,
            "table_columns": table_columns,
        }

        # Render main template
        try:
            template = self.jinja_env.get_template("suite_publish/index.html.j2")
            html_content = template.render(**context)
        except Exception as e:
            console.print(f"[red]Template error: {e}[/red]")
            raise

        # Write index.html
        index_file = self.output_dir / "index.html"
        index_file.write_text(html_content, encoding="utf-8")

        # Render and write CSS
        try:
            css_template = self.jinja_env.get_template("suite_publish/styles.css.j2")
            css_content = css_template.render(**context)
            (assets_dir / "styles.css").write_text(css_content, encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not render CSS: {e}[/yellow]")

        # Render and write JavaScript
        try:
            js_template = self.jinja_env.get_template("suite_publish/app.js.j2")
            js_content = js_template.render(**context)
            (assets_dir / "app.js").write_text(js_content, encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not render JS: {e}[/yellow]")

    def _render_leaderboard_site(self, site_data: dict[str, Any]) -> None:
        """Render the leaderboard-style HTML site."""
        assets_dir = self.output_dir / "assets"
        ensure_directory(assets_dir)

        context = {
            "title": self.title,
            "theme": self.theme,
            "base_url": self.base_url,
            "data": site_data,
            "data_json": json.dumps(site_data, indent=2),
        }

        template_dir = "suite_publish_leaderboard"

        try:
            template = self.jinja_env.get_template(f"{template_dir}/index.html.j2")
            html_content = template.render(**context)
        except Exception as e:
            console.print(f"[red]Template error: {e}[/red]")
            raise

        index_file = self.output_dir / "index.html"
        index_file.write_text(html_content, encoding="utf-8")

        try:
            css_template = self.jinja_env.get_template(f"{template_dir}/styles.css.j2")
            css_content = css_template.render(**context)
            (assets_dir / "styles.css").write_text(css_content, encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not render CSS: {e}[/yellow]")

        try:
            js_template = self.jinja_env.get_template(f"{template_dir}/app.js.j2")
            js_content = js_template.render(**context)
            (assets_dir / "app.js").write_text(js_content, encoding="utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not render JS: {e}[/yellow]")

    def _load_system_info(self, project_id: str) -> dict[str, Any]:
        """Load system.json and setup_*.json for hardware/config details."""
        results_dir = Path("results") / project_id
        info: dict[str, Any] = {}

        # Load system.json (global) or fall back to system_{name}.json (per-system)
        system_json = results_dir / "system.json"
        if system_json.exists():
            try:
                info["system"] = load_json(system_json)
            except Exception:
                pass
        else:
            for sys_file in sorted(results_dir.glob("system_*.json")):
                try:
                    info["system"] = load_json(sys_file)
                    break
                except Exception:
                    pass

        # Load setup_*.json files
        setup_info: dict[str, Any] = {}
        for setup_file in sorted(results_dir.glob("setup_*.json")):
            try:
                setup_info[setup_file.stem] = load_json(setup_file)
            except Exception:
                pass
        if setup_info:
            info["setup"] = setup_info

        return info

    def _render_queries_for_system(
        self,
        workload_name: str,
        system_kind: str,
        system_name: str,
        scale_factor: int | float | None,
        workload_config: dict[str, Any],
    ) -> dict[str, str]:
        """Render query SQL templates for a specific system kind.

        Uses lightweight Jinja2 rendering without full workload/system objects.
        """
        workloads_dir = get_workloads_dir()
        queries_dir = workloads_dir / workload_name / "queries"
        if not queries_dir.exists():
            return {}

        # Determine variant for this system
        system_variants = workload_config.get("system_variants") or {}
        variant = system_variants.get(
            system_name, workload_config.get("variant", "official")
        )

        # Build template search paths
        search_paths = [str(queries_dir)]
        env = Environment(  # nosec B701
            loader=FileSystemLoader(search_paths),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        context = {
            "system_kind": system_kind,
            "scale_factor": scale_factor or 1,
            "schema": "benchmark",
            "system_extra": {},
            "node_count": 1,
            "cluster": "benchmark_cluster",
            "variant": variant,
        }

        rendered: dict[str, str] = {}
        # Find all Q*.sql files
        for sql_file in sorted(queries_dir.glob("Q*.sql")):
            query_name = sql_file.stem  # e.g. "Q01"
            # Try variant paths first, then fall back to base
            template_paths = [
                f"variants/{variant}/{system_kind}/{query_name}.sql",
                f"variants/{variant}/{query_name}.sql",
                f"{query_name}.sql",
            ]
            for tpath in template_paths:
                try:
                    template = env.get_template(tpath)
                    rendered[query_name] = template.render(**context)
                    break
                except Exception:
                    continue

        return rendered

    def _render_ddl_for_system(
        self,
        workload_name: str,
        system_kind: str,
        node_count: int,
        scale_factor: int | float | None,
    ) -> dict[str, str]:
        """Render DDL/setup SQL scripts for a specific system kind."""
        workloads_dir = get_workloads_dir()
        setup_dir = workloads_dir / workload_name / "setup"
        if not setup_dir.exists():
            return {}

        system_setup_dir = setup_dir / system_kind
        if not system_setup_dir.exists():
            return {}

        env = Environment(  # nosec B701
            loader=FileSystemLoader([str(setup_dir)]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        context: dict[str, Any] = {
            "system_kind": system_kind,
            "scale_factor": scale_factor or 1,
            "schema": "benchmark",
            "system_extra": {},
            "node_count": node_count,
            "cluster": "benchmark_cluster",
            "variant": "official",
            "data_locations": {},
        }

        scripts: dict[str, str] = {}
        for script_name in [
            "create_tables",
            "create_constraints",
            "create_indexes",
            "analyze_tables",
        ]:
            try:
                template = env.get_template(f"{system_kind}/{script_name}.sql")
                scripts[script_name] = template.render(**context)
            except Exception:
                pass

        return scripts

    def _generate_packages(
        self, entries: list[dict[str, Any]], output_dir: Path
    ) -> None:
        """Generate workload packages for each benchmark entry."""
        from ..package.creator import create_workload_zip

        packages_dir = output_dir / "packages"
        ensure_directory(packages_dir)
        seen_projects: set[str] = set()

        for entry in entries:
            project_id = entry.get("project_id")
            if not project_id or project_id in seen_projects:
                continue
            seen_projects.add(project_id)

            config_path = Path("results") / project_id / "config.yaml"
            if not config_path.exists():
                continue

            try:
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                zip_path = create_workload_zip(cfg)
                dest = packages_dir / f"{project_id}-workload.zip"
                shutil.copy2(zip_path, dest)
                entry["package_url"] = f"packages/{project_id}-workload.zip"
            except Exception as e:
                console.print(
                    f"  [yellow]Warning: Package failed for {project_id}: {e}[/yellow]"
                )

    def _build_leaderboard_data(
        self, benchmarks: list[BenchmarkDataEntry]
    ) -> dict[str, Any]:
        """Build leaderboard data: one entry per system, grouped by workload tab."""
        entries: list[dict[str, Any]] = []
        workload_tabs_set: set[str] = set()

        for benchmark in benchmarks:
            # The workload tab is the series display name
            workload_tab = self.series_display_names.get(
                benchmark.series_name, benchmark.series_name
            )
            workload_tabs_set.add(workload_tab)

            # Load system info for hardware details
            sys_info = self._load_system_info(benchmark.project_id)
            system_json = sys_info.get("system", {})
            setup_json = sys_info.get("setup", {})

            # Load workload config from original YAML for variant resolution
            config_path = Path("results") / benchmark.project_id / "config.yaml"
            workload_config: dict[str, Any] = {}
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        cfg = yaml.safe_load(f) or {}
                    workload_config = cfg.get("workload", {})
                except Exception:
                    pass

            # Extract hardware info from system.json
            # Supports both flat format (top-level cpu_model, memory_total_gb)
            # and nested format (cpu_info.model_name, memory_info.total_gb)
            cpu_model = system_json.get("cpu_model", "") or system_json.get(
                "cpu_info", {}
            ).get("model_name", "")
            cpu_count = system_json.get("cpu_count_logical", 0) or system_json.get(
                "cpu_info", {}
            ).get("count_logical", 0)
            memory_gb = system_json.get("memory_total_gb", 0)
            if not memory_gb:
                total_kb = system_json.get("memory_total_kb", 0)
                if not total_kb:
                    total_kb = system_json.get("memory_info", {}).get("total_kb", 0)
                memory_gb = round(total_kb / (1024 * 1024), 1) if total_kb else 0
            system_info = {
                "cpu_model": cpu_model,
                "cpu_count_logical": cpu_count,
                "memory_total_gb": round(memory_gb, 1) if memory_gb else 0,
            }

            for system in benchmark.systems:
                # Build per-query times from benchmark.queries
                query_times: dict[str, dict[str, float]] = {}
                for query_name, system_stats in benchmark.queries.items():
                    if system.name in system_stats:
                        stats = system_stats[system.name]
                        query_times[query_name] = {
                            "median": round(stats.median, 2),
                            "avg": round(stats.avg, 2),
                            "min": round(stats.min, 2),
                            "max": round(stats.max, 2),
                        }

                # Build per-query errors for this system
                query_errors: dict[str, str] = {}
                for query_name, sys_errors in benchmark.query_errors.items():
                    if system.name in sys_errors:
                        query_errors[query_name] = sys_errors[system.name]

                # Render query SQL and DDL for this system
                query_sql = self._render_queries_for_system(
                    benchmark.workload,
                    system.kind,
                    system.name,
                    benchmark.scale_factor,
                    workload_config,
                )
                ddl_scripts = self._render_ddl_for_system(
                    benchmark.workload,
                    system.kind,
                    system.node_count,
                    benchmark.scale_factor,
                )

                # Extract setup commands and config parameters
                setup_data = setup_json.get(f"setup_{system.name}", {})
                setup_commands = setup_data.get("commands", {})
                config_parameters = setup_data.get("config_parameters", {})

                # Build warmup times for this system
                warmup_times: dict[str, dict[str, float]] = {}
                for qname, sys_stats in benchmark.warmup_queries.items():
                    if system.name in sys_stats:
                        warmup_times[qname] = sys_stats[system.name]

                entries.append(
                    {
                        "system_name": system.name,
                        "system_kind": system.kind,
                        "system_version": system.version,
                        "bench_score": round(system.bench_score, 1),
                        "speed_score": round(system.speed_score, 1),
                        "scale_score": round(system.scale_score, 1),
                        "geomean_ms": round(system.geomean_ms, 2),
                        "sum_medians_ms": round(system.sum_medians_ms, 2),
                        "total_ms": round(system.total_ms, 2),
                        "query_count": system.query_count,
                        "node_count": system.node_count,
                        "success_rate": round(system.success_rate, 1),
                        "workload_tab": workload_tab,
                        "workload_name": benchmark.workload,
                        "scale_factor": benchmark.scale_factor,
                        "stream_count": benchmark.stream_count,
                        "instance_type": benchmark.instance_type,
                        "environment": benchmark.environment,
                        "run_date": benchmark.run_date,
                        "project_id": benchmark.project_id,
                        "package_url": None,
                        "query_times": query_times,
                        "query_errors": query_errors,
                        "query_sql": query_sql,
                        "ddl_scripts": ddl_scripts,
                        "setup_commands": setup_commands,
                        "config_parameters": config_parameters,
                        "warmup_times": warmup_times,
                        "system_info": system_info,
                        "setup_info": setup_json,
                    }
                )

        # Sort entries by bench_score descending
        entries.sort(key=lambda e: e["bench_score"], reverse=True)

        # Order tabs to match suite.yaml series order
        series_order = list(self.series_display_names.values())
        workload_tabs = [t for t in series_order if t in workload_tabs_set]

        return {
            "meta": {
                "suite_name": self.config.name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_entries": len(entries),
                "score_formula": (
                    "sqrt(SpeedScore × ScaleScore), where "
                    "SpeedScore = SF / geomean_s, "
                    "ScaleScore = SF × S × Q / sum_medians_s"
                ),
                "score_description": (
                    "Composite metric combining per-query speed and "
                    "aggregate workload scale. Higher is better. "
                    "SF = scale factor, S = stream count, "
                    "Q = expected query count."
                ),
            },
            "workload_tabs": workload_tabs,
            "entries": entries,
        }

    def _slugify(self, text: str) -> str:
        """Convert text to filesystem-safe slug."""
        import re

        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        return slug.strip("_")

    def _format_number(self, value: float, decimals: int = 1) -> str:
        """Format number for display."""
        if pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}f}"

    def _format_duration(self, ms: float) -> str:
        """Format duration in milliseconds to human-readable string."""
        if ms < 1000:
            return f"{ms:.1f}ms"
        elif ms < 60000:
            return f"{ms / 1000:.2f}s"
        else:
            minutes = int(ms // 60000)
            seconds = (ms % 60000) / 1000
            return f"{minutes}m {seconds:.1f}s"

    def _is_report_stale(self, project_id: str) -> bool:
        """Check if a benchmark's report is older than its data.

        A report is considered stale if runs.csv has been modified more
        recently than REPORT.html, indicating the data has changed since
        the report was generated.

        Args:
            project_id: The project ID to check

        Returns:
            True if the report is stale or missing, False otherwise
        """
        results_dir = Path("results") / project_id
        runs_csv = results_dir / "runs.csv"
        report_html = results_dir / "reports" / "3-full" / "REPORT.html"

        # No report exists - it's stale
        if not report_html.exists():
            return True

        # No data exists - report is not stale (nothing to regenerate from)
        if not runs_csv.exists():
            return False

        # Compare modification times
        return runs_csv.stat().st_mtime > report_html.stat().st_mtime

    def _regenerate_stale_reports(self, benchmarks: list[BenchmarkDataEntry]) -> int:
        """Regenerate reports that are older than their data.

        Args:
            benchmarks: List of benchmark entries to check

        Returns:
            Number of reports regenerated
        """
        from ..report.render import render_report

        regenerated = 0
        for benchmark in benchmarks:
            if self._is_report_stale(benchmark.project_id):
                # Find the config path for this benchmark
                config_path = self.runner.get_config_path(
                    benchmark.series_name, benchmark.config_name
                )

                if config_path and config_path.exists():
                    console.print(
                        f"  [blue]Regenerating stale report: "
                        f"{benchmark.benchmark_id}[/blue]"
                    )
                    try:
                        cfg = load_config(str(config_path))
                        render_report(cfg)
                        regenerated += 1
                    except Exception as e:
                        console.print(
                            f"  [yellow]Warning: Could not regenerate "
                            f"{benchmark.benchmark_id}: {e}[/yellow]"
                        )

        return regenerated


def publish_suite(
    suite_path: Path,
    output_dir: Path | None = None,
    title: str | None = None,
    base_url: str | None = None,
    include_reports: bool | None = None,
    theme: str | None = None,
    regenerate_stale: bool = False,
) -> Path:
    """Main entry point for publishing a suite.

    Args:
        suite_path: Path to suite directory
        output_dir: Output directory (overrides suite.yaml)
        title: Custom site title (overrides suite.yaml)
        base_url: Base URL for assets (overrides suite.yaml)
        include_reports: Whether to copy reports (overrides suite.yaml)
        theme: Theme (overrides suite.yaml)
        regenerate_stale: Whether to regenerate reports older than their data

    Returns:
        Path to generated index.html
    """
    from . import load_suite_config

    suite_yaml = suite_path / "suite.yaml"
    if not suite_yaml.exists():
        raise FileNotFoundError(f"Suite configuration not found: {suite_yaml}")

    config = load_suite_config(suite_yaml)

    publisher = SuitePublisher(
        suite_path=suite_path,
        config=config,
        output_dir=output_dir,
        title=title,
        base_url=base_url,
        include_reports=include_reports,
        theme=theme,
        regenerate_stale=regenerate_stale,
    )

    return publisher.publish()
