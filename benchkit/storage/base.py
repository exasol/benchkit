"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class StorageBackend(ABC):
    """Abstract storage backend for workload data.

    Storage backends provide a unified interface for storing and accessing
    benchmark data across different storage systems (local filesystem, S3, etc.).

    Systems that support external tables (e.g., Trino) use storage backends to:
    1. Upload generated data (Parquet files) to the storage location
    2. Get data location URLs for external table definitions
    """

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by this storage backend.

        Override in subclasses that require additional packages.
        """
        return []

    @abstractmethod
    def get_location_prefix(self) -> str:
        """Return the URL prefix for this storage type.

        Returns:
            URL prefix string (e.g., 'file://', 's3a://')
        """
        pass

    @abstractmethod
    def get_data_location(self, schema: str, table: str) -> str:
        """Return the full location URL for a table's data.

        This URL is used in external table definitions to point to the data.

        Args:
            schema: Schema/database name
            table: Table name

        Returns:
            Full URL to data location (e.g., 's3a://bucket/prefix/schema/table')
        """
        pass

    @abstractmethod
    def upload_data(self, local_path: Path, schema: str, table: str) -> bool:
        """Upload data from local path to storage.

        Args:
            local_path: Path to local directory containing data files
            schema: Target schema name
            table: Target table name

        Returns:
            True if upload successful, False otherwise
        """
        pass

    @abstractmethod
    def exists(self, schema: str, table: str) -> bool:
        """Check if data exists for the given schema and table.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            True if data exists, False otherwise
        """
        pass

    def prepare(self) -> bool:
        """Prepare the storage backend for use.

        Called before any upload operations. Can be used to create buckets,
        verify credentials, etc.

        Returns:
            True if preparation successful, False otherwise
        """
        return True

    def cleanup(self, schema: str) -> bool:
        """Clean up data for a schema.

        Optional method to remove all data for a schema after benchmark completion.

        Args:
            schema: Schema name to clean up

        Returns:
            True if cleanup successful, False otherwise
        """
        return True

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "StorageBackend":
        """Create a storage backend from configuration.

        Factory method to create the appropriate storage backend based on config.

        Args:
            config: Storage configuration dictionary with 'type' key

        Returns:
            StorageBackend instance

        Raises:
            ValueError: If storage type is not recognized
        """
        from .local import LocalStorage
        from .s3 import S3Storage

        storage_type = config.get("type", "local")

        if storage_type == "local":
            return LocalStorage(
                base_path=config.get("base_path", "/data/hive-warehouse")
            )
        elif storage_type == "s3":
            return S3Storage(
                bucket=config["bucket"],
                prefix=config.get("prefix", ""),
                region=config.get("region", "us-east-1"),
            )
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
