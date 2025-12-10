from pathlib import Path
from typing import Any

from benchkit.systems import SystemUnderTest
from benchkit.workloads import Workload


class Clickbench(Workload):

    CSV_SOURCE_URL: str = "https://datasets.clickhouse.com/hits_compatible/hits.csv.gz"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # override default from base
        self.data_format = config.get("data_format", "csv")

    def display_name(self) -> str:
        # no scale factor
        return "ClickBench"

    def generate_data(self, output_dir: Path) -> bool:
        """TODO: download (and decompress?) data from web server"""
        if self.generator == "download":
            # is easily implemented, all components are there in common.file_management and systems.base
            raise NotImplementedError("downloading data before load")
        return True

    def load_data(self, system: SystemUnderTest) -> bool:
        """Load data into the single benchmark table"""
        system.schema = self.get_schema_name()
        return system.load_data_from_url(
            self.get_schema_name(), "hits", self.CSV_SOURCE_URL
        )

    def get_all_query_names(self) -> list[str]:
        # uppercase Q, and query number with no leading zeroes
        return [f"Q{n}" for n in range(43)]

    def get_schema_name(self) -> str:
        return "clickbench"

    def estimate_filesystem_usage_gb(self, system: SystemUnderTest) -> int:
        if system.SUPPORTS_STREAMLOAD:
            return 0
        # if system.SUPPORTS_LOAD_FROM_COMPRESSED:
        return 90
