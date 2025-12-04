import pytest

from benchkit.systems import SystemUnderTest
from benchkit.systems.clickhouse import ClickHouseSystem
from benchkit.systems.exasol import ExasolSystem
from benchkit.workloads import TPCH


def test_basics():
    dut: Workload = TPCH({"name": "test"})
    assert dut
    assert dut.scale_factor == 1
    assert dut.display_name() == "test SF1"
    assert dut.safe_display_name() == "test_SF1"


def test_naming():
    dut: Workload = TPCH({"name": "test2", "scale_factor": 99})

    assert dut.scale_factor == 99
    assert dut.display_name() == "test2 SF99"
    assert dut.safe_display_name() == "test2_SF99"


def test_scaling():
    tpch: Workload = TPCH({"name": "test"})
    exasol: SystemUnderTest = ExasolSystem(
        {"name": "testsystem", "kind": "exasol", "version": "1.0", "setup": {}}
    )

    clickhouse: SystemUnderTest = ClickHouseSystem(
        {"name": "testsystem", "kind": "clickhouse", "version": "1.0", "setup": {}}
    )

    # for the time being, there are no differences
    assert tpch.estimate_filesystem_usage_gb(exasol) == 3
    assert tpch.estimate_filesystem_usage_gb(clickhouse) == 3

    tpch.scale_factor = 100
    assert tpch.estimate_filesystem_usage_gb(exasol) == 132
    assert tpch.estimate_filesystem_usage_gb(clickhouse) == 132
