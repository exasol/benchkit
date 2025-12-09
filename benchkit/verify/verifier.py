"""Query result verification logic."""

from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]
from rich.console import Console

from ..debug import debug_print
from ..systems import create_system
from ..workloads import create_workload

console = Console()


def _resolve_infrastructure_ips(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """
    Load IPs from Terraform state and inject into system configs.

    For AWS/cloud deployments, the config often uses environment variable placeholders
    like $EXASOL_PUBLIC_IP. These are set during `run` but not during `verify`.
    This function reads the actual IPs from Terraform state and injects them directly.

    Args:
        config: The benchmark configuration dictionary
        output_dir: Results directory containing terraform/ subdirectory

    Returns:
        Modified config with resolved IP addresses
    """
    import copy

    from ..infra.manager import InfraManager

    # Check if this is a cloud deployment
    env_mode = config.get("env", {}).get("mode", "local")
    if env_mode == "local":
        return config  # No infrastructure to resolve for local mode

    # Check if terraform directory exists in results
    terraform_dir = output_dir / "terraform"
    if not terraform_dir.exists():
        debug_print(f"No terraform directory found at {terraform_dir}")
        return config

    try:
        provider = env_mode
        infra_manager = InfraManager(provider, config)

        # Override working directory to use results terraform state
        infra_manager.working_dir = terraform_dir

        result = infra_manager._run_terraform_command("output", ["-json"])
        if not result.success:
            debug_print(f"Failed to get terraform outputs: {result.error}")
            return config

        outputs = result.outputs or {}
        public_ips = outputs.get("system_public_ips", {})

        if not public_ips:
            debug_print("No system_public_ips found in terraform outputs")
            return config

        # Deep copy config to avoid modifying original
        resolved_config = copy.deepcopy(config)

        # Inject IPs into system configs
        for system_config in resolved_config["systems"]:
            system_name = system_config["name"]
            if system_name in public_ips:
                ips = public_ips[system_name]
                # Use first IP for client connections (distributed routing is internal)
                resolved_ip = ips[0] if isinstance(ips, list) else ips

                setup = system_config.get("setup", {})

                # Check if host contains an unresolved env var or is empty
                current_host = setup.get("host", "")
                if current_host.startswith("$") or not current_host:
                    setup["host"] = resolved_ip
                    debug_print(f"Resolved {system_name} host to {resolved_ip}")

                # Same for host_external_addrs (used by Exasol)
                current_external = setup.get("host_external_addrs", "")
                if current_external.startswith("$") or not current_external:
                    setup["host_external_addrs"] = resolved_ip
                    debug_print(
                        f"Resolved {system_name} host_external_addrs to {resolved_ip}"
                    )

        console.print(
            f"[dim]Resolved infrastructure IPs from {terraform_dir}[/dim]"
        )
        return resolved_config

    except Exception as e:
        debug_print(f"Failed to resolve infrastructure IPs: {e}")
        return config  # Fall back to original config


class QueryVerifier:
    """Verifies query results against expected data."""

    def __init__(self, config: dict[str, Any], output_dir: Path):
        self.config = config
        self.output_dir = Path(output_dir)
        self.project_id = config["project_id"]

        # Get workload info
        self.workload_config = config["workload"]
        self.workload_name = self.workload_config["name"]
        self.scale_factor = self.workload_config["scale_factor"]

        # Get queries to verify - default to all if not specified
        queries_config = self.workload_config.get("queries", {})
        queries_include = queries_config.get("include", [])

        if queries_include:
            self.queries_to_verify = queries_include
        else:
            # Default to all queries when not specified
            workload = create_workload(self.workload_config)
            self.queries_to_verify = list(workload.get_all_query_names())

        # Verify data directory
        self.verify_data_dir = (
            Path(__file__).parent.parent.parent
            / "workloads"
            / self.workload_name
            / "verify"
            / f"sf{self.scale_factor}"
        )

        debug_print(
            f"Workload: {self.workload_name}, Scale Factor: {self.scale_factor}"
        )
        debug_print(f"Verify data directory: {self.verify_data_dir}")
        debug_print(f"Queries to verify: {self.queries_to_verify}")

    def verify_scale_factor_available(self) -> bool:
        """Check if verify data is available for the configured scale factor."""
        if not self.verify_data_dir.exists():
            console.print(
                f"[red]No verification data available for scale factor {self.scale_factor}[/red]"
            )
            console.print(
                f"[yellow]Expected directory: {self.verify_data_dir}[/yellow]"
            )
            return False

        debug_print(f"Verify data directory exists: {self.verify_data_dir}")
        return True

    def execute_queries_and_save(self, system_config: dict[str, Any]) -> bool:
        """Execute queries on a system and save results as parquet files."""
        system_name = system_config["name"]
        console.print(f"\n[blue]Executing queries on {system_name}...[/blue]")

        # Create system instance
        system = create_system(system_config)

        # Create workload instance
        workload = create_workload(self.workload_config)

        # Create output directory for this system's verify results
        system_verify_dir = self.output_dir / system_name / "verify"
        system_verify_dir.mkdir(parents=True, exist_ok=True)

        debug_print(f"Output directory for {system_name}: {system_verify_dir}")

        # Check if system is healthy
        if not system.is_healthy(quiet=True):
            console.print(f"[red]System {system_name} is not healthy[/red]")
            return False

        # Get queries for this system
        queries = workload.get_queries(system)

        # Execute each query and save results
        for query_name in self.queries_to_verify:
            if query_name not in queries:
                console.print(
                    f"[yellow]Query {query_name} not found in workload[/yellow]"
                )
                continue

            query_sql = queries[query_name]

            # Format query with schema name
            schema_name = workload.get_schema_name()
            formatted_sql = query_sql.format(schema=schema_name)

            console.print(f"  Executing {query_name}...")
            debug_print(f"Query SQL: {formatted_sql[:200]}...")

            # Execute query with data return enabled
            result = system.execute_query(
                formatted_sql, query_name=query_name, return_data=True
            )

            if not result.get("success"):
                console.print(
                    f"[red]  Failed to execute {query_name}: {result.get('error')}[/red]"
                )
                return False

            # Get result data
            result_data = result.get("data")
            debug_print(f"Result keys: {result.keys()}")
            debug_print(f"Result data type: {type(result_data)}")
            if result_data is not None:
                debug_print(
                    f"Result data shape: {result_data.shape if hasattr(result_data, 'shape') else len(result_data)}"
                )

            if result_data is None:
                console.print(f"[yellow]  No data returned for {query_name}[/yellow]")
                continue

            # Convert to DataFrame
            if isinstance(result_data, pd.DataFrame):
                df = result_data
            else:
                df = pd.DataFrame(result_data)

            # Normalize column names to lowercase for consistent comparison
            df.columns = [col.lower() for col in df.columns]

            # Convert query name to lowercase for filename (q1, q3, etc.)
            # Strip leading zeros from query numbers (Q01 -> q1)
            query_filename = query_name.lower().replace("q0", "q") + ".parquet"
            output_file = system_verify_dir / query_filename

            # Save as parquet
            table = pa.Table.from_pandas(df)
            pq.write_table(table, output_file)

            console.print(f"  [green]✓ {query_name} saved to {output_file}[/green]")
            debug_print(f"Result shape: {df.shape}")

        return True

    def compare_results(self, system_name: str) -> dict[str, Any]:
        """Compare system results with expected verify data."""
        console.print(f"\n[blue]Comparing results for {system_name}...[/blue]")

        system_verify_dir = self.output_dir / system_name / "verify"

        comparison_results: dict[str, Any] = {
            "system": system_name,
            "queries": {},
            "all_passed": True,
        }

        for query_name in self.queries_to_verify:
            # Convert query name to lowercase and strip leading zeros (Q01 -> q1)
            query_filename = query_name.lower().replace("q0", "q") + ".parquet"

            expected_file = self.verify_data_dir / query_filename
            actual_file = system_verify_dir / query_filename

            if not expected_file.exists():
                console.print(f"[yellow]  {query_name}: No expected data file[/yellow]")
                comparison_results["queries"][query_name] = {
                    "status": "skipped",
                    "reason": "No expected data",
                }
                continue

            if not actual_file.exists():
                console.print(f"[red]  {query_name}: No actual results file[/red]")
                comparison_results["queries"][query_name] = {
                    "status": "failed",
                    "reason": "No actual results",
                }
                comparison_results["all_passed"] = False
                continue

            # Load both parquet files
            expected_df = pq.read_table(expected_file).to_pandas()
            actual_df = pq.read_table(actual_file).to_pandas()

            # Normalize column names to lowercase for consistent comparison
            expected_df.columns = [col.lower() for col in expected_df.columns]
            actual_df.columns = [col.lower() for col in actual_df.columns]

            debug_print(
                f"{query_name} - Expected shape: {expected_df.shape}, Actual shape: {actual_df.shape}"
            )

            # Compare results
            comparison = self._compare_dataframes(expected_df, actual_df, query_name)
            comparison_results["queries"][query_name] = comparison

            if comparison["status"] == "passed":
                console.print(f"  [green]✓ {query_name}: Results match[/green]")
            else:
                console.print(f"  [red]✗ {query_name}: {comparison['reason']}[/red]")
                comparison_results["all_passed"] = False

        return comparison_results

    def _compare_dataframes(
        self, expected: pd.DataFrame, actual: pd.DataFrame, query_name: str
    ) -> dict[str, Any]:
        """Compare two DataFrames for equality, ignoring column names and row order."""
        from ..debug import debug_print

        # Check row count first
        if len(expected) != len(actual):
            return {
                "status": "failed",
                "reason": f"Row count mismatch: expected {len(expected)} rows, got {len(actual)} rows",
            }

        # Check column count
        if len(expected.columns) != len(actual.columns):
            return {
                "status": "failed",
                "reason": f"Column count mismatch: expected {len(expected.columns)} columns, got {len(actual.columns)} columns",
            }

        # Rename actual columns to match expected (column names don't matter, only data)
        actual.columns = expected.columns

        # Convert object columns to numeric for both DataFrames (for Decimal types)
        # Also normalize dates and strip whitespace from string columns (CHAR fields have trailing spaces)
        import warnings

        for df in [expected, actual]:
            for col in df.columns:
                if df[col].dtype == "object":
                    try:
                        # Try to convert to numeric first
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        # Try to convert to datetime (handles date columns)
                        try:
                            # Suppress the format inference warning
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                df[col] = pd.to_datetime(df[col])
                        except (ValueError, TypeError, pd.errors.ParserError):
                            # If not date, strip whitespace from strings
                            try:
                                df[col] = df[col].str.strip()
                            except AttributeError:
                                pass  # Not a string column

        # Round numeric columns to match the smallest decimal precision between expected and actual
        # This handles cases where one system returns full precision and another rounds
        for col in expected.columns:
            if pd.api.types.is_numeric_dtype(
                expected[col]
            ) and pd.api.types.is_numeric_dtype(actual[col]):
                # Determine decimal places in expected data
                expected_decimals = self._get_decimal_places(expected[col])
                actual_decimals = self._get_decimal_places(actual[col])

                # Round both to the smaller precision (usually expected is rounded)
                target_decimals = min(expected_decimals, actual_decimals)
                if (
                    target_decimals < 10
                ):  # Only round if there's actual rounding (not full precision)
                    expected[col] = expected[col].round(target_decimals)
                    actual[col] = actual[col].round(target_decimals)
                    debug_print(
                        f"{query_name} - Rounded column '{col}' to {target_decimals} decimal places"
                    )

        debug_print(
            f"{query_name} - Comparing {len(expected)} rows, {len(expected.columns)} columns"
        )

        # Sort both dataframes by all columns for consistent comparison
        # Use a more robust sorting that handles NaN and mixed types
        try:
            expected_sorted = expected.sort_values(
                by=list(expected.columns), na_position="last"
            ).reset_index(drop=True)
            actual_sorted = actual.sort_values(
                by=list(actual.columns), na_position="last"
            ).reset_index(drop=True)
        except Exception as e:
            debug_print(f"Warning: Could not sort dataframes: {e}")
            # If sorting fails, just use reset index without sorting
            expected_sorted = expected.reset_index(drop=True)
            actual_sorted = actual.reset_index(drop=True)

        # Compare values with tolerance for floating point
        try:
            pd.testing.assert_frame_equal(
                expected_sorted,
                actual_sorted,
                check_dtype=False,  # Don't check exact dtype match
                rtol=1e-5,  # Relative tolerance for floats
                atol=1e-8,  # Absolute tolerance for floats
            )
            return {
                "status": "passed",
                "rows": len(expected),
                "columns": len(expected.columns),
            }
        except AssertionError as e:
            error_msg = str(e)
            # Truncate long error messages
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
            return {"status": "failed", "reason": f"Data mismatch: {error_msg}"}

    def _get_decimal_places(self, series: pd.Series) -> int:
        """
        Determine the maximum number of decimal places in a numeric series.

        Args:
            series: Pandas Series with numeric data

        Returns:
            Maximum number of decimal places found (or 10 if no clear pattern)
        """
        import decimal

        max_decimals = 0
        for val in series:
            if pd.isna(val):
                continue

            # Convert to string to count decimal places
            val_str = str(val)

            # Handle scientific notation
            if "e" in val_str.lower():
                # Use decimal for proper handling
                dec = decimal.Decimal(str(val))
                # Get the tuple representation
                sign, digits, exponent = dec.as_tuple()
                # exponent can be int or literal 'n', 'N', 'F' for special values
                if isinstance(exponent, int) and exponent < 0:
                    max_decimals = max(max_decimals, abs(exponent))
            elif "." in val_str:
                # Count digits after decimal point
                decimal_part = val_str.split(".")[1]
                # Remove trailing zeros for counting
                decimal_part = decimal_part.rstrip("0")
                max_decimals = max(max_decimals, len(decimal_part))

        # If no decimals found, return 10 (full precision)
        return max_decimals if max_decimals > 0 else 10


def verify_results(
    config: dict[str, Any], output_dir: Path, systems: list[str] | None = None
) -> bool:
    """
    Verify query results against expected data.

    Args:
        config: Benchmark configuration
        output_dir: Directory to save verification results
        systems: Optional list of system names to verify (default: all)

    Returns:
        True if all verifications passed, False otherwise
    """
    # Resolve infrastructure IPs from Terraform state for cloud deployments
    # This handles cases where config uses $VARIABLE placeholders that aren't set
    resolved_config = _resolve_infrastructure_ips(config, output_dir)

    verifier = QueryVerifier(resolved_config, output_dir)

    # Check if verify data is available for this scale factor
    if not verifier.verify_scale_factor_available():
        return False

    # Filter systems if specified
    systems_to_verify = resolved_config["systems"]
    if systems:
        systems_to_verify = [s for s in systems_to_verify if s["name"] in systems]
        if not systems_to_verify:
            console.print(f"[red]No matching systems found: {systems}[/red]")
            return False

    all_passed = True

    # Execute queries and save results for each system
    for system_config in systems_to_verify:
        if not verifier.execute_queries_and_save(system_config):
            all_passed = False
            continue

    # Compare results for each system
    comparison_summary = []
    for system_config in systems_to_verify:
        system_name = system_config["name"]
        comparison = verifier.compare_results(system_name)
        comparison_summary.append(comparison)

        if not comparison["all_passed"]:
            all_passed = False

    # Print summary
    console.print("\n[bold]Verification Summary:[/bold]")
    for summary in comparison_summary:
        system_name = summary["system"]
        status = (
            "[green]PASSED[/green]" if summary["all_passed"] else "[red]FAILED[/red]"
        )
        console.print(f"  {system_name}: {status}")

        # Show query-level details
        for query_name, result in summary["queries"].items():
            status_symbol = "✓" if result["status"] == "passed" else "✗"
            status_color = "green" if result["status"] == "passed" else "red"
            console.print(
                f"    [{status_color}]{status_symbol} {query_name}[/{status_color}]"
            )

    return all_passed
