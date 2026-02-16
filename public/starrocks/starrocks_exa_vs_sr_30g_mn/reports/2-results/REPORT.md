# Exasol vs StarRocks: TPC-H SF30 (Multi-Node 3, Single-User) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 16:08:20


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor 30.

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
- **exasol** was the fastest overall with **433.3ms** median runtime
- **starrocks** was **9.1×** slower- Tested **220** total query executions across 22 different query types

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
| Aggregation        |    330.7 |      3069   | exasol   |
| Join-Heavy         |    683.4 |      6039.2 | exasol   |
| Complex Analytical |    899   |      4773.4 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1266   |         15779.8 |   12.46 |      0.08 | False    |
| Q02     | exasol            | starrocks           |         107   |           489.3 |    4.57 |      0.22 | False    |
| Q03     | exasol            | starrocks           |        1358.8 |          6286.8 |    4.63 |      0.22 | False    |
| Q04     | exasol            | starrocks           |         290.8 |          4773.4 |   16.41 |      0.06 | False    |
| Q05     | exasol            | starrocks           |        1066.2 |          6012.8 |    5.64 |      0.18 | False    |
| Q06     | exasol            | starrocks           |          70.1 |          2387.9 |   34.06 |      0.03 | False    |
| Q07     | exasol            | starrocks           |        1386   |          4551.4 |    3.28 |      0.3  | False    |
| Q08     | exasol            | starrocks           |         467.1 |          6065.6 |   12.99 |      0.08 | False    |
| Q09     | exasol            | starrocks           |        3963   |         10519.3 |    2.65 |      0.38 | False    |
| Q10     | exasol            | starrocks           |         905.5 |          9646.8 |   10.65 |      0.09 | False    |
| Q11     | exasol            | starrocks           |         265   |           614.7 |    2.32 |      0.43 | False    |
| Q12     | exasol            | starrocks           |         264.2 |          3392.8 |   12.84 |      0.08 | False    |
| Q13     | exasol            | starrocks           |        1236.8 |          7479.4 |    6.05 |      0.17 | False    |
| Q14     | exasol            | starrocks           |         363.6 |          2863.9 |    7.88 |      0.13 | False    |
| Q15     | exasol            | starrocks           |         330.7 |          2473.6 |    7.48 |      0.13 | False    |
| Q16     | exasol            | starrocks           |         566.4 |          1257.6 |    2.22 |      0.45 | False    |
| Q17     | exasol            | starrocks           |          82.3 |          3159.9 |   38.39 |      0.03 | False    |
| Q18     | exasol            | starrocks           |         899   |         10921.7 |   12.15 |      0.08 | False    |
| Q19     | exasol            | starrocks           |         108.7 |          3319.4 |   30.54 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         398.2 |          3069   |    7.71 |      0.13 | False    |
| Q21     | exasol            | starrocks           |        1076.3 |         15735.6 |   14.62 |      0.07 | False    |
| Q22     | exasol            | starrocks           |         282.6 |          1047.7 |    3.71 |      0.27 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1364.4 |      5 |      1266   |    1265.5 |      2.5 |   1261.9 |   1268.2 |
| Q01     | starrocks |  16770.1 |      5 |     15779.8 |   15742.9 |    111.3 |  15619.2 |  15873.5 |
| Q02     | exasol    |    113   |      5 |       107   |     106.6 |      1.7 |    103.8 |    107.9 |
| Q02     | starrocks |    986.4 |      5 |       489.3 |     523.3 |     77   |    472.2 |    658.9 |
| Q03     | exasol    |    993.6 |      5 |      1358.8 |    1404.2 |    494.6 |   1007.2 |   2234.7 |
| Q03     | starrocks |   6622   |      5 |      6286.8 |    6301.9 |     97.3 |   6200.7 |   6415.3 |
| Q04     | exasol    |    292.7 |      5 |       290.8 |     289   |      3.4 |    285   |    291.8 |
| Q04     | starrocks |   4743.7 |      5 |      4773.4 |    4767.7 |    112.2 |   4629.5 |   4912.9 |
| Q05     | exasol    |   1121.2 |      5 |      1066.2 |    1065.8 |     14.2 |   1047.9 |   1083.3 |
| Q05     | starrocks |   5766.2 |      5 |      6012.8 |    6091.3 |    186.1 |   5942.5 |   6410.2 |
| Q06     | exasol    |     69.7 |      5 |        70.1 |      70.2 |      0.6 |     69.6 |     71.1 |
| Q06     | starrocks |   2503.2 |      5 |      2387.9 |    2449.2 |    142.2 |   2377.5 |   2703.4 |
| Q07     | exasol    |   1378.1 |      5 |      1386   |    1397.7 |     21.1 |   1377.4 |   1427.9 |
| Q07     | starrocks |   4572.3 |      5 |      4551.4 |    4548.5 |     48.7 |   4492.9 |   4622.6 |
| Q08     | exasol    |    454.4 |      5 |       467.1 |     465.6 |      4.9 |    457.4 |    470.5 |
| Q08     | starrocks |   5841.1 |      5 |      6065.6 |    6139.1 |    315.4 |   5785.2 |   6539.3 |
| Q09     | exasol    |   5400.1 |      5 |      3963   |    4028.9 |    147   |   3910.6 |   4245.4 |
| Q09     | starrocks |  10182.2 |      5 |     10519.3 |   10497.5 |    538   |   9965   |  11239.6 |
| Q10     | exasol    |    903.5 |      5 |       905.5 |    1023.8 |    212.1 |    896.3 |   1391.8 |
| Q10     | starrocks |  10037.9 |      5 |      9646.8 |    9665.2 |    149.2 |   9534.8 |   9908.7 |
| Q11     | exasol    |   2756.6 |      5 |       265   |     264.2 |      5.3 |    258.1 |    269.6 |
| Q11     | starrocks |    745.1 |      5 |       614.7 |     597   |     58.2 |    523.5 |    671   |
| Q12     | exasol    |    310.8 |      5 |       264.2 |     263.6 |      3   |    260.2 |    267.4 |
| Q12     | starrocks |   3510.6 |      5 |      3392.8 |    3375.2 |     42   |   3315   |   3416.7 |
| Q13     | exasol    |   1311.5 |      5 |      1236.8 |    1237.1 |     10.8 |   1226   |   1248.7 |
| Q13     | starrocks |   7662.6 |      5 |      7479.4 |    7460.6 |    104.7 |   7362.8 |   7615.2 |
| Q14     | exasol    |    400.9 |      5 |       363.6 |     364   |      3.4 |    359.9 |    369.2 |
| Q14     | starrocks |   2897   |      5 |      2863.9 |    2858.2 |     16.5 |   2833.9 |   2877.8 |
| Q15     | exasol    |    376.8 |      5 |       330.7 |     333.7 |      7.3 |    329.2 |    346.7 |
| Q15     | starrocks |   2601   |      5 |      2473.6 |    2483.7 |     22.2 |   2461.8 |   2516.5 |
| Q16     | exasol    |    583.5 |      5 |       566.4 |     570   |      9.5 |    563.6 |    586.9 |
| Q16     | starrocks |   1435.8 |      5 |      1257.6 |    1254.8 |     42.8 |   1199.1 |   1308.7 |
| Q17     | exasol    |     93   |      5 |        82.3 |      82.4 |      2.2 |     79.1 |     84.5 |
| Q17     | starrocks |   3164   |      5 |      3159.9 |    3153.7 |     48.6 |   3081   |   3215.4 |
| Q18     | exasol    |    732.7 |      5 |       899   |    1090.8 |    411   |    727   |   1571.3 |
| Q18     | starrocks |  11107.2 |      5 |     10921.7 |   10605.8 |    481.6 |  10027.8 |  11001.9 |
| Q19     | exasol    |    130.6 |      5 |       108.7 |     108.8 |      1.3 |    107   |    110.2 |
| Q19     | starrocks |   3449   |      5 |      3319.4 |    3330.9 |     41.6 |   3281.2 |   3385   |
| Q20     | exasol    |    410.8 |      5 |       398.2 |     398.2 |      6.3 |    390.8 |    406.9 |
| Q20     | starrocks |   3097.5 |      5 |      3069   |    3101   |     67   |   3050   |   3211   |
| Q21     | exasol    |  16532.3 |      5 |      1076.3 |    1196.1 |    260.1 |   1065.7 |   1660.2 |
| Q21     | starrocks |  16539.3 |      5 |     15735.6 |   15702.3 |    105.1 |  15556.7 |  15823   |
| Q22     | exasol    |    436.3 |      5 |       282.6 |     275.8 |    109.9 |    164.1 |    409.2 |
| Q22     | starrocks |   1283.6 |      5 |      1047.7 |    1050.4 |     78.4 |    984.9 |   1177.5 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 433.3ms
- Average: 786.4ms
- Range: 69.6ms - 4245.4ms

**#2. Starrocks**
- Median: 3954.8ms
- Average: 5531.8ms
- Range: 472.2ms - 15873.5ms



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