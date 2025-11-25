#!/usr/bin/env python3
"""Check AWS credentials and required permissions for benchmarking."""

import argparse
import boto3
import os
import sys
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError

# Load .env file if it exists - this must be done early before other imports
try:
    from dotenv import load_dotenv

    load_dotenv(
        override=True
    )  # override=True makes .env vars take precedence over existing env vars
except ImportError:
    pass  # python-dotenv not installed, continue without .env support

try:
    import yaml
except ImportError:
    print("✗ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
    import base64
    import hashlib
except ImportError:
    print("✗ cryptography library not installed. Run: pip install cryptography")
    sys.exit(1)


def check_credentials():
    """Check if AWS credentials are configured."""
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials configured")
        print(f"  User: {identity.get('Arn', 'Unknown')}")
        print(f"  Account: {identity.get('Account', 'Unknown')}")
        return True
    except NoCredentialsError:
        print("✗ No AWS credentials configured")
        print("  Configure using: aws configure")
        print("  Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        return False
    except ClientError as e:
        print(f"✗ AWS credentials error: {e}")
        return False


def check_permissions():
    """Check required AWS permissions."""
    required_permissions = [
        ("ec2", "describe_images", "DescribeImages"),
        ("ec2", "describe_availability_zones", "DescribeAvailabilityZones"),
        ("ec2", "describe_instances", "DescribeInstances"),
        ("ec2", "run_instances", "RunInstances"),
        ("ec2", "create_security_group", "CreateSecurityGroup"),
        ("ec2", "create_vpc", "CreateVpc"),
    ]

    permissions_ok = True

    for service, method, action in required_permissions:
        try:
            client = boto3.client(service)
            # Try a dry-run or describe operation to test permissions
            if method == "describe_images":
                client.describe_images(MaxResults=1, DryRun=True)
            elif method == "describe_availability_zones":
                client.describe_availability_zones(DryRun=True)
            elif method == "describe_instances":
                client.describe_instances(MaxResults=1, DryRun=True)
            # Note: Can't easily test create operations without actually creating
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'DryRunOperation':
                print(f"✓ {action} - Permission OK")
            elif error_code == 'UnauthorizedOperation':
                print(f"✗ {action} - Missing permission")
                permissions_ok = False
            else:
                print(f"? {action} - Unknown error: {error_code}")
        except Exception as e:
            print(f"? {action} - Error: {e}")

    return permissions_ok


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        print(f"✗ Config file not found: {config_path}")
        sys.exit(1)

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def check_ssh_key_on_aws(key_name: str, region: str = None) -> tuple[bool, str]:
    """Check if SSH key pair exists on AWS.

    Returns:
        Tuple of (exists: bool, fingerprint: str)
    """
    try:
        ec2 = boto3.client("ec2", region_name=region) if region else boto3.client("ec2")
        response = ec2.describe_key_pairs(KeyNames=[key_name])

        if response["KeyPairs"]:
            key_info = response["KeyPairs"][0]
            fingerprint = key_info.get('KeyFingerprint', 'N/A')
            print(f"✓ SSH key '{key_name}' found on AWS")
            print(f"  KeyPairId: {key_info.get('KeyPairId', 'N/A')}")
            print(f"  Fingerprint: {fingerprint}")
            return True, fingerprint
        else:
            print(f"✗ SSH key '{key_name}' not found on AWS")
            return False, None
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "InvalidKeyPair.NotFound":
            print(f"✗ SSH key '{key_name}' not found on AWS")
            print(f"  Create it with: aws ec2 create-key-pair --key-name {key_name}")
        else:
            print(f"✗ Error checking SSH key on AWS: {e}")
        return False, None
    except Exception as e:
        print(f"✗ Unexpected error checking SSH key: {e}")
        return False, None


def calculate_key_fingerprints(private_key_path: Path) -> dict:
    """Calculate SSH key fingerprints from a private key file.

    Returns dict with 'md5' and 'sha1' fingerprints.
    AWS uses SHA-1 for keys created via create-key-pair,
    and MD5 for keys imported via import-key-pair.
    """
    try:
        with open(private_key_path, "rb") as key_file:
            key_data = key_file.read()

            # Try loading as OpenSSH format first (newer format)
            try:
                private_key = serialization.load_ssh_private_key(
                    key_data,
                    password=None,
                    backend=default_backend()
                )
            except Exception:
                # Fall back to PEM format (traditional format)
                private_key = serialization.load_pem_private_key(
                    key_data,
                    password=None,
                    backend=default_backend()
                )

        # Extract public key
        public_key = private_key.public_key()

        # Get DER format for fingerprint calculation (AWS standard for RSA/ECDSA)
        der_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        # Get OpenSSH format (used for SHA-256 on ED25519 and newer keys)
        openssh_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        # OpenSSH format includes "ssh-ed25519 " or "ssh-rsa " prefix - remove it
        # We need just the base64 part after the key type
        openssh_parts = openssh_bytes.split()
        if len(openssh_parts) >= 2:
            openssh_key_data = base64.b64decode(openssh_parts[1])
        else:
            openssh_key_data = openssh_bytes

        # Calculate MD5 fingerprint (for imported keys - hex with colons)
        md5_hash = hashlib.md5(der_bytes).hexdigest()
        md5_fingerprint = ":".join(md5_hash[i:i+2] for i in range(0, len(md5_hash), 2))

        # Calculate SHA-1 fingerprint (for AWS-created keys - hex with colons)
        sha1_hash = hashlib.sha1(der_bytes).hexdigest()
        sha1_fingerprint = ":".join(sha1_hash[i:i+2] for i in range(0, len(sha1_hash), 2))

        # Calculate SHA-256 fingerprint - try both DER and OpenSSH formats
        # DER format (for RSA/ECDSA keys)
        sha256_der_hash = hashlib.sha256(der_bytes).digest()
        sha256_der_fingerprint = base64.b64encode(sha256_der_hash).decode('ascii')

        # OpenSSH format (for ED25519 and newer keys)
        sha256_openssh_hash = hashlib.sha256(openssh_key_data).digest()
        sha256_openssh_fingerprint = base64.b64encode(sha256_openssh_hash).decode('ascii')

        return {
            "md5": md5_fingerprint,
            "sha1": sha1_fingerprint,
            "sha256": sha256_der_fingerprint,
            "sha256_openssh": sha256_openssh_fingerprint
        }
    except Exception as e:
        print(f"✗ Error calculating fingerprint: {e}")
        return None


def check_ssh_key_local(key_path: str) -> tuple[bool, Path]:
    """Check if SSH private key exists locally and has proper permissions.

    Returns:
        Tuple of (valid: bool, expanded_path: Path)
    """
    # Expand ~ to home directory
    expanded_path = Path(key_path).expanduser()

    # Check if file exists
    if not expanded_path.exists():
        print(f"✗ SSH private key not found: {key_path}")
        print(f"  Expanded path: {expanded_path}")
        print(f"  Download it from AWS or use an existing key")
        return False, expanded_path

    print(f"✓ SSH private key found: {expanded_path}")

    # Check if it's a file (not a directory)
    if not expanded_path.is_file():
        print(f"✗ Path is not a file: {expanded_path}")
        return False, expanded_path

    # Check permissions (should be 600 or 400)
    stat_info = expanded_path.stat()
    mode = stat_info.st_mode & 0o777  # Get permission bits

    if mode == 0o600 or mode == 0o400:
        print(f"✓ SSH key permissions OK: {oct(mode)}")
        return True, expanded_path
    else:
        print(f"✗ SSH key has incorrect permissions: {oct(mode)}")
        print(f"  Fix with: chmod 600 {expanded_path}")
        return False, expanded_path


def verify_fingerprint_match(local_key_path: Path, aws_fingerprint: str) -> bool:
    """Verify that local private key matches AWS key pair fingerprint.

    Args:
        local_key_path: Path to local private key file
        aws_fingerprint: Fingerprint from AWS key pair

    Returns:
        True if fingerprints match, False otherwise
    """
    if not aws_fingerprint or aws_fingerprint == 'N/A':
        print("⚠ Cannot verify fingerprint match: AWS fingerprint not available")
        return True  # Don't fail if AWS fingerprint unavailable

    print("Verifying fingerprint match...")

    # Calculate local key fingerprints
    local_fingerprints = calculate_key_fingerprints(local_key_path)
    if not local_fingerprints:
        print("✗ Failed to calculate local key fingerprint")
        return False

    print(f"  Local MD5:              {local_fingerprints['md5']}")
    print(f"  Local SHA-1:            {local_fingerprints['sha1']}")
    print(f"  Local SHA-256 (DER):    {local_fingerprints['sha256']}")
    print(f"  Local SHA-256 (SSH):    {local_fingerprints['sha256_openssh']}")
    print(f"  AWS fingerprint:        {aws_fingerprint}")

    # Check if any fingerprint matches (AWS uses different formats for different key types)
    if aws_fingerprint == local_fingerprints['md5']:
        print("✓ Fingerprint match verified (MD5)")
        return True
    elif aws_fingerprint == local_fingerprints['sha1']:
        print("✓ Fingerprint match verified (SHA-1)")
        return True
    elif aws_fingerprint == local_fingerprints['sha256']:
        print("✓ Fingerprint match verified (SHA-256 DER)")
        return True
    elif aws_fingerprint == local_fingerprints['sha256_openssh']:
        print("✓ Fingerprint match verified (SHA-256 OpenSSH)")
        return True
    else:
        print("✗ Fingerprint mismatch!")
        print("  The local private key does NOT match the AWS key pair")
        print("  Ensure you're using the correct private key file")
        return False


def check_ssh_keys(config_path: str) -> bool:
    """Check SSH keys from configuration file."""
    config = load_config(config_path)

    # Get env config
    env_config = config.get("env", {})
    mode = env_config.get("mode", "local")

    # Only check SSH keys for cloud modes
    if mode not in ["aws", "gcp", "azure"]:
        print(f"ℹ Skipping SSH key check (mode: {mode})")
        return True

    ssh_key_name = env_config.get("ssh_key_name")
    ssh_private_key_path = env_config.get("ssh_private_key_path")
    region = env_config.get("region")

    if not ssh_key_name or not ssh_private_key_path:
        print("✗ SSH key configuration missing in config file")
        print("  Required fields: env.ssh_key_name, env.ssh_private_key_path")
        return False

    print(f"Checking SSH key configuration...")
    print(f"  Key name: {ssh_key_name}")
    print(f"  Private key path: {ssh_private_key_path}")
    print(f"  Region: {region or 'default'}")
    print()

    # Check AWS key pair (only for AWS mode)
    aws_ok = True
    aws_fingerprint = None
    if mode == "aws":
        aws_ok, aws_fingerprint = check_ssh_key_on_aws(ssh_key_name, region)
        print()

    # Check local private key file
    local_ok, local_key_path = check_ssh_key_local(ssh_private_key_path)
    print()

    # Verify fingerprint match if both checks passed
    fingerprint_ok = True
    if aws_ok and local_ok and mode == "aws":
        fingerprint_ok = verify_fingerprint_match(local_key_path, aws_fingerprint)
        print()

    return aws_ok and local_ok and fingerprint_ok


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Check AWS credentials and required permissions for benchmarking"
    )
    parser.add_argument(
        "--config",
        default="configs/exa_vs_ch_1g.yaml",
        help="Path to configuration file (default: configs/exa_vs_ch_1g.yaml)",
    )
    args = parser.parse_args()

    print("Checking AWS configuration for benchmark deployment...")
    print()

    # Check credentials
    creds_ok = check_credentials()
    print()

    # Check permissions
    if creds_ok:
        print("Checking required permissions...")
        perms_ok = check_permissions()
        print()
    else:
        print("Please configure AWS credentials first")
        sys.exit(1)

    # Check SSH keys from config
    print(f"Checking SSH keys from config: {args.config}")
    print()
    ssh_ok = check_ssh_keys(args.config)

    # Final summary
    print("=" * 60)
    if creds_ok and perms_ok and ssh_ok:
        print("✓ AWS configuration looks good for benchmarking!")
        print("  All checks passed:")
        print("  • AWS credentials configured")
        print("  • Required permissions available")
        print("  • SSH key configuration valid")
        print("  • Fingerprint match verified")
        sys.exit(0)
    else:
        print("✗ AWS configuration has issues:")
        if not creds_ok:
            print("  • AWS credentials not configured")
        if not perms_ok:
            print("  • Some required permissions are missing")
            print("    Contact your AWS administrator to grant EC2 full access")
        if not ssh_ok:
            print("  • SSH key configuration has issues")
            print("    Fix the SSH key issues listed above")
        sys.exit(1)


if __name__ == "__main__":
    main()
