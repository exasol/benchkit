# Exasol vs StarRocks: TPC-H SF1 (Multi-Node 3, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:08:26


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 1.

**Systems Compared:**
- **exasol**
- **starrocks**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** exasol 2025.1.8
- **Deployment:** 3-node cluster

### Starrocks 4.0.4


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** starrocks 4.0.4
- **Deployment:** 3-node cluster


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **82.2ms** median runtime
- **starrocks** was **1.6×** slower- Tested **220** total query executions across 22 different query types

### Performance Visualizations

![System performance overview](attachments/figures/system_performance_overview.html)

![All systems comparison](attachments/figures/all_systems_comparison.html)

![Performance heatmap](attachments/figures/performance_heatmap.html)

![Speedup comparison](attachments/figures/speedup_comparison.html)


## Detailed Analysis

### Performance by Query Type

The benchmark results reveal distinct performance characteristics across different query categories:

- **Aggregation queries** (Q01, Q06, Q12, Q14, Q15, Q19, Q20): Test data reduction and grouping operations
- **Join-heavy queries** (Q02, Q05, Q08, Q09, Q10, Q11, Q21, Q22): Evaluate multi-table join performance
- **Complex analytical queries** (Q03, Q04, Q07, Q13, Q16, Q17, Q18): Combine multiple operations

The following table shows the median performance for each query category across all systems:

| Query Type         |   exasol |   starrocks | Winner   |
|--------------------|----------|-------------|----------|
| Aggregation        |     51.6 |       104.1 | exasol   |
| Join-Heavy         |    101.9 |       194.2 | exasol   |
| Complex Analytical |    106   |       132.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |          72.4 |           480.9 |    6.64 |      0.15 | False    |
| Q02     | exasol            | starrocks           |         117.6 |           244.4 |    2.08 |      0.48 | False    |
| Q03     | exasol            | starrocks           |          76   |           118.6 |    1.56 |      0.64 | False    |
| Q04     | exasol            | starrocks           |          49.5 |           106.8 |    2.16 |      0.46 | False    |
| Q05     | exasol            | starrocks           |         101.2 |           157.9 |    1.56 |      0.64 | False    |
| Q06     | exasol            | starrocks           |          25.3 |            56.6 |    2.24 |      0.45 | False    |
| Q07     | exasol            | starrocks           |         109.4 |           132.3 |    1.21 |      0.83 | False    |
| Q08     | exasol            | starrocks           |         110.1 |           174.4 |    1.58 |      0.63 | False    |
| Q09     | exasol            | starrocks           |         195.3 |           242.9 |    1.24 |      0.8  | False    |
| Q10     | exasol            | starrocks           |         102.9 |           236.3 |    2.3  |      0.44 | False    |
| Q11     | exasol            | starrocks           |          71.3 |           118.2 |    1.66 |      0.6  | False    |
| Q12     | exasol            | starrocks           |          51   |           106.4 |    2.09 |      0.48 | False    |
| Q13     | exasol            | starrocks           |          77.8 |           179   |    2.3  |      0.43 | False    |
| Q14     | exasol            | starrocks           |          46.4 |            89   |    1.92 |      0.52 | False    |
| Q15     | exasol            | starrocks           |          72.6 |           107   |    1.47 |      0.68 | False    |
| Q16     | exasol            | starrocks           |         133.7 |           219.3 |    1.64 |      0.61 | False    |
| Q17     | exasol            | starrocks           |          77.7 |            94.3 |    1.21 |      0.82 | False    |
| Q18     | exasol            | starrocks           |         226.2 |           225.1 |    1    |      1    | True     |
| Q19     | exasol            | starrocks           |          42.8 |            73.5 |    1.72 |      0.58 | False    |
| Q20     | exasol            | starrocks           |          94.7 |           113.6 |    1.2  |      0.83 | False    |
| Q21     | exasol            | starrocks           |          83.1 |           424.3 |    5.11 |      0.2  | False    |
| Q22     | exasol            | starrocks           |          47.6 |            75.9 |    1.59 |      0.63 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |     80.7 |      5 |        72.4 |      72.6 |      0.6 |     71.9 |     73.3 |
| Q01     | starrocks |    868   |      5 |       480.9 |     499   |     42.2 |    463.4 |    559.9 |
| Q02     | exasol    |    193   |      5 |       117.6 |     120.1 |      4.1 |    116.7 |    124.8 |
| Q02     | starrocks |    369.4 |      5 |       244.4 |     238.2 |     40   |    183   |    280.9 |
| Q03     | exasol    |     76.8 |      5 |        76   |      80.9 |     10.9 |     72.9 |     99.1 |
| Q03     | starrocks |    258.3 |      5 |       118.6 |     119.1 |      7   |    111.7 |    129.7 |
| Q04     | exasol    |     68.9 |      5 |        49.5 |      63.2 |     27.1 |     47.5 |    110.9 |
| Q04     | starrocks |    153.2 |      5 |       106.8 |     112.6 |     20.4 |     91.8 |    145.9 |
| Q05     | exasol    |    164.6 |      5 |       101.2 |     101.2 |      0.8 |    100   |    101.9 |
| Q05     | starrocks |    203.5 |      5 |       157.9 |     163   |     23.9 |    133.9 |    198.5 |
| Q06     | exasol    |     26.8 |      5 |        25.3 |      25.5 |      0.6 |     24.9 |     26.3 |
| Q06     | starrocks |     65.5 |      5 |        56.6 |      57   |     11.2 |     46.8 |     74.4 |
| Q07     | exasol    |    113.5 |      5 |       109.4 |     109.2 |      2   |    106   |    111.3 |
| Q07     | starrocks |    157.8 |      5 |       132.3 |     142.6 |     35.3 |    115.9 |    204.7 |
| Q08     | exasol    |    109.8 |      5 |       110.1 |     110.1 |      1.2 |    108.2 |    111.6 |
| Q08     | starrocks |    183.1 |      5 |       174.4 |     171.2 |     23.5 |    141.9 |    203.7 |
| Q09     | exasol    |    196.4 |      5 |       195.3 |     194.9 |      2.5 |    191.5 |    198.3 |
| Q09     | starrocks |    310.1 |      5 |       242.9 |     235.5 |     28.7 |    189.9 |    261.3 |
| Q10     | exasol    |    101.4 |      5 |       102.9 |     102.5 |      0.9 |    101   |    103.3 |
| Q10     | starrocks |    236.5 |      5 |       236.3 |     244.9 |     48.7 |    198.4 |    301   |
| Q11     | exasol    |     71.5 |      5 |        71.3 |      71.9 |      2.2 |     69.2 |     74.4 |
| Q11     | starrocks |    127.2 |      5 |       118.2 |     115.6 |      8.9 |    101.5 |    125   |
| Q12     | exasol    |     55.7 |      5 |        51   |      50.6 |      0.9 |     49.6 |     51.6 |
| Q12     | starrocks |    166.5 |      5 |       106.4 |     104.3 |      4.9 |     96.1 |    108   |
| Q13     | exasol    |     83.4 |      5 |        77.8 |      78.2 |      1.5 |     76.9 |     80.6 |
| Q13     | starrocks |    258   |      5 |       179   |     179.4 |      9.5 |    167.6 |    191.7 |
| Q14     | exasol    |     48.3 |      5 |        46.4 |      46.4 |      0.3 |     45.8 |     46.7 |
| Q14     | starrocks |    102.1 |      5 |        89   |      97.8 |     28.7 |     72.4 |    144.6 |
| Q15     | exasol    |     74.4 |      5 |        72.6 |      72.5 |      0.9 |     71.2 |     73.5 |
| Q15     | starrocks |    102.7 |      5 |       107   |     102.8 |     15.2 |     76.7 |    116.3 |
| Q16     | exasol    |    143.3 |      5 |       133.7 |     136.7 |      7.9 |    132.4 |    150.7 |
| Q16     | starrocks |    260.4 |      5 |       219.3 |     236.7 |     50.7 |    190.5 |    322.6 |
| Q17     | exasol    |     76.6 |      5 |        77.7 |     104.3 |     40   |     73.8 |    154.1 |
| Q17     | starrocks |    126   |      5 |        94.3 |     101.6 |     17   |     86.2 |    125.1 |
| Q18     | exasol    |    240   |      5 |       226.2 |     278.3 |     93.2 |    223.7 |    440.1 |
| Q18     | starrocks |    265.8 |      5 |       225.1 |     257.4 |     68   |    196.2 |    352.2 |
| Q19     | exasol    |    161.3 |      5 |        42.8 |      62.2 |     35   |     41.7 |    123.1 |
| Q19     | starrocks |    100.5 |      5 |        73.5 |      72   |      6.8 |     61.2 |     79   |
| Q20     | exasol    |     94.9 |      5 |        94.7 |      94.6 |      1   |     93.3 |     95.9 |
| Q20     | starrocks |    140.8 |      5 |       113.6 |     118.1 |     14.1 |    104.1 |    139.4 |
| Q21     | exasol    |     84.2 |      5 |        83.1 |      83.1 |      0.9 |     81.9 |     84.2 |
| Q21     | starrocks |    467.8 |      5 |       424.3 |     429.8 |     51   |    379   |    509.5 |
| Q22     | exasol    |     48.3 |      5 |        47.6 |      48   |      0.9 |     47.4 |     49.6 |
| Q22     | starrocks |     75.7 |      5 |        75.9 |      73.9 |      9.5 |     58.7 |     84.9 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 82.2ms
- Average: 95.8ms
- Range: 24.9ms - 440.1ms

**#2. Starrocks**
- Median: 132.3ms
- Average: 176.0ms
- Range: 46.8ms - 559.9ms



## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 1
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 5
- **Execution Mode:** Sequential (single connection)
- **Metric Reported:** Median execution time

### Performance Measurement

All queries were executed with the same data and parameters across all systems. The median execution time from 5 runs is reported for each query to minimize the impact of system variance and outliers.

## Conclusion

This benchmark provides a detailed, query-level comparison of 2 database systems on analytical workloads. The results demonstrate the performance characteristics and trade-offs of each system when processing TPC-H queries.

While **exasol** demonstrated the strongest overall performance in this test, the optimal choice for a specific use case depends on multiple factors including workload characteristics, operational requirements, and system integration needs.

---

**For complete reproduction details** including installation steps, configuration parameters, and a self-contained benchmark package, see the [full benchmark report](../3-full/REPORT.md).

---

*All benchmark data, figures, and configuration files are available in the attachments directory for independent analysis and verification.*