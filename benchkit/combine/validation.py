"""Validation functions for the combine command."""

from pathlib import Path
from typing import Any

from .source_parser import SourceSpec


class WorkloadMismatchError(Exception):
    """Raised when workloads from different sources don't match."""

    def __init__(self, field: str, values: dict[str, Any]):
        self.field = field
        self.values = values
        super().__init__(
            f"Workload mismatch on '{field}': "
            f"{', '.join(f'{k}={v!r}' for k, v in values.items())}"
        )


class SystemNameConflictError(Exception):
    """Raised when system names conflict after renames."""

    def __init__(self, name: str, sources: list[str]):
        self.name = name
        self.sources = sources
        super().__init__(
            f"System name '{name}' appears in multiple sources after renames: "
            f"{', '.join(sources)}. Use rename syntax (system:new_name) to resolve."
        )


class MissingResultsError(Exception):
    """Raised when required result files are missing."""

    def __init__(self, message: str, available: list[str] | None = None):
        self.available = available
        full_message = message
        if available:
            full_message += f" Available: {', '.join(available)}"
        super().__init__(full_message)


# Fields that must match exactly between workloads
WORKLOAD_STRICT_FIELDS = [
    "name",
    "scale_factor",
    "data_format",
    "generator",
    "runs_per_query",
    "warmup_runs",
    "variant",
]

# Fields that need deep comparison
WORKLOAD_DEEP_FIELDS = [
    "queries",
    "system_variants",
    "multiuser",
]


def _normalize_queries(queries: dict[str, list[str]] | None) -> dict[str, list[str]]:
    """Normalize queries dict for comparison."""
    if queries is None:
        return {"include": [], "exclude": []}
    return {
        "include": sorted(queries.get("include", [])),
        "exclude": sorted(queries.get("exclude", [])),
    }


def _normalize_multiuser(multiuser: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize multiuser config for comparison."""
    if multiuser is None:
        return None
    # Only compare relevant fields
    return {
        "enabled": multiuser.get("enabled", False),
        "num_streams": multiuser.get("num_streams", 1),
        "randomize": multiuser.get("randomize", False),
        "random_seed": multiuser.get("random_seed"),
    }


def validate_workloads_compatible(
    sources: list[SourceSpec],
    strict: bool = True,
) -> dict[str, Any]:
    """Validate that all workloads are compatible for combining.

    Args:
        sources: List of SourceSpec objects with configs already loaded.
        strict: If True, all workload fields must match exactly.
                If False, only workload name must match (relaxed mode for suites).
                Non-matching fields will generate warnings.

    Returns:
        The validated workload config (from first source).

    Raises:
        WorkloadMismatchError: If workload compatibility check fails.
        ValueError: If any source has no workload config.
    """
    from rich.console import Console

    console = Console()

    if not sources:
        raise ValueError("No sources provided")

    # Get workloads from all sources
    workloads: dict[str, dict[str, Any]] = {}
    for source in sources:
        workload = source.config.get("workload")
        if not workload:
            raise ValueError(f"No workload config in {source.config_path}")
        workloads[str(source.config_path)] = workload

    # Use first workload as reference
    reference_path = list(workloads.keys())[0]
    reference = workloads[reference_path]

    # In relaxed mode, only check workload name
    fields_to_check = ["name"] if not strict else WORKLOAD_STRICT_FIELDS
    fields_to_warn = (
        [] if strict else [f for f in WORKLOAD_STRICT_FIELDS if f != "name"]
    )

    # Check required fields (error if mismatch)
    for field in fields_to_check:
        ref_value = reference.get(field)
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            value = workload.get(field)
            if value != ref_value:
                raise WorkloadMismatchError(
                    field=field,
                    values={reference_path: ref_value, path: value},
                )

    # Check warning fields (warn if mismatch, don't error)
    mismatches_warned: set[str] = set()
    for field in fields_to_warn:
        ref_value = reference.get(field)
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            value = workload.get(field)
            if value != ref_value and field not in mismatches_warned:
                console.print(
                    f"[yellow]Warning: '{field}' differs across configs "
                    f"(e.g., {ref_value!r} vs {value!r})[/yellow]"
                )
                mismatches_warned.add(field)

    if strict:
        # Check queries (deep comparison with normalization)
        ref_queries = _normalize_queries(reference.get("queries"))
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            queries = _normalize_queries(workload.get("queries"))
            if queries != ref_queries:
                raise WorkloadMismatchError(
                    field="queries",
                    values={reference_path: ref_queries, path: queries},
                )

        # Check system_variants (can be None or dict)
        ref_variants = reference.get("system_variants")
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            variants = workload.get("system_variants")
            if variants != ref_variants:
                raise WorkloadMismatchError(
                    field="system_variants",
                    values={reference_path: ref_variants, path: variants},
                )

        # Check multiuser config
        ref_multiuser = _normalize_multiuser(reference.get("multiuser"))
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            multiuser = _normalize_multiuser(workload.get("multiuser"))
            if multiuser != ref_multiuser:
                raise WorkloadMismatchError(
                    field="multiuser",
                    values={reference_path: ref_multiuser, path: multiuser},
                )
    else:
        # Warn about deep field differences in relaxed mode
        ref_queries = _normalize_queries(reference.get("queries"))
        queries_differ = False
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            queries = _normalize_queries(workload.get("queries"))
            if queries != ref_queries:
                queries_differ = True
                break
        if queries_differ:
            console.print(
                "[yellow]Warning: 'queries' configuration differs across configs[/yellow]"
            )

        ref_multiuser = _normalize_multiuser(reference.get("multiuser"))
        multiuser_differ = False
        for path, workload in workloads.items():
            if path == reference_path:
                continue
            multiuser = _normalize_multiuser(workload.get("multiuser"))
            if multiuser != ref_multiuser:
                multiuser_differ = True
                break
        if multiuser_differ:
            console.print(
                "[yellow]Warning: 'multiuser' configuration differs across configs[/yellow]"
            )

    return reference


def validate_no_name_conflicts(
    sources: list[SourceSpec],
) -> dict[tuple[str, str], str]:
    """Validate that there are no system name conflicts after renames.

    Args:
        sources: List of SourceSpec objects.

    Returns:
        Mapping of (project_id, original_name) -> final_name.

    Raises:
        SystemNameConflictError: If any final names conflict.
    """
    # Build mapping and check for conflicts
    name_mapping: dict[tuple[str, str], str] = {}
    final_name_sources: dict[str, list[str]] = {}

    for source in sources:
        project_id = source.project_id
        for system in source.systems:
            final_name = system.final_name
            key = (project_id, system.original_name)
            name_mapping[key] = final_name

            # Track which sources use each final name
            if final_name not in final_name_sources:
                final_name_sources[final_name] = []
            final_name_sources[final_name].append(
                f"{source.config_path}:{system.original_name}"
            )

    # Check for conflicts
    for final_name, sources_list in final_name_sources.items():
        if len(sources_list) > 1:
            raise SystemNameConflictError(name=final_name, sources=sources_list)

    return name_mapping


def validate_results_exist(sources: list[SourceSpec]) -> None:
    """Validate that required result files exist for all sources.

    Args:
        sources: List of SourceSpec objects with configs already loaded.

    Raises:
        MissingResultsError: If results directory or required files are missing.
    """
    for source in sources:
        results_dir = source.results_dir

        # Check results directory exists
        if not results_dir.exists():
            raise MissingResultsError(
                f"Results directory not found: {results_dir} "
                f"(for config {source.config_path})"
            )

        # Check each requested system has results
        available_systems = _find_available_systems(results_dir)

        for system in source.systems:
            csv_file = results_dir / f"runs_{system.original_name}.csv"
            if not csv_file.exists():
                raise MissingResultsError(
                    f"System '{system.original_name}' not found in results "
                    f"for project '{source.project_id}'.",
                    available=available_systems,
                )


def _find_available_systems(results_dir: Path) -> list[str]:
    """Find available system names from result files.

    Args:
        results_dir: Path to the results directory.

    Returns:
        List of system names found in result files.
    """
    systems = set()
    for csv_file in results_dir.glob("runs_*.csv"):
        name = csv_file.stem
        # Skip combined files
        if name in ("runs", "runs_warmup"):
            continue
        # Extract system name from runs_{system}.csv or runs_{system}_warmup.csv
        if name.startswith("runs_"):
            system_name = name[5:]  # Remove "runs_" prefix
            if system_name.endswith("_warmup"):
                system_name = system_name[:-7]  # Remove "_warmup" suffix
            if system_name:
                systems.add(system_name)
    return sorted(systems)


def validate_system_in_config(source: SourceSpec, system_name: str) -> bool:
    """Check if a system is defined in the source config.

    Args:
        source: The SourceSpec with loaded config.
        system_name: Name of the system to check.

    Returns:
        True if the system is defined in the config.
    """
    systems = source.config.get("systems", [])
    return any(s.get("name") == system_name for s in systems)


def get_system_config(source: SourceSpec, system_name: str) -> dict[str, Any] | None:
    """Get the config for a specific system from a source.

    Args:
        source: The SourceSpec with loaded config.
        system_name: Name of the system.

    Returns:
        The system config dict, or None if not found.
    """
    systems: list[dict[str, Any]] = source.config.get("systems", [])
    for system in systems:
        if system.get("name") == system_name:
            return system
    return None
