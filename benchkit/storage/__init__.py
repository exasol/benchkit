"""Storage backends for benchmark workload data.

This module provides abstractions for different storage backends (local filesystem, S3)
that can be used with systems supporting external tables (e.g., Trino with Hive connector).
"""

from .base import StorageBackend
from .local import LocalStorage
from .s3 import S3Storage

__all__ = ["StorageBackend", "LocalStorage", "S3Storage"]
