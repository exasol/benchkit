# Exasol vs StarRocks: TPC-H SF30 (Single-Node, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:12:46


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **starrocks**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Starrocks 4.0.4


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** starrocks 4.0.4


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **1482.6ms** median runtime
- **starrocks** was **2.7×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |   1025   |      3341.6 | exasol   |
| Join-Heavy         |   1307   |      4771.8 | exasol   |
| Complex Analytical |   2934.7 |      4048.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        5230.3 |         35293.4 |    6.75 |      0.15 | False    |
| Q02     | exasol            | starrocks           |         303.1 |          1419.8 |    4.68 |      0.21 | False    |
| Q03     | exasol            | starrocks           |        1318.9 |          7787.7 |    5.9  |      0.17 | False    |
| Q04     | exasol            | starrocks           |         814.9 |          2856.8 |    3.51 |      0.29 | False    |
| Q05     | exasol            | starrocks           |        2123.3 |          7215.1 |    3.4  |      0.29 | False    |
| Q06     | exasol            | starrocks           |         507.2 |          2260.7 |    4.46 |      0.22 | False    |
| Q07     | exasol            | starrocks           |        3204.4 |          4062.4 |    1.27 |      0.79 | False    |
| Q08     | exasol            | starrocks           |         813.7 |          4246.1 |    5.22 |      0.19 | False    |
| Q09     | exasol            | starrocks           |       11026.6 |         24735.3 |    2.24 |      0.45 | False    |
| Q10     | exasol            | starrocks           |        3129.3 |          5313.8 |    1.7  |      0.59 | False    |
| Q11     | exasol            | starrocks           |         597.4 |           836.2 |    1.4  |      0.71 | False    |
| Q12     | exasol            | starrocks           |         829.1 |          2437.8 |    2.94 |      0.34 | False    |
| Q13     | exasol            | starrocks           |        8203.7 |         15953.1 |    1.94 |      0.51 | False    |
| Q14     | exasol            | starrocks           |        1037.6 |          2424.4 |    2.34 |      0.43 | False    |
| Q15     | exasol            | starrocks           |        1581.5 |          2323   |    1.47 |      0.68 | False    |
| Q16     | exasol            | starrocks           |        2460.5 |          1494.8 |    0.61 |      1.65 | True     |
| Q17     | exasol            | starrocks           |         202.5 |          1620.8 |    8    |      0.12 | False    |
| Q18     | exasol            | starrocks           |        4468.8 |         12834.9 |    2.87 |      0.35 | False    |
| Q19     | exasol            | starrocks           |         348.3 |          3481.5 |   10    |      0.1  | False    |
| Q20     | exasol            | starrocks           |        1722.9 |          4402.7 |    2.56 |      0.39 | False    |
| Q21     | exasol            | starrocks           |        4580.1 |         48064.6 |   10.49 |      0.1  | False    |
| Q22     | exasol            | starrocks           |         950   |          2652.6 |    2.79 |      0.36 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1870.2 |      5 |      5230.3 |    6061.8 |   2072.9 |   3575   |   8263.2 |
| Q01     | starrocks |   8279.7 |      5 |     35293.4 |   47015.9 |  29629.2 |  27573.3 |  99495.1 |
| Q02     | exasol    |     79.6 |      5 |       303.1 |     301.6 |     43.8 |    243.9 |    362.7 |
| Q02     | starrocks |    625.9 |      5 |      1419.8 |    1410.6 |    250.1 |   1044   |   1732.7 |
| Q03     | exasol    |    657.7 |      5 |      1318.9 |    1944.3 |   1259.5 |    646.7 |   3605.2 |
| Q03     | starrocks |   2943.1 |      5 |      7787.7 |    8149.8 |   3267.5 |   3609.7 |  11678.6 |
| Q04     | exasol    |    128.5 |      5 |       814.9 |    1038.5 |    731.4 |    599.3 |   2332.4 |
| Q04     | starrocks |   1525.7 |      5 |      2856.8 |    2888.7 |    464.9 |   2275.7 |   3559.3 |
| Q05     | exasol    |    531.2 |      5 |      2123.3 |    2030.6 |    633.7 |    969.8 |   2659.5 |
| Q05     | starrocks |   2708.5 |      5 |      7215.1 |    7300.3 |   2161.8 |   4405.8 |  10105.4 |
| Q06     | exasol    |     82.9 |      5 |       507.2 |     450.3 |    319.9 |     82.8 |    817.8 |
| Q06     | starrocks |   1246   |      5 |      2260.7 |    2290.6 |    906.9 |   1388.1 |   3505   |
| Q07     | exasol    |    647.6 |      5 |      3204.4 |    3253.3 |    380.1 |   2821   |   3856   |
| Q07     | starrocks |   3218.7 |      5 |      4062.4 |    5502.4 |   2960.1 |   3815.7 |  10752.8 |
| Q08     | exasol    |    153.4 |      5 |       813.7 |     733.5 |    242.1 |    313   |    928.6 |
| Q08     | starrocks |   2397.8 |      5 |      4246.1 |    4233.5 |   1332   |   2266.9 |   5950.5 |
| Q09     | exasol    |   2297.6 |      5 |     11026.6 |    9852.3 |   2643.6 |   5299   |  11625.1 |
| Q09     | starrocks |   5841.2 |      5 |     24735.3 |   20114.9 |   8385.2 |  10332.9 |  28188.4 |
| Q10     | exasol    |    743.2 |      5 |      3129.3 |    3200.6 |    254.3 |   2929.1 |   3547.6 |
| Q10     | starrocks |   2709.4 |      5 |      5313.8 |    6331.2 |   2561.2 |   4128.6 |  10559.4 |
| Q11     | exasol    |    139.3 |      5 |       597.4 |     703.7 |    301.8 |    329.3 |   1028.5 |
| Q11     | starrocks |    384.6 |      5 |       836.2 |     969   |    496.8 |    549.3 |   1831.1 |
| Q12     | exasol    |    173   |      5 |       829.1 |     944.7 |    425.7 |    517.9 |   1650.1 |
| Q12     | starrocks |   1700.8 |      5 |      2437.8 |    3259.2 |   1827.9 |   2144.9 |   6504.4 |
| Q13     | exasol    |   1693.6 |      5 |      8203.7 |   10276.7 |   7355   |   3284.8 |  22733.3 |
| Q13     | starrocks |   3630.8 |      5 |     15953.1 |   17863.7 |   7319.2 |   7847.9 |  26569.5 |
| Q14     | exasol    |    160.4 |      5 |      1037.6 |     996.6 |    188.6 |    669.9 |   1128.9 |
| Q14     | starrocks |   1318.1 |      5 |      2424.4 |    3222.4 |   1904.9 |   1702.4 |   6455.8 |
| Q15     | exasol    |    353   |      5 |      1581.5 |    1565.2 |    571.6 |    676.4 |   2202.9 |
| Q15     | starrocks |   1328.4 |      5 |      2323   |    2195.5 |    807.1 |   1420.4 |   3341.6 |
| Q16     | exasol    |    619.3 |      5 |      2460.5 |    2513.6 |    970.5 |   1062.5 |   3602.3 |
| Q16     | starrocks |    843.6 |      5 |      1494.8 |    1660.1 |    786.4 |    850.8 |   2845.4 |
| Q17     | exasol    |     24.7 |      5 |       202.5 |     205.1 |    146.5 |     78.6 |    442.1 |
| Q17     | starrocks |   1327.1 |      5 |      1620.8 |    2234.8 |    955.3 |   1495.4 |   3586.5 |
| Q18     | exasol    |   1095.1 |      5 |      4468.8 |    4602   |    443.4 |   4201.3 |   5343.6 |
| Q18     | starrocks |   4457.3 |      5 |     12834.9 |   13563.2 |   2077.6 |  12140.4 |  17225.1 |
| Q19     | exasol    |     49.7 |      5 |       348.3 |     283.4 |    124.1 |    107.8 |    408.4 |
| Q19     | starrocks |   1685.8 |      5 |      3481.5 |    3496.9 |   1384.3 |   2083.1 |   5227.3 |
| Q20     | exasol    |    351.2 |      5 |      1722.9 |    1615.7 |    459.7 |    814.3 |   1964.5 |
| Q20     | starrocks |   1538   |      5 |      4402.7 |    4843   |   1362.3 |   3639.9 |   7089.4 |
| Q21     | exasol    |    950.6 |      5 |      4580.1 |    4250.1 |   2780.7 |   1485.4 |   8032.4 |
| Q21     | starrocks |   8980.9 |      5 |     48064.6 |   66975.4 |  36762.7 |  35601.8 | 113098   |
| Q22     | exasol    |    207.8 |      5 |       950   |    1261.8 |    735.8 |    806.2 |   2559.9 |
| Q22     | starrocks |    687.3 |      5 |      2652.6 |    3174.1 |   2090.9 |   1621.1 |   6761.3 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1482.6ms
- Average: 2640.2ms
- Range: 78.6ms - 22733.3ms

**#2. Starrocks**
- Median: 4005.6ms
- Average: 10395.2ms
- Range: 549.3ms - 113097.5ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 2992.5 | 1050.0 | 107.8 | 22733.3 |
| 1 | 22 | 2354.2 | 2033.2 | 202.5 | 8203.7 |
| 2 | 22 | 2596.5 | 1425.8 | 202.5 | 11625.1 |
| 3 | 22 | 3023.8 | 1892.1 | 82.8 | 11495.0 |
| 4 | 22 | 2234.1 | 1255.0 | 78.6 | 8263.2 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1050.0ms
- **Worst stream median:** 2033.2ms
- **Performance variance:** 93.6% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 11758.6 | 3598.1 | 549.3 | 100106.2 |
| 1 | 22 | 6309.4 | 3771.9 | 836.2 | 33628.4 |
| 2 | 22 | 11305.8 | 4022.2 | 1044.0 | 99495.1 |
| 3 | 22 | 11517.0 | 5190.8 | 778.9 | 48064.6 |
| 4 | 22 | 11085.3 | 3660.3 | 849.7 | 113097.5 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 3598.1ms
- **Worst stream median:** 5190.8ms
- **Performance variance:** 44.3% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

**Query Distribution Method:**
- Query distribution was **randomized** (seed: 42) for realistic concurrent user simulation


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 30
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