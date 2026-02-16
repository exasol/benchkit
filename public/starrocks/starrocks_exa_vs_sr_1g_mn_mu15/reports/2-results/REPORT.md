# Exasol vs StarRocks: TPC-H SF1 (Multi-Node 3, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:50:43


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
- **exasol** was the fastest overall with **724.2ms** median runtime
- **starrocks** was **2.5×** slower- Tested **220** total query executions across 22 different query types
- **Execution mode:** Multiuser with **15 concurrent streams** (randomized distribution)

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
| Aggregation        |    418.3 |      1481   | exasol   |
| Join-Heavy         |   1049   |      2314.6 | exasol   |
| Complex Analytical |    722.5 |      1756.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         561.3 |          1292   |    2.3  |      0.43 | False    |
| Q02     | exasol            | starrocks           |        1066.5 |          3166.3 |    2.97 |      0.34 | False    |
| Q03     | exasol            | starrocks           |         672.5 |          1216   |    1.81 |      0.55 | False    |
| Q04     | exasol            | starrocks           |         391   |          1650.7 |    4.22 |      0.24 | False    |
| Q05     | exasol            | starrocks           |        1542.5 |          1859.2 |    1.21 |      0.83 | False    |
| Q06     | exasol            | starrocks           |         180.5 |           763.5 |    4.23 |      0.24 | False    |
| Q07     | exasol            | starrocks           |        1538.9 |          2219.2 |    1.44 |      0.69 | False    |
| Q08     | exasol            | starrocks           |        1031.5 |          1854.5 |    1.8  |      0.56 | False    |
| Q09     | exasol            | starrocks           |        2682.1 |          2427.9 |    0.91 |      1.1  | True     |
| Q10     | exasol            | starrocks           |        1291.5 |          2486.3 |    1.93 |      0.52 | False    |
| Q11     | exasol            | starrocks           |         398.2 |          2360   |    5.93 |      0.17 | False    |
| Q12     | exasol            | starrocks           |         390.7 |          2086.9 |    5.34 |      0.19 | False    |
| Q13     | exasol            | starrocks           |         749.8 |          1769.7 |    2.36 |      0.42 | False    |
| Q14     | exasol            | starrocks           |         418.3 |          1532.9 |    3.66 |      0.27 | False    |
| Q15     | exasol            | starrocks           |         681.3 |          1027   |    1.51 |      0.66 | False    |
| Q16     | exasol            | starrocks           |        1295.1 |          1499.2 |    1.16 |      0.86 | False    |
| Q17     | exasol            | starrocks           |         475.2 |          1393.9 |    2.93 |      0.34 | False    |
| Q18     | exasol            | starrocks           |        2205.7 |          4287.6 |    1.94 |      0.51 | False    |
| Q19     | exasol            | starrocks           |         347   |          1484.6 |    4.28 |      0.23 | False    |
| Q20     | exasol            | starrocks           |         719.7 |          2089.3 |    2.9  |      0.34 | False    |
| Q21     | exasol            | starrocks           |        1016.6 |          4765.1 |    4.69 |      0.21 | False    |
| Q22     | exasol            | starrocks           |         563.3 |          1638.4 |    2.91 |      0.34 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |     65   |      5 |       561.3 |     593.6 |    346.8 |     62.9 |    969.2 |
| Q01     | starrocks |    843.9 |      5 |      1292   |    1295.9 |    329.8 |    942.8 |   1752.8 |
| Q02     | exasol    |    124.8 |      5 |      1066.5 |    3116.3 |   4794.2 |    805.2 |  11690.1 |
| Q02     | starrocks |    351.7 |      5 |      3166.3 |    2952.9 |    525.1 |   2286   |   3411.6 |
| Q03     | exasol    |     61.5 |      5 |       672.5 |     620.1 |    278.5 |    237.5 |    972.3 |
| Q03     | starrocks |    221.4 |      5 |      1216   |    1465.2 |    378.6 |   1173   |   2012.1 |
| Q04     | exasol    |     36.2 |      5 |       391   |     318.9 |    286.2 |     34.1 |    722.5 |
| Q04     | starrocks |    131.7 |      5 |      1650.7 |    1490   |    833.5 |    116.4 |   2393.8 |
| Q05     | exasol    |    115.5 |      5 |      1542.5 |    1535.3 |    400.8 |   1156.5 |   2174.4 |
| Q05     | starrocks |    167.4 |      5 |      1859.2 |    1796.2 |    667.8 |    696.5 |   2332.2 |
| Q06     | exasol    |     17.7 |      5 |       180.5 |     204.4 |    120.6 |     71.8 |    387.5 |
| Q06     | starrocks |     71.2 |      5 |       763.5 |     921.9 |    415.9 |    600   |   1621.5 |
| Q07     | exasol    |     89.8 |      5 |      1538.9 |    1420.5 |    828.4 |     88.3 |   2260.5 |
| Q07     | starrocks |    148.5 |      5 |      2219.2 |    2192.3 |    279.6 |   1728.9 |   2441.9 |
| Q08     | exasol    |     76.7 |      5 |      1031.5 |    1017   |    470.5 |    578.5 |   1733.1 |
| Q08     | starrocks |    237   |      5 |      1854.5 |    1624.2 |    605.4 |    548.3 |   2009.6 |
| Q09     | exasol    |    164.7 |      5 |      2682.1 |    2951   |    824.9 |   2222.7 |   4201.1 |
| Q09     | starrocks |    275.6 |      5 |      2427.9 |    2460.3 |    264.5 |   2127.1 |   2774   |
| Q10     | exasol    |     79.4 |      5 |      1291.5 |    1287.1 |    572.6 |    717.6 |   2137.5 |
| Q10     | starrocks |    318.6 |      5 |      2486.3 |    2438   |    631.3 |   1419.2 |   3108   |
| Q11     | exasol    |     50   |      5 |       398.2 |     541.1 |    282.9 |    282   |    876.9 |
| Q11     | starrocks |    120.7 |      5 |      2360   |    2249.2 |   1101.9 |    581.3 |   3674.8 |
| Q12     | exasol    |     37   |      5 |       390.7 |     455   |    299.8 |    164.8 |    963.6 |
| Q12     | starrocks |    154.9 |      5 |      2086.9 |    1903.5 |    714.6 |    801.2 |   2650.2 |
| Q13     | exasol    |     61.6 |      5 |       749.8 |     997.9 |   1033.6 |     99.7 |   2742.4 |
| Q13     | starrocks |    228.1 |      5 |      1769.7 |    1751.3 |    417.4 |   1370.6 |   2398.8 |
| Q14     | exasol    |     33.1 |      5 |       418.3 |     478.2 |    344   |     33.3 |    991.2 |
| Q14     | starrocks |     88.4 |      5 |      1532.9 |    1687.6 |    809.3 |    621.7 |   2688.4 |
| Q15     | exasol    |     47.4 |      5 |       681.3 |     805.5 |    372.5 |    426   |   1396.7 |
| Q15     | starrocks |    126.4 |      5 |      1027   |    1192.4 |    396.8 |    868.1 |   1791.9 |
| Q16     | exasol    |    116.9 |      5 |      1295.1 |    1479.8 |   1254.6 |    325.9 |   3275.2 |
| Q16     | starrocks |    257.5 |      5 |      1499.2 |    1809.7 |    911.3 |   1190   |   3383.2 |
| Q17     | exasol    |     44.1 |      5 |       475.2 |     398.6 |    186.1 |    138.4 |    580.8 |
| Q17     | starrocks |    118.8 |      5 |      1393.9 |    1236.4 |    695.4 |    222.3 |   1931.1 |
| Q18     | exasol    |    125   |      5 |      2205.7 |    1839.7 |    926.5 |    846.6 |   2868.4 |
| Q18     | starrocks |    268.1 |      5 |      4287.6 |    4469.7 |    886.3 |   3584.5 |   5419.1 |
| Q19     | exasol    |     27.5 |      5 |       347   |     319.3 |    209.7 |     27.2 |    595.4 |
| Q19     | starrocks |    111.8 |      5 |      1484.6 |    1467.5 |    484.3 |    686.1 |   1993.1 |
| Q20     | exasol    |     60.3 |      5 |       719.7 |     719.2 |    412.9 |     61   |   1121.2 |
| Q20     | starrocks |    169   |      5 |      2089.3 |    2188.8 |    805.4 |   1357.8 |   3482   |
| Q21     | exasol    |     58.8 |      5 |      1016.6 |     848   |    363.2 |    267   |   1160.6 |
| Q21     | starrocks |    466.3 |      5 |      4765.1 |    4494.8 |   2561.8 |   1249.4 |   8088.4 |
| Q22     | exasol    |     31.5 |      5 |       563.3 |     564.1 |    191.2 |    354.7 |    763.6 |
| Q22     | starrocks |     77.8 |      5 |      1638.4 |    1630.9 |    485.9 |   1066.4 |   2130.5 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 724.2ms
- Average: 1023.2ms
- Range: 27.2ms - 11690.1ms

**#2. Starrocks**
- Median: 1807.4ms
- Average: 2032.7ms
- Range: 116.4ms - 8088.4ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 852.2 | 664.1 | 180.5 | 2405.3 |
| 1 | 8 | 1512.1 | 62.0 | 27.2 | 11690.1 |
| 10 | 7 | 953.7 | 744.7 | 231.5 | 2742.4 |
| 11 | 7 | 884.6 | 563.3 | 392.6 | 2260.5 |
| 12 | 7 | 1238.5 | 1084.7 | 49.8 | 2222.7 |
| 13 | 7 | 1109.4 | 1235.8 | 71.8 | 2312.5 |
| 14 | 7 | 963.8 | 1000.9 | 387.5 | 1538.9 |
| 2 | 8 | 837.9 | 787.4 | 354.7 | 1733.1 |
| 3 | 8 | 921.8 | 614.2 | 237.5 | 2682.1 |
| 4 | 8 | 943.4 | 709.6 | 138.4 | 3275.2 |
| 5 | 7 | 1133.6 | 1016.6 | 356.3 | 3336.4 |
| 6 | 7 | 887.1 | 717.6 | 164.8 | 2137.5 |
| 7 | 7 | 916.4 | 426.0 | 347.0 | 2868.4 |
| 8 | 7 | 1201.4 | 726.0 | 267.0 | 4201.1 |
| 9 | 7 | 999.2 | 763.6 | 135.6 | 2174.4 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 62.0ms
- **Worst stream median:** 1235.8ms
- **Performance variance:** 1894.8% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 2077.4 | 2292.9 | 548.3 | 5370.5 |
| 1 | 8 | 1793.5 | 1507.0 | 1292.0 | 3398.7 |
| 10 | 7 | 1976.9 | 1756.4 | 868.1 | 3482.0 |
| 11 | 7 | 1668.3 | 1728.9 | 1066.4 | 2130.5 |
| 12 | 7 | 2458.6 | 2427.9 | 116.4 | 4287.6 |
| 13 | 7 | 1980.9 | 2332.2 | 970.1 | 2670.8 |
| 14 | 7 | 1713.4 | 1769.7 | 763.5 | 2441.9 |
| 2 | 8 | 1741.0 | 1904.2 | 1026.1 | 2092.3 |
| 3 | 8 | 2009.9 | 1926.4 | 942.8 | 3674.8 |
| 4 | 8 | 2118.4 | 1594.4 | 222.3 | 8088.4 |
| 5 | 7 | 2448.5 | 2393.8 | 1173.0 | 4765.1 |
| 6 | 7 | 2162.2 | 2360.0 | 1210.8 | 3108.0 |
| 7 | 7 | 2221.7 | 2089.3 | 621.7 | 5419.1 |
| 8 | 7 | 2400.7 | 2286.0 | 878.3 | 5312.5 |
| 9 | 7 | 1779.3 | 1621.5 | 654.6 | 3686.9 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 1507.0ms
- **Worst stream median:** 2427.9ms
- **Performance variance:** 61.1% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

**Query Distribution Method:**
- Query distribution was **randomized** (seed: 42) for realistic concurrent user simulation


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 1
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 5
- **Execution Mode:** Multiuser (15 concurrent streams)
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