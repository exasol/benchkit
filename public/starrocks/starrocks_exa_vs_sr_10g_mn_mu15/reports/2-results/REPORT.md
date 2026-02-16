# Exasol vs StarRocks: TPC-H SF10 (Multi-Node 3, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:35:12


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 10.

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
- **exasol** was the fastest overall with **1581.2ms** median runtime
- **starrocks** was **5.6×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |    899.9 |      5900.4 | exasol   |
| Join-Heavy         |   1615.9 |      8482.3 | exasol   |
| Complex Analytical |   2492.9 |     11958.9 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        8308.2 |         85849.7 |   10.33 |      0.1  | False    |
| Q02     | exasol            | starrocks           |         760.7 |          2087.5 |    2.74 |      0.36 | False    |
| Q03     | exasol            | starrocks           |        1896.5 |          9155.7 |    4.83 |      0.21 | False    |
| Q04     | exasol            | starrocks           |         993   |          6024.7 |    6.07 |      0.16 | False    |
| Q05     | exasol            | starrocks           |        2970.1 |          9069.6 |    3.05 |      0.33 | False    |
| Q06     | exasol            | starrocks           |         464.9 |          2423.5 |    5.21 |      0.19 | False    |
| Q07     | exasol            | starrocks           |       14719.8 |         11958.9 |    0.81 |      1.23 | True     |
| Q08     | exasol            | starrocks           |        1287   |          4371.3 |    3.4  |      0.29 | False    |
| Q09     | exasol            | starrocks           |       18024.4 |         20254.2 |    1.12 |      0.89 | False    |
| Q10     | exasol            | starrocks           |        3440.5 |         14085.9 |    4.09 |      0.24 | False    |
| Q11     | exasol            | starrocks           |         596.9 |          1672.7 |    2.8  |      0.36 | False    |
| Q12     | exasol            | starrocks           |        1739.8 |         11904.3 |    6.84 |      0.15 | False    |
| Q13     | exasol            | starrocks           |       17134.3 |         45158   |    2.64 |      0.38 | False    |
| Q14     | exasol            | starrocks           |         899.9 |          5900.4 |    6.56 |      0.15 | False    |
| Q15     | exasol            | starrocks           |        1032   |          4521   |    4.38 |      0.23 | False    |
| Q16     | exasol            | starrocks           |        2492.9 |          2766   |    1.11 |      0.9  | False    |
| Q17     | exasol            | starrocks           |         678.5 |          4311.3 |    6.35 |      0.16 | False    |
| Q18     | exasol            | starrocks           |        4279.5 |         39779.7 |    9.3  |      0.11 | False    |
| Q19     | exasol            | starrocks           |         476.6 |          2785.2 |    5.84 |      0.17 | False    |
| Q20     | exasol            | starrocks           |        1499   |          5154.3 |    3.44 |      0.29 | False    |
| Q21     | exasol            | starrocks           |        2508.4 |         51328.6 |   20.46 |      0.05 | False    |
| Q22     | exasol            | starrocks           |         897.7 |          5448.5 |    6.07 |      0.16 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    452.5 |      5 |      8308.2 |    8800.4 |   5277.7 |   3522.7 |  14741.2 |
| Q01     | starrocks |   6022.1 |      5 |     85849.7 |   80030.6 |  50655.2 |   5222.9 | 147037   |
| Q02     | exasol    |    170.1 |      5 |       760.7 |     891   |    243.1 |    687.1 |   1267.2 |
| Q02     | starrocks |    494.6 |      5 |      2087.5 |    3476.9 |   2829.4 |   1258.6 |   7860.3 |
| Q03     | exasol    |    356.4 |      5 |      1896.5 |    2330.8 |    732.4 |   1777   |   3477.1 |
| Q03     | starrocks |   1822.3 |      5 |      9155.7 |   14236.8 |   7434.9 |   8781.2 |  24833.6 |
| Q04     | exasol    |    128   |      5 |       993   |     955.9 |    476.7 |    255.5 |   1595.1 |
| Q04     | starrocks |    845.7 |      5 |      6024.7 |   10010.3 |   6607.1 |   3864.5 |  18492.2 |
| Q05     | exasol    |    388.6 |      5 |      2970.1 |    2629.3 |   1640.2 |    321.1 |   4304.6 |
| Q05     | starrocks |   1437.5 |      5 |      9069.6 |    8673.1 |   2087.2 |   6379.9 |  11203.2 |
| Q06     | exasol    |     42.9 |      5 |       464.9 |     429.3 |    372.9 |     47.2 |    911.2 |
| Q06     | starrocks |    515.1 |      5 |      2423.5 |    4432.2 |   3428.9 |   1762.6 |   9166.2 |
| Q07     | exasol    |    504.3 |      5 |     14719.8 |   12139.5 |   5569.4 |   2606.7 |  15987.7 |
| Q07     | starrocks |   1265.5 |      5 |     11958.9 |   15475.7 |  10152   |   3848.6 |  27075.4 |
| Q08     | exasol    |    224.1 |      5 |      1287   |    1359.5 |    784.2 |    238   |   2115.1 |
| Q08     | starrocks |   1593.9 |      5 |      4371.3 |    5054.7 |   3026.6 |   1923.8 |   9572.9 |
| Q09     | exasol    |   1317.3 |      5 |     18024.4 |   16586.1 |   3175   |  11935.6 |  19882.6 |
| Q09     | starrocks |   2634   |      5 |     20254.2 |   23102.2 |  12298.6 |   9331.3 |  42864.8 |
| Q10     | exasol    |    329.2 |      5 |      3440.5 |    8923   |   9163   |   1567.2 |  19999.1 |
| Q10     | starrocks |   2585.7 |      5 |     14085.9 |   13241.1 |   4452.8 |   6536.8 |  17564   |
| Q11     | exasol    |     97.3 |      5 |       596.9 |     583   |    368.5 |     96.6 |   1004.8 |
| Q11     | starrocks |    367.4 |      5 |      1672.7 |    2896.2 |   3024.6 |    870.6 |   8148.4 |
| Q12     | exasol    |    238.8 |      5 |      1739.8 |    3789.3 |   4659.8 |    170.3 |  11574.3 |
| Q12     | starrocks |    988   |      5 |     11904.3 |   11439.9 |   6857.1 |   3208.2 |  19758.2 |
| Q13     | exasol    |    902.2 |      5 |     17134.3 |   19083.9 |  14381.7 |   2496.3 |  41918.7 |
| Q13     | starrocks |   2075.2 |      5 |     45158   |   41771.4 |  10622.7 |  25198.2 |  53862.5 |
| Q14     | exasol    |    343.3 |      5 |       899.9 |    1064.7 |    800   |    201.8 |   2097.7 |
| Q14     | starrocks |   1078.1 |      5 |      5900.4 |    6967.5 |   4769.2 |   1679.2 |  14678.8 |
| Q15     | exasol    |    262.3 |      5 |      1032   |    1312.6 |    929.5 |    563   |   2901.8 |
| Q15     | starrocks |    528.8 |      5 |      4521   |    5505.1 |   3591   |   1161.3 |   9547.4 |
| Q16     | exasol    |    673.9 |      5 |      2492.9 |    2680.5 |   2080.2 |    562.7 |   5436.4 |
| Q16     | starrocks |    643.8 |      5 |      2766   |    3387.5 |   1931.8 |   2149.1 |   6781.5 |
| Q17     | exasol    |    104.1 |      5 |       678.5 |     752.4 |    451.1 |    207   |   1453   |
| Q17     | starrocks |   1025.5 |      5 |      4311.3 |    6692.9 |   4915.1 |   1906.8 |  12560.5 |
| Q18     | exasol    |    299.3 |      5 |      4279.5 |    5916.4 |   7179.1 |    313.7 |  18128.8 |
| Q18     | starrocks |   2572.8 |      5 |     39779.7 |   50227.5 |  39948.1 |  16458.2 | 118473   |
| Q19     | exasol    |     72.1 |      5 |       476.6 |     533   |    211.1 |    262.5 |    796   |
| Q19     | starrocks |   1026.7 |      5 |      2785.2 |    5054.2 |   5542.8 |   1461.1 |  14753.1 |
| Q20     | exasol    |    192.7 |      5 |      1499   |    1832.9 |   1706.9 |    564.1 |   4732.3 |
| Q20     | starrocks |   1502.9 |      5 |      5154.3 |    9068.6 |   9198.7 |   1970.2 |  24517.7 |
| Q21     | exasol    |    283.8 |      5 |      2508.4 |    3435.3 |   2546.5 |   1810.3 |   7949   |
| Q21     | starrocks |   4400.7 |      5 |     51328.6 |   58719.7 |  50643   |  13805.7 | 135869   |
| Q22     | exasol    |     89.4 |      5 |       897.7 |    1065.8 |    342.7 |    682.1 |   1445.4 |
| Q22     | starrocks |    486   |      5 |      5448.5 |    5454   |   5154.8 |    411.4 |  12133.6 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1581.2ms
- Average: 4413.4ms
- Range: 47.2ms - 41918.7ms

**#2. Starrocks**
- Median: 8832.0ms
- Average: 17496.3ms
- Range: 411.4ms - 147036.6ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 5413.4 | 219.9 | 47.2 | 41918.7 |
| 1 | 8 | 4617.4 | 1130.1 | 262.5 | 17134.3 |
| 10 | 7 | 4301.9 | 803.1 | 476.6 | 19911.2 |
| 11 | 7 | 3752.1 | 903.5 | 796.0 | 15987.7 |
| 12 | 7 | 5460.3 | 1130.0 | 255.5 | 18024.4 |
| 13 | 7 | 5336.0 | 1821.5 | 72.1 | 15551.1 |
| 14 | 7 | 5137.5 | 1499.0 | 440.9 | 14719.8 |
| 2 | 8 | 4276.6 | 2104.2 | 620.2 | 14741.2 |
| 3 | 8 | 4669.2 | 2686.1 | 564.1 | 19882.6 |
| 4 | 8 | 2380.6 | 1513.4 | 596.9 | 7949.0 |
| 5 | 7 | 5521.6 | 2188.7 | 859.6 | 17786.7 |
| 6 | 7 | 5284.1 | 1567.2 | 356.1 | 19999.1 |
| 7 | 7 | 1680.5 | 1291.0 | 688.9 | 4279.5 |
| 8 | 7 | 4410.0 | 1810.3 | 207.0 | 18240.4 |
| 9 | 7 | 4060.9 | 1032.0 | 651.1 | 18128.8 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 219.9ms
- **Worst stream median:** 2686.1ms
- **Performance variance:** 1121.5% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 14497.6 | 8111.4 | 1057.7 | 45158.0 |
| 1 | 8 | 20195.5 | 6907.0 | 1461.1 | 72596.5 |
| 10 | 7 | 15100.5 | 12560.5 | 2087.5 | 39283.2 |
| 11 | 7 | 10165.2 | 9378.0 | 6024.7 | 14753.1 |
| 12 | 7 | 16363.1 | 16458.2 | 1258.6 | 39779.7 |
| 13 | 7 | 14015.4 | 14085.9 | 1762.6 | 25198.2 |
| 14 | 7 | 22567.7 | 5154.3 | 1810.6 | 89447.3 |
| 2 | 8 | 21395.0 | 3662.1 | 411.4 | 147036.6 |
| 3 | 8 | 19681.2 | 9743.8 | 5425.8 | 85849.7 |
| 4 | 8 | 19823.7 | 3251.3 | 870.6 | 135869.4 |
| 5 | 7 | 20042.9 | 11384.6 | 2225.7 | 77331.5 |
| 6 | 7 | 14933.6 | 17564.0 | 2731.8 | 24833.6 |
| 7 | 7 | 20371.5 | 1831.5 | 1161.3 | 118473.0 |
| 8 | 7 | 18978.5 | 11391.4 | 1906.8 | 51328.6 |
| 9 | 7 | 13154.1 | 9166.2 | 3015.3 | 47902.2 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 1831.5ms
- **Worst stream median:** 17564.0ms
- **Performance variance:** 859.0% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

**Query Distribution Method:**
- Query distribution was **randomized** (seed: 42) for realistic concurrent user simulation


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
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