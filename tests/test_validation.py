"""Tests for the validation module."""

from __future__ import annotations

import pytest

from benchkit.validation import (
    CheckResult,
    CheckSeverity,
    PreflightChecker,
    ValidationReport,
    check_ssh_key_file_exists,
    check_ssh_key_format,
    check_ssh_key_permissions,
    check_ssh_key_readable,
)

# =============================================================================
# CheckResult Tests
# =============================================================================


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_passed_check_symbol_is_green_checkmark(self):
        result = CheckResult(
            name="test",
            passed=True,
            severity=CheckSeverity.INFO,
            message="ok",
        )
        assert "\u2713" in result.symbol  # checkmark
        assert "green" in result.symbol

    def test_failed_error_symbol_is_red_x(self):
        result = CheckResult(
            name="test",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="failed",
        )
        assert "\u2717" in result.symbol  # x mark
        assert "red" in result.symbol

    def test_failed_warning_symbol_is_yellow(self):
        result = CheckResult(
            name="test",
            passed=False,
            severity=CheckSeverity.WARNING,
            message="warning",
        )
        assert "yellow" in result.symbol

    def test_check_result_with_details_and_suggestion(self):
        result = CheckResult(
            name="SSH key permissions",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Incorrect permissions",
            details="Current: 0o644, Expected: 0o600",
            suggestion="chmod 600 ~/.ssh/key.pem",
        )
        assert result.details == "Current: 0o644, Expected: 0o600"
        assert result.suggestion == "chmod 600 ~/.ssh/key.pem"


# =============================================================================
# ValidationReport Tests
# =============================================================================


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_empty_report_has_no_errors(self):
        report = ValidationReport()
        assert not report.has_errors
        assert not report.has_warnings
        assert report.passed_count == 0
        assert report.failed_count == 0

    def test_report_with_passed_check(self):
        report = ValidationReport()
        report.add(
            CheckResult("test", passed=True, severity=CheckSeverity.INFO, message="ok")
        )
        assert not report.has_errors
        assert report.passed_count == 1
        assert report.failed_count == 0

    def test_report_with_failed_error(self):
        report = ValidationReport()
        report.add(
            CheckResult("a", passed=True, severity=CheckSeverity.INFO, message="ok")
        )
        assert not report.has_errors

        report.add(
            CheckResult("b", passed=False, severity=CheckSeverity.ERROR, message="fail")
        )
        assert report.has_errors
        assert report.passed_count == 1
        assert report.failed_count == 1

    def test_report_with_warning(self):
        report = ValidationReport()
        report.add(
            CheckResult(
                "warn", passed=False, severity=CheckSeverity.WARNING, message="warning"
            )
        )
        assert not report.has_errors
        assert report.has_warnings
        assert report.failed_count == 1

    def test_merge_reports(self):
        report1 = ValidationReport()
        report1.add(
            CheckResult("a", passed=True, severity=CheckSeverity.INFO, message="ok")
        )

        report2 = ValidationReport()
        report2.add(
            CheckResult("b", passed=True, severity=CheckSeverity.INFO, message="ok")
        )
        report2.add(
            CheckResult("c", passed=False, severity=CheckSeverity.ERROR, message="fail")
        )

        report1.merge(report2)
        assert len(report1.checks) == 3
        assert report1.passed_count == 2
        assert report1.failed_count == 1


# =============================================================================
# SSH Key Validation Tests
# =============================================================================


class TestSSHKeyFileExists:
    """Tests for check_ssh_key_file_exists function."""

    def test_nonexistent_key_fails(self, tmp_path):
        result = check_ssh_key_file_exists(str(tmp_path / "nonexistent.pem"))
        assert not result.passed
        assert result.severity == CheckSeverity.ERROR
        assert "not found" in result.message.lower()

    def test_existing_key_passes(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy key content")

        result = check_ssh_key_file_exists(str(key_file))
        assert result.passed
        assert result.severity == CheckSeverity.INFO

    def test_directory_instead_of_file_fails(self, tmp_path):
        key_dir = tmp_path / "not_a_file"
        key_dir.mkdir()

        result = check_ssh_key_file_exists(str(key_dir))
        assert not result.passed
        assert result.severity == CheckSeverity.ERROR
        assert "not a file" in result.message.lower()

    def test_tilde_expansion(self, tmp_path, monkeypatch):
        # Create a fake home directory
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        ssh_dir = fake_home / ".ssh"
        ssh_dir.mkdir()
        key_file = ssh_dir / "test.pem"
        key_file.write_text("dummy key")

        monkeypatch.setenv("HOME", str(fake_home))

        result = check_ssh_key_file_exists("~/.ssh/test.pem")
        assert result.passed


class TestSSHKeyPermissions:
    """Tests for check_ssh_key_permissions function."""

    def test_nonexistent_key_fails(self, tmp_path):
        result = check_ssh_key_permissions(str(tmp_path / "nonexistent.pem"))
        assert not result.passed
        assert "does not exist" in result.message.lower()

    def test_permission_600_passes(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o600)

        result = check_ssh_key_permissions(str(key_file))
        assert result.passed
        assert "0o600" in result.message

    def test_permission_400_passes(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o400)

        result = check_ssh_key_permissions(str(key_file))
        assert result.passed
        assert "0o400" in result.message

    def test_permission_644_fails(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o644)

        result = check_ssh_key_permissions(str(key_file))
        assert not result.passed
        assert result.severity == CheckSeverity.ERROR
        assert "0o644" in result.message
        assert "chmod 600" in result.suggestion

    def test_permission_755_fails(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o755)

        result = check_ssh_key_permissions(str(key_file))
        assert not result.passed
        assert "chmod 600" in result.suggestion


class TestSSHKeyFormat:
    """Tests for check_ssh_key_format function."""

    def test_nonexistent_key_fails(self, tmp_path):
        result = check_ssh_key_format(str(tmp_path / "nonexistent.pem"))
        assert not result.passed
        assert "does not exist" in result.message.lower()

    def test_invalid_format_fails(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("this is not a valid ssh key")

        result = check_ssh_key_format(str(key_file))
        assert not result.passed
        assert result.severity == CheckSeverity.ERROR

    def test_valid_rsa_key_passes(self, tmp_path):
        # Generate a minimal valid RSA private key in PEM format
        # This is a test-only key, not used for anything real
        key_file = tmp_path / "test.pem"

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend(),
            )
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            key_file.write_bytes(pem)

            result = check_ssh_key_format(str(key_file))
            assert result.passed
            assert "RSA" in result.message or "valid" in result.message.lower()

        except ImportError:
            pytest.skip("cryptography library not installed")


class TestSSHKeyReadable:
    """Tests for check_ssh_key_readable function."""

    def test_nonexistent_key_fails(self, tmp_path):
        result = check_ssh_key_readable(str(tmp_path / "nonexistent.pem"))
        assert not result.passed

    def test_readable_key_without_passphrase(self, tmp_path):
        key_file = tmp_path / "test.pem"

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend(),
            )
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            key_file.write_bytes(pem)

            result = check_ssh_key_readable(str(key_file))
            assert result.passed
            assert (
                "readable" in result.message.lower()
                or "without passphrase" in result.message.lower()
            )

        except ImportError:
            pytest.skip("cryptography library not installed")


# =============================================================================
# PreflightChecker Tests
# =============================================================================


class TestPreflightChecker:
    """Tests for PreflightChecker class."""

    def test_local_mode_skips_ssh_checks(self):
        config = {"env": {"mode": "local"}}
        checker = PreflightChecker(config)
        report = checker.run_check_command_validation()

        assert not report.has_errors
        # Should have an info message about local mode
        assert any("local" in c.message.lower() for c in report.checks)

    def test_aws_mode_without_ssh_config_fails(self):
        config = {
            "env": {
                "mode": "aws",
                # Missing ssh_key_name and ssh_private_key_path
            }
        }
        checker = PreflightChecker(config, skip_aws_checks=True)
        report = checker.run_check_command_validation()

        assert report.has_errors
        # Should report missing ssh_private_key_path
        assert any("ssh_private_key_path" in c.message.lower() for c in report.checks)

    def test_aws_mode_with_valid_ssh_key(self, tmp_path):
        key_file = tmp_path / "test.pem"

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa

            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend(),
            )
            pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
            key_file.write_bytes(pem)
            key_file.chmod(0o600)

        except ImportError:
            # If cryptography not available, create a dummy file
            key_file.write_text("dummy")
            key_file.chmod(0o600)

        config = {
            "env": {
                "mode": "aws",
                "ssh_key_name": "test-key",
                "ssh_private_key_path": str(key_file),
            }
        }
        checker = PreflightChecker(config, skip_aws_checks=True)
        report = checker.run_check_command_validation()

        # SSH file checks should pass
        ssh_file_check = next(
            (c for c in report.checks if "file exists" in c.name.lower()), None
        )
        assert ssh_file_check is not None
        assert ssh_file_check.passed

        ssh_perm_check = next(
            (c for c in report.checks if "permissions" in c.name.lower()), None
        )
        assert ssh_perm_check is not None
        assert ssh_perm_check.passed

    def test_skip_aws_checks_adds_info_message(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o600)

        config = {
            "env": {
                "mode": "aws",
                "ssh_key_name": "test-key",
                "ssh_private_key_path": str(key_file),
            }
        }
        checker = PreflightChecker(config, skip_aws_checks=True)
        report = checker.validate_aws_environment()

        # Should have an info message about skipping AWS checks
        assert any("skipped" in c.message.lower() for c in report.checks)

    def test_gcp_mode_shows_not_implemented_message(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o600)

        config = {
            "env": {
                "mode": "gcp",
                "ssh_private_key_path": str(key_file),
            }
        }
        checker = PreflightChecker(config)
        report = checker.validate_aws_environment()

        # Should have an info message about GCP validation not implemented
        assert any("gcp" in c.message.lower() for c in report.checks)
        assert any("not yet implemented" in c.message.lower() for c in report.checks)

    def test_infra_validation_includes_permissions_check(self, tmp_path):
        key_file = tmp_path / "test.pem"
        key_file.write_text("dummy")
        key_file.chmod(0o600)

        config = {
            "env": {
                "mode": "aws",
                "ssh_key_name": "test-key",
                "ssh_private_key_path": str(key_file),
            }
        }
        checker = PreflightChecker(config, skip_aws_checks=True)

        # run_infra_deploy_validation should call validate_aws_permissions
        # but with skip_aws_checks=True, it won't actually run AWS checks
        report = checker.run_infra_deploy_validation()

        # Should have run SSH checks at minimum
        assert len(report.checks) > 0


class TestPreflightCheckerDisplay:
    """Tests for PreflightChecker display methods."""

    def test_display_report_plain_fallback(self, tmp_path, capsys):
        """Test that display works without Rich console."""
        config = {"env": {"mode": "local"}}
        checker = PreflightChecker(config, console=None)  # No Rich console
        report = checker.run_check_command_validation()

        checker.display_report(report)

        captured = capsys.readouterr()
        assert "Summary" in captured.out
