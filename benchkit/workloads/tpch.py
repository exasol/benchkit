"""TPC-H benchmark workload implementation."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from benchkit.common.markers import exclude_from_package
from benchkit.systems import SystemUnderTest
from benchkit.util import safe_command

from .base import Workload


class TPCH(Workload):
    """TPC-H benchmark workload implementation."""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required for TPC-H workload."""
        return ["tpchgen-cli>=0.2.0"]  # For TPC-H data generation

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        assert self.generator in ["dbgen", "dbgen-pipe"]

    def generate_data(self, output_dir: Path, force: bool = False) -> bool:
        """Generate TPC-H data using tpchgen-cli (modern Python approach)."""
        if self.generator == "dbgen":
            return self._generate_with_tpchgen_cli(output_dir, force)
        # else: generate data on the fly later
        return True

    def _generate_with_tpchgen_cli(self, output_dir: Path, force: bool = False) -> bool:
        """Generate TPC-H data using tpchgen-cli (modern Python package)."""

        # precheck: is data already there?
        if not force:
            missing: bool = False
            for table in self.get_table_names():
                tbl_file = output_dir / f"{table}.tbl"
                if not tbl_file.exists():
                    missing = True
                    break
            if not missing:
                # all files already there
                return True

        try:
            # Check if tpchgen-cli is available

            result = safe_command("python -m pip show tpchgen-cli")
            if not result["success"]:
                print("tpchgen-cli not found. Install with: pip install tpchgen-cli")
                return False

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate TPC-H data using tpchgen-cli
            # Format: tbl = pipe-delimited files (TPC-H standard)
            cmd = [
                "tpchgen-cli",
                f"--output-dir={output_dir}",
                "--format=tbl",
                f"-s {self.scale_factor}",
            ]

            print(
                f"Generating TPC-H data (scale factor {self.scale_factor}) using tpchgen-cli..."
            )
            result = safe_command(" ".join(cmd), timeout=3600)  # 1 hour timeout

            if not result["success"]:
                print(f"tpchgen-cli failed: {result.get('stderr', 'Unknown error')}")
                return False

            # Verify all table files were created
            missing_files = []
            for table in self.get_table_names():
                tbl_file = output_dir / f"{table}.tbl"
                if not tbl_file.exists():
                    missing_files.append(str(tbl_file))

            if missing_files:
                print(f"Missing data files: {missing_files}")
                return False

            print(f"Successfully generated TPC-H data in {output_dir}")
            return True

        except Exception as e:
            print(f"Data generation failed: {e}")
            return False

    def create_indexes(self, system: SystemUnderTest) -> bool:
        """Create TPC-H indexes using templated setup scripts."""
        return self.execute_setup_script(system, "create_indexes.sql")

    def analyze_tables(self, system: SystemUnderTest) -> bool:
        """Analyze TPC-H tables using templated setup scripts."""
        return self.execute_setup_script(system, "analyze_tables.sql")

    def calculate_statement_timeout(
        self, statement: str, system: SystemUnderTest
    ) -> timedelta:
        # Check if this is an OPTIMIZE operation (ClickHouse specific)
        statement_upper = statement.upper().strip()

        if "OPTIMIZE TABLE" in statement_upper:
            # Base timeout for OPTIMIZE: 10 minutes per SF1
            # Scale factor 100 = ~1000 minutes base for lineitem
            # But we apply table-specific multipliers

            # Determine table being optimized
            table_multipliers = {
                "LINEITEM": 1.0,  # Largest table (~6x orders)
                "ORDERS": 0.25,  # ~25% of lineitem
                "PARTSUPP": 0.13,  # ~13% of lineitem
                "PART": 0.03,  # ~3% of lineitem
                "CUSTOMER": 0.025,  # ~2.5% of lineitem
                "SUPPLIER": 0.002,  # ~0.2% of lineitem
                "NATION": 0.0001,  # Tiny table
                "REGION": 0.0001,  # Tiny table
            }

            # Find which table is being optimized
            multiplier = 0.1  # Default for unknown tables
            for table_name, table_mult in table_multipliers.items():
                if table_name in statement_upper:
                    multiplier = table_mult
                    break

            return system.estimate_execution_time(
                "OPTIMIZE TABLE", self.scale_factor * multiplier
            )

        # For MATERIALIZE STATISTICS, also needs longer timeout
        if "MATERIALIZE STATISTICS" in statement_upper:
            return system.estimate_execution_time(
                "MATERIALIZE STATISTICS", self.scale_factor
            )

        return system.estimate_execution_time("DEFAULT", self.scale_factor)

    def prepare(self, system: SystemUnderTest) -> bool:
        """Complete TPC-H setup process: generate data, create tables, load data, create indexes, analyze tables."""
        print("Setting up TPC-H workload...")

        # Check if system provides a custom data generation directory (e.g., on additional disk)
        custom_data_dir = system.get_data_generation_directory(self)
        if custom_data_dir:
            self.data_dir = Path(custom_data_dir)
            print(f"Using system-provided data directory: {self.data_dir}")

        # Step 0: Generate TPC-H data
        print("0. Generating TPC-H data...")
        if not self.generate_data(self.data_dir):
            print("Failed to generate TPC-H data")
            return False

        # Step 1: Create tables and schema
        print("1. Creating tables and schema...")
        if not self.create_schema(system):
            print("Failed to create schema and tables")
            return False

        # Step 2: Load data
        print("2. Loading data...")
        if not self.load_data(system):
            print("Failed to load data")
            return False

        # Step 3: Create indexes for performance
        print("3. Creating indexes...")
        if not self.create_indexes(system):
            print("Failed to create indexes")
            return False

        # Step 4: Analyze tables for query optimization
        print("4. Analyzing tables...")
        if not self.analyze_tables(system):
            print("Failed to analyze tables")
            return False

        print("TPC-H workload setup completed successfully")
        return True

    def load_data(self, system: SystemUnderTest) -> bool:
        """Load TPC-H data into the database system."""
        if self.generator == "dbgen-pipe" and system.SUPPORTS_STREAMLOAD:
            return self._load_data_from_pipe(system)
        else:
            # note: generate_data should detect things have already happened.
            return self.generate_data(self.data_dir) and self._load_data_from_files(
                system
            )

    def _load_data_from_files(self, system: SystemUnderTest) -> bool:
        schema_name = self.get_schema_name()

        for table_name in self.get_table_names():
            data_file = self.data_dir / f"{table_name}.tbl"

            if not data_file.exists():
                print(f"Data file not found: {data_file}")
                return False

            print(f"Loading {table_name}...")
            columns = self.get_table_columns(table_name)
            success = system.load_data(
                table_name,
                data_file,
                schema=schema_name,
                format=self.data_format,
                columns=columns,
            )

            if not success:
                print(f"Failed to load {table_name}")
                return False

            # Delete data file immediately after successful load to save disk space
            try:
                data_file.unlink()
                print(f"  ✓ Cleaned up {data_file.name}")
            except Exception as e:
                print(f"  Warning: Could not delete {data_file.name}: {e}")

        # Try to remove the empty data directory
        try:
            if self.data_dir.exists() and not any(self.data_dir.iterdir()):
                self.data_dir.rmdir()
                print(f"Cleaned up empty data directory: {self.data_dir}")
        except Exception as e:
            print(f"Warning: Could not remove data directory: {e}")

        return True

    def _load_data_from_pipe(self, system: SystemUnderTest) -> bool:
        from benchkit.common import DataFormat, DbGenPipe

        schema_name = self.get_schema_name()

        for table_name in self.get_table_names():
            print(f"Loading {table_name}...")

            with DbGenPipe(table_name, self.scale_factor) as dbgen:
                if not system.load_data_from_iterable(
                    table_name, dbgen.file_stream(), DataFormat.CSV, schema=schema_name
                ):
                    print(f"Failed to load {table_name}")
                    return False
        return True

    def run_workload(
        self,
        system: SystemUnderTest,
        query_names: list[str],
        runs_per_query: int = 3,
        warmup_runs: int = 1,
        num_streams: int = 1,
        randomize: bool = False,
        random_seed: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Execute the TPC-H workload with system context for template resolution."""
        # Store system context for template resolution
        self._current_system = system

        # Determine the variant used for this system
        variant_for_system = self._get_query_variant_for_system(system)

        # Call parent implementation
        result_dict = super().run_workload(
            system,
            query_names,
            runs_per_query,
            warmup_runs,
            num_streams,
            randomize,
            random_seed,
        )

        # Override variant with the actual variant used for this system
        # (parent uses global config, but we may have per-system overrides)
        for result in result_dict["measured"]:
            result["variant"] = variant_for_system
        for result in result_dict["warmup"]:
            result["variant"] = variant_for_system

        return result_dict

    def get_workload_description(self) -> dict[str, Any]:
        """Return TPC-H workload description."""
        return {
            "short": "TPC-H is an industry-standard decision support benchmark simulating complex business analytics queries",
            "full": """TPC-H is a decision support benchmark that consists of a suite of business-oriented ad-hoc queries
            and concurrent data modifications. The queries and data are chosen to have broad industry-wide relevance.
            This benchmark illustrates decision support systems that examine large volumes of data, execute queries with
            a high degree of complexity, and give answers to critical business questions. The benchmark models a wholesale
            supplier with a distribution network across multiple regions.""",
            "characteristics": [
                "22 complex analytical queries",
                "8 tables with varying cardinality",
                "Queries involve multi-table joins, aggregations, and subqueries",
                "Simulates real-world business intelligence workloads",
            ],
        }

    def get_table_names(self) -> list[str]:
        """Get list of TPC-H table names."""
        return [
            "nation",
            "region",
            "part",
            "supplier",
            "partsupp",
            "customer",
            "orders",
            "lineitem",
        ]

    def get_table_columns(self, table_name: str) -> list[str]:
        """Get column names for a TPC-H table."""
        table_columns = {
            "nation": ["n_nationkey", "n_name", "n_regionkey", "n_comment"],
            "region": ["r_regionkey", "r_name", "r_comment"],
            "part": [
                "p_partkey",
                "p_name",
                "p_mfgr",
                "p_brand",
                "p_type",
                "p_size",
                "p_container",
                "p_retailprice",
                "p_comment",
            ],
            "supplier": [
                "s_suppkey",
                "s_name",
                "s_address",
                "s_nationkey",
                "s_phone",
                "s_acctbal",
                "s_comment",
            ],
            "partsupp": [
                "ps_partkey",
                "ps_suppkey",
                "ps_availqty",
                "ps_supplycost",
                "ps_comment",
            ],
            "customer": [
                "c_custkey",
                "c_name",
                "c_address",
                "c_nationkey",
                "c_phone",
                "c_acctbal",
                "c_mktsegment",
                "c_comment",
            ],
            "orders": [
                "o_orderkey",
                "o_custkey",
                "o_orderstatus",
                "o_totalprice",
                "o_orderdate",
                "o_orderpriority",
                "o_clerk",
                "o_shippriority",
                "o_comment",
            ],
            "lineitem": [
                "l_orderkey",
                "l_partkey",
                "l_suppkey",
                "l_linenumber",
                "l_quantity",
                "l_extendedprice",
                "l_discount",
                "l_tax",
                "l_returnflag",
                "l_linestatus",
                "l_shipdate",
                "l_commitdate",
                "l_receiptdate",
                "l_shipinstruct",
                "l_shipmode",
                "l_comment",
            ],
        }
        return table_columns.get(table_name, [])

    def get_table_info(self) -> dict[str, dict[str, Any]]:
        """Return TPC-H table metadata."""
        return {
            "nation": {
                "description": "Nations/countries (25 rows)",
                "columns": self.get_table_columns("nation"),
                "cardinality_sf1": 25,
                "relationships": ["Foreign key to region"],
            },
            "region": {
                "description": "Geographic regions (5 rows)",
                "columns": self.get_table_columns("region"),
                "cardinality_sf1": 5,
                "relationships": [],
            },
            "part": {
                "description": "Parts/products catalog",
                "columns": self.get_table_columns("part"),
                "cardinality_sf1": 200000,
                "relationships": [],
            },
            "supplier": {
                "description": "Suppliers/vendors",
                "columns": self.get_table_columns("supplier"),
                "cardinality_sf1": 10000,
                "relationships": ["Foreign key to nation"],
            },
            "partsupp": {
                "description": "Parts supplied by suppliers (association table)",
                "columns": self.get_table_columns("partsupp"),
                "cardinality_sf1": 800000,
                "relationships": ["Foreign keys to part and supplier"],
            },
            "customer": {
                "description": "Customers/buyers",
                "columns": self.get_table_columns("customer"),
                "cardinality_sf1": 150000,
                "relationships": ["Foreign key to nation"],
            },
            "orders": {
                "description": "Customer orders",
                "columns": self.get_table_columns("orders"),
                "cardinality_sf1": 1500000,
                "relationships": ["Foreign key to customer"],
            },
            "lineitem": {
                "description": "Order line items (largest table)",
                "columns": self.get_table_columns("lineitem"),
                "cardinality_sf1": 6001215,
                "relationships": ["Foreign keys to orders, part, supplier, partsupp"],
            },
        }

    def get_setup_script_info(self) -> dict[str, str]:
        """Return TPC-H setup step descriptions."""
        return {
            "schema_creation": "Create 8 TPC-H tables with system-optimized data types",
            "index_creation": "Create indexes on foreign keys and join columns",
            "table_analysis": "Update database statistics for query optimizer",
        }

    @exclude_from_package
    def get_rendered_setup_scripts(self, system: SystemUnderTest) -> dict[str, str]:
        """Render setup scripts for specific system."""
        scripts = {}

        for script_name in ["create_tables", "create_indexes", "analyze_tables"]:
            try:
                template = self.get_template_env().get_template(f"{script_name}.sql")
                system_extra = {}
                if hasattr(system, "setup_config"):
                    system_extra = system.setup_config.get("extra", {})

                # Get node_count and cluster for multinode support
                node_count = getattr(system, "node_count", 1)
                cluster = getattr(system, "cluster_name", "benchmark_cluster")

                rendered = template.render(
                    system_kind=system.kind,
                    scale_factor=self.scale_factor,
                    schema=self.get_schema_name(),
                    system_extra=system_extra,
                    node_count=node_count,
                    cluster=cluster,
                )
                scripts[script_name] = rendered
            except Exception as e:
                print(f"Warning: Failed to render {script_name}.sql: {e}")
                scripts[script_name] = f"-- Error rendering script: {e}"

        return scripts

    def get_all_query_names(self) -> list[str]:
        """Get list of all TPC-H query names."""
        return [f"Q{i:02d}" for i in range(1, 23)]  # Q01 through Q22

    def get_schema_name(self) -> str:
        """Get the schema name for TPC-H workload."""
        # ClickHouse uses 'database', Exasol uses 'schema'
        if self._current_system is None:
            return "benchmark"

        # Check schema first (Exasol), then database (ClickHouse)
        # Must check if attribute exists AND is not None
        if hasattr(self._current_system, "schema") and self._current_system.schema:
            return str(self._current_system.schema)
        elif (
            hasattr(self._current_system, "database") and self._current_system.database
        ):
            return str(self._current_system.database)
        else:
            return "benchmark"

    def estimate_filesystem_usage_gb(self, system: SystemUnderTest) -> int:
        """
        Estimate required storage size for TPC-H data at specific scale factor

        # SF1 ≈ 1GB, add 20% safety margin
        # estimated_gb = max(int(scale_factor * 1.3), 3)
        """
        if system.SUPPORTS_STREAMLOAD and self.generator == "dbgen-pipe":
            return 0

        def scale_multiplier(sf: float) -> float:
            # 2.0 at very small sf (≈1–10), ~1.6 at 30, →1.3 for sf ≥ 100
            # f(sf) = 1.3 + 0.7 / (1 + (sf/K)^p), with K≈26.8537, p≈2.5966
            if sf <= 10:
                return 2.0
            val = 1.3 + 0.7 / (1.0 + (sf / 26.853725639548) ** 2.5965770266157073)
            return float(max(1.3, min(val, 2.0)))

        def estimate_gb(sf: float) -> int:
            return int(max(sf * scale_multiplier(sf), 3.0))

        return estimate_gb(float(self.scale_factor))
