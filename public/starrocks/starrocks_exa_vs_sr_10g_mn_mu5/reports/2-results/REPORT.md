# Exasol vs StarRocks: TPC-H SF10 (Multi-Node 3, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:34:59


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
- **exasol** was the fastest overall with **805.8ms** median runtime
- **starrocks** was **3.2×** slower- Tested **220** total query executions across 22 different query types
- **Execution mode:** Multiuser with **5 concurrent streams** (randomized distribution)

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
| Aggregation        |    573   |      2070.8 | exasol   |
| Join-Heavy         |   1105   |      3893.3 | exasol   |
| Complex Analytical |   1537.1 |      3006.6 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        2121   |         30394   |   14.33 |      0.07 | False    |
| Q02     | exasol            | starrocks           |         418.8 |          1184.6 |    2.83 |      0.35 | False    |
| Q03     | exasol            | starrocks           |        1420.5 |          9395.6 |    6.61 |      0.15 | False    |
| Q04     | exasol            | starrocks           |         525.6 |          1965.7 |    3.74 |      0.27 | False    |
| Q05     | exasol            | starrocks           |        1665.2 |          4039.9 |    2.43 |      0.41 | False    |
| Q06     | exasol            | starrocks           |         140.3 |           849.1 |    6.05 |      0.17 | False    |
| Q07     | exasol            | starrocks           |        2419.3 |          3492.3 |    1.44 |      0.69 | False    |
| Q08     | exasol            | starrocks           |         957.2 |          3990   |    4.17 |      0.24 | False    |
| Q09     | exasol            | starrocks           |        5934.6 |          6900   |    1.16 |      0.86 | False    |
| Q10     | exasol            | starrocks           |        1759.8 |          6537.9 |    3.72 |      0.27 | False    |
| Q11     | exasol            | starrocks           |         346.9 |           733.2 |    2.11 |      0.47 | False    |
| Q12     | exasol            | starrocks           |         507.6 |          2024.4 |    3.99 |      0.25 | False    |
| Q13     | exasol            | starrocks           |        2866   |          6883   |    2.4  |      0.42 | False    |
| Q14     | exasol            | starrocks           |         638.1 |          2236.1 |    3.5  |      0.29 | False    |
| Q15     | exasol            | starrocks           |         470.1 |          1221.4 |    2.6  |      0.38 | False    |
| Q16     | exasol            | starrocks           |        1377.6 |          1814.8 |    1.32 |      0.76 | False    |
| Q17     | exasol            | starrocks           |         226.8 |          1584.7 |    6.99 |      0.14 | False    |
| Q18     | exasol            | starrocks           |        2065.3 |          6166   |    2.99 |      0.33 | False    |
| Q19     | exasol            | starrocks           |         488.1 |          1990.8 |    4.08 |      0.25 | False    |
| Q20     | exasol            | starrocks           |         804.8 |          3202.7 |    3.98 |      0.25 | False    |
| Q21     | exasol            | starrocks           |        1345.2 |         25363.2 |   18.85 |      0.05 | False    |
| Q22     | exasol            | starrocks           |         335   |          1004.3 |    3    |      0.33 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    440.8 |      5 |      2121   |    2097.8 |   1247.2 |    438.6 |   3349   |
| Q01     | starrocks |   5710.8 |      5 |     30394   |   40143.5 |  36874.2 |   5246.5 |  99238.1 |
| Q02     | exasol    |    126.6 |      5 |       418.8 |     394.7 |    123.2 |    261.4 |    569   |
| Q02     | starrocks |    475.2 |      5 |      1184.6 |    1294   |    591.4 |    811.9 |   2251.1 |
| Q03     | exasol    |    369.4 |      5 |      1420.5 |    1339.4 |    642.4 |    360   |   2137.2 |
| Q03     | starrocks |   1749.3 |      5 |      9395.6 |    8470.3 |   1745.7 |   6393.1 |  10328.3 |
| Q04     | exasol    |    115.7 |      5 |       525.6 |     513.8 |    135.5 |    288.7 |    627.2 |
| Q04     | starrocks |    833.8 |      5 |      1965.7 |    1845.9 |    536.4 |   1003.4 |   2470.6 |
| Q05     | exasol    |    347.9 |      5 |      1665.2 |    2084.5 |   1028.2 |   1423.2 |   3891.7 |
| Q05     | starrocks |   1262.4 |      5 |      4039.9 |    4005.9 |   2054.4 |   1659.1 |   7230.1 |
| Q06     | exasol    |     36.3 |      5 |       140.3 |     163.3 |    108.2 |     33.7 |    327.1 |
| Q06     | starrocks |    491.8 |      5 |       849.1 |    1095.2 |    721.3 |    312.4 |   2087   |
| Q07     | exasol    |    517.4 |      5 |      2419.3 |    2318   |    491.6 |   1544.5 |   2901.8 |
| Q07     | starrocks |   1233.7 |      5 |      3492.3 |    3620.1 |   1217   |   2052.6 |   5227.3 |
| Q08     | exasol    |    191.4 |      5 |       957.2 |     930   |    229.3 |    576.8 |   1212.3 |
| Q08     | starrocks |   1609.6 |      5 |      3990   |    4261.3 |   1221.6 |   2876.3 |   6124.5 |
| Q09     | exasol    |   1399.7 |      5 |      5934.6 |    5522   |   1536.8 |   2983.4 |   7033.7 |
| Q09     | starrocks |   2544.8 |      5 |      6900   |    8917   |   4250.2 |   5590.8 |  15573.4 |
| Q10     | exasol    |    321   |      5 |      1759.8 |    1559.1 |    550.7 |    690.8 |   2158.2 |
| Q10     | starrocks |   2558.4 |      5 |      6537.9 |    5896.2 |   1676.8 |   3796.6 |   7950.7 |
| Q11     | exasol    |     80.8 |      5 |       346.9 |    1900.3 |   3528.2 |    250   |   8210.2 |
| Q11     | starrocks |    284.5 |      5 |       733.2 |    1151.5 |    826.7 |    416.2 |   2399   |
| Q12     | exasol    |    110   |      5 |       507.6 |     500.7 |     95.5 |    363.6 |    602.9 |
| Q12     | starrocks |    948.6 |      5 |      2024.4 |    1766.7 |    542.6 |   1175.7 |   2356.4 |
| Q13     | exasol    |    534.9 |      5 |      2866   |    2533   |   1249.5 |    515.3 |   3895.9 |
| Q13     | starrocks |   1884.5 |      5 |      6883   |    6691.1 |   4448.6 |   2493   |  13638.8 |
| Q14     | exasol    |    139.7 |      5 |       638.1 |     624.8 |    150.9 |    390.8 |    806.9 |
| Q14     | starrocks |    960.1 |      5 |      2236.1 |    2117.6 |   1064.5 |    717.4 |   3437.3 |
| Q15     | exasol    |    108.4 |      5 |       470.1 |     619.4 |    412.2 |    258.7 |   1307.6 |
| Q15     | starrocks |    641.9 |      5 |      1221.4 |    1297.6 |    564.4 |    690.3 |   2166.5 |
| Q16     | exasol    |    309.2 |      5 |      1377.6 |    2663.7 |   2869.2 |   1017.4 |   7747.5 |
| Q16     | starrocks |    596.8 |      5 |      1814.8 |    1701   |    650   |    651.6 |   2428   |
| Q17     | exasol    |     55   |      5 |       226.8 |     172.2 |    103.9 |     53.4 |    272.9 |
| Q17     | starrocks |    947.4 |      5 |      1584.7 |    2528.6 |   2019.2 |   1092.7 |   5950.7 |
| Q18     | exasol    |    275.9 |      5 |      2065.3 |    2090.1 |    482.6 |   1606.6 |   2711.6 |
| Q18     | starrocks |   2320.9 |      5 |      6166   |    5673.5 |   2300.5 |   2599   |   8167.8 |
| Q19     | exasol    |     53.9 |      5 |       488.1 |     525.9 |    271.5 |    250.9 |    905.7 |
| Q19     | starrocks |   1500.9 |      5 |      1990.8 |    1836.9 |    370   |   1382.1 |   2231   |
| Q20     | exasol    |    234.7 |      5 |       804.8 |    1054.6 |    771.3 |    180.8 |   2050.5 |
| Q20     | starrocks |   1523.6 |      5 |      3202.7 |    3265.2 |   1284.8 |   1405   |   4860.4 |
| Q21     | exasol    |    274.8 |      5 |      1345.2 |    1646.6 |   1083.4 |    278.1 |   3134.9 |
| Q21     | starrocks |   4094.3 |      5 |     25363.2 |   31960.5 |  20353.2 |  16666   |  67636   |
| Q22     | exasol    |     72.4 |      5 |       335   |     343   |    106.4 |    223.3 |    512   |
| Q22     | starrocks |    502.6 |      5 |      1004.3 |    1164.9 |    884.6 |    398.8 |   2565.1 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 805.8ms
- Average: 1436.2ms
- Range: 33.7ms - 8210.2ms

**#2. Starrocks**
- Median: 2582.1ms
- Average: 6395.7ms
- Range: 312.4ms - 99238.1ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 1459.4 | 1047.6 | 140.3 | 5934.6 |
| 1 | 22 | 1198.2 | 672.9 | 255.9 | 3895.9 |
| 2 | 22 | 1400.5 | 856.5 | 250.9 | 6252.1 |
| 3 | 22 | 1643.3 | 562.8 | 33.7 | 8210.2 |
| 4 | 22 | 1479.8 | 1259.9 | 66.6 | 7747.5 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 562.8ms
- **Worst stream median:** 1259.9ms
- **Performance variance:** 123.9% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 6295.6 | 3388.1 | 626.3 | 25363.2 |
| 1 | 22 | 5566.1 | 2303.8 | 733.2 | 49189.5 |
| 2 | 22 | 7398.9 | 2668.2 | 398.8 | 99238.1 |
| 3 | 22 | 5869.7 | 3173.3 | 1092.7 | 27501.1 |
| 4 | 22 | 6848.0 | 2069.8 | 312.4 | 67636.0 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 2069.8ms
- **Worst stream median:** 3388.1ms
- **Performance variance:** 63.7% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

**Query Distribution Method:**
- Query distribution was **randomized** (seed: 42) for realistic concurrent user simulation


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 5
- **Execution Mode:** Multiuser (5 concurrent streams)
- **Query Distribution:** Randomized (seed: 42)- **Metric Reported:** Median execution time

### Performance Measurement

All queries were executed with the same data and parameters across all systems. The median execution time from 5 runs is reported for each query to minimize the impact of system variance and outliers.

## Conclusion

This benchmark provides a detailed, query-level comparison of 2 database systems on analytical workloads. The results demonstrate the performance characteristics and trade-offs of each system when processing TPC-H queries.

While **exasol** demonstrated the strongest overall performance in this test, the optimal choice for a specific use case depends on multiple factors including workload characteristics, operational requirements, and system integration needs.

---

**For complete reproduction details** including installation steps, configuration parameters, and a self-contained benchmark package, see the [full benchmark report](../3-full/REPORT.md).

---

*All benchmark data, figures, and configuration files are available in the attachments directory for independent analysis and verification.*