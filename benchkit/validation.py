"""Pre-flight validation for benchkit operations.

This module provides comprehensive validation for SSH keys, AWS credentials,
and configuration before infrastructure deployment or benchmark execution.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rich.console import Console


class CheckSeverity(Enum):
    """Severity level for check results."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str  # e.g., "SSH Key Exists"
    passed: bool  # True if check passed
    severity: CheckSeverity  # ERROR, WARNING, INFO
    message: str  # Human-readable message
    details: str | None = None  # Additional details/context
    suggestion: str | None = None  # Actionable fix suggestion

    @property
    def symbol(self) -> str:
        """Return check symbol for display."""
        if self.passed:
            return "[green]\u2713[/green]"
        elif self.severity == CheckSeverity.ERROR:
            return "[red]\u2717[/red]"
        elif self.severity == CheckSeverity.WARNING:
            return "[yellow]\u26a0[/yellow]"
        else:
            return "[blue]\u2139[/blue]"


@dataclass
class ValidationReport:
    """Aggregated results of all validation checks."""

    checks: list[CheckResult] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Return True if any check failed with ERROR severity."""
        return any(
            not c.passed and c.severity == CheckSeverity.ERROR for c in self.checks
        )

    @property
    def has_warnings(self) -> bool:
        """Return True if any check failed with WARNING severity."""
        return any(
            not c.passed and c.severity == CheckSeverity.WARNING for c in self.checks
        )

    @property
    def passed_count(self) -> int:
        """Return count of passed checks."""
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        """Return count of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    def add(self, result: CheckResult) -> None:
        """Add a check result to the report."""
        self.checks.append(result)

    def merge(self, other: ValidationReport) -> None:
        """Merge another report's checks into this one."""
        self.checks.extend(other.checks)


# =============================================================================
# SSH Key Validation Functions
# =============================================================================


def check_ssh_key_file_exists(key_path: str) -> CheckResult:
    """
    Check if SSH private key file exists at the specified path.

    Args:
        key_path: Path to the SSH private key (supports ~ expansion)

    Returns:
        CheckResult with pass/fail status and details
    """
    expanded_path = Path(key_path).expanduser()

    if not expanded_path.exists():
        return CheckResult(
            name="SSH key file exists",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"SSH private key not found: {key_path}",
            details=f"Expanded path: {expanded_path}",
            suggestion="Ensure the SSH key file exists at the specified path",
        )

    if not expanded_path.is_file():
        return CheckResult(
            name="SSH key file exists",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Path is not a file: {key_path}",
            details=f"Expanded path: {expanded_path}",
        )

    return CheckResult(
        name="SSH key file exists",
        passed=True,
        severity=CheckSeverity.INFO,
        message=f"SSH key found: {expanded_path}",
    )


def check_ssh_key_permissions(key_path: str) -> CheckResult:
    """
    Check if SSH private key has correct permissions (600 or 400).

    Args:
        key_path: Path to the SSH private key

    Returns:
        CheckResult with pass/fail and chmod suggestion if needed
    """
    expanded_path = Path(key_path).expanduser()

    if not expanded_path.exists():
        return CheckResult(
            name="SSH key permissions",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Cannot check permissions: file does not exist",
        )

    stat_info = expanded_path.stat()
    mode = stat_info.st_mode & 0o777  # Get permission bits

    if mode in (0o600, 0o400):
        return CheckResult(
            name="SSH key permissions",
            passed=True,
            severity=CheckSeverity.INFO,
            message=f"Permissions OK: {oct(mode)}",
        )
    else:
        return CheckResult(
            name="SSH key permissions",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Incorrect permissions: {oct(mode)}",
            details="Expected: 0o600 or 0o400",
            suggestion=f"chmod 600 {expanded_path}",
        )


def check_ssh_key_format(key_path: str) -> CheckResult:
    """
    Check if file is a valid SSH private key format.

    Args:
        key_path: Path to the SSH private key

    Returns:
        CheckResult indicating if key format is valid
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        return CheckResult(
            name="SSH key format",
            passed=True,  # Don't fail if cryptography not installed
            severity=CheckSeverity.WARNING,
            message="Cannot verify key format: cryptography library not installed",
            suggestion="pip install cryptography",
        )

    expanded_path = Path(key_path).expanduser()

    if not expanded_path.exists():
        return CheckResult(
            name="SSH key format",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Cannot check format: file does not exist",
        )

    try:
        key_data = expanded_path.read_bytes()

        # Try loading as OpenSSH format first (newer format)
        private_key: Any = None
        try:
            private_key = serialization.load_ssh_private_key(
                key_data, password=None, backend=default_backend()
            )
        except (ValueError, TypeError):
            # Fall back to PEM format (traditional format)
            try:
                private_key = serialization.load_pem_private_key(
                    key_data, password=None, backend=default_backend()
                )
            except TypeError:
                # Password required - still a valid key format
                return CheckResult(
                    name="SSH key format",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="Valid SSH key format (passphrase protected)",
                )

        # Determine key type and size
        key_type = type(private_key).__name__
        key_info = key_type.replace("_", " ").replace("PrivateKey", "").strip()

        # Get key size if available
        if hasattr(private_key, "key_size"):
            key_info += f" {private_key.key_size}-bit"

        return CheckResult(
            name="SSH key format",
            passed=True,
            severity=CheckSeverity.INFO,
            message=f"Valid SSH key: {key_info}",
        )

    except Exception as e:
        return CheckResult(
            name="SSH key format",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Invalid SSH key format: {e}",
            suggestion="Ensure the file is a valid SSH private key",
        )


def check_ssh_key_readable(key_path: str) -> CheckResult:
    """
    Check if SSH key file is readable and detect passphrase protection.

    Keys with passphrases will show a warning, not an error,
    as ssh-agent can handle them.

    Args:
        key_path: Path to the SSH private key

    Returns:
        CheckResult with warning if passphrase detected
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        return CheckResult(
            name="SSH key readable",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Skipped: cryptography library not installed",
        )

    expanded_path = Path(key_path).expanduser()

    if not expanded_path.exists():
        return CheckResult(
            name="SSH key readable",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Cannot read key: file does not exist",
        )

    try:
        key_data = expanded_path.read_bytes()

        # Try loading without passphrase
        try:
            serialization.load_ssh_private_key(
                key_data, password=None, backend=default_backend()
            )
            return CheckResult(
                name="SSH key readable",
                passed=True,
                severity=CheckSeverity.INFO,
                message="Key is readable without passphrase",
            )
        except (ValueError, TypeError):
            pass

        try:
            serialization.load_pem_private_key(
                key_data, password=None, backend=default_backend()
            )
            return CheckResult(
                name="SSH key readable",
                passed=True,
                severity=CheckSeverity.INFO,
                message="Key is readable without passphrase",
            )
        except TypeError:
            # Password required
            return CheckResult(
                name="SSH key readable",
                passed=True,  # Still passes, just with warning
                severity=CheckSeverity.WARNING,
                message="Key requires passphrase",
                details="Ensure ssh-agent is running and key is added",
                suggestion=f"eval $(ssh-agent) && ssh-add {expanded_path}",
            )
        except ValueError:
            pass

        return CheckResult(
            name="SSH key readable",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Key format recognized",
        )

    except PermissionError:
        return CheckResult(
            name="SSH key readable",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Permission denied reading key file",
            suggestion=f"Check file permissions: ls -la {expanded_path}",
        )
    except Exception as e:
        return CheckResult(
            name="SSH key readable",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Error reading key file: {e}",
        )


# =============================================================================
# AWS Validation Functions
# =============================================================================


def check_aws_credentials() -> CheckResult:
    """
    Check if AWS credentials are configured and valid.

    Uses STS get-caller-identity for verification.

    Returns:
        CheckResult with IAM user/role information on success
    """
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        return CheckResult(
            name="AWS credentials",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="boto3 not installed",
            suggestion="pip install boto3",
        )

    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        arn = identity.get("Arn", "Unknown")
        account = identity.get("Account", "Unknown")

        return CheckResult(
            name="AWS credentials",
            passed=True,
            severity=CheckSeverity.INFO,
            message="AWS credentials configured",
            details=f"User: {arn}\nAccount: {account}",
        )
    except NoCredentialsError:
        return CheckResult(
            name="AWS credentials",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="No AWS credentials configured",
            suggestion="Run: aws configure\nOr set: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY",
        )
    except ClientError as e:
        return CheckResult(
            name="AWS credentials",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"AWS credentials error: {e}",
        )


def check_aws_ssh_key_exists(key_name: str, region: str | None = None) -> CheckResult:
    """
    Check if SSH key pair exists on AWS.

    Args:
        key_name: Name of the AWS key pair
        region: AWS region (uses default if not specified)

    Returns:
        CheckResult with key pair ID and fingerprint on success
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return CheckResult(
            name="AWS SSH key exists",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="boto3 not installed",
            suggestion="pip install boto3",
        )

    try:
        ec2 = boto3.client("ec2", region_name=region) if region else boto3.client("ec2")
        response = ec2.describe_key_pairs(KeyNames=[key_name])

        if response["KeyPairs"]:
            key_info = response["KeyPairs"][0]
            key_pair_id = key_info.get("KeyPairId", "N/A")
            fingerprint = key_info.get("KeyFingerprint", "N/A")

            return CheckResult(
                name="AWS SSH key exists",
                passed=True,
                severity=CheckSeverity.INFO,
                message=f"SSH key '{key_name}' found on AWS",
                details=f"KeyPairId: {key_pair_id}\nFingerprint: {fingerprint}",
            )
        else:
            return CheckResult(
                name="AWS SSH key exists",
                passed=False,
                severity=CheckSeverity.ERROR,
                message=f"SSH key '{key_name}' not found on AWS",
                suggestion=f"aws ec2 create-key-pair --key-name {key_name}",
            )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "InvalidKeyPair.NotFound":
            return CheckResult(
                name="AWS SSH key exists",
                passed=False,
                severity=CheckSeverity.ERROR,
                message=f"SSH key '{key_name}' not found on AWS",
                suggestion=f"aws ec2 create-key-pair --key-name {key_name}",
            )
        else:
            return CheckResult(
                name="AWS SSH key exists",
                passed=False,
                severity=CheckSeverity.ERROR,
                message=f"Error checking AWS SSH key: {e}",
            )


def _calculate_key_fingerprints(key_path: Path) -> dict[str, str] | None:
    """
    Calculate SSH key fingerprints from a private key file.

    Returns dict with 'md5', 'sha1', 'sha256', 'sha256_openssh' fingerprints.
    AWS uses SHA-1 for keys created via create-key-pair,
    and MD5 for keys imported via import-key-pair.
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
    except ImportError:
        return None

    try:
        key_data = key_path.read_bytes()

        # Try loading as OpenSSH format first
        private_key: Any = None
        try:
            private_key = serialization.load_ssh_private_key(
                key_data, password=None, backend=default_backend()
            )
        except (ValueError, TypeError):
            # Fall back to PEM format
            private_key = serialization.load_pem_private_key(
                key_data, password=None, backend=default_backend()
            )

        # Extract public key
        public_key = private_key.public_key()

        # Get DER format for fingerprint calculation
        der_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        # Get OpenSSH format
        openssh_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

        # OpenSSH format includes key type prefix - extract key data
        openssh_parts = openssh_bytes.split()
        if len(openssh_parts) >= 2:
            openssh_key_data = base64.b64decode(openssh_parts[1])
        else:
            openssh_key_data = openssh_bytes

        # Calculate fingerprints (MD5/SHA1 used for certificate identification, not security)
        md5_hash = hashlib.md5(der_bytes, usedforsecurity=False).hexdigest()
        md5_fingerprint = ":".join(
            md5_hash[i : i + 2] for i in range(0, len(md5_hash), 2)
        )

        sha1_hash = hashlib.sha1(der_bytes, usedforsecurity=False).hexdigest()
        sha1_fingerprint = ":".join(
            sha1_hash[i : i + 2] for i in range(0, len(sha1_hash), 2)
        )

        sha256_der_hash = hashlib.sha256(der_bytes).digest()
        sha256_der_fingerprint = base64.b64encode(sha256_der_hash).decode("ascii")

        sha256_openssh_hash = hashlib.sha256(openssh_key_data).digest()
        sha256_openssh_fingerprint = base64.b64encode(sha256_openssh_hash).decode(
            "ascii"
        )

        return {
            "md5": md5_fingerprint,
            "sha1": sha1_fingerprint,
            "sha256": sha256_der_fingerprint,
            "sha256_openssh": sha256_openssh_fingerprint,
        }
    except Exception:
        return None


def check_aws_ssh_key_fingerprint_match(
    local_key_path: str, key_name: str, region: str | None = None
) -> CheckResult:
    """
    Verify that local SSH key matches AWS key pair fingerprint.

    Args:
        local_key_path: Path to local private key file
        key_name: AWS key pair name
        region: AWS region

    Returns:
        CheckResult with fingerprint comparison details
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="boto3 not installed",
            suggestion="pip install boto3",
        )

    expanded_path = Path(local_key_path).expanduser()

    # Get AWS fingerprint
    try:
        ec2 = boto3.client("ec2", region_name=region) if region else boto3.client("ec2")
        response = ec2.describe_key_pairs(KeyNames=[key_name])

        if not response["KeyPairs"]:
            return CheckResult(
                name="SSH key fingerprint match",
                passed=False,
                severity=CheckSeverity.ERROR,
                message=f"AWS key pair '{key_name}' not found",
            )

        aws_fingerprint = response["KeyPairs"][0].get("KeyFingerprint", "")

    except ClientError as e:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Error getting AWS key fingerprint: {e}",
        )

    if not aws_fingerprint or aws_fingerprint == "N/A":
        return CheckResult(
            name="SSH key fingerprint match",
            passed=True,
            severity=CheckSeverity.WARNING,
            message="Cannot verify: AWS fingerprint not available",
        )

    # Calculate local fingerprints
    local_fingerprints = _calculate_key_fingerprints(expanded_path)

    if not local_fingerprints:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=False,
            severity=CheckSeverity.WARNING,
            message="Cannot calculate local key fingerprint",
            details="cryptography library may not be installed or key has passphrase",
        )

    # Check if any fingerprint matches
    if aws_fingerprint == local_fingerprints["md5"]:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Fingerprint match verified (MD5)",
        )
    elif aws_fingerprint == local_fingerprints["sha1"]:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Fingerprint match verified (SHA-1)",
        )
    elif aws_fingerprint == local_fingerprints["sha256"]:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Fingerprint match verified (SHA-256)",
        )
    elif aws_fingerprint == local_fingerprints["sha256_openssh"]:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Fingerprint match verified (SHA-256 OpenSSH)",
        )
    else:
        return CheckResult(
            name="SSH key fingerprint match",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Fingerprint mismatch!",
            details=(
                f"AWS: {aws_fingerprint}\n"
                f"Local MD5: {local_fingerprints['md5']}\n"
                f"Local SHA-1: {local_fingerprints['sha1']}"
            ),
            suggestion="Ensure you're using the correct private key file for this AWS key pair",
        )


def check_aws_permissions() -> CheckResult:
    """
    Check required AWS permissions for infrastructure operations.

    Uses DryRun operations to test permissions without creating resources.

    Returns:
        CheckResult with list of verified/missing permissions
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        return CheckResult(
            name="AWS permissions",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="boto3 not installed",
            suggestion="pip install boto3",
        )

    required_permissions = [
        ("describe_images", "DescribeImages"),
        ("describe_availability_zones", "DescribeAvailabilityZones"),
        ("describe_instances", "DescribeInstances"),
    ]

    passed_permissions = []
    failed_permissions = []

    try:
        ec2 = boto3.client("ec2")

        for method, action in required_permissions:
            try:
                if method == "describe_images":
                    ec2.describe_images(MaxResults=1, DryRun=True)
                elif method == "describe_availability_zones":
                    ec2.describe_availability_zones(DryRun=True)
                elif method == "describe_instances":
                    ec2.describe_instances(MaxResults=1, DryRun=True)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "DryRunOperation":
                    passed_permissions.append(action)
                elif error_code == "UnauthorizedOperation":
                    failed_permissions.append(action)
                else:
                    # Unknown error, treat as warning
                    pass

        if failed_permissions:
            return CheckResult(
                name="AWS permissions",
                passed=False,
                severity=CheckSeverity.ERROR,
                message="Missing required AWS permissions",
                details=f"Missing: {', '.join(failed_permissions)}",
                suggestion="Contact your AWS administrator to grant EC2 permissions",
            )
        elif passed_permissions:
            return CheckResult(
                name="AWS permissions",
                passed=True,
                severity=CheckSeverity.INFO,
                message="AWS permissions verified",
                details=f"Verified: {', '.join(passed_permissions)}",
            )
        else:
            return CheckResult(
                name="AWS permissions",
                passed=True,
                severity=CheckSeverity.WARNING,
                message="Could not verify AWS permissions",
                details="DryRun operations returned unexpected results",
            )

    except Exception as e:
        return CheckResult(
            name="AWS permissions",
            passed=False,
            severity=CheckSeverity.ERROR,
            message=f"Error checking AWS permissions: {e}",
        )


# =============================================================================
# Main Validator Class
# =============================================================================


class PreflightChecker:
    """
    Coordinates pre-flight validation checks for benchkit operations.

    Supports two modes:
    1. Local validation only (skip_aws_checks=True): SSH file checks without AWS API calls
    2. Full validation: SSH file + AWS API checks
    """

    def __init__(
        self,
        config: dict[str, Any],
        skip_aws_checks: bool = False,
        console: Console | None = None,
    ):
        """
        Initialize the pre-flight checker.

        Args:
            config: Loaded benchmark configuration dictionary
            skip_aws_checks: If True, skip all AWS API calls
            console: Rich console for formatted output (optional)
        """
        self.config = config
        self.skip_aws_checks = skip_aws_checks
        self.console = console

    def _get_env_config(self) -> dict[str, Any]:
        """Get environment configuration.

        Handles both legacy 'env' and multi-environment 'environments' configs.
        Returns the first cloud/remote environment config found, or the default env.
        """
        from .common.cli_helpers import get_all_environments
        from .common.enums import EnvironmentMode

        # First check legacy env config
        env = self.config.get("env")
        if env and isinstance(env, dict):
            return dict(env)

        # Check environments config - find first cloud or remote environment
        environments = get_all_environments(self.config)
        for _env_name, env_cfg in environments.items():
            mode = env_cfg.get("mode", EnvironmentMode.LOCAL.value)
            if EnvironmentMode.requires_ssh(str(mode)):
                return dict(env_cfg)

        # Return first environment if no cloud/remote providers found
        if environments:
            return dict(next(iter(environments.values())))

        return {}

    def _get_mode(self) -> str:
        """Get deployment mode.

        Checks explicit mode in env config first, then falls back to
        checking cloud providers from systems configuration.
        Returns 'local' if no cloud/remote mode is configured.
        """
        # First check explicit mode in env config
        env_config = self._get_env_config()
        explicit_mode = env_config.get("mode")
        if explicit_mode and explicit_mode != "local":
            return str(explicit_mode)

        # Fall back to checking cloud providers from systems
        from .common.cli_helpers import get_first_cloud_provider

        provider = get_first_cloud_provider(self.config)
        return provider if provider else "local"

    def validate_ssh_keys(self) -> ValidationReport:
        """
        Run all SSH key validation checks.

        Checks performed:
        1. File exists at ssh_private_key_path
        2. File permissions are 600 or 400
        3. File is a valid SSH key format
        4. File is readable (passphrase warning if applicable)

        Returns:
            ValidationReport with all SSH key check results
        """
        report = ValidationReport()
        env_config = self._get_env_config()

        ssh_private_key_path = env_config.get("ssh_private_key_path")

        if not ssh_private_key_path:
            report.add(
                CheckResult(
                    name="SSH key configuration",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="ssh_private_key_path not configured",
                    details="Required for cloud deployments",
                    suggestion="Add env.ssh_private_key_path to your config",
                )
            )
            return report

        # Run all SSH key checks
        report.add(check_ssh_key_file_exists(ssh_private_key_path))
        report.add(check_ssh_key_permissions(ssh_private_key_path))
        report.add(check_ssh_key_format(ssh_private_key_path))
        report.add(check_ssh_key_readable(ssh_private_key_path))

        return report

    def validate_cloud_environment(self) -> ValidationReport:
        """
        Run cloud provider environment validation checks.

        Dispatches to provider-specific validation based on env.mode:
        - aws: AWS credentials, SSH key pair, fingerprint match
        - stackit: Project ID, image ID, availability zone, SSH public key, auth
        - Others: INFO stub noting validation is not yet implemented

        Returns:
            ValidationReport with all cloud provider check results
        """
        mode = self._get_mode()
        env_config = self._get_env_config()

        if mode == "aws":
            return self._validate_aws_environment(env_config)
        elif mode == "stackit":
            return self._validate_stackit_environment(env_config)
        else:
            from .common.enums import EnvironmentMode

            report = ValidationReport()
            if EnvironmentMode.is_cloud_provider(mode):
                report.add(
                    CheckResult(
                        name=f"{mode.upper()} validation",
                        passed=True,
                        severity=CheckSeverity.INFO,
                        message=f"{mode.upper()}-specific validation not yet implemented",
                        details="SSH key file checks still apply",
                    )
                )
            return report

    def _validate_aws_environment(self, env_config: dict[str, Any]) -> ValidationReport:
        """Run AWS-specific environment validation checks."""
        report = ValidationReport()

        if self.skip_aws_checks:
            report.add(
                CheckResult(
                    name="AWS checks",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="AWS checks skipped (--skip-aws-check)",
                )
            )
            return report

        # Check AWS credentials
        report.add(check_aws_credentials())

        # Check SSH key on AWS
        ssh_key_name = env_config.get("ssh_key_name")
        region = env_config.get("region")

        if not ssh_key_name:
            report.add(
                CheckResult(
                    name="AWS SSH key configuration",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="ssh_key_name not configured",
                    suggestion="Add env.ssh_key_name to your config",
                )
            )
        else:
            report.add(check_aws_ssh_key_exists(ssh_key_name, region))

            # Check fingerprint match
            ssh_private_key_path = env_config.get("ssh_private_key_path")
            if ssh_private_key_path:
                report.add(
                    check_aws_ssh_key_fingerprint_match(
                        ssh_private_key_path, ssh_key_name, region
                    )
                )

        return report

    def _validate_stackit_environment(
        self, env_config: dict[str, Any]
    ) -> ValidationReport:
        """Run STACKIT-specific environment validation checks.

        Checks:
        1. stackit_project_id present and valid UUID
        2. stackit_image_id present and valid UUID
        3. availability_zone present and matches pattern (e.g. eu01-1)
        4. ssh_public_key_path file exists
        5. Authentication: STACKIT_SERVICE_ACCOUNT_KEY_PATH or
           STACKIT_SERVICE_ACCOUNT_TOKEN env var set
        """
        import os
        import re

        report = ValidationReport()
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )

        # 1. Project ID
        project_id = env_config.get("stackit_project_id", "")
        if not project_id:
            report.add(
                CheckResult(
                    name="STACKIT project ID",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="stackit_project_id not configured",
                    suggestion="Add env.stackit_project_id (UUID) to your config",
                )
            )
        elif not uuid_pattern.match(project_id):
            report.add(
                CheckResult(
                    name="STACKIT project ID",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message=f"stackit_project_id is not a valid UUID: {project_id}",
                    suggestion="Use a valid UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                )
            )
        else:
            report.add(
                CheckResult(
                    name="STACKIT project ID",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message=f"Project ID configured: {project_id[:8]}...",
                )
            )

        # 2. Image ID
        image_id = env_config.get("stackit_image_id", "")
        if not image_id:
            report.add(
                CheckResult(
                    name="STACKIT image ID",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="stackit_image_id not configured",
                    suggestion="Add env.stackit_image_id (UUID) to your config",
                )
            )
        elif not uuid_pattern.match(image_id):
            report.add(
                CheckResult(
                    name="STACKIT image ID",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message=f"stackit_image_id is not a valid UUID: {image_id}",
                    suggestion="Use a valid UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                )
            )
        else:
            report.add(
                CheckResult(
                    name="STACKIT image ID",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message=f"Image ID configured: {image_id[:8]}...",
                )
            )

        # 3. Availability zone
        az = env_config.get("stackit_availability_zone", "")
        az_pattern = re.compile(r"^[a-z]{2}\d{2}-\d$")
        if not az:
            report.add(
                CheckResult(
                    name="STACKIT availability zone",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="stackit_availability_zone not configured",
                    suggestion="Add env.stackit_availability_zone (e.g. eu01-1) to your config",
                )
            )
        elif not az_pattern.match(az):
            report.add(
                CheckResult(
                    name="STACKIT availability zone",
                    passed=False,
                    severity=CheckSeverity.WARNING,
                    message=f"Unusual availability zone format: {az}",
                    details="Expected pattern like eu01-1",
                )
            )
        else:
            report.add(
                CheckResult(
                    name="STACKIT availability zone",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message=f"Availability zone: {az}",
                )
            )

        # 4. SSH public key file
        ssh_public_key_path = env_config.get("ssh_public_key_path", "")
        if not ssh_public_key_path:
            report.add(
                CheckResult(
                    name="STACKIT SSH public key",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="ssh_public_key_path not configured",
                    suggestion="Add env.ssh_public_key_path to your config",
                )
            )
        elif not Path(ssh_public_key_path).expanduser().exists():
            report.add(
                CheckResult(
                    name="STACKIT SSH public key",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message=f"SSH public key file not found: {ssh_public_key_path}",
                    suggestion="Create the key or update ssh_public_key_path in config",
                )
            )
        else:
            report.add(
                CheckResult(
                    name="STACKIT SSH public key",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message=f"SSH public key found: {ssh_public_key_path}",
                )
            )

        # 5. Authentication
        key_path_env = os.environ.get("STACKIT_SERVICE_ACCOUNT_KEY_PATH", "")
        token_env = os.environ.get("STACKIT_SERVICE_ACCOUNT_TOKEN", "")

        if key_path_env and Path(key_path_env).exists():
            report.add(
                CheckResult(
                    name="STACKIT authentication",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="Authenticated via STACKIT_SERVICE_ACCOUNT_KEY_PATH",
                )
            )
        elif key_path_env and not Path(key_path_env).exists():
            report.add(
                CheckResult(
                    name="STACKIT authentication",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message=f"STACKIT_SERVICE_ACCOUNT_KEY_PATH file not found: {key_path_env}",
                    suggestion="Check the file path in STACKIT_SERVICE_ACCOUNT_KEY_PATH",
                )
            )
        elif token_env:
            report.add(
                CheckResult(
                    name="STACKIT authentication",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="Authenticated via STACKIT_SERVICE_ACCOUNT_TOKEN",
                )
            )
        else:
            report.add(
                CheckResult(
                    name="STACKIT authentication",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="No STACKIT authentication configured",
                    suggestion=(
                        "Set STACKIT_SERVICE_ACCOUNT_KEY_PATH (path to JSON key file) "
                        "or STACKIT_SERVICE_ACCOUNT_TOKEN environment variable"
                    ),
                )
            )

        return report

    def validate_aws_permissions(self) -> ValidationReport:
        """
        Validate AWS permissions for infrastructure operations.

        Returns:
            ValidationReport with AWS permission check results
        """
        report = ValidationReport()
        mode = self._get_mode()

        if mode != "aws" or self.skip_aws_checks:
            return report

        report.add(check_aws_permissions())
        return report

    def run_check_command_validation(self) -> ValidationReport:
        """
        Run validations appropriate for 'benchkit check' command.

        For cloud modes (aws/gcp/azure):
        - SSH key file validations
        - AWS key existence (unless skip_aws_checks)

        For remote mode:
        - SSH key file validations only (no cloud provider checks)
        - Node configuration summary

        For local mode:
        - No additional validation needed

        Returns:
            Combined ValidationReport
        """
        report = ValidationReport()
        mode = self._get_mode()

        if mode == "local":
            report.add(
                CheckResult(
                    name="Mode check",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="Local mode: SSH key checks not required",
                )
            )
            return report

        # Cloud and remote modes: validate SSH keys
        ssh_report = self.validate_ssh_keys()
        report.merge(ssh_report)

        if mode == "remote":
            # Remote mode: validate node configuration
            remote_report = self.validate_remote_config()
            report.merge(remote_report)
        else:
            # Cloud provider checks (AWS, STACKIT, etc.)
            cloud_report = self.validate_cloud_environment()
            report.merge(cloud_report)

        return report

    def validate_remote_config(self) -> ValidationReport:
        """
        Validate remote mode configuration.

        Checks:
        - Nodes are configured
        - Node count per system

        Returns:
            ValidationReport with remote config check results
        """
        report = ValidationReport()
        env_config = self._get_env_config()

        nodes = env_config.get("nodes", {})
        if not nodes:
            report.add(
                CheckResult(
                    name="Remote nodes",
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message="No nodes configured for remote mode",
                    suggestion="Add nodes with public_ip to your environment config",
                )
            )
            return report

        total_nodes = 0
        for _system_name, node_info in nodes.items():
            if isinstance(node_info, list):
                node_count = len(node_info)
            else:
                node_count = 1
            total_nodes += node_count

        report.add(
            CheckResult(
                name="Remote nodes",
                passed=True,
                severity=CheckSeverity.INFO,
                message=f"{len(nodes)} system(s), {total_nodes} node(s) configured",
                details=", ".join(
                    f"{name}: {len(info) if isinstance(info, list) else 1} node(s)"
                    for name, info in nodes.items()
                ),
            )
        )

        return report

    def run_infra_deploy_validation(self) -> ValidationReport:
        """
        Run full validations for 'benchkit infra deploy/apply' command.

        All checks from run_check_command_validation plus:
        - AWS permissions validation (cloud modes only, skipped for remote)

        Returns:
            Combined ValidationReport
        """
        report = self.run_check_command_validation()

        # Additional permission checks for infra deploy (AWS only)
        mode = self._get_mode()
        if mode == "aws":
            permissions_report = self.validate_aws_permissions()
            report.merge(permissions_report)

        return report

    def display_report(self, report: ValidationReport) -> None:
        """
        Display validation report using Rich console.

        Shows all checks with symbols, groups by category,
        and provides a summary with pass/fail counts.

        Args:
            report: ValidationReport to display
        """
        if self.console is None:
            # Fallback to print if no console
            self._display_report_plain(report)
            return

        # Group checks by category
        ssh_checks = [
            c for c in report.checks if "SSH" in c.name or "ssh" in c.name.lower()
        ]
        cloud_providers = ("AWS", "STACKIT", "GCP", "Azure")
        cloud_checks = [
            c for c in report.checks if any(p in c.name for p in cloud_providers)
        ]
        other_checks = [
            c for c in report.checks if c not in ssh_checks and c not in cloud_checks
        ]

        # Display SSH checks
        if ssh_checks:
            self.console.print("\n[bold]SSH Key Checks:[/bold]")
            for check in ssh_checks:
                self._display_check(check)

        # Display cloud provider checks
        if cloud_checks:
            self.console.print("\n[bold]Cloud Provider Checks:[/bold]")
            for check in cloud_checks:
                self._display_check(check)

        # Display other checks
        if other_checks:
            self.console.print("\n[bold]Other Checks:[/bold]")
            for check in other_checks:
                self._display_check(check)

        # Summary
        self.console.print()
        if report.has_errors:
            self.console.print(
                f"[red bold]Summary: {report.passed_count} passed, {report.failed_count} failed[/red bold]"
            )
        elif report.has_warnings:
            self.console.print(
                f"[yellow]Summary: {report.passed_count} passed, {report.failed_count} warnings[/yellow]"
            )
        else:
            self.console.print(
                f"[green]Summary: {report.passed_count} passed, {report.failed_count} failed[/green]"
            )

    def _display_check(self, check: CheckResult) -> None:
        """Display a single check result."""
        if self.console is None:
            return

        # Main check line
        self.console.print(f"  {check.symbol} {check.name}: {check.message}")

        # Details
        if check.details and not check.passed:
            for line in check.details.split("\n"):
                self.console.print(f"      {line}")

        # Suggestion
        if check.suggestion and not check.passed:
            self.console.print(f"      [dim]\u2192 Fix:[/dim] {check.suggestion}")

    def _display_report_plain(self, report: ValidationReport) -> None:
        """Display report without Rich formatting."""
        for check in report.checks:
            symbol = "OK" if check.passed else "FAIL"
            print(f"  [{symbol}] {check.name}: {check.message}")
            if check.details and not check.passed:
                print(f"      {check.details}")
            if check.suggestion and not check.passed:
                print(f"      Fix: {check.suggestion}")

        print()
        print(f"Summary: {report.passed_count} passed, {report.failed_count} failed")
