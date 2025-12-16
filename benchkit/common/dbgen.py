from __future__ import annotations

from collections.abc import Iterable
from subprocess import PIPE, Popen
from typing import IO, Any

from .markers import exclude_from_package


class DbGenPipe:
    """
    Class to encapsulate TPC-H data generation

    Usage:
    <code>
        with DbGenPipe('nation', 100) as p:
          # either:
          for csv_line in p.readlines():
          # or:
          file_stream = p.file_stream()
          [...]
    """

    def __init__(self, table_name: str, scale_factor: int):
        self.table_name: str = table_name
        self.scale_factor: int = scale_factor
        self.proc: Popen | None = None

    def __enter__(self) -> DbGenPipe:
        """Start the subprocess and data generation"""
        self.proc = Popen(
            [
                "tpchgen-cli",
                "--scale-factor",
                str(self.scale_factor),
                "--tables",
                self.table_name,
                "--format",
                "csv",
                "--stdout",
            ],
            stdin=None,
            stdout=PIPE,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exiting the with block, make sure the subprocess is exiting"""
        if not self.proc:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
        # give the process 5 seconds to terminate
        return_code: int = self.proc.wait(timeout=5)
        if return_code != 0:
            raise ChildProcessError("tpchgen-cli exited with error")

    def file_stream(self) -> IO[Any]:
        """Return the generators file stream (stdout) after reading the first line (column names)"""
        assert self.proc
        assert self.proc.stdout
        # we just read the header so it is out of the way
        header: str = self.proc.stdout.readline()
        assert header
        return self.proc.stdout

    @exclude_from_package
    def readlines(self) -> Iterable[str]:
        """Returns the generated data one line at a time, excluding the column names header"""
        assert self.proc
        assert self.proc.stdout
        # we just read the header so it is out of the way
        header: str = self.proc.stdout.readline()
        assert header
        # then we iterate over lines and return them
        # TPC-H is ASCII only and strings do not contain line breaks.
        while line := self.proc.stdout.readline():
            b: bytes = line
            yield b.decode(encoding="ASCII")
