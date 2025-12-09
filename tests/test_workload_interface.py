from datetime import timedelta
from itertools import product

import pytest

from benchkit.systems import (
    SYSTEM_IMPLEMENTATIONS,
    SystemUnderTest,
    _lazy_import_system,
)
from benchkit.workloads import TPCH, WORKLOAD_IMPLEMENTATIONS, Workload, create_workload


@pytest.fixture(params=WORKLOAD_IMPLEMENTATIONS.keys())
def workload(request) -> Workload:
    return create_workload({"name": request.param})


def make_bare_system(kind: str) -> SystemUnderTest:
    return _lazy_import_system(kind)(
        {
            "name": "testsystem",
            "version": "1.0",
            "kind": kind,
            "setup": {},
        }
    )


@pytest.fixture(params=SYSTEM_IMPLEMENTATIONS.keys())
def system(request) -> SystemUnderTest:
    return make_bare_system(request.param)


@pytest.mark.parametrize(
    "workload_name, scale_factor", product(WORKLOAD_IMPLEMENTATIONS.keys(), [1, 99])
)
def test_basics(workload_name: str, scale_factor: int):
    """Not using the fixtures because we want to test name generation"""
    dut: Workload = create_workload(
        {"name": workload_name, "scale_factor": scale_factor}
    )
    assert dut
    assert dut.scale_factor == scale_factor
    assert dut.display_name() == f"{workload_name} SF{scale_factor}"
    assert dut.safe_display_name() == f"{workload_name}_SF{scale_factor}"


@pytest.mark.parametrize(
    "workload_name, system_kind, default_gb, sf100_gb",
    [
        ("tpch", "exasol", 3, 132),
        ("tpch", "clickhouse", 3, 132),
        ("estuary", "exasol", 0, 0),
        ("estuary", "clickhouse", 3, 132),
    ],
)
def test_size_estimations(
    workload_name: str, system_kind: str, default_gb: int, sf100_gb: int
):
    workload: Workload = create_workload({"name": workload_name})
    system: SystemUnderTest = make_bare_system(system_kind)

    assert workload.estimate_filesystem_usage_gb(system) == default_gb
    workload.scale_factor = 100
    assert workload.estimate_filesystem_usage_gb(system) == sf100_gb


@pytest.mark.parametrize(
    "system_kind, node_count, scale_factor, orders_timeout_seconds",
    [
        # exasol always has default timeout
        ("exasol", 1, 100, 300),
        ("exasol", 10, 100, 300),
        ("exasol", 1, 1000, 300),
        ("exasol", 3, 1000, 300),
        # clickhouse differs
        ("clickhouse", 1, 100, 1500),
        ("clickhouse", 10, 100, 300),  # hits lower bound
        ("clickhouse", 1, 1000, 7200),  # hits upper bound
        ("clickhouse", 3, 1000, 5000),
    ],
)
def test_timeout_calculation(
    system_kind: str, node_count: int, scale_factor: int, orders_timeout_seconds: int
):
    """Currently only implemented in TCPH workload -- will move to base class soon"""
    system: SystemUnderTest = make_bare_system(system_kind)
    workload: TPCH = TPCH({"name": "tpch", "scale_factor": scale_factor})
    system.node_count = node_count

    assert workload.calculate_statement_timeout(
        "OPTIMIZE TABLE ORDERS", system
    ) == timedelta(seconds=orders_timeout_seconds)

    assert workload.calculate_statement_timeout(
        "SELECT * FROM ORDERS", system
    ) == timedelta(minutes=5), "should be default timeout"

    assert (
        timedelta(minutes=5)
        <= workload.calculate_statement_timeout("MATERIALIZE STATISTICS", system)
        <= timedelta(hours=1)
    ), "timeout should be within bounds"
