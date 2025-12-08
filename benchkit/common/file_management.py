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
