from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .tpch import TPCH


class Estuary(TPCH):
    """Inherits all but very few methods from the TPC-H benchmark"""

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
