"""Configuration management for the benchmark framework."""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, model_validator

from .common.markers import exclude_from_package


class SystemConfig(BaseModel):
    """Configuration for a system under test."""

    name: str
    kind: str
    version: str
    setup: dict[str, Any]
    environment: str | None = None  # Reference to named environment in 'environments'

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure system name is valid for bash variable names."""
        if not v:
            raise ValueError("System name cannot be empty")
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(
                f"System name '{v}' must be a valid bash variable name: "
                "start with letter/underscore, contain only alphanumeric/underscores"
            )
        return v

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        """Ensure system kind is supported."""
        valid_kinds = {"exasol", "clickhouse"}
        if v not in valid_kinds:
            raise ValueError(
                f"Unknown system kind '{v}'. Supported: {', '.join(sorted(valid_kinds))}"
            )
        return v


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

    @field_validator("name")
    @classmethod
    def validate_workload_name(cls, v: str) -> str:
        """Ensure workload name is valid."""
        from benchkit.workloads import WORKLOAD_IMPLEMENTATIONS

        valid_workloads = WORKLOAD_IMPLEMENTATIONS.keys()

        if v not in valid_workloads:
            raise ValueError(
                f"Unknown workload '{v}'. Supported: {', '.join(sorted(valid_workloads))}"
            )
        return v

    @field_validator("scale_factor")
    @classmethod
    def validate_scale_factor(cls, v: int) -> int:
        """Ensure scale factor is positive."""
        if v < 1:
            raise ValueError(f"scale_factor must be positive (got {v})")
        return v

    @field_validator("runs_per_query")
    @classmethod
    def validate_runs_per_query(cls, v: int) -> int:
        """Ensure runs_per_query is positive."""
        if v < 1:
            raise ValueError(f"runs_per_query must be positive (got {v})")
        return v

    @field_validator("warmup_runs")
    @classmethod
    def validate_warmup_runs(cls, v: int) -> int:
        """Ensure warmup_runs is non-negative."""
        if v < 0:
            raise ValueError(f"warmup_runs must be non-negative (got {v})")
        return v

    @field_validator("data_format")
    @classmethod
    def validate_data_format(cls, v: str) -> str:
        """Ensure data format is valid."""
        valid_formats = {"csv", "parquet"}
        if v not in valid_formats:
            raise ValueError(
                f"Unknown data_format '{v}'. Supported: {', '.join(sorted(valid_formats))}"
            )
        return v

    @field_validator("multiuser")
    @classmethod
    def validate_multiuser(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate multiuser configuration."""
        if v is None:
            return v
        # Multiuser uses num_streams for concurrent execution
        num_streams = v.get("num_streams", 1)
        if not isinstance(num_streams, int) or num_streams < 1:
            raise ValueError(
                f"multiuser.num_streams must be a positive integer (got {num_streams})"
            )
        # random_seed should be an integer if provided
        random_seed = v.get("random_seed")
        if random_seed is not None and not isinstance(random_seed, int):
            raise ValueError(
                f"multiuser.random_seed must be an integer (got {type(random_seed).__name__})"
            )
        return v


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

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Ensure environment mode is valid."""
        valid_modes = {"local", "aws", "gcp", "azure", "managed"}
        if v not in valid_modes:
            raise ValueError(
                f"Unknown environment mode '{v}'. Supported: {', '.join(sorted(valid_modes))}"
            )
        return v


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
    # Support both legacy 'env' (single) and 'environments' (multi) formats
    env: EnvironmentConfig | None = None
    environments: dict[str, EnvironmentConfig] | None = None
    systems: list[SystemConfig]
    workload: WorkloadConfig
    execution: ExecutionConfig = ExecutionConfig()  # Optional, defaults to sequential
    metrics: dict[str, Any] = {}
    report: ReportConfig | None = None

    @model_validator(mode="after")
    def validate_env_or_environments(self) -> "BenchmarkConfig":
        """Ensure at least one of env or environments is provided."""
        if self.env is None and self.environments is None:
            raise ValueError(
                "Either 'env' or 'environments' must be provided in configuration"
            )
        return self

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str | None) -> str | None:
        """Ensure project_id is filesystem-safe."""
        if v is None:
            return v
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "project_id must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v

    @field_validator("systems")
    @classmethod
    def validate_systems(cls, v: list[SystemConfig]) -> list[SystemConfig]:
        """Ensure at least one system is configured and validate multinode support."""
        if len(v) < 1:
            raise ValueError("At least one system must be configured")

        # Check for unique system names
        names = [s.name for s in v]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate system names: {', '.join(set(duplicates))}")

        # Collect all system names (uppercase) for IP variable validation
        system_names_upper = {s.name.upper() for s in v}

        # Import here to avoid circular dependency
        from .systems.base import get_system_class

        # Validate each system configuration
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

            # Validate IP variable references
            ip_fields = ["host", "host_addrs", "host_external_addrs"]
            for field in ip_fields:
                value = system_config.setup.get(field, "")
                if isinstance(value, str) and value.startswith("$"):
                    var_name = value[1:]  # Remove $ prefix
                    # Check if it matches the IP variable pattern
                    match = re.match(
                        r"^([A-Z_][A-Z0-9_]*)_(PRIVATE|PUBLIC)_IP$", var_name
                    )
                    if match:
                        ref_system = match.group(1)
                        if ref_system not in system_names_upper:
                            valid_vars = [
                                f"${name}_PRIVATE_IP, ${name}_PUBLIC_IP"
                                for name in sorted(system_names_upper)
                            ]
                            raise ValueError(
                                f"System '{system_config.name}': IP variable '{value}' "
                                f"references unknown system '{ref_system}'. "
                                f"Valid IP variables: {'; '.join(valid_vars)}"
                            )

            # Validate method-specific required fields
            method = system_config.setup.get("method", "")
            kind = system_config.kind

            if kind == "exasol" and method == "installer":
                required_fields = [
                    "c4_version",
                    "image_password",
                    "db_password",
                ]
                missing = [f for f in required_fields if not system_config.setup.get(f)]
                if missing:
                    raise ValueError(
                        f"System '{system_config.name}': Exasol installer method requires: "
                        f"{', '.join(missing)}"
                    )

                # Validate db_mem_size if provided (must be integer, at least 4GB per node)
                db_mem_size = system_config.setup.get("db_mem_size")
                if db_mem_size is not None:
                    if not isinstance(db_mem_size, int):
                        raise ValueError(
                            f"System '{system_config.name}': db_mem_size must be an integer "
                            f"(in MB), got {type(db_mem_size).__name__}"
                        )
                    min_mem_per_node = 4000  # 4GB in MB
                    min_total_mem = node_count * min_mem_per_node
                    if db_mem_size < min_total_mem:
                        raise ValueError(
                            f"System '{system_config.name}': db_mem_size must be at least "
                            f"{min_mem_per_node}MB per node. With {node_count} node(s), "
                            f"minimum is {min_total_mem}MB (got {db_mem_size}MB)"
                        )

        return v

    @model_validator(mode="after")
    def validate_instance_config_matches_systems(self) -> "BenchmarkConfig":
        """Validate that instance configs reference valid system names."""
        system_names = {s.name for s in self.systems} if self.systems else set()

        # Validate legacy 'env' format
        if self.env and self.env.instances:
            for instance_name in self.env.instances:
                if instance_name not in system_names:
                    raise ValueError(
                        f"Instance config '{instance_name}' does not match any system. "
                        f"Valid systems: {', '.join(sorted(system_names))}"
                    )

        # Validate 'environments' format - check that systems reference valid environments
        if self.environments and self.systems:
            env_names = set(self.environments.keys())
            for system in self.systems:
                if system.environment and system.environment not in env_names:
                    raise ValueError(
                        f"System '{system.name}' references unknown environment "
                        f"'{system.environment}'. Valid environments: {', '.join(sorted(env_names))}"
                    )

        return self


@exclude_from_package
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
        result: dict[str, Any] = validated_config.model_dump()
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
