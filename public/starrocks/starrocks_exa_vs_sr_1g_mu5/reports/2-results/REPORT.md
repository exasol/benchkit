# Exasol vs StarRocks: TPC-H SF1 (Single-Node, 5 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 10:53:32


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
- **exasol** was the fastest overall with **178.4ms** median runtime
- **starrocks** was **3.2×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |    126.3 |       430   | exasol   |
| Join-Heavy         |    224.3 |       635.2 | exasol   |
| Complex Analytical |    285.7 |       628.7 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         562.8 |           904.9 |    1.61 |      0.62 | False    |
| Q02     | exasol            | starrocks           |         240.5 |           559.7 |    2.33 |      0.43 | False    |
| Q03     | exasol            | starrocks           |         173.2 |           463   |    2.67 |      0.37 | False    |
| Q04     | exasol            | starrocks           |          86.6 |           626   |    7.23 |      0.14 | False    |
| Q05     | exasol            | starrocks           |         203.8 |           533.5 |    2.62 |      0.38 | False    |
| Q06     | exasol            | starrocks           |          85.2 |           382.5 |    4.49 |      0.22 | False    |
| Q07     | exasol            | starrocks           |         258.9 |           941.7 |    3.64 |      0.27 | False    |
| Q08     | exasol            | starrocks           |         132   |           986.9 |    7.48 |      0.13 | False    |
| Q09     | exasol            | starrocks           |         539.5 |          1006.1 |    1.86 |      0.54 | False    |
| Q10     | exasol            | starrocks           |         473.2 |           866.7 |    1.83 |      0.55 | False    |
| Q11     | exasol            | starrocks           |         225.3 |           324   |    1.44 |      0.7  | False    |
| Q12     | exasol            | starrocks           |         156.6 |           723   |    4.62 |      0.22 | False    |
| Q13     | exasol            | starrocks           |         653.6 |           519   |    0.79 |      1.26 | True     |
| Q14     | exasol            | starrocks           |          67.3 |           352.2 |    5.23 |      0.19 | False    |
| Q15     | exasol            | starrocks           |         121.8 |           380.9 |    3.13 |      0.32 | False    |
| Q16     | exasol            | starrocks           |         378.1 |           851.2 |    2.25 |      0.44 | False    |
| Q17     | exasol            | starrocks           |          53.2 |           509.7 |    9.58 |      0.1  | False    |
| Q18     | exasol            | starrocks           |         345.7 |          1772.8 |    5.13 |      0.2  | False    |
| Q19     | exasol            | starrocks           |          85.6 |           331.4 |    3.87 |      0.26 | False    |
| Q20     | exasol            | starrocks           |         195.5 |           429.5 |    2.2  |      0.46 | False    |
| Q21     | exasol            | starrocks           |         319.9 |          2133.7 |    6.67 |      0.15 | False    |
| Q22     | exasol            | starrocks           |         157.5 |           296.2 |    1.88 |      0.53 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    134.3 |      5 |       562.8 |     568.6 |    156.9 |    334.8 |    751.7 |
| Q01     | starrocks |    877.5 |      5 |       904.9 |     989.3 |    368.7 |    698.6 |   1611.6 |
| Q02     | exasol    |     55.1 |      5 |       240.5 |     238.5 |    116.3 |     93.8 |    377.7 |
| Q02     | starrocks |    568.6 |      5 |       559.7 |     653.3 |    213.9 |    519.2 |   1031.3 |
| Q03     | exasol    |     47.3 |      5 |       173.2 |     268.3 |    197.9 |     45.9 |    506.5 |
| Q03     | starrocks |    272.1 |      5 |       463   |     466.6 |     96.3 |    318.6 |    576.6 |
| Q04     | exasol    |     18.3 |      5 |        86.6 |      98.2 |     39.9 |     60.3 |    150.2 |
| Q04     | starrocks |    184.1 |      5 |       626   |     692.3 |    196.6 |    472.4 |    901.4 |
| Q05     | exasol    |     55.8 |      5 |       203.8 |     189.5 |     39.6 |    140.5 |    225.4 |
| Q05     | starrocks |    272.9 |      5 |       533.5 |     614.8 |    168.8 |    469.8 |    894.8 |
| Q06     | exasol    |     11.5 |      5 |        85.2 |      65.6 |     35   |     10.4 |     92.4 |
| Q06     | starrocks |     65   |      5 |       382.5 |     374   |    108.8 |    219.9 |    509.2 |
| Q07     | exasol    |     49.9 |      5 |       258.9 |     252.1 |    113.6 |    131.1 |    416.8 |
| Q07     | starrocks |    279.1 |      5 |       941.7 |     846.2 |    176.5 |    564   |    989.9 |
| Q08     | exasol    |     25.8 |      5 |       132   |     114.8 |     56.1 |     25.8 |    162.3 |
| Q08     | starrocks |    347.8 |      5 |       986.9 |     887.4 |    421.4 |    350   |   1340.6 |
| Q09     | exasol    |    108.9 |      5 |       539.5 |     527   |     71.2 |    424.1 |    610.9 |
| Q09     | starrocks |    379.1 |      5 |      1006.1 |     992.1 |    292.1 |    605.5 |   1419.5 |
| Q10     | exasol    |     56.5 |      5 |       473.2 |     448.9 |    198.3 |    207.1 |    720.9 |
| Q10     | starrocks |    295.5 |      5 |       866.7 |     935.2 |    520   |    332.3 |   1703.6 |
| Q11     | exasol    |     23.4 |      5 |       225.3 |     179.3 |    104.7 |     60.5 |    294.6 |
| Q11     | starrocks |    105.1 |      5 |       324   |     350.9 |    187   |    177.1 |    627   |
| Q12     | exasol    |     21.3 |      5 |       156.6 |     163.3 |     73.7 |     86.5 |    283.3 |
| Q12     | starrocks |    157.9 |      5 |       723   |     712.3 |    185.4 |    520.3 |    990.5 |
| Q13     | exasol    |    114.6 |      5 |       653.6 |    1117.4 |    875.9 |    500.2 |   2582.4 |
| Q13     | starrocks |    265.8 |      5 |       519   |     568.2 |    170.8 |    433.4 |    866.6 |
| Q14     | exasol    |     17.1 |      5 |        67.3 |     160.7 |    165.7 |     17.2 |    413.6 |
| Q14     | starrocks |    109.9 |      5 |       352.2 |     526.9 |    325.5 |    331.5 |   1094   |
| Q15     | exasol    |     24.2 |      5 |       121.8 |     125.5 |     79.1 |     23.6 |    243.9 |
| Q15     | starrocks |    161   |      5 |       380.9 |     391   |    111.1 |    271.6 |    563.7 |
| Q16     | exasol    |    102.9 |      5 |       378.1 |     381   |    194.4 |     92.7 |    594.3 |
| Q16     | starrocks |    312.6 |      5 |       851.2 |     843.6 |    249.7 |    589.2 |   1239   |
| Q17     | exasol    |     12.1 |      5 |        53.2 |      69.4 |     33.6 |     33.9 |    109.1 |
| Q17     | starrocks |    112.7 |      5 |       509.7 |     536.3 |    155.6 |    365.9 |    751.5 |
| Q18     | exasol    |     80.3 |      5 |       345.7 |     343.9 |     47   |    285.7 |    409   |
| Q18     | starrocks |    276   |      5 |      1772.8 |    2062.3 |    750.4 |   1472.5 |   3344.2 |
| Q19     | exasol    |     11.5 |      5 |        85.6 |      85.1 |     26.1 |     59.7 |    124.9 |
| Q19     | starrocks |    153.2 |      5 |       331.4 |     362.3 |    159   |    176.2 |    616.1 |
| Q20     | exasol    |     31   |      5 |       195.5 |     239.2 |     85.4 |    156.4 |    349.2 |
| Q20     | starrocks |    173   |      5 |       429.5 |     426.4 |     93.5 |    291.7 |    543.8 |
| Q21     | exasol    |     65.7 |      5 |       319.9 |     370.7 |    257.6 |     79.1 |    772.3 |
| Q21     | starrocks |    592.3 |      5 |      2133.7 |    2201.7 |    726.9 |   1205   |   2927.6 |
| Q22     | exasol    |     23.5 |      5 |       157.5 |     140.9 |     31.5 |     99.3 |    167.1 |
| Q22     | starrocks |     82.9 |      5 |       296.2 |     346.9 |    254   |    147.9 |    773.1 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 178.4ms
- Average: 279.5ms
- Range: 10.4ms - 2582.4ms

**#2. Starrocks**
- Median: 566.2ms
- Average: 762.7ms
- Range: 147.9ms - 3344.2ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 347.2 | 166.8 | 10.4 | 2582.4 |
| 1 | 22 | 224.6 | 157.9 | 64.7 | 653.6 |
| 2 | 22 | 278.7 | 213.4 | 53.2 | 662.8 |
| 3 | 22 | 276.9 | 232.8 | 49.4 | 594.3 |
| 4 | 22 | 270.0 | 180.7 | 60.5 | 772.3 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 157.9ms
- **Worst stream median:** 232.8ms
- **Performance variance:** 47.4% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 815.2 | 570.6 | 190.9 | 2886.3 |
| 1 | 22 | 583.0 | 519.6 | 176.2 | 1129.8 |
| 2 | 22 | 820.1 | 552.6 | 161.8 | 3344.2 |
| 3 | 22 | 798.2 | 743.0 | 328.2 | 2133.7 |
| 4 | 22 | 797.1 | 553.8 | 147.9 | 2927.6 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 519.6ms
- **Worst stream median:** 743.0ms
- **Performance variance:** 43.0% difference between fastest and slowest streams
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