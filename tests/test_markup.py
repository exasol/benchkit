"""Tests for markup stripping utilities."""

from benchkit.common.markup import strip_markup


def test_strip_bold():
    """Test stripping bold markup."""
    assert strip_markup("[bold]Hello[/bold]") == "Hello"
    assert strip_markup("[b]text[/b]") == "text"


def test_strip_colors():
    """Test stripping color markup."""
    assert strip_markup("[red]Error[/red]") == "Error"
    assert strip_markup("[green]Success[/green]") == "Success"
    assert strip_markup("[blue]Info[/blue]") == "Info"
    assert strip_markup("[yellow]Warning[/yellow]") == "Warning"


def test_strip_dim():
    """Test stripping dim markup."""
    assert strip_markup("[dim]faded[/dim]") == "faded"


def test_preserve_task_tags():
    """Test that task identifiers are preserved."""
    # System names should NOT be stripped
    assert strip_markup("[exasol] Query starting") == "[exasol] Query starting"
    assert strip_markup("[clickhouse] Loading data") == "[clickhouse] Loading data"
    assert strip_markup("[postgres] Connected") == "[postgres] Connected"


def test_preserve_arbitrary_tags():
    """Test that non-Rich tags are preserved."""
    assert strip_markup("[status] Running") == "[status] Running"
    assert strip_markup("[stderr] error message") == "[stderr] error message"


def test_mixed_content():
    """Test mixed Rich markup and task tags."""
    text = "[exasol] [green]Success[/green]: Query completed"
    assert strip_markup(text) == "[exasol] Success: Query completed"


def test_nested_markup():
    """Test nested markup handling."""
    assert strip_markup("[bold][red]Important[/red][/bold]") == "Important"


def test_empty_string():
    """Test empty string handling."""
    assert strip_markup("") == ""


def test_no_markup():
    """Test string with no markup."""
    assert strip_markup("plain text here") == "plain text here"
