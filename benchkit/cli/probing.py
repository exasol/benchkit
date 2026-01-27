"""System probing functionality for remote and managed systems.

This module handles probing system information from:
- Cloud instances (via Terraform/SSH)
- Managed deployments (via SSH or API)
- Local systems (direct probing)
"""

import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def probe_remote_systems(config: dict[str, Any], outdir: Path) -> bool:
    """Probe system information on remote cloud instances.

    Args:
        config: Configuration dictionary
        outdir: Output directory for probe results

    Returns:
        True if all probes succeeded, False otherwise
    """
    from ..common.cli_helpers import (
        get_all_environments,
        get_cloud_ssh_key_path,
        get_first_cloud_provider,
    )
    from ..common.enums import EnvironmentMode
    from ..infra.manager import InfraManager

    try:
        # Get cloud provider from config
        provider = get_first_cloud_provider(config)
        if not provider:
            console.print("[yellow]No cloud provider found in configuration[/yellow]")
            return False

        # Create infrastructure manager to get instance information
        infra_manager = InfraManager(provider, config)

        # Get terraform outputs to find instances
        result = infra_manager._run_terraform_command("output", ["-json"])
        if not result.success:
            console.print(f"[red]Failed to get terraform outputs: {result.error}[/red]")
            return False

        outputs = result.outputs or {}

        # Extract instance information from new terraform output format
        # After Terraform fix, IPs are always lists: ["ip"] for single-node, ["ip1", "ip2"] for multinode
        instances_to_probe = (
            []
        )  # List of (system_name, node_idx, public_ip, private_ip)

        # New format: system_public_ips = {"exasol": ["ip"], "clickhouse": ["ip1", "ip2"]}
        # Note: _parse_terraform_outputs already extracted the "value" field
        if "system_public_ips" in outputs:
            public_ips = outputs["system_public_ips"] or {}
            private_ips = outputs.get("system_private_ips", {}) or {}

            for system_name, public_ip_list in public_ips.items():
                private_ip_list = private_ips.get(system_name)

                # Handle both list and single IP (backward compatibility)
                if isinstance(public_ip_list, list):
                    for idx, public_ip in enumerate(public_ip_list):
                        private_ip = (
                            private_ip_list[idx]
                            if isinstance(private_ip_list, list)
                            else private_ip_list
                        )
                        instances_to_probe.append(
                            (system_name, idx, public_ip, private_ip)
                        )
                else:
                    # Backward compatibility: single IP (not a list)
                    instances_to_probe.append(
                        (system_name, 0, public_ip_list, private_ip_list)
                    )

        if not instances_to_probe:
            console.print("[yellow]No instances found in terraform outputs[/yellow]")
            return False

        # SSH configuration - use helper to support multi-environment configs
        ssh_key_path = get_cloud_ssh_key_path(config)
        if not ssh_key_path:
            ssh_key_path = "~/.ssh/id_rsa"

        # Get ssh_user from first cloud environment
        environments = get_all_environments(config)
        ssh_user = "ubuntu"
        for env_cfg in environments.values():
            mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
            if EnvironmentMode.is_cloud_provider(mode):
                ssh_user = env_cfg.get("ssh_user", "ubuntu")
                break

        # Expand tilde in SSH key path
        ssh_key_path = os.path.expanduser(ssh_key_path)

        success_count = 0
        total_instances = len(instances_to_probe)

        for system_name, node_idx, public_ip, _private_ip in instances_to_probe:
            # Show node index for multinode systems
            node_label = (
                f"-node{node_idx}"
                if any(
                    s == system_name and i != node_idx
                    for s, i, _, _ in instances_to_probe
                )
                else ""
            )
            console.print(
                f"[blue]Probing {system_name}{node_label} ([{public_ip}])...[/blue]"
            )

            if probe_single_remote_system(
                f"{system_name}{node_label}", public_ip, ssh_key_path, ssh_user, outdir
            ):
                console.print(
                    f"[green]✓ {system_name}{node_label} probe completed[/green]"
                )
                success_count += 1
            else:
                console.print(f"[red]✗ {system_name}{node_label} probe failed[/red]")

        console.print(
            f"[blue]Completed {success_count}/{total_instances} system probes[/blue]"
        )
        return success_count == total_instances

    except Exception as e:
        console.print(f"[red]Error during remote system probing: {e}[/red]")
        return False


def probe_managed_systems(config: dict[str, Any], outdir: Path) -> bool:
    """Probe system information on managed deployments (like Exasol PE).

    Managed systems are probed either via SSH (if ssh info is in connection_info.extra)
    or via API using the deployment's get_system_info() method.

    Note: We fetch fresh connection info from the deployment rather than relying
    on potentially stale state data.

    Args:
        config: Configuration dictionary
        outdir: Output directory for probe results

    Returns:
        True if all probes succeeded, False otherwise
    """
    from ..common.cli_helpers import get_managed_deployment_dir, get_managed_systems
    from ..infra.managed_state import load_managed_state
    from ..infra.self_managed import get_self_managed_deployment

    try:
        managed_systems = get_managed_systems(config)
        if not managed_systems:
            console.print("[yellow]No managed systems found in config[/yellow]")
            return True

        project_id = config.get("project_id", "default")
        success_count = 0
        total_systems = len(managed_systems)

        for system in managed_systems:
            system_name = system["name"]
            system_kind = system["kind"]

            console.print(f"[blue]Probing managed system: {system_name}...[/blue]")

            # Check state exists (system must be deployed via infra apply)
            state = load_managed_state(project_id, system_name)
            if not state:
                console.print(
                    f"[red]No state found for {system_name}. "
                    f"Run 'infra apply' first to deploy managed systems.[/red]"
                )
                continue

            # Get deployment_dir (where CLI and state files live)
            deployment_dir = get_managed_deployment_dir(config, system)

            # Get fresh connection info from the deployment instead of stale state
            deployment = get_self_managed_deployment(
                system_kind, deployment_dir, console.print
            )

            if not deployment:
                console.print(
                    f"[red]Could not create deployment handler for {system_name}[/red]"
                )
                continue

            # Fetch fresh connection info
            connection_info = deployment.get_connection_info()
            if not connection_info:
                console.print(
                    f"[red]Could not get connection info for {system_name}[/red]"
                )
                continue

            extra = connection_info.extra or {}

            # Try SSH probing first if SSH info is available
            ssh_command = extra.get("ssh_command")
            if ssh_command:
                # Parse SSH command to extract host, user, and key
                # Pass deployment_dir as state_dir for resolving relative key paths
                success = probe_managed_via_ssh(
                    system_name, ssh_command, outdir, state_dir=deployment_dir
                )
                if success:
                    console.print(
                        f"[green]✓ {system_name} probe completed (via SSH)[/green]"
                    )
                    success_count += 1
                    continue
                else:
                    console.print(
                        f"[yellow]SSH probe failed for {system_name}, "
                        f"trying API probe...[/yellow]"
                    )

            # Fall back to API probing via get_system_info()
            system_info = deployment.get_system_info()
            if system_info:
                # Save the system info to a file
                system_file = outdir / f"system_{system_name}.json"
                with open(system_file, "w") as f:
                    json.dump(system_info, f, indent=2)
                console.print(
                    f"[green]✓ {system_name} probe completed (via API)[/green]"
                )
                success_count += 1
                continue

            console.print(f"[red]✗ {system_name} probe failed[/red]")

        console.print(
            f"[blue]Completed {success_count}/{total_systems} managed system probes[/blue]"
        )
        return success_count == total_systems

    except Exception as e:
        console.print(f"[red]Error during managed system probing: {e}[/red]")
        return False


def probe_managed_via_ssh(
    system_name: str, ssh_command: str, outdir: Path, state_dir: str | None = None
) -> bool:
    """Probe a managed system via SSH using its ssh_command from connection info.

    Args:
        system_name: Name of the system
        ssh_command: Full SSH command (e.g., "ssh -i key.pem user@host -p 22")
        outdir: Output directory for probe results
        state_dir: Directory where the SSH key file might be located (for relative paths)

    Returns:
        True if probe succeeded, False otherwise
    """
    import re

    # Parse the SSH command to extract components
    # Format can be: "ssh -i key.pem user@host -p 22" or "ssh -i /path/to/key user@host"
    # The -p port can come before or after user@host
    # Extract key path (if present)
    key_match = re.search(r"-i\s+([^\s]+)", ssh_command)
    key_path = key_match.group(1) if key_match else "~/.ssh/id_rsa"

    # Extract user@host
    user_host_match = re.search(r"(\w+)@([\w\.\-]+)", ssh_command)
    if not user_host_match:
        console.print(f"[yellow]Could not parse SSH command: {ssh_command}[/yellow]")
        return False

    ssh_user = user_host_match.group(1)
    host = user_host_match.group(2)

    # Expand tilde in key path
    key_path = os.path.expanduser(key_path)

    # If key path is relative and we have a state_dir, resolve it
    if not os.path.isabs(key_path) and state_dir:
        key_path = os.path.join(state_dir, key_path)

    # Check if key file exists
    if not os.path.exists(key_path):
        console.print(f"[yellow]SSH key not found: {key_path}[/yellow]")
        return False

    return probe_single_remote_system(system_name, host, key_path, ssh_user, outdir)


def probe_single_remote_system(
    system_name: str, public_ip: str, ssh_key_path: str, ssh_user: str, outdir: Path
) -> bool:
    """Probe a single remote system and save results.

    Args:
        system_name: Name to use for the output file
        public_ip: IP address to connect to
        ssh_key_path: Path to SSH private key
        ssh_user: SSH username
        outdir: Output directory for probe results

    Returns:
        True if probe succeeded, False otherwise
    """
    import tempfile

    from ..debug import debug_log_command, debug_log_result
    from ..util import safe_command

    try:
        # Create a temporary Python script for remote execution
        probe_script = _get_probe_script()

        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(probe_script)
            temp_script_path = f.name

        try:
            # Copy script to remote system
            scp_cmd = (
                f'scp -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f"{temp_script_path} {ssh_user}@{public_ip}:/tmp/probe_system.py"
            )
            debug_log_command(scp_cmd, timeout=30)
            scp_result = safe_command(scp_cmd, timeout=30)
            debug_log_result(
                scp_result.get("success", False),
                scp_result.get("stdout"),
                scp_result.get("stderr"),
            )

            if not scp_result.get("success", False):
                console.print(
                    f"[red]Failed to copy probe script to {system_name}[/red]"
                )
                return False

            # Execute probe script on remote system
            ssh_cmd = (
                f'ssh -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "python3 /tmp/probe_system.py"'
            )
            debug_log_command(ssh_cmd, timeout=60)
            probe_result = safe_command(ssh_cmd, timeout=60)
            debug_log_result(
                probe_result.get("success", False),
                probe_result.get("stdout"),
                probe_result.get("stderr"),
            )

            if not probe_result.get("success", False):
                console.print(
                    f"[red]Failed to execute probe script on {system_name}[/red]"
                )
                return False

            # Parse the result
            probe_output = probe_result.get("stdout", "")
            system_data = json.loads(probe_output)

            # Save system-specific probe result
            system_probe_file = outdir / f"system_{system_name}.json"
            with open(system_probe_file, "w") as f:
                json.dump(system_data, f, indent=2)

            # Clean up remote script
            safe_command(
                f'ssh -i "{ssh_key_path}" -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "rm -f /tmp/probe_system.py"',
                timeout=10,
            )

            return True

        finally:
            # Clean up local temporary file
            os.unlink(temp_script_path)

    except Exception as e:
        console.print(f"[red]Error probing {system_name}: {e}[/red]")
        return False


def _get_probe_script() -> str:
    """Return the Python script used for remote system probing."""
    return '''
import json
import subprocess
import platform
import os
import time

def get_cpu_info():
    """Get detailed CPU information."""
    cpu_info = {}

    # Basic info from platform
    cpu_info["architecture"] = platform.machine()

    try:
        # Try to get detailed CPU info from /proc/cpuinfo
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        lines = cpuinfo.strip().split("\\n")
        cpu_data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "model name":
                    cpu_info["model_name"] = value
                elif key == "vendor_id":
                    cpu_info["vendor_id"] = value
                elif key == "cpu family":
                    cpu_info["cpu_family"] = int(value) if value.isdigit() else value
                elif key == "model":
                    cpu_info["model"] = int(value) if value.isdigit() else value
                elif key == "stepping":
                    cpu_info["stepping"] = int(value) if value.isdigit() else value
                elif key == "microcode":
                    cpu_info["microcode"] = value
                elif key == "cpu MHz":
                    cpu_info["cpu_mhz"] = float(value) if value.replace(".", "").isdigit() else value
                elif key == "cache size":
                    cpu_info["cache_size"] = value
                elif key == "physical id":
                    cpu_data["physical_id"] = value
                elif key == "siblings":
                    cpu_data["siblings"] = int(value) if value.isdigit() else value
                elif key == "core id":
                    cpu_data["core_id"] = value
                elif key == "cpu cores":
                    cpu_data["cpu_cores"] = int(value) if value.isdigit() else value

        # Count logical and physical CPUs
        try:
            cpu_info["count_logical"] = int(subprocess.check_output("nproc", shell=True).decode().strip())
        except:
            cpu_info["count_logical"] = os.cpu_count() or 1

        # Get physical CPU count
        try:
            cpu_info["count_physical"] = len(set([line.split(":")[1].strip() for line in cpuinfo.split("\\n") if line.startswith("physical id")]))
        except:
            cpu_info["count_physical"] = 1

    except Exception as e:
        cpu_info["error"] = str(e)

    return cpu_info

def get_memory_info():
    """Get detailed memory information."""
    memory_info = {}

    try:
        with open("/proc/meminfo", "r") as f:
            meminfo = f.read()

        for line in meminfo.split("\\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "MemTotal":
                    memory_kb = int(value.split()[0])
                    memory_info["total_kb"] = memory_kb
                    memory_info["total_gb"] = round(memory_kb / 1024 / 1024, 1)
                elif key == "MemAvailable":
                    memory_info["available_kb"] = int(value.split()[0])
                elif key == "MemFree":
                    memory_info["free_kb"] = int(value.split()[0])
                elif key == "Buffers":
                    memory_info["buffers_kb"] = int(value.split()[0])
                elif key == "Cached":
                    memory_info["cached_kb"] = int(value.split()[0])
    except Exception as e:
        memory_info["error"] = str(e)

    return memory_info

def get_disk_info():
    """Get disk information."""
    disk_info = {}

    try:
        # Get disk usage for root filesystem
        result = subprocess.check_output("df -h /", shell=True).decode()
        lines = result.strip().split("\\n")
        if len(lines) > 1:
            parts = lines[1].split()
            disk_info["root_filesystem"] = {
                "total": parts[1],
                "used": parts[2],
                "available": parts[3],
                "usage_percent": parts[4]
            }

        # Get block device information
        try:
            result = subprocess.check_output("lsblk -J", shell=True).decode()
            disk_info["block_devices"] = json.loads(result)
        except:
            pass

    except Exception as e:
        disk_info["error"] = str(e)

    return disk_info

def get_network_info():
    """Get network information."""
    network_info = {}

    try:
        # Get network interfaces
        result = subprocess.check_output("ip -j addr show", shell=True).decode()
        network_info["interfaces"] = json.loads(result)
    except Exception as e:
        network_info["error"] = str(e)

    return network_info

def get_system_info():
    """Get general system information."""
    system_info = {}

    system_info["hostname"] = platform.node()
    system_info["system"] = platform.system()
    system_info["release"] = platform.release()
    system_info["version"] = platform.version()
    system_info["machine"] = platform.machine()
    system_info["processor"] = platform.processor()

    # Get uptime
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.read().split()[0])
            system_info["uptime_seconds"] = uptime_seconds
    except:
        pass

    # Get load average
    try:
        system_info["load_average"] = os.getloadavg()
    except:
        pass

    return system_info

# Collect all system information
probe_data = {
    "timestamp": time.time(),
    "cpu": get_cpu_info(),
    "memory": get_memory_info(),
    "disk": get_disk_info(),
    "network": get_network_info(),
    "system": get_system_info()
}

# Convert to the expected format
result = {
    "timestamp": probe_data["timestamp"],
    "hostname": probe_data["system"].get("hostname", "unknown"),
    "cpu_model": probe_data["cpu"].get("model_name", "unknown"),
    "cpu_vendor": probe_data["cpu"].get("vendor_id", "unknown"),
    "cpu_count_logical": probe_data["cpu"].get("count_logical", 1),
    "cpu_count_physical": probe_data["cpu"].get("count_physical", 1),
    "cpu_mhz": probe_data["cpu"].get("cpu_mhz", 0),
    "memory_total_kb": probe_data["memory"].get("total_kb", 0),
    "memory_total_gb": probe_data["memory"].get("total_gb", 0),
    "system_info": probe_data["system"],
    "cpu_info": probe_data["cpu"],
    "memory_info": probe_data["memory"],
    "disk_info": probe_data["disk"],
    "network_info": probe_data["network"]
}

print(json.dumps(result))
'''
