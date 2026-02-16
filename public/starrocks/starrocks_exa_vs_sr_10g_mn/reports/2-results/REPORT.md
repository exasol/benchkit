# Exasol vs StarRocks: TPC-H SF10 (Multi-Node 3, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:05:17


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
- **exasol** was the fastest overall with **195.2ms** median runtime
- **starrocks** was **5.4×** slower- Tested **220** total query executions across 22 different query types

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
| Aggregation        |    122.4 |       473.1 | exasol   |
| Join-Heavy         |    229.2 |      1379.8 | exasol   |
| Complex Analytical |    289.3 |      1526.5 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         439   |          5163.2 |   11.76 |      0.09 | False    |
| Q02     | exasol            | starrocks           |          78.9 |           238.3 |    3.02 |      0.33 | False    |
| Q03     | exasol            | starrocks           |         342.8 |          1715.4 |    5    |      0.2  | False    |
| Q04     | exasol            | starrocks           |         111.3 |           575.3 |    5.17 |      0.19 | False    |
| Q05     | exasol            | starrocks           |         267.4 |          1149   |    4.3  |      0.23 | False    |
| Q06     | exasol            | starrocks           |          33.1 |           274.5 |    8.29 |      0.12 | False    |
| Q07     | exasol            | starrocks           |         861.4 |          1546.1 |    1.79 |      0.56 | False    |
| Q08     | exasol            | starrocks           |         192.6 |          1572.3 |    8.16 |      0.12 | False    |
| Q09     | exasol            | starrocks           |        1323.7 |          2638.3 |    1.99 |      0.5  | False    |
| Q10     | exasol            | starrocks           |         296.8 |          2732.9 |    9.21 |      0.11 | False    |
| Q11     | exasol            | starrocks           |          69   |           223.4 |    3.24 |      0.31 | False    |
| Q12     | exasol            | starrocks           |         101.1 |           470.1 |    4.65 |      0.22 | False    |
| Q13     | exasol            | starrocks           |         477.9 |          1539.8 |    3.22 |      0.31 | False    |
| Q14     | exasol            | starrocks           |         123.3 |           435.1 |    3.53 |      0.28 | False    |
| Q15     | exasol            | starrocks           |          99.4 |           353   |    3.55 |      0.28 | False    |
| Q16     | exasol            | starrocks           |         289.3 |           510.5 |    1.76 |      0.57 | False    |
| Q17     | exasol            | starrocks           |          52.2 |           673.8 |   12.91 |      0.08 | False    |
| Q18     | exasol            | starrocks           |         268.9 |          2211.3 |    8.22 |      0.12 | False    |
| Q19     | exasol            | starrocks           |         179.9 |          1062   |    5.9  |      0.17 | False    |
| Q20     | exasol            | starrocks           |         166.1 |           900.4 |    5.42 |      0.18 | False    |
| Q21     | exasol            | starrocks           |         268.3 |          4488.1 |   16.73 |      0.06 | False    |
| Q22     | exasol            | starrocks           |          71.5 |           438.7 |    6.14 |      0.16 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |    439.2 |      5 |       439   |     442.4 |      7   |    437.3 |    454.2 |
| Q01     | starrocks |   5956.1 |      5 |      5163.2 |    5159.5 |     29.3 |   5126.5 |   5201.4 |
| Q02     | exasol    |    116.6 |      5 |        78.9 |      79   |      1.2 |     77.8 |     80.6 |
| Q02     | starrocks |    498   |      5 |       238.3 |     254.6 |     31.3 |    232.9 |    307.7 |
| Q03     | exasol    |    348.5 |      5 |       342.8 |     343.3 |      3.4 |    340   |    347.8 |
| Q03     | starrocks |   1859.3 |      5 |      1715.4 |    1706.9 |     73.5 |   1587.9 |   1789.7 |
| Q04     | exasol    |    110.9 |      5 |       111.3 |     111.3 |      1.7 |    108.9 |    113.4 |
| Q04     | starrocks |    846   |      5 |       575.3 |     579.8 |      9.7 |    569.4 |    590.5 |
| Q05     | exasol    |    322.5 |      5 |       267.4 |     266.6 |      2.7 |    262.9 |    269.6 |
| Q05     | starrocks |   1392.6 |      5 |      1149   |    1155.7 |     47.9 |   1106.9 |   1208.7 |
| Q06     | exasol    |     33.3 |      5 |        33.1 |      33.1 |      0.1 |     32.9 |     33.3 |
| Q06     | starrocks |    505   |      5 |       274.5 |     294.9 |     48.8 |    262.1 |    380.9 |
| Q07     | exasol    |    482.4 |      5 |       861.4 |     750.6 |    260.5 |    470.1 |   1006.6 |
| Q07     | starrocks |   1251.6 |      5 |      1546.1 |    1553.2 |     49.8 |   1508.4 |   1637.5 |
| Q08     | exasol    |    295.3 |      5 |       192.6 |     191.4 |      5.2 |    182.7 |    195.6 |
| Q08     | starrocks |   1644   |      5 |      1572.3 |    1584   |     33.3 |   1551   |   1629.9 |
| Q09     | exasol    |   1292.2 |      5 |      1323.7 |    1321.4 |     43.1 |   1275.5 |   1369   |
| Q09     | starrocks |   2605.8 |      5 |      2638.3 |    2629.3 |     91.5 |   2526.2 |   2752.1 |
| Q10     | exasol    |    298.8 |      5 |       296.8 |     297.3 |      2   |    295.5 |    300.7 |
| Q10     | starrocks |   2593.3 |      5 |      2732.9 |    2705.8 |    206.6 |   2365   |   2920.4 |
| Q11     | exasol    |     70   |      5 |        69   |      69.2 |      1.1 |     67.9 |     70.8 |
| Q11     | starrocks |    363   |      5 |       223.4 |     223.7 |     26.9 |    194.8 |    255.6 |
| Q12     | exasol    |    129.3 |      5 |       101.1 |     100.9 |      0.5 |    100   |    101.3 |
| Q12     | starrocks |    988.5 |      5 |       470.1 |     472.4 |     11.3 |    463.3 |    491.3 |
| Q13     | exasol    |    495.7 |      5 |       477.9 |     483   |     11.5 |    476.6 |    503.4 |
| Q13     | starrocks |   1912.9 |      5 |      1539.8 |    1604.4 |    150.1 |   1522.9 |   1872.1 |
| Q14     | exasol    |    136.3 |      5 |       123.3 |     123.1 |      0.8 |    122.2 |    124.1 |
| Q14     | starrocks |    933.3 |      5 |       435.1 |     449.2 |     53.4 |    401.4 |    540.7 |
| Q15     | exasol    |    101.2 |      5 |        99.4 |      99.7 |      1.1 |     98.4 |    101.1 |
| Q15     | starrocks |    513.8 |      5 |       353   |     370.7 |     40.2 |    336   |    420   |
| Q16     | exasol    |    298.8 |      5 |       289.3 |     295   |     13.3 |    287.1 |    318.6 |
| Q16     | starrocks |    650.2 |      5 |       510.5 |     524.5 |     29.8 |    495.5 |    571.6 |
| Q17     | exasol    |     56.6 |      5 |        52.2 |      52.4 |      0.9 |     51.2 |     53.7 |
| Q17     | starrocks |    931.3 |      5 |       673.8 |     692.6 |     62.4 |    638.3 |    797.5 |
| Q18     | exasol    |    274.4 |      5 |       268.9 |     268.5 |      1.8 |    265.7 |    270.2 |
| Q18     | starrocks |   2516.3 |      5 |      2211.3 |    2214.2 |     74.6 |   2138.7 |   2298.8 |
| Q19     | exasol    |    193.2 |      5 |       179.9 |     188.3 |     89.2 |     87.7 |    329.1 |
| Q19     | starrocks |   1105.6 |      5 |      1062   |    1093   |     58.4 |   1055.4 |   1192.7 |
| Q20     | exasol    |    281.7 |      5 |       166.1 |     242.5 |    121.9 |    155.9 |    430.7 |
| Q20     | starrocks |   1712.6 |      5 |       900.4 |     880.7 |    169.3 |    635.8 |   1106.7 |
| Q21     | exasol    |    273.3 |      5 |       268.3 |     268.1 |      1.4 |    266.2 |    269.6 |
| Q21     | starrocks |   4882.1 |      5 |      4488.1 |    4506.5 |     88   |   4434.8 |   4658.5 |
| Q22     | exasol    |     75   |      5 |        71.5 |      71.6 |      0.6 |     71   |     72.5 |
| Q22     | starrocks |    482.3 |      5 |       438.7 |     464.4 |     51   |    420.1 |    528.5 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 195.2ms
- Average: 277.2ms
- Range: 32.9ms - 1369.0ms

**#2. Starrocks**
- Median: 1056.2ms
- Average: 1414.6ms
- Range: 194.8ms - 5201.4ms



## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 5
- **Execution Mode:** Sequential (single connection)
- **Metric Reported:** Median execution time

### Performance Measurement

All queries were executed with the same data and parameters across all systems. The median execution time from 5 runs is reported for each query to minimize the impact of system variance and outliers.

## Conclusion

This benchmark provides a detailed, query-level comparison of 2 database systems on analytical workloads. The results demonstrate the performance characteristics and trade-offs of each system when processing TPC-H queries.

While **exasol** demonstrated the strongest overall performance in this test, the optimal choice for a specific use case depends on multiple factors including workload characteristics, operational requirements, and system integration needs.

---

**For complete reproduction details** including installation steps, configuration parameters, and a self-contained benchmark package, see the [full benchmark report](../3-full/REPORT.md).

---

*All benchmark data, figures, and configuration files are available in the attachments directory for independent analysis and verification.*