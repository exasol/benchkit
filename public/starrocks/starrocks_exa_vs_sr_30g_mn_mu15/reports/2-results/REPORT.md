# Exasol vs StarRocks: TPC-H SF30 (Multi-Node 3, 15 Streams) - Detailed Query Results

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 16:07:06


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
- **exasol** was the fastest overall with **4041.0ms** median runtime
- **starrocks** was **6.3×** slower- Tested **220** total query executions across 22 different query types
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
| Aggregation        |   2802   |     15966   | exasol   |
| Join-Heavy         |   4430.6 |     23683.3 | exasol   |
| Complex Analytical |   5398.6 |     48433.1 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6866.8 |        226415   |   32.97 |      0.03 | False    |
| Q02     | exasol            | starrocks           |        1073   |          4435.5 |    4.13 |      0.24 | False    |
| Q03     | exasol            | starrocks           |        5297.4 |         28330.8 |    5.35 |      0.19 | False    |
| Q04     | exasol            | starrocks           |        2131.4 |        300032   |  140.77 |      0.01 | False    |
| Q05     | exasol            | starrocks           |       30751.5 |         31095.5 |    1.01 |      0.99 | False    |
| Q06     | exasol            | starrocks           |         554.9 |          6366.9 |   11.47 |      0.09 | False    |
| Q07     | exasol            | starrocks           |       29359.7 |         45919.2 |    1.56 |      0.64 | False    |
| Q08     | exasol            | starrocks           |        4961.1 |         16473.3 |    3.32 |      0.3  | False    |
| Q09     | exasol            | starrocks           |       45606.7 |         39890.6 |    0.87 |      1.14 | True     |
| Q10     | exasol            | starrocks           |       34500.5 |         31651.7 |    0.92 |      1.09 | True     |
| Q11     | exasol            | starrocks           |        1969.4 |          1898.2 |    0.96 |      1.04 | True     |
| Q12     | exasol            | starrocks           |        4280.2 |         23592.4 |    5.51 |      0.18 | False    |
| Q13     | exasol            | starrocks           |       35692.7 |        157089   |    4.4  |      0.23 | False    |
| Q14     | exasol            | starrocks           |        2628.7 |         17007.7 |    6.47 |      0.15 | False    |
| Q15     | exasol            | starrocks           |        3635.8 |         17646.9 |    4.85 |      0.21 | False    |
| Q16     | exasol            | starrocks           |       14140.7 |          5289.7 |    0.37 |      2.67 | True     |
| Q17     | exasol            | starrocks           |         583.3 |         36337.6 |   62.3  |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3939.8 |        107288   |   27.23 |      0.04 | False    |
| Q19     | exasol            | starrocks           |         903.6 |          9965.9 |   11.03 |      0.09 | False    |
| Q20     | exasol            | starrocks           |        3869.3 |         15966   |    4.13 |      0.24 | False    |
| Q21     | exasol            | starrocks           |       15371.8 |         91833.4 |    5.97 |      0.17 | False    |
| Q22     | exasol            | starrocks           |        1000.7 |         12311.4 |   12.3  |      0.08 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1276.9 |      5 |      6866.8 |   16459.9 |  16535.9 |   4827.3 |  43663.7 |
| Q01     | starrocks |  17636.5 |      5 |    226415   |  178553   | 128537   |  22693   | 300119   |
| Q02     | exasol    |    113.6 |      5 |      1073   |     916.2 |    313.4 |    520.4 |   1190.2 |
| Q02     | starrocks |   1086.6 |      5 |      4435.5 |    6097.8 |   3426.7 |   2964.3 |  10766.9 |
| Q03     | exasol    |   1176.4 |      5 |      5297.4 |   12615   |  13120   |   3253.3 |  34114.1 |
| Q03     | starrocks |   6600.8 |      5 |     28330.8 |   32548.4 |  10151.1 |  23845.3 |  48656.7 |
| Q04     | exasol    |    290   |      5 |      2131.4 |    2593   |   1721.7 |    980.1 |   5398.6 |
| Q04     | starrocks |   4778.5 |      5 |    300032   |  270933   |  55007.4 | 173675   | 300111   |
| Q05     | exasol    |   1121.1 |      5 |     30751.5 |   21436   |  17778.5 |   2132.2 |  40632.2 |
| Q05     | starrocks |   5898   |      5 |     31095.5 |   68963.4 |  63291.4 |  15176.2 | 149061   |
| Q06     | exasol    |     69.9 |      5 |       554.9 |    1249.2 |   1828.8 |    157.7 |   4507.3 |
| Q06     | starrocks |   2416.6 |      5 |      6366.9 |   14540.7 |  19750.6 |   2838.2 |  49366.2 |
| Q07     | exasol    |   1397.2 |      5 |     29359.7 |   33462   |   9817.1 |  24700.6 |  46269.7 |
| Q07     | starrocks |   4635.1 |      5 |     45919.2 |   55023.9 |  38543.9 |   9335.7 |  97849.7 |
| Q08     | exasol    |    456.2 |      5 |      4961.1 |   10746.7 |  15617   |    641.7 |  38488.4 |
| Q08     | starrocks |   5642   |      5 |     16473.3 |   17340.9 |   4469.9 |  12876.5 |  23682.2 |
| Q09     | exasol    |   3716.1 |      5 |     45606.7 |   45170.8 |   6678.9 |  36943.8 |  54180   |
| Q09     | starrocks |   9924.8 |      5 |     39890.6 |   45252.3 |  18443.9 |  27353.3 |  66206   |
| Q10     | exasol    |    864.8 |      5 |     34500.5 |   29903.3 |  14660.4 |   4309.1 |  40045.7 |
| Q10     | starrocks |   9643.5 |      5 |     31651.7 |   31568.2 |   4974.4 |  26354.2 |  37103.5 |
| Q11     | exasol    |   1774.6 |      5 |      1969.4 |    2191.5 |   1099.4 |    605.7 |   3313.4 |
| Q11     | starrocks |    786.6 |      5 |      1898.2 |    3170.4 |   2963.3 |   1365   |   8401.1 |
| Q12     | exasol    |    431.7 |      5 |      4280.2 |    5475.4 |   5741.9 |    932.8 |  15312.2 |
| Q12     | starrocks |   3514.8 |      5 |     23592.4 |   25560.1 |  16452.3 |   9921.2 |  47120.4 |
| Q13     | exasol    |   2473.2 |      5 |     35692.7 |   51773.8 |  36342.1 |  31801.8 | 116417   |
| Q13     | starrocks |   7214.3 |      5 |    157089   |  131200   |  62315.9 |  20255.4 | 165099   |
| Q14     | exasol    |    897.6 |      5 |      2628.7 |    9397.1 |   9912.1 |   1379   |  21094   |
| Q14     | starrocks |   3256   |      5 |     17007.7 |   20038.6 |  11810.3 |   7050.4 |  35534.2 |
| Q15     | exasol    |    346.3 |      5 |      3635.8 |    5397.5 |   5380.8 |   1759.3 |  14907.6 |
| Q15     | starrocks |   2638.7 |      5 |     17646.9 |   21020.3 |  11088.5 |  13885.8 |  40557.2 |
| Q16     | exasol    |    573.1 |      5 |     14140.7 |   17233.5 |  14931   |   1513.2 |  34218.7 |
| Q16     | starrocks |   1518.9 |      5 |      5289.7 |    5306.1 |   3284   |   1229.9 |  10267.1 |
| Q17     | exasol    |     85.2 |      5 |       583.3 |     564.9 |    196.3 |    342.3 |    864.7 |
| Q17     | starrocks |   3104.4 |      5 |     36337.6 |   34307.1 |  15584.4 |  11611   |  48433.1 |
| Q18     | exasol    |    732.5 |      5 |      3939.8 |   13455.4 |  14296.4 |   2089.1 |  29180.6 |
| Q18     | starrocks |  11100   |      5 |    107288   |  100510   |  15628.9 |  75837.7 | 115660   |
| Q19     | exasol    |    111.5 |      5 |       903.6 |     773.3 |    427.4 |    190.4 |   1322.4 |
| Q19     | starrocks |   3467.6 |      5 |      9965.9 |    9132.5 |   4415.5 |   3485.6 |  15334.1 |
| Q20     | exasol    |    403   |      5 |      3869.3 |    6296.5 |   7902.9 |    888   |  20259.8 |
| Q20     | starrocks |   3404   |      5 |     15966   |   20054.6 |  22140.1 |   3984.1 |  58150.9 |
| Q21     | exasol    |  16412   |      5 |     15371.8 |   21678.6 |  16491.3 |   2844.6 |  39902.2 |
| Q21     | starrocks |  18091.8 |      5 |     91833.4 |  128740   |  68484.7 |  59895.5 | 218487   |
| Q22     | exasol    |    165.2 |      5 |      1000.7 |    1267.3 |    664   |    632.3 |   2190.2 |
| Q22     | starrocks |   1306.2 |      5 |     12311.4 |   12843.2 |   7992.1 |   4923.9 |  25374.8 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 4041.0ms
- Average: 14093.5ms
- Range: 157.7ms - 116417.2ms

**#2. Starrocks**
- Median: 25564.4ms
- Average: 56032.0ms
- Range: 1229.9ms - 300119.4ms


### Per-Stream Performance Analysis

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show how queries were distributed and performed across each stream for each system:

#### Exasol - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 15665.4 | 1639.8 | 157.7 | 116417.2 |
| 1 | 8 | 14887.8 | 3830.6 | 190.4 | 46269.7 |
| 10 | 7 | 9013.4 | 1759.3 | 587.2 | 35692.7 |
| 11 | 7 | 12922.3 | 1000.7 | 540.8 | 41486.1 |
| 12 | 7 | 12223.0 | 3939.8 | 520.4 | 40776.8 |
| 13 | 7 | 15814.6 | 4309.1 | 554.9 | 45606.7 |
| 14 | 7 | 16144.9 | 5089.9 | 457.5 | 43663.7 |
| 2 | 8 | 13495.6 | 5914.0 | 342.3 | 38488.4 |
| 3 | 8 | 13492.9 | 4553.8 | 2548.9 | 54180.0 |
| 4 | 8 | 12773.1 | 4751.7 | 583.3 | 38627.0 |
| 5 | 7 | 17285.9 | 5398.6 | 1513.2 | 38124.5 |
| 6 | 7 | 16435.9 | 15312.2 | 2131.4 | 40045.7 |
| 7 | 7 | 8685.9 | 3882.9 | 909.4 | 29018.8 |
| 8 | 7 | 16703.5 | 12150.1 | 447.1 | 48346.7 |
| 9 | 7 | 15880.0 | 4507.3 | 568.8 | 40632.2 |

**Stream Performance Analysis for Exasol:**
- **Best stream median:** 1000.7ms
- **Worst stream median:** 15312.2ms
- **Performance variance:** 1430.1% difference between fastest and slowest streams
- This demonstrates Exasol's ability to handle concurrent query loads with **varying** performance across streams
#### Starrocks - Stream Performance

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 43858.5 | 16740.5 | 1898.2 | 165098.9 |
| 1 | 8 | 66208.1 | 15681.1 | 3485.6 | 280774.6 |
| 10 | 7 | 47651.2 | 48433.1 | 4435.5 | 149828.4 |
| 11 | 7 | 60441.0 | 23684.4 | 6709.1 | 300072.5 |
| 12 | 7 | 69137.8 | 75837.7 | 2964.3 | 173674.8 |
| 13 | 7 | 55110.4 | 35897.1 | 6366.9 | 149060.8 |
| 14 | 7 | 71812.8 | 15334.1 | 2838.2 | 282750.8 |
| 2 | 8 | 60538.5 | 28017.1 | 4923.9 | 300119.4 |
| 3 | 8 | 63811.8 | 32845.3 | 8401.1 | 226414.9 |
| 4 | 8 | 37491.9 | 10766.1 | 1560.7 | 218487.3 |
| 5 | 7 | 76043.1 | 29525.7 | 1229.9 | 300111.2 |
| 6 | 7 | 63639.0 | 26834.7 | 1365.0 | 300032.5 |
| 7 | 7 | 31343.5 | 17150.5 | 9965.9 | 115659.8 |
| 8 | 7 | 61177.7 | 48331.6 | 3653.3 | 184050.3 |
| 9 | 7 | 33393.6 | 25374.8 | 3995.8 | 95208.0 |

**Stream Performance Analysis for Starrocks:**
- **Best stream median:** 10766.1ms
- **Worst stream median:** 75837.7ms
- **Performance variance:** 604.4% difference between fastest and slowest streams
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