from time import time


def test_supplier():
    from benchkit.workloads.dbgen_estuary import TableGenerator

    start_time_seconds: float = time()
    generator = TableGenerator(table_name='supplier')

    generator_construction_timer = time()
    assert generator_construction_timer - start_time_seconds <= 1.0, "constructor must be done in 1 sec"

    # override default settings
    generator.total_rows = 100
    generated_rows: int = 0
    last_row_time = time()

    max_length: list[int] = [0] * 10

    for row in generator.rows():
        next_row_time = time()
        assert next_row_time - last_row_time <= 1.0, "Batches must not delay more than a second"
        last_row_time = next_row_time
        assert isinstance(row[0], int), "Column zero must be integer"
        generated_rows += 1

        for col, value in enumerate(row):
            if isinstance(value, str):
                max_length[col] = max(max_length[col], len(value))

    assert generated_rows == 100, "Must produce the expected number of rows"
    assert last_row_time - generator_construction_timer <= 10.0, "100 rows must be done in less than 10 seconds"
    assert max_length[0] <= 8, "suppkey"
    assert max_length[1] <= 35, "name"
    assert max_length[2] <= 40, "address"
    assert max_length[3] <= 2, "nationkey"
    assert max_length[4] <= 35, "phone"
    assert max_length[5] <= 15, "acctbal"
    assert max_length[6] <= 256, "comment"
    assert max_length[7] == 0, "enough columns"


def test_estuary_workload():
    from benchkit.workloads import Estuary

    dut = Estuary({
        "name": "test"
    })
    deps = dut.get_python_dependencies()
    assert deps
    assert any("Faker" in d for d in deps), "Faker package must be in dependency list"
