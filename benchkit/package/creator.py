"""Create portable benchmark packages."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Literal, cast

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from ..systems.base import SystemUnderTest
from ..util import ensure_directory
from .code_minimizer import CodeMinimizer
from .formatter import PackageFormatter
from .import_cleaner import ImportCleaner

console = Console()


def create_workload_zip(
    config: dict[str, Any], output_dir: Path | None = None, force: bool = False
) -> Path:
    """
    Create a minimal workload package containing only execution components.

    Args:
        config: Benchmark configuration
        output_dir: Directory to create package in
        force: If True, recreate even if exists

    Returns:
        Path to created ZIP file
    """
    package = WorkloadPackage(config, output_dir)

    if not force and package.can_reuse_existing_package():
        console.print(f"[dim]Package already exists, reusing: {package.zip_path}[/]")
        return package.zip_path

    if force:
        console.print("[dim]Force flag detected, rebuilding workload package[/]")
    else:
        reason_map = {
            "zip_missing": "no cached package found",
            "metadata_missing": "metadata missing",
            "config_changed": "configuration changed",
        }
        reason_key = package.reuse_reason or "cache invalidated"
        reason_text = reason_map.get(reason_key, reason_key.replace("_", " "))
        console.print(f"[yellow]Rebuilding workload package ({reason_text}).[/yellow]")

    package.invalidate_cached_package()
    package.create_package()
    zip_path = package.create_zip_package()
    package.write_metadata()
    return zip_path


class WorkloadPackage:
    """Creates package containing only workload execution components."""

    def __init__(self, config: dict[str, Any], package_dir: Path | None = None):
        self.config = config
        self.project_id = config["project_id"]
        self.package_dir = (
            package_dir or Path("packages") / f"{self.project_id}_workload"
        )
        self.metadata_file = self.package_dir / ".package_meta.json"
        self._config_hash = self._compute_config_hash()
        self._reuse_reason: Literal[
            "zip_missing", "metadata_missing", "config_changed", ""
        ] = ""
        self._jinja_env: Environment | None = None

    def _get_jinja_env(self) -> Environment:
        """Get or create Jinja2 environment for package templates."""
        if self._jinja_env is None:
            self._jinja_env = Environment(
                loader=FileSystemLoader("templates/package"),
                keep_trailing_newline=True,
            )
        return self._jinja_env

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context.

        Args:
            template_name: Name of template file (e.g., 'phase_script.sh.j2')
            context: Dictionary of variables to pass to the template

        Returns:
            Rendered template content
        """
        env = self._get_jinja_env()
        template = env.get_template(template_name)
        return template.render(**context)

    @property
    def zip_path(self) -> Path:
        """Location of the cached workload ZIP."""
        return self.package_dir.with_suffix(".zip")

    @property
    def reuse_reason(self) -> str:
        """Reason the cached package could not be reused (empty string if reusable)."""
        return self._reuse_reason

    def can_reuse_existing_package(self) -> bool:
        """Determine whether an existing package matches the current config."""
        self._reuse_reason = ""

        if not self.zip_path.exists():
            self._reuse_reason = "zip_missing"
            return False

        metadata = self._load_metadata()
        if metadata is None:
            self._reuse_reason = "metadata_missing"
            return False

        cached_hash = metadata.get("config_hash")
        if cached_hash != self._config_hash:
            self._reuse_reason = "config_changed"
            return False

        return True

    def invalidate_cached_package(self) -> None:
        """Remove cached package artifacts so a fresh build can proceed."""
        if self.zip_path.exists():
            try:
                self.zip_path.unlink()
            except OSError as exc:
                console.print(
                    f"[yellow]Warning: Could not remove {self.zip_path}: {exc}[/yellow]"
                )

        if self.metadata_file.exists():
            try:
                self.metadata_file.unlink()
            except OSError as exc:
                console.print(
                    f"[yellow]Warning: Could not remove {self.metadata_file}: {exc}[/yellow]"
                )

    def create_package(self) -> Path:
        """Create a minimal workload package with only execution files."""
        if self.package_dir.exists():
            shutil.rmtree(self.package_dir)

        ensure_directory(self.package_dir)

        console.print("[blue]Creating workload package...[/]")

        # Copy minimal framework files (execution only)
        self._copy_minimal_framework_files()

        # Copy workload configuration
        self._copy_workload_config()

        # Copy workload files
        self._copy_workload_files()

        # Copy minimal system files (drivers only)
        self._copy_minimal_system_files()

        # Create workload runner script
        self._create_workload_runner_script()

        # Create minimal requirements file
        self._create_minimal_requirements_file()

        # Create workload CLI
        self._create_workload_cli()

        # Minimize code (remove excluded methods)
        console.print("[blue]Minimizing package code...[/]")
        minimizer = CodeMinimizer(self.package_dir)
        stats = minimizer.minimize_all()
        console.print(
            f"[green]✂️  Removed {stats['methods_removed']} methods and "
            f"{stats['functions_removed']} functions[/]"
        )
        console.print(
            f"[green]📉 Reduced from {stats['lines_before']} → "
            f"{stats['lines_after']} lines "
            f"({stats['files_processed']} files)[/]"
        )

        # Clean unused imports
        console.print("[blue]Cleaning unused imports...[/]")
        cleaner = ImportCleaner()
        for py_file in self.package_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                cleaned = cleaner.clean_file(py_file)
                py_file.write_text(cleaned)
        console.print("[green]✓ Imports cleaned[/]")

        # Format package
        console.print("[blue]Formatting and validating package code...[/]")
        formatter = PackageFormatter(self.package_dir)
        format_results = formatter.format_all()

        # Report formatting
        formatters_used = []
        if format_results.get("black"):
            formatters_used.append("Black")
        if format_results.get("ruff_fix"):
            formatters_used.append("Ruff")
        if format_results.get("isort"):
            formatters_used.append("isort")

        if formatters_used:
            console.print(f"[green]✨ Formatted with {', '.join(formatters_used)}[/]")
        else:
            console.print(
                "[yellow]⚠ Formatting tools not available (install black, ruff, isort)[/]"
            )

        # Report validation results
        console.print("[blue]Running quality checks...[/]")

        # Ruff validation
        ruff_check_raw: Any = format_results.get("ruff_check", {})
        ruff_check: dict[str, Any] = (
            ruff_check_raw if isinstance(ruff_check_raw, dict) else {}
        )
        if isinstance(ruff_check, dict):
            if ruff_check.get("success"):
                console.print("[green]✓ Ruff: No linting issues[/]")
            elif ruff_check.get("success") is None:
                console.print("[yellow]⚠ Ruff: Not installed[/]")
            else:
                error_count = ruff_check.get("error_count", 0)
                console.print(f"[yellow]⚠ Ruff: {error_count} issues found[/]")
                if error_count > 0 and error_count <= 10:
                    console.print(f"[dim]{ruff_check.get('errors', '')}[/]")

        # Mypy validation
        mypy_check_raw: Any = format_results.get("mypy", {})
        mypy_check: dict[str, Any] = (
            mypy_check_raw if isinstance(mypy_check_raw, dict) else {}
        )
        if isinstance(mypy_check, dict):
            if mypy_check.get("success"):
                console.print("[green]✓ mypy: Type checking passed[/]")
            elif mypy_check.get("success") is None:
                console.print("[yellow]⚠ mypy: Not installed[/]")
            else:
                error_count = mypy_check.get("error_count", 0)
                console.print(f"[yellow]⚠ mypy: {error_count} type issues found[/]")
                if error_count > 0 and error_count <= 10:
                    console.print(f"[dim]{mypy_check.get('errors', '')}[/]")

        self._clean_cache_artifacts()

        console.print("[green]✓ Package created successfully[/]")

        return self.package_dir

    def _clean_cache_artifacts(self) -> None:
        """Remove cache directories created by formatters/validators."""
        import shutil

        cache_patterns = [
            ".mypy_cache",
            "__pycache__",
            ".ruff_cache",
            ".pytest_cache",
            "*.pyc",
            "*.pyo",
        ]

        for pattern in cache_patterns:
            if "*" in pattern:
                # Handle file patterns
                for cache_file in self.package_dir.rglob(pattern):
                    cache_file.unlink()
            else:
                # Handle directory patterns
                for cache_dir in self.package_dir.rglob(pattern):
                    if cache_dir.is_dir():
                        shutil.rmtree(cache_dir)

        console.print(
            "[dim]Cleaned cache artifacts (.mypy_cache, __pycache__, etc.)[/]"
        )

    def create_zip_package(self) -> Path:
        """Create a ZIP file of the minimal workload package."""
        with zipfile.ZipFile(self.zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.package_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.package_dir)
                    zipf.write(file_path, arcname)

        return self.zip_path

    def write_metadata(self) -> None:
        """Persist metadata about the cached package for reuse checks."""
        ensure_directory(self.package_dir)
        metadata = {"config_hash": self._config_hash}
        self.metadata_file.write_text(json.dumps(metadata, indent=2))

    def _load_metadata(self) -> dict[str, Any] | None:
        """Load metadata describing an existing package."""
        if not self.metadata_file.exists():
            return None

        try:
            raw = self.metadata_file.read_text()
            return cast("dict[str, Any]", json.loads(raw))
        except Exception:
            return None

    def _compute_config_hash(self) -> str:
        """Compute a stable hash of the configuration for cache invalidation."""
        normalized = json.dumps(self.config, sort_keys=True, default=self._json_default)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _json_default(value: Any) -> Any:
        """Fallback serializer for JSON-dumping configuration structures."""
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, set):
            return sorted(value)
        return str(value)

    def _copy_minimal_framework_files(self) -> None:
        """Copy only essential framework files for workload execution."""
        # Core files needed for execution
        core_files = [
            "benchkit/__init__.py",
            "benchkit/config.py",
            "benchkit/util.py",
            "benchkit/debug.py",  # Include debug utilities
        ]

        for file_path in core_files:
            src = Path(file_path)
            if src.exists():
                dst = self.package_dir / file_path
                ensure_directory(dst.parent)
                shutil.copy2(src, dst)

        # Copy only workload execution modules (no setup, infra, package, report)
        workload_modules = {
            "run": [
                "parsers.py"
            ],  # Only parsers, no __init__.py to avoid import issues
            "package": [
                "markers.py",  # imported by systems/base
            ],
            "systems": None,  # Copy all - needed for database connections
            "workloads": None,  # Copy all - needed for workload execution
            "common": None,
        }

        for module, files in workload_modules.items():
            src_dir = Path("benchkit") / module
            dst_dir = self.package_dir / "benchkit" / module

            if not src_dir.exists():
                continue

            ensure_directory(dst_dir)

            if files is None:
                # Copy entire module
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            else:
                # Copy only specific files
                for filename in files:
                    src_file = src_dir / filename
                    if src_file.exists():
                        shutil.copy2(src_file, dst_dir / filename)

                # Create minimal __init__.py for run module
                if module == "run":
                    init_file = dst_dir / "__init__.py"
                    init_file.write_text(
                        '"""Minimal run module for workload execution."""\n'
                    )

    def _copy_workload_config(self) -> None:
        """Copy configuration modified for workload execution only."""
        import yaml

        # Create workload-only configuration
        workload_config = {
            "project_id": self.config["project_id"],
            "workload": self.config["workload"],
            "systems": [],
        }

        # Add minimal system configs (connection info only)
        for system_config in self.config.get("systems", []):
            system_kind = system_config["kind"]
            setup_config = system_config.get("setup", {})

            # Use system-specific extraction method to get connection info
            system_class = self._get_system_class(system_kind)
            if system_class:
                connection_info = system_class.extract_workload_connection_info(
                    setup_config, for_local_execution=True
                )
            else:
                # This should not happen, but fallback to empty dict if system not found
                connection_info = {}

            minimal_system = {
                "name": system_config["name"],
                "kind": system_kind,
                "version": system_config.get(
                    "version", "unknown"
                ),  # Include version for system creation
                "setup": connection_info,
            }
            workload_config["systems"].append(minimal_system)

        dst = self.package_dir / "config.yaml"
        with open(dst, "w") as f:
            yaml.dump(workload_config, f, default_flow_style=False)

    def _copy_workload_files(self) -> None:
        """Copy workload-specific files."""
        workload_name = self.config["workload"]["name"]
        workload_dir = Path("workloads") / workload_name

        if workload_dir.exists():
            dst_dir = self.package_dir / "workloads" / workload_name
            shutil.copytree(workload_dir, dst_dir, dirs_exist_ok=True)

    def _copy_minimal_system_files(self) -> None:
        """Copy only system files needed for database connections."""
        # System files are already copied in _copy_minimal_framework_files
        # No additional system files needed for workload execution
        pass

    def _create_workload_runner_script(self) -> None:
        """Create scripts for load (Phase 2) and run (Phase 3) execution."""
        systems = [s["name"] for s in self.config["systems"]]

        # Phase configurations for template rendering
        phases = {
            "load_data.sh": {
                "header": "Data Loading",
                "description": "This script loads data into pre-configured systems (Phase 2)",
                "action": "Loading data",
                "command": "load",
                "result_msg": "Load completion marker",
            },
            "run_queries.sh": {
                "header": "Query Execution",
                "description": "This script executes benchmark queries only (Phase 3)",
                "action": "Executing queries",
                "command": "run",
                "result_msg": "Results",
            },
        }

        # Render and write each script
        for script_name, phase_config in phases.items():
            context = {
                "project_id": self.project_id,
                "systems": systems,
                "phase": phase_config,
            }
            content = self._render_template("phase_script.sh.j2", context)
            script_path = self.package_dir / script_name
            script_path.write_text(content)
            script_path.chmod(0o755)

    def _create_minimal_requirements_file(self) -> None:
        """Create requirements.txt with only database drivers and execution dependencies."""
        # Minimal requirements for workload execution
        requirements = [
            "pyyaml>=6.0",
            "pandas>=2.0.0",
            "typer>=0.12.0",
            "rich>=13.0.0",
            "psutil>=5.0.0",
            "pydantic>=2.0.0",
            "jinja2>=3.1.0",
        ]

        # Add system-specific dependencies
        for system_config in self.config.get("systems", []):
            system_kind = system_config.get("kind", "").lower()

            try:
                # Use the same dynamic system loading as the main package
                system_class = self._get_system_class(system_kind)
                if system_class and hasattr(system_class, "get_python_dependencies"):
                    requirements.extend(system_class.get_python_dependencies())
            except Exception as e:
                print(
                    f"Warning: Error loading dependencies for system '{system_kind}': {e}"
                )

        # Add workload-specific dependencies
        workload_name = self.config["workload"]["name"]
        try:
            workload_class = self._get_workload_class(workload_name)
            if workload_class and hasattr(workload_class, "get_python_dependencies"):
                requirements.extend(workload_class.get_python_dependencies())
        except Exception as e:
            print(
                f"Warning: Error loading dependencies for workload '{workload_name}': {e}"
            )

        # Remove duplicates
        unique_requirements = list(dict.fromkeys(requirements))

        requirements_file = self.package_dir / "requirements.txt"
        requirements_file.write_text("\n".join(unique_requirements))

    def _get_system_class(self, system_kind: str) -> type[SystemUnderTest] | None:
        """Dynamically import and return the system class for the given system kind."""
        import importlib
        import inspect

        class_name = f"{system_kind.capitalize()}System"
        module_name = f"benchkit.systems.{system_kind}"

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                return cls if isinstance(cls, type) else None
            else:
                # Try to find any class that inherits from SystemUnderTest
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, SystemUnderTest)
                        and attr != SystemUnderTest
                        and hasattr(attr, "get_python_dependencies")
                    ):
                        return attr

                return None

        except ImportError:
            return None

    def _get_workload_class(self, workload_name: str) -> type | None:
        """Dynamically import and return the workload class for the given workload name."""
        import importlib
        import inspect

        # Convert workload name to class name (e.g., tpch -> TPCH)
        class_name = workload_name.upper()
        module_name = f"benchkit.workloads.{workload_name.lower()}"

        try:
            module = importlib.import_module(module_name)

            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                return cls if isinstance(cls, type) else None
            else:
                # Try to find any class that inherits from Workload
                from ..workloads.base import Workload

                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, Workload)
                        and attr != Workload
                        and hasattr(attr, "get_python_dependencies")
                    ):
                        return attr

                return None

        except ImportError:
            return None

    def _create_workload_cli(self) -> None:
        """Create a unified CLI with load and run subcommands using templates."""
        # Template files to copy (static Python files, no Jinja interpolation needed)
        template_files = {
            "cli.py.j2": "benchkit/cli.py",
            "load_runner.py.j2": "benchkit/load_runner.py",
            "workload_runner.py.j2": "benchkit/workload_runner.py",
            "__main__.py.j2": "benchkit/__main__.py",
        }

        for template_name, output_path in template_files.items():
            # These templates are static (no variables), so just render with empty context
            content = self._render_template(template_name, {})
            output_file = self.package_dir / output_path
            output_file.write_text(content)
