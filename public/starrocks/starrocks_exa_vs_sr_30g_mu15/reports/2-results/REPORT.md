# Exasol vs StarRocks: TPC-H SF30 (Single-Node, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:13:11


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **starrocks**

## Systems Under Test

### Exasol 2025.1.8


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** exasol 2025.1.8

### Starrocks 4.0.4


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** starrocks 4.0.4


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **4532.4ms** median runtime
- **starrocks** was **1.8×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |   3391.9 |      6099.7 | exasol   |
| Join-Heavy         |   3786   |      8916   | exasol   |
| Complex Analytical |  11352.9 |     12546.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |       20282.5 |        109887   |    5.42 |      0.18 | False    |
| Q02     | exasol            | starrocks           |         669.2 |          1835.6 |    2.74 |      0.36 | False    |
| Q03     | exasol            | starrocks           |       17468   |         12973.6 |    0.74 |      1.35 | True     |
| Q04     | exasol            | starrocks           |        2456.7 |          3956.3 |    1.61 |      0.62 | False    |
| Q05     | exasol            | starrocks           |       15414.4 |         19796   |    1.28 |      0.78 | False    |
| Q06     | exasol            | starrocks           |        1840.9 |          2996.4 |    1.63 |      0.61 | False    |
| Q07     | exasol            | starrocks           |       20826.6 |         19369.9 |    0.93 |      1.08 | True     |
| Q08     | exasol            | starrocks           |        2753.8 |          6262.9 |    2.27 |      0.44 | False    |
| Q09     | exasol            | starrocks           |       33013.6 |         90882   |    2.75 |      0.36 | False    |
| Q10     | exasol            | starrocks           |       17804.2 |         18506.5 |    1.04 |      0.96 | False    |
| Q11     | exasol            | starrocks           |        1540.8 |          1301.1 |    0.84 |      1.18 | True     |
| Q12     | exasol            | starrocks           |        5152.2 |         10671.9 |    2.07 |      0.48 | False    |
| Q13     | exasol            | starrocks           |       27910.7 |         80256.9 |    2.88 |      0.35 | False    |
| Q14     | exasol            | starrocks           |        3175.4 |          7840.3 |    2.47 |      0.41 | False    |
| Q15     | exasol            | starrocks           |        5012.5 |          4893.5 |    0.98 |      1.02 | True     |
| Q16     | exasol            | starrocks           |       11545.6 |          1315.5 |    0.11 |      8.78 | True     |
| Q17     | exasol            | starrocks           |         364.5 |          1984.8 |    5.45 |      0.18 | False    |
| Q18     | exasol            | starrocks           |       18005.4 |         23613.1 |    1.31 |      0.76 | False    |
| Q19     | exasol            | starrocks           |        1428.1 |          3218.3 |    2.25 |      0.44 | False    |
| Q20     | exasol            | starrocks           |        4872.1 |          3996.2 |    0.82 |      1.22 | True     |
| Q21     | exasol            | starrocks           |       19181.3 |         59616.1 |    3.11 |      0.32 | False    |
| Q22     | exasol            | starrocks           |        2831   |          1893.1 |    0.67 |      1.5  | True     |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1886.2 |      5 |     20282.5 |   18852.6 |   5254.6 |  11569.5 |  24712.8 |
| Q01     | starrocks |   8645   |      5 |    109887   |  107173   |  66694.6 |  27156.3 | 203874   |
| Q02     | exasol    |     88.5 |      5 |       669.2 |     680.1 |    136   |    559.3 |    904.5 |
| Q02     | starrocks |    606.9 |      5 |      1835.6 |    2024.9 |    588.1 |   1615.7 |   3056.7 |
| Q03     | exasol    |    733.3 |      5 |     17468   |   13871.6 |   7186.2 |   3485.3 |  20076.1 |
| Q03     | starrocks |   3110.1 |      5 |     12973.6 |   15272.6 |   4767.5 |  11034.1 |  23061.7 |
| Q04     | exasol    |    132.3 |      5 |      2456.7 |    2422.6 |   1119.1 |    790.5 |   3933.9 |
| Q04     | starrocks |   1596.1 |      5 |      3956.3 |    7771.6 |   8457.9 |   2071.2 |  22498.6 |
| Q05     | exasol    |    578.8 |      5 |     15414.4 |   13266.9 |   7242.7 |    550   |  18212.4 |
| Q05     | starrocks |   2827.3 |      5 |     19796   |   41550.4 |  38142.8 |  11406.8 |  92309.1 |
| Q06     | exasol    |     86.7 |      5 |      1840.9 |    1652.5 |   1401.8 |     85.1 |   3253   |
| Q06     | starrocks |   1327   |      5 |      2996.4 |    6960.1 |   7971   |   1812.9 |  20931.6 |
| Q07     | exasol    |    739.8 |      5 |     20826.6 |   18208.8 |   4661.1 |  11352.9 |  21884.2 |
| Q07     | starrocks |   3634.3 |      5 |     19369.9 |   21031.1 |  13250.7 |   8238   |  36746.1 |
| Q08     | exasol    |    168.6 |      5 |      2753.8 |    2362.5 |   1276.1 |    195.6 |   3379.2 |
| Q08     | starrocks |   2667.4 |      5 |      6262.9 |    6922   |   4179   |   2785.7 |  13845.3 |
| Q09     | exasol    |   2544.6 |      5 |     33013.6 |   34024.4 |   8801.9 |  24829.1 |  43571.1 |
| Q09     | starrocks |   5941.6 |      5 |     90882   |   77326.4 |  49751.2 |  10944.6 | 139073   |
| Q10     | exasol    |    796.6 |      5 |     17804.2 |   18856.9 |   2392.9 |  16688.8 |  22772.5 |
| Q10     | starrocks |   2766.3 |      5 |     18506.5 |   21646   |  17666.5 |   3850   |  51013.8 |
| Q11     | exasol    |    151.2 |      5 |      1540.8 |    1393.7 |    736.1 |    166   |   2042.9 |
| Q11     | starrocks |    365.5 |      5 |      1301.1 |    1628.3 |   1134.6 |    551   |   3198.6 |
| Q12     | exasol    |    178.5 |      5 |      5152.2 |    5159.4 |   3954.2 |    308.5 |  11137   |
| Q12     | starrocks |   1773.6 |      5 |     10671.9 |   13323.1 |   9174.1 |   2146.9 |  22804.6 |
| Q13     | exasol    |   1792.4 |      5 |     27910.7 |   35756.7 |  31681.1 |   8330.3 |  90350.8 |
| Q13     | starrocks |   3903.7 |      5 |     80256.9 |   63855.4 |  27283.2 |  23270.2 |  84196.7 |
| Q14     | exasol    |    176.2 |      5 |      3175.4 |    3018.7 |   2200.3 |    274.2 |   6249.9 |
| Q14     | starrocks |   1374   |      5 |      7840.3 |   11794   |  10402.3 |   2315.7 |  28550.7 |
| Q15     | exasol    |    408.4 |      5 |      5012.5 |    8386.6 |   6790   |   3119.7 |  18904.3 |
| Q15     | starrocks |   1350.6 |      5 |      4893.5 |    8440.7 |  11287   |   1498.9 |  28342   |
| Q16     | exasol    |    678.2 |      5 |     11545.6 |    9369.1 |   6587.5 |   1901   |  15399.3 |
| Q16     | starrocks |    933.8 |      5 |      1315.5 |    3154.5 |   3980.9 |   1067.4 |  10247.1 |
| Q17     | exasol    |     28.3 |      5 |       364.5 |     402.8 |    200.9 |    155.4 |    681.5 |
| Q17     | starrocks |   1360.6 |      5 |      1984.8 |    2683.3 |   1225.2 |   1502   |   4287.2 |
| Q18     | exasol    |   1141   |      5 |     18005.4 |   13353.5 |   9175.7 |   1187.2 |  21300.2 |
| Q18     | starrocks |   4639.7 |      5 |     23613.1 |   49998.9 |  63319.5 |  12546.4 | 162713   |
| Q19     | exasol    |     53.5 |      5 |      1428.1 |    1373.7 |    257.9 |   1120.7 |   1735.2 |
| Q19     | starrocks |   2250.1 |      5 |      3218.3 |    4309   |   2333.2 |   2029.9 |   7178   |
| Q20     | exasol    |    370   |      5 |      4872.1 |    6913.5 |   5846.9 |   1806.3 |  16430.9 |
| Q20     | starrocks |   1952.3 |      5 |      3996.2 |    9267.1 |  13458.2 |   2073.2 |  33287.3 |
| Q21     | exasol    |   1062.7 |      5 |     19181.3 |   15049.9 |   7837.1 |   6401.7 |  23308.4 |
| Q21     | starrocks |   9566.9 |      5 |     59616.1 |  102182   |  86402.6 |  43454.8 | 249316   |
| Q22     | exasol    |    229.7 |      5 |      2831   |    2847.7 |    859.1 |   1953   |   4192.7 |
| Q22     | starrocks |    659.5 |      5 |      1893.1 |    2341.4 |   1149.6 |   1368.5 |   4235.5 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 4532.4ms
- Average: 10328.4ms
- Range: 85.1ms - 90350.8ms

**#2. Starrocks**
- Median: 8237.7ms
- Average: 26393.4ms
- Range: 551.0ms - 249315.6ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 11639.7 | 291.4 | 85.1 | 90350.8 |
| 1 | 8 | 9762.7 | 2733.3 | 559.3 | 27910.7 |
| 10 | 7 | 9051.7 | 3119.7 | 364.5 | 30208.7 |
| 11 | 7 | 8347.5 | 4192.7 | 1735.2 | 21602.9 |
| 12 | 7 | 11876.8 | 5930.7 | 669.2 | 43571.1 |
| 13 | 7 | 12419.5 | 15377.3 | 362.3 | 26200.6 |
| 14 | 7 | 11061.6 | 4872.1 | 1126.1 | 22090.4 |
| 2 | 8 | 8522.9 | 3181.1 | 303.7 | 24712.8 |
| 3 | 8 | 11095.5 | 7311.1 | 1806.3 | 33013.6 |
| 4 | 8 | 8019.8 | 4154.1 | 681.5 | 19448.7 |
| 5 | 7 | 12724.0 | 9311.9 | 1901.0 | 24829.1 |
| 6 | 7 | 10286.9 | 5751.5 | 1858.6 | 22772.5 |
| 7 | 7 | 9738.6 | 6249.9 | 681.6 | 21300.2 |
| 8 | 7 | 11627.8 | 6909.5 | 155.4 | 42507.8 |
| 9 | 7 | 9122.3 | 3391.9 | 1840.9 | 20343.9 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 291.4ms
- **Worst stream median:** 15377.3ms
- **Performance variance:** 5177.9% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 18942.8 | 9256.1 | 1301.1 | 83667.7 |
| 1 | 8 | 30522.2 | 4778.8 | 2029.9 | 127833.2 |
| 10 | 7 | 15719.8 | 7178.0 | 1835.6 | 47885.7 |
| 11 | 7 | 19898.3 | 3088.7 | 1893.1 | 92309.1 |
| 12 | 7 | 25059.0 | 12546.4 | 1161.4 | 99866.2 |
| 13 | 7 | 20930.0 | 19796.0 | 2960.0 | 45866.2 |
| 14 | 7 | 33281.9 | 8238.0 | 4271.5 | 109887.2 |
| 2 | 8 | 32752.7 | 6575.1 | 1368.5 | 203873.5 |
| 3 | 8 | 28829.5 | 15535.6 | 3198.6 | 90882.0 |
| 4 | 8 | 32740.9 | 1824.5 | 551.0 | 249315.6 |
| 5 | 7 | 36475.4 | 22498.6 | 1315.5 | 110097.8 |
| 6 | 7 | 13768.6 | 18506.5 | 1498.9 | 23061.7 |
| 7 | 7 | 28971.2 | 2707.1 | 1615.7 | 162713.0 |
| 8 | 7 | 37438.9 | 10247.1 | 1703.9 | 139073.0 |
| 9 | 7 | 18881.3 | 5791.3 | 1981.3 | 72619.9 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 1824.5ms
- **Worst stream median:** 22498.6ms
- **Performance variance:** 1133.2% difference between fastest and slowest streams
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