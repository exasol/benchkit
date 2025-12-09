from pathlib import Path
from typing import Any

from benchkit.systems import SystemUnderTest
from benchkit.workloads import Workload


class Estuary(Workload):
    """Inherits all but very few methods from the TPC-H benchmark"""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return Python packages required for Estuary workload."""
        return ["Faker>=38.0.0"]  # For data generation

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # arbitrary restriction introduced by the row calculation in load_data
        assert (
            1 <= self.scale_factor <= 1000
        ), "estuary benchmark only supports scale factors 1 to 1000"

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
        from .dbgen_faker import TableGenerator

        schema_name = self.get_schema_name()

        for table_name in self.get_table_names():
            print(f"Loading {table_name}...")

            generator = TableGenerator(table_name)
            # generator configuration is set up for SF 1000
            generator.total_rows /= 1000 / self.scale_factor

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

    def estimate_filesystem_usage_gb(self, system: SystemUnderTest) -> int:
        """
        Estuary workload uses streaming import where possible,
        in which case it does not require local storage.
        Otherwise, same code as TPC-H (although not 100% correct, as Estuary loads table-by-table)
        """
        if system.SUPPORTS_STREAMLOAD:
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
