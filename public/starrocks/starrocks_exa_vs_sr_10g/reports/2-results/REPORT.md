# Exasol vs StarRocks: TPC-H SF10 (Single-Node, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 13:14:48


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 10.

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
- **exasol** was the fastest overall with **210.0ms** median runtime
- **starrocks** was **4.6×** slower- Tested **220** total query executions across 22 different query types

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
| Aggregation        |    111   |       476   | exasol   |
| Join-Heavy         |    326.4 |      1636   | exasol   |
| Complex Analytical |    422.9 |      1663.7 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1244.5 |          4221   |    3.39 |      0.29 | False    |
| Q02     | exasol            | starrocks           |          41.6 |           312   |    7.5  |      0.13 | False    |
| Q03     | exasol            | starrocks           |         422.9 |          1811   |    4.28 |      0.23 | False    |
| Q04     | exasol            | starrocks           |          88.1 |           620.3 |    7.04 |      0.14 | False    |
| Q05     | exasol            | starrocks           |         328.1 |          1645.1 |    5.01 |      0.2  | False    |
| Q06     | exasol            | starrocks           |          58.4 |           321.8 |    5.51 |      0.18 | False    |
| Q07     | exasol            | starrocks           |         389.6 |          2556.2 |    6.56 |      0.15 | False    |
| Q08     | exasol            | starrocks           |         107.9 |          1629.6 |   15.1  |      0.07 | False    |
| Q09     | exasol            | starrocks           |        1111.5 |          3131.8 |    2.82 |      0.35 | False    |
| Q10     | exasol            | starrocks           |         463.4 |          1776.6 |    3.83 |      0.26 | False    |
| Q11     | exasol            | starrocks           |          82.6 |           198   |    2.4  |      0.42 | False    |
| Q12     | exasol            | starrocks           |         118.6 |           476   |    4.01 |      0.25 | False    |
| Q13     | exasol            | starrocks           |        1108.8 |          1663.7 |    1.5  |      0.67 | False    |
| Q14     | exasol            | starrocks           |         104.2 |           339.9 |    3.26 |      0.31 | False    |
| Q15     | exasol            | starrocks           |         110.5 |           390.3 |    3.53 |      0.28 | False    |
| Q16     | exasol            | starrocks           |         438.1 |           448.4 |    1.02 |      0.98 | False    |
| Q17     | exasol            | starrocks           |          19.8 |           486.2 |   24.56 |      0.04 | False    |
| Q18     | exasol            | starrocks           |         679.5 |          2388.6 |    3.52 |      0.28 | False    |
| Q19     | exasol            | starrocks           |          34.2 |          1190.9 |   34.82 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         210.9 |           543   |    2.57 |      0.39 | False    |
| Q21     | exasol            | starrocks           |         627.7 |          3171.3 |    5.05 |      0.2  | False    |
| Q22     | exasol            | starrocks           |         141.9 |           427.5 |    3.01 |      0.33 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1251.2 |      5 |      1244.5 |    1248.7 |      6.4 |   1243.5 |   1256.4 |
| Q01     | starrocks |   5800.7 |      5 |      4221   |    4197.3 |     56.2 |   4118.6 |   4257   |
| Q02     | exasol    |     96.8 |      5 |        41.6 |      41.5 |      0.3 |     41.2 |     41.9 |
| Q02     | starrocks |    637.5 |      5 |       312   |     307.9 |     39.8 |    241.4 |    343.9 |
| Q03     | exasol    |    434.2 |      5 |       422.9 |     422.1 |      2.7 |    417.5 |    424.2 |
| Q03     | starrocks |   1892.1 |      5 |      1811   |    1849.8 |     85.6 |   1783.1 |   1987.9 |
| Q04     | exasol    |     89.8 |      5 |        88.1 |      88.2 |      0.5 |     87.7 |     89   |
| Q04     | starrocks |   1055.9 |      5 |       620.3 |     634.7 |     94   |    551.7 |    795   |
| Q05     | exasol    |    387.2 |      5 |       328.1 |     328.5 |      2.3 |    325.6 |    331.3 |
| Q05     | starrocks |   1735.2 |      5 |      1645.1 |    1670.7 |    106.8 |   1592   |   1856.3 |
| Q06     | exasol    |     57.3 |      5 |        58.4 |      60   |      3.7 |     57.8 |     66.5 |
| Q06     | starrocks |    584.1 |      5 |       321.8 |     314.4 |     23   |    282.8 |    339.3 |
| Q07     | exasol    |    402.1 |      5 |       389.6 |     391   |      6.4 |    383.6 |    398.6 |
| Q07     | starrocks |   2183.6 |      5 |      2556.2 |    2541.2 |    109   |   2425.4 |   2685.9 |
| Q08     | exasol    |    110.4 |      5 |       107.9 |     156.4 |    107   |    106.3 |    347.7 |
| Q08     | starrocks |   1846.3 |      5 |      1629.6 |    1640.7 |     20   |   1628   |   1674.8 |
| Q09     | exasol    |   1139   |      5 |      1111.5 |    1112.3 |      8.8 |   1101.4 |   1121.2 |
| Q09     | starrocks |   3167.7 |      5 |      3131.8 |    3167.1 |    171.7 |   3020.9 |   3459.9 |
| Q10     | exasol    |    473.6 |      5 |       463.4 |     462.8 |      3.9 |    456.4 |    466.6 |
| Q10     | starrocks |   1825.3 |      5 |      1776.6 |    1833   |    138.3 |   1739.9 |   2071.2 |
| Q11     | exasol    |     85.2 |      5 |        82.6 |      84.9 |      6.5 |     80.4 |     96.4 |
| Q11     | starrocks |    251.2 |      5 |       198   |     198.6 |      5.9 |    193.1 |    208.4 |
| Q12     | exasol    |    168.9 |      5 |       118.6 |     119.9 |      3.5 |    117.4 |    125.9 |
| Q12     | starrocks |   1520.8 |      5 |       476   |     483.9 |     39.7 |    453.4 |    552.2 |
| Q13     | exasol    |   1197.9 |      5 |      1108.8 |    1108.4 |      6.3 |   1098.9 |   1114   |
| Q13     | starrocks |   2092.7 |      5 |      1663.7 |    1673.5 |     38   |   1637.5 |   1738.1 |
| Q14     | exasol    |    148.8 |      5 |       104.2 |     104   |      0.6 |    103.2 |    104.6 |
| Q14     | starrocks |    861.1 |      5 |       339.9 |     359.7 |     42.1 |    328.7 |    431.4 |
| Q15     | exasol    |    121.3 |      5 |       110.5 |     110.7 |      0.8 |    109.8 |    112   |
| Q15     | starrocks |    558.6 |      5 |       390.3 |     403.2 |     41   |    362.8 |    462.5 |
| Q16     | exasol    |    457.2 |      5 |       438.1 |     441.2 |     10.2 |    430.9 |    455.7 |
| Q16     | starrocks |    673   |      5 |       448.4 |     455.8 |     66.8 |    384   |    531   |
| Q17     | exasol    |     29.9 |      5 |        19.8 |      19.7 |      0.5 |     19   |     20.1 |
| Q17     | starrocks |    769.6 |      5 |       486.2 |     497.3 |     38.6 |    470.5 |    564.9 |
| Q18     | exasol    |    692.1 |      5 |       679.5 |     679.5 |      0.7 |    678.3 |    680.1 |
| Q18     | starrocks |   2693.6 |      5 |      2388.6 |    2413.2 |     75.8 |   2337.3 |   2536.1 |
| Q19     | exasol    |     46   |      5 |        34.2 |      63.3 |     53.8 |     33.8 |    157.9 |
| Q19     | starrocks |   1581.2 |      5 |      1190.9 |    1181.5 |     55.9 |   1117.3 |   1252.9 |
| Q20     | exasol    |    247   |      5 |       210.9 |     210.7 |      0.7 |    209.9 |    211.5 |
| Q20     | starrocks |    908.6 |      5 |       543   |     554.8 |     33   |    529.2 |    612.3 |
| Q21     | exasol    |    623.9 |      5 |       627.7 |     625.9 |      5.4 |    619   |    632.5 |
| Q21     | starrocks |   3773.3 |      5 |      3171.3 |    3158   |     36.8 |   3094.3 |   3185   |
| Q22     | exasol    |    146.6 |      5 |       141.9 |     142.1 |      0.5 |    141.6 |    142.9 |
| Q22     | starrocks |    469.5 |      5 |       427.5 |     410.2 |     32.2 |    354.6 |    431   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 210.0ms
- Average: 364.6ms
- Range: 19.0ms - 1256.4ms

**#2. Starrocks**
- Median: 956.1ms
- Average: 1361.2ms
- Range: 193.1ms - 4257.0ms



## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
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