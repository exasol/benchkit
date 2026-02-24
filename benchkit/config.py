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
        from benchkit.systems import SYSTEM_IMPLEMENTATIONS

        valid_kinds = SYSTEM_IMPLEMENTATIONS.keys()
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
    load_workers: int | None = None  # Parallel data loading workers
    data_loading_timeout: int | None = (
        None  # Explicit timeout for data loading (seconds)
    )
    data_generation_timeout: int | None = (
        None  # Explicit timeout for data generation (seconds)
    )
    execution_timeout: int | None = (
        None  # Explicit timeout for query execution (seconds)
    )

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
        valid_formats = {"csv", "parquet", "tsv"}
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

    mode: str = "local"  # local, aws, gcp, azure, managed, remote
    region: str | None = None
    availability_zone_index: int = (
        0  # Index of AZ to use (0, 1, 2) - useful when specific AZ lacks capacity
    )

    # Direct instance config (simplified format - when environment serves one system)
    instance_type: str | None = None
    disk: dict[str, Any] | None = None
    label: str | None = None

    # Legacy format (when multiple systems share one environment)
    instances: dict[str, dict[str, Any]] | None = None

    os_image: str | None = None
    ssh_key_name: str | None = None  # SSH key name for cloud instances
    ssh_private_key_path: str | None = None  # Path to private key file for SSH access
    allow_external_database_access: bool = (
        False  # Allow external access to database ports
    )

    # Remote mode fields (pre-provisioned machines)
    nodes: dict[str, Any] | None = None  # Maps system names to IP info
    ssh_user: str = "ubuntu"  # SSH user for remote connections
    ssh_port: int = 22  # SSH port for remote connections

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Ensure environment mode is valid."""
        valid_modes = {"local", "aws", "gcp", "azure", "managed", "remote"}
        if v not in valid_modes:
            raise ValueError(
                f"Unknown environment mode '{v}'. Supported: {', '.join(sorted(valid_modes))}"
            )
        return v

    @model_validator(mode="after")
    def validate_remote_config(self) -> "EnvironmentConfig":
        """Validate remote mode has required fields."""
        if self.mode == "remote":
            if not self.nodes:
                raise ValueError(
                    "Remote mode requires 'nodes' mapping system names to IP info. "
                    "Example: nodes: {exasol: {public_ip: '54.1.2.3'}}"
                )
            if not self.ssh_private_key_path:
                raise ValueError(
                    "Remote mode requires 'ssh_private_key_path' for SSH access"
                )
        return self


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
    sequential: bool = False  # Per-system infrastructure lifecycle mode
    continue_on_failure: bool = False  # Continue with next system if one fails

    @model_validator(mode="after")
    def validate_parallel_max_workers(self) -> "ExecutionConfig":
        """Ensure consistency between parallel flag and max_workers."""
        if self.max_workers is not None:
            if self.max_workers == 1 and self.parallel:
                raise ValueError(
                    "execution.parallel=true with max_workers=1 is contradictory. "
                    "Set parallel=false for sequential execution."
                )
            if self.max_workers > 1 and not self.parallel:
                raise ValueError(
                    f"execution.max_workers={self.max_workers} requires parallel=true. "
                    "Set parallel=true to enable concurrent execution."
                )
        return self


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

            # Get system class for validation
            system_class = get_system_class(system_config.kind)
            if system_class is None:
                raise ValueError(
                    f"System '{system_config.name}': Unknown system kind '{system_config.kind}'"
                )

            # Check if system supports multinode when node_count > 1
            if node_count > 1:
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

            # Delegate system-specific validation to the system class
            system_class.validate_setup(
                system_config.setup, system_config.name, node_count
            )

        return v

    @model_validator(mode="after")
    def validate_remote_nodes_match_systems(self) -> "BenchmarkConfig":
        """Validate that remote mode nodes reference valid systems with required fields."""
        if not self.systems:
            return self

        system_names = {s.name for s in self.systems}

        # Collect all environments (both legacy and multi-format)
        envs: dict[str, EnvironmentConfig] = {}
        if self.environments:
            for name, env in self.environments.items():
                envs[name] = env
        elif self.env:
            envs["default"] = self.env

        for env_name, env_cfg in envs.items():
            if env_cfg.mode != "remote" or not env_cfg.nodes:
                continue

            # Find systems using this environment
            systems_using_env = set()
            for system in self.systems:
                sys_env = system.environment or "default"
                if sys_env == env_name:
                    systems_using_env.add(system.name)

            # Validate each node entry
            for node_name, node_info in env_cfg.nodes.items():
                if node_name not in system_names:
                    raise ValueError(
                        f"Remote node '{node_name}' does not match any system. "
                        f"Valid systems: {', '.join(sorted(system_names))}"
                    )

                # Validate node info structure (single or multinode)
                if isinstance(node_info, list):
                    for i, node in enumerate(node_info):
                        if not isinstance(node, dict) or "public_ip" not in node:
                            raise ValueError(
                                f"Remote node '{node_name}[{i}]' must have 'public_ip'"
                            )
                elif isinstance(node_info, dict):
                    if "public_ip" not in node_info:
                        raise ValueError(
                            f"Remote node '{node_name}' must have 'public_ip'"
                        )
                else:
                    raise ValueError(
                        f"Remote node '{node_name}' must be a dict or list of dicts"
                    )

            # Check that all systems using this remote env have node entries
            for system_name in systems_using_env:
                if system_name not in env_cfg.nodes:
                    raise ValueError(
                        f"System '{system_name}' uses remote environment '{env_name}' "
                        f"but has no entry in 'nodes'. Add: nodes.{system_name}.public_ip"
                    )

        return self

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
