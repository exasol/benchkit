"""CLI helper functions for reducing code duplication across CLI commands.

This module consolidates common patterns used in multiple CLI commands:
- Config loading and output directory creation
- System filtering by name
- Environment configuration normalization (handling both 'environments' and legacy 'env')
- Cloud mode detection
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console

from .enums import EnvironmentMode

if TYPE_CHECKING:
    pass  # No type-only imports needed currently

console = Console()


def init_config_and_outdir(config_path: str) -> tuple[dict[str, Any], Path]:
    """Load configuration and create the output directory.

    Consolidates the repeated pattern:
        cfg = load_config(config)
        outdir = Path("results") / cfg["project_id"]
        outdir.mkdir(parents=True, exist_ok=True)

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Tuple of (config_dict, output_directory_path)
    """
    # Lazy import to avoid circular dependency (config.py imports from common)
    from ..config import load_config

    cfg = load_config(config_path)
    outdir = Path("results") / cfg["project_id"]
    outdir.mkdir(parents=True, exist_ok=True)
    return cfg, outdir


def filter_systems_by_names(
    cfg: dict[str, Any],
    systems: str | None,
    *,
    verbose: bool = True,
    raise_on_empty: bool = True,
) -> bool:
    """Filter config systems by comma-separated names.

    Modifies cfg["systems"] in place to only include matching systems.

    Args:
        cfg: Configuration dictionary (modified in place)
        systems: Comma-separated system names, or None to skip filtering
        verbose: Whether to print filtering info to console
        raise_on_empty: Whether to raise typer.Exit(1) if no systems match

    Returns:
        True if filtering was applied, False if systems was None

    Raises:
        typer.Exit: If raise_on_empty=True and no matching systems found
    """
    if not systems:
        return False

    import typer

    requested_systems = [s.strip() for s in systems.split(",")]
    original_systems = cfg.get("systems", [])
    original_count = len(original_systems)

    cfg["systems"] = [s for s in original_systems if s["name"] in requested_systems]

    if not cfg["systems"]:
        if raise_on_empty:
            available = [s["name"] for s in original_systems]
            console.print(
                f"[red]No matching systems found. Available: {available}[/red]"
            )
            raise typer.Exit(1)
        return True

    if verbose:
        console.print(
            f"[blue]Filtering to {len(cfg['systems'])} of {original_count} "
            f"systems: {', '.join(requested_systems)}[/blue]"
        )

    return True


def get_all_environments(cfg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Get all environments, normalizing both 'environments' and legacy 'env'.

    Handles the transition from single 'env' to multiple 'environments' configs:
    - If 'environments' exists: returns it directly
    - If only 'env' exists: wraps it as {"default": env}
    - If neither exists: returns empty dict

    Args:
        cfg: Configuration dictionary

    Returns:
        Dictionary mapping environment names to their configurations
    """
    environments = cfg.get("environments")
    if environments and isinstance(environments, dict):
        return dict(environments)

    env = cfg.get("env")
    if env and isinstance(env, dict):
        return {"default": dict(env)}

    return {}


def get_environment_for_system(
    cfg: dict[str, Any], system_name: str
) -> tuple[str, dict[str, Any]]:
    """Get the environment config for a specific system.

    Args:
        cfg: Configuration dictionary
        system_name: Name of the system to look up

    Returns:
        Tuple of (environment_name, environment_config)
    """
    environments = get_all_environments(cfg)

    # Find the system and its environment
    for system in cfg.get("systems", []):
        if system["name"] == system_name:
            env_name = system.get("environment") or "default"
            return env_name, environments.get(env_name, {})

    # System not found, return default
    return "default", environments.get("default", {})


def get_environment_mode(cfg: dict[str, Any], env_name: str = "default") -> str:
    """Get the mode for a specific environment.

    Args:
        cfg: Configuration dictionary
        env_name: Name of the environment (default: "default")

    Returns:
        Environment mode string (e.g., "local", "aws", "managed")
    """
    environments = get_all_environments(cfg)
    env_cfg = environments.get(env_name, {})
    mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
    return str(mode) if mode else EnvironmentMode.LOCAL.value


def is_any_system_cloud_mode(cfg: dict[str, Any]) -> bool:
    """Check if any system in the config uses a cloud environment.

    This checks all environments used by configured systems.

    Args:
        cfg: Configuration dictionary

    Returns:
        True if any system uses a cloud provider (aws, gcp, azure)
    """
    environments = get_all_environments(cfg)

    # Get all environment names used by systems
    used_env_names = {
        system.get("environment") or "default" for system in cfg.get("systems", [])
    }

    # Check if any used environment is a cloud provider
    for env_name in used_env_names:
        env_cfg = environments.get(env_name, {})
        mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
        if EnvironmentMode.is_cloud_provider(mode):
            return True

    return False


def get_first_cloud_provider(cfg: dict[str, Any]) -> str | None:
    """Get the first cloud provider mode from the config.

    Useful when you need a specific provider string for InfraManager.

    Args:
        cfg: Configuration dictionary

    Returns:
        Provider string ('aws', 'gcp', 'azure') or None if no cloud provider
    """
    environments = get_all_environments(cfg)

    # Get all environment names used by systems
    used_env_names = {
        system.get("environment") or "default" for system in cfg.get("systems", [])
    }

    # Find the first cloud provider
    for env_name in used_env_names:
        env_cfg = environments.get(env_name, {})
        mode = str(env_cfg.get("mode", EnvironmentMode.LOCAL.value))
        if EnvironmentMode.is_cloud_provider(mode):
            return mode

    return None


def get_system_environment_modes(
    cfg: dict[str, Any],
) -> dict[str, str]:
    """Build a mapping of system names to their environment modes.

    Args:
        cfg: Configuration dictionary

    Returns:
        Dictionary mapping system names to their environment mode strings
    """
    environments = get_all_environments(cfg)
    modes: dict[str, str] = {}

    for system in cfg.get("systems", []):
        env_name = system.get("environment") or "default"
        env_cfg = environments.get(env_name, {})
        modes[system["name"]] = env_cfg.get("mode", EnvironmentMode.LOCAL.value)

    return modes


def get_cloud_ssh_key_path(cfg: dict[str, Any]) -> str | None:
    """Get the SSH private key path from cloud environment config.

    Checks both legacy 'env' and multi-environment 'environments' configs.

    Args:
        cfg: Configuration dictionary

    Returns:
        SSH private key path string, or None if not configured
    """
    # First check legacy env config
    env_config = cfg.get("env") or {}
    if env_config.get("ssh_private_key_path"):
        return str(env_config["ssh_private_key_path"])

    # Then check environments config
    environments = get_all_environments(cfg)
    used_env_names = {
        system.get("environment") or "default" for system in cfg.get("systems", [])
    }

    for env_name in used_env_names:
        env_cfg = environments.get(env_name, {})
        mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
        if EnvironmentMode.is_cloud_provider(mode):
            ssh_key = env_cfg.get("ssh_private_key_path")
            if ssh_key:
                return str(ssh_key)

    return None


def print_project_banner(action: str, cfg: dict[str, Any]) -> None:
    """Print a consistent project action banner.

    Args:
        action: Action description (e.g., "Setting up systems for")
        cfg: Configuration dictionary
    """
    console.print(f"[blue]{action} project:[/] {cfg['project_id']}")


def print_workload_info(cfg: dict[str, Any]) -> None:
    """Print workload information in a consistent format.

    Args:
        cfg: Configuration dictionary
    """
    systems = cfg.get("systems", [])
    workload = cfg.get("workload", {})

    console.print(f"[dim]Systems: {[s['name'] for s in systems]}[/]")
    if workload:
        console.print(
            f"[dim]Workload: {workload.get('name', 'unknown')} "
            f"(SF={workload.get('scale_factor', '?')})[/]"
        )


def is_any_system_managed_mode(cfg: dict[str, Any]) -> bool:
    """Check if any system in the config uses a managed environment.

    Managed environments are self-managed deployments like Exasol Personal Edition
    that handle their own infrastructure provisioning.

    Args:
        cfg: Configuration dictionary

    Returns:
        True if any system uses managed mode
    """
    environments = get_all_environments(cfg)

    # Get all environment names used by systems
    used_env_names = {
        system.get("environment") or "default" for system in cfg.get("systems", [])
    }

    # Check if any used environment is managed mode
    for env_name in used_env_names:
        env_cfg = environments.get(env_name, {})
        mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
        if mode == EnvironmentMode.MANAGED.value:
            return True

    return False


def get_managed_systems(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Get list of systems that use managed environments.

    Args:
        cfg: Configuration dictionary

    Returns:
        List of system configuration dictionaries for managed systems
    """
    environments = get_all_environments(cfg)
    managed_systems: list[dict[str, Any]] = []

    for system in cfg.get("systems", []):
        env_name = system.get("environment") or "default"
        env_cfg = environments.get(env_name, {})
        mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)

        if mode == EnvironmentMode.MANAGED.value:
            managed_systems.append(system)

    return managed_systems


def get_managed_deployment_dir(cfg: dict[str, Any], system: dict[str, Any]) -> str:
    """Get the deployment directory for a managed system.

    The directory structure is:
        results/{project_id}/managed/{system_name}/state/

    Args:
        cfg: Full configuration dictionary
        system: System configuration dictionary

    Returns:
        Path to the deployment state directory
    """
    project_id = cfg.get("project_id", "default")
    system_name = system["name"]
    default_dir = f"results/{project_id}/managed/{system_name}/state"
    deployment_dir = system.get("setup", {}).get("deployment_dir", default_dir)
    return str(deployment_dir) if deployment_dir else default_dir
