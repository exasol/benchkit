# Exasol vs StarRocks: TPC-H SF1 (Single-Node, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 10:32:20


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

### Starrocks 4.0.4


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** starrocks 4.0.4


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **32.8ms** median runtime
- **starrocks** was **5.7×** slower- Tested **220** total query executions across 22 different query types

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
| Aggregation        |     21.5 |       102   | exasol   |
| Join-Heavy         |     43.3 |       239.2 | exasol   |
| Complex Analytical |     48.9 |       208.1 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         135   |           388.5 |    2.88 |      0.35 | False    |
| Q02     | exasol            | starrocks           |          32.9 |           266.2 |    8.09 |      0.12 | False    |
| Q03     | exasol            | starrocks           |          47.3 |           203.4 |    4.3  |      0.23 | False    |
| Q04     | exasol            | starrocks           |          17.1 |           115.6 |    6.76 |      0.15 | False    |
| Q05     | exasol            | starrocks           |          45.5 |           223.6 |    4.91 |      0.2  | False    |
| Q06     | exasol            | starrocks           |          11.2 |            81.1 |    7.24 |      0.14 | False    |
| Q07     | exasol            | starrocks           |          48.9 |           265.6 |    5.43 |      0.18 | False    |
| Q08     | exasol            | starrocks           |          27.2 |           260.8 |    9.59 |      0.1  | False    |
| Q09     | exasol            | starrocks           |         112.3 |           305.5 |    2.72 |      0.37 | False    |
| Q10     | exasol            | starrocks           |          55.3 |           188   |    3.4  |      0.29 | False    |
| Q11     | exasol            | starrocks           |          24.4 |           109.2 |    4.48 |      0.22 | False    |
| Q12     | exasol            | starrocks           |          21.5 |           123.6 |    5.75 |      0.17 | False    |
| Q13     | exasol            | starrocks           |         120   |           208.1 |    1.73 |      0.58 | False    |
| Q14     | exasol            | starrocks           |          17.2 |            86.9 |    5.05 |      0.2  | False    |
| Q15     | exasol            | starrocks           |          23.8 |            98.5 |    4.14 |      0.24 | False    |
| Q16     | exasol            | starrocks           |          94.4 |           232.1 |    2.46 |      0.41 | False    |
| Q17     | exasol            | starrocks           |          11.8 |            85.3 |    7.23 |      0.14 | False    |
| Q18     | exasol            | starrocks           |          79.4 |           237.1 |    2.99 |      0.33 | False    |
| Q19     | exasol            | starrocks           |          11.5 |            87.3 |    7.59 |      0.13 | False    |
| Q20     | exasol            | starrocks           |          31.4 |           110.2 |    3.51 |      0.28 | False    |
| Q21     | exasol            | starrocks           |          67.4 |           407.3 |    6.04 |      0.17 | False    |
| Q22     | exasol            | starrocks           |          23.9 |            91.5 |    3.83 |      0.26 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    134.9 |      5 |       135   |     152.3 |     31.3 |    134.1 |    206.9 |
| Q01     | starrocks |    980.1 |      5 |       388.5 |     392.7 |     27.3 |    365.1 |    431.5 |
| Q02     | exasol    |     59.3 |      5 |        32.9 |      34.6 |      3.9 |     32.5 |     41.6 |
| Q02     | starrocks |    533.9 |      5 |       266.2 |     270.7 |     37.1 |    221.2 |    325.3 |
| Q03     | exasol    |     49.1 |      5 |        47.3 |      47.2 |      0.1 |     47   |     47.3 |
| Q03     | starrocks |    305.3 |      5 |       203.4 |     186   |     42.9 |    136   |    231.6 |
| Q04     | exasol    |     17.8 |      5 |        17.1 |      17.1 |      0.6 |     16.5 |     18.1 |
| Q04     | starrocks |    280.2 |      5 |       115.6 |     129.6 |     34   |     98.9 |    167.2 |
| Q05     | exasol    |     57.5 |      5 |        45.5 |      47.9 |      5.6 |     45   |     57.8 |
| Q05     | starrocks |    247.4 |      5 |       223.6 |     220.5 |     23.9 |    180.8 |    240   |
| Q06     | exasol    |     11.4 |      5 |        11.2 |      11.2 |      0.1 |     11   |     11.3 |
| Q06     | starrocks |     84.1 |      5 |        81.1 |      80.7 |     16.6 |     54.9 |     95.4 |
| Q07     | exasol    |     50.7 |      5 |        48.9 |      48.7 |      0.5 |     48.1 |     49.4 |
| Q07     | starrocks |    349.1 |      5 |       265.6 |     263.8 |     37.6 |    207.5 |    306.8 |
| Q08     | exasol    |     35.7 |      5 |        27.2 |      27.8 |      1.9 |     26.4 |     31.1 |
| Q08     | starrocks |    370.9 |      5 |       260.8 |     258.4 |     48.1 |    195.6 |    328.7 |
| Q09     | exasol    |    113.6 |      5 |       112.3 |     112.9 |      2.5 |    109.8 |    115.6 |
| Q09     | starrocks |    307.9 |      5 |       305.5 |     309.2 |     53.7 |    260.6 |    397.1 |
| Q10     | exasol    |     57.5 |      5 |        55.3 |      55.2 |      0.3 |     54.9 |     55.6 |
| Q10     | starrocks |    212.7 |      5 |       188   |     198.4 |     27.1 |    172.5 |    242.2 |
| Q11     | exasol    |     23   |      5 |        24.4 |      29.3 |      7.7 |     23.7 |     40.9 |
| Q11     | starrocks |     96   |      5 |       109.2 |     100.8 |     16.4 |     82.8 |    116.6 |
| Q12     | exasol    |     25.9 |      5 |        21.5 |      21.5 |      0.3 |     21.2 |     21.8 |
| Q12     | starrocks |    184.3 |      5 |       123.6 |     120.2 |     13.3 |    103.6 |    136.3 |
| Q13     | exasol    |    122.2 |      5 |       120   |     120.2 |      1.1 |    118.5 |    121.3 |
| Q13     | starrocks |    294.7 |      5 |       208.1 |     218.8 |     25.3 |    196.3 |    257.4 |
| Q14     | exasol    |     19.5 |      5 |        17.2 |      17.1 |      0.2 |     16.9 |     17.3 |
| Q14     | starrocks |    109.7 |      5 |        86.9 |      85.7 |     20.4 |     62.3 |    106.7 |
| Q15     | exasol    |     25.8 |      5 |        23.8 |      23.9 |      0.3 |     23.5 |     24.2 |
| Q15     | starrocks |    152.6 |      5 |        98.5 |      92.5 |     13.7 |     76.9 |    108.8 |
| Q16     | exasol    |    103   |      5 |        94.4 |      96.8 |      7.2 |     92.3 |    109.6 |
| Q16     | starrocks |    269.8 |      5 |       232.1 |     263.3 |     64.5 |    199.8 |    348.6 |
| Q17     | exasol    |     13   |      5 |        11.8 |      11.9 |      0.4 |     11.7 |     12.6 |
| Q17     | starrocks |    103.7 |      5 |        85.3 |      95.1 |     26.1 |     68.1 |    125.7 |
| Q18     | exasol    |     83.4 |      5 |        79.4 |      79.4 |      0.3 |     79.1 |     79.8 |
| Q18     | starrocks |    233.3 |      5 |       237.1 |     248.1 |     28.5 |    221.3 |    285.5 |
| Q19     | exasol    |     12.7 |      5 |        11.5 |      11.5 |      0.3 |     11.1 |     11.8 |
| Q19     | starrocks |     92.3 |      5 |        87.3 |      85.6 |      9.8 |     71.4 |     98.3 |
| Q20     | exasol    |     35   |      5 |        31.4 |      31.4 |      0.1 |     31.3 |     31.6 |
| Q20     | starrocks |    114.9 |      5 |       110.2 |     122.9 |     29   |    102   |    170.6 |
| Q21     | exasol    |     70   |      5 |        67.4 |      67.3 |      0.1 |     67.1 |     67.4 |
| Q21     | starrocks |    549.8 |      5 |       407.3 |     409.7 |     50.9 |    358   |    491.1 |
| Q22     | exasol    |     24.2 |      5 |        23.9 |      24   |      0.3 |     23.8 |     24.4 |
| Q22     | starrocks |     95.7 |      5 |        91.5 |      84.8 |     13.2 |     62   |     93.8 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 32.8ms
- Average: 49.5ms
- Range: 11.0ms - 206.9ms

**#2. Starrocks**
- Median: 186.2ms
- Average: 192.6ms
- Range: 54.9ms - 491.1ms



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