"""Tests for import cleaner - handles TYPE_CHECKING blocks and unused imports."""

from benchkit.package.import_cleaner import ImportCleaner


def test_empty_type_checking_block_removed():
    """Test that empty TYPE_CHECKING blocks are removed entirely."""
    code = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foo import Bar

def hello():
    pass
"""
    cleaner = ImportCleaner()
    cleaned = cleaner._clean_source(code)

    # TYPE_CHECKING block and import should be gone
    assert "TYPE_CHECKING" not in cleaned
    assert "from foo import Bar" not in cleaned
    # Function should remain
    assert "def hello" in cleaned


def test_type_checking_with_used_import_preserved():
    """Test that TYPE_CHECKING blocks with used imports are kept."""
    code = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foo import Bar

def hello(x: Bar) -> None:
    pass
"""
    cleaner = ImportCleaner()
    cleaned = cleaner._clean_source(code)

    # TYPE_CHECKING block should remain since Bar is used in type hint
    assert "TYPE_CHECKING" in cleaned
    assert "from foo import Bar" in cleaned
    assert "def hello" in cleaned


def test_partial_type_checking_cleanup():
    """Test that only unused imports in TYPE_CHECKING are removed."""
    code = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from foo import Used, Unused

def hello(x: Used) -> None:
    pass
"""
    cleaner = ImportCleaner()
    cleaned = cleaner._clean_source(code)

    # TYPE_CHECKING block should remain with Used, but Unused removed
    assert "TYPE_CHECKING" in cleaned
    assert "Used" in cleaned
    assert "Unused" not in cleaned


def test_regular_unused_imports_removed():
    """Test that regular unused imports are still removed."""
    code = """
import os
import sys

def hello():
    return sys.version
"""
    cleaner = ImportCleaner()
    cleaned = cleaner._clean_source(code)

    # os is unused, sys is used
    assert "import os" not in cleaned
    assert "sys" in cleaned


def test_cascading_cleanup():
    """Test that multi-pass cleanup works for cascading removals."""
    code = """
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from foo import Bar

def hello():
    pass
"""
    cleaner = ImportCleaner()
    cleaned = cleaner._clean_source(code)

    # TYPE_CHECKING is unused after block removal
    assert "TYPE_CHECKING" not in cleaned
    # Optional is also unused
    assert "Optional" not in cleaned
    assert "def hello" in cleaned
