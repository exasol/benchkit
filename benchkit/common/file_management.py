from __future__ import annotations

from enum import Enum
from pathlib import Path


def download_file_to_storage(url: str, target: Path) -> None:
    """Download data from a given URL to given target path"""
    import requests

    with (
        requests.get(url, allow_redirects=True, stream=True) as handle,
        open(target, "wb") as file,
    ):
        handle.raise_for_status()
        file.write(handle.content)


class DataFormat(Enum):
    CSV = 1
    TBL = 2
    TSV = 3
    DATA_LIST = 4

    @staticmethod
    def fromString(name: str) -> DataFormat:
        upper_name = name.upper()
        fmt: DataFormat
        for fmt in list(DataFormat):
            # note: soule be easier with StrEnum, but that requires python 3.11
            if upper_name == str(fmt).split(".")[-1]:
                return fmt
        raise KeyError(f"DataFormat '{name}'")
