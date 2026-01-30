# Extended Scalability Experiment Design

## Overview

This directory contains a comprehensive scalability benchmark comparing **5 database systems** across **3 dimensions**, while respecting system limitations and ensuring fair comparisons.

### Systems

| System | Multinode | Max Practical Streams | Notes |
|--------|-----------|----------------------|-------|
| Exasol | Yes (1-16 nodes) | 16+ | Full cluster support via c4 |
| ClickHouse | Yes (1-16 nodes) | 4 (8+ needs larger instances) | Sharding without replication |
| Trino | Yes (1-16 nodes) | 16+ | Requires S3 for multinode |
| StarRocks | Yes (1-16 nodes) | 16+ | FE/BE architecture |
| DuckDB | No (single-node only) | 16+ | Embedded database |

### Dimensions

- **Nodes**: 1, 4, 8, 16
- **Scale Factor**: 25, 50, 100 (GB)
- **Streams**: 1, 4, 8, 16

---

## Design Decision: Independent Dimension Testing

**Recommendation**: Test dimensions **independently** rather than full factorial (4x3x4=48 combinations).

**Rationale**:
- Full factorial would require 48 configs x 5 systems = 240 experiments
- Independent testing reduces to ~17 configs, ~75 experiments
- Scientific principle: Isolate one variable while holding others constant
- Combined effects can be inferred; validate with selected stress tests

**Baseline Parameters** (held constant when not the test variable):
- Scale Factor: **50** (mid-range, reasonable runtime)
- Streams: **4** (moderate, all systems handle well)
- Nodes: **1** (for non-node-scaling tests) or **4** (for cluster tests)

---

## Experiment Series Structure

```
configs/extended_scalability/
├── README.md                    # This design document
├── run_all.sh                   # Master orchestration script
│
├── series_1_nodes/              # Node scaling (4 systems)
│   ├── nodes_1.yaml
│   ├── nodes_4.yaml
│   ├── nodes_8.yaml
│   └── nodes_16.yaml
│
├── series_2_sf/                 # Scale factor scaling (5 systems, 1 node)
│   ├── sf_25.yaml
│   ├── sf_50.yaml
│   └── sf_100.yaml
│
├── series_3_streams_cluster/    # Stream scaling on 4-node clusters
│   ├── streams_1.yaml
│   ├── streams_4.yaml
│   ├── streams_8.yaml
│   └── streams_16.yaml
│
├── series_4_streams_single/     # Stream scaling single-node (5 systems)
│   ├── streams_1.yaml
│   ├── streams_4.yaml
│   ├── streams_8.yaml
│   └── streams_16.yaml
│
└── series_5_stress/             # Combined stress tests (validation)
    ├── max_nodes_sf.yaml
    └── max_nodes_streams.yaml
```

---

## Series 1: Node Scaling

**Purpose**: Measure horizontal scalability
**Systems**: Exasol, ClickHouse, Trino, StarRocks (DuckDB excluded)
**Fixed**: SF=50, Streams=4
**Variable**: Nodes = 1, 4, 8, 16

| Config | Nodes | Instance Type | RAM/Node | Total RAM | Notes |
|--------|-------|---------------|----------|-----------|-------|
| `nodes_1.yaml` | 1 | r6id.2xlarge | 64GB | 64GB | Single-node baseline |
| `nodes_4.yaml` | 4 | r6id.xlarge | 32GB | 128GB | 4-node cluster |
| `nodes_8.yaml` | 8 | r6id.xlarge | 32GB | 256GB | 8-node cluster |
| `nodes_16.yaml` | 16 | r6id.xlarge | 32GB | 512GB | 16-node cluster |

**Instance Sizing Rationale**:
- For node scaling, use smaller per-node instances (32GB) to show true horizontal scalability benefit
- Single-node uses larger instance (64GB) as baseline for comparison
- Total cluster RAM grows with node count, demonstrating scalability

**Experiments**: 4 configs x 4 systems = **16 experiments**

---

## Series 2: Scale Factor Scaling (Single-Node)

**Purpose**: Measure data scalability on single node
**Systems**: All 5 (Exasol, ClickHouse, Trino, StarRocks, DuckDB)
**Fixed**: Nodes=1, Streams=4
**Variable**: SF = 25, 50, 100

| Config | SF | Instance Type | RAM | Data Size | Notes |
|--------|-----|---------------|-----|-----------|-------|
| `sf_25.yaml` | 25 | r6id.xlarge | 32GB | ~25GB | Fits in memory |
| `sf_50.yaml` | 50 | r6id.2xlarge | 64GB | ~50GB | Fits in memory |
| `sf_100.yaml` | 100 | r6id.4xlarge | 128GB | ~100GB | Fits in memory |

**Instance Sizing Rationale**:
- Instance size scales proportionally with data size
- Ensures data fits in memory for fair comparison
- All systems get same resources within each SF config

**Fair Comparison**: All 5 systems on identical hardware within each config.

**Experiments**: 3 configs x 5 systems = **15 experiments**

---

## Series 3: Stream Scaling (4-Node Clusters)

**Purpose**: Measure concurrent query throughput on clusters
**Systems**: Exasol, ClickHouse, Trino, StarRocks (DuckDB excluded)
**Fixed**: Nodes=4, SF=50
**Variable**: Streams = 1, 4, 8, 16

| Config | Streams | Instance Type | RAM/Node | Total RAM | Mem/Stream |
|--------|---------|---------------|----------|-----------|------------|
| `streams_1.yaml` | 1 | r6id.xlarge | 32GB | 128GB | ~100GB |
| `streams_4.yaml` | 4 | r6id.xlarge | 32GB | 128GB | ~25GB |
| `streams_8.yaml` | 8 | r6id.2xlarge | 64GB | 256GB | ~25GB |
| `streams_16.yaml` | 16 | r6id.4xlarge | 128GB | 512GB | ~25GB |

**Instance Sizing Rationale**:
- Memory per stream kept roughly constant (~25GB) as streams increase
- ClickHouse especially benefits from consistent per-stream memory
- Smaller instances for low concurrency to avoid over-provisioning

**Experiments**: 4 configs x 4 systems = **16 experiments**

---

## Series 4: Stream Scaling (Single-Node)

**Purpose**: Measure single-node concurrent throughput (fair DuckDB comparison)
**Systems**: All 5
**Fixed**: Nodes=1, SF=50
**Variable**: Streams = 1, 4, 8, 16

| Config | Streams | Instance Type | RAM | Mem/Stream |
|--------|---------|---------------|-----|------------|
| `streams_1.yaml` | 1 | r6id.xlarge | 32GB | ~25GB |
| `streams_4.yaml` | 4 | r6id.xlarge | 32GB | ~6GB |
| `streams_8.yaml` | 8 | r6id.2xlarge | 64GB | ~6GB |
| `streams_16.yaml` | 16 | r6id.4xlarge | 128GB | ~6GB |

**Instance Sizing Rationale**:
- Memory per stream kept roughly constant (~6GB) for fair comparison
- Smaller instances for low concurrency avoid over-provisioning
- DuckDB can participate in all single-node tests

**Experiments**: 4 configs x 5 systems = **20 experiments**

---

## Series 5: Stress Tests (Combined Dimensions)

**Purpose**: Validate combined scaling behavior at extremes
**Systems**: 4 (exclude DuckDB for cluster tests)

| Config | Nodes | SF | Streams | Instance | RAM/Node | Total RAM | Purpose |
|--------|-------|-----|---------|----------|----------|-----------|---------|
| `max_nodes_sf.yaml` | 16 | 100 | 4 | r6id.2xlarge | 64GB | 1024GB | Max data + nodes |
| `max_nodes_streams.yaml` | 16 | 50 | 16 | r6id.2xlarge | 64GB | 1024GB | Max concurrency + nodes |

**Instance Sizing Rationale**:
- 16 nodes x 64GB = 1TB total cluster RAM
- Sufficient for SF100 data (~100GB) with comfortable margin
- Adequate memory per stream even at 16 concurrent streams

**Experiments**: 2 configs x 4 systems = **8 experiments**

---

## Summary

| Series | Configs | Systems | Experiments | Purpose |
|--------|---------|---------|-------------|---------|
| 1. Node Scaling | 4 | 4 | 16 | Horizontal scalability |
| 2. SF Scaling | 3 | 5 | 15 | Data scalability (single-node) |
| 3. Streams (Cluster) | 4 | 4 | 16 | Cluster concurrency |
| 4. Streams (Single) | 4 | 5 | 20 | Single-node concurrency |
| 5. Stress Tests | 2 | 4 | 8 | Combined validation |
| **Total** | **17** | - | **75** | - |

**Reduction**: From 240 (full factorial) to 75 experiments (69% reduction)

---

## Fair Comparison Strategy

### Hardware Consistency
- Within each config file, ALL systems use the **same instance type**
- Results only compared when hardware is identical

### Comparison Groups
1. **All 5 systems**: Series 2 (SF scaling), Series 4 (single-node streams)
2. **4 cluster systems**: Series 1 (nodes), Series 3 (cluster streams), Series 5 (stress)

### Analysis Approach
- Present results grouped by series
- Never compare DuckDB cluster vs distributed systems on clusters
- Highlight ClickHouse stream limitations in analysis

---

## Usage

### View Experiment Plan (Dry-Run)

```bash
./configs/extended_scalability/run_all.sh --dry-run
```

### View Current Status

```bash
./configs/extended_scalability/run_all.sh --list
```

### Run All Series

```bash
./configs/extended_scalability/run_all.sh
```

### Run Specific Series

```bash
./configs/extended_scalability/run_all.sh --series 1   # Node scaling
./configs/extended_scalability/run_all.sh --series 2   # SF scaling
./configs/extended_scalability/run_all.sh --series 3   # Cluster streams
./configs/extended_scalability/run_all.sh --series 4   # Single-node streams
./configs/extended_scalability/run_all.sh --series 5   # Stress tests
```

### Resume After Interruption

```bash
./configs/extended_scalability/run_all.sh --resume
```

### Run Single Experiment

```bash
./configs/extended_scalability/run_all.sh --experiment s1_nodes_4
```

### Sequential System Execution

By default, all systems in a config run simultaneously. For large clusters (e.g., 16-node configs), this requires 64+ instances which may exceed cloud quotas.

The `--systems` option enables sequential execution where each system is provisioned, benchmarked, and destroyed before the next:

```bash
# Run all systems one at a time (reduces resource pressure)
./configs/extended_scalability/run_all.sh --systems sequential --experiment s1_nodes_16

# Run only specific systems sequentially
./configs/extended_scalability/run_all.sh --systems exasol,clickhouse --series 1

# Run entire series with sequential system execution
./configs/extended_scalability/run_all.sh --systems sequential --series 1

# Resume sequential run (tracks per-system state)
./configs/extended_scalability/run_all.sh --resume --systems sequential --series 1
```

**Benefits**:
- **Reduced resource pressure**: Deploy 1 system instead of 4-5 simultaneously
- **Lower instance requirements**: 16 instances max (16-node single system) vs 64 (16-node × 4 systems)
- **Better availability**: Easier to get cloud capacity for fewer instances
- **Incremental progress**: Completed systems are preserved if later systems fail
- **Resume granularity**: Can resume at per-system level

---

## Verification Plan

### Config Validation

```bash
# Validate each config before running
for config in configs/extended_scalability/**/*.yaml; do
  python -m benchkit check -c "$config"
done
```

### Infrastructure Verification

```bash
# Verify AWS quotas support 64 instances (Series 1, 16-node config)
aws service-quotas get-service-quota \
  --service-code ec2 \
  --quota-code L-1216C47A  # Running On-Demand instances
```

### Post-Run Verification

- Check `results/*/runs.csv` contains all expected queries (22 TPC-H x runs)
- Verify no failed queries in results
- Compare system timing variance across runs

---

## System-Specific Configuration Notes

### Exasol
- Uses c4 cluster tool for native installation
- `db_mem_size` is cluster-wide memory in MB
- Supports multinode via `node_count` parameter

### ClickHouse
- Native APT installation with sharding (no replication)
- `max_memory_usage` is per-query-per-node
- Uses `grace_hash` join algorithm for large joins

### Trino
- Requires S3 bucket for multinode (auto-provisioned by Terraform)
- Single-node works without S3
- `query_max_memory` is cluster-wide limit

### StarRocks
- FE/BE architecture with native installation
- `bucket_count` should be `nodes x 4` for even distribution
- `replication_num: 1` for sharding (not replication)

### DuckDB
- Embedded single-node only
- Excluded from all multinode tests
- Participates in Series 2 (SF) and Series 4 (single-node streams)
