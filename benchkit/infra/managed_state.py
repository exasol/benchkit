"""State management for self-managed deployments.

This module provides functions to persist and load connection info for
self-managed systems (like Exasol Personal Edition) between CLI commands.

State files are stored at: results/<project_id>/managed/<system_name>/benchkit_state.json
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from benchkit.infra.self_managed import SelfManagedConnectionInfo

# State file version for future schema migrations
STATE_VERSION = 2

# State file name (stored in system's managed directory)
STATE_FILENAME = "benchkit_state.json"


def _get_state_file_path(project_id: str, system_name: str) -> Path:
    """Get the path to the state file for a managed system.

    Args:
        project_id: Project identifier
        system_name: Name of the system

    Returns:
        Path to the state file
    """
    return Path(f"results/{project_id}/managed/{system_name}/{STATE_FILENAME}")


def save_managed_state(
    project_id: str,
    system_name: str,
    system_kind: str,
    status: str,
    connection_info: SelfManagedConnectionInfo | None,
    deployment_dir: str | None = None,
    infrastructure_commands: list[dict[str, Any]] | None = None,
    deployment_timing_s: float | None = None,
) -> bool:
    """Save state for a managed system deployment.

    Args:
        project_id: Project identifier
        system_name: Name of the system
        system_kind: Kind of system (e.g., "exasol")
        status: Deployment status (e.g., "database_ready", "running")
        connection_info: Connection information from the deployment
        deployment_dir: Path to the deployment directory
        infrastructure_commands: List of infrastructure deployment commands
            recorded during infra apply phase for report reproduction
        deployment_timing_s: Deployment duration in seconds (from SelfManagedDeployment)

    Returns:
        True if state was saved successfully
    """
    state_file = _get_state_file_path(project_id, system_name)

    # Ensure parent directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "version": STATE_VERSION,
        "status": status,
        "system_kind": system_kind,
        "system_name": system_name,
        "deployment_dir": deployment_dir,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "deployment_timing_s": deployment_timing_s,
        "connection_info": None,
        "infrastructure_commands": infrastructure_commands or [],
    }

    if connection_info:
        # Convert dataclass to dict, but don't store password for security
        conn_dict = asdict(connection_info)
        conn_dict.pop("password", None)  # Don't persist password
        state["connection_info"] = conn_dict

    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except OSError as e:
        print(f"Failed to save managed state: {e}")
        return False


def load_managed_state(project_id: str, system_name: str) -> dict[str, Any] | None:
    """Load state for a managed system deployment.

    Args:
        project_id: Project identifier
        system_name: Name of the system

    Returns:
        State dictionary if found, None otherwise
    """
    state_file = _get_state_file_path(project_id, system_name)

    if not state_file.exists():
        return None

    try:
        with open(state_file) as f:
            state: dict[str, Any] = json.load(f)
        return state
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to load managed state: {e}")
        return None


def get_all_managed_states(project_id: str) -> dict[str, dict[str, Any]]:
    """Get state for all managed systems in a project.

    Args:
        project_id: Project identifier

    Returns:
        Dictionary mapping system names to their states
    """
    managed_dir = Path(f"results/{project_id}/managed")

    if not managed_dir.exists():
        return {}

    states: dict[str, dict[str, Any]] = {}

    # Look for state files in each system subdirectory
    for system_dir in managed_dir.iterdir():
        if system_dir.is_dir():
            state_file = system_dir / STATE_FILENAME
            if state_file.exists():
                try:
                    with open(state_file) as f:
                        state = json.load(f)
                    states[system_dir.name] = state
                except (OSError, json.JSONDecodeError):
                    continue

    return states


def clear_managed_state(project_id: str, system_name: str) -> bool:
    """Remove state file for a managed system.

    Called after destroying the infrastructure.

    Args:
        project_id: Project identifier
        system_name: Name of the system

    Returns:
        True if state was cleared (or didn't exist)
    """
    state_file = _get_state_file_path(project_id, system_name)

    if not state_file.exists():
        return True

    try:
        state_file.unlink()
        return True
    except OSError as e:
        print(f"Failed to clear managed state: {e}")
        return False


def update_managed_state_status(project_id: str, system_name: str, status: str) -> bool:
    """Update just the status field in a managed state file.

    Args:
        project_id: Project identifier
        system_name: Name of the system
        status: New status value

    Returns:
        True if status was updated successfully
    """
    state = load_managed_state(project_id, system_name)
    if not state:
        return False

    state["status"] = status
    state["last_updated"] = datetime.now(timezone.utc).isoformat()

    state_file = _get_state_file_path(project_id, system_name)
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except OSError as e:
        print(f"Failed to update managed state: {e}")
        return False


def update_managed_state_timing(
    state_dir: str | Path, timing_s: float, project_id: str | None = None
) -> bool:
    """Update deployment timing in an existing managed state file.

    This function can be called from within the deployment process to persist
    timing information immediately after a deployment completes, before the
    full state save happens.

    Args:
        state_dir: Path to the deployment state directory (contains benchkit_state.json)
        timing_s: Deployment timing in seconds
        project_id: Optional project_id for logging (not used for file path)

    Returns:
        True if timing was updated successfully
    """
    state_file = Path(state_dir) / STATE_FILENAME

    if not state_file.exists():
        # No state file yet - timing will be saved when full state is written
        return False

    try:
        with open(state_file) as f:
            state: dict[str, Any] = json.load(f)

        state["deployment_timing_s"] = timing_s
        state["timing_updated_at"] = datetime.now(timezone.utc).isoformat()

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except (OSError, json.JSONDecodeError) as e:
        print(f"Failed to update managed state timing: {e}")
        return False
