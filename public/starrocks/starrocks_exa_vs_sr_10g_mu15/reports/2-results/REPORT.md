# Exasol vs StarRocks: TPC-H SF10 (Single-Node, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:05:37


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

### Starrocks 4.0.4


**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz (2 vCPUs)- **Memory:** 15.3GB RAM

**Software:**
- **Database:** starrocks 4.0.4


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **2766.6ms** median runtime
- **starrocks** was **3.0×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |   2028.2 |      8273   | exasol   |
| Join-Heavy         |   3401   |      6960.9 | exasol   |
| Complex Analytical |   2799.2 |     12045.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |       11432.3 |         31155.1 |    2.73 |      0.37 | False    |
| Q02     | exasol            | starrocks           |         523.1 |          1966.9 |    3.76 |      0.27 | False    |
| Q03     | exasol            | starrocks           |        3115.5 |          5939.9 |    1.91 |      0.52 | False    |
| Q04     | exasol            | starrocks           |        1550.5 |          9226.2 |    5.95 |      0.17 | False    |
| Q05     | exasol            | starrocks           |        3631.7 |          7086.2 |    1.95 |      0.51 | False    |
| Q06     | exasol            | starrocks           |         591.6 |          3747.8 |    6.34 |      0.16 | False    |
| Q07     | exasol            | starrocks           |       14219.6 |         26109.1 |    1.84 |      0.54 | False    |
| Q08     | exasol            | starrocks           |        1101.7 |          6835.6 |    6.2  |      0.16 | False    |
| Q09     | exasol            | starrocks           |       15278   |         38198.6 |    2.5  |      0.4  | False    |
| Q10     | exasol            | starrocks           |        4905.4 |          6230.6 |    1.27 |      0.79 | False    |
| Q11     | exasol            | starrocks           |         771.8 |          1941.5 |    2.52 |      0.4  | False    |
| Q12     | exasol            | starrocks           |        2472.7 |          9312.9 |    3.77 |      0.27 | False    |
| Q13     | exasol            | starrocks           |       19279.1 |         47022.2 |    2.44 |      0.41 | False    |
| Q14     | exasol            | starrocks           |        3455.5 |         13573.7 |    3.93 |      0.25 | False    |
| Q15     | exasol            | starrocks           |        1861.9 |          8273   |    4.44 |      0.23 | False    |
| Q16     | exasol            | starrocks           |       12548.4 |          1031.9 |    0.08 |     12.16 | True     |
| Q17     | exasol            | starrocks           |         312.3 |          8213.1 |   26.3  |      0.04 | False    |
| Q18     | exasol            | starrocks           |        5013.8 |         59770   |   11.92 |      0.08 | False    |
| Q19     | exasol            | starrocks           |         730.9 |          4370.1 |    5.98 |      0.17 | False    |
| Q20     | exasol            | starrocks           |        1612.5 |          4877.6 |    3.02 |      0.33 | False    |
| Q21     | exasol            | starrocks           |       12553.4 |         55024.1 |    4.38 |      0.23 | False    |
| Q22     | exasol            | starrocks           |        1473.4 |          7376.4 |    5.01 |      0.2  | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1254.4 |      5 |     11432.3 |   11448.7 |   8880.9 |   2734   |  24626.5 |
| Q01     | starrocks |   6057.6 |      5 |     31155.1 |   38366.2 |  18850.3 |  22182.3 |  69103.3 |
| Q02     | exasol    |     98.2 |      5 |       523.1 |    4337.9 |   8591.1 |    379.2 |  19705.5 |
| Q02     | starrocks |    707.9 |      5 |      1966.9 |    2327   |   1245.8 |    805.4 |   3763.8 |
| Q03     | exasol    |    447   |      5 |      3115.5 |    4274.2 |   4063.5 |   1497.2 |  11382.2 |
| Q03     | starrocks |   1744.8 |      5 |      5939.9 |    6035.2 |   1223.7 |   4276.1 |   7647.5 |
| Q04     | exasol    |     90.1 |      5 |      1550.5 |    1311.8 |    790   |    187.9 |   2300.3 |
| Q04     | starrocks |   1031.4 |      5 |      9226.2 |    7549.5 |   4477.3 |    836.6 |  12045.3 |
| Q05     | exasol    |    388.5 |      5 |      3631.7 |    6096.2 |   6092   |   2936.8 |  16974   |
| Q05     | starrocks |   1714.1 |      5 |      7086.2 |    8123   |   4143.8 |   3348   |  13818.5 |
| Q06     | exasol    |     59.2 |      5 |       591.6 |     959.4 |    900.7 |    184.2 |   2331.6 |
| Q06     | starrocks |    601.2 |      5 |      3747.8 |    6287.5 |   7083.4 |    984.7 |  18607.7 |
| Q07     | exasol    |    400.3 |      5 |     14219.6 |    9767.3 |   6969.2 |   1775.5 |  15687.5 |
| Q07     | starrocks |   2063.4 |      5 |     26109.1 |   24876.5 |   7391.2 |  13303.8 |  32230.8 |
| Q08     | exasol    |    110   |      5 |      1101.7 |    1655.1 |   1075.2 |    682.7 |   3147.7 |
| Q08     | starrocks |   1690.6 |      5 |      6835.6 |    9617.2 |   5294.5 |   5323.1 |  18142.6 |
| Q09     | exasol    |   1152.1 |      5 |     15278   |   11127.8 |   6483   |   4035.3 |  16507.1 |
| Q09     | starrocks |   3341.7 |      5 |     38198.6 |   39350.2 |   9112.6 |  27615.4 |  51258.3 |
| Q10     | exasol    |    487.5 |      5 |      4905.4 |   11173   |   9734.2 |   3447.7 |  22372.3 |
| Q10     | starrocks |   1907.5 |      5 |      6230.6 |    7571.5 |   4797.4 |   2733.5 |  12684.2 |
| Q11     | exasol    |     85.6 |      5 |       771.8 |    4181.3 |   7668.4 |    665   |  17898.5 |
| Q11     | starrocks |    404.4 |      5 |      1941.5 |    2702.5 |   2839.3 |    484.9 |   7555.6 |
| Q12     | exasol    |    120.7 |      5 |      2472.7 |    2281.3 |   1181.8 |    759.9 |   3449.8 |
| Q12     | starrocks |   1146.6 |      5 |      9312.9 |    8425   |   3418.8 |   2919.9 |  11545.2 |
| Q13     | exasol    |   1141.8 |      5 |     19279.1 |   18071.4 |   3354.3 |  13952.9 |  21045.1 |
| Q13     | starrocks |   1927.7 |      5 |     47022.2 |   42941.9 |   8846.9 |  32743.6 |  50465.7 |
| Q14     | exasol    |    108.9 |      5 |      3455.5 |    5367.5 |   5573.7 |    720.7 |  14919.6 |
| Q14     | starrocks |    845   |      5 |     13573.7 |   11808.1 |   4694.2 |   5486.5 |  17404   |
| Q15     | exasol    |    118.7 |      5 |      1861.9 |    2081.9 |   1286.9 |    621   |   4160.6 |
| Q15     | starrocks |    777.7 |      5 |      8273   |    9541   |   5720.9 |   2827.1 |  16546.1 |
| Q16     | exasol    |    453.5 |      5 |     12548.4 |   10764.6 |   9253.4 |    995.2 |  22807.5 |
| Q16     | starrocks |    697.8 |      5 |      1031.9 |    3061.7 |   3164.7 |    418   |   7120.7 |
| Q17     | exasol    |     20.3 |      5 |       312.3 |     263.4 |    130.1 |     95.4 |    387.4 |
| Q17     | starrocks |    755   |      5 |      8213.1 |    9677.6 |   5217.1 |   4706.6 |  17415.1 |
| Q18     | exasol    |    679.6 |      5 |      5013.8 |    8787.7 |   9028.5 |   1658.7 |  23654.9 |
| Q18     | starrocks |   2492.2 |      5 |     59770   |   61562.3 |  27544.8 |  20742.7 |  94639.8 |
| Q19     | exasol    |     35.7 |      5 |       730.9 |     898.3 |    785.3 |     63.3 |   2190.9 |
| Q19     | starrocks |   1461.6 |      5 |      4370.1 |    6029.3 |   4015.6 |   3064.2 |  12735.3 |
| Q20     | exasol    |    213.2 |      5 |      1612.5 |    2418.8 |   2336.7 |    451.4 |   6190.4 |
| Q20     | starrocks |    989.8 |      5 |      4877.6 |    7123.3 |   6505.7 |   1920.6 |  17970.6 |
| Q21     | exasol    |    642.9 |      5 |     12553.4 |   10326.4 |   6130   |   3140   |  15765   |
| Q21     | starrocks |   3593.2 |      5 |     55024.1 |   57175.9 |  45010.7 |   6540.8 | 112296   |
| Q22     | exasol    |    145.2 |      5 |      1473.4 |    2099.7 |   1411.2 |    557.6 |   3822.3 |
| Q22     | starrocks |    504   |      5 |      7376.4 |    7010.6 |   2609.4 |   3094.2 |   9402.2 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 2766.6ms
- Average: 5895.2ms
- Range: 63.3ms - 24626.5ms

**#2. Starrocks**
- Median: 8243.0ms
- Average: 17143.8ms
- Range: 418.0ms - 112296.5ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 3706.0 | 2270.1 | 720.7 | 13952.9 |
| 1 | 8 | 6931.3 | 2152.8 | 63.3 | 21018.4 |
| 10 | 7 | 6011.9 | 1738.0 | 387.4 | 21045.1 |
| 11 | 7 | 1993.3 | 1473.4 | 557.6 | 4160.6 |
| 12 | 7 | 8044.6 | 2799.2 | 187.9 | 19705.5 |
| 13 | 7 | 7692.1 | 3888.6 | 184.2 | 15769.3 |
| 14 | 7 | 7284.5 | 1775.5 | 591.6 | 24626.5 |
| 2 | 8 | 4772.8 | 3234.9 | 156.7 | 14516.8 |
| 3 | 8 | 6699.9 | 3984.7 | 780.5 | 17898.5 |
| 4 | 8 | 5000.0 | 2450.4 | 365.2 | 15765.0 |
| 5 | 7 | 7374.2 | 4049.2 | 1840.5 | 21251.0 |
| 6 | 7 | 5269.0 | 3447.7 | 665.0 | 22372.3 |
| 7 | 7 | 5168.8 | 2587.4 | 523.1 | 23654.9 |
| 8 | 7 | 6922.1 | 3140.0 | 95.4 | 16507.1 |
| 9 | 7 | 5895.1 | 2331.6 | 297.2 | 22807.5 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1473.4ms
- **Worst stream median:** 4049.2ms
- **Performance variance:** 174.8% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 17211.8 | 7776.9 | 916.6 | 55703.0 |
| 1 | 8 | 18040.3 | 9474.2 | 2802.5 | 47022.2 |
| 10 | 7 | 13799.2 | 14193.7 | 3282.8 | 34028.5 |
| 11 | 7 | 14225.4 | 12045.3 | 5951.0 | 32230.8 |
| 12 | 7 | 21663.2 | 20742.7 | 836.6 | 59770.0 |
| 13 | 7 | 16524.2 | 7086.2 | 2733.5 | 34797.2 |
| 14 | 7 | 17203.5 | 11364.1 | 2579.9 | 50449.4 |
| 2 | 8 | 18170.1 | 8721.2 | 3094.2 | 69103.3 |
| 3 | 8 | 13271.7 | 8679.0 | 2614.0 | 38198.6 |
| 4 | 8 | 17724.2 | 5996.9 | 484.9 | 112296.5 |
| 5 | 7 | 21860.5 | 10264.4 | 418.0 | 91324.1 |
| 6 | 7 | 8650.8 | 8273.0 | 3624.2 | 12684.2 |
| 7 | 7 | 19837.6 | 5865.0 | 805.4 | 94639.8 |
| 8 | 7 | 21683.9 | 12290.1 | 1966.9 | 55024.1 |
| 9 | 7 | 17475.8 | 7120.7 | 2827.1 | 76955.9 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 5865.0ms
- **Worst stream median:** 20742.7ms
- **Performance variance:** 253.7% difference between fastest and slowest streams
- This demonstrates Starrocks's ability to handle concurrent query loads with **varying** performance across streams

**Query Distribution Method:**
- Query distribution was **randomized** (seed: 42) for realistic concurrent user simulation


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
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