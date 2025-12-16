"""Infrastructure management for cloud environments."""

import json
import shlex
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..common.cli_helpers import (
    get_all_environments,
    get_cloud_ssh_key_path,
    get_environment_for_system,
)
from ..common.enums import EnvironmentMode
from ..debug import is_debug_enabled
from ..util import Timer, ensure_directory, safe_command


@dataclass
class InfraResult:
    """Result of an infrastructure operation."""

    success: bool
    message: str
    error: str | None = None
    outputs: dict[str, Any] | None = None
    plan_output: str | None = None  # For terraform plan detailed output


class InfraManager:
    """Manages cloud infrastructure for benchmarks."""

    def __init__(self, provider: str, config: dict[str, Any]):
        self.provider = provider.lower()
        self.config = config

        # Source Terraform configuration (shared, read-only templates)
        self.tf_source_dir = Path(f"infra/{self.provider}")

        # Per-project state directory for complete isolation
        # This allows multiple benchmarks to run in parallel without conflicts
        project_id = config.get("project_id", "default")
        self.project_state_dir = Path("results") / project_id / "terraform"

        # Legacy compatibility: keep infra_dir for any code that might reference it
        self.infra_dir = self.tf_source_dir

        if not self.tf_source_dir.exists():
            raise ValueError(
                f"Infrastructure directory not found: {self.tf_source_dir}"
            )

    def plan(self) -> InfraResult:
        """Plan infrastructure changes."""
        if self.provider in ["aws", "gcp", "azure"]:
            return self._terraform_plan()
        else:
            return InfraResult(
                success=False,
                message=f"Unsupported provider: {self.provider}",
                error=f"Provider {self.provider} not implemented",
            )

    def apply(self, wait_for_init: bool = True) -> InfraResult:
        """Apply infrastructure changes."""
        if self.provider in ["aws", "gcp", "azure"]:
            return self._terraform_apply(wait_for_init)
        else:
            return InfraResult(
                success=False,
                message=f"Unsupported provider: {self.provider}",
                error=f"Provider {self.provider} not implemented",
            )

    def destroy(self) -> InfraResult:
        """Destroy infrastructure."""
        if self.provider in ["aws", "gcp", "azure"]:
            return self._terraform_destroy()
        else:
            return InfraResult(
                success=False,
                message=f"Unsupported provider: {self.provider}",
                error=f"Provider {self.provider} not implemented",
            )

    def get_infrastructure_ips(self) -> dict[str, dict[str, Any]] | None:
        """
        Get public and private IPs for all systems in the infrastructure.

        Returns:
            Dictionary mapping system names to their IP addresses:
            For single-node systems:
            {
                "system_name": {
                    "public_ip": "1.2.3.4",
                    "private_ip": "10.0.0.1"
                }
            }
            For multi-node systems:
            {
                "system_name": {
                    "public_ips": ["1.2.3.4", "1.2.3.5", "1.2.3.6"],
                    "private_ips": ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
                }
            }
            Returns None if infrastructure not provisioned or IPs not available.
        """
        if self.provider not in ["aws", "gcp", "azure"]:
            return None

        try:
            result = self._run_terraform_command("output", ["-json"])
            if not result.success or not result.outputs:
                return None

            outputs = result.outputs
            public_ips = outputs.get("system_public_ips", {})
            private_ips = outputs.get("system_private_ips", {})

            if not public_ips:
                return None

            # Build infrastructure details
            infra_ips = {}
            for system_name, public_ip in public_ips.items():
                private_ip = private_ips.get(system_name, "-")

                # IPs are always lists now (Terraform outputs are consistent)
                # Single-node: [ip], Multinode: [ip1, ip2, ...]
                if isinstance(public_ip, list) and len(public_ip) > 1:
                    # Multinode system (multiple IPs)
                    infra_ips[system_name] = {
                        "public_ips": public_ip,
                        "private_ips": (
                            private_ip if isinstance(private_ip, list) else [private_ip]
                        ),
                    }
                elif isinstance(public_ip, list) and len(public_ip) == 1:
                    # Single node system (list with one element)
                    infra_ips[system_name] = {
                        "public_ip": public_ip[0],
                        "private_ip": (
                            private_ip[0]
                            if isinstance(private_ip, list)
                            else private_ip
                        ),
                    }
                else:
                    # Backward compatibility: non-list (single node)
                    infra_ips[system_name] = {
                        "public_ip": public_ip,
                        "private_ip": private_ip,
                    }

            return infra_ips
        except Exception:
            return None

    def _terraform_plan(self) -> InfraResult:
        """Run terraform plan."""
        result = self._run_terraform_command_raw("plan", ["-detailed-exitcode"])

        # Handle terraform plan exit codes:
        # 0 = no changes, 1 = error, 2 = changes detected
        if result["returncode"] in [0, 2]:
            # Determine plan status from exit code
            if result["returncode"] == 0:
                plan_status = "No changes detected"
            else:  # returncode == 2
                plan_status = "Changes detected"

            return InfraResult(
                success=True,
                message=f"Terraform plan completed successfully - {plan_status}",
                outputs=self._parse_terraform_outputs(result["stdout"]),
                plan_output=result["stdout"],  # Include full plan output
            )
        else:
            return InfraResult(
                success=False,
                message="Terraform plan failed",
                error=result["stderr"],
            )

    def _terraform_apply(self, wait_for_init: bool = True) -> InfraResult:
        """Run terraform apply and optionally wait for full initialization."""
        # Track timing for infrastructure provisioning
        with Timer("Infrastructure provisioning") as provision_timer:
            # First run terraform apply
            result = self._run_terraform_command("apply", ["-auto-approve"])

            if not result.success:
                return result

            # Optionally wait for instances to be fully initialized
            if wait_for_init:
                print(
                    "Infrastructure created successfully. Waiting for instances to initialize..."
                )
                initialization_result = self._wait_for_instance_initialization(
                    result.outputs or {}
                )

                if not initialization_result:
                    return InfraResult(
                        success=False,
                        message="Infrastructure created but instance initialization failed or timed out",
                        error="Instance initialization timeout or failure",
                    )

        # Save provisioning timing to results directory
        self._save_provisioning_timing(provision_timer.elapsed)

        if wait_for_init:
            return InfraResult(
                success=True,
                message="Infrastructure created and instances fully initialized",
                outputs=result.outputs,
            )
        else:
            return InfraResult(
                success=True,
                message="Infrastructure created successfully (initialization not waited for)",
                outputs=result.outputs,
            )

    def _terraform_destroy(self) -> InfraResult:
        """Run terraform destroy."""
        return self._run_terraform_command("destroy", ["-auto-approve"])

    def _save_provisioning_timing(self, elapsed_seconds: float) -> None:
        """Save infrastructure provisioning timing to results directory."""
        try:
            project_id = self.config.get("project_id")
            if not project_id:
                return

            results_dir = Path("results") / project_id
            ensure_directory(results_dir)

            timing_file = results_dir / "infrastructure_provisioning.json"
            timing_data = {
                "infrastructure_provisioning_s": elapsed_seconds,
                "timestamp": self._get_timestamp(),
            }

            with open(timing_file, "w") as f:
                json.dump(timing_data, f, indent=2)

            print(f"Saved infrastructure provisioning timing: {elapsed_seconds:.2f}s")

        except Exception as e:
            print(f"Warning: Failed to save provisioning timing: {e}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime

        return datetime.now().isoformat()

    def _ensure_terraform_files_copied(self) -> None:
        """
        Copy Terraform configuration files to project state directory.

        This enables per-project isolation of Terraform state, allowing
        multiple benchmarks to run in parallel without conflicts.
        Only copies if files don't exist (idempotent).
        """
        import shutil

        # Ensure project state directory exists
        self.project_state_dir.mkdir(parents=True, exist_ok=True)

        # Files to copy from source to project directory
        tf_files = ["main.tf", "user_data.sh"]

        for tf_file in tf_files:
            source = self.tf_source_dir / tf_file
            dest = self.project_state_dir / tf_file

            if source.exists() and not dest.exists():
                shutil.copy2(source, dest)

    def _run_terraform_command_raw(
        self, command: str, args: list[Any] | None = None
    ) -> dict[str, Any]:
        """Run terraform command and return raw result without success interpretation."""
        args = args or []

        try:
            # Ensure Terraform files are copied to project state directory
            self._ensure_terraform_files_copied()

            # Change to project-specific state directory (not shared infra_dir)
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_state_dir)

            try:
                # Initialize terraform if needed (uses project-local .terraform/)
                if not (Path(".terraform").exists()):
                    init_result = safe_command("terraform init -no-color", timeout=300)
                    if not init_result["success"]:
                        return init_result

                # Prepare terraform variables from config
                var_args = []
                if command == "destroy":
                    # For destroy, only provide minimal required variables
                    tf_vars = self._prepare_minimal_terraform_vars()
                else:
                    # For plan/apply, provide full configuration
                    tf_vars = self._prepare_terraform_vars()

                # Add variables as command line arguments
                import shlex

                for key, value in tf_vars.items():
                    quoted_value = shlex.quote(str(value))
                    var_args.extend(["-var", f"{key}={quoted_value}"])

                # Run terraform command with no-color flag to avoid ANSI escape sequences
                full_command = ["terraform", command, "-no-color"] + var_args + args
                result = safe_command(
                    " ".join(full_command),
                    timeout=3600,  # 1 hour timeout for infrastructure operations
                )
                return result
            finally:
                # Always restore original directory
                os.chdir(original_cwd)

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": 1,
                "elapsed_s": 0.0,
            }

    def _run_terraform_command(
        self, command: str, args: list[Any] | None = None
    ) -> InfraResult:
        """Run a terraform command with proper setup."""
        args = args or []

        try:
            # Ensure Terraform files are copied to project state directory
            self._ensure_terraform_files_copied()

            # Change to project-specific state directory (not shared infra_dir)
            import os

            original_cwd = os.getcwd()
            os.chdir(self.project_state_dir)

            try:
                # Initialize terraform if needed (uses project-local .terraform/)
                if not (Path(".terraform").exists()):
                    init_result = safe_command("terraform init -no-color", timeout=300)
                    if not init_result["success"]:
                        return InfraResult(
                            success=False,
                            message="Terraform init failed",
                            error=init_result["stderr"],
                        )

                # Prepare terraform variables from config (except for output command)
                var_args = []
                if command not in [
                    "output",
                    "show",
                    "state",
                ]:  # Commands that don't accept -var
                    if command == "destroy":
                        # For destroy, only provide minimal required variables
                        tf_vars = self._prepare_minimal_terraform_vars()
                    else:
                        # For plan/apply, provide full configuration
                        tf_vars = self._prepare_terraform_vars()

                    for key, value in tf_vars.items():
                        # Properly quote values that contain spaces or special characters
                        import shlex

                        quoted_value = shlex.quote(str(value))
                        var_args.extend(["-var", f"{key}={quoted_value}"])

                # Run terraform command with no-color flag to avoid ANSI escape sequences
                full_command = ["terraform", command, "-no-color"] + var_args + args
                result = safe_command(
                    " ".join(full_command),
                    timeout=3600,  # 1 hour timeout for infrastructure operations
                )
            finally:
                # Always restore original directory
                os.chdir(original_cwd)

            if result["success"]:
                return InfraResult(
                    success=True,
                    message=f"Terraform {command} completed successfully",
                    outputs=self._parse_terraform_outputs(result["stdout"]),
                )
            else:
                return InfraResult(
                    success=False,
                    message=f"Terraform {command} failed",
                    error=result["stderr"],
                )

        except Exception as e:
            return InfraResult(
                success=False, message="Infrastructure operation failed", error=str(e)
            )

    def _prepare_terraform_vars(self) -> dict[str, str]:
        """Prepare terraform variables from configuration."""
        env_config = self.config.get("env") or {}
        environments = self.config.get("environments") or {}

        # Determine region - check env first, then look at cloud environments
        region = env_config.get("region", "us-east-1")
        if not env_config and environments:
            # Find first cloud environment to get region
            for env_cfg in environments.values():
                if env_cfg.get("mode") in ["aws", "gcp", "azure"]:
                    region = env_cfg.get("region", "us-east-1")
                    break

        # Common variables
        tf_vars = {
            "region": region,
            "project_id": self.config.get("project_id", "benchmark"),
        }

        # Collect all required ports from the systems used in the benchmark
        all_required_ports = self._collect_required_ports()

        # Build generic systems configuration for Terraform
        # Support both legacy 'env.instances' and new 'environments.*.instances' formats
        instances_config = env_config.get("instances") or {}

        # If no instances in env, collect from environments
        if not instances_config and environments:
            for _env_name, env_cfg in environments.items():
                if env_cfg.get("mode") in ["aws", "gcp", "azure"]:
                    env_instances = env_cfg.get("instances") or {}
                    instances_config.update(env_instances)

        if not instances_config:
            raise ValueError(
                "Instance configuration is required for cloud benchmarks. "
                "Define instances in 'env.instances' or 'environments.<name>.instances'"
            )

        # Get the actual systems that should be created (respects --systems filter)
        active_systems = {s["name"] for s in self.config.get("systems", [])}

        systems_tf = {}
        for system_name, system_config in instances_config.items():
            # Only include systems that are in the filtered systems list
            if system_name in active_systems:
                disk_config = system_config.get("disk", {})
                # Default to "local" (instance store) - no EBS created unless specified
                disk_type = disk_config.get("type", "local")

                # Validate: size_gb is required for EBS volumes (anything not "local")
                if disk_type != "local":
                    if "size_gb" not in disk_config:
                        raise ValueError(
                            f"System '{system_name}': disk.size_gb is required when using "
                            f"disk type '{disk_type}'. Please specify the EBS volume size."
                        )

                # Get node_count from system setup config
                node_count = 1
                for sys_cfg in self.config.get("systems", []):
                    if sys_cfg["name"] == system_name:
                        node_count = sys_cfg.get("setup", {}).get("node_count", 1)
                        break

                systems_tf[system_name] = {
                    "instance_type": system_config.get("instance_type", "m7i.4xlarge"),
                    "disk_size": disk_config.get(
                        "size_gb", 0
                    ),  # 0 for local (unused by Terraform)
                    "disk_type": disk_type,
                    "label": system_config.get("label", ""),
                    "node_count": node_count,
                }

        # Convert to JSON string for Terraform
        import json

        tf_vars["systems"] = json.dumps(systems_tf)
        tf_vars["required_ports"] = json.dumps(all_required_ports)

        # Add SSH key if provided - check env first, then environments
        ssh_key_name = env_config.get("ssh_key_name", "")
        if not ssh_key_name and environments:
            for env_cfg in environments.values():
                if env_cfg.get("mode") in ["aws", "gcp", "azure"]:
                    ssh_key_name = env_cfg.get("ssh_key_name", "")
                    if ssh_key_name:
                        break
        if ssh_key_name:
            tf_vars["ssh_key_name"] = ssh_key_name

        # Add external access option (default false for security)
        allow_external = env_config.get("allow_external_database_access", False)
        if not allow_external and environments:
            for env_cfg in environments.values():
                if env_cfg.get("mode") in ["aws", "gcp", "azure"]:
                    allow_external = env_cfg.get(
                        "allow_external_database_access", False
                    )
                    if allow_external:
                        break
        tf_vars["allow_external_database_access"] = str(allow_external).lower()

        return tf_vars

    def _collect_required_ports(self) -> dict[str, int]:
        """Collect all required ports from systems used in this benchmark."""
        from ..systems import create_system

        # First collect all ports with their descriptions
        port_descriptions: dict[int, list[str]] = {}

        # Get systems configuration from the benchmark config
        systems_config = self.config.get("systems", [])

        for system_config in systems_config:
            try:
                # Create system instance to access class methods
                system_class = create_system(system_config).__class__
                required_ports = system_class.get_required_ports()

                # Group ports by port number to handle duplicates
                for desc, port in required_ports.items():
                    if port not in port_descriptions:
                        port_descriptions[port] = []
                    # Add system name and description to the list
                    port_descriptions[port].append(
                        f"{system_config['name']}_{desc.replace(' ', '_').lower()}"
                    )

            except Exception as e:
                # If system creation fails, skip port collection for this system
                print(
                    f"Warning: Could not collect ports for {system_config.get('name', 'unknown')}: {e}"
                )
                continue

        # Create deduplicated port map with combined descriptions
        all_ports = {}
        for port, descriptions in port_descriptions.items():
            # Use the first description as the key (they all map to the same port anyway)
            # If multiple systems use the same port, just use one key
            port_key = descriptions[0]
            all_ports[port_key] = port

        return all_ports

    def _prepare_minimal_terraform_vars(self) -> dict[str, str]:
        """Prepare minimal terraform variables for destroy operations."""
        # Get region and SSH key from any cloud environment
        environments = get_all_environments(self.config)
        region = "us-east-1"
        ssh_key_name = ""
        for env_cfg in environments.values():
            mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
            if EnvironmentMode.is_cloud_provider(mode):
                region = env_cfg.get("region", region)
                ssh_key_name = env_cfg.get("ssh_key_name", ssh_key_name)
                break  # Use first cloud environment found

        # Only provide required variables without validating full configuration
        tf_vars = {
            "project_id": self.config.get("project_id", "benchmark"),
            "region": region,
            "systems": "{}",  # Empty systems for destroy
        }

        # Add SSH key if provided
        if ssh_key_name:
            tf_vars["ssh_key_name"] = ssh_key_name

        return tf_vars

    def _parse_terraform_outputs(self, stdout: str) -> dict[str, Any]:
        """Parse terraform outputs from command output."""
        # Instead of parsing stdout (which may not contain outputs),
        # run terraform output -json to get actual outputs
        try:
            import json
            import os

            # Ensure Terraform files exist in project state directory
            self._ensure_terraform_files_copied()

            original_cwd = os.getcwd()
            os.chdir(self.project_state_dir)
            try:
                # Run terraform output -json to get structured output
                result = safe_command("terraform output -json", timeout=60)
                if result["success"] and result["stdout"]:
                    raw_outputs = json.loads(result["stdout"])
                    # Terraform output -json returns outputs in format: {"key": {"value": actual_value}}
                    # We need to extract just the values
                    outputs = {}
                    for key, output_obj in raw_outputs.items():
                        if isinstance(output_obj, dict) and "value" in output_obj:
                            outputs[key] = output_obj["value"]
                        else:
                            outputs[key] = output_obj
                    return outputs
                else:
                    print(
                        f"Warning: terraform output failed: {result.get('stderr', 'Unknown error')}"
                    )
                    return {}
            finally:
                os.chdir(original_cwd)
        except Exception as e:
            print(f"Warning: Failed to parse terraform outputs: {e}")
            return {}

    def get_instance_info(self) -> dict[str, Any]:
        """Get information about created instances."""
        if self.provider == "aws":
            return self._get_aws_instance_info()
        elif self.provider == "gcp":
            return self._get_gcp_instance_info()
        else:
            return {"error": f"Provider {self.provider} not supported"}

    def _get_aws_instance_info(self) -> dict[str, Any]:
        """Get AWS instance information for both Exasol and ClickHouse instances."""
        # Ensure Terraform files exist in project state directory
        self._ensure_terraform_files_copied()

        # Use terraform output to get instance info from project-specific directory
        import os

        original_cwd = os.getcwd()
        os.chdir(self.project_state_dir)

        try:
            result = safe_command("terraform output -json -no-color", timeout=30)
        finally:
            os.chdir(original_cwd)

        if result["success"]:
            import json

            try:
                outputs = json.loads(result["stdout"])

                # Extract generic system information from Terraform outputs
                system_data = {}

                instance_ids = outputs.get("system_instance_ids", {}).get("value", {})
                public_ips = outputs.get("system_public_ips", {}).get("value", {})
                private_ips = outputs.get("system_private_ips", {}).get("value", {})

                for system_name in instance_ids.keys():
                    instance_id = instance_ids.get(system_name)
                    public_ip = public_ips.get(system_name)
                    private_ip = private_ips.get(system_name)

                    # IPs are always lists now (Terraform outputs are consistent)
                    # Single-node: [ip], Multinode: [ip1, ip2, ...]
                    if isinstance(public_ip, list) and len(public_ip) > 1:
                        # Multinode system: create list of node info
                        system_data[system_name] = {
                            "multinode": True,
                            "node_count": len(public_ip),
                            "nodes": [
                                {
                                    "instance_id": (
                                        instance_id[i]
                                        if isinstance(instance_id, list)
                                        else instance_id
                                    ),
                                    "public_ip": public_ip[i],
                                    "private_ip": private_ip[i],
                                    "node_idx": i,
                                }
                                for i in range(len(public_ip))
                            ],
                        }
                    elif isinstance(public_ip, list) and len(public_ip) == 1:
                        # Single node system (list with one element) - extract values
                        system_data[system_name] = {
                            "multinode": False,
                            "instance_id": (
                                instance_id[0]
                                if isinstance(instance_id, list)
                                else instance_id
                            ),
                            "public_ip": public_ip[0],
                            "private_ip": (
                                private_ip[0]
                                if isinstance(private_ip, list)
                                else private_ip
                            ),
                        }
                    else:
                        # Backward compatibility: non-list (single node)
                        system_data[system_name] = {
                            "multinode": False,
                            "instance_id": instance_id,
                            "public_ip": public_ip,
                            "private_ip": private_ip,
                        }

                return system_data
            except json.JSONDecodeError:
                return {"error": "Failed to parse terraform outputs"}
        else:
            return {"error": "Failed to get terraform outputs"}

    def _get_gcp_instance_info(self) -> dict[str, Any]:
        """Get GCP instance information."""
        # Similar to AWS but for GCP
        return {"error": "GCP instance info not implemented"}

    @staticmethod
    def resolve_ip_from_infrastructure(
        var_name: str, system_name: str, project_id: str
    ) -> str | None:
        """
        Resolve IP address from project-specific infrastructure state files.

        This utility checks the project-specific Terraform state file to resolve
        IP addresses when environment variables are not set.

        Args:
            var_name: Variable name to resolve (e.g., "EXASOL_PUBLIC_IP")
            system_name: System name to match (e.g., "exasol", "clickhouse")
            project_id: Project ID for project-specific state lookup (required)

        Returns:
            IP address string if found, None otherwise
        """
        import json
        import os

        # First check environment variable
        resolved = os.environ.get(var_name)
        if resolved:
            return resolved

        # Determine if we need public or private IP based on variable name
        ip_type = "public_ip" if "PUBLIC" in var_name.upper() else "private_ip"

        # Only use project-specific state location (no legacy fallbacks)
        if not project_id:
            return None

        state_locations = [
            Path("results") / project_id / "terraform" / "terraform.tfstate"
        ]

        for state_file in state_locations:
            if not state_file.exists():
                continue

            try:
                with open(state_file) as f:
                    state = json.load(f)

                # Look for instance resources in state
                for resource in state.get("resources", []):
                    # Check for cloud instance resources (AWS, GCP, Azure)
                    if resource.get("type") not in [
                        "aws_instance",
                        "google_compute_instance",
                        "azurerm_virtual_machine",
                    ]:
                        continue

                    for instance in resource.get("instances", []):
                        attrs = instance.get("attributes", {})

                        # Get instance name from tags/labels (varies by cloud provider)
                        instance_name = ""
                        if "tags" in attrs:  # AWS
                            instance_name = attrs["tags"].get("Name", "").lower()
                        elif "labels" in attrs:  # GCP
                            instance_name = attrs["labels"].get("name", "").lower()
                        elif "name" in attrs:  # Azure or direct name
                            instance_name = attrs["name"].lower()

                        # Check if this instance matches our system
                        if system_name.lower() in instance_name:
                            ip_address: Any = attrs.get(ip_type)
                            if ip_address and isinstance(ip_address, str):
                                print(
                                    f"✓ Resolved {var_name}={ip_address} from infrastructure state"
                                )
                                return str(ip_address)

            except (json.JSONDecodeError, OSError, KeyError):
                # Silently continue to next state file
                continue

        return None

    def _wait_for_instance_initialization(
        self, terraform_outputs: dict[str, Any]
    ) -> bool:
        """
        Wait for all instances to be fully initialized and ready.

        Args:
            terraform_outputs: Dictionary containing terraform outputs with instance IPs

        Returns:
            True if all instances are ready, False if timeout or failure
        """
        import time

        # Parse instance information from terraform outputs
        # Flatten multinode systems into individual instances to wait for
        instances_to_check = []  # List of (system_name, node_idx, public_ip)

        # Check if we have the expected terraform output structure
        if "system_public_ips" in terraform_outputs:
            # New structure: system_public_ips = {"exasol": ["1.2.3.4"], "clickhouse": ["5.6.7.8"]}
            # or multinode: {"exasol": ["1.2.3.4", "1.2.3.5", "1.2.3.6"]}
            system_public_ips = terraform_outputs["system_public_ips"]
            if isinstance(system_public_ips, dict):
                for system_name, public_ip in system_public_ips.items():
                    # Handle both list and single IP (backward compatibility)
                    if isinstance(public_ip, list):
                        # List of IPs (single-node returns [ip], multinode returns [ip1, ip2, ...])
                        for idx, ip in enumerate(public_ip):
                            instances_to_check.append((system_name, idx, ip))
                    else:
                        # Single IP (backward compatibility)
                        instances_to_check.append((system_name, 0, public_ip))
            else:
                print(
                    f"Warning: system_public_ips is not a dict: {type(system_public_ips)}"
                )
        else:
            # Fallback: look for individual keys like "exasol_public_ip"
            for key, value in terraform_outputs.items():
                if key.endswith("_public_ip"):
                    system_name = key.replace("_public_ip", "")
                    instances_to_check.append((system_name, 0, value))

        if not instances_to_check:
            print("No instances found in terraform outputs")
            return False

        # Display useful instance information
        print("\n📋 Instance Information:")
        system_instance_ids = terraform_outputs.get("system_instance_ids", {})
        system_private_ips = terraform_outputs.get("system_private_ips", {})
        system_ssh_commands = terraform_outputs.get("system_ssh_commands", {})

        for system_name in {s for s, _, _ in instances_to_check}:
            instance_id = system_instance_ids.get(system_name, "unknown")
            private_ip = system_private_ips.get(system_name, "unknown")
            ssh_command = system_ssh_commands.get(system_name, "unknown")

            print(f"  🖥️  {system_name}:")
            print(f"     Instance ID: {instance_id}")
            # Format IPs nicely for multinode
            if isinstance(private_ip, list) and len(private_ip) > 1:
                print(f"     Nodes: {len(private_ip)}")
                for idx in range(len(private_ip)):
                    pub_ip = (
                        system_public_ips.get(system_name, [])[idx]
                        if isinstance(system_public_ips.get(system_name), list)
                        else "unknown"
                    )
                    priv_ip = private_ip[idx]
                    print(f"       Node {idx}: {pub_ip} ({priv_ip})")
            else:
                # Extract single values from lists if needed
                pub_ip = system_public_ips.get(system_name)
                if isinstance(pub_ip, list) and len(pub_ip) == 1:
                    pub_ip = pub_ip[0]
                priv_ip = (
                    private_ip[0]
                    if isinstance(private_ip, list) and len(private_ip) == 1
                    else private_ip
                )
                print(f"     Public IP:   {pub_ip}")
                print(f"     Private IP:  {priv_ip}")
                print(
                    f"     SSH:         {ssh_command if isinstance(ssh_command, str) else ssh_command[0] if isinstance(ssh_command, list) else 'unknown'}"
                )
            print()

        print(f"Waiting for {len(instances_to_check)} instance(s) to initialize...")

        max_wait_time = 900  # 15 minutes
        check_interval = 30  # Check every 30 seconds
        start_time = time.time()

        ready_instances = set()  # Set of (system_name, node_idx) tuples

        while time.time() - start_time < max_wait_time:
            for system_name, node_idx, public_ip in instances_to_check:
                instance_key = (system_name, node_idx)
                if instance_key in ready_instances:
                    continue  # Already confirmed ready

                if self._check_instance_ready(public_ip, system_name):
                    # Display node index for multinode systems
                    node_label = (
                        f"-node{node_idx}"
                        if any(
                            s == system_name and i != node_idx
                            for s, i, _ in instances_to_check
                        )
                        else ""
                    )
                    print(f"✅ {system_name}{node_label} instance ready ({public_ip})")
                    ready_instances.add(instance_key)
                else:
                    remaining_time = max_wait_time - (time.time() - start_time)
                    node_label = (
                        f"-node{node_idx}"
                        if any(
                            s == system_name and i != node_idx
                            for s, i, _ in instances_to_check
                        )
                        else ""
                    )
                    print(
                        f"⏳ {system_name}{node_label} still initializing... ({remaining_time:.0f}s remaining)"
                    )

            # Check if all instances are ready
            if len(ready_instances) == len(instances_to_check):
                print("\n🎉 All instances are ready and initialized!")
                return True

            time.sleep(check_interval)

        # Timeout reached
        failed_instances = []
        for system_name, node_idx, _public_ip in instances_to_check:
            if (system_name, node_idx) not in ready_instances:
                node_label = (
                    f"-node{node_idx}"
                    if any(
                        s == system_name and i != node_idx
                        for s, i, _ in instances_to_check
                    )
                    else ""
                )
                failed_instances.append(f"{system_name}{node_label}")
        print(
            f"✗ Timeout: {', '.join(failed_instances)} failed to initialize within {max_wait_time}s"
        )
        return False

    def _check_instance_ready(self, public_ip: str, system_name: str) -> bool:
        """
        Check if a specific instance is fully ready.

        Args:
            public_ip: Public IP address of the instance
            system_name: Name of the system (for SSH key selection)

        Returns:
            True if instance is ready, False otherwise
        """
        try:
            # Get environment config for this specific system
            _, env_config = get_environment_for_system(self.config, system_name)

            # Get SSH configuration from the system's environment
            ssh_key_path = env_config.get("ssh_private_key_path")
            if not ssh_key_path:
                # Fallback to helper that checks all cloud environments
                ssh_key_path = get_cloud_ssh_key_path(self.config)
            if not ssh_key_path:
                ssh_key_path = "~/.ssh/id_rsa"

            ssh_user = env_config.get("ssh_user", "ubuntu")

            # Expand tilde in SSH key path
            import os

            ssh_key_path = os.path.expanduser(ssh_key_path)

            # Test basic SSH connectivity
            ssh_test_result = safe_command(
                f'ssh -i "{ssh_key_path}" -o ConnectTimeout=10 -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "echo ssh_ready"',
                timeout=15,
            )
            if not ssh_test_result.get("success", False):
                print(f"  [{system_name}] SSH connectivity check failed")
                return False

            # Check for user data completion marker
            completion_check = safe_command(
                f'ssh -i "{ssh_key_path}" -o ConnectTimeout=10 -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "test -f /var/lib/cloud/instance/boot-finished && echo boot_finished"',
                timeout=15,
            )
            if not completion_check.get("success", False):
                print(f"  [{system_name}] Cloud-init boot not finished yet")
                return False

            # Check that essential tools are installed (created by user data)
            # Note: /data directory is now created by benchmark system classes, not user_data
            tools_check = safe_command(
                f'ssh -i "{ssh_key_path}" -o ConnectTimeout=10 -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "which docker && which python3 && echo tools_ready"',
                timeout=15,
            )
            if not tools_check.get("success", False):
                print(f"  [{system_name}] Essential tools not yet installed")
                return False

            # Check that Docker is running
            docker_check = safe_command(
                f'ssh -i "{ssh_key_path}" -o ConnectTimeout=10 -o StrictHostKeyChecking=no '
                f'{ssh_user}@{public_ip} "sudo systemctl is-active docker && echo docker_ready"',
                timeout=15,
            )
            if not docker_check.get("success", False):
                print(f"  [{system_name}] Docker service not yet active")
                return False

            return True

        except Exception as e:
            print(f"Error checking instance readiness: {e}")
            return False


class CloudInstanceManager:
    """Manages individual cloud instances for benchmarks."""

    def __init__(
        self,
        instance_info: dict[str, Any],
        ssh_private_key_path: str | None = None,
        ssh_user: str = "ubuntu",
        ssh_port: int = 22,
    ):
        self.instance_info = instance_info
        self.public_ip = instance_info.get("public_ip")
        self.private_ip = instance_info.get("private_ip")
        self.ssh_private_key_path = ssh_private_key_path
        self.ssh_user = ssh_user
        self.ssh_port = ssh_port

    def _get_ssh_command_prefix(self) -> str:
        """Get SSH command prefix with key and port if configured."""
        import os

        ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=5"

        if self.ssh_private_key_path:
            key_path = os.path.expanduser(self.ssh_private_key_path)
            ssh_opts += f" -i {key_path}"

        if self.ssh_port != 22:
            ssh_opts += f" -p {self.ssh_port}"

        return f"ssh {ssh_opts}"

    def wait_for_ssh(self, timeout: int = 300) -> bool:
        """Wait for SSH to be available on the instance."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            ssh_cmd = self._get_ssh_command_prefix()
            result = safe_command(
                f"{ssh_cmd} {self.ssh_user}@{self.public_ip} {shlex.quote('echo ready')}",
                timeout=10,
            )

            if result["success"]:
                return True

            time.sleep(10)

        return False

    def run_remote_command(
        self,
        command: str,
        timeout: int = 300,
        debug: bool = False,
        stream_callback: Callable[[str, str], None] | None = None,
    ) -> dict[str, Any]:
        """Run a command on the remote instance.

        Args:
            command: Command to execute on the remote instance
            timeout: Timeout in seconds (default: 300)
            debug: Enable debug logging
            stream_callback: Callback for streaming output (line, stream_name).
                Use this for real-time output handling and to add per-system
                tagging during parallel execution.

        Returns:
            Dictionary with success, stdout, stderr, returncode, elapsed_s, command
        """
        ssh_cmd = self._get_ssh_command_prefix()
        ssh_command = (
            f"{ssh_cmd} {self.ssh_user}@{self.public_ip} {shlex.quote(command)}"
        )

        # Use global debug state if no explicit debug parameter
        enable_debug = debug or is_debug_enabled()

        # Helper to route debug output through stream_callback if available
        # This avoids race conditions with redirect_stdout in parallel execution
        def debug_output(message: str) -> None:
            if stream_callback is not None:
                stream_callback(message, "stdout")
            else:
                print(message)

        if enable_debug:
            if timeout:
                debug_output(f"[DEBUG] Command ({timeout}s): {ssh_command}")
            else:
                debug_output(f"[DEBUG] Command: {ssh_command}")

        if stream_callback is None:
            result = safe_command(ssh_command, timeout=timeout)
        else:
            result = self._run_remote_command_streaming(
                ssh_command, timeout=timeout, stream_callback=stream_callback
            )

        if enable_debug:
            debug_output(f"[DEBUG] Command success: {result.get('success', False)}")
            # Only dump stdout/stderr if not using streaming callback
            # (streaming already printed output in real-time)
            if stream_callback is None:
                stdout = result.get("stdout", "")
                stderr = result.get("stderr", "")
                if stdout:
                    debug_output(f"[DEBUG] Stdout: {stdout}")
                if stderr:
                    debug_output(f"[DEBUG] Stderr: {stderr}")

        return result

    def _run_remote_command_streaming(
        self,
        ssh_command: str,
        timeout: int,
        stream_callback: Callable[[str, str], None],
    ) -> dict[str, Any]:
        """Execute SSH command while streaming stdout/stderr lines to callback."""
        start_time = time.time()

        try:
            process = subprocess.Popen(
                ssh_command,
                shell=True,  # nosec B602
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:  # pragma: no cover - defensive path
            elapsed = time.time() - start_time
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "returncode": -1,
                "elapsed_s": elapsed,
                "command": ssh_command,
            }

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def reader(pipe: Any, label: str, collector: list[str]) -> None:
            try:
                for raw_line in iter(pipe.readline, ""):
                    collector.append(raw_line)
                    clean_line = raw_line.rstrip("\r\n")
                    # Preserve blank lines so progress output renders correctly
                    try:
                        stream_callback(clean_line, label)
                    except Exception:
                        # Streaming output should be best-effort; ignore callback errors
                        pass
            finally:
                pipe.close()

        threads: list[threading.Thread] = []
        if process.stdout is not None:
            t = threading.Thread(
                target=reader, args=(process.stdout, "stdout", stdout_lines)
            )
            t.daemon = True
            t.start()
            threads.append(t)
        if process.stderr is not None:
            t = threading.Thread(
                target=reader, args=(process.stderr, "stderr", stderr_lines)
            )
            t.daemon = True
            t.start()
            threads.append(t)

        returncode: int
        timed_out = False
        try:
            returncode = process.wait(timeout=timeout if timeout else None)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            returncode = process.wait()
            timeout_message = f"Command timed out after {timeout}s"
            stderr_lines.append(timeout_message + "\n")
            stream_callback(timeout_message, "stderr")

        for thread in threads:
            thread.join()

        elapsed = time.time() - start_time

        return {
            "success": (returncode == 0) and not timed_out,
            "stdout": "".join(stdout_lines),
            "stderr": "".join(stderr_lines),
            "returncode": -1 if timed_out else returncode,
            "elapsed_s": elapsed,
            "command": ssh_command,
        }

    def copy_file_to_instance(self, local_path: Path, remote_path: str) -> bool:
        """Copy a file to the remote instance."""
        import os

        scp_opts = "-o StrictHostKeyChecking=no"

        if self.ssh_private_key_path:
            key_path = os.path.expanduser(self.ssh_private_key_path)
            scp_opts += f" -i {key_path}"

        if self.ssh_port != 22:
            scp_opts += f" -P {self.ssh_port}"

        scp_command = f"scp {scp_opts} {local_path} {self.ssh_user}@{self.public_ip}:{remote_path}"

        result = safe_command(scp_command, timeout=300)
        return bool(result.get("success", False))

    def copy_file_from_instance(self, remote_path: str, local_path: Path) -> bool:
        """Copy a file from the remote instance."""
        import os

        scp_opts = "-o StrictHostKeyChecking=no"

        if self.ssh_private_key_path:
            key_path = os.path.expanduser(self.ssh_private_key_path)
            scp_opts += f" -i {key_path}"

        if self.ssh_port != 22:
            scp_opts += f" -P {self.ssh_port}"

        scp_command = f"scp {scp_opts} {self.ssh_user}@{self.public_ip}:{remote_path} {local_path}"

        result = safe_command(scp_command, timeout=300)
        return bool(result.get("success", False))
