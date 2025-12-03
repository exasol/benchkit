from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .tpch import TPCH
from ..systems import SystemUnderTest


## TODO -- refactoring #14
class Estuary(TPCH):
    """Inherits all but very few methods from the TPC-H benchmark"""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required for Estuary workload."""
        return ["Faker>=38.0.0"]  # For data generation

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Override workload folders
        self.workload_dir = Path(__file__).parent.parent.parent / "workloads" / "estuary"
        self.template_env = Environment(
            loader=FileSystemLoader(
                [self.workload_dir / "queries", self.workload_dir / "setup"]
            ),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        assert 1 <= self.scale_factor <= 1000, "estuary benchmark only supports scale factors 1 to 1000"

    def get_workload_description(self) -> dict[str, Any]:
        """Return Estuary workload description."""
        return {
            "short": "Based on TPC-H, the Estuary Warehouse Benchmark uses a different query set.",
            "full": "...",
            "characteristics": [
                "12 complex analytical queries",
                "8 tables with varying cardinality",
                "Queries involve multi-table joins, aggregations, and subqueries",
                "Simulates real-world business intelligence workloads",
            ],
        }

    def get_all_query_names(self) -> list[str]:
        """Get list of all query names."""
        return [f"q{i:02d}" for i in range(1, 12)] + ["Frankenquery"]

    def generate_data(self, output_dir: Path) -> bool:
        """Data is generated on-the fly at load time"""
        return True

    def get_schema_name(self) -> str:
        return "estuary"

    def prepare(self, system: SystemUnderTest) -> bool:
        print("Setting up estuary workload...")

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

        # Estuary by definition does not create indices or statistics before the cold run

        print("Estuary workload setup completed successfully")
        return True

    def load_data(self, system: SystemUnderTest) -> bool:
        """Load Estuary data into the database system, directly streaming from generator to database"""
        from .dbgen_estuary import TableGenerator

        schema_name = self.get_schema_name()

        for table_name in self.get_table_names():
            print(f"Loading {table_name}...")

            generator = TableGenerator(table_name)
            # generator configuration is set up for SF 1000
            generator.total_rows /= (1000 / self.scale_factor)

            success = system.load_data_from_iterable(
                table_name,
                generator.rows(),
                schema=schema_name,
            )

            if not success:
                print(f"Failed to load {table_name}")
                return False

        return True

    def get_table_names(self) -> list[str]:
        """Get list of estuary table names."""
        return [
            "part",
            "supplier",
            "partsupp",
            "customer",
            "orders",
            "lineitem",
        ]
