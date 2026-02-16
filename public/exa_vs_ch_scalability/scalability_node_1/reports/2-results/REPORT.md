# Node Scaling - 1 Node (32GB) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-19 16:08:07


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **clickhouse**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **1520.7ms** median runtime
- **clickhouse** was **8.2×** slower- Tested **220** total query executions across 22 different query types
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

| Query Type         |   clickhouse |   exasol | Winner   |
|--------------------|--------------|----------|----------|
| Aggregation        |       8844.4 |   1053.7 | exasol   |
| Join-Heavy         |      11510.3 |   2318.7 | exasol   |
| Complex Analytical |      14691.6 |   3386.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        7676.2 |         20651.9 |    2.69 |      0.37 | False    |
| Q02     | exasol            | clickhouse          |         342.8 |         11944.5 |   34.84 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        3386.3 |         13385.9 |    3.95 |      0.25 | False    |
| Q04     | exasol            | clickhouse          |         638   |         23112   |   36.23 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2413.6 |         12482.1 |    5.17 |      0.19 | False    |
| Q06     | exasol            | clickhouse          |         390.4 |          3389.3 |    8.68 |      0.12 | False    |
| Q07     | exasol            | clickhouse          |        3532.8 |         10736.3 |    3.04 |      0.33 | False    |
| Q08     | exasol            | clickhouse          |         844.4 |         11338.7 |   13.43 |      0.07 | False    |
| Q09     | exasol            | clickhouse          |       12093.8 |         12932.6 |    1.07 |      0.94 | False    |
| Q10     | exasol            | clickhouse          |        3327.4 |         16809.9 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse          |         738.8 |         10898.1 |   14.75 |      0.07 | False    |
| Q12     | exasol            | clickhouse          |        1050.9 |          8844.4 |    8.42 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |        7831.7 |         18824.6 |    2.4  |      0.42 | False    |
| Q14     | exasol            | clickhouse          |        1013.9 |          4107.9 |    4.05 |      0.25 | False    |
| Q15     | exasol            | clickhouse          |        1505.9 |          4068.1 |    2.7  |      0.37 | False    |
| Q16     | exasol            | clickhouse          |        2698.3 |          8651.8 |    3.21 |      0.31 | False    |
| Q17     | exasol            | clickhouse          |         112.6 |         12737.2 |  113.12 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        4730.9 |         15750   |    3.33 |      0.3  | False    |
| Q19     | exasol            | clickhouse          |         394.8 |         42695.6 |  108.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        1683.7 |         13505.7 |    8.02 |      0.12 | False    |
| Q21     | exasol            | clickhouse          |        5745.1 |         11051.5 |    1.92 |      0.52 | False    |
| Q22     | exasol            | clickhouse          |         898.3 |         10009.9 |   11.14 |      0.09 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   5625.6 |      5 |     20651.9 |   20410.7 |   4177   |  16781.9 |  26997.8 |
| Q01     | exasol     |   1893.6 |      5 |      7676.2 |    6922.5 |   3112.7 |   3105.4 |  10689   |
| Q02     | clickhouse |   2326   |      5 |     11944.5 |   12361.8 |   2300.3 |  10186.6 |  16140.6 |
| Q02     | exasol     |     81.8 |      5 |       342.8 |     644.5 |    744.3 |    234.8 |   1969.1 |
| Q03     | clickhouse |   2821.2 |      5 |     13385.9 |   12357.5 |   4452.9 |   5305.5 |  17257.5 |
| Q03     | exasol     |    707.7 |      5 |      3386.3 |    2821.3 |   1699.9 |    686.2 |   4433.9 |
| Q04     | clickhouse |   4699   |      5 |     23112   |   23120.1 |   2980.7 |  19978.7 |  27705.5 |
| Q04     | exasol     |    131.7 |      5 |       638   |     617.5 |    216.4 |    260.5 |    807   |
| Q05     | clickhouse |   2433.8 |      5 |     12482.1 |   13348.7 |   1588.6 |  11913.2 |  15695.9 |
| Q05     | exasol     |    558.2 |      5 |      2413.6 |    2482   |    240.8 |   2291.3 |   2896.8 |
| Q06     | clickhouse |    345.4 |      5 |      3389.3 |    3481.6 |    999.8 |   2227.8 |   4497.2 |
| Q06     | exasol     |     87.1 |      5 |       390.4 |     378.4 |    303.4 |     85.4 |    862.2 |
| Q07     | clickhouse |   1814.5 |      5 |     10736.3 |   11918.6 |   2484.5 |   9206.8 |  14691.6 |
| Q07     | exasol     |    694.7 |      5 |      3532.8 |    4900.4 |   3362.9 |   2832.3 |  10870.4 |
| Q08     | clickhouse |   1584.4 |      5 |     11338.7 |   10436.5 |   2445.9 |   6457.8 |  12940.6 |
| Q08     | exasol     |    165.5 |      5 |       844.4 |    1148   |    993.9 |    336.9 |   2882.6 |
| Q09     | clickhouse |   1903   |      5 |     12932.6 |   13068   |   3204.9 |  10489.4 |  18386.8 |
| Q09     | exasol     |   2510.2 |      5 |     12093.8 |   13594.1 |   3325.1 |  11658.7 |  19497.1 |
| Q10     | clickhouse |   3088.5 |      5 |     16809.9 |   17621.9 |   2743.4 |  14845.1 |  22079.6 |
| Q10     | exasol     |    787.7 |      5 |      3327.4 |    3355.2 |    447.1 |   2860.9 |   3995.2 |
| Q11     | clickhouse |   1397.3 |      5 |     10898.1 |   10109.6 |   2283.7 |   6065.8 |  11645.1 |
| Q11     | exasol     |    149.9 |      5 |       738.8 |     693.8 |    131.1 |    554.7 |    855.3 |
| Q12     | clickhouse |   1903.6 |      5 |      8844.4 |   11000.5 |   3802.2 |   8031.1 |  16325.3 |
| Q12     | exasol     |    178.7 |      5 |      1050.9 |    1170.5 |    415.7 |    732.5 |   1831   |
| Q13     | clickhouse |   4541   |      5 |     18824.6 |   20782   |   4074.1 |  17347.2 |  26533.8 |
| Q13     | exasol     |   1827.8 |      5 |      7831.7 |    6887.3 |   1955.9 |   4101.1 |   8558.8 |
| Q14     | clickhouse |    349.2 |      5 |      4107.9 |    3569.7 |   1167.1 |   2171   |   4760.2 |
| Q14     | exasol     |    175.4 |      5 |      1013.9 |     957.3 |    162.5 |    673.9 |   1069.1 |
| Q15     | clickhouse |    361.4 |      5 |      4068.1 |    4078.3 |    489   |   3317   |   4615.2 |
| Q15     | exasol     |    388   |      5 |      1505.9 |    2140.3 |   1651.2 |   1186.4 |   5084.4 |
| Q16     | clickhouse |   1175   |      5 |      8651.8 |    9040.3 |   1989.2 |   7584   |  12474.2 |
| Q16     | exasol     |    699   |      5 |      2698.3 |    3292.2 |   1766   |   1379.7 |   6112.5 |
| Q17     | clickhouse |   2113.3 |      5 |     12737.2 |   13181.2 |   1060.2 |  12533.6 |  15049.9 |
| Q17     | exasol     |     28.2 |      5 |       112.6 |     132.2 |     45.3 |     92.3 |    197.2 |
| Q18     | clickhouse |   3534.3 |      5 |     15750   |   16495.4 |   1473.7 |  15654.8 |  19101.6 |
| Q18     | exasol     |   1125.4 |      5 |      4730.9 |    4657.1 |    380.5 |   4154.3 |   5147   |
| Q19     | clickhouse |  11806.1 |      5 |     42695.6 |   36737.5 |  14097.5 |  11699.3 |  45535.4 |
| Q19     | exasol     |     53   |      5 |       394.8 |     371.2 |     74.3 |    290.5 |    465.9 |
| Q20     | clickhouse |   2758.1 |      5 |     13505.7 |   13014.1 |   2453.6 |   9168.7 |  15896.9 |
| Q20     | exasol     |    429.3 |      5 |      1683.7 |    1644.5 |    472.8 |    912.6 |   2107.5 |
| Q21     | clickhouse |   1882.4 |      5 |     11051.5 |   11286.4 |   2076.2 |   9066   |  14678.4 |
| Q21     | exasol     |   1063.3 |      5 |      5745.1 |    5235.4 |   2516.1 |   1014.6 |   7598.5 |
| Q22     | clickhouse |    966.7 |      5 |     10009.9 |    8496.3 |   4579.4 |    966.2 |  12793.2 |
| Q22     | exasol     |    215.2 |      5 |       898.3 |    1308.2 |    976.9 |    828.7 |   3054.6 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1520.7ms
- Average: 2970.6ms
- Range: 85.4ms - 19497.1ms

**#2. Clickhouse**
- Median: 12507.9ms
- Average: 13450.8ms
- Range: 966.2ms - 45535.4ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 13649.8 | 12004.1 | 4497.2 | 45535.4 |
| 1 | 22 | 14327.0 | 11413.2 | 966.2 | 42695.6 |
| 2 | 22 | 13680.1 | 12740.5 | 2171.0 | 42948.1 |
| 3 | 22 | 12551.8 | 12503.9 | 3389.3 | 26533.8 |
| 4 | 22 | 13045.1 | 12292.9 | 2227.8 | 40808.9 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 11413.2ms
- **Worst stream median:** 12740.5ms
- **Performance variance:** 11.6% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **consistent** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 3180.1 | 1375.8 | 112.6 | 19497.1 |
| 1 | 22 | 2643.3 | 1757.3 | 290.5 | 10689.0 |
| 2 | 22 | 3002.0 | 1227.8 | 197.2 | 11948.0 |
| 3 | 22 | 3271.1 | 1741.3 | 85.4 | 12773.0 |
| 4 | 22 | 2756.7 | 1934.5 | 92.3 | 8558.8 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1227.8ms
- **Worst stream median:** 1934.5ms
- **Performance variance:** 57.6% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams

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