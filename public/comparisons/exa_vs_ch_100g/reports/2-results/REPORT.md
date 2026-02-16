# Exasol vs ClickHouse Performance Comparison on TPC-H SF100 - Detailed Query Results

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2025-10-24 17:28:50


## Overview

This report presents the complete query-by-query performance results for 4 database systems tested using the TPC-H benchmark at scale factor 100.

**Systems Compared:**
- **exasol**
- **clickhouse**
- **clickhouse_tuned**
- **clickhouse_stat**

## Systems Under Test

### Exasol 2025.1.0

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** exasol 2025.1.0

### Clickhouse 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58

### Clickhouse_tuned 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58

### Clickhouse_stat 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (32 vCPUs)- **Memory:** 247.7GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **242.5ms** median runtime
- **clickhouse_tuned** was **11.5×** slower
- Tested **462** total query executions across 22 different query types

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

| Query Type         |   clickhouse |   clickhouse_tuned |   exasol | Winner   |
|--------------------|--------------|--------------------|----------|----------|
| Aggregation        |        345.5 |              881.8 |     85.3 | exasol   |
| Join-Heavy         |       5196.3 |             5824   |    186.4 | exasol   |
| Complex Analytical |       4735   |             5042.2 |    346.5 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |         801.1 |          2462   |    3.07 |      0.33 | False    |
| Q02     | exasol            | clickhouse          |          78.8 |          1052.7 |   13.36 |      0.07 | False    |
| Q03     | exasol            | clickhouse          |         346.5 |          3986.5 |   11.51 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |          63.2 |          2547.9 |   40.31 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         208.9 |          8776.7 |   42.01 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |          43.7 |           163.1 |    3.73 |      0.27 | False    |
| Q07     | exasol            | clickhouse          |         288.6 |          4886.4 |   16.93 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |          76.4 |          7765.6 |  101.64 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         960.6 |         11756.1 |   12.24 |      0.08 | False    |
| Q10     | exasol            | clickhouse          |         573   |          2846.6 |    4.97 |      0.2  | False    |
| Q11     | exasol            | clickhouse          |         150   |           617.1 |    4.11 |      0.24 | False    |
| Q12     | exasol            | clickhouse          |          85.3 |           749.4 |    8.79 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |         675.4 |          4735   |    7.01 |      0.14 | False    |
| Q14     | exasol            | clickhouse          |          82.7 |           213.1 |    2.58 |      0.39 | False    |
| Q15     | exasol            | clickhouse          |         380.9 |           280.5 |    0.74 |      1.36 | True     |
| Q16     | exasol            | clickhouse          |         486.1 |           450.5 |    0.93 |      1.08 | True     |
| Q17     | exasol            | clickhouse          |          30.9 |          5394.8 |  174.59 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |         639.4 |          5354.3 |    8.37 |      0.12 | False    |
| Q19     | exasol            | clickhouse          |          27   |          2190.9 |   81.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         281.2 |           345.5 |    1.23 |      0.81 | False    |
| Q21     | exasol            | clickhouse          |         384.7 |         46498.2 |  120.87 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          95.6 |           609   |    6.37 |      0.16 | False    |
| Q01     | exasol            | clickhouse_tuned    |         801.1 |          2640.6 |    3.3  |      0.3  | False    |
| Q02     | exasol            | clickhouse_tuned    |          78.8 |          1120.5 |   14.22 |      0.07 | False    |
| Q03     | exasol            | clickhouse_tuned    |         346.5 |          4446.6 |   12.83 |      0.08 | False    |
| Q04     | exasol            | clickhouse_tuned    |          63.2 |         14560.7 |  230.39 |      0    | False    |
| Q05     | exasol            | clickhouse_tuned    |         208.9 |          9282.5 |   44.44 |      0.02 | False    |
| Q06     | exasol            | clickhouse_tuned    |          43.7 |           170   |    3.89 |      0.26 | False    |
| Q07     | exasol            | clickhouse_tuned    |         288.6 |          5042.2 |   17.47 |      0.06 | False    |
| Q08     | exasol            | clickhouse_tuned    |          76.4 |          8082.3 |  105.79 |      0.01 | False    |
| Q09     | exasol            | clickhouse_tuned    |         960.6 |         11956.3 |   12.45 |      0.08 | False    |
| Q10     | exasol            | clickhouse_tuned    |         573   |          2895.4 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse_tuned    |         150   |           744.8 |    4.97 |      0.2  | False    |
| Q12     | exasol            | clickhouse_tuned    |          85.3 |           881.8 |   10.34 |      0.1  | False    |
| Q13     | exasol            | clickhouse_tuned    |         675.4 |          5423.1 |    8.03 |      0.12 | False    |
| Q14     | exasol            | clickhouse_tuned    |          82.7 |           230.4 |    2.79 |      0.36 | False    |
| Q15     | exasol            | clickhouse_tuned    |         380.9 |           367.1 |    0.96 |      1.04 | True     |
| Q16     | exasol            | clickhouse_tuned    |         486.1 |           691.5 |    1.42 |      0.7  | False    |
| Q17     | exasol            | clickhouse_tuned    |          30.9 |          1317.4 |   42.63 |      0.02 | False    |
| Q18     | exasol            | clickhouse_tuned    |         639.4 |         13314.8 |   20.82 |      0.05 | False    |
| Q19     | exasol            | clickhouse_tuned    |          27   |          5623.4 |  208.27 |      0    | False    |
| Q20     | exasol            | clickhouse_tuned    |         281.2 |          2660.6 |    9.46 |      0.11 | False    |
| Q21     | exasol            | clickhouse_tuned    |         384.7 |         33190.9 |   86.28 |      0.01 | False    |
| Q22     | exasol            | clickhouse_tuned    |          95.6 |           632.5 |    6.62 |      0.15 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |   2482.6 |      7 |      2462   |    2466.2 |     11.9 |   2456.1 |   2491.7 |
| Q01     | clickhouse_tuned |   2540.8 |      7 |      2640.6 |    2654.9 |     74.8 |   2551.8 |   2739.1 |
| Q01     | exasol           |    802.3 |      7 |       801.1 |     800.1 |      4.6 |    794.7 |    806.6 |
| Q02     | clickhouse       |   1241.4 |      7 |      1052.7 |    1066.9 |     36.1 |   1039   |   1144.4 |
| Q02     | clickhouse_tuned |   1353   |      7 |      1120.5 |    1121.6 |     26.5 |   1088.5 |   1172   |
| Q02     | exasol           |     93.7 |      7 |        78.8 |      78.8 |      2.4 |     75.2 |     82.1 |
| Q03     | clickhouse       |   4117.1 |      7 |      3986.5 |    3981.1 |     20.8 |   3953.8 |   4017.3 |
| Q03     | clickhouse_tuned |   4507.2 |      7 |      4446.6 |    4424.5 |    104.7 |   4310.3 |   4613.5 |
| Q03     | exasol           |    341.8 |      7 |       346.5 |     344.9 |      5   |    339.4 |    353   |
| Q04     | clickhouse       |   3293.6 |      7 |      2547.9 |    2583.8 |     95.2 |   2517.3 |   2792.1 |
| Q04     | clickhouse_tuned |  16957   |      7 |     14560.7 |   14683.2 |    272.3 |  14433.4 |  15122.6 |
| Q04     | exasol           |     64.7 |      7 |        63.2 |      63.4 |      0.4 |     62.9 |     64   |
| Q05     | clickhouse       |   9505.4 |      7 |      8776.7 |    8751   |    115   |   8590.8 |   8923.6 |
| Q05     | clickhouse_tuned |   9433.2 |      7 |      9282.5 |    9191.1 |    403.5 |   8309.8 |   9537.2 |
| Q05     | exasol           |    273.4 |      7 |       208.9 |     209.3 |      1.3 |    207.7 |    211.8 |
| Q06     | clickhouse       |    940.2 |      7 |       163.1 |     164.3 |      2.6 |    161.8 |    167.9 |
| Q06     | clickhouse_tuned |   1050.5 |      7 |       170   |     171.2 |      4.2 |    166.7 |    179.3 |
| Q06     | exasol           |     43.8 |      7 |        43.7 |      43.6 |      0.3 |     43.2 |     43.9 |
| Q07     | clickhouse       |   6372.7 |      7 |      4886.4 |    4882.5 |     23   |   4849.5 |   4915.3 |
| Q07     | clickhouse_tuned |   6436.7 |      7 |      5042.2 |    5054.3 |     38.4 |   5011.7 |   5116.4 |
| Q07     | exasol           |    276   |      7 |       288.6 |     286.1 |     11.3 |    273.2 |    303.4 |
| Q08     | clickhouse       |   7063.3 |      7 |      7765.6 |    7734.8 |    249.1 |   7213.6 |   7979.8 |
| Q08     | clickhouse_tuned |   7309.4 |      7 |      8082.3 |    8094.1 |     84   |   8006   |   8226.2 |
| Q08     | exasol           |     80.2 |      7 |        76.4 |      79.5 |      8.9 |     75.3 |     99.6 |
| Q09     | clickhouse       |  13474.3 |      7 |     11756.1 |   11904   |    293.8 |  11645.6 |  12456.1 |
| Q09     | clickhouse_tuned |  14229.4 |      7 |     11956.3 |   12014.1 |    214.1 |  11816   |  12414.9 |
| Q09     | exasol           |    965.2 |      7 |       960.6 |     962.4 |      3.5 |    959.4 |    968.3 |
| Q10     | clickhouse       |   4175.6 |      7 |      2846.6 |    2937.9 |    163.2 |   2801.9 |   3179   |
| Q10     | clickhouse_tuned |   4312.2 |      7 |      2895.4 |    3084.2 |    349.1 |   2831.3 |   3642.1 |
| Q10     | exasol           |    570.5 |      7 |       573   |     574.6 |      6.2 |    565.2 |    585   |
| Q11     | clickhouse       |    884.7 |      7 |       617.1 |     615.9 |     12.1 |    599   |    629.7 |
| Q11     | clickhouse_tuned |   1176.2 |      7 |       744.8 |     743.5 |     24.2 |    707.6 |    774   |
| Q11     | exasol           |    152.7 |      7 |       150   |     151.2 |      7   |    144.3 |    165   |
| Q12     | clickhouse       |   2277.1 |      7 |       749.4 |     759.7 |     25.2 |    736.1 |    811.4 |
| Q12     | clickhouse_tuned |   2734.6 |      7 |       881.8 |     895.3 |     46.1 |    856   |    987.1 |
| Q12     | exasol           |     88.1 |      7 |        85.3 |      85.2 |      0.5 |     84.6 |     85.7 |
| Q13     | clickhouse       |   5018.2 |      7 |      4735   |    4750.9 |     83.5 |   4668.9 |   4912.8 |
| Q13     | clickhouse_tuned |   5910.1 |      7 |      5423.1 |    5465   |    108.9 |   5350.9 |   5662.7 |
| Q13     | exasol           |    682.5 |      7 |       675.4 |     675.6 |      7.9 |    664.3 |    690.5 |
| Q14     | clickhouse       |    201.1 |      7 |       213.1 |     211.6 |      5.3 |    201.4 |    216.7 |
| Q14     | clickhouse_tuned |    238.3 |      7 |       230.4 |     231.7 |      3.6 |    227.8 |    237.2 |
| Q14     | exasol           |     82.7 |      7 |        82.7 |      82.8 |      0.3 |     82.4 |     83.4 |
| Q15     | clickhouse       |    335.2 |      7 |       280.5 |     289.5 |     16.5 |    277.4 |    322.7 |
| Q15     | clickhouse_tuned |    414.8 |      7 |       367.1 |     371.6 |     23.6 |    352.3 |    419.7 |
| Q15     | exasol           |    389.4 |      7 |       380.9 |     380.7 |      4.4 |    373.7 |    386.1 |
| Q16     | clickhouse       |    458.1 |      7 |       450.5 |     449.8 |      3.9 |    445.1 |    454.8 |
| Q16     | clickhouse_tuned |    760.6 |      7 |       691.5 |     690.3 |     19.3 |    669.2 |    728.6 |
| Q16     | exasol           |    470.7 |      7 |       486.1 |     485.5 |      4.4 |    479.6 |    492.8 |
| Q17     | clickhouse       |   6053.9 |      7 |      5394.8 |    5396.3 |     21.1 |   5366.9 |   5425.6 |
| Q17     | clickhouse_tuned |   1461.1 |      7 |      1317.4 |    1320   |     11.9 |   1307.5 |   1343   |
| Q17     | exasol           |     31   |      7 |        30.9 |      31   |      0.2 |     30.8 |     31.4 |
| Q18     | clickhouse       |   5538   |      7 |      5354.3 |    5369.8 |     55.8 |   5330.4 |   5490.9 |
| Q18     | clickhouse_tuned |  15523.8 |      7 |     13314.8 |   13608.1 |    594.9 |  12974.5 |  14455.8 |
| Q18     | exasol           |    649.5 |      7 |       639.4 |     638.5 |      8.3 |    626.6 |    648.1 |
| Q19     | clickhouse       |   2260.1 |      7 |      2190.9 |    2190.9 |     11.4 |   2176.9 |   2205.1 |
| Q19     | clickhouse_tuned |   7027.4 |      7 |      5623.4 |    5641.5 |     68.8 |   5538.5 |   5744.1 |
| Q19     | exasol           |     27.1 |      7 |        27   |      27.1 |      0.4 |     26.5 |     27.6 |
| Q20     | clickhouse       |    378.5 |      7 |       345.5 |     345.2 |      4.7 |    340   |    354.2 |
| Q20     | clickhouse_tuned |   3288.4 |      7 |      2660.6 |    2637.5 |     62.8 |   2532.6 |   2701.8 |
| Q20     | exasol           |    286.9 |      7 |       281.2 |     281.4 |      1.9 |    278.4 |    283.7 |
| Q21     | clickhouse       |  46792.6 |      7 |     46498.2 |   46517.8 |    463   |  45952.2 |  47354.7 |
| Q21     | clickhouse_tuned |  33517.2 |      7 |     33190.9 |   33276.7 |   2162.9 |  30555.8 |  36986.6 |
| Q21     | exasol           |    390.1 |      7 |       384.7 |     389.8 |     10.9 |    383.1 |    413.4 |
| Q22     | clickhouse       |    616.3 |      7 |       609   |     613.5 |     23.1 |    586.5 |    647.7 |
| Q22     | clickhouse_tuned |   2335.7 |      7 |       632.5 |     651.4 |     95.3 |    548.5 |    766.4 |
| Q22     | exasol           |     96.4 |      7 |        95.6 |      95.6 |      0.3 |     95   |     96   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 242.5ms
- Average: 307.6ms
- Range: 26.5ms - 968.3ms

**#2. Clickhouse**
- Median: 2504.5ms
- Average: 5181.1ms
- Range: 161.8ms - 47354.7ms

**#3. Clickhouse_tuned**
- Median: 2785.2ms
- Average: 5728.4ms
- Range: 166.7ms - 36986.6ms


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 100
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 7
- **Metric Reported:** Median execution time

### Performance Measurement

All queries were executed with the same data and parameters across all systems. The median execution time from 7 runs is reported for each query to minimize the impact of system variance and outliers.

## Conclusion

This benchmark provides a detailed, query-level comparison of 4 database systems on analytical workloads. The results demonstrate the performance characteristics and trade-offs of each system when processing TPC-H queries.

While **exasol** demonstrated the strongest overall performance in this test, the optimal choice for a specific use case depends on multiple factors including workload characteristics, operational requirements, and system integration needs.

---

**For complete reproduction details** including installation steps, configuration parameters, and a self-contained benchmark package, see the [full benchmark report](../3-full/REPORT.md).

---

*All benchmark data, figures, and configuration files are available in the attachments directory for independent analysis and verification.*