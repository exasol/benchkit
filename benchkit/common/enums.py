"""Common enums used across the benchkit framework."""

from enum import Enum


class EnvironmentMode(str, Enum):
    """Environment mode for benchmark execution.

    Defines where and how the benchmark infrastructure is managed:
    - LOCAL: Run on local machine (no cloud infrastructure)
    - AWS: Use AWS cloud infrastructure (managed by benchkit terraform)
    - GCP: Use GCP cloud infrastructure (managed by benchkit terraform)
    - AZURE: Use Azure cloud infrastructure (managed by benchkit terraform)
    - MANAGED: Self-managed deployment (infrastructure managed externally, e.g., Exasol Personal Edition)
    """

    LOCAL = "local"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    MANAGED = "managed"  # Self-managed deployments (e.g., Exasol Personal Edition)

    @classmethod
    def cloud_providers(cls) -> set["EnvironmentMode"]:
        """Return set of cloud provider modes (terraform-managed)."""
        return {cls.AWS, cls.GCP, cls.AZURE}

    @classmethod
    def is_cloud_provider(cls, mode: str) -> bool:
        """Check if a mode string represents a cloud provider."""
        try:
            return cls(mode) in cls.cloud_providers()
        except ValueError:
            return False

    @classmethod
    def valid_values(cls) -> set[str]:
        """Return all valid mode values as strings."""
        return {m.value for m in cls}

    def __str__(self) -> str:
        return self.value
