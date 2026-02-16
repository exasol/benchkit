# Minimum Viable Resources - 32GB - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-19 13:50:38


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

### Clickhouse 25.10.2.65


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (4 vCPUs)- **Memory:** 30.8GB RAM

**Software:**
- **Database:** clickhouse 25.10.2.65


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **1239.3ms** median runtime
- **clickhouse** was **9.3×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |       9656.6 |   1111.2 | exasol   |
| Join-Heavy         |      10619   |   1035.2 | exasol   |
| Complex Analytical |      13128.1 |   2933.1 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        8237   |         20281.9 |    2.46 |      0.41 | False    |
| Q02     | exasol            | clickhouse          |         344.9 |         10354.4 |   30.02 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        1444.2 |         12252.2 |    8.48 |      0.12 | False    |
| Q04     | exasol            | clickhouse          |         666   |         20709.8 |   31.1  |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2577.8 |         13133.8 |    5.09 |      0.2  | False    |
| Q06     | exasol            | clickhouse          |         437.7 |          4177.9 |    9.55 |      0.1  | False    |
| Q07     | exasol            | clickhouse          |        3253.9 |          9755.5 |    3    |      0.33 | False    |
| Q08     | exasol            | clickhouse          |         817.4 |          9263.7 |   11.33 |      0.09 | False    |
| Q09     | exasol            | clickhouse          |       12002   |         13917.5 |    1.16 |      0.86 | False    |
| Q10     | exasol            | clickhouse          |        3512.9 |         13128   |    3.74 |      0.27 | False    |
| Q11     | exasol            | clickhouse          |         673.6 |         10391.8 |   15.43 |      0.06 | False    |
| Q12     | exasol            | clickhouse          |        1111.2 |         11017.3 |    9.91 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        8062.2 |         15431.9 |    1.91 |      0.52 | False    |
| Q14     | exasol            | clickhouse          |         955.2 |          3168.3 |    3.32 |      0.3  | False    |
| Q15     | exasol            | clickhouse          |        1509   |          3454.3 |    2.29 |      0.44 | False    |
| Q16     | exasol            | clickhouse          |        2607.4 |          6592.5 |    2.53 |      0.4  | False    |
| Q17     | exasol            | clickhouse          |         157.9 |         12327.1 |   78.07 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        4408.1 |         17318.6 |    3.93 |      0.25 | False    |
| Q19     | exasol            | clickhouse          |         365.5 |         40416.5 |  110.58 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        1596.8 |         15068.2 |    9.44 |      0.11 | False    |
| Q21     | exasol            | clickhouse          |        5391   |          7869.1 |    1.46 |      0.69 | False    |
| Q22     | exasol            | clickhouse          |         913.4 |          7431.4 |    8.14 |      0.12 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   5455.2 |      5 |     20281.9 |   18932.9 |   4991.9 |  11901.3 |  23732.2 |
| Q01     | exasol     |   1884.6 |      5 |      8237   |    7387.9 |   3653.9 |   2983   |  12507.1 |
| Q02     | clickhouse |   2129   |      5 |     10354.4 |   10997.9 |   2426   |   8974.5 |  14935.1 |
| Q02     | exasol     |     80.2 |      5 |       344.9 |     291   |    116   |    123.2 |    408.5 |
| Q03     | clickhouse |   2535   |      5 |     12252.2 |   12075.2 |   2883.5 |   8692.9 |  14910   |
| Q03     | exasol     |    671.8 |      5 |      1444.2 |    2177.2 |   1495.4 |    680.6 |   4006.7 |
| Q04     | clickhouse |   4340.3 |      5 |     20709.8 |   20314.7 |   2477.4 |  16442.8 |  23140.5 |
| Q04     | exasol     |    129.4 |      5 |       666   |     681.4 |     79.3 |    572.6 |    767   |
| Q05     | clickhouse |   2275.2 |      5 |     13133.8 |   13006   |   1079.8 |  11842.1 |  14614.5 |
| Q05     | exasol     |    540.7 |      5 |      2577.8 |    2623.8 |   1245   |    854.7 |   4269.5 |
| Q06     | clickhouse |    328.8 |      5 |      4177.9 |    4166.8 |    230.8 |   3818.6 |   4429.8 |
| Q06     | exasol     |     84.8 |      5 |       437.7 |     385.6 |    258.4 |     85.3 |    700.2 |
| Q07     | clickhouse |   1692   |      5 |      9755.5 |   10210.2 |   1631.7 |   8686.7 |  12231.8 |
| Q07     | exasol     |    644   |      5 |      3253.9 |    3401   |    412.1 |   2933.1 |   3991.2 |
| Q08     | clickhouse |   1499.7 |      5 |      9263.7 |    8614.1 |   2300.6 |   4731.1 |  10846.2 |
| Q08     | exasol     |    157.6 |      5 |       817.4 |     722.7 |    193.8 |    383.8 |    840.2 |
| Q09     | clickhouse |   1705.3 |      5 |     13917.5 |   12126.5 |   3062.8 |   8187.5 |  15067.9 |
| Q09     | exasol     |   2316.7 |      5 |     12002   |   10900.2 |   1999.1 |   7702.5 |  12362   |
| Q10     | clickhouse |   2824.4 |      5 |     13128   |   13209.8 |    510   |  12833.9 |  14080.2 |
| Q10     | exasol     |    773.3 |      5 |      3512.9 |    3627.1 |    416.1 |   3187.1 |   4314   |
| Q11     | clickhouse |   1123.8 |      5 |     10391.8 |    9758   |   2344.4 |   7244.8 |  12431.6 |
| Q11     | exasol     |    142.9 |      5 |       673.6 |     672.2 |    359.4 |    222   |   1063.2 |
| Q12     | clickhouse |   1740.3 |      5 |     11017.3 |   10918.6 |   2007.9 |   8284.5 |  13250.6 |
| Q12     | exasol     |    176.3 |      5 |      1111.2 |    1141.9 |    342   |    757.3 |   1667.4 |
| Q13     | clickhouse |   3938.6 |      5 |     15431.9 |   16603.9 |   1793.4 |  15088.3 |  18670.9 |
| Q13     | exasol     |   1773.5 |      5 |      8062.2 |   10472.6 |   7648.4 |   3275.3 |  23488.5 |
| Q14     | clickhouse |    346.5 |      5 |      3168.3 |    3080.7 |    769.1 |   2246.8 |   4034   |
| Q14     | exasol     |    168.4 |      5 |       955.2 |    1014.4 |    199.1 |    788.7 |   1256.1 |
| Q15     | clickhouse |    345.1 |      5 |      3454.3 |    3328.7 |    632.6 |   2630.9 |   4206   |
| Q15     | exasol     |    370.8 |      5 |      1509   |    1642.2 |    755.9 |    737   |   2815.3 |
| Q16     | clickhouse |   1530.9 |      5 |      6592.5 |    6753.1 |   1057.3 |   5258.6 |   7982.3 |
| Q16     | exasol     |    649.3 |      5 |      2607.4 |    2510.7 |    861.4 |   1145.9 |   3472.6 |
| Q17     | clickhouse |   1981.8 |      5 |     12327.1 |   12142.9 |   1289.1 |  10721.3 |  13608.6 |
| Q17     | exasol     |     26.6 |      5 |       157.9 |     139.7 |     93.3 |     44.6 |    256.2 |
| Q18     | clickhouse |   3057   |      5 |     17318.6 |   17455.1 |   4771.8 |  11479.6 |  23587.4 |
| Q18     | exasol     |   1110.5 |      5 |      4408.1 |    4515.3 |    296.8 |   4250.8 |   5010.9 |
| Q19     | clickhouse |  11434.7 |      5 |     40416.5 |   37125.3 |  12888.3 |  14623.7 |  47060.1 |
| Q19     | exasol     |     51.2 |      5 |       365.5 |     310.7 |    129.1 |     95.1 |    415.6 |
| Q20     | clickhouse |   2458   |      5 |     15068.2 |   13873.1 |   3825.9 |   8024.2 |  17744.1 |
| Q20     | exasol     |    371.8 |      5 |      1596.8 |    1556.7 |    570.2 |    610.5 |   2095.1 |
| Q21     | clickhouse |   1851.4 |      5 |      7869.1 |    9572.2 |   2984.3 |   7421.3 |  14248.2 |
| Q21     | exasol     |    988.6 |      5 |      5391   |    4135.5 |   2366.3 |   1046.5 |   6206.6 |
| Q22     | clickhouse |    894.9 |      5 |      7431.4 |    6956.7 |   2708.7 |   2449.4 |   9463.7 |
| Q22     | exasol     |    212.1 |      5 |       913.4 |     927.1 |     85.3 |    830   |   1024   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 1239.3ms
- Average: 2783.5ms
- Range: 44.6ms - 23488.5ms

**#2. Clickhouse**
- Median: 11504.9ms
- Average: 12328.3ms
- Range: 2246.8ms - 47060.1ms


### Per-Stream Performance Analysis

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Clickhouse - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 12387.4 | 11504.9 | 2630.9 | 47060.1 |
| 1 | 22 | 13148.7 | 11767.8 | 2371.8 | 43430.5 |
| 2 | 22 | 12751.2 | 11755.0 | 3582.6 | 40095.6 |
| 3 | 22 | 11711.4 | 12289.7 | 2246.8 | 20281.9 |
| 4 | 22 | 11642.8 | 9442.4 | 3454.3 | 40416.5 |

**Stream Performance Analysis for Clickhouse:**
- **Best stream median:** 9442.4ms
- **Worst stream median:** 12289.7ms
- **Performance variance:** 30.2% difference between fastest and slowest streams
- This demonstrates Clickhouse's ability to handle concurrent query loads with **varying** performance across streams
#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 3107.9 | 1050.6 | 95.1 | 23488.5 |
| 1 | 22 | 2289.2 | 1532.2 | 290.4 | 8237.0 |
| 2 | 22 | 2661.8 | 1256.8 | 194.5 | 12002.0 |
| 3 | 22 | 3193.5 | 1917.0 | 45.5 | 12362.0 |
| 4 | 22 | 2665.2 | 1409.7 | 44.6 | 12507.1 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1050.6ms
- **Worst stream median:** 1917.0ms
- **Performance variance:** 82.5% difference between fastest and slowest streams
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