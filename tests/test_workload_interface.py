import pytest
from itertools import product

from benchkit.systems import SystemUnderTest, SYSTEM_IMPLEMENTATIONS, _lazy_import_system
from benchkit.workloads import Workload, create_workload, WORKLOAD_IMPLEMENTATIONS


@pytest.fixture(params=WORKLOAD_IMPLEMENTATIONS.keys())
def workload(request) -> Workload:
    return create_workload({"name": request.param})

def make_bare_system(kind: str) -> SystemUnderTest:
    return _lazy_import_system(kind)({
        "name": "testsystem",
        "version": "1.0",
        "kind": kind,
        "setup": {},
    })

@pytest.fixture(params=SYSTEM_IMPLEMENTATIONS.keys())
def system(request) -> SystemUnderTest:
    return make_bare_system(request.param)

@pytest.mark.parametrize(
    "workload_name, scale_factor",
    product(
        WORKLOAD_IMPLEMENTATIONS.keys(),
        [1,99]
    )
)
def test_basics(workload_name: str, scale_factor: int):
    """Not using the fixtures because we want to test name generation"""
    dut: Workload = create_workload({"name": workload_name, "scale_factor": scale_factor})
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
def test_size_estimations(workload_name: str, system_kind: str, default_gb: int, sf100_gb: int):
    workload: Workload = create_workload({"name": workload_name})
    system: System = make_bare_system(system_kind)

    assert workload.estimate_filesystem_usage_gb(system) == default_gb
    workload.scale_factor = 100
    assert workload.estimate_filesystem_usage_gb(system) == sf100_gb
