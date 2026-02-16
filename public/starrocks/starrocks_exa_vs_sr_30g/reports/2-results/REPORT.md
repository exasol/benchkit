# Exasol vs StarRocks: TPC-H SF30 (Single-Node, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:13:07


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
- **exasol** was the fastest overall with **368.7ms** median runtime
- **starrocks** was **4.6×** slower- Tested **220** total query executions across 22 different query types

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
| Aggregation        |    171.8 |      1463.3 | exasol   |
| Join-Heavy         |    352.6 |      2471.5 | exasol   |
| Complex Analytical |    646.9 |      2789.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1876   |          5984.4 |    3.19 |      0.31 | False    |
| Q02     | exasol            | starrocks           |          60.8 |           352.7 |    5.8  |      0.17 | False    |
| Q03     | exasol            | starrocks           |         667.8 |          2789.4 |    4.18 |      0.24 | False    |
| Q04     | exasol            | starrocks           |         127.5 |           814.9 |    6.39 |      0.16 | False    |
| Q05     | exasol            | starrocks           |         498   |          2686.7 |    5.39 |      0.19 | False    |
| Q06     | exasol            | starrocks           |          84.1 |          1178.8 |   14.02 |      0.07 | False    |
| Q07     | exasol            | starrocks           |         644.8 |          3220.6 |    4.99 |      0.2  | False    |
| Q08     | exasol            | starrocks           |         158.3 |          2246.1 |   14.19 |      0.07 | False    |
| Q09     | exasol            | starrocks           |        2284   |          5546.6 |    2.43 |      0.41 | False    |
| Q10     | exasol            | starrocks           |         739.8 |          2717.6 |    3.67 |      0.27 | False    |
| Q11     | exasol            | starrocks           |         138.6 |           253   |    1.83 |      0.55 | False    |
| Q12     | exasol            | starrocks           |         171.8 |          1602.6 |    9.33 |      0.11 | False    |
| Q13     | exasol            | starrocks           |        1704.1 |          3027.5 |    1.78 |      0.56 | False    |
| Q14     | exasol            | starrocks           |         164   |          1249   |    7.62 |      0.13 | False    |
| Q15     | exasol            | starrocks           |         369.2 |          1249.1 |    3.38 |      0.3  | False    |
| Q16     | exasol            | starrocks           |         635.2 |           478.4 |    0.75 |      1.33 | True     |
| Q17     | exasol            | starrocks           |          25.2 |           662   |   26.27 |      0.04 | False    |
| Q18     | exasol            | starrocks           |        1101.2 |          4827.9 |    4.38 |      0.23 | False    |
| Q19     | exasol            | starrocks           |          50.8 |          1799.9 |   35.43 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         358.1 |          1463.3 |    4.09 |      0.24 | False    |
| Q21     | exasol            | starrocks           |         969.3 |          8435.3 |    8.7  |      0.11 | False    |
| Q22     | exasol            | starrocks           |         210   |           567.5 |    2.7  |      0.37 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1874.9 |      5 |      1876   |    1875.3 |     15.7 |   1851.8 |   1893   |
| Q01     | starrocks |   8105.3 |      5 |      5984.4 |    6013   |     50   |   5965.8 |   6074.2 |
| Q02     | exasol    |     78.2 |      5 |        60.8 |      61   |      0.7 |     60.3 |     62.1 |
| Q02     | starrocks |    601.1 |      5 |       352.7 |     341.3 |     29.7 |    296.4 |    367.1 |
| Q03     | exasol    |    684   |      5 |       667.8 |     668.9 |      3.3 |    666.5 |    674.6 |
| Q03     | starrocks |   2822.7 |      5 |      2789.4 |    2780.2 |     53.3 |   2724.1 |   2856.4 |
| Q04     | exasol    |    129.4 |      5 |       127.5 |     127.5 |      0.5 |    126.9 |    128.2 |
| Q04     | starrocks |   1552.1 |      5 |       814.9 |     821.2 |     24.3 |    800.5 |    863.2 |
| Q05     | exasol    |    544.1 |      5 |       498   |     506.1 |     20.4 |    493.8 |    542.5 |
| Q05     | starrocks |   2568.1 |      5 |      2686.7 |    2704.3 |     67.3 |   2646.5 |   2819.8 |
| Q06     | exasol    |     84.4 |      5 |        84.1 |      84.1 |      0.4 |     83.7 |     84.8 |
| Q06     | starrocks |   1222.8 |      5 |      1178.8 |    1178.2 |     21.6 |   1146.5 |   1207.5 |
| Q07     | exasol    |    667.2 |      5 |       644.8 |     643.9 |      5.9 |    635   |    650.8 |
| Q07     | starrocks |   3179.7 |      5 |      3220.6 |    3231.6 |     45.7 |   3192.6 |   3308.6 |
| Q08     | exasol    |    157.1 |      5 |       158.3 |     159.1 |      2.9 |    156.3 |    164.1 |
| Q08     | starrocks |   2323.3 |      5 |      2246.1 |    2260.5 |     32   |   2224   |   2297.6 |
| Q09     | exasol    |   2364.7 |      5 |      2284   |    2290.4 |     12.8 |   2278.9 |   2307.5 |
| Q09     | starrocks |   5706.1 |      5 |      5546.6 |    5551.4 |     39.7 |   5508.1 |   5592.6 |
| Q10     | exasol    |    753.5 |      5 |       739.8 |     740.7 |      4.2 |    736   |    745.7 |
| Q10     | starrocks |   2576.4 |      5 |      2717.6 |    2704.4 |     44.6 |   2645.4 |   2761.8 |
| Q11     | exasol    |    137   |      5 |       138.6 |     151.8 |     31.3 |    136.4 |    207.7 |
| Q11     | starrocks |    333.3 |      5 |       253   |     252.5 |     26.5 |    221.1 |    291.3 |
| Q12     | exasol    |    308.8 |      5 |       171.8 |     171.5 |      0.5 |    170.9 |    172   |
| Q12     | starrocks |   1674.2 |      5 |      1602.6 |    1604.1 |     15.3 |   1585.2 |   1624.1 |
| Q13     | exasol    |   1855   |      5 |      1704.1 |    1704.9 |      2.5 |   1702.7 |   1709.1 |
| Q13     | starrocks |   3585.2 |      5 |      3027.5 |    3015.5 |     64.2 |   2911.8 |   3076.1 |
| Q14     | exasol    |    267.1 |      5 |       164   |     163.9 |      1   |    162.6 |    165.3 |
| Q14     | starrocks |   1284.7 |      5 |      1249   |    1257.7 |     19.7 |   1238   |   1287.7 |
| Q15     | exasol    |    400.1 |      5 |       369.2 |     369.8 |      1.3 |    368.5 |    371.6 |
| Q15     | starrocks |   1277.1 |      5 |      1249.1 |    1241.7 |     19.2 |   1210.6 |   1258.2 |
| Q16     | exasol    |    655.8 |      5 |       635.2 |     639.5 |     11.9 |    627.7 |    659.1 |
| Q16     | starrocks |    876.2 |      5 |       478.4 |     476.8 |     12.1 |    459.4 |    493   |
| Q17     | exasol    |     46.4 |      5 |        25.2 |      25.4 |      0.3 |     25.1 |     25.9 |
| Q17     | starrocks |   1293.9 |      5 |       662   |     682.5 |     38.5 |    653.6 |    747.2 |
| Q18     | exasol    |   1136.1 |      5 |      1101.2 |    1109.6 |     18.8 |   1097.7 |   1142.6 |
| Q18     | starrocks |   5043   |      5 |      4827.9 |    4821.4 |     55   |   4751.2 |   4900.7 |
| Q19     | exasol    |     83.4 |      5 |        50.8 |      50.9 |      0.3 |     50.5 |     51.4 |
| Q19     | starrocks |   1754.8 |      5 |      1799.9 |    1780.3 |     28.6 |   1744.9 |   1802.7 |
| Q20     | exasol    |    426.2 |      5 |       358.1 |     365.4 |     17.4 |    356.6 |    396.5 |
| Q20     | starrocks |   1579.4 |      5 |      1463.3 |    1459.6 |     26.3 |   1421.9 |   1494.2 |
| Q21     | exasol    |    986.8 |      5 |       969.3 |     969.8 |      5   |    964.3 |    976.9 |
| Q21     | starrocks |   9285.4 |      5 |      8435.3 |    8505.5 |    153   |   8369.9 |   8723.5 |
| Q22     | exasol    |    219   |      5 |       210   |     210.2 |      1.4 |    208.2 |    211.5 |
| Q22     | starrocks |    641.5 |      5 |       567.5 |     565   |      8.2 |    555.9 |    573.8 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 368.7ms
- Average: 595.0ms
- Range: 25.1ms - 2307.5ms

**#2. Starrocks**
- Median: 1684.5ms
- Average: 2420.4ms
- Range: 221.1ms - 8723.5ms



## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 30
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