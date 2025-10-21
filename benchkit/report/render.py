"""Report rendering and generation."""

import json
import os
import shutil
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..package.creator import create_workload_zip
from ..util import ensure_directory, load_json
from .figures import create_performance_plots
from .html_renderer import render_html_report
from .tables import (
    create_aggregated_performance_table_html,
    create_comparison_table,
    create_comparison_table_html,
    create_ranking_table_html,
    create_summary_table_html,
    format_table_markdown,
    summary_table,
)


class ReportRenderer:
    """Renders benchmark results into reports using templates."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.project_id = config["project_id"]
        self.report_config = config["report"]

        # Store sensitive values to be sanitized (populated during rendering)
        self.sensitive_values: dict[str, str] = {}

        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape(enabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom functions to Jinja2 environment
        self.jinja_env.globals["include"] = self._include_template
        self.jinja_env.filters["format_number"] = self._format_number
        self.jinja_env.filters["format_number_ceil"] = self._format_number_ceil
        self.jinja_env.filters["format_duration"] = self._format_duration
        self.jinja_env.filters["sanitize"] = self._sanitize_for_report

        # Shared setup rendering configuration
        self.setup_category_order = [
            "storage_setup",
            "prerequisites",
            "repository_setup",
            "user_setup",
            "tool_setup",
            "ssh_setup",
            "installation",
            "configuration",
            "user_configuration",
            "cluster_deployment",
            "license_setup",
            "database_tuning",
            "service_management",
        ]
        self.setup_category_labels = {
            "storage_setup": "Storage Configuration",
            "prerequisites": "Prerequisites",
            "repository_setup": "Repository Setup",
            "user_setup": "User Setup",
            "tool_setup": "Tool Setup",
            "ssh_setup": "SSH Setup",
            "installation": "Installation",
            "configuration": "Configuration",
            "user_configuration": "User Configuration",
            "cluster_deployment": "Cluster Deployment",
            "license_setup": "License Setup",
            "database_tuning": "Database Tuning",
            "service_management": "Service Management",
        }
        default_filters = ["touch ~/", "echo 'installed'", "c4 ps", "uptime"]
        self.setup_category_filters = {
            "storage_setup": default_filters,
            "cluster_deployment": default_filters,
            "installation": default_filters,
            "default": default_filters,
        }
        self.jinja_env.globals.update(
            {
                "SETUP_CATEGORY_ORDER": self.setup_category_order,
                "SETUP_CATEGORY_LABELS": self.setup_category_labels,
                "SETUP_CATEGORY_FILTERS": self.setup_category_filters,
            }
        )

    def _get_baseline_system(self) -> str | None:
        """Get the baseline system from config (first system in systems list)."""
        systems = self.config.get("systems", [])
        if systems and len(systems) > 0:
            return str(systems[0]["name"])
        return None

    def render_report(self) -> str:
        """Render the complete report from results and templates."""
        # Extract system names from config to filter results
        system_names = [s["name"] for s in self.config.get("systems", [])]

        # Load benchmark data
        results_dir = Path("results") / self.project_id
        data = self._load_benchmark_data(results_dir)

        # Filter data to only include systems from config
        if system_names:
            data = self._filter_data_for_systems(data, system_names)

        # Generate figures
        figures = self._generate_figures(data, results_dir)

        # Create tables
        tables = self._generate_tables(data)

        # Load system information (filtered by system_names)
        system_info = self._load_system_info(results_dir, system_names=system_names)

        # Load setup summaries for actual commands used (filtered by system_names)
        setup_summaries = self._load_setup_summaries(
            results_dir, system_names=system_names
        )

        # Extract sensitive values from config and setup summaries for sanitization
        self._extract_sensitive_values(setup_summaries)

        # Load preparation timings (filtered by system_names)
        preparation_timings = self._load_preparation_timings(
            results_dir, system_names=system_names
        )

        # Load infrastructure setup timings
        infrastructure_timings = self._load_infrastructure_timings(results_dir)

        # Generate workload metadata
        workload_metadata = self._generate_workload_metadata()

        # Prepare template context
        context = {
            "cfg": self.config,
            "data": data,
            "figures": figures,
            "tables": tables,
            "system_info": system_info,
            "setup_summaries": setup_summaries,
            "preparation_timings": preparation_timings,
            "infrastructure_timings": infrastructure_timings,
            "workload_metadata": workload_metadata,
            "project_id": self.project_id,
            "results_dir": str(results_dir),
        }

        # Render main report template
        template = self.jinja_env.get_template("report.md.j2")
        rendered_content = template.render(**context)

        return rendered_content

    def save_report(self, content: str) -> Path:
        """
        Save rendered report and create self-contained report directory.

        Generates 3 reports:
        1. Short report (compares first two systems with installation details)
        2. Results report (all systems, query-focused, no installation)
        3. Full benchmark report (complete with all details)
        """
        output_path = Path(self.report_config["output_path"])

        # Create base report directory structure
        report_base_dir = output_path.parent / output_path.stem
        ensure_directory(report_base_dir)

        # Generate Report 1: Short
        print("Generating Report 1: Short (first two systems with installation)...")
        short_dir = self._generate_short_report(report_base_dir)

        # Generate Report 2: Results
        print("Generating Report 2: Detailed Results (all systems, no installation)...")
        self._generate_results_report(report_base_dir)

        # Generate Report 3: Full Benchmark (original REPORT.md/html)
        print("Generating Report 3: Full Benchmark Report...")
        full_report_dir = report_base_dir / "3-full"
        ensure_directory(full_report_dir)

        # Save markdown report
        report_file = full_report_dir / "REPORT.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)

        # Copy all result files as attachments (filtered by systems in config)
        system_names = [s["name"] for s in self.config.get("systems", [])]
        self._copy_attachments(full_report_dir, system_names=system_names)

        # Generate and save HTML version if enabled
        if self.report_config.get("generate_html", True):
            self._render_and_save_html(full_report_dir)

        # Create benchmark package
        self._create_workload_package(full_report_dir)
        if short_dir:
            self._create_workload_package(short_dir)

        # Persist project metadata for index generation
        metadata_file = self._write_project_metadata(report_base_dir)

        # Update the global report index if enabled
        if metadata_file and self.report_config.get("generate_index", True):
            index_dir = Path(self.report_config.get("index_output_dir", "results"))
            try:
                self._render_report_index(index_dir)
            except Exception as exc:
                print(f"Warning: Failed to render report index: {exc}")

        print(f"✓ Generated full benchmark report: {full_report_dir}")
        print(f"\n✅ All 3 reports generated successfully in: {report_base_dir}")

        return report_base_dir

    def _render_and_save_html(self, report_dir: Path) -> None:
        """Render and save HTML version of the report."""
        # Extract system names from config to filter results
        system_names = [s["name"] for s in self.config.get("systems", [])]

        # Load benchmark data
        results_dir = Path("results") / self.project_id
        data = self._load_benchmark_data(results_dir)

        # Filter data to only include systems from config
        if system_names:
            data = self._filter_data_for_systems(data, system_names)

        # Generate HTML-specific tables
        html_tables = self._generate_html_tables(data)

        # Load system information (filtered by system_names)
        system_info = self._load_system_info(results_dir, system_names=system_names)

        # Load setup summaries (filtered by system_names)
        setup_summaries = self._load_setup_summaries(
            results_dir, system_names=system_names
        )

        # Extract sensitive values
        self._extract_sensitive_values(setup_summaries)

        # Load preparation timings (filtered by system_names)
        preparation_timings = self._load_preparation_timings(
            results_dir, system_names=system_names
        )

        # Load infrastructure timings
        infrastructure_timings = self._load_infrastructure_timings(results_dir)

        # Get relative paths to figures for HTML
        figures_dir = Path(self.report_config["figures_dir"])
        relative_figures = {}
        if figures_dir.exists():
            for fig_file in figures_dir.glob("*.html"):
                fig_name = fig_file.stem
                # Path relative to report directory
                relative_figures[fig_name] = f"attachments/figures/{fig_file.name}"

        # Generate workload metadata
        workload_metadata = self._generate_workload_metadata()

        # Prepare context for HTML rendering
        context = {
            "cfg": self.config,
            "data": data,
            "figures": relative_figures,
            "tables": html_tables,
            "system_info": system_info,
            "setup_summaries": setup_summaries,
            "preparation_timings": preparation_timings,
            "infrastructure_timings": infrastructure_timings,
            "workload_metadata": workload_metadata,
            "project_id": self.project_id,
            "results_dir": str(results_dir),
        }

        # Render HTML report
        html_file = report_dir / "REPORT.html"
        render_html_report(context, template_dir="templates", output_file=html_file)

        # Copy CSS file
        css_src = Path("templates/styles.css.j2")
        if css_src.exists():
            css_dst = report_dir / "styles.css"
            # Render CSS template (in case it has variables)
            css_template = self.jinja_env.get_template("styles.css.j2")
            css_content = css_template.render(**context)
            with open(css_dst, "w", encoding="utf-8") as f:
                f.write(css_content)

    def _load_benchmark_data(self, results_dir: Path) -> dict[str, Any]:
        """Load and process benchmark data."""
        data = {}

        # Load CSV results
        runs_file = results_dir / "runs.csv"
        if runs_file.exists():
            data["runs_df"] = pd.read_csv(runs_file)
        else:
            data["runs_df"] = pd.DataFrame()

        # Load summary if available
        summary_file = results_dir / "summary.json"
        if summary_file.exists():
            data["summary"] = load_json(summary_file)
        else:
            data["summary"] = {}  # type: ignore

        # Load raw results
        raw_results_file = results_dir / "raw_results.json"
        if raw_results_file.exists():
            data["raw_results"] = load_json(raw_results_file)
        else:
            data["raw_results"] = []  # type: ignore

        return data

    def _load_system_info(
        self, results_dir: Path, system_names: list[str] | None = None
    ) -> dict[str, Any]:
        """Load system information and compare across instances.

        Args:
            results_dir: Directory containing result files
            system_names: Optional list of system names to filter by. If None, loads all systems.
        """
        from ..gather.system_probe import compare_system_configurations

        system_info = {}

        # Load main system.json (single system or local benchmark)
        system_file = results_dir / "system.json"
        if system_file.exists():
            system_info["primary"] = load_json(system_file)  # type: ignore

        # Look for per-system probe results (from cloud benchmarks)
        system_files = list(results_dir.glob("system_*.json"))
        if system_files:
            system_info["per_system"] = {}
            all_systems_data = []

            for sys_file in system_files:
                # Extract system name from filename
                system_name = sys_file.stem.replace("system_", "")

                # Filter by system_names if provided
                if system_names is not None and system_name not in system_names:
                    continue

                system_data = load_json(sys_file)
                system_info["per_system"][system_name] = system_data
                all_systems_data.append(system_data)

            # Compare and group similar systems
            if len(all_systems_data) > 1:
                system_info["comparison"] = compare_system_configurations(
                    all_systems_data
                )
            else:
                system_info["comparison"] = {
                    "groups": [
                        {
                            "description": "Single system",
                            "systems": [list(system_info["per_system"].keys())[0]],
                        }
                    ],
                    "total_systems": 1,
                    "unique_configurations": 1,
                }

        # If we only have main system.json, create a simple structure
        elif "primary" in system_info:
            system_info["comparison"] = {
                "groups": [
                    {
                        "description": self._create_system_description(
                            system_info["primary"]
                        ),
                        "systems": ["primary"],
                    }
                ],
                "total_systems": 1,
                "unique_configurations": 1,
            }

        return system_info

    def _create_system_description(self, system_data: dict[str, Any]) -> str:
        """Create a human-readable description of a system."""
        parts = []

        # CPU information
        if system_data.get("cpu_model"):
            cpu_model = str(system_data["cpu_model"]).strip()
            cpu_model = (
                cpu_model.replace("Intel(R)", "").replace("(R)", "").replace("(TM)", "")
            )
            cpu_model = " ".join(cpu_model.split())  # Remove extra spaces
            parts.append(f"CPU: {cpu_model}")

        if system_data.get("cpu_count_logical"):
            parts.append(f"{system_data['cpu_count_logical']} vCPUs")

        # Memory information
        if system_data.get("memory_total_gb"):
            parts.append(f"{system_data['memory_total_gb']}GB RAM")

        # Cloud instance type
        if system_data.get("aws", {}).get("instance_type"):
            parts.append(f"({system_data['aws']['instance_type']})")
        elif system_data.get("gcp", {}).get("machine_type"):
            parts.append(f"({system_data['gcp']['machine_type']})")
        elif system_data.get("azure", {}).get("vm_size"):
            parts.append(f"({system_data['azure']['vm_size']})")

        return ", ".join(parts) if parts else "System configuration available"

    def _load_setup_summaries(
        self, results_dir: Path, system_names: list[str] | None = None
    ) -> dict[str, Any]:
        """Load setup summaries for all systems.

        Args:
            results_dir: Directory containing result files
            system_names: Optional list of system names to filter by. If None, loads all systems.
        """
        setup_summaries = {}

        # Find all setup_*.json files
        setup_files = list(results_dir.glob("setup_*.json"))

        for setup_file in setup_files:
            # Extract system name from filename (setup_systemname.json -> systemname)
            system_name = setup_file.stem.replace("setup_", "")

            # Filter by system_names if provided
            if system_names is not None and system_name not in system_names:
                continue

            setup_summaries[system_name] = load_json(setup_file)

        return setup_summaries

    def _load_preparation_timings(
        self, results_dir: Path, system_names: list[str] | None = None
    ) -> dict[str, Any]:
        """Load workload preparation timings for all systems.

        Args:
            results_dir: Directory containing result files
            system_names: Optional list of system names to filter by. If None, loads all systems.
        """
        preparation_timings = {}

        # Find all preparation_*.json files
        prep_files = list(results_dir.glob("preparation_*.json"))

        for prep_file in prep_files:
            # Extract system name from filename (preparation_systemname.json -> systemname)
            system_name = prep_file.stem.replace("preparation_", "")

            # Filter by system_names if provided
            if system_names is not None and system_name not in system_names:
                continue

            preparation_timings[system_name] = load_json(prep_file)

        return preparation_timings

    def _load_infrastructure_timings(self, results_dir: Path) -> dict[str, Any]:
        """Load infrastructure setup timings."""
        infra_file = results_dir / "infrastructure_setup.json"
        if infra_file.exists():
            return cast(dict[str, Any], load_json(infra_file))
        return {}

    def _generate_figures(
        self, data: dict[str, Any], results_dir: Path
    ) -> dict[str, str]:
        """Generate visualization figures using Plotly."""
        figures_dir = Path(self.report_config["figures_dir"])
        ensure_directory(figures_dir)

        figures: dict[str, str] = {}
        runs_df = data["runs_df"]

        if runs_df.empty:
            return figures

        # Generate performance plots based on configuration
        if self.report_config.get("show_boxplots", True):
            figures["boxplot"] = create_performance_plots(
                runs_df, figures_dir, plot_type="boxplot"
            )

        if self.report_config.get("show_latency_cdf", False):
            figures["cdf"] = create_performance_plots(
                runs_df, figures_dir, plot_type="cdf"
            )

        if self.report_config.get("show_bar_chart", True):
            figures["bar_chart"] = create_performance_plots(
                runs_df, figures_dir, plot_type="bar"
            )

        if self.report_config.get("show_heatmap", False):
            figures["heatmap"] = create_performance_plots(
                runs_df, figures_dir, plot_type="heatmap"
            )

        # Generate additional visualization types
        if (
            self.report_config.get("show_speedup_plot", True)
            and len(runs_df["system"].unique()) > 1
        ):
            from .figures import create_speedup_plot

            # Get baseline from config (first system), not from CSV order
            baseline_system = self._get_baseline_system()
            if baseline_system is not None:
                figures["speedup"] = create_speedup_plot(
                    runs_df, baseline_system, figures_dir
                )

        # Generate all-systems comparison plot for full report (Post 3)
        if len(runs_df["system"].unique()) > 1:
            from .figures import create_all_systems_comparison_plot

            figures["all_systems"] = create_all_systems_comparison_plot(
                runs_df, figures_dir
            )

        if self.report_config.get("show_system_overview", True):
            from .figures import create_system_overview_plot

            figures["system_overview"] = create_system_overview_plot(
                runs_df, figures_dir
            )

        return figures

    def _generate_tables(self, data: dict[str, Any]) -> dict[str, str]:
        """Generate markdown tables from data."""
        tables: dict[str, str] = {}
        runs_df = data["runs_df"]

        if runs_df.empty:
            return tables

        # Summary table
        if not runs_df.empty:
            summary_df = summary_table(runs_df, data.get("summary"))
            tables["summary"] = format_table_markdown(summary_df)

        # Comparison table
        if len(runs_df["system"].unique()) > 1:
            baseline_system = self._get_baseline_system()
            comparison_df = create_comparison_table(runs_df, baseline_system)
            tables["comparison"] = format_table_markdown(comparison_df)

        # Query type performance table
        if not runs_df.empty:
            from .tables import create_query_type_performance_table

            query_type_df = create_query_type_performance_table(runs_df)
            if not query_type_df.empty:
                tables["query_type_performance"] = format_table_markdown(query_type_df)

        return tables

    def _generate_html_tables(self, data: dict[str, Any]) -> dict[str, str]:
        """Generate HTML tables with color coding from data."""
        tables: dict[str, str] = {}
        runs_df = data["runs_df"]

        if runs_df.empty:
            return tables

        # Summary table
        if not runs_df.empty:
            tables["summary"] = create_summary_table_html(runs_df, data.get("summary"))

        # Comparison table
        if len(runs_df["system"].unique()) > 1:
            baseline_system = self._get_baseline_system()
            tables["comparison"] = create_comparison_table_html(
                runs_df, baseline_system
            )

        # Query type performance table
        if not runs_df.empty:
            from .tables import create_query_type_performance_table_html

            tables["query_type_performance"] = create_query_type_performance_table_html(
                runs_df
            )

        # Ranking table
        if len(runs_df["system"].unique()) > 1:
            tables["ranking"] = create_ranking_table_html(runs_df)

        # Aggregated performance table
        if not runs_df.empty:
            tables["aggregated"] = create_aggregated_performance_table_html(runs_df)

        return tables

    def _include_template(self, template_name: str, **kwargs: Any) -> str:
        """Include a sub-template (for Jinja2 include function)."""
        try:
            template = self.jinja_env.get_template(f"snippets/{template_name}.md.j2")
            # Merge context with provided kwargs
            context = dict(kwargs)
            context.update({"cfg": self.config, "project_id": self.project_id})
            return template.render(**context)
        except Exception as e:
            return f"<!-- Error including template {template_name}: {e} -->"

    def _format_number(self, value: float, decimals: int = 1) -> str:
        """Format number for display."""
        if pd.isna(value):
            return "N/A"
        return f"{value:.{decimals}f}"

    def _format_number_ceil(self, value: float) -> str:
        """
        Format speedup factor with smart rounding:
        - If within 10% of 1.0 (0.9-1.1): show as "~1.0" (essentially equal)
        - If < 5.0: show 1 decimal place (e.g., 1.7, 2.3, 4.5)
        - If >= 5.0: use ceiling for cleaner display (e.g., 6, 10, 30)
        """
        import math

        if pd.isna(value):
            return "N/A"

        v = abs(value)

        # Handle edge case: tested system is actually faster (shouldn't happen in teaser)
        if v < 0.9:
            return f"{value:.1f}"

        # Case 1: Nearly equal performance (within 10% of 1.0)
        if v <= 1.1:
            return "~1.0"

        # Case 2: Small to moderate differences (1.1-5.0x)
        # Show precise 1 decimal to distinguish performance gaps
        if v < 3.5:
            return f"{value:.1f}"

        # Case 3: Large differences (5.0x and above)
        # Use ceiling for cleaner, more readable display
        return str(math.ceil(value))

    def _format_duration(self, seconds: float) -> str:
        """Format duration in a human-readable way."""
        if seconds < 1:
            return f"{seconds * 1000:.1f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"

    def _extract_sensitive_values(self, setup_summaries: dict[str, Any]) -> None:
        """Extract sensitive values from setup summaries and config for sanitization."""
        # Extract from setup summaries (which contain actual passwords and IPs used)
        for _system_name, summary in setup_summaries.items():
            config_params = summary.get("config_parameters", {})

            # Extract passwords
            if "image_password" in config_params:
                self.sensitive_values[config_params["image_password"]] = (
                    "<EXASOL_IMAGE_PASSWORD>"
                )
            if "db_password" in config_params:
                self.sensitive_values[config_params["db_password"]] = (
                    "<EXASOL_DB_PASSWORD>"
                )
            if "admin_password" in config_params:
                self.sensitive_values[config_params["admin_password"]] = (
                    "<EXASOL_ADMIN_PASSWORD>"
                )
            if "password" in config_params:
                self.sensitive_values[config_params["password"]] = "<DATABASE_PASSWORD>"

            # Extract IP addresses
            if "host_addrs" in config_params:
                self.sensitive_values[config_params["host_addrs"]] = "<PRIVATE_IP>"
            if "host_external_addrs" in config_params:
                self.sensitive_values[config_params["host_external_addrs"]] = (
                    "<PUBLIC_IP>"
                )
            if "host" in config_params:
                # Could be private or public, we'll determine by IP range
                self.sensitive_values[config_params["host"]] = "<SERVER_IP>"

        # Also extract from main config if systems have passwords defined
        for system_config in self.config.get("systems", []):
            setup = system_config.get("setup", {})
            if "password" in setup:
                self.sensitive_values[setup["password"]] = "<DATABASE_PASSWORD>"

    def _sanitize_for_report(self, value: Any) -> Any:
        """Sanitize sensitive information from any value before displaying in report."""
        import re

        if isinstance(value, str):
            # Replace specific sensitive values extracted from config
            sanitized = value
            for actual_value, placeholder in self.sensitive_values.items():
                if actual_value:  # Only replace non-empty values
                    sanitized = sanitized.replace(str(actual_value), placeholder)

            # Replace private IP addresses
            sanitized = re.sub(
                r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "<PRIVATE_IP>", sanitized
            )
            sanitized = re.sub(
                r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b",
                "<PRIVATE_IP>",
                sanitized,
            )
            sanitized = re.sub(
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b", "<PRIVATE_IP>", sanitized
            )

            # Replace public IP addresses (not localhost, not after = for version numbers)
            # Use negative lookbehind to avoid matching version numbers like clickhouse-server=25.9.2.1
            sanitized = re.sub(
                r"(?<![=:@])(?<![a-zA-Z0-9-])(?!127\.0\.0\.1\b)(?!localhost\b)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
                "<PUBLIC_IP>",
                sanitized,
            )

            return sanitized
        elif isinstance(value, dict):
            return {k: self._sanitize_for_report(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._sanitize_for_report(item) for item in value]
        else:
            return value

    def _rank_systems_by_performance(self, data: dict[str, Any]) -> list[str]:
        """
        Rank systems by performance (fastest first).

        Returns:
            List of system names ordered by median runtime (ascending)
        """
        if "summary" not in data or "per_system" not in data["summary"]:
            # Fallback: use order from config
            return [s["name"] for s in self.config.get("systems", [])]

        per_system = data["summary"]["per_system"]
        # Sort by median_runtime_ms ascending (fastest first)
        ranked = sorted(
            per_system.items(),
            key=lambda x: x[1].get("median_runtime_ms", float("inf")),
        )
        return [system_name for system_name, _stats in ranked]

    def _calculate_speedup_factor(
        self, data: dict[str, Any], fast_system: str, slow_system: str
    ) -> float:
        """Calculate speedup factor: slow_median / fast_median."""
        if "summary" not in data or "per_system" not in data["summary"]:
            return 1.0

        per_system = data["summary"]["per_system"]
        fast_median = float(
            per_system.get(fast_system, {}).get("median_runtime_ms", 1.0)
        )
        slow_median = float(
            per_system.get(slow_system, {}).get("median_runtime_ms", 1.0)
        )

        if fast_median == 0:
            return 1.0

        return slow_median / fast_median

    def _select_extreme_queries(
        self, data: dict[str, Any], winner: str, tested: list[str], limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Select queries with extreme performance differences.

        Returns queries where tested systems show largest differences from winner,
        plus some where they're competitive.
        """
        if "runs_df" not in data or data["runs_df"].empty:
            return []

        df = data["runs_df"]

        # Calculate median runtime per query per system
        query_medians = (
            df.groupby(["system", "query"])["elapsed_ms"]
            .median()
            .unstack(level="system", fill_value=0)
        )

        if winner not in query_medians.columns:
            return []

        extreme_queries = []
        queries_per_system = max(1, limit // len(tested)) if tested else 0
        worst_count = max(1, min(3, queries_per_system))
        best_count = max(1, min(2, queries_per_system))

        for tested_system in tested:
            if tested_system not in query_medians.columns:
                continue

            # Calculate slowdown ratio for each query
            winner_times = query_medians[winner]
            tested_times = query_medians[tested_system]

            # Only calculate where both have valid times
            valid_mask = (winner_times > 0) & (tested_times > 0)
            slowdown_ratios = tested_times[valid_mask] / winner_times[valid_mask]

            if len(slowdown_ratios) == 0:
                continue

            worst_queries = slowdown_ratios.nlargest(
                min(worst_count, len(slowdown_ratios))
            )
            best_queries = slowdown_ratios.nsmallest(
                min(best_count, len(slowdown_ratios))
            )

            for query_name in worst_queries.index:
                extreme_queries.append(
                    {
                        "query_name": query_name,
                        "winner": winner,
                        "winner_median": query_medians.loc[query_name, winner],
                        "tested_system": tested_system,
                        "tested_median": query_medians.loc[query_name, tested_system],
                        "speedup_factor": slowdown_ratios[query_name],
                        "category": "slowest",
                    }
                )

            for query_name in best_queries.index:
                extreme_queries.append(
                    {
                        "query_name": query_name,
                        "winner": winner,
                        "winner_median": query_medians.loc[query_name, winner],
                        "tested_system": tested_system,
                        "tested_median": query_medians.loc[query_name, tested_system],
                        "speedup_factor": slowdown_ratios[query_name],
                        "category": "competitive",
                    }
                )

        return extreme_queries

    def _filter_data_for_systems(
        self, data: dict[str, Any], system_names: list[str]
    ) -> dict[str, Any]:
        """Filter benchmark data to only include specified systems."""
        filtered = data.copy()

        # Filter runs DataFrame
        if "runs_df" in filtered and not filtered["runs_df"].empty:
            filtered["runs_df"] = filtered["runs_df"][
                filtered["runs_df"]["system"].isin(system_names)
            ]

        # Filter summary
        if "summary" in filtered and "per_system" in filtered["summary"]:
            filtered["summary"]["per_system"] = {
                k: v
                for k, v in filtered["summary"]["per_system"].items()
                if k in system_names
            }
            filtered["summary"]["systems"] = system_names

        return filtered

    def _filter_setup_for_systems(
        self, setup_summaries: dict[str, Any], system_names: list[str]
    ) -> dict[str, Any]:
        """Filter setup summaries to only include specified systems."""
        return {k: v for k, v in setup_summaries.items() if k in system_names}

    def _copy_attachments(
        self, post_dir: Path, system_names: list[str] | None = None
    ) -> None:
        """Copy all result files and figures as attachments.

        Args:
            post_dir: Directory to copy attachments to
            system_names: Optional list of system names to filter by. If None, copies all systems.
        """
        results_dir = Path("results") / self.project_id
        attachments_dir = post_dir / "attachments"

        # Clear attachments directory if it exists to remove stale files
        if attachments_dir.exists():
            shutil.rmtree(attachments_dir)
        ensure_directory(attachments_dir)

        # Copy and filter data files
        # For runs.csv and summary.json, filter by systems if system_names is provided
        if system_names is not None:
            # Filter and copy runs.csv
            runs_file = results_dir / "runs.csv"
            if runs_file.exists():
                runs_df = pd.read_csv(runs_file)
                filtered_runs = runs_df[runs_df["system"].isin(system_names)]
                filtered_runs.to_csv(attachments_dir / "runs.csv", index=False)

            # Filter and copy summary.json
            summary_file = results_dir / "summary.json"
            if summary_file.exists():
                summary = load_json(summary_file)
                if "per_system" in summary:
                    summary["per_system"] = {
                        k: v
                        for k, v in summary["per_system"].items()
                        if k in system_names
                    }
                summary["systems"] = system_names
                with open(attachments_dir / "summary.json", "w") as f:
                    json.dump(summary, f, indent=2)
        else:
            # Copy without filtering
            for filename in ["runs.csv", "summary.json"]:
                src_file = results_dir / filename
                if src_file.exists():
                    shutil.copy2(src_file, attachments_dir / filename)

        # Copy system.json and raw_results.json (not system-specific)
        for filename in ["system.json", "raw_results.json"]:
            src_file = results_dir / filename
            if src_file.exists():
                shutil.copy2(src_file, attachments_dir / filename)

        # Copy per-system probe outputs to preserve environment details
        system_probe_files = sorted(results_dir.glob("system_*.json"))
        for system_file in system_probe_files:
            system_name = system_file.stem.replace("system_", "")
            # Filter by system_names if provided
            if system_names is not None and system_name not in system_names:
                continue
            shutil.copy2(system_file, attachments_dir / system_file.name)

        # Create a consolidated system.json when only per-system probes exist
        system_json_src = results_dir / "system.json"
        system_json_dst = attachments_dir / "system.json"
        if not system_json_src.exists() and system_probe_files:
            combined_system_info: dict[str, Any] = {"systems": {}}
            for system_file in system_probe_files:
                system_name = system_file.stem.replace("system_", "")
                combined_system_info["systems"][system_name] = load_json(system_file)

            system_json_dst.write_text(json.dumps(combined_system_info, indent=2))

        # Copy setup summaries (setup_*.json files)
        setup_files = list(results_dir.glob("setup_*.json"))
        for setup_file in setup_files:
            system_name = setup_file.stem.replace("setup_", "")
            # Filter by system_names if provided
            if system_names is not None and system_name not in system_names:
                continue
            shutil.copy2(setup_file, attachments_dir / setup_file.name)

        # Copy figures
        figures_src = results_dir / "figures"
        if figures_src.exists():
            figures_dst = attachments_dir / "figures"
            shutil.copytree(figures_src, figures_dst, dirs_exist_ok=True)

        # Generate and save system-specific query files for clickable table functionality
        self._generate_query_files(attachments_dir, system_names=system_names)

        # Copy configuration file
        config_file = Path(f"configs/{self.project_id}.yaml")
        if config_file.exists():
            shutil.copy2(config_file, attachments_dir / "config.yaml")

    def _generate_workload_metadata(self) -> dict[str, Any]:
        """Generate workload metadata for report."""
        from ..systems import create_system
        from ..workloads import create_workload

        # Get workload configuration
        workload_config = self.config.get("workload", {})
        workload_name = workload_config.get("name")

        if not workload_name:
            return {"info": {}, "per_system_ddl": {}}

        # Instantiate the workload
        try:
            workload = create_workload(workload_config)
        except Exception as e:
            print(f"Warning: Failed to instantiate workload {workload_name}: {e}")
            return {"info": {}, "per_system_ddl": {}}

        # Get workload information
        workload_info = workload.get_workload_info()

        # Generate system-specific DDL and scripts
        per_system_ddl = {}
        for system_config in self.config.get("systems", []):
            system_name = system_config["name"]

            try:
                # Instantiate the system (minimal - just need kind and config)
                system = create_system(system_config)

                # Get rendered setup scripts for this system
                scripts = workload.get_rendered_setup_scripts(system)

                per_system_ddl[system_name] = {"scripts": scripts}

            except Exception as e:
                print(f"Warning: Failed to generate DDL for {system_name}: {e}")
                per_system_ddl[system_name] = {"scripts": {}}

        return {"info": workload_info, "per_system_ddl": per_system_ddl}

    def _generate_query_files(
        self, attachments_dir: Path, system_names: list[str] | None = None
    ) -> None:
        """Generate system-specific query files from templates."""
        from ..systems import create_system
        from ..workloads import create_workload

        # Get workload configuration
        workload_config = self.config.get("workload", {})
        workload_name = workload_config.get("name")

        if not workload_name:
            return

        # Instantiate the workload
        try:
            workload = create_workload(workload_config)
        except Exception as e:
            print(f"Warning: Failed to instantiate workload {workload_name}: {e}")
            return

        # Create queries directory
        queries_dir = attachments_dir / "queries"
        ensure_directory(queries_dir)

        # For each system, generate and save queries
        for system_config in self.config.get("systems", []):
            system_name = system_config["name"]

            if system_names and system_name not in system_names:
                continue

            try:
                # Instantiate the system (minimal - just need kind and config)
                system = create_system(system_config)

                # Get rendered queries for this system
                queries = workload.get_queries(system)

                # Create system-specific directory
                system_queries_dir = queries_dir / system_name
                ensure_directory(system_queries_dir)

                # Save each query
                for query_name, query_sql in queries.items():
                    query_file = system_queries_dir / f"{query_name}.sql"
                    query_file.write_text(query_sql, encoding="utf-8")

                print(f"Generated {len(queries)} queries for {system_name}")

            except Exception as e:
                print(f"Warning: Failed to generate queries for {system_name}: {e}")
                continue

    def _create_workload_package(self, post_dir: Path) -> None:
        """Create a workload package for reproduction."""
        try:
            # Reuse global package cache (create_workload_zip handles deduplication)
            zip_path = create_workload_zip(self.config)

            # Copy the cached package into the report directory
            final_zip = post_dir / f"{self.project_id}-workload.zip"
            shutil.copy2(zip_path, final_zip)
        except Exception as e:
            # If package creation fails, create a simple note
            note_file = post_dir / "workload-package-error.txt"
            note_file.write_text(f"Failed to create workload package: {e}")

    def _generate_short_report(self, report_base_dir: Path) -> Path | None:
        """Generate Report 1: Short comparing first two systems with installation details."""
        # Load benchmark data
        results_dir = Path("results") / self.project_id
        data = self._load_benchmark_data(results_dir)

        # Use config order (not performance ranking) to determine baseline and tested systems
        # Baseline is always the first system in config
        # Short report compares only first two systems for clarity
        config_systems = [s["name"] for s in self.config.get("systems", [])]
        if len(config_systems) < 2:
            print("Need at least 2 systems for short report generation")
            return None

        winner_system = config_systems[0]  # First system in config is baseline
        tested_systems = [config_systems[1]]  # Only the second system for short report

        summary: dict[str, Any] = cast(dict[str, Any], data.get("summary") or {})
        per_system: dict[str, Any] = cast(
            dict[str, Any], summary.get("per_system") or {}
        )
        if not per_system:
            print(
                "No per-system summary data available; skipping short report generation."
            )
            return None

        # Calculate speedup factors
        speedup_factor = self._calculate_speedup_factor(
            data, winner_system, tested_systems[0]
        )

        # Get winner statistics
        winner_stats = per_system.get(winner_system, {})
        winner_median = winner_stats.get("median_runtime_ms", 0)
        winner_avg = winner_stats.get("avg_runtime_ms", 0)
        winner_min = winner_stats.get("min_runtime_ms", 0)
        winner_max = winner_stats.get("max_runtime_ms", 0)

        # Select extreme queries
        extreme_queries = self._select_extreme_queries(
            data, winner_system, tested_systems, limit=10
        )

        # Filter data to tested systems only
        filtered_data = self._filter_data_for_systems(data, tested_systems)

        # Load system info and setup summaries (filtered to tested systems only)
        system_info = self._load_system_info(results_dir, system_names=tested_systems)
        setup_summaries = self._load_setup_summaries(
            results_dir, system_names=tested_systems
        )

        # Filter setup summaries to tested systems only (already filtered by load, but keep for clarity)
        filtered_setup = self._filter_setup_for_systems(setup_summaries, tested_systems)

        # Extract sensitive values
        self._extract_sensitive_values(filtered_setup)

        # Load preparation timings (filtered to tested systems only)
        preparation_timings = self._load_preparation_timings(
            results_dir, system_names=tested_systems
        )

        # Get tested system configs
        tested_system_configs = [
            s for s in self.config["systems"] if s["name"] in tested_systems
        ]

        # Generate workload metadata
        workload_metadata = self._generate_workload_metadata()

        # Prepare context
        context = {
            "cfg": self.config,
            "data": filtered_data,
            "system_info": system_info,
            "setup_summaries": filtered_setup,
            "preparation_timings": preparation_timings,
            "workload_metadata": workload_metadata,
            "winner_system_name": winner_system,
            "winner_median": winner_median,
            "winner_avg": winner_avg,
            "winner_min": winner_min,
            "winner_max": winner_max,
            "tested_systems": tested_system_configs,
            "tested_systems_names": tested_systems,
            "speedup_factor": speedup_factor,
            "extreme_queries": extreme_queries,
            "project_id": self.project_id,
        }

        # Create short report directory and attachments
        short_dir = report_base_dir / "1-short"
        ensure_directory(short_dir)
        attachments_dir = short_dir / "attachments"
        if attachments_dir.exists():
            shutil.rmtree(attachments_dir)
        ensure_directory(attachments_dir)

        # Prepare download artifacts limited to tested systems
        download_cards: list[dict[str, str]] = []

        runs_df = filtered_data.get("runs_df")
        if runs_df is not None and not runs_df.empty:
            runs_path = attachments_dir / "runs_tested.csv"
            runs_df.to_csv(runs_path, index=False)
            download_cards.append(
                {
                    "icon": "📊",
                    "title": "Query Results (Tested Systems)",
                    "description": "Raw benchmark results for tested systems (CSV format)",
                    "path": f"attachments/{runs_path.name}",
                }
            )

        filtered_summary = filtered_data.get("summary")
        if filtered_summary:
            summary_path = attachments_dir / "summary_tested.json"
            summary_path.write_text(json.dumps(filtered_summary, indent=2))
            download_cards.append(
                {
                    "icon": "📈",
                    "title": "Summary Statistics (Tested Systems)",
                    "description": "Aggregated performance metrics for tested systems (JSON)",
                    "path": f"attachments/{summary_path.name}",
                }
            )

        per_system_info = system_info.get("per_system", {}) if system_info else {}
        for system_name in tested_systems:
            system_display = self._format_display_name(system_name)
            system_file = results_dir / f"system_{system_name}.json"
            system_dest = attachments_dir / f"system_{system_name}.json"

            if system_file.exists():
                shutil.copy2(system_file, system_dest)
            elif isinstance(per_system_info, dict) and system_name in per_system_info:
                system_dest.write_text(
                    json.dumps(per_system_info[system_name], indent=2)
                )
            else:
                continue

            download_cards.append(
                {
                    "icon": "💻",
                    "title": f"{system_display} System Information",
                    "description": "Hardware specifications captured during the benchmark (JSON)",
                    "path": f"attachments/{system_dest.name}",
                }
            )

        # Package card placeholder (file created later)
        download_cards.append(
            {
                "icon": "📦",
                "title": "Benchmark Package",
                "description": "Self-contained reproduction package for tested systems",
                "path": f"{self.project_id}-workload.zip",
            }
        )

        context["download_cards"] = download_cards

        # Render Markdown
        template_md = self.jinja_env.get_template("short_report.md.j2")
        content_md = template_md.render(**context)
        with open(short_dir / "REPORT.md", "w", encoding="utf-8") as f:
            f.write(content_md)

        # Render HTML
        template_html = self.jinja_env.get_template("short_report.html.j2")
        content_html = template_html.render(**context)
        with open(short_dir / "REPORT.html", "w", encoding="utf-8") as f:
            f.write(content_html)

        # Copy CSS file
        css_src = Path("templates/styles.css.j2")
        if css_src.exists():
            css_dst = short_dir / "styles.css"
            css_template = self.jinja_env.get_template("styles.css.j2")
            css_content = css_template.render(**context)
            with open(css_dst, "w", encoding="utf-8") as f:
                f.write(css_content)

        # Copy setup summaries for tested systems
        for system_name in tested_systems:
            setup_file = results_dir / f"setup_{system_name}.json"
            if setup_file.exists():
                shutil.copy2(setup_file, attachments_dir / setup_file.name)

        # Copy configuration file
        config_file = Path(f"configs/{self.project_id}.yaml")
        if config_file.exists():
            shutil.copy2(config_file, attachments_dir / "config.yaml")

        # Copy query files for tested systems only
        self._generate_query_files(attachments_dir, system_names=tested_systems)

        print(f"✓ Generated short report: {short_dir}")

        return short_dir

    def _generate_results_report(self, report_base_dir: Path) -> Path:
        """Generate Report 2: Detailed results for all systems without installation."""
        # Extract system names from config to filter results
        system_names = [s["name"] for s in self.config.get("systems", [])]

        # Load benchmark data
        results_dir = Path("results") / self.project_id
        data = self._load_benchmark_data(results_dir)

        # Filter data to only include systems from config
        if system_names:
            data = self._filter_data_for_systems(data, system_names)

        # Generate figures
        figures_dir = Path(self.report_config["figures_dir"])
        relative_figures = {}
        if figures_dir.exists():
            for fig_file in figures_dir.glob("*.html"):
                fig_name = fig_file.stem
                relative_figures[fig_name] = f"attachments/figures/{fig_file.name}"

        # Generate tables
        tables = self._generate_tables(data)

        # Load system info (but no setup summaries - no installation) - filtered by system_names
        system_info = self._load_system_info(results_dir, system_names=system_names)

        # Generate workload metadata
        workload_metadata = self._generate_workload_metadata()

        # Prepare context
        context = {
            "cfg": self.config,
            "data": data,
            "figures": relative_figures,
            "tables": tables,
            "system_info": system_info,
            "workload_metadata": workload_metadata,
            "project_id": self.project_id,
        }

        # Create results directory
        results_report_dir = report_base_dir / "2-results"
        ensure_directory(results_report_dir)

        # Render Markdown
        template_md = self.jinja_env.get_template("results_report.md.j2")
        content_md = template_md.render(**context)
        with open(results_report_dir / "REPORT.md", "w", encoding="utf-8") as f:
            f.write(content_md)

        # Render HTML
        html_tables = self._generate_html_tables(data)
        context["tables"] = html_tables
        template_html = self.jinja_env.get_template("results_report.html.j2")
        content_html = template_html.render(**context)
        with open(results_report_dir / "REPORT.html", "w", encoding="utf-8") as f:
            f.write(content_html)

        # Copy CSS file
        css_src = Path("templates/styles.css.j2")
        if css_src.exists():
            css_dst = results_report_dir / "styles.css"
            css_template = self.jinja_env.get_template("styles.css.j2")
            css_content = css_template.render(**context)
            with open(css_dst, "w", encoding="utf-8") as f:
                f.write(css_content)

        # Copy attachments (figures only, no setup files)
        attachments_dir = results_report_dir / "attachments"
        ensure_directory(attachments_dir)

        # Copy figures
        if figures_dir.exists():
            figures_dest = attachments_dir / "figures"
            ensure_directory(figures_dest)
            for fig_file in figures_dir.glob("*"):
                shutil.copy(fig_file, figures_dest)

        # Copy query files for all systems
        self._generate_query_files(attachments_dir)

        print(f"✓ Generated results report: {results_report_dir}")

        return results_report_dir

    def _write_project_metadata(self, report_base_dir: Path) -> Path | None:
        """Collect and persist metadata describing this project's reports."""
        try:
            metadata = self._build_project_metadata(report_base_dir)
        except Exception as exc:
            print(f"Warning: Failed to build project metadata: {exc}")
            return None

        metadata_path = report_base_dir / "project_metadata.json"
        try:
            metadata_path.write_text(
                json.dumps(metadata, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            return metadata_path
        except Exception as exc:
            print(f"Warning: Failed to write project metadata: {exc}")
            return None

    def _build_project_metadata(self, report_base_dir: Path) -> dict[str, Any]:
        """Assemble metadata used for the global report index."""
        results_dir = Path("results") / self.project_id
        data = self._load_benchmark_data(results_dir)
        summary = data.get("summary", {}) or {}
        env_config = self.config.get("env", {}) or {}
        workload_config = self.config.get("workload", {}) or {}

        run_date = summary.get("run_date")
        last_updated_iso = self._coerce_timestamp(run_date)

        instances_config = env_config.get("instances") or {}
        default_instance_type = env_config.get("instance_type")

        systems_metadata: list[dict[str, Any]] = []
        tags: list[dict[str, str]] = []
        existing_slugs: set[str] = set()

        def add_tag(raw_value: str | None, label: str, category: str) -> None:
            if not raw_value:
                return
            slug = self._normalize_tag_value(str(raw_value))
            if not slug or slug in existing_slugs:
                return
            tags.append({"slug": slug, "label": label, "category": category})
            existing_slugs.add(slug)

        env_mode = env_config.get("mode")
        if env_mode:
            add_tag(env_mode, env_mode.upper(), "environment")

        region = env_config.get("region")
        if region:
            add_tag(region, region, "environment")

        workload_name = workload_config.get("name")
        workload_label = self._format_display_name(workload_name)
        if workload_name:
            add_tag(workload_name, workload_label, "workload")

        scale_factor = workload_config.get("scale_factor")
        if scale_factor is not None:
            sf_value = self._format_scale_factor_value(scale_factor)
            if sf_value:
                label = f"SF{sf_value}"
                add_tag(f"sf{sf_value}", label, "workload")

        # Add variant tags (global and per-system)
        variant_values: set[str] = set()
        configured_variant = workload_config.get("variant")
        normalized_variant = self._normalize_variant_value(configured_variant)
        if normalized_variant:
            variant_values.add(normalized_variant)

        system_variants = workload_config.get("system_variants") or {}
        for sys_variant in system_variants.values():
            normalized = self._normalize_variant_value(sys_variant)
            if normalized:
                variant_values.add(normalized)

        for variant_value in sorted(variant_values):
            variant_label = self._format_display_name(variant_value) or variant_value
            add_tag(
                f"variant-{variant_value}",
                f"{variant_label}",
                "variant",
            )

        for system_name, sys_variant in system_variants.items():
            system_key = (system_name or "").strip()
            if not system_key:
                continue
            variant_value = self._normalize_variant_value(sys_variant) or "official"
            variant_label = self._format_display_name(variant_value) or variant_value
            system_label = self._format_display_name(system_key) or system_key
            add_tag(
                f"{system_key}-{variant_value}",
                f"{variant_label}",
                "variant",
            )

        for system_config in self.config.get("systems", []):
            system_name = system_config.get("name", "")
            system_kind = system_config.get("kind", "")
            system_version = system_config.get("version")
            setup_config = system_config.get("setup", {}) or {}
            setup_method = setup_config.get("method")

            instance_details = (
                instances_config.get(system_name, {}) if instances_config else {}
            )
            instance_type = instance_details.get("instance_type", default_instance_type)

            systems_metadata.append(
                {
                    "name": system_name,
                    "kind": system_kind,
                    "version": system_version,
                    "setup_method": setup_method,
                    "instance_type": instance_type,
                    "extras": setup_config.get("extra", {}),
                }
            )

            add_tag(
                system_kind or system_name,
                self._format_display_name(system_kind or system_name),
                "system",
            )
            if setup_method:
                add_tag(
                    setup_method,
                    self._format_display_name(setup_method),
                    "installation",
                )
            if instance_type:
                add_tag(instance_type, str(instance_type), "instance")

        report_entries: list[dict[str, Any]] = []

        if report_base_dir.exists():
            for variant_dir in sorted(
                p for p in report_base_dir.iterdir() if p.is_dir()
            ):
                variant_slug = variant_dir.name
                variant_label = self._format_report_variant_name(variant_slug)

                html_file = variant_dir / "REPORT.html"
                if html_file.exists():
                    report_entries.append(
                        {
                            "variant": variant_slug,
                            "name": variant_label,
                            "format": "html",
                            "path": str(
                                html_file.relative_to(report_base_dir).as_posix()
                            ),
                        }
                    )

                markdown_file = variant_dir / "REPORT.md"
                if markdown_file.exists():
                    report_entries.append(
                        {
                            "variant": variant_slug,
                            "name": variant_label,
                            "format": "markdown",
                            "path": str(
                                markdown_file.relative_to(report_base_dir).as_posix()
                            ),
                        }
                    )

                for package_file in sorted(variant_dir.glob("*.zip")):
                    report_entries.append(
                        {
                            "variant": variant_slug,
                            "name": variant_label,
                            "format": "package",
                            "path": str(
                                package_file.relative_to(report_base_dir).as_posix()
                            ),
                        }
                    )

        queries_config = workload_config.get("queries", {}) or {}
        included_queries = queries_config.get("include") or []

        metadata: dict[str, Any] = {
            "project_id": self.project_id,
            "title": self.config.get("title") or self.project_id,
            "author": self.config.get("author"),
            "summary": summary,
            "last_updated": last_updated_iso,
            "report_base_dir": str(report_base_dir),
            "tags": sorted(tags, key=lambda tag: (tag["category"], tag["label"])),
            "systems": systems_metadata,
            "environment": {
                "mode": env_mode,
                "region": region,
                "instances": instances_config,
            },
            "workload": {
                "name": workload_name,
                "label": workload_label,
                "scale_factor": scale_factor,
                "runs_per_query": workload_config.get("runs_per_query"),
                "warmup_runs": workload_config.get("warmup_runs"),
                "queries": included_queries,
                "variant": workload_config.get("variant", "official"),
                "system_variants": workload_config.get("system_variants"),
            },
            "reports": report_entries,
        }

        return metadata

    def _render_report_index(self, index_dir: Path) -> None:
        """Render the global report index page."""
        index_file = render_global_report_index(index_dir)
        print(f"✓ Updated report index: {index_file}")

    def _coerce_timestamp(self, raw_timestamp: str | None) -> str:
        """Convert stored timestamps to ISO-8601 (UTC)."""
        if not raw_timestamp:
            return datetime.now(timezone.utc).isoformat()

        try:
            parsed = datetime.fromisoformat(raw_timestamp)
        except ValueError:
            return datetime.now(timezone.utc).isoformat()

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).isoformat()

    def _normalize_tag_value(self, value: str) -> str:
        """Normalize values used for tag-based filtering."""
        normalized = value.strip().lower()
        normalized = normalized.replace("#", "")
        normalized = "-".join(normalized.split())
        return normalized

    def _format_scale_factor_value(self, scale_factor: Any) -> str:
        """Return a compact string representation of the scale factor."""
        if scale_factor is None:
            return ""

        if isinstance(scale_factor, int):
            return str(scale_factor)

        if isinstance(scale_factor, float):
            if scale_factor.is_integer():
                return str(int(scale_factor))
            return str(scale_factor).rstrip("0").rstrip(".")

        # Attempt to normalise numeric strings using Decimal
        try:
            decimal_value = Decimal(str(scale_factor))
        except (InvalidOperation, ValueError):
            return str(scale_factor).strip()

        if decimal_value == decimal_value.to_integral():
            return str(int(decimal_value))

        normalized = format(decimal_value.normalize(), "f")
        return normalized.rstrip("0").rstrip(".") or normalized

    def _normalize_variant_value(self, variant: Any) -> str:
        """Normalize variant names, defaulting to 'official' when unset."""
        if variant is None:
            return "official"

        value = str(variant).strip()
        return value or "official"

    def _format_display_name(self, value: str | None) -> str:
        """Format identifiers for human-friendly display."""
        if not value:
            return ""

        canonical = value.strip()
        tokens = [
            tok for tok in canonical.replace("_", " ").replace("-", " ").split() if tok
        ]
        if not tokens:
            return canonical

        def _smart_case(token: str) -> str:
            if token.isupper():
                return token
            lower = token.lower()
            if lower.isalpha() and not any(ch in "aeiou" for ch in lower):
                return token.upper()
            if lower.isalpha():
                return token.capitalize()
            return token

        formatted = " ".join(_smart_case(tok) for tok in tokens)
        return formatted or canonical

    def _format_report_variant_name(self, variant_slug: str) -> str:
        """Generate a human friendly name from a report variant directory."""
        if not variant_slug:
            return "Report"

        slug = variant_slug.strip()
        if not slug:
            return "Report"

        # Remove numeric prefixes like "1-" if present
        parts = slug.split("-", 1)
        if len(parts) == 2 and parts[0].isdigit():
            base = parts[1]
        else:
            base = slug

        return self._format_display_name(base) or "Report"


def collect_all_project_metadata(index_dir: Path) -> list[dict[str, Any]]:
    """Load metadata for all projects discovered under the index directory."""
    metadata_files = sorted(index_dir.glob("**/project_metadata.json"))
    projects: list[dict[str, Any]] = []
    index_root = index_dir.resolve()

    for metadata_file in metadata_files:
        try:
            metadata = load_json(metadata_file)
        except Exception as exc:
            print(f"Warning: Failed to read metadata {metadata_file}: {exc}")
            continue

        base_dir = metadata_file.parent.resolve()
        rel_base = os.path.relpath(base_dir, index_root)
        rel_base_path = Path(rel_base)

        enriched_reports: list[dict[str, Any]] = []
        for report in metadata.get("reports", []):
            relative_path = report.get("path")
            if not relative_path:
                continue
            resolved = (rel_base_path / Path(relative_path)).as_posix()
            enriched_reports.append(
                {
                    **report,
                    "href": resolved,
                }
            )

        metadata["reports"] = enriched_reports
        metadata["relative_path"] = rel_base_path.as_posix()
        metadata["tag_slugs"] = [tag.get("slug") for tag in metadata.get("tags", [])]
        projects.append(metadata)

    projects.sort(key=lambda proj: (proj.get("title") or proj["project_id"]).lower())
    return projects


def render_global_report_index(
    index_dir: Path = Path("results"), template_dir: str = "templates"
) -> Path:
    """Render the standalone report index for all available projects."""
    ensure_directory(index_dir)
    projects = collect_all_project_metadata(index_dir)

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(enabled_extensions=("j2",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("report_index.html.j2")
    rendered = template.render(
        generated_at=datetime.now(timezone.utc).isoformat(),
        project_count=len(projects),
        projects_json=json.dumps(projects, ensure_ascii=True),
    )

    index_file = index_dir / "index.html"
    index_file.write_text(rendered, encoding="utf-8")
    return index_file


def render_report(config: dict[str, Any]) -> Path:
    """
    Main entry point for rendering benchmark reports.

    Args:
        config: Benchmark configuration

    Returns:
        Path to the generated report file
    """
    renderer = ReportRenderer(config)
    content = renderer.render_report()
    output_path = renderer.save_report(content)

    return output_path
