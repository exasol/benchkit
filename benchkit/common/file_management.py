from __future__ import annotations

import os
import tarfile
import tempfile
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


def download_file_to_storage(url: str, target: Path) -> None:
    """Download data from a given URL to given target path"""
    import requests

    with (
        requests.get(url, allow_redirects=True, stream=True) as handle,
        open(target, "wb") as file,
    ):
        handle.raise_for_status()
        file.write(handle.content)


def download_github_release(
    repo: str,
    version: str,
    asset_pattern: str,
    target_dir: Path,
    gh_token: str | None = None,
    binary_name: str = "exasol",
) -> Path:
    """
    Download asset from GitHub release.

    Tries public access first, falls back to GH_TOKEN if provided.
    Extracts tarball and returns path to the binary.

    Args:
        repo: GitHub repository (e.g., "exasol/personal-edition")
        version: Release version (e.g., "0.5.1")
        asset_pattern: Asset filename (e.g., "exasol-personal-edition_Linux_x86_64.tar.gz")
        target_dir: Directory to extract binary to
        gh_token: GitHub token for private repo access (optional)
        binary_name: Name of binary file to extract (default: "exasol")

    Returns:
        Path to the extracted binary

    Raises:
        RuntimeError: If download fails
    """
    import requests

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Try public URL first
    public_url = (
        f"https://github.com/{repo}/releases/download/v{version}/{asset_pattern}"
    )

    downloaded_file = None

    # Try public access first (no auth)
    try:
        response = requests.get(public_url, allow_redirects=True, stream=True)
        if response.status_code == 200:
            downloaded_file = _download_to_temp(response)
    except requests.RequestException:
        pass

    # If public failed and token provided, try authenticated API
    if downloaded_file is None and gh_token:
        downloaded_file = _download_via_github_api(
            repo, version, asset_pattern, gh_token
        )

    if downloaded_file is None:
        raise RuntimeError(
            f"Failed to download {asset_pattern} from {repo} v{version}. "
            "Check if the release exists and GH_TOKEN is set for private repos."
        )

    # Extract tarball
    binary_path = _extract_tarball(downloaded_file, target_dir, binary_name)

    # Clean up temp file
    os.unlink(downloaded_file)

    return binary_path


def _download_to_temp(response: requests.Response) -> str:
    """Download response content to a temporary file."""
    fd, temp_path = tempfile.mkstemp(suffix=".tar.gz")
    try:
        with os.fdopen(fd, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return temp_path
    except Exception:
        os.close(fd)
        os.unlink(temp_path)
        raise


def _download_via_github_api(
    repo: str, version: str, asset_pattern: str, gh_token: str
) -> str | None:
    """Download asset using GitHub API (for private repos)."""
    import requests

    api_url = f"https://api.github.com/repos/{repo}/releases/tags/v{version}"
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # Get release info
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            return None

        release_data = response.json()
        assets = release_data.get("assets", [])

        # Find matching asset
        asset_url = None
        for asset in assets:
            if asset.get("name") == asset_pattern:
                asset_url = asset.get("url")
                break

        if not asset_url:
            return None

        # Download asset with octet-stream accept header
        download_headers = {
            "Authorization": f"token {gh_token}",
            "Accept": "application/octet-stream",
        }
        response = requests.get(
            asset_url, headers=download_headers, allow_redirects=True, stream=True
        )
        if response.status_code != 200:
            return None

        return _download_to_temp(response)

    except requests.RequestException:
        return None


def _extract_tarball(tarball_path: str, target_dir: Path, binary_name: str) -> Path:
    """Extract binary from tarball."""
    binary_path = target_dir / binary_name

    with tarfile.open(tarball_path, "r:gz") as tar:
        # Find the binary in the archive
        for member in tar.getmembers():
            if member.name.endswith(binary_name) or member.name == binary_name:
                # Extract to target directory
                member.name = binary_name  # Rename to just binary name
                tar.extract(member, target_dir)
                binary_path.chmod(0o755)  # Make executable
                return binary_path

        # If exact name not found, try extracting all and finding it
        tar.extractall(target_dir)

    # Look for the binary in extracted contents
    for item in target_dir.iterdir():
        if item.name == binary_name:
            item.chmod(0o755)
            return item
        if item.is_dir():
            candidate = item / binary_name
            if candidate.exists():
                # Move to target_dir
                final_path = target_dir / binary_name
                candidate.rename(final_path)
                final_path.chmod(0o755)
                return final_path

    raise RuntimeError(f"Binary '{binary_name}' not found in tarball")


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
