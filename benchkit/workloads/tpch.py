"""TPC-H benchmark workload implementation."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ..systems.base import SystemUnderTest
from ..util import safe_command
from .base import Workload


class TPCH(Workload):
    """TPC-H benchmark workload implementation."""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required for TPC-H workload."""
        return ["tpchgen-cli>=0.2.0"]  # For TPC-H data generation

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.data_format = config.get("data_format", "tbl")  # TPC-H standard format

        # Determine which queries to include based on include/exclude logic
        queries_config = config.get("queries", {})
        queries_include = queries_config.get("include", [])
        queries_exclude = queries_config.get("exclude", [])

        all_queries = list(self.get_all_query_names())

        if queries_include:
            # If include is specified, use only those queries
            self.queries_to_include = queries_include
        elif queries_exclude:
            # If exclude is specified, use all queries except excluded ones
            self.queries_to_include = [
                q for q in all_queries if q not in queries_exclude
            ]
        else:
            # If neither is specified, use all queries
            self.queries_to_include = all_queries

        # Setup template environment for TPC-H workload
        self.workload_dir = Path(__file__).parent.parent.parent / "workloads" / "tpch"
        self.template_env = Environment(
            loader=FileSystemLoader(
                [self.workload_dir / "queries", self.workload_dir / "setup"]
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Store system for template resolution
        self._current_system: SystemUnderTest | None = None

    def generate_data(self, output_dir: Path) -> bool:
        """Generate TPC-H data using tpchgen-cli (modern Python approach)."""
        return self._generate_with_tpchgen_cli(output_dir)

    def _generate_with_tpchgen_cli(self, output_dir: Path) -> bool:
        """Generate TPC-H data using tpchgen-cli (modern Python package)."""
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

    def create_schema(self, system: SystemUnderTest) -> bool:
        """Create TPC-H schema and tables using templated setup scripts."""
        # Use TPC-H specific schema name (e.g., tpch_sf100)
        schema = self.get_schema_name()

        # First, create the schema using the system's method
        if hasattr(system, "create_schema"):
            print(f"Creating schema '{schema}'...")
            if not system.create_schema(schema):
                print(f"Failed to create schema '{schema}'")
                return False
            print(f"✓ Schema '{schema}' created successfully")

        # Then create the tables using the templated script
        print("Creating TPC-H tables...")
        return self._execute_setup_script(system, "create_tables.sql")

    def create_indexes(self, system: SystemUnderTest) -> bool:
        """Create TPC-H indexes using templated setup scripts."""
        return self._execute_setup_script(system, "create_indexes.sql")

    def analyze_tables(self, system: SystemUnderTest) -> bool:
        """Analyze TPC-H tables using templated setup scripts."""
        return self._execute_setup_script(system, "analyze_tables.sql")

    def _execute_setup_script(self, system: SystemUnderTest, script_name: str) -> bool:
        """Execute a templated setup script by splitting into individual statements."""
        try:
            # Load and render the template
            template = self.template_env.get_template(script_name)
            rendered_sql = template.render(
                system_kind=system.kind,
                scale_factor=self.scale_factor,
                schema=self.get_schema_name(),
            )

            # Split SQL into individual statements and execute them one by one
            statements = self._split_sql_statements(rendered_sql)

            for idx, statement in enumerate(statements):
                # Skip empty statements
                if not statement.strip():
                    continue

                # Execute each statement individually
                result = system.execute_query(
                    statement,
                    query_name=f"setup_{script_name.replace('.sql', '')}_{idx+1}",
                )

                if not result["success"]:
                    print(
                        f"Failed to execute statement {idx+1} in {script_name}: {result.get('error', 'Unknown error')}"
                    )
                    print(f"Statement was: {statement[:200]}...")
                    return False

            return True

        except Exception as e:
            print(f"Error executing setup script {script_name}: {e}")
            return False

    def _split_sql_statements(self, sql: str) -> list[str]:
        """
        Split SQL script into individual statements.

        Handles:
        - Semicolon-separated statements
        - SQL comments (-- and /* */)
        - Empty lines

        Returns:
            List of individual SQL statements
        """
        statements = []
        current_statement = []
        in_comment = False

        for line in sql.split("\n"):
            stripped = line.strip()

            # Skip SQL comments
            if stripped.startswith("--"):
                continue

            # Handle multi-line comments
            if "/*" in stripped:
                in_comment = True
            if "*/" in stripped:
                in_comment = False
                continue
            if in_comment:
                continue

            # Skip empty lines
            if not stripped:
                continue

            # Check if line ends with semicolon (statement terminator)
            if stripped.endswith(";"):
                # Add the line without semicolon to current statement
                current_statement.append(stripped[:-1])
                # Join and add to statements list
                statements.append("\n".join(current_statement))
                # Reset for next statement
                current_statement = []
            else:
                # Add line to current statement
                current_statement.append(stripped)

        # Add any remaining statement (for scripts without trailing semicolon)
        if current_statement:
            statements.append("\n".join(current_statement))

        return statements

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

        return True

    def get_queries(self, system: SystemUnderTest | None = None) -> dict[str, str]:
        """Get TPC-H queries with templates resolved for the target system."""
        # Use provided system or stored system
        target_system = system or self._current_system
        if target_system is None:
            raise ValueError(
                "System must be provided either as parameter or stored from previous call"
            )

        # Store system for future template resolution
        self._current_system = target_system

        queries = {}
        for query_name in self.get_all_query_names():
            if query_name in self.queries_to_include:
                queries[query_name] = self._get_query_sql(query_name, target_system)

        return queries

    def run_workload(
        self,
        system: "SystemUnderTest",
        query_names: list[str],
        runs_per_query: int = 3,
        warmup_runs: int = 1,
    ) -> list[dict[str, Any]]:
        """Execute the TPC-H workload with system context for template resolution."""
        # Store system context for template resolution
        self._current_system = system

        # Call parent implementation
        return super().run_workload(system, query_names, runs_per_query, warmup_runs)

    def run_query(
        self, system: SystemUnderTest, query_name: str, query_sql: str
    ) -> dict[str, Any]:
        """Execute a TPC-H query."""
        # Substitute schema name in query
        schema_name = self.get_schema_name()
        formatted_sql = query_sql.format(schema=schema_name)

        return system.execute_query(formatted_sql, query_name=query_name)

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

    def get_rendered_setup_scripts(self, system: SystemUnderTest) -> dict[str, str]:
        """Render setup scripts for specific system."""
        scripts = {}

        for script_name in ["create_tables", "create_indexes", "analyze_tables"]:
            try:
                template = self.template_env.get_template(f"{script_name}.sql")
                rendered = template.render(
                    system_kind=system.kind,
                    scale_factor=self.scale_factor,
                    schema=self.get_schema_name(),
                )
                scripts[script_name] = rendered
            except Exception as e:
                print(f"Warning: Failed to render {script_name}.sql: {e}")
                scripts[script_name] = f"-- Error rendering script: {e}"

        return scripts

    def get_all_query_names(self) -> list[str]:
        """Get list of all TPC-H query names."""
        return [f"Q{i:02d}" for i in range(1, 23)]  # Q01 through Q22

    # Note: Table DDLs are now handled by templated setup scripts

    def _get_query_sql(self, query_name: str, system: SystemUnderTest) -> str:
        """Get SQL text for a specific TPC-H query with templates resolved."""
        try:
            # Load and render the query template
            template = self.template_env.get_template(f"{query_name}.sql")
            rendered_sql = template.render(
                system_kind=system.kind,
                scale_factor=self.scale_factor,
                schema=self.get_schema_name(),
            )
            return rendered_sql

        except Exception as e:
            print(f"Error loading query {query_name}: {e}")
            return f"-- Error loading query {query_name}: {e}"

    def get_schema_name(self) -> str:
        """Get the schema name for TPC-H workload."""
        # ClickHouse uses 'database', Exasol uses 'schema'
        if self._current_system is None:
            return "benchmark"

        if hasattr(self._current_system, "schema"):
            return str(self._current_system.schema)
        elif hasattr(self._current_system, "database"):
            return str(self._current_system.database)
        else:
            return "benchmark"
