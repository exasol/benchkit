# Exasol vs StarRocks: TPC-H SF30 (Multi-Node 3, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 16:07:27


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

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
- **exasol** was the fastest overall with **2204.8ms** median runtime
- **starrocks** was **3.8×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |   1329.1 |      5350   | exasol   |
| Join-Heavy         |   3517.4 |     17938.6 | exasol   |
| Complex Analytical |   2652.1 |     13310.7 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6507.6 |         79180.9 |   12.17 |      0.08 | False    |
| Q02     | exasol            | starrocks           |         557   |          2141.5 |    3.84 |      0.26 | False    |
| Q03     | exasol            | starrocks           |        4292.4 |         28039.7 |    6.53 |      0.15 | False    |
| Q04     | exasol            | starrocks           |        1181.2 |         61306.7 |   51.9  |      0.02 | False    |
| Q05     | exasol            | starrocks           |        4776.5 |         34220.2 |    7.16 |      0.14 | False    |
| Q06     | exasol            | starrocks           |         341.4 |          4103.5 |   12.02 |      0.08 | False    |
| Q07     | exasol            | starrocks           |        7067   |          7231   |    1.02 |      0.98 | False    |
| Q08     | exasol            | starrocks           |        1671.4 |         14230.4 |    8.51 |      0.12 | False    |
| Q09     | exasol            | starrocks           |       17644.7 |         25264   |    1.43 |      0.7  | False    |
| Q10     | exasol            | starrocks           |        4488.1 |         21979.5 |    4.9  |      0.2  | False    |
| Q11     | exasol            | starrocks           |        1326.8 |          1576.8 |    1.19 |      0.84 | False    |
| Q12     | exasol            | starrocks           |        1296.3 |          8436.8 |    6.51 |      0.15 | False    |
| Q13     | exasol            | starrocks           |        8908.6 |         20548.2 |    2.31 |      0.43 | False    |
| Q14     | exasol            | starrocks           |        1427   |          4663.7 |    3.27 |      0.31 | False    |
| Q15     | exasol            | starrocks           |        1425.8 |          4766.4 |    3.34 |      0.3  | False    |
| Q16     | exasol            | starrocks           |        2406.4 |          2572.5 |    1.07 |      0.94 | False    |
| Q17     | exasol            | starrocks           |         395.8 |          5475.8 |   13.83 |      0.07 | False    |
| Q18     | exasol            | starrocks           |        2586.4 |         33756.7 |   13.05 |      0.08 | False    |
| Q19     | exasol            | starrocks           |         648.4 |          4697   |    7.24 |      0.14 | False    |
| Q20     | exasol            | starrocks           |        2495.4 |          5350   |    2.14 |      0.47 | False    |
| Q21     | exasol            | starrocks           |        5373   |         69623.8 |   12.96 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         976.4 |          2068.5 |    2.12 |      0.47 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1268   |      5 |      6507.6 |    5730.6 |   2882   |   1286.7 |   8341   |
| Q01     | starrocks |  16160.3 |      5 |     79180.9 |   95120.5 |  52652.8 |  48541.7 | 185595   |
| Q02     | exasol    |    115.2 |      5 |       557   |    3729.5 |   5703.2 |    299.5 |  13598.1 |
| Q02     | starrocks |   1032.7 |      5 |      2141.5 |    3006.5 |   2150.5 |   1388.3 |   6753.1 |
| Q03     | exasol    |   1020.1 |      5 |      4292.4 |    7487.6 |   8202   |   1788.8 |  21783.7 |
| Q03     | starrocks |   6643.1 |      5 |     28039.7 |   22216   |  11967.1 |   6153.4 |  34818.7 |
| Q04     | exasol    |    288.5 |      5 |      1181.2 |    1162.7 |    667.5 |    322.5 |   1938.5 |
| Q04     | starrocks |   4842.3 |      5 |     61306.7 |   94458.6 |  79140.2 |  17905.6 | 184738   |
| Q05     | exasol    |   1068.8 |      5 |      4776.5 |    5434.4 |   1816.6 |   3480.9 |   8300.6 |
| Q05     | starrocks |   6213   |      5 |     34220.2 |   29528.7 |  10618.9 |  16467.4 |  41031.5 |
| Q06     | exasol    |     68.9 |      5 |       341.4 |     377.9 |    163.3 |    229.2 |    650.2 |
| Q06     | starrocks |   2428.6 |      5 |      4103.5 |    4064.3 |   1735   |   2313.8 |   6837.5 |
| Q07     | exasol    |   1369.1 |      5 |      7067   |    8182.9 |   3753.2 |   5822.8 |  14774.8 |
| Q07     | starrocks |   4491.2 |      5 |      7231   |    7666.2 |   1007.8 |   6572.6 |   9143.9 |
| Q08     | exasol    |    722.4 |      5 |      1671.4 |    1991.2 |    593.1 |   1476.9 |   2787.6 |
| Q08     | starrocks |   5699.5 |      5 |     14230.4 |   14047   |   4825.5 |   6137.5 |  18295.3 |
| Q09     | exasol    |   5581   |      5 |     17644.7 |   19557.9 |   5156.1 |  15660.8 |  28564.3 |
| Q09     | starrocks |   9872.3 |      5 |     25264   |   27145.2 |   6313.2 |  22026.4 |  37764.3 |
| Q10     | exasol    |    884.7 |      5 |      4488.1 |    6223.1 |   4201.6 |   3553.9 |  13641.9 |
| Q10     | starrocks |   9023.3 |      5 |     21979.5 |   22430.7 |   2330.5 |  19499.7 |  25440.4 |
| Q11     | exasol    |   1741.6 |      5 |      1326.8 |    1363.1 |    608   |    766.1 |   2260.1 |
| Q11     | starrocks |    724.9 |      5 |      1576.8 |    2546.5 |   2147   |   1252.4 |   6340.7 |
| Q12     | exasol    |    292.4 |      5 |      1296.3 |    1468.1 |    553.7 |    963.3 |   2058.8 |
| Q12     | starrocks |   3561.2 |      5 |      8436.8 |   10376.1 |   5117.6 |   6263.7 |  18564.8 |
| Q13     | exasol    |   1213.6 |      5 |      8908.6 |    8326.2 |   2752.2 |   4327.8 |  11903.1 |
| Q13     | starrocks |   6572.6 |      5 |     20548.2 |   22888.8 |  12957.1 |  13126   |  45123.4 |
| Q14     | exasol    |    400.5 |      5 |      1427   |    1469.2 |    737.5 |    390.9 |   2422.4 |
| Q14     | starrocks |   2876.9 |      5 |      4663.7 |    5282.1 |   2510.2 |   3430.1 |   9654.2 |
| Q15     | exasol    |    324.9 |      5 |      1425.8 |    1494.6 |    398.1 |    956   |   1961.6 |
| Q15     | starrocks |   2539.8 |      5 |      4766.4 |    4466.6 |   1567.8 |   2534.6 |   6441.9 |
| Q16     | exasol    |    564.6 |      5 |      2406.4 |    2378.7 |    825.5 |   1345.2 |   3555.4 |
| Q16     | starrocks |   1331.9 |      5 |      2572.5 |    2747.3 |   1001   |   1325.3 |   3864.7 |
| Q17     | exasol    |     79.4 |      5 |       395.8 |     482.8 |    257.2 |    258.6 |    922.5 |
| Q17     | starrocks |   3135.1 |      5 |      5475.8 |    6819.1 |   3456.6 |   3871.8 |  12756   |
| Q18     | exasol    |    726.8 |      5 |      2586.4 |    6933.3 |   8627.2 |   2149.5 |  22183.9 |
| Q18     | starrocks |  10515.5 |      5 |     33756.7 |   32971.4 |   5742.5 |  23349   |  38578.5 |
| Q19     | exasol    |    109.8 |      5 |       648.4 |     583.1 |    136   |    435.7 |    727.3 |
| Q19     | starrocks |   3537.4 |      5 |      4697   |    5168.4 |   1708.1 |   3628.3 |   7740.1 |
| Q20     | exasol    |    395.3 |      5 |      2495.4 |    2253.7 |    821.2 |    834.9 |   2975.9 |
| Q20     | starrocks |   3103.4 |      5 |      5350   |    6251   |   2540   |   3680   |   9810.1 |
| Q21     | exasol    |  16117.6 |      5 |      5373   |    6681   |   4260.7 |   2503.9 |  13805.2 |
| Q21     | starrocks |  16816.9 |      5 |     69623.8 |   66094.6 |  30065   |  22138.7 | 103828   |
| Q22     | exasol    |    323   |      5 |       976.4 |     789.2 |    488.9 |    176   |   1366.9 |
| Q22     | starrocks |   1321.6 |      5 |      2068.5 |    2690.1 |   1374.6 |   1644.8 |   4973.9 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 2204.8ms
- Average: 4277.3ms
- Range: 176.0ms - 28564.3ms

**#2. Starrocks**
- Median: 8312.5ms
- Average: 22181.2ms
- Range: 1252.4ms - 185595.1ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 4504.4 | 2640.2 | 386.0 | 18756.8 |
| 1 | 22 | 4115.3 | 1869.6 | 439.8 | 13641.9 |
| 2 | 22 | 4786.4 | 1343.6 | 176.0 | 28564.3 |
| 3 | 22 | 4621.7 | 2992.4 | 229.2 | 17644.7 |
| 4 | 22 | 3358.8 | 2379.2 | 258.6 | 14774.8 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1343.6ms
- **Worst stream median:** 2992.4ms
- **Performance variance:** 122.7% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 25100.1 | 8120.5 | 1325.3 | 174007.0 |
| 1 | 22 | 23713.3 | 7709.6 | 1252.4 | 184738.5 |
| 2 | 22 | 23023.8 | 7156.4 | 1801.8 | 185595.1 |
| 3 | 22 | 23014.1 | 16127.9 | 1388.3 | 87820.4 |
| 4 | 22 | 16054.5 | 7016.5 | 1576.8 | 79180.9 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 7016.5ms
- **Worst stream median:** 16127.9ms
- **Performance variance:** 129.9% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

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