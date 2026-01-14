"""Parse --source CLI arguments for the combine command."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SystemSelection:
    """A single system selection with optional rename.

    Attributes:
        original_name: The system name as it appears in the source project.
        new_name: Optional new name for the system in the combined project.
    """

    original_name: str
    new_name: str | None = None

    @property
    def final_name(self) -> str:
        """Get the final name (renamed or original)."""
        return self.new_name if self.new_name else self.original_name


@dataclass
class SourceSpec:
    """Parsed source specification from a --source argument.

    Attributes:
        config_path: Path to the source config YAML file.
        systems: List of system selections from this source.
        config: The loaded config dictionary (populated after loading).
        results_dir: Path to the results directory (derived from project_id).
    """

    config_path: Path
    systems: list[SystemSelection]
    config: dict[str, Any] = field(default_factory=dict)
    results_dir: Path = field(default_factory=lambda: Path())

    @property
    def project_id(self) -> str:
        """Get the project ID from the loaded config."""
        project_id = self.config.get("project_id")
        if project_id is not None:
            return str(project_id)
        return self.config_path.stem

    def load_config(self) -> dict[str, Any]:
        """Load the config file and set results_dir.

        Returns:
            The loaded config dictionary.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            yaml.YAMLError: If the config file is invalid YAML.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

        # Set results directory based on project_id
        self.results_dir = Path("results") / self.project_id
        return self.config


def parse_source_arg(source_arg: str) -> SourceSpec:
    """Parse a --source argument into a SourceSpec.

    Syntax:
        config.yaml:sys1,sys2           - Select systems without rename
        config.yaml:sys1,sys2:renamed   - Rename sys2 to "renamed"
        config.yaml:sys1:new1,sys2:new2 - Rename both systems

    Args:
        source_arg: The source specification string.

    Returns:
        A SourceSpec with the parsed config path and system selections.

    Raises:
        ValueError: If the syntax is invalid.

    Examples:
        >>> spec = parse_source_arg("config.yaml:exasol,clickhouse")
        >>> spec.config_path
        PosixPath('config.yaml')
        >>> [s.original_name for s in spec.systems]
        ['exasol', 'clickhouse']

        >>> spec = parse_source_arg("config.yaml:exasol:exa_v8,clickhouse")
        >>> spec.systems[0].final_name
        'exa_v8'
        >>> spec.systems[1].final_name
        'clickhouse'
    """
    if ":" not in source_arg:
        raise ValueError(
            f"Invalid source syntax: '{source_arg}'. "
            "Expected format: config.yaml:system1,system2 or "
            "config.yaml:sys1:new_name,sys2"
        )

    # Split into config path and systems part
    parts = source_arg.split(":", 1)
    config_path = Path(parts[0])
    systems_part = parts[1]

    if not systems_part:
        raise ValueError(
            f"No systems specified in '{source_arg}'. "
            "Expected at least one system name after the colon."
        )

    # Parse individual system selections
    systems = []
    for system_entry in systems_part.split(","):
        system_entry = system_entry.strip()
        if not system_entry:
            continue

        # Check for rename syntax: original:new_name
        if ":" in system_entry:
            sys_parts = system_entry.split(":", 1)
            original_name = sys_parts[0].strip()
            new_name = sys_parts[1].strip()

            if not original_name:
                raise ValueError(
                    f"Empty system name in '{system_entry}'. "
                    "Expected format: original_name:new_name"
                )
            if not new_name:
                raise ValueError(
                    f"Empty new name in '{system_entry}'. "
                    "Expected format: original_name:new_name"
                )

            systems.append(
                SystemSelection(original_name=original_name, new_name=new_name)
            )
        else:
            systems.append(SystemSelection(original_name=system_entry))

    if not systems:
        raise ValueError(
            f"No valid systems found in '{source_arg}'. "
            "Expected at least one system name."
        )

    return SourceSpec(config_path=config_path, systems=systems)


def parse_source_args(source_args: list[str]) -> list[SourceSpec]:
    """Parse multiple --source arguments.

    Args:
        source_args: List of source specification strings.

    Returns:
        List of parsed SourceSpec objects.

    Raises:
        ValueError: If any source argument is invalid.
    """
    return [parse_source_arg(arg) for arg in source_args]
