"""Report generation modules."""

from .figures import create_performance_plots
from .render import ReportRenderer, render_report
from .tables import create_comparison_table, format_table_markdown, summary_table

__all__ = [
    "render_report",
    "ReportRenderer",
    "summary_table",
    "create_comparison_table",
    "format_table_markdown",
    "create_performance_plots",
]
