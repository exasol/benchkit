# Exasol vs ClickHouse Performance Comparison on TPC-H SF30 - Detailed Query Results

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-24 15:46:50


## Overview

This report presents the complete query-by-query performance results for 4 database systems tested using the TPC-H benchmark at scale factor 30.

**Systems Compared:**
- **exasol**
- **clickhouse**
- **clickhouse_tuned**
- **clickhouse_stat**

## Systems Under Test

### Exasol 2025.1.0

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** exasol 2025.1.0

### Clickhouse 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58

### Clickhouse_tuned 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58

### Clickhouse_stat 25.9.4.58

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** clickhouse 25.9.4.58


## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **165.9ms** median runtime
- **clickhouse_stat** was **10.0×** slower
- Tested **616** total query executions across 22 different query types

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

| Query Type         |   clickhouse |   clickhouse_stat |   clickhouse_tuned |   exasol | Winner   |
|--------------------|--------------|-------------------|--------------------|----------|----------|
| Aggregation        |        217.2 |             275.3 |              530.9 |     63.4 | exasol   |
| Join-Heavy         |       3484.6 |            1414.9 |             3477   |    138.4 | exasol   |
| Complex Analytical |       2445   |            2744.9 |             2472.3 |    213.5 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse_tuned    |         622.3 |          1613.6 |    2.59 |      0.39 | False    |
| Q02     | exasol            | clickhouse_tuned    |          51.9 |           615.3 |   11.86 |      0.08 | False    |
| Q03     | exasol            | clickhouse_tuned    |         213.5 |          2440.4 |   11.43 |      0.09 | False    |
| Q04     | exasol            | clickhouse_tuned    |          48   |          4707   |   98.06 |      0.01 | False    |
| Q05     | exasol            | clickhouse_tuned    |         154.4 |          5313.8 |   34.42 |      0.03 | False    |
| Q06     | exasol            | clickhouse_tuned    |          32.3 |           128.3 |    3.97 |      0.25 | False    |
| Q07     | exasol            | clickhouse_tuned    |         177.6 |          2951.5 |   16.62 |      0.06 | False    |
| Q08     | exasol            | clickhouse_tuned    |          60.7 |          5712.7 |   94.11 |      0.01 | False    |
| Q09     | exasol            | clickhouse_tuned    |         696.8 |          7658.8 |   10.99 |      0.09 | False    |
| Q10     | exasol            | clickhouse_tuned    |         343.7 |          1652   |    4.81 |      0.21 | False    |
| Q11     | exasol            | clickhouse_tuned    |         121   |           400.8 |    3.31 |      0.3  | False    |
| Q12     | exasol            | clickhouse_tuned    |          63.4 |           530.9 |    8.37 |      0.12 | False    |
| Q13     | exasol            | clickhouse_tuned    |         449.1 |          2443.7 |    5.44 |      0.18 | False    |
| Q14     | exasol            | clickhouse_tuned    |          57.7 |           131.4 |    2.28 |      0.44 | False    |
| Q15     | exasol            | clickhouse_tuned    |         205.9 |           191.3 |    0.93 |      1.08 | True     |
| Q16     | exasol            | clickhouse_tuned    |         377.5 |           441.2 |    1.17 |      0.86 | False    |
| Q17     | exasol            | clickhouse_tuned    |          21.6 |           811.8 |   37.58 |      0.03 | False    |
| Q18     | exasol            | clickhouse_tuned    |         418.9 |          6865.3 |   16.39 |      0.06 | False    |
| Q19     | exasol            | clickhouse_tuned    |          22.2 |          3895.4 |  175.47 |      0.01 | False    |
| Q20     | exasol            | clickhouse_tuned    |         228.7 |           847.9 |    3.71 |      0.27 | False    |
| Q21     | exasol            | clickhouse_tuned    |         261.9 |          9568.8 |   36.54 |      0.03 | False    |
| Q22     | exasol            | clickhouse_tuned    |          78.8 |           362.4 |    4.6  |      0.22 | False    |
| Q01     | exasol            | clickhouse          |         622.3 |          1592.2 |    2.56 |      0.39 | False    |
| Q02     | exasol            | clickhouse          |          51.9 |           611.2 |   11.78 |      0.08 | False    |
| Q03     | exasol            | clickhouse          |         213.5 |          2435   |   11.41 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |          48   |          1410.4 |   29.38 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |         154.4 |          5338.4 |   34.58 |      0.03 | False    |
| Q06     | exasol            | clickhouse          |          32.3 |           126.7 |    3.92 |      0.25 | False    |
| Q07     | exasol            | clickhouse          |         177.6 |          2920.1 |   16.44 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |          60.7 |          5646.5 |   93.02 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         696.8 |          7560.3 |   10.85 |      0.09 | False    |
| Q10     | exasol            | clickhouse          |         343.7 |          1615.7 |    4.7  |      0.21 | False    |
| Q11     | exasol            | clickhouse          |         121   |           389.9 |    3.22 |      0.31 | False    |
| Q12     | exasol            | clickhouse          |          63.4 |           528.8 |    8.34 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |         449.1 |          2431.7 |    5.41 |      0.18 | False    |
| Q14     | exasol            | clickhouse          |          57.7 |           129   |    2.24 |      0.45 | False    |
| Q15     | exasol            | clickhouse          |         205.9 |           182   |    0.88 |      1.13 | True     |
| Q16     | exasol            | clickhouse          |         377.5 |           338.3 |    0.9  |      1.12 | True     |
| Q17     | exasol            | clickhouse          |          21.6 |          2589.9 |  119.9  |      0.01 | False    |
| Q18     | exasol            | clickhouse          |         418.9 |          2556.2 |    6.1  |      0.16 | False    |
| Q19     | exasol            | clickhouse          |          22.2 |          1618.7 |   72.91 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         228.7 |           217.2 |    0.95 |      1.05 | True     |
| Q21     | exasol            | clickhouse          |         261.9 |         20869.6 |   79.69 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          78.8 |           379.7 |    4.82 |      0.21 | False    |
| Q01     | exasol            | clickhouse_stat     |         622.3 |          1750.8 |    2.81 |      0.36 | False    |
| Q02     | exasol            | clickhouse_stat     |          51.9 |           531.5 |   10.24 |      0.1  | False    |
| Q03     | exasol            | clickhouse_stat     |         213.5 |          2801.3 |   13.12 |      0.08 | False    |
| Q04     | exasol            | clickhouse_stat     |          48   |          1614.4 |   33.63 |      0.03 | False    |
| Q05     | exasol            | clickhouse_stat     |         154.4 |          5460.1 |   35.36 |      0.03 | False    |
| Q06     | exasol            | clickhouse_stat     |          32.3 |           158   |    4.89 |      0.2  | False    |
| Q07     | exasol            | clickhouse_stat     |         177.6 |          3063.2 |   17.25 |      0.06 | False    |
| Q08     | exasol            | clickhouse_stat     |          60.7 |          1113.6 |   18.35 |      0.05 | False    |
| Q09     | exasol            | clickhouse_stat     |         696.8 |          3163.1 |    4.54 |      0.22 | False    |
| Q10     | exasol            | clickhouse_stat     |         343.7 |          1736.3 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse_stat     |         121   |           401.3 |    3.32 |      0.3  | False    |
| Q12     | exasol            | clickhouse_stat     |          63.4 |           669.3 |   10.56 |      0.09 | False    |
| Q13     | exasol            | clickhouse_stat     |         449.1 |          2440.9 |    5.44 |      0.18 | False    |
| Q14     | exasol            | clickhouse_stat     |          57.7 |           243.3 |    4.22 |      0.24 | False    |
| Q15     | exasol            | clickhouse_stat     |         205.9 |           236.1 |    1.15 |      0.87 | False    |
| Q16     | exasol            | clickhouse_stat     |         377.5 |           347.3 |    0.92 |      1.09 | True     |
| Q17     | exasol            | clickhouse_stat     |          21.6 |          2805.5 |  129.88 |      0.01 | False    |
| Q18     | exasol            | clickhouse_stat     |         418.9 |          2755.6 |    6.58 |      0.15 | False    |
| Q19     | exasol            | clickhouse_stat     |          22.2 |          2800.3 |  126.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse_stat     |         228.7 |           275.3 |    1.2  |      0.83 | False    |
| Q21     | exasol            | clickhouse_stat     |         261.9 |         21243.2 |   81.11 |      0.01 | False    |
| Q22     | exasol            | clickhouse_stat     |          78.8 |           396.7 |    5.03 |      0.2  | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |   1603.8 |      7 |      1592.2 |    1597.4 |     16.2 |   1580.2 |   1618.2 |
| Q01     | clickhouse_stat  |   1759.4 |      7 |      1750.8 |    1755.9 |      9.1 |   1746.1 |   1768   |
| Q01     | clickhouse_tuned |   1611.5 |      7 |      1613.6 |    1616.4 |      9.5 |   1605.9 |   1633.8 |
| Q01     | exasol           |    621.5 |      7 |       622.3 |     622.5 |      1   |    621.4 |    623.9 |
| Q02     | clickhouse       |    836.1 |      7 |       611.2 |     613.4 |     15.6 |    597.2 |    636.8 |
| Q02     | clickhouse_stat  |    663.8 |      7 |       531.5 |     530.9 |      7.5 |    518.3 |    538.4 |
| Q02     | clickhouse_tuned |    824.7 |      7 |       615.3 |     622.6 |     15.1 |    601.5 |    639.5 |
| Q02     | exasol           |     67.4 |      7 |        51.9 |      52   |      0.5 |     51.2 |     52.5 |
| Q03     | clickhouse       |   2683.9 |      7 |      2435   |    2423.9 |     27.6 |   2379.3 |   2445.5 |
| Q03     | clickhouse_stat  |   3171.3 |      7 |      2801.3 |    2817.1 |     55.1 |   2744.9 |   2908.5 |
| Q03     | clickhouse_tuned |   2698.7 |      7 |      2440.4 |    2437.9 |     34.2 |   2389.2 |   2487.8 |
| Q03     | exasol           |    219.1 |      7 |       213.5 |     210.2 |      7.5 |    200.7 |    220.5 |
| Q04     | clickhouse       |   1482.4 |      7 |      1410.4 |    1386.6 |     40.4 |   1336.4 |   1427.2 |
| Q04     | clickhouse_stat  |   1676.7 |      7 |      1614.4 |    1613.5 |     24.1 |   1579.7 |   1638.8 |
| Q04     | clickhouse_tuned |   5293.9 |      7 |      4707   |    4685.3 |    158.3 |   4406.2 |   4930.7 |
| Q04     | exasol           |     49.5 |      7 |        48   |      48.3 |      1   |     47.2 |     50.3 |
| Q05     | clickhouse       |   5639.2 |      7 |      5338.4 |    5324.9 |     59.9 |   5252.4 |   5402.4 |
| Q05     | clickhouse_stat  |   6255.9 |      7 |      5460.1 |    5534.6 |    177.6 |   5357   |   5882   |
| Q05     | clickhouse_tuned |   5811.4 |      7 |      5313.8 |    5319.9 |     76   |   5231.7 |   5438.4 |
| Q05     | exasol           |    207.2 |      7 |       154.4 |     154.4 |      0.8 |    153.1 |    155.5 |
| Q06     | clickhouse       |    132.3 |      7 |       126.7 |     127.6 |      4.9 |    122.7 |    136.7 |
| Q06     | clickhouse_stat  |    334.2 |      7 |       158   |     162.4 |      9.9 |    153.7 |    182.2 |
| Q06     | clickhouse_tuned |    276.8 |      7 |       128.3 |     128.3 |      3   |    124.8 |    134.1 |
| Q06     | exasol           |     32.8 |      7 |        32.3 |      32.2 |      0.3 |     31.6 |     32.5 |
| Q07     | clickhouse       |   3212.4 |      7 |      2920.1 |    2898   |     77.7 |   2789.7 |   2973.2 |
| Q07     | clickhouse_stat  |   3340.7 |      7 |      3063.2 |    3064.8 |     26.5 |   3036.9 |   3112   |
| Q07     | clickhouse_tuned |   3241.6 |      7 |      2951.5 |    2947.1 |     73.2 |   2828.7 |   3025.1 |
| Q07     | exasol           |    183.2 |      7 |       177.6 |     177.6 |      1.2 |    176.4 |    179.5 |
| Q08     | clickhouse       |   5644.9 |      7 |      5646.5 |    5661.7 |     66.9 |   5566.5 |   5757.2 |
| Q08     | clickhouse_stat  |   1116.1 |      7 |      1113.6 |    1111.4 |     23.8 |   1080.9 |   1149.9 |
| Q08     | clickhouse_tuned |   5676.7 |      7 |      5712.7 |    5702.9 |     54.3 |   5610.2 |   5773   |
| Q08     | exasol           |     71.2 |      7 |        60.7 |      66.8 |     17   |     59.9 |    105.4 |
| Q09     | clickhouse       |   7980.7 |      7 |      7560.3 |    7544.3 |     90   |   7372.7 |   7653.5 |
| Q09     | clickhouse_stat  |   3635.7 |      7 |      3163.1 |    3149.8 |     63.7 |   3051.4 |   3221.2 |
| Q09     | clickhouse_tuned |   8137.7 |      7 |      7658.8 |    7640.9 |     90.6 |   7540   |   7751.1 |
| Q09     | exasol           |    727.5 |      7 |       696.8 |     697.3 |      1.3 |    696.2 |    699.5 |
| Q10     | clickhouse       |   1892.8 |      7 |      1615.7 |    1633.6 |     47.7 |   1573.7 |   1716.8 |
| Q10     | clickhouse_stat  |   1874.1 |      7 |      1736.3 |    1741.9 |     41.6 |   1679.9 |   1794.3 |
| Q10     | clickhouse_tuned |   1901   |      7 |      1652   |    1649   |     54   |   1589.7 |   1722.3 |
| Q10     | exasol           |    348.8 |      7 |       343.7 |     342.6 |      5.6 |    333.8 |    348.5 |
| Q11     | clickhouse       |    456.4 |      7 |       389.9 |     393.1 |     11.9 |    378.4 |    410.8 |
| Q11     | clickhouse_stat  |    462.6 |      7 |       401.3 |     400.3 |      7.3 |    389.1 |    409.2 |
| Q11     | clickhouse_tuned |    459.2 |      7 |       400.8 |     403.3 |     10.1 |    387.1 |    417.8 |
| Q11     | exasol           |    117.5 |      7 |       121   |     120.8 |      1.8 |    118.7 |    123.7 |
| Q12     | clickhouse       |   1321.7 |      7 |       528.8 |     526.7 |     13   |    505.8 |    540.7 |
| Q12     | clickhouse_stat  |    817.5 |      7 |       669.3 |     659.2 |     34.2 |    583.2 |    684.7 |
| Q12     | clickhouse_tuned |   1294   |      7 |       530.9 |     532.5 |     10.5 |    517.6 |    549.7 |
| Q12     | exasol           |     65.1 |      7 |        63.4 |      63.3 |      0.5 |     62.6 |     64   |
| Q13     | clickhouse       |   2631.6 |      7 |      2431.7 |    2452   |     47.2 |   2407.5 |   2536.3 |
| Q13     | clickhouse_stat  |   2692   |      7 |      2440.9 |    2449.5 |     64.1 |   2359.8 |   2574.1 |
| Q13     | clickhouse_tuned |   2674.4 |      7 |      2443.7 |    2463.2 |     66.7 |   2371.2 |   2555.2 |
| Q13     | exasol           |    451.6 |      7 |       449.1 |     448.5 |      2   |    445.1 |    451.3 |
| Q14     | clickhouse       |    129.5 |      7 |       129   |     129.3 |      2.6 |    126   |    134.6 |
| Q14     | clickhouse_stat  |    250.5 |      7 |       243.3 |     249.8 |     14   |    235   |    268.5 |
| Q14     | clickhouse_tuned |    130.9 |      7 |       131.4 |     130.7 |      2.1 |    127.3 |    133.1 |
| Q14     | exasol           |     57.6 |      7 |        57.7 |      57.8 |      0.4 |     57.3 |     58.3 |
| Q15     | clickhouse       |    215.9 |      7 |       182   |     180.1 |     24.6 |    154.3 |    212.6 |
| Q15     | clickhouse_stat  |    290.6 |      7 |       236.1 |     236.6 |      4   |    231.9 |    242.8 |
| Q15     | clickhouse_tuned |    216.5 |      7 |       191.3 |     189.7 |     19.4 |    169.5 |    215.5 |
| Q15     | exasol           |    208.4 |      7 |       205.9 |     205.6 |      2.4 |    200.4 |    207.7 |
| Q16     | clickhouse       |    331.8 |      7 |       338.3 |     338.6 |      1.8 |    336.7 |    341.3 |
| Q16     | clickhouse_stat  |    335.3 |      7 |       347.3 |     349.4 |      9.5 |    339.8 |    362.8 |
| Q16     | clickhouse_tuned |    499.9 |      7 |       441.2 |     442.5 |     10.3 |    433.8 |    464.3 |
| Q16     | exasol           |    385.1 |      7 |       377.5 |     378.6 |      5.6 |    373.5 |    390.1 |
| Q17     | clickhouse       |   2784.8 |      7 |      2589.9 |    2580   |     24.1 |   2543.7 |   2609.2 |
| Q17     | clickhouse_stat  |   3027   |      7 |      2805.5 |    2796.9 |     40.9 |   2709.8 |   2841.4 |
| Q17     | clickhouse_tuned |    701   |      7 |       811.8 |     814.3 |      7.1 |    805.3 |    823.3 |
| Q17     | exasol           |     22.1 |      7 |        21.6 |      21.4 |      0.5 |     20.7 |     22   |
| Q18     | clickhouse       |   2571.2 |      7 |      2556.2 |    2543.1 |     49.9 |   2464.5 |   2597.9 |
| Q18     | clickhouse_stat  |   2784.2 |      7 |      2755.6 |    2760.3 |     72.1 |   2651.6 |   2887.8 |
| Q18     | clickhouse_tuned |   7973.3 |      7 |      6865.3 |    6884.1 |    122.3 |   6743   |   7133.7 |
| Q18     | exasol           |    419.8 |      7 |       418.9 |     418.9 |      1.3 |    417.2 |    421.2 |
| Q19     | clickhouse       |   1597.7 |      7 |      1618.7 |    1621.8 |      9.8 |   1609.9 |   1636.6 |
| Q19     | clickhouse_stat  |   2754.2 |      7 |      2800.3 |    2803.1 |     33.9 |   2761.3 |   2861.4 |
| Q19     | clickhouse_tuned |   4301.4 |      7 |      3895.4 |    3903.5 |     17.5 |   3891.7 |   3939.6 |
| Q19     | exasol           |     22   |      7 |        22.2 |      22.2 |      0.3 |     21.8 |     22.6 |
| Q20     | clickhouse       |    248.9 |      7 |       217.2 |     217.3 |      2   |    213.7 |    219.4 |
| Q20     | clickhouse_stat  |    332.2 |      7 |       275.3 |     274.9 |      4.6 |    266   |    280.9 |
| Q20     | clickhouse_tuned |   1094.3 |      7 |       847.9 |     847.2 |     24.7 |    827.8 |    897.7 |
| Q20     | exasol           |    230.4 |      7 |       228.7 |     227.7 |      1.5 |    225.8 |    229.1 |
| Q21     | clickhouse       |  21315.7 |      7 |     20869.6 |   20892.9 |    122.7 |  20749.5 |  21093.3 |
| Q21     | clickhouse_stat  |  21772.8 |      7 |     21243.2 |   21235.4 |    175.2 |  20921.7 |  21416.4 |
| Q21     | clickhouse_tuned |  11408.7 |      7 |      9568.8 |    9638   |    182.4 |   9425.1 |   9982.5 |
| Q21     | exasol           |    263.7 |      7 |       261.9 |     268.3 |     18.3 |    260.3 |    309.7 |
| Q22     | clickhouse       |    395.8 |      7 |       379.7 |     393.8 |     28.7 |    368.4 |    446.5 |
| Q22     | clickhouse_stat  |    412.5 |      7 |       396.7 |     395.4 |      9.2 |    383.4 |    410.6 |
| Q22     | clickhouse_tuned |    404.8 |      7 |       362.4 |     358.3 |     32.5 |    315.6 |    394.1 |
| Q22     | exasol           |     80.7 |      7 |        78.8 |      78.7 |      0.3 |     78.2 |     79.1 |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 165.9ms
- Average: 214.4ms
- Range: 20.7ms - 699.5ms

**#2. Clickhouse**
- Median: 1608.8ms
- Average: 2794.5ms
- Range: 122.7ms - 21093.3ms

**#3. Clickhouse_tuned**
- Median: 1615.2ms
- Average: 2698.1ms
- Range: 124.8ms - 9982.5ms

**#4. Clickhouse_stat**
- Median: 1659.3ms
- Average: 2549.7ms
- Range: 153.7ms - 21416.4ms


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 30
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