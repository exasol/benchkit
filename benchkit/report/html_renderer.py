"""HTML rendering for benchmark reports."""

from pathlib import Path
from typing import Any

import pandas as pd
from jinja2 import Environment, FileSystemLoader


def _format_number(value: float, decimals: int = 1) -> str:
    """Format number for display."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def _format_duration(seconds: float) -> str:
    """Format duration in a human-readable way."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}m {secs:.1f}s"


def _sanitize(value: Any) -> Any:
    """Sanitize sensitive information (placeholder - actual sanitization done in renderer)."""
    # This is a passthrough filter - actual sanitization is handled by the renderer
    # which extracts sensitive values and replaces them before rendering
    return value


def render_html_report(
    context: dict[str, Any],
    template_dir: str = "templates",
    output_file: Path | None = None,
) -> str:
    """
    Render report as HTML using template.

    Args:
        context: Template context with all data
        template_dir: Directory containing templates
        output_file: Path to save HTML output

    Returns:
        Rendered HTML content
    """
    jinja_env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )

    jinja_env.filters["format_number"] = _format_number
    jinja_env.filters["format_duration"] = _format_duration
    jinja_env.filters["sanitize"] = _sanitize

    template = jinja_env.get_template("report.html.j2")
    html_content = template.render(**context)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    return html_content
