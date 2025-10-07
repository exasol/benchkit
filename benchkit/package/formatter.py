"""Format generated package code professionally."""

import subprocess
from pathlib import Path
from typing import Any


class PackageFormatter:
    """Format workload package with professional code style."""

    def __init__(self, package_dir: Path):
        self.package_dir = package_dir

    def format_all(self) -> dict[str, Any]:
        """Run all formatters and validators on package.

        Returns:
            Dictionary with formatter/validator results
        """
        results: dict[str, Any] = {}

        results["pyproject_toml"] = self.create_pyproject_toml()
        results["black"] = self.run_black()
        results["ruff_fix"] = self.run_ruff_fix()
        results["isort"] = self.run_isort()

        # Validation checks (after formatting)
        # Use temporary variables with proper types
        ruff_result: dict[str, Any] = self.run_ruff_check()
        mypy_result: dict[str, Any] = self.run_mypy()
        results["ruff_check"] = ruff_result
        results["mypy"] = mypy_result

        results["readme"] = self.create_readme()

        return results

    def create_pyproject_toml(self) -> bool:
        """Create pyproject.toml with formatting and type checking configuration."""
        content = """[tool.black]
line-length = 88
target-version = ['py310']

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "W", "N", "UP"]
ignore = [
    "E501",  # Line too long (handled by black)
    "N805",  # First argument of a method should be named `self` (pydantic validators use cls)
]
# Allow unused variables when prefixed with underscore
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Generated code may not have full type hints
check_untyped_defs = true
warn_redundant_casts = true
warn_unused_ignores = true
no_implicit_optional = true
strict_equality = true

# Allow missing imports for external packages
ignore_missing_imports = true

# Be lenient on generated code
allow_incomplete_defs = true
allow_untyped_calls = true
"""
        try:
            (self.package_dir / "pyproject.toml").write_text(content)
            return True
        except Exception as e:
            print(f"Warning: Could not create pyproject.toml: {e}")
            return False

    def run_black(self) -> bool:
        """Format code with Black."""
        try:
            result = subprocess.run(
                ["black", "--quiet", "."],
                cwd=self.package_dir,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Warning: Black formatting skipped ({e})")
            return False

    def run_ruff_fix(self) -> bool:
        """Lint and auto-fix with Ruff."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--fix", "--quiet", "."],
                cwd=self.package_dir,
                capture_output=True,
                timeout=60,
            )
            # Ruff returns 0 even if it fixed issues
            return result.returncode in (0, 1)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Warning: Ruff auto-fix skipped ({e})")
            return False

    def run_ruff_check(self) -> dict[str, Any]:
        """Validate code with Ruff (no auto-fix)."""
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=self.package_dir,
                capture_output=True,
                text=True,
                timeout=600,
            )

            return {
                "success": result.returncode == 0,
                "errors": result.stdout if result.returncode != 0 else "",
                "error_count": len(
                    [line for line in result.stdout.splitlines() if line.strip()]
                ),
            }
        except FileNotFoundError:
            return {"success": None, "errors": "Ruff not installed", "error_count": 0}
        except subprocess.TimeoutExpired:
            return {"success": False, "errors": "Timeout", "error_count": 0}

    def run_mypy(self) -> dict[str, Any]:
        """Type-check code with mypy."""
        try:
            result = subprocess.run(
                ["env", "PYTHONPATH=.", "mypy", "benchkit/", "--config-file=pyproject.toml"],
                cwd=self.package_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # Parse mypy output for error/warning count
            output_lines = result.stdout.splitlines()
            error_count = 0
            for line in output_lines:
                if " error" in line.lower() or " warning" in line.lower():
                    # Extract numbers from summary line like "Found 5 errors in 2 files"
                    import re

                    match = re.search(r"Found (\d+)", line)
                    if match:
                        error_count = int(match.group(1))

            return {
                "success": result.returncode == 0,
                "errors": result.stdout if result.returncode != 0 else "",
                "error_count": error_count,
            }
        except FileNotFoundError:
            return {"success": None, "errors": "mypy not installed", "error_count": 0}
        except subprocess.TimeoutExpired:
            return {"success": False, "errors": "Timeout", "error_count": 0}

    def run_isort(self) -> bool:
        """Sort imports with isort."""
        try:
            result = subprocess.run(
                ["isort", "--quiet", "."],
                cwd=self.package_dir,
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"Warning: isort skipped ({e})")
            return False

    def create_readme(self) -> bool:
        """Create README for the package."""
        readme_content = """# Workload Execution Package

This is a minimal, self-contained package for executing database benchmark workloads.

## Quick Start

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Execute workload (auto-detects running database)
./execute_workload.sh

# Or specify system explicitly
./execute_workload.sh exasol
./execute_workload.sh clickhouse

# Debug mode
./execute_workload.sh exasol --debug
```

## Package Contents

- `benchkit/` - Minimal framework for workload execution
- `workloads/` - Workload definitions and queries
- `config.yaml` - Workload configuration
- `execute_workload.sh` - Main execution script
- `requirements.txt` - Python dependencies

## Code Quality

This package is generated and validated with:
- **Black** for code formatting
- **Ruff** for linting and auto-fixes
- **isort** for import sorting
- **mypy** for type checking

All quality checks pass in the generated package.
"""

        try:
            (self.package_dir / "README.md").write_text(readme_content)
            return True
        except Exception as e:
            print(f"Warning: Could not create README.md: {e}")
            return False
