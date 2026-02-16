# Concurrency Cliff - 15 Streams - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 15:33:26


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
- **exasol** was the fastest overall with **813.3ms** median runtime
- **clickhouse** was **12.6×** slower- Tested **220** total query executions across 22 different query types
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

| Query Type         |   clickhouse |   exasol | Winner   |
|--------------------|--------------|----------|----------|
| Aggregation        |       6914.8 |    707   | exasol   |
| Join-Heavy         |      10544.8 |   1020.4 | exasol   |
| Complex Analytical |      10823.8 |   1569.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        4689.1 |         14824   |    3.16 |      0.32 | False    |
| Q02     | exasol            | clickhouse          |         245.6 |          9436.7 |   38.42 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        1092.1 |          9723.9 |    8.9  |      0.11 | False    |
| Q04     | exasol            | clickhouse          |         356.8 |         15662.5 |   43.9  |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1466.5 |         10330.8 |    7.04 |      0.14 | False    |
| Q06     | exasol            | clickhouse          |         265.1 |          3272.3 |   12.34 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        1780.6 |          9981.2 |    5.61 |      0.18 | False    |
| Q08     | exasol            | clickhouse          |         337.2 |         14526.7 |   43.08 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        5784.2 |         10611.8 |    1.83 |      0.55 | False    |
| Q10     | exasol            | clickhouse          |        3064   |         13751.3 |    4.49 |      0.22 | False    |
| Q11     | exasol            | clickhouse          |         533.6 |          7452.8 |   13.97 |      0.07 | False    |
| Q12     | exasol            | clickhouse          |         707   |         10204.8 |   14.43 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3959.6 |         15598.8 |    3.94 |      0.25 | False    |
| Q14     | exasol            | clickhouse          |         531.8 |          3139.4 |    5.9  |      0.17 | False    |
| Q15     | exasol            | clickhouse          |        1484   |          3458.1 |    2.33 |      0.43 | False    |
| Q16     | exasol            | clickhouse          |        2291.7 |          6661.7 |    2.91 |      0.34 | False    |
| Q17     | exasol            | clickhouse          |         120.5 |          9768.9 |   81.07 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3914.2 |         11617.6 |    2.97 |      0.34 | False    |
| Q19     | exasol            | clickhouse          |         191.1 |         25347.6 |  132.64 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         778   |         10928.8 |   14.05 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1810.6 |         11676   |    6.45 |      0.16 | False    |
| Q22     | exasol            | clickhouse          |         600   |          7371.3 |   12.29 |      0.08 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   1419   |      5 |     14824   |   12979.6 |   5769.3 |   3325.8 |  18401.7 |
| Q01     | exasol     |    479.5 |      5 |      4689.1 |    5137.5 |   4721.1 |    514.8 |  12946   |
| Q02     | clickhouse |    594.6 |      5 |      9436.7 |   10121.2 |   1673.7 |   8936.1 |  12989.5 |
| Q02     | exasol     |     51.9 |      5 |       245.6 |     223   |     78.4 |     92.4 |    283.5 |
| Q03     | clickhouse |    661   |      5 |      9723.9 |    8838.7 |   2963.2 |   4643.2 |  11863   |
| Q03     | exasol     |    176.1 |      5 |      1092.1 |    1332.3 |    699.7 |    703.7 |   2473.3 |
| Q04     | clickhouse |   2224.4 |      5 |     15662.5 |   16110.5 |   1670.1 |  14795.8 |  18982.7 |
| Q04     | exasol     |     39.7 |      5 |       356.8 |     310.3 |    170.5 |     82   |    513.4 |
| Q05     | clickhouse |    584.5 |      5 |     10330.8 |    9967.4 |    628.9 |   9053.3 |  10477.8 |
| Q05     | exasol     |    166.5 |      5 |      1466.5 |    1483.9 |    130.5 |   1367.6 |   1698.2 |
| Q06     | clickhouse |    103.2 |      5 |      3272.3 |    2604.7 |   1436.9 |    511.4 |   3813.6 |
| Q06     | exasol     |     25.6 |      5 |       265.1 |     230   |    109.7 |     82.6 |    350.9 |
| Q07     | clickhouse |    594.8 |      5 |      9981.2 |    8664   |   4067.3 |   1581.8 |  11322.7 |
| Q07     | exasol     |    150.6 |      5 |      1780.6 |    1663.7 |    479   |    916.1 |   2218.1 |
| Q08     | clickhouse |    919   |      5 |     14526.7 |   14372.3 |    961.4 |  13231.2 |  15543.6 |
| Q08     | exasol     |     51   |      5 |       337.2 |     415.1 |    216.3 |    159.2 |    686.5 |
| Q09     | clickhouse |    668.6 |      5 |     10611.8 |   10954.3 |   1313.6 |   9621.8 |  12829.3 |
| Q09     | exasol     |    548.2 |      5 |      5784.2 |    6020.8 |    786.6 |   5296.1 |   7156.5 |
| Q10     | clickhouse |    848.4 |      5 |     13751.3 |   13128.7 |   1969.8 |  11106.8 |  15696.8 |
| Q10     | exasol     |    279   |      5 |      3064   |    2991.1 |    125.4 |   2802.5 |   3084.1 |
| Q11     | clickhouse |    300.5 |      5 |      7452.8 |    8058.5 |   1607.3 |   6978   |  10833.2 |
| Q11     | exasol     |     92.6 |      5 |       533.6 |     518.6 |     47.9 |    462.2 |    574.3 |
| Q12     | clickhouse |    566.4 |      5 |     10204.8 |   10455.5 |    693.7 |   9653.6 |  11428.2 |
| Q12     | exasol     |     53.1 |      5 |       707   |     702.9 |     89.5 |    582.5 |    832   |
| Q13     | clickhouse |   1764.7 |      5 |     15598.8 |   14154.4 |   4939.5 |   5653.3 |  17717.4 |
| Q13     | exasol     |    379.4 |      5 |      3959.6 |    3760.2 |   1502.2 |   1712.5 |   5529.2 |
| Q14     | clickhouse |    107   |      5 |      3139.4 |    3183.9 |    374.3 |   2706.4 |   3717.6 |
| Q14     | exasol     |     46.8 |      5 |       531.8 |     574.9 |    151.9 |    412.6 |    793.5 |
| Q15     | clickhouse |    168.9 |      5 |      3458.1 |    3492.2 |    623   |   2657.1 |   4224.1 |
| Q15     | exasol     |    157.1 |      5 |      1484   |    1340.3 |    296.2 |    888.6 |   1576.8 |
| Q16     | clickhouse |    363.6 |      5 |      6661.7 |    6441.1 |   1814.7 |   4498.8 |   8349.3 |
| Q16     | exasol     |    302.5 |      5 |      2291.7 |    1798.4 |    970.9 |    735.6 |   2861.3 |
| Q17     | clickhouse |    556.2 |      5 |      9768.9 |    9708.2 |   2161   |   6310.5 |  12142.1 |
| Q17     | exasol     |     17.4 |      5 |       120.5 |     112.5 |     24.2 |     76.8 |    139.2 |
| Q18     | clickhouse |    664.3 |      5 |     11617.6 |   11681.1 |   2460.8 |   8626.6 |  15436.7 |
| Q18     | exasol     |    321.5 |      5 |      3914.2 |    3640   |   1036.2 |   1840.8 |   4408.7 |
| Q19     | clickhouse |   2928.3 |      5 |     25347.6 |   21840.8 |   8379.1 |   6914.8 |  26380.7 |
| Q19     | exasol     |     18.1 |      5 |       191.1 |     173.6 |     50.7 |    113.1 |    237.4 |
| Q20     | clickhouse |    785.7 |      5 |     10928.8 |    9961.6 |   3508.5 |   5485.3 |  14591.3 |
| Q20     | exasol     |    194.9 |      5 |       778   |    1013.1 |    379.6 |    713.7 |   1499.6 |
| Q21     | clickhouse |    796.4 |      5 |     11676   |   12499.6 |   1895.6 |  10623.3 |  14792   |
| Q21     | exasol     |    226.8 |      5 |      1810.6 |    1800   |    585.6 |   1187.4 |   2619.1 |
| Q22     | clickhouse |    286.2 |      5 |      7371.3 |    7259   |   1082.9 |   5714.5 |   8756.7 |
| Q22     | exasol     |     62.4 |      5 |       600   |     522.1 |    301.5 |    170.8 |    853.4 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 813.3ms
- Average: 1625.6ms
- Range: 76.8ms - 12946.0ms

**#2. Clickhouse**
- Median: 10267.8ms
- Average: 10294.4ms
- Range: 511.4ms - 26380.7ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 8016.1 | 7818.5 | 2706.4 | 14526.7 |
| 1 | 8 | 10637.2 | 9648.8 | 3027.3 | 18982.7 |
| 10 | 7 | 11704.8 | 10928.8 | 2657.1 | 25347.6 |
| 11 | 7 | 11360.2 | 9981.2 | 4224.1 | 26140.7 |
| 12 | 7 | 11447.1 | 10823.8 | 8349.3 | 15436.7 |
| 13 | 7 | 10749.9 | 10611.8 | 1726.6 | 17391.8 |
| 14 | 7 | 11951.1 | 13579.1 | 511.4 | 26380.7 |
| 2 | 8 | 10024.7 | 9625.6 | 3325.8 | 15543.6 |
| 3 | 8 | 9818.3 | 9629.0 | 3328.7 | 15638.5 |
| 4 | 8 | 10119.7 | 10243.4 | 6310.5 | 14980.9 |
| 5 | 7 | 11323.5 | 11172.1 | 4660.8 | 14795.8 |
| 6 | 7 | 10952.6 | 11106.8 | 3458.1 | 15696.8 |
| 7 | 7 | 9451.6 | 8936.1 | 3139.4 | 24420.1 |
| 8 | 7 | 10422.8 | 10792.3 | 4498.8 | 14792.0 |
| 9 | 7 | 6844.8 | 7371.3 | 3272.3 | 11900.7 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 7371.3ms
- **Worst stream median:** 13579.1ms
- **Performance variance:** 84.2% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 1384.8 | 627.1 | 265.1 | 4408.7 |
| 1 | 8 | 1527.4 | 619.8 | 92.4 | 4689.1 |
| 10 | 7 | 1428.9 | 888.6 | 125.1 | 5529.2 |
| 11 | 7 | 1054.1 | 853.4 | 237.4 | 2218.1 |
| 12 | 7 | 2058.3 | 1834.3 | 82.0 | 5784.2 |
| 13 | 7 | 2014.0 | 1712.5 | 82.6 | 5296.1 |
| 14 | 7 | 1751.3 | 713.7 | 113.1 | 4965.4 |
| 2 | 8 | 1921.2 | 275.2 | 120.5 | 12946.0 |
| 3 | 8 | 1772.6 | 805.0 | 462.2 | 6476.0 |
| 4 | 8 | 1250.5 | 652.2 | 139.2 | 3064.0 |
| 5 | 7 | 2043.9 | 1187.4 | 198.3 | 5391.0 |
| 6 | 7 | 1543.4 | 1191.8 | 356.8 | 2921.5 |
| 7 | 7 | 1250.8 | 793.5 | 131.3 | 4247.9 |
| 8 | 7 | 1931.7 | 1302.8 | 76.8 | 7156.5 |
| 9 | 7 | 1490.5 | 1484.0 | 298.3 | 3914.2 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 275.2ms
- **Worst stream median:** 1834.3ms
- **Performance variance:** 566.4% difference between fastest and slowest streams
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