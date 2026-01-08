"""S3 storage backend."""

from pathlib import Path
from typing import Any

from .base import StorageBackend


class S3Storage(StorageBackend):
    """S3 storage backend (s3a:// URLs).

    Used for Trino deployments (especially multinode) where data is stored in S3
    and accessed via the Hive connector's s3a:// protocol.

    Uses boto3 with the default credential chain (IAM role preferred).

    Note: Multinode Trino clusters REQUIRE S3 storage to avoid data replication
    across nodes.
    """

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str = "us-east-1",
    ):
        """Initialize S3 storage backend.

        Args:
            bucket: S3 bucket name
            prefix: Optional prefix path within the bucket
            region: AWS region (default: us-east-1)
        """
        self.bucket = bucket
        self.prefix = prefix.strip("/")  # Remove leading/trailing slashes
        self.region = region
        self._client: Any = None
        self._resource: Any = None

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required for S3 storage."""
        return ["boto3>=1.26.0"]

    def get_location_prefix(self) -> str:
        """Return the s3a:// URL prefix."""
        return "s3a://"

    def get_data_location(self, schema: str, table: str) -> str:
        """Return s3a:// URL for table data.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            Full s3a:// URL (e.g., 's3a://bucket/prefix/schema/table')
        """
        parts = [f"s3a://{self.bucket}"]
        if self.prefix:
            parts.append(self.prefix)
        parts.append(schema)
        parts.append(table)
        return "/".join(parts)

    def get_s3_key_prefix(self, schema: str, table: str) -> str:
        """Get S3 key prefix for table data.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            S3 key prefix (without bucket name)
        """
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        parts.append(schema)
        parts.append(table)
        return "/".join(parts)

    def _get_client(self) -> Any:
        """Get or create boto3 S3 client."""
        if self._client is None:
            try:
                import boto3
            except ImportError as e:
                raise ImportError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                ) from e

            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def _get_resource(self) -> Any:
        """Get or create boto3 S3 resource."""
        if self._resource is None:
            try:
                import boto3
            except ImportError as e:
                raise ImportError(
                    "boto3 is required for S3 storage. Install with: pip install boto3"
                ) from e

            self._resource = boto3.resource("s3", region_name=self.region)
        return self._resource

    def upload_data(self, local_path: Path, schema: str, table: str) -> bool:
        """Upload data from local path to S3.

        Uploads all files from the local directory to S3 using multipart upload
        for large files.

        Args:
            local_path: Path to local directory containing data files
            schema: Target schema name
            table: Target table name

        Returns:
            True if upload successful, False otherwise
        """
        try:
            from boto3.s3.transfer import TransferConfig
        except ImportError:
            print("boto3 is required for S3 storage. Install with: pip install boto3")
            return False

        try:
            s3 = self._get_resource()
            bucket = s3.Bucket(self.bucket)
            key_prefix = self.get_s3_key_prefix(schema, table)

            # Configure multipart upload for large files
            config = TransferConfig(
                multipart_threshold=8 * 1024 * 1024,  # 8MB
                max_concurrency=10,
                multipart_chunksize=8 * 1024 * 1024,  # 8MB
            )

            uploaded_count = 0

            if local_path.is_dir():
                # Upload all files in directory
                for file_path in local_path.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(local_path)
                        s3_key = f"{key_prefix}/{relative_path}"

                        bucket.upload_file(str(file_path), s3_key, Config=config)
                        uploaded_count += 1
            else:
                # Upload single file
                s3_key = f"{key_prefix}/{local_path.name}"
                bucket.upload_file(str(local_path), s3_key, Config=config)
                uploaded_count = 1

            print(
                f"  Uploaded {uploaded_count} file(s) to s3://{self.bucket}/{key_prefix}"
            )
            return True

        except Exception as e:
            print(f"  Failed to upload data to S3: {e}")
            return False

    def exists(self, schema: str, table: str) -> bool:
        """Check if data exists in S3 for the given table.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            True if any objects exist with the table prefix
        """
        try:
            client = self._get_client()
            key_prefix = self.get_s3_key_prefix(schema, table)

            response = client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=key_prefix,
                MaxKeys=1,
            )

            return bool(response.get("KeyCount", 0) > 0)

        except Exception as e:
            print(f"  Error checking S3 existence: {e}")
            return False

    def prepare(self) -> bool:
        """Prepare S3 storage by creating bucket if it doesn't exist.

        Uses IAM role credentials from the default credential chain.

        Returns:
            True if bucket exists or was created, False on error
        """
        try:
            client = self._get_client()

            # Check if bucket exists
            try:
                client.head_bucket(Bucket=self.bucket)
                print(f"  S3 bucket exists: {self.bucket}")
                return True
            except client.exceptions.ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                if error_code == "404":
                    # Bucket doesn't exist, try to create it
                    print(f"  Creating S3 bucket: {self.bucket}")
                    try:
                        if self.region == "us-east-1":
                            # us-east-1 doesn't use LocationConstraint
                            client.create_bucket(Bucket=self.bucket)
                        else:
                            client.create_bucket(
                                Bucket=self.bucket,
                                CreateBucketConfiguration={
                                    "LocationConstraint": self.region
                                },
                            )
                        print(f"  Created S3 bucket: {self.bucket}")
                        return True
                    except Exception as create_error:
                        print(
                            f"  Warning: Could not create bucket {self.bucket}: {create_error}"
                        )
                        print("  Will attempt to proceed assuming bucket exists...")
                        return True  # Try to proceed anyway

                elif error_code == "403":
                    # Access denied - bucket may exist but we can't check
                    print(
                        f"  Warning: Access denied checking bucket {self.bucket}. "
                        "Assuming it exists..."
                    )
                    return True

                else:
                    print(f"  Error checking bucket: {e}")
                    return False

        except ImportError:
            print("boto3 is required for S3 storage. Install with: pip install boto3")
            return False
        except Exception as e:
            print(f"  Failed to prepare S3 storage: {e}")
            return False

    def cleanup(self, schema: str) -> bool:
        """Remove all data for a schema from S3.

        Args:
            schema: Schema name to clean up

        Returns:
            True if cleanup successful
        """
        try:
            s3 = self._get_resource()
            bucket = s3.Bucket(self.bucket)

            # Build prefix for this schema
            parts = []
            if self.prefix:
                parts.append(self.prefix)
            parts.append(schema)
            prefix = "/".join(parts) + "/"

            # Delete all objects with this prefix
            deleted_count = 0
            for obj in bucket.objects.filter(Prefix=prefix):
                obj.delete()
                deleted_count += 1

            if deleted_count > 0:
                print(
                    f"  Deleted {deleted_count} object(s) from "
                    f"s3://{self.bucket}/{prefix}"
                )

            return True

        except Exception as e:
            print(f"  Failed to clean up S3 schema {schema}: {e}")
            return False

    def __repr__(self) -> str:
        location = f"s3://{self.bucket}"
        if self.prefix:
            location = f"{location}/{self.prefix}"
        return f"S3Storage({location}, region={self.region})"
