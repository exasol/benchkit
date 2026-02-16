# Minimum Viable Resources - 64GB - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-01-19 16:37:21


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **clickhouse**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (8 vCPUs)- **Memory:** 61.8GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (8 vCPUs)- **Memory:** 61.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **861.0ms** median runtime
- **clickhouse** was **13.7×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |       6125.1 |    579.5 | exasol   |
| Join-Heavy         |      12291.2 |    502.6 | exasol   |
| Complex Analytical |      13885.5 |   1481.2 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3775.5 |         13185.1 |    3.49 |      0.29 | False    |
| Q02     | exasol            | clickhouse          |         179.9 |         10485.6 |   58.29 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |        1311.8 |         16781.1 |   12.79 |      0.08 | False    |
| Q04     | exasol            | clickhouse          |         317.9 |         17866.9 |   56.2  |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1210.1 |         14976.4 |   12.38 |      0.08 | False    |
| Q06     | exasol            | clickhouse          |         192.5 |          3225.8 |   16.76 |      0.06 | False    |
| Q07     | exasol            | clickhouse          |        1509.6 |         23838.7 |   15.79 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         428   |         18864   |   44.07 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        5245.7 |         11944.9 |    2.28 |      0.44 | False    |
| Q10     | exasol            | clickhouse          |        2263   |         21171.6 |    9.36 |      0.11 | False    |
| Q11     | exasol            | clickhouse          |         389.9 |          4549.4 |   11.67 |      0.09 | False    |
| Q12     | exasol            | clickhouse          |         466.4 |          6458.3 |   13.85 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3592.1 |         11800.6 |    3.29 |      0.3  | False    |
| Q14     | exasol            | clickhouse          |         465.8 |          2780.8 |    5.97 |      0.17 | False    |
| Q15     | exasol            | clickhouse          |         922.4 |          3941   |    4.27 |      0.23 | False    |
| Q16     | exasol            | clickhouse          |        1406.5 |          6218.8 |    4.42 |      0.23 | False    |
| Q17     | exasol            | clickhouse          |          68.3 |          8588.7 |  125.75 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2539.5 |         15526.6 |    6.11 |      0.16 | False    |
| Q19     | exasol            | clickhouse          |         171   |         24494.9 |  143.25 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         904.2 |         10375.1 |   11.47 |      0.09 | False    |
| Q21     | exasol            | clickhouse          |        2350.6 |         12376.2 |    5.27 |      0.19 | False    |
| Q22     | exasol            | clickhouse          |         469.2 |          4165.7 |    8.88 |      0.11 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2813.4 |      5 |     13185.1 |   12912.8 |   4235.1 |   6336.2 |  17572.3 |
| Q01     | exasol     |    938.9 |      5 |      3775.5 |    3198.2 |   1716   |    948.9 |   5135.1 |
| Q02     | clickhouse |   1077.5 |      5 |     10485.6 |   10666.5 |   1520.5 |   9184.7 |  13158.8 |
| Q02     | exasol     |     63.8 |      5 |       179.9 |     180.9 |     11.5 |    167.8 |    192.7 |
| Q03     | clickhouse |   3354   |      5 |     16781.1 |   14967.4 |   6981.7 |   3038.2 |  21280.1 |
| Q03     | exasol     |    384.7 |      5 |      1311.8 |    1167.6 |    569   |    359.7 |   1731.9 |
| Q04     | clickhouse |   4663.3 |      5 |     17866.9 |   16309.2 |   3499.4 |  12226.4 |  19931.1 |
| Q04     | exasol     |     72.5 |      5 |       317.9 |     302.8 |     95   |    169.7 |    432.6 |
| Q05     | clickhouse |   2761.6 |      5 |     14976.4 |   14731.5 |   1769.4 |  12206.3 |  17082.9 |
| Q05     | exasol     |    292.3 |      5 |      1210.1 |    1233.8 |    177.9 |   1072   |   1506.2 |
| Q06     | clickhouse |    196.8 |      5 |      3225.8 |    3039.5 |    677.8 |   1911.8 |   3687.1 |
| Q06     | exasol     |     47.2 |      5 |       192.5 |     194.9 |    130.3 |     46.6 |    401.3 |
| Q07     | clickhouse |   7808.9 |      5 |     23838.7 |   24982.4 |   4018.5 |  20529   |  30518.7 |
| Q07     | exasol     |    339.4 |      5 |      1509.6 |    1532.2 |    225.1 |   1198.2 |   1785.5 |
| Q08     | clickhouse |   3740.5 |      5 |     18864   |   18870.3 |   1311.8 |  17359.9 |  20726.6 |
| Q08     | exasol     |    101.6 |      5 |       428   |     417.9 |     94.8 |    262.1 |    508.8 |
| Q09     | clickhouse |   2175   |      5 |     11944.9 |   12136.2 |   1698.7 |  10609.9 |  14727.6 |
| Q09     | exasol     |   1183.7 |      5 |      5245.7 |    5185.6 |   1130   |   3499   |   6684.4 |
| Q10     | clickhouse |   5264.9 |      5 |     21171.6 |   22152.1 |   2680.6 |  19906.8 |  26742.7 |
| Q10     | exasol     |    460.1 |      5 |      2263   |    2346   |    392.2 |   1959.9 |   2971.5 |
| Q11     | clickhouse |    654.1 |      5 |      4549.4 |    4614.2 |   1898.9 |   2636.8 |   7620.4 |
| Q11     | exasol     |    110.8 |      5 |       389.9 |     387.3 |     45.3 |    322.3 |    440.4 |
| Q12     | clickhouse |   1781.3 |      5 |      6458.3 |    7434.9 |   1858.1 |   5698   |   9572.8 |
| Q12     | exasol     |     96.4 |      5 |       466.4 |     488.6 |    109.5 |    365.3 |    622.1 |
| Q13     | clickhouse |   2877.8 |      5 |     11800.6 |   10620.7 |   3060.6 |   7218.5 |  13885.5 |
| Q13     | exasol     |    871.3 |      5 |      3592.1 |    3345.7 |   1038.6 |   1539.7 |   4150.8 |
| Q14     | clickhouse |    197.7 |      5 |      2780.8 |    2517.3 |    476.8 |   1756.4 |   2864.9 |
| Q14     | exasol     |     87.3 |      5 |       465.8 |     503.7 |    246.9 |    206   |    891.6 |
| Q15     | clickhouse |    240.3 |      5 |      3941   |    3513.8 |   1143.2 |   1875.8 |   4483.7 |
| Q15     | exasol     |    233.2 |      5 |       922.4 |     923.3 |    146   |    699.5 |   1074.6 |
| Q16     | clickhouse |    625   |      5 |      6218.8 |    5492.6 |   1725.7 |   2777.2 |   6843.4 |
| Q16     | exasol     |    418.9 |      5 |      1406.5 |    1306.5 |    293.9 |    931.7 |   1572.1 |
| Q17     | clickhouse |   1123.5 |      5 |      8588.7 |    9433.7 |   2513.5 |   7072.8 |  12421.3 |
| Q17     | exasol     |     22.5 |      5 |        68.3 |      69.1 |     32.2 |     36.1 |    120.2 |
| Q18     | clickhouse |   3247.1 |      5 |     15526.6 |   15922.6 |   1179.2 |  14860   |  17920.6 |
| Q18     | exasol     |    600.1 |      5 |      2539.5 |    2804.9 |    674.3 |   2274   |   3951.3 |
| Q19     | clickhouse |   5970   |      5 |     24494.9 |   20834.5 |   8459.3 |   5847.2 |  25959   |
| Q19     | exasol     |     37.7 |      5 |       171   |     178.5 |     43.4 |    132.8 |    248.7 |
| Q20     | clickhouse |   1559.7 |      5 |     10375.1 |   10182.3 |   2494   |   7277.5 |  13039   |
| Q20     | exasol     |    236.1 |      5 |       904.2 |     831.8 |    181   |    612.9 |   1004.4 |
| Q21     | clickhouse |   2251.9 |      5 |     12376.2 |   12118.2 |   3318.6 |   7693.4 |  16601.1 |
| Q21     | exasol     |    491.8 |      5 |      2350.6 |    1952.7 |    835   |    496.5 |   2496.5 |
| Q22     | clickhouse |    539.6 |      5 |      4165.7 |    3638.6 |   1817.4 |    581.5 |   5376.1 |
| Q22     | exasol     |    111.6 |      5 |       469.2 |     439.7 |     62.3 |    333.9 |    482   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 861.0ms
- Average: 1317.8ms
- Range: 36.1ms - 6684.4ms

**#2. Clickhouse**
- Median: 11791.7ms
- Average: 11686.0ms
- Range: 581.5ms - 30518.7ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 11651.3 | 11872.8 | 2777.2 | 25102.5 |
| 1 | 22 | 12103.3 | 10931.5 | 581.5 | 27542.6 |
| 2 | 22 | 11640.2 | 11945.8 | 1756.4 | 22769.1 |
| 3 | 22 | 11428.3 | 10492.5 | 2845.9 | 30518.7 |
| 4 | 22 | 11606.7 | 12257.7 | 1911.8 | 24494.9 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 10492.5ms
- **Worst stream median:** 12257.7ms
- **Performance variance:** 16.8% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **consistent** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 1351.2 | 881.5 | 68.3 | 5245.7 |
| 1 | 22 | 1147.0 | 763.2 | 157.3 | 4205.8 |
| 2 | 22 | 1392.7 | 777.5 | 72.4 | 5300.3 |
| 3 | 22 | 1486.0 | 780.9 | 36.1 | 6684.4 |
| 4 | 22 | 1212.0 | 756.6 | 48.3 | 3895.7 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 756.6ms
- **Worst stream median:** 881.5ms
- **Performance variance:** 16.5% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **consistent** performance across streams

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