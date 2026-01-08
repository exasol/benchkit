"""Local filesystem storage backend."""

import shutil
from pathlib import Path

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage backend (file:// URLs).

    Used for single-node Trino deployments where data is stored on the local
    filesystem and accessed via the Hive connector's file:// protocol.

    This is the default storage backend for Trino single-node configurations.
    """

    def __init__(self, base_path: str = "/data/hive-warehouse"):
        """Initialize local storage backend.

        Args:
            base_path: Base directory for storing data (default: /data/hive-warehouse)
        """
        self.base_path = Path(base_path)

    def get_location_prefix(self) -> str:
        """Return the file:// URL prefix."""
        return "file://"

    def get_data_location(self, schema: str, table: str) -> str:
        """Return file:// URL for table data.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            Full file:// URL (e.g., 'file:///data/hive-warehouse/benchmark/lineitem')
        """
        return f"file://{self.base_path}/{schema}/{table}"

    def get_local_path(self, schema: str, table: str) -> Path:
        """Get local filesystem path for table data.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            Local Path object
        """
        return self.base_path / schema / table

    def upload_data(self, local_path: Path, schema: str, table: str) -> bool:
        """Copy data from source path to storage location.

        For local storage, this copies or moves files to the target directory.

        Args:
            local_path: Path to source directory containing data files
            schema: Target schema name
            table: Target table name

        Returns:
            True if copy successful, False otherwise
        """
        try:
            target_path = self.get_local_path(schema, table)

            # If source and target are the same, nothing to do
            if local_path.resolve() == target_path.resolve():
                print(f"  Data already in place at {target_path}")
                return True

            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # If target exists, remove it first
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

            # Copy directory (for Parquet with multiple files)
            if local_path.is_dir():
                shutil.copytree(local_path, target_path)
            else:
                # Single file - create directory and copy
                target_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_path, target_path / local_path.name)

            print(f"  Copied {local_path} to {target_path}")
            return True

        except Exception as e:
            print(f"  Failed to copy data to {target_path}: {e}")
            return False

    def exists(self, schema: str, table: str) -> bool:
        """Check if data exists for the given table.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            True if data directory exists and contains files
        """
        path = self.get_local_path(schema, table)
        if not path.exists():
            return False
        if path.is_dir():
            # Check if directory has any files
            return any(path.iterdir())
        return True

    def prepare(self) -> bool:
        """Prepare local storage by creating base directory.

        Returns:
            True if directory created/exists, False on error
        """
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"Failed to create local storage directory {self.base_path}: {e}")
            return False

    def cleanup(self, schema: str) -> bool:
        """Remove all data for a schema.

        Args:
            schema: Schema name to clean up

        Returns:
            True if cleanup successful
        """
        try:
            schema_path = self.base_path / schema
            if schema_path.exists():
                shutil.rmtree(schema_path)
                print(f"  Cleaned up local storage for schema: {schema}")
            return True
        except Exception as e:
            print(f"  Failed to clean up schema {schema}: {e}")
            return False

    def __repr__(self) -> str:
        return f"LocalStorage(base_path='{self.base_path}')"
