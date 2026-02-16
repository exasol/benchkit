# Exasol vs StarRocks: TPC-H SF10 (Single-Node, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:05:26


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
- **exasol** was the fastest overall with **1092.8ms** median runtime
- **starrocks** was **2.8×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |    793   |      2410.4 | exasol   |
| Join-Heavy         |   1219   |      3458   | exasol   |
| Complex Analytical |   2193.1 |      4275.6 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6470.2 |         47219.6 |    7.3  |      0.14 | False    |
| Q02     | exasol            | starrocks           |         245.5 |           722.6 |    2.94 |      0.34 | False    |
| Q03     | exasol            | starrocks           |        1004.6 |          4275.6 |    4.26 |      0.23 | False    |
| Q04     | exasol            | starrocks           |         558.3 |          2206.4 |    3.95 |      0.25 | False    |
| Q05     | exasol            | starrocks           |        1790.1 |          3694.2 |    2.06 |      0.48 | False    |
| Q06     | exasol            | starrocks           |         325.1 |          1181.8 |    3.64 |      0.28 | False    |
| Q07     | exasol            | starrocks           |        2785.9 |          7757.5 |    2.78 |      0.36 | False    |
| Q08     | exasol            | starrocks           |         582.9 |          3431.5 |    5.89 |      0.17 | False    |
| Q09     | exasol            | starrocks           |        5088.6 |          7629.6 |    1.5  |      0.67 | False    |
| Q10     | exasol            | starrocks           |        2554.9 |          3907.8 |    1.53 |      0.65 | False    |
| Q11     | exasol            | starrocks           |         513.1 |           979.5 |    1.91 |      0.52 | False    |
| Q12     | exasol            | starrocks           |         909.3 |          4476.3 |    4.92 |      0.2  | False    |
| Q13     | exasol            | starrocks           |        5526.4 |          7942.6 |    1.44 |      0.7  | False    |
| Q14     | exasol            | starrocks           |         951   |          1903.8 |    2    |      0.5  | False    |
| Q15     | exasol            | starrocks           |         532.3 |          2217.3 |    4.17 |      0.24 | False    |
| Q16     | exasol            | starrocks           |        2881.9 |          1326.2 |    0.46 |      2.17 | True     |
| Q17     | exasol            | starrocks           |         119.3 |          2164   |   18.14 |      0.06 | False    |
| Q18     | exasol            | starrocks           |        3270.3 |          8650.4 |    2.65 |      0.38 | False    |
| Q19     | exasol            | starrocks           |         315   |          2238.8 |    7.11 |      0.14 | False    |
| Q20     | exasol            | starrocks           |        1232.2 |          1670.9 |    1.36 |      0.74 | False    |
| Q21     | exasol            | starrocks           |        2888.7 |         24165.2 |    8.37 |      0.12 | False    |
| Q22     | exasol            | starrocks           |         774.1 |           918.3 |    1.19 |      0.84 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1267.5 |      5 |      6470.2 |    6287.5 |   1531.8 |   3887.8 |   7695.8 |
| Q01     | starrocks |   5946.3 |      5 |     47219.6 |   44617.6 |  29946.4 |   3963.3 |  85941.4 |
| Q02     | exasol    |    101.1 |      5 |       245.5 |     224.2 |    111.3 |     52.1 |    335.7 |
| Q02     | starrocks |    741.5 |      5 |       722.6 |     919   |    373.5 |    659   |   1541.6 |
| Q03     | exasol    |    482   |      5 |      1004.6 |    1379.7 |   1061.7 |    453.2 |   2791.9 |
| Q03     | starrocks |   2113.1 |      5 |      4275.6 |    4446.2 |    801   |   3588.6 |   5530.5 |
| Q04     | exasol    |     94.8 |      5 |       558.3 |     570.3 |    229.3 |    274.4 |    908   |
| Q04     | starrocks |    915.8 |      5 |      2206.4 |    2132.6 |    895.1 |    954.1 |   3214.5 |
| Q05     | exasol    |    423.3 |      5 |      1790.1 |    1777.6 |   1031   |    349.1 |   3179.8 |
| Q05     | starrocks |   1792.6 |      5 |      3694.2 |    3764   |    609.3 |   3006.9 |   4514.7 |
| Q06     | exasol    |    237.5 |      5 |       325.1 |     277.3 |    144.2 |     61.9 |    415   |
| Q06     | starrocks |    571   |      5 |      1181.8 |    1672.3 |    801.2 |    924.1 |   2654.6 |
| Q07     | exasol    |    451.5 |      5 |      2785.9 |    2684.9 |    559   |   1797.7 |   3211.9 |
| Q07     | starrocks |   2326.6 |      5 |      7757.5 |    7831.4 |   1434.5 |   5669.6 |   9562.7 |
| Q08     | exasol    |    119.9 |      5 |       582.9 |     708   |    491   |    125   |   1351.9 |
| Q08     | starrocks |   1843.9 |      5 |      3431.5 |    3052.4 |   1182.6 |   1671.6 |   4614.7 |
| Q09     | exasol    |   1287.8 |      5 |      5088.6 |    4315.9 |   1742.6 |   1248.1 |   5359.3 |
| Q09     | starrocks |   3375.5 |      5 |      7629.6 |    8104.1 |   2650   |   4477.8 |  10783.1 |
| Q10     | exasol    |    516.4 |      5 |      2554.9 |    2553   |    567.4 |   1907.8 |   3312.5 |
| Q10     | starrocks |   1949.2 |      5 |      3907.8 |    4163.3 |    762.3 |   3456.3 |   5431.9 |
| Q11     | exasol    |     93.6 |      5 |       513.1 |     564.9 |    441.5 |     93.3 |   1281.2 |
| Q11     | starrocks |    355.7 |      5 |       979.5 |    1226.9 |    535.8 |    874.9 |   2170.7 |
| Q12     | exasol    |    125.4 |      5 |       909.3 |     937.2 |    410.7 |    408.1 |   1465.8 |
| Q12     | starrocks |   1150.5 |      5 |      4476.3 |    4164.3 |   1729.4 |   2250   |   6124.4 |
| Q13     | exasol    |   1228.1 |      5 |      5526.4 |   11580.9 |  14791.8 |   2494.9 |  37904.7 |
| Q13     | starrocks |   2231.8 |      5 |      7942.6 |    8835.9 |   3148.1 |   5503.4 |  12604.6 |
| Q14     | exasol    |    119.3 |      5 |       951   |     956.1 |    237.6 |    657   |   1205.1 |
| Q14     | starrocks |    871.9 |      5 |      1903.8 |    1855.9 |   1016.8 |    620.3 |   3100.7 |
| Q15     | exasol    |    135   |      5 |       532.3 |     740.2 |    560.3 |    133.6 |   1611.3 |
| Q15     | starrocks |    567.3 |      5 |      2217.3 |    2446.5 |   1039.4 |   1370.5 |   3966.3 |
| Q16     | exasol    |    495.3 |      5 |      2881.9 |    2495.1 |   1294.6 |    477   |   3789.3 |
| Q16     | starrocks |    725.6 |      5 |      1326.2 |    1491.3 |    839.3 |    391.7 |   2709.3 |
| Q17     | exasol    |     23.5 |      5 |       119.3 |     165.5 |     70.6 |    116.5 |    275.6 |
| Q17     | starrocks |    881.1 |      5 |      2164   |    2251.2 |    715.8 |   1366.3 |   3016.2 |
| Q18     | exasol    |    696.4 |      5 |      3270.3 |    2866.6 |   1063   |   1016.8 |   3579.2 |
| Q18     | starrocks |   3352.6 |      5 |      8650.4 |    8679.8 |   2918.7 |   4857.4 |  12624.1 |
| Q19     | exasol    |     38.6 |      5 |       315   |     391.4 |    263.3 |     57.9 |    699.4 |
| Q19     | starrocks |   1167.1 |      5 |      2238.8 |    2124.3 |    396.3 |   1486.8 |   2465   |
| Q20     | exasol    |    225.6 |      5 |      1232.2 |    1236.8 |    578.4 |    694.6 |   2157.5 |
| Q20     | starrocks |    972.4 |      5 |      1670.9 |    1919.7 |    726.2 |   1083.7 |   2940.8 |
| Q21     | exasol    |    747   |      5 |      2888.7 |    2596.2 |   1436.2 |    682.6 |   4424.2 |
| Q21     | starrocks |   3887.1 |      5 |     24165.2 |   25100.7 |  10589.7 |   9949.4 |  38439.5 |
| Q22     | exasol    |    148.1 |      5 |       774.1 |     882.3 |    261.4 |    648.9 |   1189.9 |
| Q22     | starrocks |    616.1 |      5 |       918.3 |    1596.5 |   1423.7 |    467   |   3770.3 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1092.8ms
- Average: 2099.6ms
- Range: 52.1ms - 37904.7ms

**#2. Starrocks**
- Median: 3011.6ms
- Average: 6472.5ms
- Range: 391.7ms - 85941.4ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 2518.7 | 579.8 | 52.1 | 37904.7 |
| 1 | 22 | 1690.6 | 746.2 | 274.4 | 7492.9 |
| 2 | 22 | 2038.5 | 1182.2 | 116.5 | 6470.2 |
| 3 | 22 | 2213.6 | 1763.9 | 119.3 | 5526.4 |
| 4 | 22 | 2036.8 | 1481.6 | 118.4 | 7695.8 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 579.8ms
- **Worst stream median:** 1763.9ms
- **Performance variance:** 204.2% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 6046.7 | 3677.9 | 994.8 | 30742.7 |
| 1 | 22 | 5384.7 | 2383.6 | 918.3 | 53340.6 |
| 2 | 22 | 7281.0 | 3031.9 | 391.7 | 85941.4 |
| 3 | 22 | 6836.2 | 3641.4 | 722.6 | 32623.3 |
| 4 | 22 | 6814.2 | 2537.6 | 874.9 | 47219.6 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 2383.6ms
- **Worst stream median:** 3677.9ms
- **Performance variance:** 54.3% difference between fastest and slowest streams
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