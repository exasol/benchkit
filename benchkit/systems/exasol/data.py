"""Exasol data loading functionality.

This module handles data loading operations for Exasol including:
- Parquet loading with SQL-based transformations
- Parallel partition loading
- HTTP URL imports
- Iterable data sources
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchkit.common import DataFormat, exclude_from_package

if TYPE_CHECKING:
    import pyexasol  # type: ignore[import-untyped]

    from .system import ExasolSystem


class ExasolDataLoader:
    """Handles Exasol data loading operations.

    This class encapsulates data loading from various sources including
    parquet files, HTTP URLs, and iterable data sources.
    """

    def __init__(self, system: ExasolSystem):
        """Initialize the data loader.

        Args:
            system: Parent ExasolSystem instance for shared state access
        """
        self._system = system

    def _log(self, message: str) -> None:
        """Log a message using the parent system's logger."""
        self._system._log(message)

    def load_parquet_data(
        self,
        conn: Any,
        table_name: str,
        data_path: Path,
        columns: list[str],
        timestamp_columns: set[str] | None = None,
        date_columns: set[str] | None = None,
    ) -> bool:
        """Load Parquet data into Exasol using SQL-based transformations.

        Optimized approach:
        1. Create staging table with raw integer types (no Python datetime conversion)
        2. Stream raw parquet data to staging table via import_from_iterable
        3. INSERT SELECT with SQL transforms (FROM_POSIX_TIME, ADD_DAYS)
        4. Drop staging table

        This pushes all type conversions to Exasol's optimized SQL engine.

        Args:
            conn: Exasol connection
            table_name: Target table name
            data_path: Path to parquet file
            columns: List of column names
            timestamp_columns: Columns containing Unix timestamps (from workload)
            date_columns: Columns containing dates as days since epoch (from workload)
        """
        try:
            import pyarrow.parquet as pq  # type: ignore[import-untyped]
        except ImportError:
            self._log("pyarrow not installed, cannot load Parquet files")
            return False

        # Use workload-provided column metadata for SQL transformations
        # Empty sets if not provided (no transformations needed)
        effective_timestamp_cols = timestamp_columns or set()
        effective_date_cols = date_columns or set()

        staging_table = f"{table_name}_staging"

        try:
            parquet_file = pq.ParquetFile(data_path)
            total_rows = parquet_file.metadata.num_rows
            self._log(f"Loading {total_rows:,} rows from Parquet (SQL-optimized)...")

            # Step 1: Create staging table with raw types
            self._log("Creating staging table with raw types...")
            self._create_staging_table(
                conn,
                table_name,
                staging_table,
                columns,
                effective_timestamp_cols,
                effective_date_cols,
            )

            # Step 2: Stream raw data to staging table (no Python transforms)
            batch_size = 500_000  # Larger batches since no Python transforms
            loaded_rows = 0

            for batch in parquet_file.iter_batches(batch_size=batch_size):
                # Convert to list of tuples - raw values, no transformations
                # Use to_pydict() for faster conversion than pandas
                batch_dict = batch.to_pydict()
                num_rows = len(batch_dict[columns[0]])

                # Build tuples directly from pyarrow dict (faster than pandas)
                data = [
                    tuple(batch_dict[col][i] for col in columns)
                    for i in range(num_rows)
                ]

                conn.import_from_iterable(data, table=staging_table)
                loaded_rows += len(data)

                if loaded_rows % 1_000_000 == 0:
                    self._log(f"  Staged {loaded_rows:,} / {total_rows:,} rows...")

            self._log(f"Staged {loaded_rows:,} rows. Transforming with SQL...")

            # Step 3: INSERT SELECT with SQL transformations
            transform_sql = self._build_transform_sql(
                table_name,
                staging_table,
                columns,
                effective_timestamp_cols,
                effective_date_cols,
            )
            conn.execute(transform_sql)

            # Verify row count
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            final_count = result.fetchone()[0]
            self._log(f"Transformed {final_count:,} rows into {table_name}")

            # Step 4: Drop staging table
            conn.execute(f"DROP TABLE IF EXISTS {staging_table}")
            self._log("Staging table dropped")

            return True

        except Exception as e:
            self._log(f"Failed to load Parquet data: {e}")
            # Cleanup staging table on error
            try:
                conn.execute(f"DROP TABLE IF EXISTS {staging_table}")
            except Exception:
                pass
            return False

    def _create_staging_table(
        self,
        conn: Any,
        source_table: str,
        staging_table: str,
        columns: list[str],
        timestamp_columns: set[str],
        date_columns: set[str],
    ) -> None:
        """Create staging table with raw integer types for timestamp/date columns."""
        # Get column definitions from source table
        result = conn.execute(
            f"SELECT COLUMN_NAME, COLUMN_TYPE FROM EXA_ALL_COLUMNS "
            f"WHERE COLUMN_TABLE = UPPER('{source_table}') "
            f"ORDER BY COLUMN_ORDINAL_POSITION"
        )
        col_defs = {row[0]: row[1] for row in result}

        # Build staging table DDL with raw types for timestamp/date columns
        staging_cols = []
        for col in columns:
            col_upper = col.upper()
            if col in timestamp_columns:
                # Raw epoch seconds as DECIMAL
                staging_cols.append(f'"{col}" DECIMAL(18,0)')
            elif col in date_columns:
                # Raw days since epoch as DECIMAL
                staging_cols.append(f'"{col}" DECIMAL(10,0)')
            elif col_upper in col_defs:
                staging_cols.append(f'"{col}" {col_defs[col_upper]}')
            else:
                # Fallback for unknown columns
                staging_cols.append(f'"{col}" VARCHAR(2000000)')

        ddl = f"CREATE TABLE {staging_table} ({', '.join(staging_cols)})"
        conn.execute(f"DROP TABLE IF EXISTS {staging_table}")
        conn.execute(ddl)

    def _build_transform_sql(
        self,
        target_table: str,
        staging_table: str,
        columns: list[str],
        timestamp_columns: set[str],
        date_columns: set[str],
    ) -> str:
        """Build INSERT SELECT with SQL transformations for timestamps/dates."""
        select_cols = []
        for col in columns:
            if col in timestamp_columns:
                # FROM_POSIX_TIME converts Unix epoch seconds to TIMESTAMP
                select_cols.append(f'FROM_POSIX_TIME("{col}") AS "{col}"')
            elif col in date_columns:
                # ADD_DAYS adds days to epoch date (1970-01-01)
                select_cols.append(f'ADD_DAYS(DATE \'1970-01-01\', "{col}") AS "{col}"')
            else:
                select_cols.append(f'"{col}"')

        return f"""
            INSERT INTO {target_table}
            SELECT {', '.join(select_cols)}
            FROM {staging_table}
        """

    def load_data_parallel(
        self,
        table_name: str,
        schema: str,
        columns: list[str],
        num_workers: int = 16,
        timestamp_cols: set[str] | None = None,
        date_cols: set[str] | None = None,
    ) -> bool:
        """Load data using parallel parquet partition loading.

        Uses pre-partitioned parquet files loaded in parallel via ProcessPoolExecutor.
        Each worker downloads its assigned partitions and loads into staging tables,
        then a final merge combines all data into the target table.

        This approach is ~4-6x faster than single-file sequential loading
        due to parallel downloads and parallel database inserts.

        Args:
            table_name: Target table name (must already exist)
            schema: Schema name containing the target table
            columns: List of column names in the target table
            num_workers: Number of parallel worker processes (default: 16)
            timestamp_cols: Column names containing Unix timestamps (from workload)
            date_cols: Column names containing dates as days since epoch (from workload)

        Returns:
            True if all partitions loaded successfully
        """
        from benchkit.systems.exasol.parallel_loader import load_partitions_parallel

        system = self._system

        # Connection params for worker processes (must be picklable)
        # Each worker creates its own connection to Exasol
        conn_params = {
            "dsn": f"{system.host}:{system.port}",
            "user": system.username,
            "password": system.password,
            "schema": schema,
        }

        # Use workload-provided column metadata for SQL transformations
        # Empty sets if not provided (no transformations needed)
        effective_timestamp_cols = timestamp_cols or set()
        effective_date_cols = date_cols or set()

        self._log(f"Starting parallel parquet load into {schema}.{table_name}")
        self._log(f"Using {num_workers} parallel workers for 100 partitions")

        return load_partitions_parallel(
            conn_params=conn_params,
            schema=schema,
            target_table=table_name,
            columns=columns,
            timestamp_cols=effective_timestamp_cols,
            date_cols=effective_date_cols,
            num_workers=num_workers,
        )

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """Load data from an iterable source.

        Args:
            table_name: Target table name
            data_source: Iterable data source
            data_format: Format of the data (DATA_LIST or file-like)
            **kwargs: Additional options including 'schema'

        Returns:
            True if data loaded successfully
        """

        system = self._system
        schema_name: str = kwargs.get("schema", "benchmark")
        conn: pyexasol.ExaConnection | None = None

        try:
            conn = system._get_connection(compression=False)
            if not conn:
                return False
            if not system._schema_created:
                if system._schema_exists(conn, schema_name):
                    system._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            self._log(f"Loading ({data_format}) into {schema_name}.{table_name}...")
            if data_format == DataFormat.DATA_LIST:
                conn.import_from_iterable(data_source, table=table_name)
            else:
                conn.import_from_file(data_source, table_name, import_params={})

            # Verify data was loaded
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load_data_from_http_url(
        self,
        table_name: str,
        url: str,
        schema: str,
        format: str = "tsv",
        columns: list[str] | None = None,
        expected_rows: int | None = None,
    ) -> bool:
        """Load data directly from HTTP URL using Exasol IMPORT statement.

        Exasol automatically handles .gz decompression for compressed files.
        This method eliminates the need to download data locally first.

        Args:
            table_name: Name of target table
            url: HTTP(S) URL to data file
            schema: Schema name
            format: Data format (tsv or csv)
            columns: Optional list of column names (unused, for API compatibility)
            expected_rows: Optional expected row count for validation (from workload)

        Returns:
            True if successful, False otherwise
        """
        from urllib.parse import urlparse

        system = self._system
        conn = None
        try:
            conn = system._get_connection(compression=False)
            if not conn:
                return False

            if not system._schema_created:
                if system._schema_exists(conn, schema):
                    system._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema}")

            self._log(f"Loading data from {url} into {schema}.{table_name}...")

            # Parse URL into host and file path
            parsed = urlparse(url)
            host_with_scheme = f"{parsed.scheme}://{parsed.netloc}"
            file_path = parsed.path.lstrip("/")

            # Column separator: 0x09 = tab for TSV, default comma for CSV
            column_separator = "COLUMN SEPARATOR = '0x09'" if format == "tsv" else ""

            # REJECT LIMIT allows skipping rows with parsing errors (e.g., unescaped
            # delimiters in fields). ClickBench TSV has some rows with embedded tabs.
            import_sql = f"""
                IMPORT INTO {schema}.{table_name}
                FROM CSV AT '{host_with_scheme}/'
                FILE '{file_path}'
                {column_separator}
                TRIM
                REJECT LIMIT UNLIMITED
            """

            self._log("Executing IMPORT from HTTP (with REJECT LIMIT for bad rows)...")
            conn.execute(import_sql)

            # Verify row count
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")

            # If expected_rows provided (from workload), validate row count
            if expected_rows is not None:
                if row_count < expected_rows * 0.99:  # Allow 1% tolerance for bad rows
                    rejected = expected_rows - row_count
                    self._log(
                        f"Warning: {rejected:,} rows rejected (~{100*rejected/expected_rows:.2f}%)"
                    )
            return True

        except Exception as e:
            self._log(f"Failed to load data from URL: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @exclude_from_package
    def load_data_from_url(
        self,
        schema_name: str,
        table_name: str,
        data_url: str | list[str],
        /,
        extension: str = ".csv",
        **kwargs: Any,
    ) -> bool:
        """Load data from URL(s) using Exasol CSV IMPORT.

        Args:
            schema_name: Schema name
            table_name: Target table name
            data_url: URL or list of URLs to load from
            extension: File extension (unused, for API compatibility)
            **kwargs: Additional options

        Returns:
            True if data loaded successfully
        """
        system = self._system
        conn = None

        # split URL into bases and file names
        data_sources: dict[Path, list[str]] = {}
        for url in [data_url] if isinstance(data_url, str) else data_url:
            p = Path(url)
            prefix: Path = p.parent
            if prefix not in data_sources:
                data_sources[prefix] = [p.name]
            else:
                data_sources[prefix].append(p.name)

        try:
            conn = system._get_connection()
            if not conn:
                return False
            if not system._schema_created:
                if system._schema_exists(conn, schema_name):
                    system._schema_created = True
                    conn.execute(f"OPEN SCHEMA {schema_name}")

            self._log(f"Loading {data_url} into {table_name}...")
            base_sql = f"IMPORT INTO {schema_name}.{table_name} FROM CSV AT "
            for host, files in data_sources.items():
                base_sql += f"'{host}' " + " ".join([f"FILE '{f}'" for f in files])

            conn.execute(base_sql)

            # Verify data was loaded
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False
        finally:
            if conn:
                conn.close()
