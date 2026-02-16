# Exasol vs ClickHouse Performance Comparison on TPC-H SF10 - Detailed Query Results

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-24 14:55:06


## Overview

This report presents the complete query-by-query performance results for 4 database systems tested using the TPC-H benchmark at scale factor 10.

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
- **exasol** was the fastest overall with **63.6ms** median runtime
- **clickhouse_tuned** was **8.7×** slower
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
| Aggregation        |        114   |             125.6 |              181.6 |     27.3 | exasol   |
| Join-Heavy         |       1016.4 |             442.5 |             1054.4 |     55.9 | exasol   |
| Complex Analytical |        732.1 |             745.2 |              825.7 |     95.3 | exasol   |

### Query-by-Query Results

The following table shows the median execution time for each query across all systems:

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse_tuned    |         207   |           563.6 |    2.72 |      0.37 | False    |
| Q02     | exasol            | clickhouse_tuned    |          31.3 |           252.3 |    8.06 |      0.12 | False    |
| Q03     | exasol            | clickhouse_tuned    |          95.3 |           827.7 |    8.69 |      0.12 | False    |
| Q04     | exasol            | clickhouse_tuned    |          20.8 |          1179.4 |   56.7  |      0.02 | False    |
| Q05     | exasol            | clickhouse_tuned    |          60   |          1587.9 |   26.46 |      0.04 | False    |
| Q06     | exasol            | clickhouse_tuned    |          13.7 |            55.7 |    4.07 |      0.25 | False    |
| Q07     | exasol            | clickhouse_tuned    |          68.9 |           848   |   12.31 |      0.08 | False    |
| Q08     | exasol            | clickhouse_tuned    |          30.7 |          1705.3 |   55.55 |      0.02 | False    |
| Q09     | exasol            | clickhouse_tuned    |         174.5 |          2158.9 |   12.37 |      0.08 | False    |
| Q10     | exasol            | clickhouse_tuned    |         165.1 |           538.2 |    3.26 |      0.31 | False    |
| Q11     | exasol            | clickhouse_tuned    |          52.2 |           141   |    2.7  |      0.37 | False    |
| Q12     | exasol            | clickhouse_tuned    |          27.3 |           181.6 |    6.65 |      0.15 | False    |
| Q13     | exasol            | clickhouse_tuned    |         148.8 |           770.7 |    5.18 |      0.19 | False    |
| Q14     | exasol            | clickhouse_tuned    |          23.2 |            57.3 |    2.47 |      0.4  | False    |
| Q15     | exasol            | clickhouse_tuned    |          76.6 |           103.5 |    1.35 |      0.74 | False    |
| Q16     | exasol            | clickhouse_tuned    |         222.7 |           220.1 |    0.99 |      1.01 | True     |
| Q17     | exasol            | clickhouse_tuned    |          13.9 |           331.1 |   23.82 |      0.04 | False    |
| Q18     | exasol            | clickhouse_tuned    |         146.5 |          1941.1 |   13.25 |      0.08 | False    |
| Q19     | exasol            | clickhouse_tuned    |          11.9 |          1362.1 |  114.46 |      0.01 | False    |
| Q20     | exasol            | clickhouse_tuned    |          67.4 |           335.4 |    4.98 |      0.2  | False    |
| Q21     | exasol            | clickhouse_tuned    |         106.7 |          3001.6 |   28.13 |      0.04 | False    |
| Q22     | exasol            | clickhouse_tuned    |          33.6 |           124.9 |    3.72 |      0.27 | False    |
| Q01     | exasol            | clickhouse          |         207   |           556.9 |    2.69 |      0.37 | False    |
| Q02     | exasol            | clickhouse          |          31.3 |           256.7 |    8.2  |      0.12 | False    |
| Q03     | exasol            | clickhouse          |          95.3 |           802.1 |    8.42 |      0.12 | False    |
| Q04     | exasol            | clickhouse          |          20.8 |           411.7 |   19.79 |      0.05 | False    |
| Q05     | exasol            | clickhouse          |          60   |          1531.3 |   25.52 |      0.04 | False    |
| Q06     | exasol            | clickhouse          |          13.7 |            58.3 |    4.26 |      0.23 | False    |
| Q07     | exasol            | clickhouse          |          68.9 |           824.5 |   11.97 |      0.08 | False    |
| Q08     | exasol            | clickhouse          |          30.7 |          1629.4 |   53.07 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |         174.5 |          2108.7 |   12.08 |      0.08 | False    |
| Q10     | exasol            | clickhouse          |         165.1 |           515.1 |    3.12 |      0.32 | False    |
| Q11     | exasol            | clickhouse          |          52.2 |           139   |    2.66 |      0.38 | False    |
| Q12     | exasol            | clickhouse          |          27.3 |           193.6 |    7.09 |      0.14 | False    |
| Q13     | exasol            | clickhouse          |         148.8 |           760.7 |    5.11 |      0.2  | False    |
| Q14     | exasol            | clickhouse          |          23.2 |            55   |    2.37 |      0.42 | False    |
| Q15     | exasol            | clickhouse          |          76.6 |            93.5 |    1.22 |      0.82 | False    |
| Q16     | exasol            | clickhouse          |         222.7 |           192.7 |    0.87 |      1.16 | True     |
| Q17     | exasol            | clickhouse          |          13.9 |           732.1 |   52.67 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |         146.5 |           719.7 |    4.91 |      0.2  | False    |
| Q19     | exasol            | clickhouse          |          11.9 |           547.8 |   46.03 |      0.02 | False    |
| Q20     | exasol            | clickhouse          |          67.4 |           114   |    1.69 |      0.59 | False    |
| Q21     | exasol            | clickhouse          |         106.7 |          6315.8 |   59.19 |      0.02 | False    |
| Q22     | exasol            | clickhouse          |          33.6 |           141.4 |    4.21 |      0.24 | False    |
| Q01     | exasol            | clickhouse_stat     |         207   |           535.1 |    2.59 |      0.39 | False    |
| Q02     | exasol            | clickhouse_stat     |          31.3 |           210.4 |    6.72 |      0.15 | False    |
| Q03     | exasol            | clickhouse_stat     |          95.3 |           808.1 |    8.48 |      0.12 | False    |
| Q04     | exasol            | clickhouse_stat     |          20.8 |           402.1 |   19.33 |      0.05 | False    |
| Q05     | exasol            | clickhouse_stat     |          60   |          1531.9 |   25.53 |      0.04 | False    |
| Q06     | exasol            | clickhouse_stat     |          13.7 |            55.4 |    4.04 |      0.25 | False    |
| Q07     | exasol            | clickhouse_stat     |          68.9 |           828.5 |   12.02 |      0.08 | False    |
| Q08     | exasol            | clickhouse_stat     |          30.7 |           353.7 |   11.52 |      0.09 | False    |
| Q09     | exasol            | clickhouse_stat     |         174.5 |           897.8 |    5.14 |      0.19 | False    |
| Q10     | exasol            | clickhouse_stat     |         165.1 |           524.4 |    3.18 |      0.31 | False    |
| Q11     | exasol            | clickhouse_stat     |          52.2 |           144.9 |    2.78 |      0.36 | False    |
| Q12     | exasol            | clickhouse_stat     |          27.3 |           199.8 |    7.32 |      0.14 | False    |
| Q13     | exasol            | clickhouse_stat     |         148.8 |           745.6 |    5.01 |      0.2  | False    |
| Q14     | exasol            | clickhouse_stat     |          23.2 |            71.3 |    3.07 |      0.33 | False    |
| Q15     | exasol            | clickhouse_stat     |          76.6 |           100.9 |    1.32 |      0.76 | False    |
| Q16     | exasol            | clickhouse_stat     |         222.7 |           191.4 |    0.86 |      1.16 | True     |
| Q17     | exasol            | clickhouse_stat     |          13.9 |           733.7 |   52.78 |      0.02 | False    |
| Q18     | exasol            | clickhouse_stat     |         146.5 |           745.9 |    5.09 |      0.2  | False    |
| Q19     | exasol            | clickhouse_stat     |          11.9 |           821.1 |   69    |      0.01 | False    |
| Q20     | exasol            | clickhouse_stat     |          67.4 |           125.6 |    1.86 |      0.54 | False    |
| Q21     | exasol            | clickhouse_stat     |         106.7 |          6283.7 |   58.89 |      0.02 | False    |
| Q22     | exasol            | clickhouse_stat     |          33.6 |           135.6 |    4.04 |      0.25 | False    |

### Detailed Statistics

The complete performance statistics for all queries and systems:

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |    556.8 |      7 |       556.9 |     559.1 |      7.4 |    551   |    573.3 |
| Q01     | clickhouse_stat  |    534.7 |      7 |       535.1 |     536.6 |      6   |    531.4 |    548.5 |
| Q01     | clickhouse_tuned |    565.2 |      7 |       563.6 |     566.6 |     10   |    554.7 |    580.3 |
| Q01     | exasol           |    209.1 |      7 |       207   |     207.3 |      1.1 |    206.3 |    209.5 |
| Q02     | clickhouse       |    302.4 |      7 |       256.7 |     255.2 |      3.7 |    249.5 |    259.8 |
| Q02     | clickhouse_stat  |    229   |      7 |       210.4 |     210.2 |      6.1 |    203.7 |    220   |
| Q02     | clickhouse_tuned |    302.5 |      7 |       252.3 |     251.4 |      3.8 |    246.6 |    256.5 |
| Q02     | exasol           |     81.8 |      7 |        31.3 |      31.3 |      0.5 |     30.6 |     31.9 |
| Q03     | clickhouse       |    855.2 |      7 |       802.1 |     807.8 |     17.9 |    787.3 |    840.5 |
| Q03     | clickhouse_stat  |    889.6 |      7 |       808.1 |     805.7 |     15.4 |    787.4 |    829   |
| Q03     | clickhouse_tuned |    891.8 |      7 |       827.7 |     827.9 |     18.1 |    801.3 |    849.3 |
| Q03     | exasol           |    100.5 |      7 |        95.3 |      95.9 |      1.8 |     93.2 |     98.2 |
| Q04     | clickhouse       |    458   |      7 |       411.7 |     414.5 |      8.7 |    405.6 |    428.4 |
| Q04     | clickhouse_stat  |    451.1 |      7 |       402.1 |     402   |      2.6 |    398.8 |    406.2 |
| Q04     | clickhouse_tuned |   1290.2 |      7 |      1179.4 |    1168.2 |    165.5 |    963.6 |   1486.5 |
| Q04     | exasol           |     23.1 |      7 |        20.8 |      20.8 |      0.2 |     20.5 |     21.1 |
| Q05     | clickhouse       |   1734.3 |      7 |      1531.3 |    1534.1 |     28.9 |   1495.1 |   1570.9 |
| Q05     | clickhouse_stat  |   1688.6 |      7 |      1531.9 |    1537.9 |     30.8 |   1512.3 |   1604.3 |
| Q05     | clickhouse_tuned |   1790.4 |      7 |      1587.9 |    1596.2 |     45.2 |   1557.4 |   1685.4 |
| Q05     | exasol           |    111.3 |      7 |        60   |      59.9 |      0.6 |     59.3 |     61.2 |
| Q06     | clickhouse       |    111.3 |      7 |        58.3 |      58.8 |      2.6 |     56.6 |     64.2 |
| Q06     | clickhouse_stat  |    103.9 |      7 |        55.4 |      57.1 |      7   |     52.8 |     72.7 |
| Q06     | clickhouse_tuned |    106.4 |      7 |        55.7 |      58   |      3.6 |     55.2 |     64.8 |
| Q06     | exasol           |     14   |      7 |        13.7 |      13.7 |      0.1 |     13.6 |     13.8 |
| Q07     | clickhouse       |    844.7 |      7 |       824.5 |     839.9 |     48.4 |    805.1 |    946.5 |
| Q07     | clickhouse_stat  |    845   |      7 |       828.5 |     845.5 |     33.2 |    817.1 |    908.7 |
| Q07     | clickhouse_tuned |    895.7 |      7 |       848   |     848.5 |     20.3 |    823   |    871.4 |
| Q07     | exasol           |     73.1 |      7 |        68.9 |      68.8 |      0.7 |     67.7 |     69.7 |
| Q08     | clickhouse       |   1669.6 |      7 |      1629.4 |    1636.5 |     31.1 |   1611.1 |   1705.3 |
| Q08     | clickhouse_stat  |    364.3 |      7 |       353.7 |     355.2 |      6.6 |    347.7 |    366.9 |
| Q08     | clickhouse_tuned |   1686.4 |      7 |      1705.3 |    1700.8 |     27.1 |   1652.1 |   1731.5 |
| Q08     | exasol           |     32.4 |      7 |        30.7 |      33.9 |      8.1 |     30.4 |     52.3 |
| Q09     | clickhouse       |   2305.8 |      7 |      2108.7 |    2099   |     23.8 |   2070.2 |   2124.6 |
| Q09     | clickhouse_stat  |    988.2 |      7 |       897.8 |     895.9 |     26.8 |    860.1 |    933.3 |
| Q09     | clickhouse_tuned |   2261.1 |      7 |      2158.9 |    2169.1 |     28   |   2128.7 |   2205   |
| Q09     | exasol           |    183.3 |      7 |       174.5 |     174.5 |      0.5 |    174   |    175.4 |
| Q10     | clickhouse       |    609.2 |      7 |       515.1 |     517   |      9.6 |    508.5 |    537.7 |
| Q10     | clickhouse_stat  |    547.2 |      7 |       524.4 |     532.3 |     16.1 |    518.1 |    556.4 |
| Q10     | clickhouse_tuned |    629.9 |      7 |       538.2 |     535.4 |     13.7 |    511   |    551.4 |
| Q10     | exasol           |    167.2 |      7 |       165.1 |     165.3 |      7   |    153.2 |    176.2 |
| Q11     | clickhouse       |    180.3 |      7 |       139   |     140.3 |      2.3 |    138.2 |    143.8 |
| Q11     | clickhouse_stat  |    182.9 |      7 |       144.9 |     145.1 |      1.2 |    143.4 |    147   |
| Q11     | clickhouse_tuned |    184.5 |      7 |       141   |     143.6 |      6.7 |    137.3 |    155.3 |
| Q11     | exasol           |     53.4 |      7 |        52.2 |      51.5 |      1.1 |     50.1 |     52.5 |
| Q12     | clickhouse       |    300.4 |      7 |       193.6 |     192   |      7.1 |    181.7 |    200.6 |
| Q12     | clickhouse_stat  |    237.9 |      7 |       199.8 |     200.5 |     10   |    185.6 |    218.8 |
| Q12     | clickhouse_tuned |    336.5 |      7 |       181.6 |     182.7 |      8   |    175.9 |    199   |
| Q12     | exasol           |     42.2 |      7 |        27.3 |      27.3 |      0.5 |     26.8 |     28.2 |
| Q13     | clickhouse       |    791.6 |      7 |       760.7 |     754.3 |     31.6 |    685.7 |    780   |
| Q13     | clickhouse_stat  |    779.4 |      7 |       745.6 |     753.5 |     13.5 |    738.2 |    771.8 |
| Q13     | clickhouse_tuned |    792.9 |      7 |       770.7 |     762.6 |     30.4 |    708.9 |    808.6 |
| Q13     | exasol           |    148.4 |      7 |       148.8 |     148.6 |      0.6 |    147.8 |    149.4 |
| Q14     | clickhouse       |     57.8 |      7 |        55   |      55.1 |      1   |     53.4 |     56.8 |
| Q14     | clickhouse_stat  |     70.8 |      7 |        71.3 |      72.3 |      2.4 |     69.8 |     75.5 |
| Q14     | clickhouse_tuned |     65   |      7 |        57.3 |      56.9 |      2.6 |     54.1 |     61.3 |
| Q14     | exasol           |     29.3 |      7 |        23.2 |      23.2 |      0.1 |     23.1 |     23.5 |
| Q15     | clickhouse       |    103.5 |      7 |        93.5 |      93.4 |      0.5 |     92.7 |     94.2 |
| Q15     | clickhouse_stat  |    111.3 |      7 |       100.9 |     101.4 |      0.9 |    100.3 |    102.8 |
| Q15     | clickhouse_tuned |    127.7 |      7 |       103.5 |     103.6 |      3.3 |     97.9 |    108.7 |
| Q15     | exasol           |     78.6 |      7 |        76.6 |      77   |      1.4 |     75.5 |     79   |
| Q16     | clickhouse       |    197.2 |      7 |       192.7 |     192.6 |      2.4 |    188.7 |    196.8 |
| Q16     | clickhouse_stat  |    194.9 |      7 |       191.4 |     193.7 |      7.2 |    188.9 |    209.2 |
| Q16     | clickhouse_tuned |    246.2 |      7 |       220.1 |     221.9 |      4.8 |    215.3 |    227.9 |
| Q16     | exasol           |    230   |      7 |       222.7 |     225.5 |      7.2 |    218.9 |    241   |
| Q17     | clickhouse       |    805.8 |      7 |       732.1 |     734.3 |      7.2 |    727.8 |    749.7 |
| Q17     | clickhouse_stat  |    830.7 |      7 |       733.7 |     737.1 |      9.4 |    729.5 |    757   |
| Q17     | clickhouse_tuned |    255.8 |      7 |       331.1 |     331.3 |      3.1 |    327.3 |    335.3 |
| Q17     | exasol           |     15.5 |      7 |        13.9 |      13.9 |      0.2 |     13.6 |     14.2 |
| Q18     | clickhouse       |    825.2 |      7 |       719.7 |     721.4 |     15.5 |    705.6 |    751.4 |
| Q18     | clickhouse_stat  |    781.6 |      7 |       745.9 |     750.2 |     16.8 |    730.1 |    772.8 |
| Q18     | clickhouse_tuned |   2396   |      7 |      1941.1 |    1944.3 |     46.4 |   1888.2 |   2010.4 |
| Q18     | exasol           |    145.4 |      7 |       146.5 |     146   |      0.9 |    144.9 |    147   |
| Q19     | clickhouse       |    545.2 |      7 |       547.8 |     550.4 |      7.4 |    543.7 |    566.1 |
| Q19     | clickhouse_stat  |    834.8 |      7 |       821.1 |     823.5 |     22.1 |    792.5 |    863.7 |
| Q19     | clickhouse_tuned |   1450.4 |      7 |      1362.1 |    1367.4 |     17.7 |   1351.7 |   1401.9 |
| Q19     | exasol           |     14.6 |      7 |        11.9 |      12.1 |      0.5 |     11.6 |     13.1 |
| Q20     | clickhouse       |    125.8 |      7 |       114   |     113.7 |      3.3 |    108.5 |    118   |
| Q20     | clickhouse_stat  |    140.4 |      7 |       125.6 |     127.7 |      4.8 |    122.2 |    134.8 |
| Q20     | clickhouse_tuned |    475.3 |      7 |       335.4 |     329.9 |      9.2 |    316.3 |    338.2 |
| Q20     | exasol           |     66.4 |      7 |        67.4 |      67.3 |      0.9 |     66   |     68.5 |
| Q21     | clickhouse       |   6334.8 |      7 |      6315.8 |    6332.2 |    203.3 |   6003.2 |   6578.9 |
| Q21     | clickhouse_stat  |   6232.6 |      7 |      6283.7 |    6234.7 |     85.5 |   6130.2 |   6319   |
| Q21     | clickhouse_tuned |   3861.5 |      7 |      3001.6 |    3004.9 |     48.5 |   2932.1 |   3074.9 |
| Q21     | exasol           |    103.4 |      7 |       106.7 |     111.1 |     14.5 |    102.6 |    143.3 |
| Q22     | clickhouse       |    157.1 |      7 |       141.4 |     144.3 |      7.4 |    137.8 |    158.5 |
| Q22     | clickhouse_stat  |    153.2 |      7 |       135.6 |     138   |      7.3 |    130.8 |    150.5 |
| Q22     | clickhouse_tuned |    171.1 |      7 |       124.9 |     124.2 |      7.9 |    114.5 |    135.9 |
| Q22     | exasol           |     34.7 |      7 |        33.6 |      33.6 |      0.3 |     33.1 |     34   |

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 63.6ms
- Average: 82.2ms
- Range: 11.6ms - 241.0ms

**#2. Clickhouse_stat**
- Median: 462.1ms
- Average: 748.0ms
- Range: 52.8ms - 6319.0ms

**#3. Clickhouse**
- Median: 540.7ms
- Average: 852.1ms
- Range: 53.4ms - 6578.9ms

**#4. Clickhouse_tuned**
- Median: 553.0ms
- Average: 831.6ms
- Range: 54.1ms - 3074.9ms


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 10
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