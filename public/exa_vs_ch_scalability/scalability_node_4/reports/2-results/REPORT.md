# Node Scaling - 4 Nodes (128GB) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-19 18:14:55


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
- **Deployment:** 4-node cluster

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65
- **Deployment:** 4-node cluster


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **880.2ms** median runtime
- **clickhouse** was **14.0×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |       5598.5 |    592.6 | exasol   |
| Join-Heavy         |      12005.1 |   1127.8 | exasol   |
| Complex Analytical |      13911   |   1314.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        2446.4 |          5033.2 |    2.06 |      0.49 | False    |
| Q02     | exasol            | clickhouse          |         347.9 |         62260.1 |  178.96 |      0.01 | False    |
| Q03     | exasol            | clickhouse          |        1414.8 |         15657.6 |   11.07 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |         650.3 |         29635.9 |   45.57 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        2508.1 |         18989.9 |    7.57 |      0.13 | False    |
| Q06     | exasol            | clickhouse          |         172.9 |           927.3 |    5.36 |      0.19 | False    |
| Q07     | exasol            | clickhouse          |        2600.9 |         12468.7 |    4.79 |      0.21 | False    |
| Q08     | exasol            | clickhouse          |         929.5 |         11935.9 |   12.84 |      0.08 | False    |
| Q09     | exasol            | clickhouse          |        6804.2 |         12019   |    1.77 |      0.57 | False    |
| Q10     | exasol            | clickhouse          |        1698.5 |         16850.4 |    9.92 |      0.1  | False    |
| Q11     | exasol            | clickhouse          |         588.2 |          3593.9 |    6.11 |      0.16 | False    |
| Q12     | exasol            | clickhouse          |         605.6 |         51212   |   84.56 |      0.01 | False    |
| Q13     | exasol            | clickhouse          |        2373.7 |         36702.3 |   15.46 |      0.06 | False    |
| Q14     | exasol            | clickhouse          |         592.6 |          3708.7 |    6.26 |      0.16 | False    |
| Q15     | exasol            | clickhouse          |         744   |          2358.8 |    3.17 |      0.32 | False    |
| Q16     | exasol            | clickhouse          |        1092.3 |          8809.5 |    8.07 |      0.12 | False    |
| Q17     | exasol            | clickhouse          |         186.7 |          6341.9 |   33.97 |      0.03 | False    |
| Q18     | exasol            | clickhouse          |        1823   |         13911   |    7.63 |      0.13 | False    |
| Q19     | exasol            | clickhouse          |         243.5 |         24002   |   98.57 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         771.3 |         12756.5 |   16.54 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |        1728.8 |         10104.5 |    5.84 |      0.17 | False    |
| Q22     | exasol            | clickhouse          |         468.2 |          6526.4 |   13.94 |      0.07 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   1574.7 |      5 |      5033.2 |    6988.5 |   4545   |   4300.6 |  15077   |
| Q01     | exasol     |    570.6 |      5 |      2446.4 |    2172.6 |   1203.8 |    497.7 |   3402.3 |
| Q02     | clickhouse |  13401   |      5 |     62260.1 |   61141.5 |   5324.1 |  54491.3 |  68522.9 |
| Q02     | exasol     |    129.5 |      5 |       347.9 |     527.5 |    420.4 |    326   |   1279.2 |
| Q03     | clickhouse |   4702.9 |      5 |     15657.6 |   14578   |   5374.1 |   8344   |  20583.2 |
| Q03     | exasol     |    430.8 |      5 |      1414.8 |    1354   |    571.1 |    421.1 |   1891.3 |
| Q04     | clickhouse |   9201.9 |      5 |     29635.9 |   31324.5 |   2808.6 |  28808.2 |  34557.3 |
| Q04     | exasol     |    144.8 |      5 |       650.3 |     630.2 |     74.5 |    502   |    682.8 |
| Q05     | clickhouse |   4404.8 |      5 |     18989.9 |   17340.2 |   3801.1 |  10657.9 |  19693.6 |
| Q05     | exasol     |    512.7 |      5 |      2508.1 |    2522.2 |    556.5 |   1796   |   3080.2 |
| Q06     | clickhouse |    123.3 |      5 |       927.3 |     890.5 |    383.3 |    260.3 |   1245.5 |
| Q06     | exasol     |     42.5 |      5 |       172.9 |     174.7 |     96   |     44   |    288.3 |
| Q07     | clickhouse |   2995.6 |      5 |     12468.7 |   12846.3 |   1962.7 |  10900.2 |  15889.8 |
| Q07     | exasol     |    570.3 |      5 |      2600.9 |    2618.8 |    255.3 |   2276.4 |   2995.7 |
| Q08     | clickhouse |   3130.7 |      5 |     11935.9 |   10787.2 |   4362.3 |   3585.6 |  15051.5 |
| Q08     | exasol     |    257.1 |      5 |       929.5 |     915.7 |     56.3 |    827.1 |    976.5 |
| Q09     | clickhouse |   2685.3 |      5 |     12019   |   12865.1 |   1984.5 |  10924.6 |  16075.2 |
| Q09     | exasol     |   1423.3 |      5 |      6804.2 |    6146.6 |   2118.7 |   2655.3 |   7942.2 |
| Q10     | clickhouse |   4526.2 |      5 |     16850.4 |   17314.8 |   1189.8 |  15860.9 |  18799   |
| Q10     | exasol     |    434.4 |      5 |      1698.5 |    1674.1 |    185.9 |   1421.2 |   1890.8 |
| Q11     | clickhouse |    544.3 |      5 |      3593.9 |    3793.3 |   1405.2 |   2440.3 |   6062.8 |
| Q11     | exasol     |    869.6 |      5 |       588.2 |     564.4 |    130   |    421.7 |    697.8 |
| Q12     | clickhouse |  12878.4 |      5 |     51212   |   49506.7 |   9795.7 |  38900.7 |  60614.7 |
| Q12     | exasol     |    134.8 |      5 |       605.6 |     637.5 |    142   |    473.4 |    852   |
| Q13     | clickhouse |  10197.3 |      5 |     36702.3 |   35207   |   5546.6 |  26652.5 |  41451.1 |
| Q13     | exasol     |    453.1 |      5 |      2373.7 |    2212.8 |   1384.9 |    470.9 |   4172.1 |
| Q14     | clickhouse |    904.1 |      5 |      3708.7 |    4566.8 |   2188.6 |   3009.2 |   8399.9 |
| Q14     | exasol     |    165.4 |      5 |       592.6 |     654.2 |    196   |    496.9 |    977.7 |
| Q15     | clickhouse |    295.2 |      5 |      2358.8 |    2065.2 |    778.1 |    716.6 |   2685.4 |
| Q15     | exasol     |    203.3 |      5 |       744   |     812   |    146.6 |    657.9 |   1008   |
| Q16     | clickhouse |   1928.4 |      5 |      8809.5 |    8684   |   3700.6 |   3628.2 |  13924   |
| Q16     | exasol     |    353   |      5 |      1092.3 |    1096.7 |    149.6 |    858.4 |   1242.9 |
| Q17     | clickhouse |   1636.3 |      5 |      6341.9 |    6572   |    552.7 |   6082.6 |   7192.5 |
| Q17     | exasol     |     79.1 |      5 |       186.7 |     184.3 |     74.2 |     79.5 |    281.4 |
| Q18     | clickhouse |   3802.1 |      5 |     13911   |   14240.4 |   1720.9 |  12599.6 |  16752.9 |
| Q18     | exasol     |    344.9 |      5 |      1823   |    1960.6 |    380.4 |   1581.3 |   2559.4 |
| Q19     | clickhouse |   6832.5 |      5 |     24002   |   23871.9 |   7642.2 |  12323.4 |  33452   |
| Q19     | exasol     |     69.7 |      5 |       243.5 |     253.8 |     28.9 |    228.1 |    288.9 |
| Q20     | clickhouse |   3009.7 |      5 |     12756.5 |   11451.4 |   3124.2 |   5902   |  13326.6 |
| Q20     | exasol     |    255.2 |      5 |       771.3 |     728.8 |    356.6 |    239.4 |   1106.1 |
| Q21     | clickhouse |   2828.3 |      5 |     10104.5 |    9647.3 |   3083.8 |   4632.2 |  12793.3 |
| Q21     | exasol     |   6564   |      5 |      1728.8 |    1538.4 |    649   |    417.6 |   2020.4 |
| Q22     | clickhouse |    931.3 |      5 |      6526.4 |    6334.6 |   2931.7 |   2471.2 |  10142.1 |
| Q22     | exasol     |     89.2 |      5 |       468.2 |     467   |    121.2 |    293.8 |    595   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 880.2ms
- Average: 1356.7ms
- Range: 44.0ms - 7942.2ms

**#2. Clickhouse**
- Median: 12314.2ms
- Average: 16455.3ms
- Range: 260.3ms - 68522.9ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 18049.1 | 12549.2 | 260.3 | 68522.9 |
| 1 | 22 | 17834.8 | 14682.7 | 2358.8 | 62636.8 |
| 2 | 22 | 15952.2 | 11445.7 | 2685.4 | 62260.1 |
| 3 | 22 | 16647.6 | 11758.0 | 877.8 | 57796.6 |
| 4 | 22 | 13792.9 | 12202.3 | 927.3 | 60614.7 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 11445.7ms
- **Worst stream median:** 14682.7ms
- **Performance variance:** 28.3% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 1335.2 | 1086.2 | 126.5 | 5779.1 |
| 1 | 22 | 1373.2 | 914.9 | 228.5 | 4172.1 |
| 2 | 22 | 1367.7 | 842.8 | 186.7 | 7942.2 |
| 3 | 22 | 1514.6 | 681.2 | 44.0 | 7552.1 |
| 4 | 22 | 1192.7 | 922.6 | 172.9 | 3092.0 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 681.2ms
- **Worst stream median:** 1086.2ms
- **Performance variance:** 59.5% difference between fastest and slowest streams
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