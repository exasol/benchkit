# Concurrency Cliff - 10 Streams - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 14:15:56


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **clickhouse**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (16 vCPUs)- **Memory:** 123.8GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (16 vCPUs)- **Memory:** 123.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **497.8ms** median runtime
- **clickhouse** was **18.2×** slower- Tested **220** total query executions across 22 different query types
- **Execution mode:** Multiuser with **10 concurrent streams** (randomized distribution)

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
| Aggregation        |       5538   |    432.5 | exasol   |
| Join-Heavy         |      10768.6 |    465.2 | exasol   |
| Complex Analytical |      11617.8 |   1375   | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3497.5 |         12533.4 |    3.58 |      0.28 | False    |
| Q02     | exasol            | clickhouse          |         177.3 |          7882.2 |   44.46 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         768.3 |          9010.6 |   11.73 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |         298   |         14696.4 |   49.32 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         986.5 |         13852.7 |   14.04 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         112.8 |          2306.1 |   20.44 |      0.05 | False    |
| Q07     | exasol            | clickhouse          |        1382.6 |         24615.6 |   17.8  |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         362.7 |         14625.9 |   40.33 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        4049.4 |         12982.6 |    3.21 |      0.31 | False    |
| Q10     | exasol            | clickhouse          |        1909.1 |         23090.9 |   12.1  |      0.08 | False    |
| Q11     | exasol            | clickhouse          |         229.1 |          5542.3 |   24.19 |      0.04 | False    |
| Q12     | exasol            | clickhouse          |         432.5 |          6296.6 |   14.56 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3044.2 |         11499.5 |    3.78 |      0.26 | False    |
| Q14     | exasol            | clickhouse          |         395.6 |          3560.4 |    9    |      0.11 | False    |
| Q15     | exasol            | clickhouse          |         914.9 |          2257.4 |    2.47 |      0.41 | False    |
| Q16     | exasol            | clickhouse          |        1552.4 |          5618.4 |    3.62 |      0.28 | False    |
| Q17     | exasol            | clickhouse          |          95.2 |          8595.3 |   90.29 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2650   |         14022   |    5.29 |      0.19 | False    |
| Q19     | exasol            | clickhouse          |          88.2 |         18631.5 |  211.24 |      0    | False    |
| Q20     | exasol            | clickhouse          |         606.4 |          8448.2 |   13.93 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1561.8 |          9652.3 |    6.18 |      0.16 | False    |
| Q22     | exasol            | clickhouse          |         434   |          6735   |   15.52 |      0.06 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   1423.3 |      5 |     12533.4 |   10749.9 |   4612.8 |   3277.9 |  15449.5 |
| Q01     | exasol     |    477.1 |      5 |      3497.5 |    3319.8 |   1072.6 |   1833.6 |   4771.5 |
| Q02     | clickhouse |    600.8 |      5 |      7882.2 |    8343   |   1091.3 |   7058.8 |   9786.6 |
| Q02     | exasol     |     53.1 |      5 |       177.3 |     167.8 |     57.9 |     70.7 |    223.3 |
| Q03     | clickhouse |   1129.2 |      5 |      9010.6 |   11416.2 |   4125.2 |   7489.3 |  15934.4 |
| Q03     | exasol     |    189.5 |      5 |       768.3 |     805.3 |    501.5 |    243.4 |   1375   |
| Q04     | clickhouse |   4009   |      5 |     14696.4 |   14423.9 |   2233.1 |  11208.8 |  17330.6 |
| Q04     | exasol     |     39.7 |      5 |       298   |     244.7 |    120.6 |     68.1 |    368.6 |
| Q05     | clickhouse |    945.6 |      5 |     13852.7 |   14316.6 |   1829.7 |  11804.4 |  16640   |
| Q05     | exasol     |    164.8 |      5 |       986.5 |     993.6 |     45.5 |    941.3 |   1067   |
| Q06     | clickhouse |    111   |      5 |      2306.1 |    2326.4 |    462.8 |   1925.7 |   3081.3 |
| Q06     | exasol     |     25.8 |      5 |       112.8 |     134.6 |     61   |     71.4 |    212.2 |
| Q07     | clickhouse |   4223.1 |      5 |     24615.6 |   23178.3 |   4143.5 |  16799.4 |  27651.8 |
| Q07     | exasol     |    152.2 |      5 |      1382.6 |    1271.7 |    309.6 |    725   |   1462.2 |
| Q08     | clickhouse |   1745.8 |      5 |     14625.9 |   15329.8 |   2824   |  11466.5 |  18757   |
| Q08     | exasol     |     70.2 |      5 |       362.7 |     364.8 |    112.7 |    191.7 |    467.3 |
| Q09     | clickhouse |   1062.3 |      5 |     12982.6 |   11908.2 |   1692   |  10050.2 |  13347.8 |
| Q09     | exasol     |    548.5 |      5 |      4049.4 |    4087.6 |    489   |   3545.3 |   4696.7 |
| Q10     | clickhouse |   2689.5 |      5 |     23090.9 |   22476.3 |   1958.5 |  20068.8 |  24311.3 |
| Q10     | exasol     |    284.9 |      5 |      1909.1 |    1905.3 |    155.1 |   1727.6 |   2103.6 |
| Q11     | clickhouse |    387.6 |      5 |      5542.3 |    5207.1 |    956.8 |   3512.2 |   5854.3 |
| Q11     | exasol     |     88.4 |      5 |       229.1 |     262.6 |    118.7 |    154.5 |    405.7 |
| Q12     | clickhouse |   1093.3 |      5 |      6296.6 |    7031.2 |   2434.3 |   4331.4 |  10601   |
| Q12     | exasol     |     52.9 |      5 |       432.5 |     440.2 |     46.6 |    396.2 |    512.1 |
| Q13     | clickhouse |   1822.9 |      5 |     11499.5 |   11240.7 |   4426.3 |   5071.1 |  16188.9 |
| Q13     | exasol     |    377.8 |      5 |      3044.2 |    2679.5 |    722.7 |   1431.5 |   3127.8 |
| Q14     | clickhouse |    104.7 |      5 |      3560.4 |    3198   |    851.6 |   2136.7 |   3980.9 |
| Q14     | exasol     |     46.2 |      5 |       395.6 |     400.9 |     44   |    362.1 |    473.1 |
| Q15     | clickhouse |    174.8 |      5 |      2257.4 |    2474.8 |    670.1 |   1719.5 |   3499.7 |
| Q15     | exasol     |    164   |      5 |       914.9 |     852.8 |    217.5 |    483.5 |   1058.3 |
| Q16     | clickhouse |    373.7 |      5 |      5618.4 |    5872.6 |    558.5 |   5546   |   6863.5 |
| Q16     | exasol     |    301.6 |      5 |      1552.4 |    1634.1 |    204.3 |   1414.8 |   1903.3 |
| Q17     | clickhouse |    562   |      5 |      8595.3 |    7931.6 |   1387.5 |   5838.2 |   9112.4 |
| Q17     | exasol     |     18.3 |      5 |        95.2 |      90.9 |     13   |     69.3 |    102.6 |
| Q18     | clickhouse |   1045.9 |      5 |     14022   |   13746.5 |   1886.6 |  11617.8 |  15624   |
| Q18     | exasol     |    321.1 |      5 |      2650   |    2389.2 |    787.3 |   1076.1 |   3113.2 |
| Q19     | clickhouse |   2968.5 |      5 |     18631.5 |   16001.9 |   5764.2 |   7351.7 |  21619.2 |
| Q19     | exasol     |     17.8 |      5 |        88.2 |      85.6 |     17.6 |     56.4 |    104.3 |
| Q20     | clickhouse |    826.8 |      5 |      8448.2 |    7546.4 |   1665.2 |   5538   |   8949.5 |
| Q20     | exasol     |    194.1 |      5 |       606.4 |     671.4 |    405.3 |    267.8 |   1330.4 |
| Q21     | clickhouse |   1296.4 |      5 |      9652.3 |   10646.8 |   3072.3 |   7662.5 |  15475.5 |
| Q21     | exasol     |    225.8 |      5 |      1561.8 |    1335.4 |    616.2 |    393.2 |   1842   |
| Q22     | clickhouse |    274   |      5 |      6735   |    5360.8 |   2334.3 |   1703.7 |   7158.9 |
| Q22     | exasol     |     61.5 |      5 |       434   |     370.1 |    148.1 |    105.7 |    450   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 497.8ms
- Average: 1114.0ms
- Range: 56.4ms - 4771.5ms

**#2. Clickhouse**
- Median: 9061.5ms
- Average: 10487.6ms
- Range: 1703.7ms - 27651.8ms


### Per-Stream Performance Analysis

This benchmark was executed using **10 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 11 | 10399.6 | 8801.7 | 1972.4 | 24311.3 |
| 1 | 11 | 11291.7 | 7158.9 | 1703.7 | 25114.8 |
| 2 | 11 | 11215.5 | 11617.8 | 2700.4 | 21709.7 |
| 3 | 11 | 9511.0 | 8212.9 | 1925.7 | 24615.6 |
| 4 | 11 | 11154.3 | 8949.5 | 2346.6 | 23090.9 |
| 5 | 11 | 10651.0 | 11466.5 | 2257.4 | 15844.9 |
| 6 | 11 | 11456.1 | 11499.5 | 2196.8 | 27651.8 |
| 7 | 11 | 9471.6 | 9115.3 | 3560.4 | 19328.2 |
| 8 | 11 | 11086.2 | 8957.3 | 4331.4 | 20752.1 |
| 9 | 11 | 8638.9 | 6735.0 | 2306.1 | 17328.7 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 6735.0ms
- **Worst stream median:** 11617.8ms
- **Performance variance:** 72.5% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 11 | 1297.0 | 713.4 | 71.4 | 3692.7 |
| 1 | 11 | 728.5 | 434.0 | 70.7 | 2004.9 |
| 2 | 11 | 1324.8 | 1076.1 | 68.1 | 3597.6 |
| 3 | 11 | 1220.9 | 396.2 | 69.3 | 4696.7 |
| 4 | 11 | 1201.7 | 1067.0 | 91.0 | 3124.2 |
| 5 | 11 | 917.8 | 875.1 | 95.2 | 2319.5 |
| 6 | 11 | 1165.1 | 932.0 | 56.4 | 3044.2 |
| 7 | 11 | 940.9 | 369.5 | 102.6 | 3497.5 |
| 8 | 11 | 1321.7 | 986.5 | 243.4 | 4453.9 |
| 9 | 11 | 1021.5 | 437.7 | 97.8 | 4771.5 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 369.5ms
- **Worst stream median:** 1076.1ms
- **Performance variance:** 191.2% difference between fastest and slowest streams
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
- **Execution Mode:** Multiuser (10 concurrent streams)
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