# Minimum Viable Resources - 16GB - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-19 15:08:58


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **clickhouse**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **3035.7ms** median runtime
- **clickhouse** was **4.9×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |      10549.9 |   2738.6 | exasol   |
| Join-Heavy         |      12914.4 |   2592.4 | exasol   |
| Complex Analytical |      18841.8 |   5300   | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |       15961.9 |         51243.4 |    3.21 |      0.31 | False    |
| Q02     | exasol            | clickhouse          |         530.3 |         18452.5 |   34.8  |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        2785.9 |         14462.7 |    5.19 |      0.19 | False    |
| Q04     | exasol            | clickhouse          |        1899   |         23284.1 |   12.26 |      0.08 | False    |
| Q05     | exasol            | clickhouse          |        4141.5 |         13128.4 |    3.17 |      0.32 | False    |
| Q06     | exasol            | clickhouse          |        1001.4 |          4839.6 |    4.83 |      0.21 | False    |
| Q07     | exasol            | clickhouse          |        7514.9 |         11284.1 |    1.5  |      0.67 | False    |
| Q08     | exasol            | clickhouse          |        1182.4 |          8505.8 |    7.19 |      0.14 | False    |
| Q09     | exasol            | clickhouse          |       16913.4 |         12024.4 |    0.71 |      1.41 | True     |
| Q10     | exasol            | clickhouse          |        8590.5 |         16824.2 |    1.96 |      0.51 | False    |
| Q11     | exasol            | clickhouse          |        1043.9 |         13737.5 |   13.16 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |        2738.6 |         10549.9 |    3.85 |      0.26 | False    |
| Q13     | exasol            | clickhouse          |       14503.1 |         53894.5 |    3.72 |      0.27 | False    |
| Q14     | exasol            | clickhouse          |        2945.2 |          4736.4 |    1.61 |      0.62 | False    |
| Q15     | exasol            | clickhouse          |        2968   |          5745.8 |    1.94 |      0.52 | False    |
| Q16     | exasol            | clickhouse          |        5522.3 |         17329.2 |    3.14 |      0.32 | False    |
| Q17     | exasol            | clickhouse          |         343.1 |         27526.2 |   80.23 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        9178   |         18195   |    1.98 |      0.5  | False    |
| Q19     | exasol            | clickhouse          |         978.7 |        113511   |  115.98 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        5317.5 |         35412.8 |    6.66 |      0.15 | False    |
| Q21     | exasol            | clickhouse          |        7895.2 |         10112.2 |    1.28 |      0.78 | False    |
| Q22     | exasol            | clickhouse          |        1898.2 |         12295.4 |    6.48 |      0.15 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |  11976.7 |      5 |     51243.4 |   49097.9 |   9514.1 |  32750.1 |  56868.3 |
| Q01     | exasol     |   3754.5 |      5 |     15961.9 |   16693.3 |   6794   |   7452.6 |  24234.1 |
| Q02     | clickhouse |   3400.1 |      5 |     18452.5 |   19233.9 |   2003.3 |  17117.8 |  21781.7 |
| Q02     | exasol     |     98.5 |      5 |       530.3 |     474.1 |    226.1 |    109.4 |    720.4 |
| Q03     | clickhouse |   2734.6 |      5 |     14462.7 |   13710.3 |   3851.6 |   8833.1 |  18344.6 |
| Q03     | exasol     |   1293.2 |      5 |      2785.9 |    7400.9 |   7844.1 |   1265.8 |  17887.6 |
| Q04     | clickhouse |   4546.9 |      5 |     23284.1 |   23406.1 |   3071.9 |  18841.8 |  27003.8 |
| Q04     | exasol     |    246.5 |      5 |      1899   |    2177.5 |   1172.6 |    866.5 |   3416   |
| Q05     | clickhouse |   2434.3 |      5 |     13128.4 |   13173.1 |   1024.6 |  11601.8 |  14259.9 |
| Q05     | exasol     |   1021.8 |      5 |      4141.5 |    5514.8 |   4222.6 |    968.8 |  11723.2 |
| Q06     | clickhouse |    930.6 |      5 |      4839.6 |    4712.5 |   1387.5 |   2812.5 |   6687.8 |
| Q06     | exasol     |    159.1 |      5 |      1001.4 |     838.7 |    599.2 |    158.9 |   1586.3 |
| Q07     | clickhouse |   1904.6 |      5 |     11284.1 |   11977.6 |   2589.4 |   9075.6 |  15999.5 |
| Q07     | exasol     |   1298.3 |      5 |      7514.9 |    6932.8 |   2057.2 |   4411.7 |   9489.7 |
| Q08     | clickhouse |   1456.9 |      5 |      8505.8 |    8452.3 |   2513.5 |   4514.1 |  11272.7 |
| Q08     | exasol     |    303.3 |      5 |      1182.4 |    1395.2 |    964.5 |    339.8 |   2965.5 |
| Q09     | clickhouse |   1502.9 |      5 |     12024.4 |   11720.3 |   2020.6 |   8994.5 |  14151   |
| Q09     | exasol     |   4677.4 |      5 |     16913.4 |   16092   |   4495   |   8893.3 |  21005   |
| Q10     | clickhouse |   3727.6 |      5 |     16824.2 |   17216.9 |   1976.5 |  15219.1 |  20280.6 |
| Q10     | exasol     |   1346.1 |      5 |      8590.5 |    9472.9 |   3208.7 |   5334.1 |  12992.7 |
| Q11     | clickhouse |   2679.2 |      5 |     13737.5 |   16889.2 |   6819.5 |  10875.3 |  27802.1 |
| Q11     | exasol     |    228.8 |      5 |      1043.9 |    1123   |    577.4 |    250.5 |   1677.8 |
| Q12     | clickhouse |   1996.6 |      5 |     10549.9 |   10954.6 |   2046   |   8816.9 |  13291.9 |
| Q12     | exasol     |    334.5 |      5 |      2738.6 |    2596.8 |    638.9 |   1899.5 |   3415   |
| Q13     | clickhouse |  11121.4 |      5 |     53894.5 |   53362.8 |   3428.1 |  49610.1 |  57795.3 |
| Q13     | exasol     |   3504.4 |      5 |     14503.1 |   28637.2 |  36145   |   7780.4 |  93092.8 |
| Q14     | clickhouse |    701.2 |      5 |      4736.4 |    4376   |   1142.4 |   2992.7 |   5663   |
| Q14     | exasol     |    319.4 |      5 |      2945.2 |    2415.1 |    945.5 |   1079   |   3191.1 |
| Q15     | clickhouse |    613.8 |      5 |      5745.8 |    4811.3 |   1527.5 |   2826   |   6078.1 |
| Q15     | exasol     |    656.2 |      5 |      2968   |    2512.2 |   1219.8 |    658.1 |   3802.8 |
| Q16     | clickhouse |   3054.6 |      5 |     17329.2 |   16832.8 |   2329.3 |  13777.1 |  19643.6 |
| Q16     | exasol     |   1115.1 |      5 |      5522.3 |    4436.6 |   2218.3 |   1074.2 |   6531   |
| Q17     | clickhouse |   5928   |      5 |     27526.2 |   28021.7 |   3833   |  24189   |  34362   |
| Q17     | exasol     |     37.6 |      5 |       343.1 |     348.5 |    114.1 |    194   |    461.9 |
| Q18     | clickhouse |   3748   |      5 |     18195   |   18693.2 |   3454.1 |  15070.8 |  23907.7 |
| Q18     | exasol     |   2018.2 |      5 |      9178   |    8988.2 |   3898   |   4461.1 |  14171.9 |
| Q19     | clickhouse |  24598   |      5 |    113511   |   99030.5 |  39204.3 |  29294.4 | 122750   |
| Q19     | exasol     |     96.4 |      5 |       978.7 |     905.5 |    522.9 |    174   |   1544.5 |
| Q20     | clickhouse |   6517.9 |      5 |     35412.8 |   34063.6 |   3523.4 |  27904.1 |  36447.9 |
| Q20     | exasol     |    655.1 |      5 |      5317.5 |    4740.6 |   1857.1 |   2102.8 |   6702.7 |
| Q21     | clickhouse |   1880   |      5 |     10112.2 |    9834.9 |   1031.1 |   8393.9 |  11173.6 |
| Q21     | exasol     |   2006   |      5 |      7895.2 |    8015.1 |   4974.3 |   1911.2 |  14424.4 |
| Q22     | clickhouse |   1943.9 |      5 |     12295.4 |   11746.2 |   4101.3 |   6778.2 |  17741.9 |
| Q22     | exasol     |    416   |      5 |      1898.2 |    2136.6 |    469.9 |   1726   |   2886.9 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 3035.7ms
- Average: 6084.0ms
- Range: 109.4ms - 93092.8ms

**#2. Clickhouse**
- Median: 14766.8ms
- Average: 21878.1ms
- Range: 2812.5ms - 122749.8ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 22404.9 | 14685.0 | 2812.5 | 113511.3 |
| 1 | 22 | 23648.0 | 16880.2 | 3382.2 | 112039.3 |
| 2 | 22 | 22692.8 | 16726.3 | 2992.7 | 122749.8 |
| 3 | 22 | 18940.6 | 12953.2 | 4839.6 | 57795.3 |
| 4 | 22 | 21704.0 | 13016.5 | 4335.0 | 117557.7 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 12953.2ms
- **Worst stream median:** 16880.2ms
- **Performance variance:** 30.3% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 7240.0 | 1616.0 | 109.4 | 93092.8 |
| 1 | 22 | 4945.9 | 3041.0 | 720.4 | 22318.6 |
| 2 | 22 | 5736.1 | 2744.6 | 343.1 | 17887.6 |
| 3 | 22 | 6677.9 | 4426.9 | 194.0 | 21005.0 |
| 4 | 22 | 5819.9 | 3155.3 | 287.3 | 24234.1 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1616.0ms
- **Worst stream median:** 4426.9ms
- **Performance variance:** 174.0% difference between fastest and slowest streams
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