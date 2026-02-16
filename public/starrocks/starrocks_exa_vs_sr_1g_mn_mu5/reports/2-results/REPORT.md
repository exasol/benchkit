# Exasol vs StarRocks: TPC-H SF1 (Multi-Node 3, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:09:55


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
- **exasol** was the fastest overall with **240.0ms** median runtime
- **starrocks** was **2.8×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |    158.6 |       453.6 | exasol   |
| Join-Heavy         |    296.2 |       820.6 | exasol   |
| Complex Analytical |    312.1 |       703   | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         179.3 |           932.3 |    5.2  |      0.19 | False    |
| Q02     | exasol            | starrocks           |         397.1 |           953   |    2.4  |      0.42 | False    |
| Q03     | exasol            | starrocks           |         226.2 |           593.1 |    2.62 |      0.38 | False    |
| Q04     | exasol            | starrocks           |         137.6 |           502.9 |    3.65 |      0.27 | False    |
| Q05     | exasol            | starrocks           |         335   |           758.9 |    2.27 |      0.44 | False    |
| Q06     | exasol            | starrocks           |          52.3 |           255.4 |    4.88 |      0.2  | False    |
| Q07     | exasol            | starrocks           |         312.1 |           747.3 |    2.39 |      0.42 | False    |
| Q08     | exasol            | starrocks           |         239.7 |           875.8 |    3.65 |      0.27 | False    |
| Q09     | exasol            | starrocks           |         635   |           785.4 |    1.24 |      0.81 | False    |
| Q10     | exasol            | starrocks           |         320.2 |           881.8 |    2.75 |      0.36 | False    |
| Q11     | exasol            | starrocks           |         252.4 |           585.4 |    2.32 |      0.43 | False    |
| Q12     | exasol            | starrocks           |         152.9 |           509.5 |    3.33 |      0.3  | False    |
| Q13     | exasol            | starrocks           |         340.2 |           575.5 |    1.69 |      0.59 | False    |
| Q14     | exasol            | starrocks           |         186.9 |           380.7 |    2.04 |      0.49 | False    |
| Q15     | exasol            | starrocks           |         191.3 |           453.6 |    2.37 |      0.42 | False    |
| Q16     | exasol            | starrocks           |         471.9 |          1253.3 |    2.66 |      0.38 | False    |
| Q17     | exasol            | starrocks           |         116.8 |           455.6 |    3.9  |      0.26 | False    |
| Q18     | exasol            | starrocks           |         622.2 |          1830.9 |    2.94 |      0.34 | False    |
| Q19     | exasol            | starrocks           |         113.8 |           448.5 |    3.94 |      0.25 | False    |
| Q20     | exasol            | starrocks           |         224.1 |           651.8 |    2.91 |      0.34 | False    |
| Q21     | exasol            | starrocks           |         240.3 |          1903   |    7.92 |      0.13 | False    |
| Q22     | exasol            | starrocks           |         146.7 |           476.4 |    3.25 |      0.31 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |     67.1 |      5 |       179.3 |     212.9 |     99.3 |    145.8 |    387.5 |
| Q01     | starrocks |    667.8 |      5 |       932.3 |    1005.3 |    402.9 |    643.5 |   1592   |
| Q02     | exasol    |    126   |      5 |       397.1 |     383.8 |    138.1 |    232.2 |    556   |
| Q02     | starrocks |    414.1 |      5 |       953   |     995.1 |    203.2 |    794.3 |   1251.9 |
| Q03     | exasol    |     63.3 |      5 |       226.2 |     215   |     90.4 |     63   |    288.2 |
| Q03     | starrocks |    232.6 |      5 |       593.1 |     611.5 |    213.8 |    317.8 |    915.5 |
| Q04     | exasol    |     35.8 |      5 |       137.6 |     172.4 |    100.8 |    108.8 |    349.3 |
| Q04     | starrocks |    180.8 |      5 |       502.9 |     508.5 |    176.3 |    247   |    714.3 |
| Q05     | exasol    |    118.6 |      5 |       335   |     382.6 |    201.8 |    251.5 |    736   |
| Q05     | starrocks |    165.6 |      5 |       758.9 |     775.6 |    132   |    659.7 |    992.9 |
| Q06     | exasol    |     18.1 |      5 |        52.3 |      69.6 |     47   |     18.4 |    137.1 |
| Q06     | starrocks |     78   |      5 |       255.4 |     220.9 |     80.9 |    119.8 |    300.3 |
| Q07     | exasol    |     94.7 |      5 |       312.1 |     354.8 |    108.9 |    253.1 |    536.4 |
| Q07     | starrocks |    204.5 |      5 |       747.3 |     756.1 |     62.9 |    693.3 |    842.7 |
| Q08     | exasol    |     77.1 |      5 |       239.7 |     293.9 |    164.3 |     77.8 |    482.7 |
| Q08     | starrocks |    231   |      5 |       875.8 |     787.3 |    223.7 |    393.7 |    930.3 |
| Q09     | exasol    |    174.5 |      5 |       635   |     712.3 |    172.5 |    573.2 |    965.8 |
| Q09     | starrocks |    252.1 |      5 |       785.4 |     753.8 |     97.8 |    611.2 |    850.8 |
| Q10     | exasol    |     79.8 |      5 |       320.2 |     324.1 |     70.7 |    268.6 |    441.9 |
| Q10     | starrocks |    276.3 |      5 |       881.8 |     955   |    165.9 |    786.1 |   1141.8 |
| Q11     | exasol    |     52   |      5 |       252.4 |     246.9 |     75.6 |    147.3 |    340.1 |
| Q11     | starrocks |    114.3 |      5 |       585.4 |     766.5 |    352   |    533.9 |   1362.5 |
| Q12     | exasol    |     37.3 |      5 |       152.9 |     183.6 |     65.1 |    125.9 |    290.1 |
| Q12     | starrocks |    152.4 |      5 |       509.5 |     531.4 |    167.1 |    334   |    752.5 |
| Q13     | exasol    |     66.4 |      5 |       340.2 |     758.7 |    888.1 |    313.9 |   2342.5 |
| Q13     | starrocks |    244.8 |      5 |       575.5 |     660.1 |    174.4 |    535.6 |    959.1 |
| Q14     | exasol    |     32.8 |      5 |       186.9 |     176.2 |     75.9 |     81.4 |    267.1 |
| Q14     | starrocks |    111.8 |      5 |       380.7 |     398.2 |     82.4 |    316.1 |    517.6 |
| Q15     | exasol    |     50.5 |      5 |       191.3 |     165.2 |     68.1 |     47.6 |    222.1 |
| Q15     | starrocks |    141.4 |      5 |       453.6 |     468.6 |    192.9 |    216.3 |    690   |
| Q16     | exasol    |    121.9 |      5 |       471.9 |     432.6 |    207.9 |    112.5 |    688.8 |
| Q16     | starrocks |    264.4 |      5 |      1253.3 |    1249.8 |    149.4 |   1070.5 |   1429.1 |
| Q17     | exasol    |     45.9 |      5 |       116.8 |     134.6 |     37.8 |    113.8 |    201.9 |
| Q17     | starrocks |    124.3 |      5 |       455.6 |     535.8 |    220.8 |    323.2 |    884.4 |
| Q18     | exasol    |    143.6 |      5 |       622.2 |     597.1 |    157.6 |    378.1 |    804.1 |
| Q18     | starrocks |    313.1 |      5 |      1830.9 |    2018.9 |    319.5 |   1727   |   2431.3 |
| Q19     | exasol    |     28.5 |      5 |       113.8 |     118.2 |     40   |     79   |    184.7 |
| Q19     | starrocks |    122.1 |      5 |       448.5 |     464   |    121.8 |    344.6 |    618.9 |
| Q20     | exasol    |     60.4 |      5 |       224.1 |     286.4 |    195.2 |    120.4 |    624.5 |
| Q20     | starrocks |    154.1 |      5 |       651.8 |     612.5 |    129.5 |    391   |    718.7 |
| Q21     | exasol    |     61.9 |      5 |       240.3 |     289.1 |    195.5 |     67.1 |    602.7 |
| Q21     | starrocks |    509.1 |      5 |      1903   |    2006.1 |    727   |   1116.8 |   2792.7 |
| Q22     | exasol    |     33.1 |      5 |       146.7 |     201.6 |    107   |    133.1 |    385.8 |
| Q22     | starrocks |    147.9 |      5 |       476.4 |     496.9 |     88.1 |    426.9 |    647   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 240.0ms
- Average: 305.1ms
- Range: 18.4ms - 2342.5ms

**#2. Starrocks**
- Median: 675.2ms
- Average: 799.0ms
- Range: 119.8ms - 2792.7ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 372.4 | 229.5 | 18.4 | 2342.5 |
| 1 | 22 | 242.6 | 215.5 | 79.0 | 474.0 |
| 2 | 22 | 311.3 | 235.9 | 81.4 | 653.1 |
| 3 | 22 | 301.6 | 256.9 | 43.9 | 813.8 |
| 4 | 22 | 297.5 | 243.2 | 52.3 | 736.0 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 215.5ms
- **Worst stream median:** 256.9ms
- **Performance variance:** 19.2% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **consistent** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 833.7 | 737.0 | 255.4 | 1903.0 |
| 1 | 22 | 682.7 | 631.0 | 316.1 | 1592.0 |
| 2 | 22 | 849.9 | 681.2 | 247.0 | 2431.3 |
| 3 | 22 | 822.5 | 726.2 | 119.8 | 2792.7 |
| 4 | 22 | 806.1 | 665.8 | 149.7 | 2688.9 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 631.0ms
- **Worst stream median:** 737.0ms
- **Performance variance:** 16.8% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **consistent** performance across streams

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