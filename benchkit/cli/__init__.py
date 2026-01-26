"""CLI package for benchkit.

This package provides the command-line interface for the benchmark framework.
The main app is in main.py, with functionality split across:
- probing.py: System probing for remote/managed systems
- status.py: Status display and reporting
- workflows.py: Multi-phase workflow helpers
"""

from .main import app

__all__ = ["app"]
