# Concurrency Cliff - 20 Streams - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 17:01:20


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
- **exasol** was the fastest overall with **1365.2ms** median runtime
- **clickhouse** was **8.6×** slower- Tested **220** total query executions across 22 different query types
- **Execution mode:** Multiuser with **20 concurrent streams** (randomized distribution)

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
| Aggregation        |       7325.7 |    803   | exasol   |
| Join-Heavy         |      10754   |   1442.8 | exasol   |
| Complex Analytical |      13376   |   2435.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        4321.4 |         18076.4 |    4.18 |      0.24 | False    |
| Q02     | exasol            | clickhouse          |         539.4 |         11379.5 |   21.1  |      0.05 | False    |
| Q03     | exasol            | clickhouse          |         862.2 |          7950   |    9.22 |      0.11 | False    |
| Q04     | exasol            | clickhouse          |         578.9 |         18851.3 |   32.56 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2167.1 |         10283.4 |    4.75 |      0.21 | False    |
| Q06     | exasol            | clickhouse          |         233.3 |          3758   |   16.11 |      0.06 | False    |
| Q07     | exasol            | clickhouse          |        2435.4 |         12675.3 |    5.2  |      0.19 | False    |
| Q08     | exasol            | clickhouse          |        1048.2 |          9754.2 |    9.31 |      0.11 | False    |
| Q09     | exasol            | clickhouse          |        9948.7 |         10482.8 |    1.05 |      0.95 | False    |
| Q10     | exasol            | clickhouse          |        3296.9 |         15183.5 |    4.61 |      0.22 | False    |
| Q11     | exasol            | clickhouse          |         426.7 |          9830.5 |   23.04 |      0.04 | False    |
| Q12     | exasol            | clickhouse          |         730.7 |         11980.7 |   16.4  |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        4541.2 |         23025.5 |    5.07 |      0.2  | False    |
| Q14     | exasol            | clickhouse          |         863.6 |          3669.9 |    4.25 |      0.24 | False    |
| Q15     | exasol            | clickhouse          |        1728.4 |          4600.9 |    2.66 |      0.38 | False    |
| Q16     | exasol            | clickhouse          |        3035   |          9190.5 |    3.03 |      0.33 | False    |
| Q17     | exasol            | clickhouse          |         141.3 |         13735.1 |   97.21 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        5008.6 |         13376   |    2.67 |      0.37 | False    |
| Q19     | exasol            | clickhouse          |         201.9 |         32450.8 |  160.73 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         803   |         15811.1 |   19.69 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        3451.7 |         10630.5 |    3.08 |      0.32 | False    |
| Q22     | exasol            | clickhouse          |         930.1 |          8897.1 |    9.57 |      0.1  | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   1448.3 |      5 |     18076.4 |   15740.2 |   9983.1 |   3467.5 |  26217.3 |
| Q01     | exasol     |    481.6 |      5 |      4321.4 |    4692.9 |   2276.9 |   1713.5 |   7342.1 |
| Q02     | clickhouse |    641.3 |      5 |     11379.5 |   11292.7 |   2094.2 |   7897.3 |  13280.8 |
| Q02     | exasol     |     56.7 |      5 |       539.4 |     416.2 |    201.9 |    126.3 |    579.5 |
| Q03     | clickhouse |    594.5 |      5 |      7950   |    9151.7 |   5010.7 |   3806   |  16255.9 |
| Q03     | exasol     |    177.4 |      5 |       862.2 |    1425.5 |   1206.8 |    182.2 |   2885.9 |
| Q04     | clickhouse |   2156   |      5 |     18851.3 |   18586.4 |   2937.3 |  14499.6 |  22222.6 |
| Q04     | exasol     |     39.9 |      5 |       578.9 |     456.7 |    223.3 |    193   |    684.7 |
| Q05     | clickhouse |    407.3 |      5 |     10283.4 |   10637.5 |   1164.2 |   9402.8 |  12075.5 |
| Q05     | exasol     |    169.6 |      5 |      2167.1 |    2396.4 |    495.6 |   1880.5 |   3123.2 |
| Q06     | clickhouse |    104.3 |      5 |      3758   |    3580.3 |    850.4 |   2713.4 |   4634.6 |
| Q06     | exasol     |     26.5 |      5 |       233.3 |     253.2 |    103   |    144.9 |    412   |
| Q07     | clickhouse |    512.2 |      5 |     12675.3 |   11444.6 |   3701.3 |   5014.3 |  14514.2 |
| Q07     | exasol     |    158.4 |      5 |      2435.4 |    2495.5 |    816.1 |   1392.5 |   3656.2 |
| Q08     | clickhouse |    457.4 |      5 |      9754.2 |   10110.3 |   2900.6 |   5887.2 |  13527.4 |
| Q08     | exasol     |     49.3 |      5 |      1048.2 |     965.6 |    597.7 |    276.8 |   1707.7 |
| Q09     | clickhouse |    504.2 |      5 |     10482.8 |   11061.5 |   1209.9 |   9962.7 |  12767.6 |
| Q09     | exasol     |    556.9 |      5 |      9948.7 |    8982.6 |   2432.2 |   4675.9 |  10604.9 |
| Q10     | clickhouse |    696.7 |      5 |     15183.5 |   15010.3 |   1524.5 |  13367.1 |  17315.3 |
| Q10     | exasol     |    293   |      5 |      3296.9 |    3418.6 |   1251.6 |   1900.5 |   5344.1 |
| Q11     | clickhouse |    299.9 |      5 |      9830.5 |    9830.3 |   2115.2 |   6737.9 |  11921.3 |
| Q11     | exasol     |     93.4 |      5 |       426.7 |     409.2 |    256.6 |    140.5 |    718.5 |
| Q12     | clickhouse |    482.4 |      5 |     11980.7 |   12623.8 |   1601.3 |  10783.7 |  14875   |
| Q12     | exasol     |     53.6 |      5 |       730.7 |     791.7 |    404.1 |    381.9 |   1448.8 |
| Q13     | clickhouse |   3298.9 |      5 |     23025.5 |   22257.9 |   4216.9 |  15309.4 |  26159   |
| Q13     | exasol     |    394.1 |      5 |      4541.2 |    4501.9 |   2430.6 |   2115.4 |   8251.9 |
| Q14     | clickhouse |    125.9 |      5 |      3669.9 |    3852.5 |    649.2 |   3258.8 |   4711.6 |
| Q14     | exasol     |     47.9 |      5 |       863.6 |     897.3 |    378.1 |    404.9 |   1453.9 |
| Q15     | clickhouse |    174.2 |      5 |      4600.9 |    4652.7 |    470.9 |   4120.2 |   5208.1 |
| Q15     | exasol     |    167.3 |      5 |      1728.4 |    1621.8 |    472   |    882.9 |   2140.7 |
| Q16     | clickhouse |    381   |      5 |      9190.5 |    9243   |   1214.9 |   8146   |  11219.9 |
| Q16     | exasol     |    304.3 |      5 |      3035   |    3206.2 |    494.3 |   2687.5 |   3877.9 |
| Q17     | clickhouse |    557.5 |      5 |     13735.1 |   15178.3 |   2830.5 |  12672.6 |  18284.7 |
| Q17     | exasol     |     18.8 |      5 |       141.3 |     150.2 |     38.8 |    105.7 |    194.7 |
| Q18     | clickhouse |    528.8 |      5 |     13376   |   13114.5 |   1095.2 |  11537   |  14489.8 |
| Q18     | exasol     |    328.7 |      5 |      5008.6 |    4482   |   1272.6 |   2407.3 |   5549.7 |
| Q19     | clickhouse |   2931.3 |      5 |     32450.8 |   27589.6 |  12615.7 |   5462.3 |  36939.5 |
| Q19     | exasol     |     18.4 |      5 |       201.9 |     203.6 |     82.7 |     84.9 |    288.9 |
| Q20     | clickhouse |    840.5 |      5 |     15811.1 |   15491.7 |   2950.8 |  11319.3 |  18361.7 |
| Q20     | exasol     |    200.3 |      5 |       803   |     957.2 |    530   |    424   |   1527.6 |
| Q21     | clickhouse |    575.8 |      5 |     10630.5 |   10470.9 |   2993.6 |   6111.9 |  13894.6 |
| Q21     | exasol     |    232.2 |      5 |      3451.7 |    2754.7 |   2081.2 |    234.6 |   5122.3 |
| Q22     | clickhouse |    253.8 |      5 |      8897.1 |    8929.9 |   1978.9 |   5786.9 |  10877.4 |
| Q22     | exasol     |     63.7 |      5 |       930.1 |     959   |    380.1 |    486.6 |   1547.5 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1365.2ms
- Average: 2110.8ms
- Range: 84.9ms - 10604.9ms

**#2. Clickhouse**
- Median: 11765.4ms
- Average: 12265.9ms
- Range: 2713.4ms - 36939.5ms


### Per-Stream Performance Analysis

This benchmark was executed using **20 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 6 | 12521.4 | 12506.6 | 3806.0 | 24888.2 |
| 1 | 6 | 11634.6 | 10339.3 | 5786.9 | 20179.3 |
| 10 | 5 | 13677.0 | 10482.8 | 2713.4 | 36939.5 |
| 11 | 5 | 13871.1 | 14514.2 | 4120.2 | 22222.6 |
| 12 | 5 | 10537.1 | 12018.3 | 4285.2 | 13376.0 |
| 13 | 5 | 13262.3 | 12767.6 | 3282.7 | 26217.3 |
| 14 | 5 | 13728.6 | 11632.7 | 6737.9 | 23025.5 |
| 15 | 5 | 11778.4 | 12075.5 | 9309.9 | 13565.1 |
| 16 | 5 | 14046.4 | 12159.3 | 4600.9 | 23614.3 |
| 17 | 5 | 10448.1 | 11379.5 | 4711.6 | 13735.1 |
| 18 | 5 | 13150.0 | 13894.6 | 10210.0 | 15811.1 |
| 19 | 5 | 13036.2 | 13502.0 | 8897.1 | 18076.4 |
| 2 | 6 | 12127.5 | 13236.8 | 3467.5 | 18361.7 |
| 3 | 6 | 11118.4 | 11334.2 | 3758.0 | 18284.7 |
| 4 | 6 | 12308.2 | 9388.2 | 2715.2 | 30027.9 |
| 5 | 6 | 11897.3 | 12670.2 | 5049.1 | 18851.3 |
| 6 | 6 | 12956.5 | 10691.8 | 3258.8 | 32450.8 |
| 7 | 6 | 12516.6 | 8877.7 | 3669.9 | 33067.6 |
| 8 | 6 | 12278.9 | 10038.2 | 5728.1 | 26159.0 |
| 9 | 6 | 9236.6 | 7481.2 | 4080.2 | 18215.0 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 7481.2ms
- **Worst stream median:** 14514.2ms
- **Performance variance:** 94.0% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 6 | 2711.5 | 1175.0 | 140.5 | 8251.9 |
| 1 | 6 | 1037.0 | 795.4 | 126.3 | 2961.0 |
| 10 | 5 | 2644.6 | 1453.9 | 84.9 | 10032.4 |
| 11 | 5 | 1591.1 | 1508.1 | 578.9 | 3656.2 |
| 12 | 5 | 2362.6 | 2435.4 | 486.6 | 4156.0 |
| 13 | 5 | 3008.9 | 1713.5 | 539.4 | 9651.1 |
| 14 | 5 | 2137.3 | 1880.5 | 426.7 | 4541.2 |
| 15 | 5 | 2197.8 | 2167.1 | 281.4 | 5122.3 |
| 16 | 5 | 2771.9 | 2716.1 | 862.2 | 5002.0 |
| 17 | 5 | 1597.5 | 786.9 | 141.3 | 5549.7 |
| 18 | 5 | 2959.8 | 943.6 | 524.1 | 10604.9 |
| 19 | 5 | 2492.9 | 1547.5 | 571.5 | 7342.1 |
| 2 | 6 | 2483.3 | 2372.7 | 193.0 | 5008.6 |
| 3 | 6 | 2014.4 | 209.7 | 105.7 | 9948.7 |
| 4 | 6 | 2145.2 | 2422.1 | 273.0 | 3877.9 |
| 5 | 6 | 1600.6 | 670.1 | 194.7 | 5288.2 |
| 6 | 6 | 1358.4 | 679.6 | 169.2 | 3296.9 |
| 7 | 6 | 2174.2 | 1131.0 | 288.9 | 6536.6 |
| 8 | 6 | 2494.5 | 2632.4 | 657.9 | 4021.1 |
| 9 | 6 | 875.4 | 730.1 | 123.5 | 2140.7 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 209.7ms
- **Worst stream median:** 2716.1ms
- **Performance variance:** 1195.5% difference between fastest and slowest streams
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
- **Execution Mode:** Multiuser (20 concurrent streams)
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