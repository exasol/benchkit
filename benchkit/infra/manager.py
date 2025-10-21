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

from ..debug import debug_log_command, debug_log_result, is_debug_enabled
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
        self.infra_dir = Path(f"infra/{self.provider}")

        if not self.infra_dir.exists():
            raise ValueError(f"Infrastructure directory not found: {self.infra_dir}")

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

    def get_infrastructure_ips(self) -> dict[str, dict[str, str]] | None:
        """
        Get public and private IPs for all systems in the infrastructure.

        Returns:
            Dictionary mapping system names to their IP addresses:
            {
                "system_name": {
                    "public_ip": "1.2.3.4",
                    "private_ip": "10.0.0.1"
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
                infra_ips[system_name] = {
                    "public_ip": public_ip,
                    "private_ip": private_ips.get(system_name, "-"),
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

    def _run_terraform_command_raw(
        self, command: str, args: list[Any] | None = None
    ) -> dict[str, Any]:
        """Run terraform command and return raw result without success interpretation."""
        args = args or []

        try:
            # Change to infrastructure directory
            import os

            original_cwd = os.getcwd()
            os.chdir(self.infra_dir)

            try:
                # Initialize terraform if needed
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
            # Change to infrastructure directory
            import os

            original_cwd = os.getcwd()
            os.chdir(self.infra_dir)

            try:
                # Initialize terraform if needed
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
        env_config = self.config.get("env", {})

        # Common variables
        tf_vars = {
            "region": env_config.get("region", "us-east-1"),
            "project_id": self.config.get("project_id", "benchmark"),
        }

        # Collect all required ports from the systems used in the benchmark
        all_required_ports = self._collect_required_ports()

        # Build generic systems configuration for Terraform
        instances_config = env_config.get("instances", {})
        if not instances_config:
            raise ValueError(
                "env.instances configuration is required for multi-system benchmarks"
            )

        # Get the actual systems that should be created (respects --systems filter)
        active_systems = {s["name"] for s in self.config.get("systems", [])}

        systems_tf = {}
        for system_name, system_config in instances_config.items():
            # Only include systems that are in the filtered systems list
            if system_name in active_systems:
                disk_config = system_config.get("disk", {})
                systems_tf[system_name] = {
                    "instance_type": system_config.get("instance_type", "m7i.4xlarge"),
                    "disk_size": disk_config.get("size_gb", 40),
                    "disk_type": disk_config.get("type", "gp3"),
                    "label": system_config.get("label", ""),
                }

        # Convert to JSON string for Terraform
        import json

        tf_vars["systems"] = json.dumps(systems_tf)
        tf_vars["required_ports"] = json.dumps(all_required_ports)

        # Add SSH key if provided
        ssh_key_name = env_config.get("ssh_key_name", "")
        if ssh_key_name:
            tf_vars["ssh_key_name"] = ssh_key_name

        # Add external access option (default false for security)
        tf_vars["allow_external_database_access"] = str(
            env_config.get("allow_external_database_access", False)
        ).lower()

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
        # Only provide required variables without validating full configuration
        tf_vars = {
            "project_id": self.config.get("project_id", "benchmark"),
            "region": self.config.get("env", {}).get("region", "us-east-1"),
            "systems": "{}",  # Empty systems for destroy
        }

        # Add SSH key if provided
        ssh_key_name = self.config.get("env", {}).get("ssh_key_name", "")
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

            original_cwd = os.getcwd()
            os.chdir(self.infra_dir)
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
        # Use terraform output to get instance info from the correct directory
        import os

        original_cwd = os.getcwd()
        os.chdir(self.infra_dir)

        try:
            result = safe_command("terraform output -json -no-color", timeout=30)
        finally:
            os.chdir(original_cwd)

        if result["success"]:
            try:
                import json

                outputs = json.loads(result["stdout"])

                # Extract generic system information from Terraform outputs
                system_data = {}

                instance_ids = outputs.get("system_instance_ids", {}).get("value", {})
                public_ips = outputs.get("system_public_ips", {}).get("value", {})
                private_ips = outputs.get("system_private_ips", {}).get("value", {})

                for system_name in instance_ids.keys():
                    system_data[system_name] = {
                        "instance_id": instance_ids.get(system_name),
                        "public_ip": public_ips.get(system_name),
                        "private_ip": private_ips.get(system_name),
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
    def resolve_ip_from_infrastructure(var_name: str, system_name: str) -> str | None:
        """
        Resolve IP address from infrastructure state files.

        This is a generic utility that checks various infrastructure state files
        to resolve IP addresses when environment variables are not set.

        Args:
            var_name: Variable name to resolve (e.g., "EXASOL_PUBLIC_IP")
            system_name: System name to match (e.g., "exasol", "clickhouse")

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

        # Look for infrastructure state files in standard locations
        state_locations = [
            Path("infra/aws/terraform.tfstate"),
            Path("infra/gcp/terraform.tfstate"),
            Path("infra/azure/terraform.tfstate"),
            Path("terraform/terraform.tfstate"),
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
        instances = {}

        # Check if we have the expected terraform output structure
        if "system_public_ips" in terraform_outputs:
            # New structure: system_public_ips = {"exasol": "1.2.3.4", "clickhouse": "5.6.7.8"}
            system_public_ips = terraform_outputs["system_public_ips"]
            if isinstance(system_public_ips, dict):
                instances = system_public_ips
            else:
                print(
                    f"Warning: system_public_ips is not a dict: {type(system_public_ips)}"
                )
        else:
            # Fallback: look for individual keys like "exasol_public_ip"
            for key, value in terraform_outputs.items():
                if key.endswith("_public_ip"):
                    system_name = key.replace("_public_ip", "")
                    instances[system_name] = value

        if not instances:
            print("No instances found in terraform outputs")
            return False

        # Display useful instance information
        print("\n📋 Instance Information:")
        system_instance_ids = terraform_outputs.get("system_instance_ids", {})
        system_private_ips = terraform_outputs.get("system_private_ips", {})
        system_ssh_commands = terraform_outputs.get("system_ssh_commands", {})

        for system_name, public_ip in instances.items():
            instance_id = system_instance_ids.get(system_name, "unknown")
            private_ip = system_private_ips.get(system_name, "unknown")
            ssh_command = system_ssh_commands.get(
                system_name, f"ssh ubuntu@{public_ip}"
            )

            print(f"  🖥️  {system_name}:")
            print(f"     Instance ID: {instance_id}")
            print(f"     Public IP:   {public_ip}")
            print(f"     Private IP:  {private_ip}")
            print(f"     SSH:         {ssh_command}")
            print()

        print(f"Waiting for {len(instances)} instance(s) to initialize...")

        max_wait_time = 900  # 15 minutes
        check_interval = 30  # Check every 30 seconds
        start_time = time.time()

        ready_instances = set()

        while time.time() - start_time < max_wait_time:
            for system_name, public_ip in instances.items():
                if system_name in ready_instances:
                    continue  # Already confirmed ready

                if self._check_instance_ready(public_ip, system_name):
                    print(f"✅ {system_name} instance ready ({public_ip})")
                    ready_instances.add(system_name)
                else:
                    remaining_time = max_wait_time - (time.time() - start_time)
                    print(
                        f"⏳ {system_name} still initializing... ({remaining_time:.0f}s remaining)"
                    )

            # Check if all instances are ready
            if len(ready_instances) == len(instances):
                print("\n🎉 All instances are ready and initialized!")
                return True

            time.sleep(check_interval)

        # Timeout reached
        failed_instances = set(instances.keys()) - ready_instances
        print(
            f"✗ Timeout: {failed_instances} failed to initialize within {max_wait_time}s"
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
            # Get SSH configuration
            ssh_config = self.config.get("env", {})
            ssh_key_path = ssh_config.get("ssh_private_key_path", "~/.ssh/id_rsa")
            ssh_user = ssh_config.get("ssh_user", "ubuntu")

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
        self, instance_info: dict[str, Any], ssh_private_key_path: str | None = None
    ):
        self.instance_info = instance_info
        self.public_ip = instance_info.get("public_ip")
        self.private_ip = instance_info.get("private_ip")
        self.ssh_private_key_path = ssh_private_key_path

    def _get_ssh_command_prefix(self) -> str:
        """Get SSH command prefix with key if configured."""
        ssh_opts = "-o StrictHostKeyChecking=no -o ConnectTimeout=5"

        if self.ssh_private_key_path:
            # Expand ~ to home directory
            import os

            key_path = os.path.expanduser(self.ssh_private_key_path)
            ssh_opts += f" -i {key_path}"

        return f"ssh {ssh_opts}"

    def wait_for_ssh(self, timeout: int = 300) -> bool:
        """Wait for SSH to be available on the instance."""
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            ssh_cmd = self._get_ssh_command_prefix()
            result = safe_command(
                f"{ssh_cmd} ubuntu@{self.public_ip} {shlex.quote('echo ready')}",
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
        """Run a command on the remote instance."""
        ssh_cmd = self._get_ssh_command_prefix()
        ssh_command = f"{ssh_cmd} ubuntu@{self.public_ip} {shlex.quote(command)}"

        # Use global debug state if no explicit debug parameter
        enable_debug = debug or is_debug_enabled()

        if enable_debug:
            debug_log_command(ssh_command, timeout)

        if stream_callback is None:
            result = safe_command(ssh_command, timeout=timeout)
        else:
            result = self._run_remote_command_streaming(
                ssh_command, timeout=timeout, stream_callback=stream_callback
            )

        if enable_debug:
            debug_log_result(
                result.get("success", False),
                result.get("stdout", ""),
                result.get("stderr", ""),
            )

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
                shell=True,
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
        scp_opts = "-o StrictHostKeyChecking=no"

        if self.ssh_private_key_path:
            import os

            key_path = os.path.expanduser(self.ssh_private_key_path)
            scp_opts += f" -i {key_path}"

        scp_command = (
            f"scp {scp_opts} {local_path} ubuntu@{self.public_ip}:{remote_path}"
        )

        result = safe_command(scp_command, timeout=300)
        return bool(result.get("success", False))

    def copy_file_from_instance(self, remote_path: str, local_path: Path) -> bool:
        """Copy a file from the remote instance."""
        scp_opts = "-o StrictHostKeyChecking=no"

        if self.ssh_private_key_path:
            import os

            key_path = os.path.expanduser(self.ssh_private_key_path)
            scp_opts += f" -i {key_path}"

        scp_command = (
            f"scp {scp_opts} ubuntu@{self.public_ip}:{remote_path} {local_path}"
        )

        result = safe_command(scp_command, timeout=300)
        return bool(result.get("success", False))
