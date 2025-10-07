"""System information gathering for benchmark environments."""

import json
import platform
import socket
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from ..util import safe_command


def _safe(cmd: str) -> str:
    """Execute command safely, returning output or error message."""
    result = safe_command(cmd)
    if result["success"]:
        stdout = result["stdout"]
        return str(stdout).strip() if stdout else ""
    else:
        stderr = result["stderr"]
        return f"ERR: {str(stderr) if stderr else 'Unknown error'}"


def probe_all(outdir: Path) -> dict[str, Any]:
    """
    Gather comprehensive system information for benchmark reproducibility.

    Returns:
        Dictionary containing all system information
    """
    data = {
        "probe_timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        **_probe_basic_info(),
        **_probe_cpu_info(),
        **_probe_memory_info(),
        **_probe_storage_info(),
        **_probe_network_info(),
        **_probe_kernel_info(),
        **_probe_virtualization_info(),
        **_probe_cloud_metadata(),
    }

    # Save to file
    output_file = outdir / "system.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    return data


def _probe_basic_info() -> dict[str, Any]:
    """Basic Python and platform information."""
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
    }


def _probe_cpu_info() -> dict[str, Any]:
    """Detailed CPU information."""
    cpu_info: dict[str, Any] = {
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_freq": dict(psutil.cpu_freq()._asdict()) if psutil.cpu_freq() else None,
        "lscpu": _safe("lscpu"),
    }

    # Try to get more detailed CPU info
    cpu_model = _safe("grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not cpu_model.startswith("ERR:"):
        cpu_info["cpu_model"] = cpu_model.strip()

    # CPU architecture details
    cpu_vendor = _safe("grep 'vendor_id' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not cpu_vendor.startswith("ERR:"):
        cpu_info["cpu_vendor"] = cpu_vendor.strip()

    # CPU family and stepping
    cpu_family = _safe("grep 'cpu family' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not cpu_family.startswith("ERR:"):
        cpu_info["cpu_family"] = cpu_family.strip()

    cpu_stepping = _safe("grep 'stepping' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not cpu_stepping.startswith("ERR:"):
        cpu_info["cpu_stepping"] = cpu_stepping.strip()

    # Cache information
    l1_cache = _safe("grep 'cache size' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not l1_cache.startswith("ERR:"):
        cpu_info["l1_cache"] = l1_cache.strip()

    # More detailed cache info from lscpu
    cache_info = _safe("lscpu | grep -E '(L1|L2|L3).*cache'")
    if not cache_info.startswith("ERR:"):
        cpu_info["cache_details"] = cache_info

    # CPU microcode version
    microcode = _safe("grep 'microcode' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not microcode.startswith("ERR:"):
        cpu_info["microcode"] = microcode.strip()

    # CPU flags
    cpu_flags = _safe("grep 'flags' /proc/cpuinfo | head -1 | cut -d: -f2")
    if not cpu_flags.startswith("ERR:"):
        cpu_info["cpu_flags"] = cpu_flags.strip().split()

    # CPU governor and scaling
    governor = _safe("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
    if not governor.startswith("ERR:"):
        cpu_info["scaling_governor"] = governor.strip()

    # CPU temperature (if available)
    cpu_temp = _safe("sensors | grep 'Core 0' | cut -d: -f2 | cut -d'(' -f1")
    if not cpu_temp.startswith("ERR:") and cpu_temp.strip():
        cpu_info["cpu_temperature"] = cpu_temp.strip()

    return cpu_info


def _probe_memory_info() -> dict[str, Any]:
    """Memory configuration and availability."""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    memory_info: dict[str, Any] = {
        "memory_total_gb": round(memory.total / 1e9, 2),
        "memory_available_gb": round(memory.available / 1e9, 2),
        "memory_percent_used": memory.percent,
        "swap_total_gb": round(swap.total / 1e9, 2),
        "swap_used_gb": round(swap.used / 1e9, 2),
    }

    # Memory details from /proc/meminfo
    meminfo = _safe("cat /proc/meminfo")
    if not meminfo.startswith("ERR:"):
        memory_info["meminfo"] = meminfo

    # Memory hardware information from dmidecode
    memory_hardware = _safe(
        "dmidecode --type memory | grep -E '(Size|Speed|Manufacturer|Part Number|Type:|Configured|Locator)'"
    )
    if not memory_hardware.startswith("ERR:"):
        memory_info["memory_hardware"] = memory_hardware

    # Memory speed and timing information
    memory_speed = _safe(
        "dmidecode --type 17 | grep -E '(Speed|Configured Clock Speed)' | head -4"
    )
    if not memory_speed.startswith("ERR:"):
        memory_info["memory_speed"] = memory_speed

    # Memory type (DDR4, DDR5, etc.)
    memory_type = _safe("dmidecode --type 17 | grep 'Type:' | head -1 | cut -d: -f2")
    if not memory_type.startswith("ERR:"):
        memory_info["memory_type"] = memory_type.strip()

    # Memory module count and configuration
    memory_slots = _safe(
        "dmidecode --type 17 | grep 'Size:' | grep -v 'No Module Installed' | wc -l"
    )
    if not memory_slots.startswith("ERR:"):
        memory_info["memory_modules_installed"] = memory_slots.strip()

    # NUMA topology
    numa_info = _safe("numactl --hardware")
    if not numa_info.startswith("ERR:"):
        memory_info["numa"] = numa_info

    # Memory bandwidth information (if available)
    memory_bandwidth = _safe(
        "lshw -c memory 2>/dev/null | grep -E '(clock|width|size)'"
    )
    if not memory_bandwidth.startswith("ERR:"):
        memory_info["memory_bandwidth_info"] = memory_bandwidth

    # Huge pages configuration
    hugepages_info = _safe("grep -E '(HugePages|Hugepagesize)' /proc/meminfo")
    if not hugepages_info.startswith("ERR:"):
        memory_info["hugepages"] = hugepages_info

    return memory_info


def _probe_storage_info() -> dict[str, Any]:
    """Storage devices and filesystem information."""
    storage_info: dict[str, Any] = {
        "disk_usage": [],
        "lsblk": _safe(
            "lsblk -o NAME,MODEL,SIZE,TYPE,MOUNTPOINT,FSTYPE,ROTA,DISC-GRAN,DISC-MAX"
        ),
    }

    # Disk usage for all mounted filesystems
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            storage_info["disk_usage"].append(
                {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / 1e9, 2),
                    "used_gb": round(usage.used / 1e9, 2),
                    "free_gb": round(usage.free / 1e9, 2),
                    "percent": round((usage.used / usage.total) * 100, 1),
                }
            )
        except PermissionError:
            continue

    # Storage device details with performance characteristics
    storage_devices = _safe("lsblk -d -o NAME,MODEL,SIZE,ROTA,TYPE | grep -v loop")
    if not storage_devices.startswith("ERR:"):
        storage_info["storage_devices"] = storage_devices

    # NVMe devices with detailed information
    nvme_list = _safe("nvme list")
    if not nvme_list.startswith("ERR:"):
        storage_info["nvme_devices"] = nvme_list

    # NVMe smart information for performance characteristics
    nvme_smart = _safe(
        "nvme list | grep -v 'Node' | awk '{print $1}' | xargs -I {} nvme smart-log {} 2>/dev/null | head -20"
    )
    if not nvme_smart.startswith("ERR:"):
        storage_info["nvme_smart"] = nvme_smart

    # Storage scheduler information
    storage_schedulers = _safe(
        "find /sys/block -name scheduler -exec sh -c 'echo -n \"{}:\"; cat {}' \\; 2>/dev/null"
    )
    if not storage_schedulers.startswith("ERR:"):
        storage_info["io_schedulers"] = storage_schedulers

    # SSD vs HDD identification and performance parameters
    storage_types = _safe("lsblk -d -o NAME,ROTA | grep -v NAME")
    if not storage_types.startswith("ERR:"):
        storage_info["storage_types"] = storage_types

    # Mount options that affect performance
    mount_options = _safe(
        "mount | grep -E '(ext4|xfs|btrfs)' | cut -d'(' -f2 | cut -d')' -f1"
    )
    if not mount_options.startswith("ERR:"):
        storage_info["mount_options"] = mount_options

    # I/O statistics
    try:
        io_stats = psutil.disk_io_counters(perdisk=True)
        if io_stats:
            storage_info["io_stats"] = {
                device: dict(stats._asdict()) for device, stats in io_stats.items()
            }
    except Exception:
        pass

    # Block device queue depth and parameters
    block_params = _safe(
        "find /sys/block -name queue -exec sh -c 'echo \"{}:\"; cat {}/nr_requests {}/scheduler {}/rotational 2>/dev/null' \\; | head -20"
    )
    if not block_params.startswith("ERR:"):
        storage_info["block_device_params"] = block_params

    return storage_info


def _probe_network_info() -> dict[str, Any]:
    """Network configuration and statistics."""
    network_info: dict[str, Any] = {
        "interfaces": [],
        "ip_link": _safe("ip -s link"),
    }

    # Network interface details
    try:
        net_interfaces = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()

        for interface, addresses in net_interfaces.items():
            if_info: dict[str, Any] = {"name": interface, "addresses": []}

            for addr in addresses:
                if_info["addresses"].append(
                    {
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    }
                )

            if interface in net_stats:
                stats = net_stats[interface]
                if_info.update(
                    {
                        "isup": stats.isup,
                        "duplex": str(stats.duplex),
                        "speed": stats.speed,
                        "mtu": stats.mtu,
                    }
                )

            network_info["interfaces"].append(if_info)

    except Exception as e:
        network_info["interface_error"] = str(e)

    # Network driver information
    network_drivers = _safe(
        "find /sys/class/net -name 'eth*' -o -name 'ens*' -o -name 'enp*' | xargs -I {} sh -c 'echo -n \"{}:\"; cat {}/device/driver/module/drivers/*/module 2>/dev/null || echo unknown' 2>/dev/null | head -10"
    )
    if not network_drivers.startswith("ERR:"):
        network_info["network_drivers"] = network_drivers

    # Network speed and capabilities via ethtool
    network_capabilities = _safe(
        "for iface in $(ip link show | grep -E '^[0-9]+:' | grep -v lo | cut -d: -f2 | tr -d ' '); do echo \"$iface:\"; ethtool $iface 2>/dev/null | grep -E '(Speed|Duplex|Link detected)' || echo 'ethtool not available'; done"
    )
    if not network_capabilities.startswith("ERR:"):
        network_info["network_capabilities"] = network_capabilities

    # Network queue configuration
    network_queues = _safe(
        "for iface in $(ip link show | grep -E '^[0-9]+:' | grep -v lo | cut -d: -f2 | tr -d ' '); do echo \"$iface queues:\"; ls /sys/class/net/$iface/queues/ 2>/dev/null | wc -l || echo 'unknown'; done"
    )
    if not network_queues.startswith("ERR:"):
        network_info["network_queues"] = network_queues

    # TCP/UDP buffer settings
    network_buffers = _safe(
        "sysctl -a 2>/dev/null | grep -E '(net.core|net.ipv4.tcp)' | grep -E '(mem|buf)' | head -10"
    )
    if not network_buffers.startswith("ERR:"):
        network_info["network_buffers"] = network_buffers

    # Network hardware information
    network_hardware = _safe(
        "lshw -c network 2>/dev/null | grep -E '(product|vendor|capacity|driver|firmware)'"
    )
    if not network_hardware.startswith("ERR:"):
        network_info["network_hardware"] = network_hardware

    # Network interface statistics
    network_stats = _safe("cat /proc/net/dev")
    if not network_stats.startswith("ERR:"):
        network_info["interface_statistics"] = network_stats

    return network_info


def _probe_kernel_info() -> dict[str, Any]:
    """Kernel and OS information."""
    return {
        "kernel": _safe("uname -a"),
        "os_release": _safe("cat /etc/os-release"),
        "kernel_version": _safe("cat /proc/version"),
        "uptime": _safe("uptime"),
        "timezone": _safe("timedatectl show --property=Timezone --value")
        or _safe("date +%Z"),
    }


def _probe_virtualization_info() -> dict[str, Any]:
    """Virtualization and container information."""
    virt_info: dict[str, Any] = {}

    # Check if running in container
    if Path("/.dockerenv").exists():
        virt_info["container"] = "docker"
    elif Path("/run/.containerenv").exists():
        virt_info["container"] = "podman"

    # Check for virtualization
    systemd_detect = _safe("systemd-detect-virt")
    if not systemd_detect.startswith("ERR:") and systemd_detect != "none":
        virt_info["virtualization"] = systemd_detect

    # Check for hypervisor
    dmesg_hypervisor = _safe("dmesg | grep -i hypervisor | head -5")
    if not dmesg_hypervisor.startswith("ERR:") and dmesg_hypervisor.strip():
        virt_info["hypervisor_info"] = dmesg_hypervisor

    # CPU virtualization flags
    virt_flags = _safe("grep -E '(vmx|svm)' /proc/cpuinfo")
    if not virt_flags.startswith("ERR:"):
        virt_info["virt_cpu_flags"] = bool(virt_flags.strip())

    return virt_info


def _probe_cloud_metadata() -> dict[str, Any]:
    """Cloud provider metadata (if available)."""
    cloud_info = {}

    # AWS metadata
    aws_metadata = _safe(
        "curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-type"
    )
    if not aws_metadata.startswith("ERR:") and "curl:" not in aws_metadata:
        cloud_info["aws"] = {
            "instance_type": aws_metadata,
            "instance_id": _safe(
                "curl -s --max-time 2 http://169.254.169.254/latest/meta-data/instance-id"
            ),
            "availability_zone": _safe(
                "curl -s --max-time 2 http://169.254.169.254/latest/meta-data/placement/availability-zone"
            ),
            "ami_id": _safe(
                "curl -s --max-time 2 http://169.254.169.254/latest/meta-data/ami-id"
            ),
        }

    # GCP metadata
    gcp_metadata = _safe(
        "curl -s --max-time 2 -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/machine-type"
    )
    if not gcp_metadata.startswith("ERR:") and "curl:" not in gcp_metadata:
        cloud_info["gcp"] = {
            "machine_type": (
                gcp_metadata.split("/")[-1] if "/" in gcp_metadata else gcp_metadata
            ),
            "zone": _safe(
                "curl -s --max-time 2 -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/zone"
            ).split("/")[-1],
        }

    # Azure metadata
    azure_metadata = _safe(
        "curl -s --max-time 2 -H 'Metadata: true' http://169.254.169.254/metadata/instance/compute/vmSize?api-version=2021-02-01&format=text"
    )
    if not azure_metadata.startswith("ERR:") and "curl:" not in azure_metadata:
        cloud_info["azure"] = {
            "vm_size": azure_metadata,
            "location": _safe(
                "curl -s --max-time 2 -H 'Metadata: true' http://169.254.169.254/metadata/instance/compute/location?api-version=2021-02-01&format=text"
            ),
        }

    return cloud_info


def compare_system_configurations(system_data: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compare system configurations and group similar systems together.

    Args:
        system_data: List of system probe results from different instances

    Returns:
        Dictionary with grouped system configurations and differences
    """
    if not system_data:
        return {"groups": [], "differences": []}

    # Key fields to compare for grouping (with tolerance values)
    comparison_fields: dict[str, dict[str, Any]] = {
        "cpu_model": {"tolerance": None, "key": "cpu_model"},
        "cpu_count_logical": {"tolerance": 0, "key": "cpu_count_logical"},
        "cpu_count_physical": {"tolerance": 0, "key": "cpu_count_physical"},
        "cpu_freq_max": {"tolerance": 50, "key": "cpu_freq.max"},  # 50 MHz tolerance
        "memory_total_gb": {"tolerance": 1, "key": "memory_total_gb"},  # 1 GB tolerance
        "memory_type": {"tolerance": None, "key": "memory_type"},
        "storage_type": {"tolerance": None, "key": "storage_types"},
        "network_speed": {"tolerance": None, "key": "network_capabilities"},
        "cloud_instance_type": {"tolerance": None, "key": "aws.instance_type"},
    }

    groups: list[dict[str, Any]] = []

    for i, system in enumerate(system_data):
        # Ensure system is properly typed as dict
        system_dict: dict[str, Any] = system
        system_name = system_dict.get("hostname", f"system_{i}")

        # Extract key values for comparison
        system_profile = {}
        for field, config in comparison_fields.items():
            value = _extract_nested_value(system_dict, config["key"])
            system_profile[field] = value

        # Find matching group or create new one
        matched_group = None
        for group in groups:
            profile = group["profile"]
            assert isinstance(profile, dict), "Group profile should be a dict"
            if _systems_match(system_profile, profile, comparison_fields):
                matched_group = group
                break

        if matched_group:
            systems_list = matched_group["systems"]
            system_data_list = matched_group["system_data"]
            assert isinstance(systems_list, list), "Systems should be a list"
            assert isinstance(system_data_list, list), "System data should be a list"
            systems_list.append(system_name)
            system_data_list.append(system_dict)
        else:
            groups.append(
                {
                    "profile": system_profile,
                    "systems": [system_name],
                    "system_data": [system_dict],
                }
            )

    # Create human-readable group descriptions
    for group in groups:
        profile = group["profile"]
        assert isinstance(profile, dict), "Group profile should be a dict"
        group["description"] = _create_group_description(profile)
        # Remove raw system_data from final output to keep it clean
        del group["system_data"]

    return {
        "groups": groups,
        "total_systems": len(system_data),
        "unique_configurations": len(groups),
    }


def _extract_nested_value(data: dict, key_path: str) -> Any:
    """Extract value from nested dictionary using dot notation."""
    keys = key_path.split(".")
    value: Any = data
    try:
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    except (KeyError, TypeError):
        return None


def _systems_match(profile1: dict, profile2: dict, comparison_fields: dict) -> bool:
    """Check if two system profiles match within tolerances."""
    for field, config in comparison_fields.items():
        val1 = profile1.get(field)
        val2 = profile2.get(field)

        if val1 is None or val2 is None:
            if val1 != val2:  # Both None is ok, one None is not
                return False
            continue

        tolerance = config["tolerance"]
        if tolerance is None:
            # Exact match required for strings
            if val1 != val2:
                return False
        else:
            # Numeric comparison with tolerance
            try:
                if abs(float(val1) - float(val2)) > tolerance:
                    return False
            except (ValueError, TypeError):
                if val1 != val2:
                    return False

    return True


def _create_group_description(profile: dict) -> str:
    """Create human-readable description of system configuration."""
    parts = []

    if profile.get("cpu_model"):
        cpu_model = str(profile["cpu_model"]).strip()
        # Simplify CPU model name
        cpu_model = (
            cpu_model.replace("Intel(R)", "").replace("(R)", "").replace("(TM)", "")
        )
        cpu_model = " ".join(cpu_model.split())  # Remove extra spaces
        parts.append(f"CPU: {cpu_model}")

    if profile.get("cpu_count_logical"):
        parts.append(f"{profile['cpu_count_logical']} vCPUs")

    if profile.get("cpu_freq_max"):
        freq_ghz = round(float(profile["cpu_freq_max"]) / 1000, 1)
        parts.append(f"{freq_ghz}GHz")

    if profile.get("memory_total_gb"):
        parts.append(f"{profile['memory_total_gb']}GB RAM")

    if profile.get("memory_type"):
        parts.append(f"{profile['memory_type']} memory")

    if profile.get("cloud_instance_type"):
        parts.append(f"({profile['cloud_instance_type']})")

    return ", ".join(parts) if parts else "Unknown configuration"
