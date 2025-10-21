"""Figure generation for benchmark reports using Plotly."""

from itertools import cycle
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd
import plotly.express as px  # type: ignore[import-untyped]
import plotly.graph_objects as go  # type: ignore[import-untyped]
from plotly.subplots import make_subplots  # type: ignore[import-untyped]

# Modern tech-focused color palette for non-Exasol systems
TECH_COLORS = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#577590", "#7209B7"]
EXASOL_COLOR = "#2ECC71"  # Friendly green accent for Exasol visuals

# Plotly layout template for consistent styling
PLOTLY_TEMPLATE = {
    "font": {
        "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        "size": 12,
    },
    "title_font": {"size": 18, "color": "#1a1a1a"},
    "xaxis": {"showgrid": True, "gridcolor": "#f0f0f0", "zeroline": False},
    "yaxis": {"showgrid": True, "gridcolor": "#f0f0f0", "zeroline": False},
    "plot_bgcolor": "#ffffff",
    "paper_bgcolor": "#ffffff",
    "hovermode": "closest",
}


def _apply_template(fig: go.Figure, **custom_layout: Any) -> None:
    """Apply the Plotly template with custom layout options."""
    # Merge template with custom layout (custom layout takes precedence)
    layout = {**PLOTLY_TEMPLATE, **custom_layout}
    fig.update_layout(**layout)


def _build_system_color_map(systems: Sequence[str]) -> dict[str, str]:
    """Return consistent colors per system, ensuring Exasol uses green."""
    unique_norms: list[str] = []
    for system in systems:
        norm = system.strip().lower()
        if norm not in unique_norms:
            unique_norms.append(norm)

    palette = cycle(TECH_COLORS)
    color_map: dict[str, str] = {}
    for norm in unique_norms:
        if "exasol" in norm:
            color_map[norm] = EXASOL_COLOR
        else:
            color = next(palette)
            while color.lower() == EXASOL_COLOR.lower():
                color = next(palette)
            color_map[norm] = color
    return color_map


def _color_for_system(system: str, color_map: dict[str, str]) -> str:
    """Fetch the assigned color for a system, defaulting to palette head."""
    norm = system.strip().lower()
    return color_map.get(norm, TECH_COLORS[0])


def _format_system_label(system: str) -> str:
    """Pretty label for system names when shown in charts."""
    return system.replace("_", " ").title()


def create_performance_plots(
    df: pd.DataFrame, output_dir: Path, plot_type: str = "boxplot"
) -> str:
    """
    Create performance visualization plots using Plotly.

    Args:
        df: DataFrame with benchmark results
        output_dir: Directory to save plots
        plot_type: Type of plot to create

    Returns:
        Path to the created plot file (HTML for interactive, PNG for static)
    """
    if df.empty:
        return ""

    if plot_type == "boxplot":
        return _create_boxplot(df, output_dir)
    elif plot_type == "bar":
        return _create_bar_chart(df, output_dir)
    elif plot_type == "cdf":
        return _create_cdf_plot(df, output_dir)
    elif plot_type == "heatmap":
        return _create_heatmap(df, output_dir)
    elif plot_type == "speedup":
        return create_speedup_plot(df, df["system"].unique()[0], output_dir)
    elif plot_type == "overview":
        return create_system_overview_plot(df, output_dir)
    else:
        raise ValueError(f"Unknown plot type: {plot_type}")


def _save_png(
    fig: go.Figure, png_file: Path, width: int = 1200, height: int = 800
) -> None:
    """Save figure as PNG, skipping if kaleido/chrome unavailable."""
    try:
        fig.write_image(png_file, width=width, height=height)
    except Exception as e:
        # Silently skip PNG generation if kaleido/chrome fails
        # HTML version is still available and is interactive
        import warnings

        warnings.warn(f"Skipping PNG generation: {e}", stacklevel=2)


def _create_boxplot(df: pd.DataFrame, output_dir: Path) -> str:
    """Create interactive boxplot showing query runtime distributions."""
    fig = go.Figure()

    systems = df["system"].unique()
    color_map = _build_system_color_map(systems)

    # Create box plot for each system
    for system in systems:
        system_data = df[df["system"] == system]

        # Add trace for this system across all queries
        fig.add_trace(
            go.Box(
                x=[f"{row['query']}" for _, row in system_data.iterrows()],
                y=system_data["elapsed_ms"],
                name=_format_system_label(system),
                marker_color=_color_for_system(system, color_map),
                boxmean="sd",  # Show mean and standard deviation
            )
        )

    _apply_template(
        fig,
        title="Query Runtime Distribution by System",
        xaxis_title="Query",
        yaxis_title="Runtime (ms)",
        boxmode="group",
    )

    # Save as HTML (interactive)
    html_file = output_dir / "query_runtime_boxplot.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    # Save as PNG (static) - optional, skipped if kaleido/chrome unavailable
    png_file = output_dir / "query_runtime_boxplot.png"
    _save_png(fig, png_file, width=1200, height=800)

    return str(html_file)


def _create_bar_chart(df: pd.DataFrame, output_dir: Path) -> str:
    """Create interactive bar chart showing median query runtimes."""
    # Calculate median runtimes
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()

    systems = df["system"].unique()
    color_map = _build_system_color_map(systems)

    medians["system_label"] = medians["system"].apply(_format_system_label)
    color_discrete_map = {
        _format_system_label(system): _color_for_system(system, color_map)
        for system in systems
    }

    fig = px.bar(
        medians,
        x="query",
        y="elapsed_ms",
        color="system_label",
        barmode="group",
        labels={
            "elapsed_ms": "Median Runtime (ms)",
            "query": "Query",
            "system_label": "System",
        },
        title="Median Query Runtimes by System",
        color_discrete_map=color_discrete_map,
        category_orders={
            "system_label": [_format_system_label(system) for system in systems]
        },
    )

    _apply_template(fig)

    # Save as HTML and PNG
    html_file = output_dir / "median_runtime_bar.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "median_runtime_bar.png"
    _save_png(fig, png_file)

    return str(html_file)


def _create_cdf_plot(df: pd.DataFrame, output_dir: Path) -> str:
    """Create cumulative distribution function plot."""
    fig = go.Figure()

    systems = df["system"].unique()
    color_map = _build_system_color_map(systems)

    for system in systems:
        system_data = df[df["system"] == system]["elapsed_ms"].sort_values()
        n = len(system_data)
        y = np.arange(1, n + 1) / n

        fig.add_trace(
            go.Scatter(
                x=system_data,
                y=y,
                mode="lines",
                name=_format_system_label(system),
                line={"color": _color_for_system(system, color_map), "width": 2},
            )
        )

    _apply_template(
        fig,
        title="Cumulative Distribution of Query Runtimes",
        xaxis_title="Query Runtime (ms)",
        yaxis_title="Cumulative Probability",
    )

    html_file = output_dir / "query_runtime_cdf.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "query_runtime_cdf.png"
    _save_png(fig, png_file)

    return str(html_file)


def _create_heatmap(df: pd.DataFrame, output_dir: Path) -> str:
    """Create heatmap showing relative performance."""
    # Calculate median runtimes
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()
    # Swap pivot to make horizontal: systems on y-axis, queries on x-axis
    pivot_data = medians.pivot(index="system", columns="query", values="elapsed_ms")

    # Capitalize system names in index
    pivot_data.index = pivot_data.index.str.title()

    # Calculate relative performance (normalized by column minimum for horizontal layout)
    relative_data = pivot_data.div(pivot_data.min(axis=0), axis=1)

    fig = px.imshow(
        relative_data,
        labels={"x": "Query", "y": "System", "color": "Relative Performance"},
        x=relative_data.columns,
        y=relative_data.index,
        color_continuous_scale="RdYlGn_r",
        title="Relative Performance Heatmap (1.0 = fastest)",
        text_auto=".2f",
    )

    _apply_template(fig, height=400)

    html_file = output_dir / "performance_heatmap.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "performance_heatmap.png"
    _save_png(fig, png_file, width=1400, height=500)

    return str(html_file)


def create_speedup_plot(
    df: pd.DataFrame, baseline_system: str, output_dir: Path
) -> str:
    """Create speedup plot comparing systems to a baseline."""
    # Calculate medians for each system/query
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()
    pivot_data = medians.pivot(index="query", columns="system", values="elapsed_ms")

    if baseline_system not in pivot_data.columns:
        baseline_system = pivot_data.columns[0]

    fig = go.Figure()
    systems = list(pivot_data.columns)
    color_map = _build_system_color_map(systems)

    # Add speedup traces for each system
    for system in pivot_data.columns:
        if system == baseline_system:
            continue

        speedups = pivot_data[baseline_system] / pivot_data[system]

        fig.add_trace(
            go.Bar(
                x=pivot_data.index,
                y=speedups,
                name=f"{_format_system_label(system)} vs {_format_system_label(baseline_system)}",
                marker_color=_color_for_system(system, color_map),
                text=[f"{v:.2f}x" for v in speedups],
                textposition="outside",
            )
        )

    # Add horizontal line at 1.0 (no speedup)
    fig.add_hline(
        y=1.0, line_dash="dash", line_color="red", annotation_text="No speedup"
    )

    _apply_template(
        fig,
        title=f"Query Speedup Compared to {_format_system_label(baseline_system)}",
        xaxis_title="Query",
        yaxis_title="Speedup Factor",
        barmode="group",
    )

    html_file = output_dir / "speedup_comparison.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "speedup_comparison.png"
    _save_png(fig, png_file)

    return str(html_file)


def create_all_systems_comparison_plot(df: pd.DataFrame, output_dir: Path) -> str:
    """
    Create grouped bar chart showing all queries and all systems.
    Each system is displayed in a different color with a legend.
    This replaces the speedup plot for the full benchmark report.
    """
    # Calculate median runtimes for each system/query
    medians = df.groupby(["system", "query"])["elapsed_ms"].median().reset_index()

    fig = go.Figure()

    # Get unique systems and queries
    systems = medians["system"].unique()
    color_map = _build_system_color_map(systems)
    system_labels = {system: _format_system_label(system) for system in systems}
    queries = sorted(medians["query"].unique())

    # Add bar trace for each system
    for system in systems:
        system_data = medians[medians["system"] == system]

        # Create mapping of query to runtime
        query_runtimes = {
            row["query"]: row["elapsed_ms"] for _, row in system_data.iterrows()
        }

        # Ensure all queries are present (fill missing with None)
        y_values = [query_runtimes.get(q, None) for q in queries]

        fig.add_trace(
            go.Bar(
                x=queries,
                y=y_values,
                name=system_labels[system],
                marker_color=_color_for_system(system, color_map),
                text=[f"{v:.0f}ms" if v is not None else "" for v in y_values],
                textposition="outside",
                textangle=0,
            )
        )

    _apply_template(
        fig,
        title="Query Performance Comparison Across All Systems",
        xaxis_title="Query",
        yaxis_title="Median Runtime (ms)",
        barmode="group",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        height=500,
    )

    html_file = output_dir / "all_systems_comparison.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "all_systems_comparison.png"
    _save_png(fig, png_file, height=500)

    return str(html_file)


def create_system_overview_plot(df: pd.DataFrame, output_dir: Path) -> str:
    """Create overview plot showing overall system performance."""
    # Calculate overall statistics
    system_stats = (
        df.groupby("system")["elapsed_ms"]
        .agg(["count", "mean", "median", "std", "sum"])
        .reset_index()
    )

    systems = system_stats["system"].tolist()
    color_map = _build_system_color_map(systems)
    system_stats["system_label"] = system_stats["system"].apply(_format_system_label)
    colors_list = [
        _color_for_system(system, color_map) for system in system_stats["system"]
    ]

    # Create 1x3 subplot (removed "Number of Queries")
    fig = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=(
            "Total Runtime by System",
            "Average Query Runtime",
            "Runtime Variability (CV%)",
        ),
    )

    # 1. Total runtime
    fig.add_trace(
        go.Bar(
            x=system_stats["system_label"],
            y=system_stats["sum"],
            marker_color=colors_list,
            name="Total",
        ),
        row=1,
        col=1,
    )

    # 2. Average runtime
    fig.add_trace(
        go.Bar(
            x=system_stats["system_label"],
            y=system_stats["mean"],
            marker_color=colors_list,
            name="Average",
        ),
        row=1,
        col=2,
    )

    # 3. Coefficient of variation (moved to col 3)
    cv = (system_stats["std"] / system_stats["mean"]) * 100
    fig.add_trace(
        go.Bar(
            x=system_stats["system_label"], y=cv, marker_color=colors_list, name="CV"
        ),
        row=1,
        col=3,
    )

    fig.update_yaxes(title_text="Runtime (ms)", row=1, col=1)
    fig.update_yaxes(title_text="Runtime (ms)", row=1, col=2)
    fig.update_yaxes(title_text="CV (%)", row=1, col=3)

    _apply_template(
        fig,
        title_text="System Performance Overview",
        showlegend=False,
        height=500,
    )

    html_file = output_dir / "system_performance_overview.html"
    fig.write_html(html_file, include_plotlyjs="cdn")

    png_file = output_dir / "system_performance_overview.png"
    _save_png(fig, png_file, width=1400, height=900)

    return str(html_file)
