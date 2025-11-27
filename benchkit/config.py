"""Configuration management for the benchmark framework."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, validator


class SystemConfig(BaseModel):
    """Configuration for a system under test."""

    name: str
    kind: str
    version: str
    setup: dict[str, Any]


class WorkloadConfig(BaseModel):
    """Configuration for benchmark workload."""

    name: str
    scale_factor: int
    queries: dict[str, list[str]] = {"include": []}  # Optional, defaults to all queries
    runs_per_query: int = 3
    warmup_runs: int = 1
    data_format: str = "csv"
    generator: str = "dbgen"
    variant: str = "official"  # Query variant to use (official, tuned, custom, etc.)
    system_variants: dict[str, str] | None = None  # Per-system variant overrides
    multiuser: dict[str, Any] | None = None  # Multiuser execution configuration


class EnvironmentConfig(BaseModel):
    """Configuration for execution environment."""

    mode: str = "local"  # local, aws, gcp, azure
    region: str | None = None
    instances: dict[str, dict[str, Any]] | None = None  # Multi-system instances config
    os_image: str | None = None
    ssh_key_name: str | None = None  # SSH key name for cloud instances
    ssh_private_key_path: str | None = None  # Path to private key file for SSH access
    allow_external_database_access: bool = (
        False  # Allow external access to database ports
    )


class ReportConfig(BaseModel):
    """Configuration for report generation."""

    output_path: str | None = None
    figures_dir: str | None = None
    index_output_dir: str | None = None
    generate_index: bool = True
    show_boxplots: bool = True
    show_latency_cdf: bool = False
    show_heatmap: bool = True
    show_bar_chart: bool = True


class ExecutionConfig(BaseModel):
    """Configuration for parallel execution."""

    parallel: bool = False  # Enable parallel execution of systems
    max_workers: int | None = (
        None  # Max concurrent systems (defaults to number of systems)
    )


class BenchmarkConfig(BaseModel):
    """Main benchmark configuration."""

    project_id: str | None = None
    title: str
    author: str
    env: EnvironmentConfig
    systems: list[SystemConfig]
    workload: WorkloadConfig
    execution: ExecutionConfig = ExecutionConfig()  # Optional, defaults to sequential
    metrics: dict[str, Any] = {}
    report: ReportConfig | None = None

    @validator("project_id")
    def validate_project_id(cls, v: str | None) -> str | None:
        """Ensure project_id is filesystem-safe."""
        if v is None:
            return v
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "project_id must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v

    @validator("systems")
    def validate_systems(cls, v: list[SystemConfig]) -> list[SystemConfig]:
        """Ensure at least one system is configured and validate multinode support."""
        if len(v) < 1:
            raise ValueError("At least one system must be configured")

        # Import here to avoid circular dependency
        from .systems.base import get_system_class

        # Validate multinode configuration for each system
        for system_config in v:
            node_count = system_config.setup.get("node_count", 1)

            # Validate node_count is a positive integer
            if not isinstance(node_count, int) or node_count < 1:
                raise ValueError(
                    f"System '{system_config.name}': node_count must be a positive integer (got {node_count})"
                )

            # Check if system supports multinode when node_count > 1
            if node_count > 1:
                system_class = get_system_class(system_config.kind)

                if system_class is None:
                    raise ValueError(
                        f"System '{system_config.name}': Unknown system kind '{system_config.kind}'"
                    )

                if not getattr(system_class, "SUPPORTS_MULTINODE", False):
                    raise ValueError(
                        f"System '{system_config.name}' (kind: {system_config.kind}) does not support multinode clusters. "
                        f"Set node_count to 1 or remove it (defaults to 1)."
                    )

        return v


def load_config(path: str | Path) -> dict[str, Any]:
    """Load and validate benchmark configuration from YAML file."""
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    # Set default project_id from config filename if not specified
    if "project_id" not in raw_config or not raw_config["project_id"]:
        raw_config["project_id"] = config_path.stem

    # Set default report paths if not specified
    if "report" not in raw_config:
        raw_config["report"] = {}

    project_id = raw_config["project_id"]

    if (
        "output_path" not in raw_config["report"]
        or not raw_config["report"]["output_path"]
    ):
        raw_config["report"]["output_path"] = f"results/{project_id}/reports"

    if (
        "figures_dir" not in raw_config["report"]
        or not raw_config["report"]["figures_dir"]
    ):
        raw_config["report"]["figures_dir"] = f"results/{project_id}/figures"

    if (
        "index_output_dir" not in raw_config["report"]
        or not raw_config["report"]["index_output_dir"]
    ):
        raw_config["report"]["index_output_dir"] = "results"

    # Expand environment variables in config
    raw_config = _expand_env_vars(raw_config)

    # Validate using Pydantic model
    try:
        validated_config = BenchmarkConfig(**raw_config)
        result: dict[str, Any] = validated_config.dict()
        return result
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e


def _expand_env_vars(obj: Any) -> Any:
    """Recursively expand environment variables in configuration."""
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return os.path.expandvars(obj)
    else:
        return obj
