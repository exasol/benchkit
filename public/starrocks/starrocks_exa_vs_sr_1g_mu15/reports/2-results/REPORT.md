# Exasol vs StarRocks: TPC-H SF1 (Single-Node, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 11:11:04


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
- **exasol** was the fastest overall with **561.7ms** median runtime
- **starrocks** was **3.0×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |    380.1 |      1913.3 | exasol   |
| Join-Heavy         |    844.2 |      1439.5 | exasol   |
| Complex Analytical |    818.6 |      1572.9 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1771.3 |          2234.5 |    1.26 |      0.79 | False    |
| Q02     | exasol            | starrocks           |         580.7 |          1318.4 |    2.27 |      0.44 | False    |
| Q03     | exasol            | starrocks           |         587.9 |          1049.7 |    1.79 |      0.56 | False    |
| Q04     | exasol            | starrocks           |         388.5 |          1078.3 |    2.78 |      0.36 | False    |
| Q05     | exasol            | starrocks           |        1161   |          1929.5 |    1.66 |      0.6  | False    |
| Q06     | exasol            | starrocks           |         100.4 |          1184.6 |   11.8  |      0.08 | False    |
| Q07     | exasol            | starrocks           |         912.2 |          3971.3 |    4.35 |      0.23 | False    |
| Q08     | exasol            | starrocks           |         542.7 |          2564.4 |    4.73 |      0.21 | False    |
| Q09     | exasol            | starrocks           |        2465.3 |          2571.3 |    1.04 |      0.96 | False    |
| Q10     | exasol            | starrocks           |        1229.2 |          2671.1 |    2.17 |      0.46 | False    |
| Q11     | exasol            | starrocks           |         216.4 |           609.9 |    2.82 |      0.35 | False    |
| Q12     | exasol            | starrocks           |         539.1 |          2657.5 |    4.93 |      0.2  | False    |
| Q13     | exasol            | starrocks           |        3578.1 |          1527   |    0.43 |      2.34 | True     |
| Q14     | exasol            | starrocks           |         311   |          1913.3 |    6.15 |      0.16 | False    |
| Q15     | exasol            | starrocks           |         434.1 |          1964   |    4.52 |      0.22 | False    |
| Q16     | exasol            | starrocks           |        1182.5 |           874.6 |    0.74 |      1.35 | True     |
| Q17     | exasol            | starrocks           |         238.2 |          2125.2 |    8.92 |      0.11 | False    |
| Q18     | exasol            | starrocks           |        1284.6 |          5408.4 |    4.21 |      0.24 | False    |
| Q19     | exasol            | starrocks           |         242.8 |          1747.5 |    7.2  |      0.14 | False    |
| Q20     | exasol            | starrocks           |         459.2 |          1728.6 |    3.76 |      0.27 | False    |
| Q21     | exasol            | starrocks           |        1306.1 |          7698.2 |    5.89 |      0.17 | False    |
| Q22     | exasol            | starrocks           |         478.4 |           533   |    1.11 |      0.9  | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    135.4 |      5 |      1771.3 |    1852.1 |    711.9 |   1034.3 |   2915   |
| Q01     | starrocks |    803.2 |      5 |      2234.5 |    2344.1 |   1437   |    865.7 |   4300.1 |
| Q02     | exasol    |     60   |      5 |       580.7 |     707.6 |    440.3 |    239.1 |   1184.1 |
| Q02     | starrocks |    464.4 |      5 |      1318.4 |    1242.7 |    646.1 |    485.4 |   2012.8 |
| Q03     | exasol    |     53.1 |      5 |       587.9 |     861.7 |    627.8 |    384.2 |   1921.8 |
| Q03     | starrocks |    272.5 |      5 |      1049.7 |    1238.3 |    577.3 |    708.5 |   2160.2 |
| Q04     | exasol    |     19.2 |      5 |       388.5 |     422.5 |    238.3 |    105   |    715.4 |
| Q04     | starrocks |    183.1 |      5 |      1078.3 |    1345.7 |   1131.6 |    177.1 |   3154.8 |
| Q05     | exasol    |     59.6 |      5 |      1161   |    1163.1 |    925.5 |     46.7 |   2384.2 |
| Q05     | starrocks |    294.8 |      5 |      1929.5 |    1541.2 |   1015.7 |    375   |   2549   |
| Q06     | exasol    |     11.6 |      5 |       100.4 |     103.9 |     84.4 |     11.5 |    207.7 |
| Q06     | starrocks |     84.3 |      5 |      1184.6 |    1628.5 |   1268.8 |    539.9 |   3468.1 |
| Q07     | exasol    |     51.1 |      5 |       912.2 |     849   |    296.1 |    366.6 |   1151.6 |
| Q07     | starrocks |    272.9 |      5 |      3971.3 |    3665.4 |    900   |   2391.5 |   4713.3 |
| Q08     | exasol    |     26.4 |      5 |       542.7 |     610.1 |    467.7 |     26.6 |   1211.9 |
| Q08     | starrocks |    287.6 |      5 |      2564.4 |    2050.8 |    849.8 |    908.9 |   2826.9 |
| Q09     | exasol    |    114.6 |      5 |      2465.3 |    2410.5 |    659.4 |   1360.8 |   3165.7 |
| Q09     | starrocks |    379.6 |      5 |      2571.3 |    2134.8 |    781.5 |    938   |   2750.5 |
| Q10     | exasol    |     57.1 |      5 |      1229.2 |    1290.1 |    385.9 |    765.1 |   1701.9 |
| Q10     | starrocks |    318.1 |      5 |      2671.1 |    2134.8 |   1538.2 |    368.8 |   3843.4 |
| Q11     | exasol    |     24.5 |      5 |       216.4 |     261   |    187.6 |     23.7 |    510.9 |
| Q11     | starrocks |    123.1 |      5 |       609.9 |     810.8 |    510.8 |    308.3 |   1453.3 |
| Q12     | exasol    |     22.1 |      5 |       539.1 |     450   |    269.8 |     21.5 |    694   |
| Q12     | starrocks |    190.4 |      5 |      2657.5 |    2394.6 |   1222.5 |    861.9 |   3982   |
| Q13     | exasol    |    121.3 |      5 |      3578.1 |    4786   |   4037.2 |   1062   |  11682.7 |
| Q13     | starrocks |    389.1 |      5 |      1527   |    1440.6 |    432   |    736   |   1868.3 |
| Q14     | exasol    |     17.9 |      5 |       311   |     299.9 |    178.9 |     17.7 |    504   |
| Q14     | starrocks |    117.8 |      5 |      1913.3 |    2352.9 |   1294.5 |   1092.5 |   3885.5 |
| Q15     | exasol    |     25.4 |      5 |       434.1 |     634.4 |    618.7 |    172   |   1720.1 |
| Q15     | starrocks |    149.7 |      5 |      1964   |    1983.9 |   1115.1 |    380.7 |   3236.6 |
| Q16     | exasol    |    101.7 |      5 |      1182.5 |    1477.5 |   1368.4 |    464.5 |   3815.4 |
| Q16     | starrocks |    349.9 |      5 |       874.6 |     909.7 |    454.2 |    283.6 |   1390.3 |
| Q17     | exasol    |     12.2 |      5 |       238.2 |     193   |     85.2 |     82.5 |    280.2 |
| Q17     | starrocks |    178.9 |      5 |      2125.2 |    1748   |   1385.3 |    233.6 |   3170.9 |
| Q18     | exasol    |     82   |      5 |      1284.6 |    1241.9 |    792.5 |     81.4 |   1985.5 |
| Q18     | starrocks |    275.4 |      5 |      5408.4 |    5560.1 |   1229.8 |   4364.3 |   7411.9 |
| Q19     | exasol    |     12   |      5 |       242.8 |     264.8 |    179.6 |     20.5 |    462.4 |
| Q19     | starrocks |    135.4 |      5 |      1747.5 |    1673.1 |    659.1 |    619.3 |   2239.3 |
| Q20     | exasol    |     32.7 |      5 |       459.2 |     442.3 |    172.2 |    245   |    694.4 |
| Q20     | starrocks |    222.6 |      5 |      1728.6 |    2250.2 |    818.7 |   1687   |   3533.5 |
| Q21     | exasol    |     69.1 |      5 |      1306.1 |    1190.3 |    511.6 |    640.9 |   1901.1 |
| Q21     | starrocks |    486.2 |      5 |      7698.2 |    6297.8 |   4997   |   1035.7 |  12984.7 |
| Q22     | exasol    |     24.2 |      5 |       478.4 |     647.3 |    379.6 |    344.9 |   1270.6 |
| Q22     | starrocks |     84.8 |      5 |       533   |     662.8 |    446.8 |    246.5 |   1425.7 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 561.7ms
- Average: 1007.2ms
- Range: 11.5ms - 11682.7ms

**#2. Starrocks**
- Median: 1688.3ms
- Average: 2155.0ms
- Range: 177.1ms - 12984.7ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 1489.0 | 25.1 | 11.5 | 11682.7 |
| 1 | 8 | 1079.0 | 484.5 | 20.5 | 4235.3 |
| 10 | 7 | 883.7 | 462.4 | 238.2 | 3578.1 |
| 11 | 7 | 736.2 | 715.4 | 182.0 | 1270.6 |
| 12 | 7 | 1153.2 | 995.9 | 105.0 | 2465.3 |
| 13 | 7 | 1131.8 | 1062.0 | 32.3 | 2384.2 |
| 14 | 7 | 1243.8 | 416.1 | 100.4 | 3371.7 |
| 2 | 8 | 969.9 | 663.2 | 280.2 | 2093.0 |
| 3 | 8 | 951.7 | 599.0 | 178.1 | 2663.6 |
| 4 | 8 | 719.3 | 526.8 | 82.5 | 1398.8 |
| 5 | 7 | 1152.8 | 640.9 | 314.6 | 2397.1 |
| 6 | 7 | 827.4 | 765.1 | 216.4 | 1720.1 |
| 7 | 7 | 708.9 | 488.0 | 242.8 | 1985.5 |
| 8 | 7 | 1049.1 | 744.9 | 123.0 | 3165.7 |
| 9 | 7 | 987.7 | 527.4 | 167.6 | 3815.4 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 25.1ms
- **Worst stream median:** 1062.0ms
- **Performance variance:** 4122.7% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 2130.0 | 1700.4 | 573.3 | 5408.4 |
| 1 | 8 | 1811.6 | 1619.0 | 736.0 | 4713.3 |
| 10 | 7 | 2073.6 | 1747.5 | 1318.4 | 3533.5 |
| 11 | 7 | 1980.6 | 2208.2 | 533.0 | 3236.6 |
| 12 | 7 | 2526.1 | 1743.1 | 177.1 | 6029.1 |
| 13 | 7 | 2072.4 | 2313.3 | 539.9 | 4085.2 |
| 14 | 7 | 2107.7 | 2239.3 | 1184.6 | 2612.3 |
| 2 | 8 | 1954.6 | 2365.9 | 246.5 | 3201.4 |
| 3 | 8 | 1924.7 | 1571.5 | 375.0 | 4300.1 |
| 4 | 8 | 2194.6 | 646.6 | 308.3 | 12984.7 |
| 5 | 7 | 2590.0 | 1035.7 | 283.6 | 8165.7 |
| 6 | 7 | 2080.1 | 1572.9 | 609.9 | 3982.0 |
| 7 | 7 | 2229.1 | 1092.5 | 380.7 | 7411.9 |
| 8 | 7 | 2533.7 | 2012.8 | 233.6 | 7698.2 |
| 9 | 7 | 2225.3 | 2376.4 | 515.4 | 4586.6 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 646.6ms
- **Worst stream median:** 2376.4ms
- **Performance variance:** 267.5% difference between fastest and slowest streams
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