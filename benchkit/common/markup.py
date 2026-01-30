"""Rich markup utilities for text processing."""

import re

# Known Rich markup tags to strip. This is explicit to avoid stripping
# legitimate output prefixes like [exasol] or [clickhouse] which are task tags.
# See: https://rich.readthedocs.io/en/stable/markup.html
_RICH_TAGS = (
    # Style tags
    "bold",
    "b",
    "dim",
    "italic",
    "i",
    "underline",
    "u",
    "strike",
    "s",
    "blink",
    "reverse",
    "conceal",
    # Colors
    "red",
    "green",
    "blue",
    "yellow",
    "magenta",
    "cyan",
    "white",
    "black",
    "bright_red",
    "bright_green",
    "bright_blue",
    "bright_yellow",
    "bright_magenta",
    "bright_cyan",
    "bright_white",
    # Common Rich styles (but NOT status/error/warning which we use for our own tagging)
    "link",
    "repr",
    "rule",
)

# Build pattern: [tag], [/tag], [tag attr...] for known Rich tags only
_TAG_PATTERN = "|".join(re.escape(tag) for tag in _RICH_TAGS)
_MARKUP_PATTERN = re.compile(rf"\[/?(?:{_TAG_PATTERN})(?:\s+[^\]]+)?\]", re.IGNORECASE)


def strip_markup(text: str) -> str:
    """Remove Rich markup tags from text.

    Only strips known Rich markup tags, preserving legitimate output
    prefixes like [exasol] or [clickhouse] which are task identifiers.

    Args:
        text: Text possibly containing Rich markup like [bold], [red], etc.

    Returns:
        Clean text without Rich markup tags

    Examples:
        >>> strip_markup("[bold]Hello[/bold]")
        'Hello'
        >>> strip_markup("[red]Error:[/red] something failed")
        'Error: something failed'
        >>> strip_markup("[exasol] Query Q01 starting...")
        '[exasol] Query Q01 starting...'
    """
    return _MARKUP_PATTERN.sub("", text)
