# Exasol vs ClickHouse Performance Comparison on TPC-H SF100 - Detailed Query Results

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2025-10-31 12:15:42


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 100.

**Systems Compared:**
- **exasol**
- **clickhouse**

## Systems Under Test

### Exasol 2025.1.0

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** exasol 2025.1.0

### Clickhouse 25.9.5.21

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** clickhouse 25.9.5.21


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **238.1ms** median runtime
- **clickhouse** was **10.7×** slower
- Tested **308** total query executions across 22 different query types

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
| Aggregation        |        390   |     82.2 | exasol   |
| Join-Heavy         |       5596.1 |    178   | exasol   |
| Complex Analytical |       4894.5 |    324.7 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |         791   |          2527.8 |    3.2  |      0.31 | False    |
| Q02     | exasol            | clickhouse          |          74.8 |          1088.3 |   14.55 |      0.07 | False    |
| Q03     | exasol            | clickhouse          |         324.7 |          4059.9 |   12.5  |      0.08 | False    |
| Q04     | exasol            | clickhouse          |          60.7 |          2586.4 |   42.61 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         203.1 |          8884.8 |   43.75 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |          41.3 |           164.9 |    3.99 |      0.25 | False    |
| Q07     | exasol            | clickhouse          |         265.1 |          4894.5 |   18.46 |      0.05 | False    |
| Q08     | exasol            | clickhouse          |          73.7 |          7908.5 |  107.31 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         942.8 |         12545.6 |   13.31 |      0.08 | False    |
| Q10     | exasol            | clickhouse          |         557.4 |          3408.5 |    6.11 |      0.16 | False    |
| Q11     | exasol            | clickhouse          |         144.2 |           727.3 |    5.04 |      0.2  | False    |
| Q12     | exasol            | clickhouse          |          82.2 |           770.2 |    9.37 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |         657.9 |          5744.7 |    8.73 |      0.11 | False    |
| Q14     | exasol            | clickhouse          |          81   |           245.3 |    3.03 |      0.33 | False    |
| Q15     | exasol            | clickhouse          |         379.6 |           346.4 |    0.91 |      1.1  | True     |
| Q16     | exasol            | clickhouse          |         457.7 |           517.5 |    1.13 |      0.88 | False    |
| Q17     | exasol            | clickhouse          |          28   |          5821.7 |  207.92 |      0    | False    |
| Q18     | exasol            | clickhouse          |         631.4 |          5352.2 |    8.48 |      0.12 | False    |
| Q19     | exasol            | clickhouse          |          25.6 |          2207.7 |   86.24 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         277.6 |           390   |    1.4  |      0.71 | False    |
| Q21     | exasol            | clickhouse          |         384.5 |         46707.2 |  121.48 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          94.4 |           593.9 |    6.29 |      0.16 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2542.8 |      7 |      2527.8 |    2520.5 |     34   |   2460.1 |   2556.8 |
| Q01     | exasol     |    803.5 |      7 |       791   |     793.2 |      5.2 |    789.5 |    804.5 |
| Q02     | clickhouse |   1308.4 |      7 |      1088.3 |    1094.2 |     25.1 |   1071.9 |   1146   |
| Q02     | exasol     |     94   |      7 |        74.8 |      74.8 |      0.6 |     74.2 |     75.6 |
| Q03     | clickhouse |   4527.5 |      7 |      4059.9 |    4070   |    180.4 |   3884.6 |   4396.7 |
| Q03     | exasol     |    326.5 |      7 |       324.7 |     325.1 |      4.9 |    318.3 |    333.1 |
| Q04     | clickhouse |   3266.7 |      7 |      2586.4 |    2617.8 |     84.4 |   2542.8 |   2770.4 |
| Q04     | exasol     |     63.3 |      7 |        60.7 |      60.7 |      0.3 |     60.3 |     61   |
| Q05     | clickhouse |   9544.3 |      7 |      8884.8 |    8866.6 |    117.2 |   8720.3 |   9080.4 |
| Q05     | exasol     |    267.8 |      7 |       203.1 |     204.5 |      3.4 |    202.9 |    212.2 |
| Q06     | clickhouse |    996   |      7 |       164.9 |     166   |      3.2 |    162.6 |    172.1 |
| Q06     | exasol     |     41.9 |      7 |        41.3 |      41.3 |      0.4 |     40.8 |     42   |
| Q07     | clickhouse |   6395.3 |      7 |      4894.5 |    4900.8 |     29.6 |   4876   |   4963.5 |
| Q07     | exasol     |    267.2 |      7 |       265.1 |     265.1 |      1   |    264   |    266.7 |
| Q08     | clickhouse |   7138.8 |      7 |      7908.5 |    7904.9 |    222.2 |   7575.6 |   8175.8 |
| Q08     | exasol     |     74.9 |      7 |        73.7 |      77.9 |     11.6 |     72.6 |    104.2 |
| Q09     | clickhouse |  14236.3 |      7 |     12545.6 |   12998.1 |   1180.2 |  11949.3 |  15509.6 |
| Q09     | exasol     |    943.9 |      7 |       942.8 |     943.2 |      1.7 |    941.2 |    946.5 |
| Q10     | clickhouse |   5456.7 |      7 |      3408.5 |    3431.6 |     90.9 |   3352.5 |   3616.6 |
| Q10     | exasol     |    556   |      7 |       557.4 |     558.5 |      4.5 |    553.5 |    565.1 |
| Q11     | clickhouse |   1168   |      7 |       727.3 |     736.6 |     42.8 |    684.6 |    799.4 |
| Q11     | exasol     |    143.5 |      7 |       144.2 |     145.3 |      4.2 |    140.5 |    153   |
| Q12     | clickhouse |   2507   |      7 |       770.2 |     794.6 |     46.2 |    759.9 |    878.6 |
| Q12     | exasol     |     84.7 |      7 |        82.2 |      82.1 |      0.2 |     81.9 |     82.4 |
| Q13     | clickhouse |   5648.2 |      7 |      5744.7 |    5712.2 |    265.3 |   5378.1 |   6124.7 |
| Q13     | exasol     |    659.6 |      7 |       657.9 |     659.1 |      3.4 |    655.4 |    664   |
| Q14     | clickhouse |    234.5 |      7 |       245.3 |     242.8 |      4.8 |    236.7 |    248   |
| Q14     | exasol     |     94.4 |      7 |        81   |      80.9 |      0.2 |     80.6 |     81.2 |
| Q15     | clickhouse |    410.2 |      7 |       346.4 |     352.6 |     11.2 |    345.7 |    374.5 |
| Q15     | exasol     |    376.1 |      7 |       379.6 |     406.7 |     35.2 |    377.6 |    448.2 |
| Q16     | clickhouse |    538.7 |      7 |       517.5 |     513   |     14.2 |    484.3 |    525.3 |
| Q16     | exasol     |    463.8 |      7 |       457.7 |     458.5 |      6.7 |    451.3 |    472.4 |
| Q17     | clickhouse |   7380.9 |      7 |      5821.7 |    6032.4 |    528.6 |   5580.2 |   6897.6 |
| Q17     | exasol     |     29.3 |      7 |        28   |      27.9 |      0.2 |     27.5 |     28.2 |
| Q18     | clickhouse |   5835.4 |      7 |      5352.2 |    5365.8 |     88.2 |   5289.3 |   5545.5 |
| Q18     | exasol     |    632.4 |      7 |       631.4 |     632.2 |      6.3 |    622.4 |    640.4 |
| Q19     | clickhouse |   2302.7 |      7 |      2207.7 |    2216.2 |     52.6 |   2156.6 |   2310.9 |
| Q19     | exasol     |     25.7 |      7 |        25.6 |      25.6 |      0.2 |     25.2 |     25.7 |
| Q20     | clickhouse |    421.6 |      7 |       390   |     390.4 |      6.4 |    379.2 |    397.9 |
| Q20     | exasol     |    281.6 |      7 |       277.6 |     277.8 |      1.8 |    274.8 |    280.9 |
| Q21     | clickhouse |  48541.1 |      7 |     46707.2 |   46802.5 |    770.3 |  45770.5 |  47984.7 |
| Q21     | exasol     |    384.3 |      7 |       384.5 |     390   |     14.3 |    383.8 |    422.3 |
| Q22     | clickhouse |    596.3 |      7 |       593.9 |     595.8 |     16.6 |    575.7 |    619.4 |
| Q22     | exasol     |     97.2 |      7 |        94.4 |      94.4 |      0.3 |     94.1 |     95   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 238.1ms
- Average: 301.1ms
- Range: 25.2ms - 946.5ms

**#2. Clickhouse**
- Median: 2546.6ms
- Average: 5378.4ms
- Range: 162.6ms - 47984.7ms



## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 100
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 7
- **Execution Mode:** Sequential (single connection)
- **Metric Reported:** Median execution time

### Performance Measurement

All queries were executed with the same data and parameters across all systems. The median execution time from 7 runs is reported for each query to minimize the impact of system variance and outliers.

## Conclusion

This benchmark provides a detailed, query-level comparison of 2 database systems on analytical workloads. The results demonstrate the performance characteristics and trade-offs of each system when processing TPC-H queries.

While **exasol** demonstrated the strongest overall performance in this test, the optimal choice for a specific use case depends on multiple factors including workload characteristics, operational requirements, and system integration needs.

---

**For complete reproduction details** including installation steps, configuration parameters, and a self-contained benchmark package, see the [full benchmark report](../3-full/REPORT.md).

---

*All benchmark data, figures, and configuration files are available in the attachments directory for independent analysis and verification.*