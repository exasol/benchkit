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

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.console import Console

from ..config import load_config
from ..util import ensure_directory, load_json
from . import SuiteConfig, SuiteRunner, SuiteStateManager

console = Console()


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
    total_ms: float
    min_ms: float
    max_ms: float
    query_count: int
    success_rate: float = 100.0


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


class SuitePublisher:
    """Generates a static website from suite benchmark results."""

    def __init__(
        self,
        suite_path: Path,
        config: SuiteConfig,
        output_dir: Path | None = None,
        title: str | None = None,
        base_url: str = "./",
        include_reports: bool = True,
        theme: str = "auto",
        regenerate_stale: bool = False,
    ):
        """Initialize the publisher.

        Args:
            suite_path: Path to the suite directory
            config: Loaded suite configuration
            output_dir: Output directory for the website
            title: Custom site title (defaults to suite name)
            base_url: Base URL for assets
            include_reports: Whether to copy individual benchmark reports
            theme: Theme (light, dark, auto)
            regenerate_stale: Whether to regenerate reports older than their data
        """
        self.suite_path = suite_path
        self.config = config
        self.output_dir = output_dir or Path("docs") / self._slugify(config.name)
        self.title = title or config.name
        self.base_url = base_url
        self.include_reports = include_reports
        self.theme = theme
        self.regenerate_stale = regenerate_stale

        self.state_manager = SuiteStateManager(suite_path)
        self.runner = SuiteRunner(suite_path, config)

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.jinja_env.filters["format_number"] = self._format_number
        self.jinja_env.filters["format_duration"] = self._format_duration

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

        # Build site data structure
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
        discovered = self.runner.discover_configs(include_disabled=True)

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
            cfg = load_config(str(config_path))
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
        multiuser_config = workload_config.get("multiuser", {})
        stream_count = (
            multiuser_config.get("num_streams")
            or workload_config.get("num_streams")
            or 1
        )

        # Extract environment info
        env_config = cfg.get("env", {})
        environment = env_config.get("mode", "local")

        # Get node count from first system
        systems_config = cfg.get("systems", [])
        node_count = 1
        instance_type = None
        if systems_config:
            first_system = systems_config[0]
            node_count = first_system.get("setup", {}).get("node_count", 1)
            system_name = first_system.get("name", "")
            instances = env_config.get("instances", {})
            if system_name in instances:
                instance_type = instances[system_name].get("instance_type")

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
                systems.append(
                    SystemDataEntry(
                        name=system_name,
                        kind=system_config.get("kind", system_name),
                        version=system_config.get("version", "unknown"),
                        median_ms=float(success_df["elapsed_ms"].median()),
                        avg_ms=float(success_df["elapsed_ms"].mean()),
                        total_ms=float(success_df["elapsed_ms"].sum()),
                        min_ms=float(success_df["elapsed_ms"].min()),
                        max_ms=float(success_df["elapsed_ms"].max()),
                        query_count=len(success_df["query"].unique()),
                        success_rate=success_rate,
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
            series_set.add(benchmark.series_name)
            workloads_set.add(benchmark.workload)
            if benchmark.scale_factor is not None:
                scale_factors_set.add(benchmark.scale_factor)
            node_counts_set.add(benchmark.node_count)
            stream_counts_set.add(benchmark.stream_count)
            for system in benchmark.systems:
                systems_set.add(system.name)

        # Build benchmark entries for JSON
        benchmark_entries = []
        for benchmark in benchmarks:
            systems_data = [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "version": s.version,
                    "median_ms": round(s.median_ms, 2),
                    "avg_ms": round(s.avg_ms, 2),
                    "total_ms": round(s.total_ms, 2),
                    "min_ms": round(s.min_ms, 2),
                    "max_ms": round(s.max_ms, 2),
                    "query_count": s.query_count,
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

            benchmark_entries.append(
                {
                    "id": benchmark.benchmark_id,
                    "series": benchmark.series_name,
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
        # Create assets directory
        assets_dir = self.output_dir / "assets"
        ensure_directory(assets_dir)

        # Prepare context
        context = {
            "title": self.title,
            "theme": self.theme,
            "base_url": self.base_url,
            "data": site_data,
            "data_json": json.dumps(site_data, indent=2),
            "include_reports": self.include_reports,
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

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        return text.lower().replace(" ", "_").replace("-", "_").replace(".", "_")

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
    base_url: str = "./",
    include_reports: bool = True,
    theme: str = "auto",
    regenerate_stale: bool = False,
) -> Path:
    """Main entry point for publishing a suite.

    Args:
        suite_path: Path to suite directory
        output_dir: Output directory for the website
        title: Custom site title
        base_url: Base URL for assets
        include_reports: Whether to copy individual reports
        theme: Theme (light, dark, auto)
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
