from pathlib import Path

# noinspection PyUnusedImports
import pytest
from requests.exceptions import ConnectionError, HTTPError, MissingSchema

from benchkit.common import download_file_to_storage


def get_temp_file_name() -> Path:
    import tempfile

    with tempfile.NamedTemporaryFile() as f:
        return Path(f.name)


def test_bad_url():
    with pytest.raises(MissingSchema):
        download_file_to_storage("hello world", Path("data.csv"))


def test_no_server():
    with pytest.raises(ConnectionError):
        download_file_to_storage(
            "https://localhost:123/data.csv.gz", Path("data.csv.gz")
        )


def test_no_file():
    with pytest.raises(HTTPError) as e:
        download_file_to_storage(
            "https://exasol.com/data_no_such_file.tgz", Path("none")
        )
    assert "404" in str(e.value)


def test_no_access():
    with pytest.raises(HTTPError) as e:
        download_file_to_storage(
            "https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/no_such_version/c4",
            Path("xxx"),
        )
    assert "403" in str(e.value)


def test_good_file():
    from hashlib import file_digest

    target: Path = get_temp_file_name()
    assert not target.exists()
    try:
        download_file_to_storage(
            "https://github.githubassets.com/favicons/favicon.png", target
        )
        assert target.exists()
        assert target.stat().st_size == 958
        with open(target, "rb") as file:
            x = file_digest(file, "sha256")
            assert (
                x.hexdigest()
                == "74cf90ac2fe6624ab1056cacea11cf7ed4f8bef54bbb0e869638013bba45bc08"
            )

    finally:
        target.unlink(missing_ok=True)
