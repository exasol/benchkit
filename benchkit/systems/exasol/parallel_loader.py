"""Parallel parquet loader using ProcessPoolExecutor.

This module provides parallel data loading for ClickBench using the 100 pre-partitioned
parquet files from the ClickHouse datasets server. Each worker process downloads and
loads its assigned partitions into staging tables, then a final merge combines all
data into the target table.

Key design decisions:
1. ProcessPoolExecutor for clean error handling and as_completed() progress tracking
2. Download-then-load (vs streaming) for reliability with network interruptions
3. Staging tables with raw integer types to avoid Python datetime conversions
4. SQL-based transformations during final merge for maximum performance
"""

from __future__ import annotations

import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

# Partition URL pattern (100 files: hits_0.parquet through hits_99.parquet)
PARTITIONED_URL = (
    "https://datasets.clickhouse.com/hits_compatible/athena_partitioned/hits_{}.parquet"
)


def _create_staging_table(
    conn: Any,
    table_name: str,
    columns: list[str],
    timestamp_cols: set[str],
    date_cols: set[str],
) -> None:
    """Create staging table with raw integer types for timestamp/date columns.

    This avoids Python datetime conversions - we keep timestamps as Unix epoch
    seconds (DECIMAL(18,0)) and dates as days-since-epoch (DECIMAL(10,0)).
    The SQL transformation during merge converts these to proper TIMESTAMP/DATE.
    """
    col_defs = []
    for col in columns:
        if col in timestamp_cols:
            # Unix epoch seconds - fits in DECIMAL(18,0)
            col_defs.append(f'"{col}" DECIMAL(18,0)')
        elif col in date_cols:
            # Days since epoch - fits in DECIMAL(10,0)
            col_defs.append(f'"{col}" DECIMAL(10,0)')
        else:
            # Use VARCHAR(2000000) for all other columns
            # Exasol will coerce types during final INSERT SELECT
            col_defs.append(f'"{col}" VARCHAR(2000000)')

    ddl = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.execute(ddl)


def load_single_partition(
    partition_id: int,
    conn_params: dict[str, Any],
    schema: str,
    columns: list[str],
    timestamp_cols: set[str],
    date_cols: set[str],
) -> tuple[int, bool, str]:
    """Load a single parquet partition into staging table.

    This function runs in a separate process via ProcessPoolExecutor.
    All parameters must be picklable (no database connections).

    Args:
        partition_id: Partition number (0-99)
        conn_params: Dictionary with dsn, user, password for pyexasol.connect()
        schema: Target schema name
        columns: List of column names in order
        timestamp_cols: Set of column names that are Unix timestamps
        date_cols: Set of column names that are days-since-epoch

    Returns:
        Tuple of (partition_id, success, message)
    """
    import ssl

    import pyarrow.parquet as pq  # type: ignore[import-untyped]
    import pyexasol  # type: ignore[import-untyped]

    staging_table = f"hits_part_{partition_id:02d}"
    url = PARTITIONED_URL.format(partition_id)
    tmp_path = None

    try:
        # Download partition to temp file with proper User-Agent
        # (Cloudflare blocks requests without User-Agent)
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        req = Request(url, headers={"User-Agent": "benchkit/1.0 (parallel-loader)"})
        with urlopen(req) as response, open(tmp_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)

        # Connect to Exasol (each worker gets own connection)
        # Add SSL options to disable certificate verification for self-signed certs
        conn_params_with_ssl = conn_params.copy()
        conn_params_with_ssl["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}
        conn = pyexasol.connect(**conn_params_with_ssl)
        conn.execute(f"OPEN SCHEMA {schema}")

        # Create staging table (raw integer types for timestamps/dates)
        _create_staging_table(conn, staging_table, columns, timestamp_cols, date_cols)

        # Load parquet data via import_from_iterable
        parquet_file = pq.ParquetFile(tmp_path)

        # Helper to convert bytes to str (PyArrow returns bytes for some columns)
        def _convert_value(val: Any) -> Any:
            if isinstance(val, bytes):
                return val.decode("utf-8", errors="replace")
            return val

        # Process in batches to manage memory
        total_loaded = 0
        for batch in parquet_file.iter_batches(batch_size=100_000):
            batch_dict = batch.to_pydict()
            num_rows = len(batch_dict[columns[0]])
            data = [
                tuple(_convert_value(batch_dict[col][i]) for col in columns)
                for i in range(num_rows)
            ]
            conn.import_from_iterable(data, table=staging_table)
            total_loaded += num_rows

        conn.close()

        return (partition_id, True, f"Loaded {total_loaded:,} rows")

    except Exception as e:
        return (partition_id, False, str(e))

    finally:
        # Cleanup temp file
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


def _build_transform_sql(
    target: str,
    staging: str,
    columns: list[str],
    timestamp_cols: set[str],
    date_cols: set[str],
) -> str:
    """Build INSERT SELECT with SQL transformations for timestamp/date columns.

    Transforms:
    - Timestamp columns: FROM_POSIX_TIME converts Unix epoch seconds to TIMESTAMP
    - Date columns: ADD_DAYS adds days-since-epoch to 1970-01-01
    - Other columns: direct copy (Exasol handles VARCHAR->native type coercion)
    """
    select_cols = []
    for col in columns:
        if col in timestamp_cols:
            select_cols.append(f'FROM_POSIX_TIME("{col}") AS "{col}"')
        elif col in date_cols:
            select_cols.append(f'ADD_DAYS(DATE \'1970-01-01\', "{col}") AS "{col}"')
        else:
            select_cols.append(f'"{col}"')

    return f"INSERT INTO {target} SELECT {', '.join(select_cols)} FROM {staging}"


def load_partitions_parallel(
    conn_params: dict[str, Any],
    schema: str,
    target_table: str,
    columns: list[str],
    timestamp_cols: set[str],
    date_cols: set[str],
    num_workers: int = 16,
    num_partitions: int = 100,
) -> bool:
    """Load all partitions in parallel, then merge into target table.

    Phase 1: Launch N workers, each loading partitions round-robin style
             (worker 0: 0, N, 2N, ...; worker 1: 1, N+1, 2N+1, ...)
    Phase 2: Merge all staging tables into target table sequentially

    Args:
        conn_params: Connection parameters for pyexasol.connect()
        schema: Target schema name
        target_table: Target table name (must already exist)
        columns: List of column names in order
        timestamp_cols: Set of timestamp column names
        date_cols: Set of date column names
        num_workers: Number of parallel worker processes (default: 16)
        num_partitions: Number of partitions to load (default: 100)

    Returns:
        True if all partitions loaded and merged successfully
    """
    import ssl

    import pyexasol  # type: ignore[import-untyped]

    print(
        f"Starting parallel load with {num_workers} workers "
        f"for {num_partitions} partitions..."
    )
    print("Each worker downloads and loads ~1M rows per partition")

    # Phase 1: Parallel load into staging tables
    completed = 0
    failed = []

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                load_single_partition,
                i,
                conn_params,
                schema,
                columns,
                timestamp_cols,
                date_cols,
            ): i
            for i in range(num_partitions)
        }

        for future in as_completed(futures):
            partition_id, success, message = future.result()
            completed += 1
            status = "✓" if success else "✗"
            print(
                f"[{completed:3d}/{num_partitions}] Partition {partition_id:02d}: {status} {message}"
            )
            if not success:
                failed.append(partition_id)

    if failed:
        print(f"Failed partitions: {failed}")
        return False

    # Phase 2: Merge all staging tables into target (sequential)
    print("\nMerging partitions into target table...")
    conn_params_with_ssl = conn_params.copy()
    conn_params_with_ssl["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}
    conn = pyexasol.connect(**conn_params_with_ssl)
    conn.execute(f"OPEN SCHEMA {schema}")

    for i in range(num_partitions):
        staging_table = f"hits_part_{i:02d}"
        transform_sql = _build_transform_sql(
            target_table, staging_table, columns, timestamp_cols, date_cols
        )
        conn.execute(transform_sql)
        conn.execute(f"DROP TABLE {staging_table}")
        if (i + 1) % 10 == 0:
            print(f"  Merged {i + 1}/{num_partitions} partitions")

    total_rows = conn.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0]
    print(f"Total rows loaded: {total_rows:,}")
    conn.close()

    return True
