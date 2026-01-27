"""DuckDB embedded analytical database system implementation."""

from __future__ import annotations

import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TYPE_CHECKING, Any

try:
    import duckdb
except ModuleNotFoundError:
    duckdb = None  # type: ignore[assignment]

from benchkit.common import DataFormat, exclude_from_package

from ..util import Timer
from .base import SystemUnderTest

if TYPE_CHECKING:
    pass


class DuckdbSystem(SystemUnderTest):
    """DuckDB embedded analytical database system implementation.

    DuckDB is an embedded database that runs in-process (no separate server).
    This makes it simpler than other systems but requires different connection
    lifecycle management.

    Key differences from server-based databases:
    - No Docker support (runs directly in Python process)
    - Single persistent connection stored in _connection
    - Database file created lazily on first connection
    - No network ports required
    """

    # DuckDB is embedded - no multinode support
    SUPPORTS_MULTINODE = False
    # DuckDB can load from iterables
    SUPPORTS_STREAMLOAD = True
    # DuckDB doesn't use external tables (loads data into database file)
    SUPPORTS_EXTERNAL_TABLES = False
    # Embedded in-process, no network overhead - fastest loading
    LOAD_TIMEOUT_MULTIPLIER = 0.6

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required by DuckDB system."""
        return ["duckdb>=1.0.0"]

    @classmethod
    def _get_connection_defaults(cls) -> dict[str, Any]:
        """Return DuckDB-specific connection defaults."""
        return {
            "port": None,  # No network port - embedded database
            "username": None,  # No authentication
            "password": "",
            "schema_key": "database",
            "schema": "main",  # DuckDB default schema
        }

    @classmethod
    def get_valid_setup_methods(cls) -> list[str]:
        """Return valid setup methods for DuckDB.

        DuckDB is embedded - no Docker support, only native/preinstalled.
        """
        return ["native", "preinstalled"]

    @classmethod
    def get_required_ports(cls) -> dict[str, int]:
        """Return ports required by DuckDB (none - embedded database)."""
        return {}

    def get_storage_config(self) -> tuple[str | None, str]:
        """Return DuckDB-specific storage configuration."""
        return "/data/duckdb", "ubuntu:ubuntu"

    def __init__(
        self,
        config: dict[str, Any],
        output_callback: Callable[[str], None] | None = None,
        workload_config: dict[str, Any] | None = None,
    ):
        super().__init__(config, output_callback, workload_config)
        self.setup_method = self.setup_config.get("method", "native")

        # DuckDB connection settings
        # Database path can be explicit or derived from data_dir
        explicit_db_path = self.setup_config.get("database_path")
        if explicit_db_path:
            if explicit_db_path == ":memory:":
                self.database_path: Path | str = ":memory:"
            else:
                self.database_path = Path(explicit_db_path)
        else:
            # Default: use data_dir/name.duckdb
            self.database_path = Path(str(self.data_dir)) / f"{self.name}.duckdb"

        # Parse extra configuration for DuckDB settings
        extra_config = self.setup_config.get("extra") or {}
        self.memory_limit = extra_config.get("memory_limit")
        self.threads = extra_config.get("threads")

        # Connection management - lazy initialization
        self._connection: Any = None

        # Default schema for queries (DuckDB uses 'main' as default)
        self.schema = self.setup_config.get("schema", "main")

    def _get_connection(self) -> Any:
        """Get or create a DuckDB connection.

        DuckDB connections are lazily created on first use.
        The connection is reused for all subsequent operations.
        """
        if self._connection is not None:
            return self._connection

        if duckdb is None:
            raise RuntimeError(
                "duckdb package not installed. "
                "Install with: pip install duckdb>=0.8.0"
            )

        # Create connection to database
        db_path = str(self.database_path)
        self._log(f"Opening DuckDB database: {db_path}")
        self._connection = duckdb.connect(db_path)

        # Apply configuration settings
        if self.memory_limit:
            self._connection.execute(f"SET memory_limit = '{self.memory_limit}'")
            self._log(f"  Set memory_limit = {self.memory_limit}")

        if self.threads:
            self._connection.execute(f"SET threads = {self.threads}")
            self._log(f"  Set threads = {self.threads}")

        return self._connection

    def _close_connection(self) -> None:
        """Close the DuckDB connection if open."""
        if self._connection is not None:
            try:
                self._connection.close()
            except Exception as e:
                self._log(f"Warning: Error closing DuckDB connection: {e}")
            finally:
                self._connection = None

    @exclude_from_package
    def _install_native(self) -> bool:
        """Install DuckDB natively on local or remote instance."""
        self.record_setup_note("Setting up DuckDB embedded database")

        # For remote execution, install DuckDB and create data directory on remote
        if self._should_execute_remotely():
            return self._install_native_remote()

        # Local installation
        # Verify duckdb package is available
        if duckdb is None:
            self._log("ERROR: duckdb package not installed")
            self._log("Install with: pip install duckdb>=1.0.0")
            return False

        self._log(f"DuckDB version: {duckdb.__version__}")

        # Create data directory if using file-based database
        if self.database_path != ":memory:":
            db_path = Path(self.database_path)
            data_dir = db_path.parent

            if not data_dir.exists():
                self._log(f"Creating data directory: {data_dir}")
                self.record_setup_command(
                    f"mkdir -p {data_dir}",
                    f"Create DuckDB data directory: {data_dir}",
                    "preparation",
                )
                try:
                    data_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self._log(f"Failed to create data directory: {e}")
                    return False

        # Test connection by opening database
        try:
            conn = self._get_connection()
            # Verify basic functionality
            result = conn.execute("SELECT 1 as test").fetchone()
            if result and result[0] == 1:
                self._log("DuckDB connection verified")
            else:
                self._log("DuckDB connection test failed")
                return False
        except Exception as e:
            self._log(f"Failed to connect to DuckDB: {e}")
            return False

        self.record_setup_note(f"DuckDB {duckdb.__version__} ready")
        self.record_setup_note(f"Database path: {self.database_path}")

        # Mark as installed
        self._is_running = True
        self.mark_installed(record=False)

        return True

    @exclude_from_package
    def _install_native_remote(self) -> bool:
        """Install DuckDB on remote cloud instance."""
        self._log("Installing DuckDB on remote instance...")

        mgr = self._cloud_instance_manager
        if not mgr:
            self._log("ERROR: No cloud instance manager available")
            return False

        # Install DuckDB via pip on the remote instance
        self._log("Installing DuckDB Python package...")
        install_cmd = "pip3 install 'duckdb>=1.0.0'"
        result = mgr.run_remote_command(install_cmd, timeout=120)
        if not result.get("success"):
            self._log(f"Failed to install DuckDB: {result.get('stderr', '')}")
            return False

        # Create data directory on remote instance
        if self.database_path != ":memory:":
            db_path = Path(self.database_path)
            data_dir = db_path.parent

            self._log(f"Creating data directory: {data_dir}")
            mkdir_cmd = (
                f"sudo mkdir -p {data_dir} && sudo chown ubuntu:ubuntu {data_dir}"
            )
            self.record_setup_command(
                mkdir_cmd,
                f"Create DuckDB data directory: {data_dir}",
                "preparation",
            )
            result = mgr.run_remote_command(mkdir_cmd, timeout=30)
            if not result.get("success"):
                self._log(
                    f"Failed to create data directory: {result.get('stderr', '')}"
                )
                return False

        # Verify DuckDB installation
        self._log("Verifying DuckDB installation...")
        verify_cmd = "python3 -c \"import duckdb; print(f'DuckDB {duckdb.__version__} installed')\""
        result = mgr.run_remote_command(verify_cmd, timeout=30)
        if not result.get("success"):
            self._log(f"DuckDB verification failed: {result.get('stderr', '')}")
            return False

        version_output = result.get("stdout", "").strip()
        self._log(version_output)
        self.record_setup_note(version_output)
        self.record_setup_note(f"Database path: {self.database_path}")

        # Mark as installed
        self._is_running = True
        self.mark_installed(record=False)

        return True

    @exclude_from_package
    def _verify_preinstalled(self) -> bool:
        """Verify that DuckDB is available and database is accessible."""
        # For remote execution, verify via SSH
        if self._should_execute_remotely():
            return self._verify_preinstalled_remote()

        # Local verification
        if duckdb is None:
            self._log("ERROR: duckdb package not installed")
            return False

        # If database file should exist, verify it
        if self.database_path != ":memory:":
            db_path = Path(self.database_path)
            if not db_path.exists():
                self._log(f"Database file not found: {db_path}")
                # For preinstalled, we expect the file to exist
                # But we'll create it if it doesn't (might be first run)
                self._log("Creating new database file...")

        return self.is_healthy()

    @exclude_from_package
    def _verify_preinstalled_remote(self) -> bool:
        """Verify DuckDB is available on remote instance."""
        if not self._cloud_instance_manager:
            return False

        # Check if DuckDB is installed
        check_cmd = 'python3 -c "import duckdb; print(duckdb.__version__)"'
        result = self._cloud_instance_manager.run_remote_command(
            check_cmd, timeout=30, debug=False
        )
        if not result.get("success"):
            self._log("DuckDB not installed on remote instance")
            return False

        self._log(
            f"DuckDB {result.get('stdout', '').strip()} available on remote instance"
        )
        return True

    @exclude_from_package
    def start(self) -> bool:
        """Start the DuckDB system (open connection)."""
        try:
            self._get_connection()
            self._is_running = True
            return True
        except Exception as e:
            self._log(f"Failed to start DuckDB: {e}")
            return False

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if DuckDB is accessible and responding."""
        # For remote execution, check via SSH
        if self._should_execute_remotely():
            return self._is_healthy_remote(quiet)

        # Local health check
        try:
            if duckdb is None:
                if not quiet:
                    self._log("duckdb package not available")
                return False

            conn = self._get_connection()
            result = conn.execute("SELECT 1").fetchone()
            return result is not None and result[0] == 1
        except Exception as e:
            if not quiet:
                self._log(f"DuckDB health check failed: {e}")
            return False

    def _is_healthy_remote(self, quiet: bool = False) -> bool:
        """Check DuckDB health on remote instance."""
        if not self._cloud_instance_manager:
            return False

        try:
            # Test DuckDB by running a simple query
            db_path = str(self.database_path)
            check_cmd = f"python3 -c \"import duckdb; conn = duckdb.connect('{db_path}'); print(conn.execute('SELECT 1').fetchone()[0])\""
            result = self._cloud_instance_manager.run_remote_command(
                check_cmd, timeout=30, debug=False
            )
            if result.get("success"):
                stdout: str = result.get("stdout", "").strip()
                return bool(stdout == "1")
            return False
        except Exception as e:
            if not quiet:
                self._log(f"Remote DuckDB health check failed: {e}")
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a schema in DuckDB."""
        try:
            conn = self._get_connection()
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            self.schema = schema_name
            self._log(f"Created schema: {schema_name}")
            return True
        except Exception as e:
            self._log(f"Failed to create schema '{schema_name}': {e}")
            return False

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into DuckDB table using native file readers.

        DuckDB has highly optimized native readers for various formats:
        - Parquet: read_parquet()
        - CSV: read_csv_auto()
        - TSV: read_csv_auto() with delimiter
        - TBL (pipe-delimited): read_csv_auto() with delimiter
        """
        schema_name = kwargs.get("schema", self.schema or "main")
        data_format = kwargs.get("format", "csv")

        try:
            conn = self._get_connection()
            full_table_name = f"{schema_name}.{table_name}"

            self._log(
                f"Loading {data_path} into {full_table_name} (format: {data_format})..."
            )

            # Build appropriate COPY/INSERT command based on format
            if data_format == "parquet":
                # Use DuckDB's native parquet reader
                query = f"""
                    INSERT INTO {full_table_name}
                    SELECT * FROM read_parquet('{data_path}')
                """
            elif data_format == "tsv":
                # TSV format - tab delimited, no header
                query = f"""
                    INSERT INTO {full_table_name}
                    SELECT * FROM read_csv_auto(
                        '{data_path}',
                        delim = '\t',
                        header = false
                    )
                """
            elif data_format == "tbl":
                # TPC-H .tbl files - pipe delimited with trailing pipe
                # The trailing pipe creates an extra empty column we need to exclude
                # First, get the target table's column count
                table_cols_result = conn.execute(
                    f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                """
                ).fetchall()
                num_cols = len(table_cols_result)

                # Detect column naming pattern by sampling the file
                # DuckDB uses zero-padding when there are 10+ columns
                sample = conn.execute(
                    f"""
                    SELECT * FROM read_csv_auto(
                        '{data_path}',
                        delim = '|',
                        header = false
                    ) LIMIT 1
                """
                ).fetchdf()
                file_col_names = sample.columns.tolist()

                # Use the first num_cols columns from the file (excludes trailing empty column)
                col_list = ", ".join(file_col_names[:num_cols])
                query = f"""
                    INSERT INTO {full_table_name}
                    SELECT {col_list} FROM read_csv_auto(
                        '{data_path}',
                        delim = '|',
                        header = false
                    )
                """
            else:
                # Default CSV format
                query = f"""
                    INSERT INTO {full_table_name}
                    SELECT * FROM read_csv_auto(
                        '{data_path}',
                        header = false
                    )
                """

            conn.execute(query)

            # Verify row count
            count_result = conn.execute(
                f"SELECT COUNT(*) FROM {full_table_name}"
            ).fetchone()
            row_count = count_result[0] if count_result else 0

            self._log(f"Successfully loaded {row_count:,} rows into {table_name}")
            return True

        except Exception as e:
            self._log(f"Failed to load data into {table_name}: {e}")
            return False

    def load_data_from_iterable(
        self,
        table_name: str,
        data_source: Iterable[Any],
        data_format: DataFormat,
        **kwargs: Any,
    ) -> bool:
        """Load data into DuckDB from an iterable.

        Supports:
        - DATA_LIST: Direct insertion using executemany
        - Text formats (CSV, TSV, TBL): Write to temp file then load
        """
        schema_name = kwargs.get("schema", self.schema or "main")
        full_table_name = f"{schema_name}.{table_name}"

        try:
            conn = self._get_connection()

            if data_format == DataFormat.DATA_LIST:
                # Direct insertion using executemany
                # Convert iterable to list for counting
                data_list = list(data_source)
                if not data_list:
                    self._log(f"No data to load into {table_name}")
                    return True

                # Get column count from first row
                first_row = data_list[0]
                placeholders = ", ".join(["?"] * len(first_row))
                insert_sql = f"INSERT INTO {full_table_name} VALUES ({placeholders})"

                conn.executemany(insert_sql, data_list)
                self._log(f"Loaded {len(data_list):,} rows into {table_name}")
                return True

            else:
                # For text formats, write to temp file and load
                # Determine delimiter based on format
                if data_format == DataFormat.TSV:
                    delimiter = "\t"
                    suffix = ".tsv"
                elif data_format == DataFormat.TBL:
                    delimiter = "|"
                    suffix = ".tbl"
                else:  # CSV
                    delimiter = ","
                    suffix = ".csv"

                # Write data to temp file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=suffix, delete=False
                ) as f:
                    for row in data_source:
                        if isinstance(row, str):
                            f.write(row)
                            if not row.endswith("\n"):
                                f.write("\n")
                        else:
                            # Assume it's a sequence - join with delimiter
                            f.write(delimiter.join(str(v) for v in row) + "\n")
                    temp_path = f.name

                try:
                    # Load from temp file
                    query = f"""
                        INSERT INTO {full_table_name}
                        SELECT * FROM read_csv_auto(
                            '{temp_path}',
                            delim = '{delimiter}',
                            header = false
                        )
                    """
                    conn.execute(query)

                    # Get row count
                    count_result = conn.execute(
                        f"SELECT COUNT(*) FROM {full_table_name}"
                    ).fetchone()
                    row_count = count_result[0] if count_result else 0
                    self._log(f"Loaded {row_count:,} rows into {table_name}")
                    return True

                finally:
                    # Clean up temp file
                    Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            self._log(f"Failed to load data from iterable into {table_name}: {e}")
            return False

    def execute_query(
        self,
        query: str,
        query_name: str | None = None,
        return_data: bool = False,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute a SQL query and return timing and result information.

        Args:
            query: SQL query to execute
            query_name: Optional name for the query (for logging)
            return_data: If True, include result data in response as DataFrame
            timeout: Ignored for DuckDB (no query timeout support in Python API)

        Returns:
            Dictionary with success, elapsed_s, rows_returned, error, query_name, data
        """
        from ..debug import debug_print

        if not query_name:
            query_name = "unnamed_query"

        try:
            debug_print(f"Executing query: {query_name}")
            if len(query) > 200:
                debug_print(f"SQL: {query[:200]}...")
            else:
                debug_print(f"SQL: {query}")

            with Timer(f"Query {query_name}") as timer:
                conn = self._get_connection()

                # Use active schema if set (from workload), else fall back to instance schema
                schema_to_use = getattr(self, "_active_schema", None) or self.schema
                if schema_to_use and schema_to_use != "main":
                    # Set the schema context
                    conn.execute(f"SET search_path = '{schema_to_use}'")

                # Strip comments from beginning to detect query type
                query_stripped = query.strip()
                while query_stripped.startswith("--"):
                    newline_pos = query_stripped.find("\n")
                    if newline_pos == -1:
                        query_stripped = ""
                        break
                    query_stripped = query_stripped[newline_pos + 1 :].strip()

                # Execute query
                result = conn.execute(query)

                # Determine if this is a SELECT-like query
                is_select = query_stripped.upper().startswith(
                    ("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN")
                )

                if is_select:
                    # Fetch results
                    if return_data:
                        # DuckDB's fetchdf() returns a pandas DataFrame directly
                        df = result.fetchdf()
                        rows_returned = len(df)
                    else:
                        rows = result.fetchall()
                        rows_returned = len(rows)
                        df = None
                else:
                    # DDL/DML - no result rows
                    rows_returned = 0
                    df = None

            response: dict[str, Any] = {
                "success": True,
                "elapsed_s": timer.elapsed,
                "rows_returned": rows_returned,
                "query_name": query_name,
                "error": None,
            }

            if return_data and df is not None:
                response["data"] = df

            return response

        except Exception as e:
            elapsed = timer.elapsed if "timer" in locals() else 0
            return {
                "success": False,
                "elapsed_s": elapsed,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e),
            }

    def get_system_metrics(self) -> dict[str, Any]:
        """Get DuckDB-specific system metrics."""
        metrics: dict[str, Any] = {}

        try:
            conn = self._get_connection()

            # Database file size
            if self.database_path != ":memory:":
                db_path = Path(self.database_path)
                if db_path.exists():
                    size_bytes = db_path.stat().st_size
                    metrics["database_size_bytes"] = size_bytes
                    metrics["database_size_mb"] = size_bytes / (1024 * 1024)

            # DuckDB settings
            if self.memory_limit:
                metrics["memory_limit"] = self.memory_limit
            if self.threads:
                metrics["threads"] = self.threads

            # Get DuckDB version
            if duckdb:
                metrics["duckdb_version"] = duckdb.__version__

            # Query some DuckDB pragmas
            try:
                result = conn.execute("SELECT current_setting('threads')").fetchone()
                if result:
                    metrics["current_threads"] = result[0]
            except Exception:
                pass  # Setting might not be available

            try:
                result = conn.execute(
                    "SELECT current_setting('memory_limit')"
                ).fetchone()
                if result:
                    metrics["current_memory_limit"] = result[0]
            except Exception:
                pass

        except Exception as e:
            metrics["error"] = str(e)

        return metrics

    def teardown(self) -> bool:
        """Clean up DuckDB resources."""
        success = True

        # Close connection
        self._close_connection()
        self._is_running = False

        # Optionally remove database file
        if self.setup_config.get("cleanup_data", False):
            if self.database_path != ":memory:":
                db_path = Path(self.database_path)
                if db_path.exists():
                    try:
                        db_path.unlink()
                        self._log(f"Removed database file: {db_path}")
                    except Exception as e:
                        self._log(f"Failed to remove database file: {e}")
                        success = False

            # Clean up data directory
            success = success and self.cleanup_data_directory()

        return success

    @exclude_from_package
    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """Get DuckDB connection info (for documentation purposes)."""
        db_path = self.database_path
        if db_path == ":memory:":
            return "duckdb.connect(':memory:')"
        return f"duckdb.connect('{db_path}')"

    @exclude_from_package
    def is_already_installed(self) -> bool:
        """Check if DuckDB is already installed and ready."""
        if duckdb is None:
            return False

        # Check for installation marker
        if not self.has_install_marker():
            return False

        # Verify database is accessible
        return self.is_healthy(quiet=True)

    def _should_execute_remotely(self) -> bool:
        """Check if commands should execute on remote cloud instance.

        DuckDB is embedded and runs in-process, but when deployed to AWS,
        the benchmark package is transferred to the remote instance and
        executed there. In this case, setup commands (like creating data
        directories) should run on the remote instance.
        """
        return self._cloud_instance_manager is not None
