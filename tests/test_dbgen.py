import pytest

from benchkit.common import DbGenPipe


@pytest.mark.parametrize(argnames=["scale_factor"], argvalues=[[1], [1000]])
def test_region_lines(scale_factor: int) -> None:
    """Region always has 5 rows, from 0 to 4"""
    region_key: int = 0
    with DbGenPipe("region", scale_factor) as p:
        row: str
        for row in p.readlines():
            assert row.startswith(f"{region_key},")
            region_key += 1
    assert region_key == 5


@pytest.mark.parametrize(argnames=["scale_factor"], argvalues=[[1], [1000]])
def test_nation_lines(scale_factor: int) -> None:
    """Region always has 25 rows, from 0 to 24"""
    nation_key: int = 0
    with DbGenPipe("nation", scale_factor) as p:
        row: str
        for row in p.readlines():
            assert row.startswith(f"{nation_key},")
            nation_key += 1
    assert nation_key == 25


@pytest.mark.parametrize(
    argnames=["scale_factor"],
    argvalues=[[1], [1000]],
)
def test_supplier_stream(scale_factor: int) -> None:
    buf_len: int = 1024
    short_reads: int = 0
    total_bytes: int = 0

    with DbGenPipe("supplier", scale_factor) as p:
        stream = p.file_stream()
        buffer: bytes
        last_buffer: str = ""
        while buffer := stream.read(buf_len):
            read_bytes: int = len(buffer)
            if read_bytes < buf_len:
                short_reads += 1
            total_bytes += read_bytes
            last_buffer = buffer.decode("ascii")
    assert last_buffer.endswith(
        '"\n'
    ), f"End of stream must be end of record: {last_buffer}"
    last_line: str = last_buffer.split("\n")[-2]
    assert last_line.startswith(f"{scale_factor*10000},Supplier#")
    assert short_reads <= 1


def test_raises_on_bad_table() -> None:
    with pytest.raises(ChildProcessError):
        with DbGenPipe("ation", 1) as p:
            for _ in p.readlines():
                pass


def test_raises_on_bad_scalefactor() -> None:
    with pytest.raises(ChildProcessError):
        with DbGenPipe("nation", -1) as p:
            for _ in p.readlines():
                pass


def test_raises_on_broken_pipe() -> None:
    with pytest.raises(ChildProcessError):
        with DbGenPipe("partsupp", 1000):
            # exit here
            pass


def test_raises_on_exception() -> None:
    with pytest.raises(ChildProcessError):
        try:
            with DbGenPipe("partsupp", 1000):
                # exit here
                raise ValueError("exit the loop")
        except ValueError:
            pass
