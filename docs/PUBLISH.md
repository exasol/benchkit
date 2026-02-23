# Publishing Benchmark Results

Benchmark results are displayed on the performance leaderboard hosted at `public/performance/`.
To add your results, you submit a config YAML and the result files via a pull request.
A maintainer (or CI) regenerates the leaderboard after merging — you do not need to run `benchkit suite publish`.

## Prerequisites

- A completed benchmark run with results in `results/<project_id>/`
- The run must have finished successfully (`runs.csv` and `summary.json` exist)

## Step 1: Create a config YAML

Create a file in `public/performance/<workload>/` where `<workload>` is `tpch` or `clickbench`.

### Naming conventions

| Workload | Pattern | Example |
|----------|---------|---------|
| TPC-H | `{system}_{nodes}_{instance}_{sf}{scale}_{streams}s.yaml` | `clickhouse_sn_c7i2xl_sf50_1s.yaml` |
| ClickBench | `{system}_{instance}.yaml` | `exasol_r5d4xl.yaml` |

Node shorthand: `sn` = single-node, `2n` / `4n` = multi-node.
Instance shorthand: drop the dot and size suffix (e.g., `c7i.2xlarge` → `c7i2xl`).

### Required fields

```yaml
project_id: perf_tpch_clickhouse_sn_c7i2xl_sf50
title: 'Combined benchmark: perf_tpch_clickhouse_sn_c7i2xl_sf50'
author: Combined
systems:
- name: clickhouse
  kind: clickhouse
  version: 25.10.2.65
  setup:
    method: preinstalled
workload:
  name: tpch
  scale_factor: 50
  runs_per_query: 5
  warmup_runs: 1
env:
  mode: local
  instance_type: c7i.2xlarge
report:
  output_path: results/perf_tpch_clickhouse_sn_c7i2xl_sf50/reports
  figures_dir: results/perf_tpch_clickhouse_sn_c7i2xl_sf50/figures
```

The `project_id` must match the directory name under `public/performance/results/`.

## Step 2: Copy result files

Copy the required files from your local `results/<project_id>/` into `public/performance/results/<project_id>/`:

```
public/performance/results/<project_id>/
├── runs.csv              # (required) Raw query timings
├── summary.json          # (required) Aggregated statistics
├── config.yaml           # (required) Exact config used for the run
├── system_<name>.json    # (recommended) Hardware and OS details
├── setup_<name>.json     # (recommended) Database installation steps
└── runs_warmup.csv       # (optional) Warmup run timings
```

Example:

```bash
mkdir -p public/performance/results/perf_tpch_clickhouse_sn_c7i2xl_sf50
cp results/perf_tpch_clickhouse_sn_c7i2xl_sf50/{runs.csv,summary.json,config.yaml} \
   public/performance/results/perf_tpch_clickhouse_sn_c7i2xl_sf50/
cp results/perf_tpch_clickhouse_sn_c7i2xl_sf50/system_clickhouse.json \
   public/performance/results/perf_tpch_clickhouse_sn_c7i2xl_sf50/
cp results/perf_tpch_clickhouse_sn_c7i2xl_sf50/setup_clickhouse.json \
   public/performance/results/perf_tpch_clickhouse_sn_c7i2xl_sf50/
```

## Step 3: Open a pull request

```bash
git checkout -b results/perf_tpch_clickhouse_sn_c7i2xl_sf50
git add public/performance/tpch/clickhouse_sn_c7i2xl_sf50_1s.yaml
git add public/performance/results/perf_tpch_clickhouse_sn_c7i2xl_sf50/
git commit -m "Add TPC-H SF50 results for ClickHouse on c7i.2xlarge"
git push -u origin results/perf_tpch_clickhouse_sn_c7i2xl_sf50
gh pr create --title "Add TPC-H SF50 results for ClickHouse on c7i.2xlarge"
```

## Reference: Result file formats

### `runs.csv`

Each row is one query execution. Columns:

| Column | Description |
|--------|-------------|
| `success` | `True` / `False` |
| `elapsed_s` | Wall-clock seconds |
| `rows_returned` | Number of result rows |
| `query` | Query name (e.g., `Q01`) |
| `error` | Error message if failed |
| `run` | Run number (1-based) |
| `system` | System name |
| `workload` | Workload name (`tpch`, `clickbench`) |
| `scale_factor` | TPC-H scale factor |
| `variant` | Query variant |
| `stream_id` | Stream identifier |
| `elapsed_ms` | Wall-clock milliseconds |

### `summary.json`

Aggregated statistics including:

- `total_queries` — number of query executions
- `systems` — list of system names
- `run_date` — timestamp of the run
- `per_system` — avg/median/min/max runtime per system
- `per_query` — avg/median/min/max runtime per query per system
- `warmup_statistics` — warmup run stats (if warmup was enabled)

### `config.yaml`

The exact configuration used for the benchmark run. Must contain `project_id`, `systems`, `workload`, and `env` sections.

### `system_<name>.json`

Hardware and OS details collected from the benchmark host: CPU model, core count, memory, kernel version, disk info.

### `setup_<name>.json`

Database installation and configuration steps: commands executed, versions installed, storage setup.
