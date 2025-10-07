"""Table generation and formatting for reports."""

from typing import Any

import numpy as np
import pandas as pd
from tabulate import tabulate


def summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a summary table with basic statistics per system and query.

    Args:
        df: DataFrame with benchmark results

    Returns:
        DataFrame with summary statistics (sorted by query, then system)
    """
    if df.empty:
        return pd.DataFrame()

    # Group by query and system (query first for easier comparison)
    summary = (
        df.groupby(["query", "system"])["elapsed_ms"]
        .agg(["count", "median", "mean", "std", "min", "max"])
        .reset_index()
    )

    # Round numeric values
    numeric_columns = ["median", "mean", "std", "min", "max"]
    summary[numeric_columns] = summary[numeric_columns].round(1)

    # Rename columns for better presentation
    summary = summary.rename(
        columns={
            "count": "runs",
            "median": "median_ms",
            "mean": "mean_ms",
            "std": "std_ms",
            "min": "min_ms",
            "max": "max_ms",
        }
    )

    # Sort by query first (natural sort for Q01, Q02, etc.), then system
    # This ensures queries are grouped together for easy comparison
    summary = summary.sort_values(["query", "system"])

    return summary


def create_comparison_table(
    df: pd.DataFrame, baseline_system: str | None = None
) -> pd.DataFrame:
    """
    Create a comparison table showing relative performance between systems.

    Args:
        df: DataFrame with benchmark results
        baseline_system: System to use as baseline (defaults to first system)

    Returns:
        DataFrame with comparison metrics
    """
    if df.empty:
        return pd.DataFrame()

    systems = df["system"].unique()
    if len(systems) < 2:
        return pd.DataFrame()

    if baseline_system is None:
        baseline_system = systems[0]

    if baseline_system not in systems:
        baseline_system = systems[0]

    # Calculate median performance for each system/query combination
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()
    medians_pivot = medians.pivot(index="query", columns="system", values="elapsed_ms")

    # Calculate relative performance compared to baseline
    comparison_data: list[dict[str, Any]] = []
    baseline_values = medians_pivot[baseline_system]

    for system in systems:
        if system == baseline_system:
            continue

        system_values = medians_pivot[system]

        for query in medians_pivot.index:
            if pd.notna(baseline_values[query]) and pd.notna(system_values[query]):
                ratio = system_values[query] / baseline_values[query]
                speedup = baseline_values[query] / system_values[query]

                comparison_data.append(
                    {
                        "query": query,
                        "baseline_system": baseline_system,
                        "comparison_system": system,
                        "baseline_ms": round(baseline_values[query], 1),
                        "comparison_ms": round(system_values[query], 1),
                        "ratio": round(ratio, 2),
                        "speedup": round(speedup, 2),
                        "faster": speedup > 1.0,
                    }
                )

    return pd.DataFrame(comparison_data)


def create_ranking_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a ranking table showing which system performs best for each query.

    Args:
        df: DataFrame with benchmark results

    Returns:
        DataFrame with rankings
    """
    if df.empty:
        return pd.DataFrame()

    # Calculate median performance for ranking
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()

    ranking_data = []
    for query in medians["query"].unique():
        query_data = medians[medians["query"] == query].copy()
        query_data = query_data.sort_values("elapsed_ms")

        for rank, (_, row) in enumerate(query_data.iterrows(), 1):
            fastest_time = query_data.iloc[0]["elapsed_ms"]
            slowdown = row["elapsed_ms"] / fastest_time

            ranking_data.append(
                {
                    "query": query,
                    "rank": rank,
                    "system": row["system"],
                    "time_ms": round(row["elapsed_ms"], 1),
                    "slowdown": round(slowdown, 2),
                }
            )

    return pd.DataFrame(ranking_data)


def create_aggregated_performance_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create an aggregated performance table across all queries.

    Args:
        df: DataFrame with benchmark results

    Returns:
        DataFrame with aggregated metrics
    """
    if df.empty:
        return pd.DataFrame()

    agg_data = []
    for system in df["system"].unique():
        system_df = df[df["system"] == system]

        # Calculate various aggregated metrics
        total_time = system_df["elapsed_ms"].sum()
        avg_time = system_df["elapsed_ms"].mean()
        median_time = system_df["elapsed_ms"].median()
        n_queries = len(system_df)
        geomean_time = (
            system_df["elapsed_ms"].apply(lambda x, n=n_queries: x ** (1 / n)).prod()
        )

        agg_data.append(
            {
                "system": system,
                "total_queries": len(system_df),
                "total_time_ms": round(total_time, 1),
                "avg_time_ms": round(avg_time, 1),
                "median_time_ms": round(median_time, 1),
                "geomean_time_ms": round(geomean_time, 1),
                "fastest_query_ms": round(system_df["elapsed_ms"].min(), 1),
                "slowest_query_ms": round(system_df["elapsed_ms"].max(), 1),
            }
        )

    result_df = pd.DataFrame(agg_data)

    # Add ranking based on geometric mean
    result_df["rank"] = result_df["geomean_time_ms"].rank().astype(int)
    result_df = result_df.sort_values("rank")

    return result_df


def format_table_markdown(df: pd.DataFrame, table_format: str = "github") -> str:
    """
    Format a DataFrame as a markdown table.

    Args:
        df: DataFrame to format
        table_format: Table format for tabulate (github, pipe, etc.)

    Returns:
        Markdown table string
    """
    if df.empty:
        return "*No data available*"

    return tabulate(df.values, headers=df.columns.tolist(), tablefmt=table_format)


def get_performance_category(
    value: float, values_list: list[float], lower_is_better: bool = True
) -> str:
    """
    Categorize performance value into excellent/good/average/poor.

    Args:
        value: Value to categorize
        values_list: List of all values for comparison
        lower_is_better: Whether lower values are better

    Returns:
        CSS class name: 'perf-excellent', 'perf-good', 'perf-average', 'perf-poor'
    """
    if not values_list or pd.isna(value):
        return ""

    # Calculate percentiles
    p25 = np.percentile(values_list, 25)
    p50 = np.percentile(values_list, 50)
    p75 = np.percentile(values_list, 75)

    if lower_is_better:
        # Lower is better (e.g., execution time)
        if value <= p25:
            return "perf-excellent"
        elif value <= p50:
            return "perf-good"
        elif value <= p75:
            return "perf-average"
        else:
            return "perf-poor"
    else:
        # Higher is better (e.g., throughput, speedup)
        if value >= p75:
            return "perf-excellent"
        elif value >= p50:
            return "perf-good"
        elif value >= p25:
            return "perf-average"
        else:
            return "perf-poor"


def format_table_html_with_colors(
    df: pd.DataFrame,
    color_columns: dict[str, bool] | None = None,
    table_id: str | None = None,
    css_classes: str | None = None,
) -> str:
    """
    Format a DataFrame as an HTML table with performance-based color coding.

    Args:
        df: DataFrame to format
        color_columns: Dict mapping column names to lower_is_better flag
                      (e.g., {'time_ms': True, 'speedup': False})
        table_id: HTML table ID
        css_classes: CSS classes to apply to table

    Returns:
        HTML table string with color-coded cells
    """
    if df.empty:
        return "<p><em>No data available</em></p>"

    if color_columns is None:
        color_columns = {}

    # Build HTML manually for better control over cell styling
    table_classes = f'class="{css_classes}"' if css_classes else ""
    table_id_attr = f'id="{table_id}"' if table_id else ""
    html_parts = [f"<table {table_id_attr} {table_classes}>"]

    # Header
    html_parts.append("<thead><tr>")
    for col in df.columns:
        html_parts.append(f"<th>{col}</th>")
    html_parts.append("</tr></thead>")

    # Body
    html_parts.append("<tbody>")
    prev_query = None
    query_group_num = 0
    for _idx, row in df.iterrows():
        # Track query groups for alternating backgrounds (if query column exists)
        row_attrs = []
        if "query" in df.columns:
            current_query = row["query"]
            if current_query != prev_query:
                query_group_num += 1
                row_attrs.append('data-query-start="true"')
                prev_query = current_query

            # Add query group for alternating backgrounds
            query_group = "odd" if query_group_num % 2 == 1 else "even"
            row_attrs.append(f'data-query-group="{query_group}"')

            # Add query and system data for JavaScript to use
            row_attrs.append(f'data-query="{current_query}"')
            if "system" in df.columns:
                row_attrs.append(f'data-system="{row["system"]}"')

        # Build tr tag with attributes
        tr_attrs = " ".join(row_attrs)
        html_parts.append(f"<tr {tr_attrs}>")

        for col in df.columns:
            value = row[col]
            cell_class = ""

            # Apply color coding if specified
            if col in color_columns and pd.api.types.is_numeric_dtype(df[col]):
                values_list = df[col].dropna().tolist()
                lower_is_better = color_columns[col]
                cell_class = get_performance_category(
                    value, values_list, lower_is_better
                )

            class_attr = f' class="{cell_class}"' if cell_class else ""

            # Format value
            if pd.isna(value):
                formatted_value = ""
            elif isinstance(value, int | float | np.number):
                formatted_value = (
                    f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
                )
            else:
                formatted_value = str(value)

            html_parts.append(f"<td{class_attr}>{formatted_value}</td>")
        html_parts.append("</tr>")
    html_parts.append("</tbody>")

    html_parts.append("</table>")
    return "\n".join(html_parts)


def create_comparison_table_html(
    df: pd.DataFrame, baseline_system: str | None = None
) -> str:
    """
    Create an HTML comparison table with color-coded performance metrics.

    Args:
        df: DataFrame with benchmark results
        baseline_system: System to use as baseline

    Returns:
        HTML table string with color coding
    """
    comparison_df = create_comparison_table(df, baseline_system)

    if comparison_df.empty:
        return "<p><em>No comparison data available</em></p>"

    # Define which columns should be color-coded
    color_columns = {
        "baseline_ms": True,  # Lower is better
        "comparison_ms": True,  # Lower is better
        "speedup": False,  # Higher is better
    }

    return format_table_html_with_colors(
        comparison_df,
        color_columns=color_columns,
        css_classes="comparison-table",
    )


def create_ranking_table_html(df: pd.DataFrame) -> str:
    """
    Create an HTML ranking table with color-coded performance metrics.

    Args:
        df: DataFrame with benchmark results

    Returns:
        HTML table string with color coding
    """
    ranking_df = create_ranking_table(df)

    if ranking_df.empty:
        return "<p><em>No ranking data available</em></p>"

    # Define which columns should be color-coded
    color_columns = {
        "rank": True,  # Lower is better
        "time_ms": True,  # Lower is better
        "slowdown": True,  # Lower is better
    }

    return format_table_html_with_colors(
        ranking_df,
        color_columns=color_columns,
        css_classes="ranking-table",
    )


def create_aggregated_performance_table_html(df: pd.DataFrame) -> str:
    """
    Create an HTML aggregated performance table with color-coded metrics.

    Args:
        df: DataFrame with benchmark results

    Returns:
        HTML table string with color coding
    """
    agg_df = create_aggregated_performance_table(df)

    if agg_df.empty:
        return "<p><em>No aggregated data available</em></p>"

    # Define which columns should be color-coded
    color_columns = {
        "total_time_ms": True,  # Lower is better
        "avg_time_ms": True,  # Lower is better
        "median_time_ms": True,  # Lower is better
        "geomean_time_ms": True,  # Lower is better
        "fastest_query_ms": True,  # Lower is better
        "slowest_query_ms": True,  # Lower is better
        "rank": True,  # Lower is better
    }

    return format_table_html_with_colors(
        agg_df,
        color_columns=color_columns,
        css_classes="aggregated-table",
    )


def create_summary_table_html(df: pd.DataFrame) -> str:
    """
    Create an HTML summary table with color-coded performance metrics.

    Args:
        df: DataFrame with benchmark results

    Returns:
        HTML table string with color coding
    """
    summary_df = summary_table(df)

    if summary_df.empty:
        return "<p><em>No summary data available</em></p>"

    # Define which columns should be color-coded
    color_columns = {
        "median_ms": True,  # Lower is better
        "mean_ms": True,  # Lower is better
        "std_ms": True,  # Lower is better
        "min_ms": True,  # Lower is better
        "max_ms": True,  # Lower is better
    }

    return format_table_html_with_colors(
        summary_df,
        color_columns=color_columns,
        css_classes="summary-table",
    )
