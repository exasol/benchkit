"""E2E test configuration and fixtures.

This module provides pytest configuration, fixtures, and hooks for E2E testing.

E2E tests are NOT run by default. Use --e2e flag to enable them:
    pytest tests/e2e/ --e2e

Available options:
    --e2e               Run E2E tests with real infrastructure
    --e2e-skip-cleanup  Skip infrastructure cleanup after tests (debugging)
    --e2e-systems       Comma-separated list of systems to test
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for E2E tests."""
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests requiring real infrastructure (deselect: -m 'not e2e')",
    )
    config.addinivalue_line(
        "markers",
        "e2e_dryrun: Dry-run tests for CLI validation only (no infrastructure)",
    )
    config.addinivalue_line(
        "markers",
        "e2e_slow: Slow E2E tests that provision infrastructure",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip E2E tests unless --e2e flag is provided."""
    if not config.getoption("--e2e", default=False):
        skip_e2e = pytest.mark.skip(
            reason="E2E tests require --e2e flag. Use: pytest tests/e2e/ --e2e"
        )
        for item in items:
            # Skip tests marked with @pytest.mark.e2e but not @pytest.mark.e2e_dryrun
            if "e2e" in item.keywords and "e2e_dryrun" not in item.keywords:
                item.add_marker(skip_e2e)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options for E2E tests."""
    parser.addoption(
        "--e2e",
        action="store_true",
        default=False,
        help="Run end-to-end tests with real infrastructure",
    )
    parser.addoption(
        "--e2e-skip-cleanup",
        action="store_true",
        default=False,
        help="Skip infrastructure cleanup after tests (for debugging)",
    )
    parser.addoption(
        "--e2e-systems",
        action="store",
        default=None,
        help="Comma-separated list of systems to test (e.g., exasol_sn,clickhouse_sn)",
    )


# =============================================================================
# Path Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def e2e_config_dir() -> Path:
    """Return the E2E config directory path."""
    return Path(__file__).parent / "configs"


@pytest.fixture(scope="session")
def comprehensive_config_path(e2e_config_dir: Path) -> Path:
    """Return path to comprehensive test config."""
    config_path = e2e_config_dir / "e2e_comprehensive_1g.yaml"
    if not config_path.exists():
        pytest.skip(f"Comprehensive config not found: {config_path}")
    return config_path


@pytest.fixture(scope="session")
def dryrun_config_path(e2e_config_dir: Path) -> Path:
    """Return path to dry-run (local mode) test config."""
    config_path = e2e_config_dir / "e2e_dryrun_local.yaml"
    if not config_path.exists():
        pytest.skip(f"Dry-run config not found: {config_path}")
    return config_path


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def loaded_config(comprehensive_config_path: Path) -> dict[str, Any]:
    """Load and return the comprehensive config as a dictionary."""
    with open(comprehensive_config_path) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def project_id(loaded_config: dict[str, Any]) -> str:
    """Get project ID from config, falling back to filename."""
    if "project_id" in loaded_config:
        return loaded_config["project_id"]
    # Derive from title if no explicit project_id
    title = loaded_config.get("title", "e2e_comprehensive_1g")
    return title.lower().replace(" ", "_").replace(":", "")[:50]


@pytest.fixture(scope="session")
def results_dir(project_id: str) -> Path:
    """Return the results directory for E2E tests."""
    return Path("results") / project_id


@pytest.fixture(scope="session")
def expected_systems(loaded_config: dict[str, Any]) -> list[str]:
    """Return list of expected system names from config."""
    return [s["name"] for s in loaded_config.get("systems", [])]


# =============================================================================
# CLI Option Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def e2e_systems(request: pytest.FixtureRequest) -> list[str] | None:
    """Get list of systems to test from CLI option."""
    systems_opt = request.config.getoption("--e2e-systems")
    if systems_opt:
        return [s.strip() for s in systems_opt.split(",")]
    return None


@pytest.fixture
def skip_cleanup(request: pytest.FixtureRequest) -> bool:
    """Check if cleanup should be skipped."""
    return request.config.getoption("--e2e-skip-cleanup")


@pytest.fixture
def is_e2e_enabled(request: pytest.FixtureRequest) -> bool:
    """Check if E2E tests are enabled."""
    return request.config.getoption("--e2e")


# =============================================================================
# Timeout Constants
# =============================================================================


@pytest.fixture(scope="session")
def timeouts() -> dict[str, int]:
    """Return timeout values for various operations (in seconds)."""
    return {
        "infra_apply": 900,  # 15 minutes
        "infra_destroy": 600,  # 10 minutes
        "infra_plan": 300,  # 5 minutes
        "setup": 1800,  # 30 minutes (all systems)
        "load": 1800,  # 30 minutes
        "run": 3600,  # 1 hour
        "probe": 300,  # 5 minutes
        "report": 300,  # 5 minutes
        "package": 120,  # 2 minutes
        "status": 60,  # 1 minute
        "check": 30,  # 30 seconds
    }
