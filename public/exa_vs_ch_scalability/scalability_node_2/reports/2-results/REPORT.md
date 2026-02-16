# Node Scaling - 2 Nodes (64GB) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-19 17:33:53


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
- **Deployment:** 2-node cluster

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65
- **Deployment:** 2-node cluster


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **1206.1ms** median runtime
- **clickhouse** was **6.9×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |       7461.3 |    921.6 | exasol   |
| Join-Heavy         |       7844.6 |   1542.3 | exasol   |
| Complex Analytical |       9444   |   2037.9 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3136.8 |          7461.3 |    2.38 |      0.42 | False    |
| Q02     | exasol            | clickhouse          |         355.2 |         29354.3 |   82.64 |      0.01 | False    |
| Q03     | exasol            | clickhouse          |        1802.9 |          9826   |    5.45 |      0.18 | False    |
| Q04     | exasol            | clickhouse          |         817.5 |         25119.7 |   30.73 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2759.1 |          9974.2 |    3.62 |      0.28 | False    |
| Q06     | exasol            | clickhouse          |         212   |          1695.6 |    8    |      0.13 | False    |
| Q07     | exasol            | clickhouse          |        4027.1 |          8080.7 |    2.01 |      0.5  | False    |
| Q08     | exasol            | clickhouse          |        1324.6 |          8061.7 |    6.09 |      0.16 | False    |
| Q09     | exasol            | clickhouse          |       10652.3 |          7741   |    0.73 |      1.38 | True     |
| Q10     | exasol            | clickhouse          |        2754.4 |          9217.2 |    3.35 |      0.3  | False    |
| Q11     | exasol            | clickhouse          |        1008.7 |          4366.4 |    4.33 |      0.23 | False    |
| Q12     | exasol            | clickhouse          |         735.7 |          9850.2 |   13.39 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        4494   |         15324   |    3.41 |      0.29 | False    |
| Q14     | exasol            | clickhouse          |        1004.5 |          3898.6 |    3.88 |      0.26 | False    |
| Q15     | exasol            | clickhouse          |        1211.2 |          1764.8 |    1.46 |      0.69 | False    |
| Q16     | exasol            | clickhouse          |        1811.5 |          6711.3 |    3.7  |      0.27 | False    |
| Q17     | exasol            | clickhouse          |         201.7 |          8159.3 |   40.45 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |        2892.8 |          9270.3 |    3.2  |      0.31 | False    |
| Q19     | exasol            | clickhouse          |         379.8 |         21943.4 |   57.78 |      0.02 | False    |
| Q20     | exasol            | clickhouse          |        1255.5 |         10827.8 |    8.62 |      0.12 | False    |
| Q21     | exasol            | clickhouse          |        3582.8 |          6777.3 |    1.89 |      0.53 | False    |
| Q22     | exasol            | clickhouse          |         641.5 |          3024   |    4.71 |      0.21 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2914   |      5 |      7461.3 |    7578   |   1708.3 |   5032.9 |   9182.3 |
| Q01     | exasol     |    954.6 |      5 |      3136.8 |    2752.2 |   1356.2 |    959.1 |   4529.6 |
| Q02     | clickhouse |   9555.9 |      5 |     29354.3 |   29222.4 |    919.3 |  27769   |  30280   |
| Q02     | exasol     |     86.8 |      5 |       355.2 |     425.7 |    183.2 |    286.9 |    746.7 |
| Q03     | clickhouse |   3680.7 |      5 |      9826   |   10568.3 |   4335.9 |   4180.5 |  14971.8 |
| Q03     | exasol     |    668.7 |      5 |      1802.9 |    2200.9 |   1442.9 |    672.5 |   3999.1 |
| Q04     | clickhouse |   8117.4 |      5 |     25119.7 |   24507.1 |   3778.6 |  18664   |  29103.8 |
| Q04     | exasol     |    189.8 |      5 |       817.5 |     928.1 |    297.1 |    643.4 |   1403.1 |
| Q05     | clickhouse |   3201.8 |      5 |      9974.2 |   11124   |   1842.8 |   9601.7 |  13625.1 |
| Q05     | exasol     |    665.8 |      5 |      2759.1 |    2995   |    411.1 |   2619.3 |   3448.5 |
| Q06     | clickhouse |    200.5 |      5 |      1695.6 |    1437.2 |    771.5 |    519.3 |   2257.3 |
| Q06     | exasol     |     52.3 |      5 |       212   |     224.6 |    136.2 |     52.8 |    417.1 |
| Q07     | clickhouse |   2312.6 |      5 |      8080.7 |    8301.9 |   1039.9 |   7120.8 |   9766.6 |
| Q07     | exasol     |    788.9 |      5 |      4027.1 |    3923.9 |    318.1 |   3415.7 |   4188.8 |
| Q08     | clickhouse |   2020.6 |      5 |      8061.7 |    8208.8 |   1750.8 |   5858.3 |   9977.8 |
| Q08     | exasol     |    279.5 |      5 |      1324.6 |    1205.3 |    513.3 |    421.5 |   1727.7 |
| Q09     | clickhouse |   1795.9 |      5 |      7741   |    7847.2 |    758.5 |   7206.4 |   9081.4 |
| Q09     | exasol     |   2044.7 |      5 |     10652.3 |   10777.3 |   2105.2 |   7824.3 |  13765.4 |
| Q10     | clickhouse |   2530.2 |      5 |      9217.2 |   10538.3 |   2547.7 |   8301.3 |  14068.6 |
| Q10     | exasol     |    745.5 |      5 |      2754.4 |    2932.9 |    579.2 |   2385.5 |   3885.7 |
| Q11     | clickhouse |    792.5 |      5 |      4366.4 |    5461.8 |   1828.8 |   3965.5 |   7614.4 |
| Q11     | exasol     |   1467   |      5 |      1008.7 |     930.5 |    183.4 |    670.6 |   1138.3 |
| Q12     | clickhouse |   2832.5 |      5 |      9850.2 |    9855.2 |   1405.7 |   8440   |  11296.7 |
| Q12     | exasol     |    197.1 |      5 |       735.7 |     816.9 |    230   |    588.6 |   1158.6 |
| Q13     | clickhouse |   3884   |      5 |     15324   |   14890.6 |   2964.5 |  11853.8 |  19119.5 |
| Q13     | exasol     |   1091.2 |      5 |      4494   |    4745.1 |   2719.3 |    883.6 |   8485.3 |
| Q14     | clickhouse |   1004.8 |      5 |      3898.6 |    3626.1 |   1286.4 |   1597.9 |   4833.5 |
| Q14     | exasol     |    219.9 |      5 |      1004.5 |    1070.3 |    310.7 |    700.3 |   1524   |
| Q15     | clickhouse |    295.3 |      5 |      1764.8 |    1841.9 |    727.2 |    970.8 |   2738.5 |
| Q15     | exasol     |    243.6 |      5 |      1211.2 |    1288.4 |    492.9 |    778.4 |   1948   |
| Q16     | clickhouse |   2032.4 |      5 |      6711.3 |    6346.8 |   1452.6 |   4679.8 |   8208.2 |
| Q16     | exasol     |    444.8 |      5 |      1811.5 |    2162.5 |   1236.3 |   1055.5 |   4276.2 |
| Q17     | clickhouse |   1608.5 |      5 |      8159.3 |    7994.5 |   1103.7 |   6456.2 |   9507.6 |
| Q17     | exasol     |     57.2 |      5 |       201.7 |     188.1 |     93.1 |     56.3 |    312.8 |
| Q18     | clickhouse |   2471   |      5 |      9270.3 |    9257.5 |   1644.4 |   7259.9 |  11765.1 |
| Q18     | exasol     |    595.7 |      5 |      2892.8 |    2772.5 |    273.3 |   2468.3 |   3093.1 |
| Q19     | clickhouse |   8499.4 |      5 |     21943.4 |   18910.4 |   6933.8 |   8407.7 |  24698.9 |
| Q19     | exasol     |     67.2 |      5 |       379.8 |     419.7 |    208.6 |    233.6 |    776.2 |
| Q20     | clickhouse |   3165.3 |      5 |     10827.8 |   12104.1 |   3102.7 |   8742   |  16104.3 |
| Q20     | exasol     |    301.7 |      5 |      1255.5 |    1218   |    586.7 |    284.1 |   1864   |
| Q21     | clickhouse |   1937.2 |      5 |      6777.3 |    6562   |    909.4 |   5094.4 |   7567.1 |
| Q21     | exasol     |  11009.8 |      5 |      3582.8 |    2823.6 |   1653   |    673.3 |   4666.8 |
| Q22     | clickhouse |    920.7 |      5 |      3024   |    3322.4 |   1885.4 |    868.4 |   6074   |
| Q22     | exasol     |    125   |      5 |       641.5 |     669.6 |    259.1 |    377.8 |   1018.3 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1206.1ms
- Average: 2157.8ms
- Range: 52.8ms - 13765.4ms

**#2. Clickhouse**
- Median: 8354.5ms
- Average: 9977.6ms
- Range: 519.3ms - 30280.0ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 10580.5 | 8984.9 | 519.3 | 29574.8 |
| 1 | 22 | 11186.2 | 8728.5 | 868.4 | 30280.0 |
| 2 | 22 | 10619.6 | 8386.3 | 1597.9 | 29354.3 |
| 3 | 22 | 9615.2 | 8053.8 | 1983.8 | 29134.1 |
| 4 | 22 | 7886.4 | 7673.1 | 729.9 | 24103.3 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 7673.1ms
- **Worst stream median:** 8984.9ms
- **Performance variance:** 17.1% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **consistent** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 2309.9 | 1290.6 | 159.7 | 10652.3 |
| 1 | 22 | 1775.7 | 1085.6 | 233.6 | 4494.0 |
| 2 | 22 | 2197.2 | 1618.0 | 212.4 | 13765.4 |
| 3 | 22 | 2484.5 | 985.0 | 52.8 | 10994.9 |
| 4 | 22 | 2021.5 | 1433.8 | 157.2 | 4666.8 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 985.0ms
- **Worst stream median:** 1618.0ms
- **Performance variance:** 64.3% difference between fastest and slowest streams
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