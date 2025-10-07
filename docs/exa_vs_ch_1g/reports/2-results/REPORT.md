# Exasol vs ClickHouse Performance Comparison on TPC-H - Detailed Query Results

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-09 08:31:14


## Overview

This report presents the complete query-by-query performance results for 2 database systems tested using the TPC-H benchmark at scale factor .

**Systems Compared:**
- **clickhouse**
- **exasol**

## Systems Under Test

### Exasol 2025.1.0

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** exasol 2025.1.0

### Clickhouse 25.9.3.48

**Environment & Hardware:**
- **Cloud:** AWS eu-west-1
- **Instance:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz (16 vCPUs)- **Memory:** 124.4GB RAM

**Software:**
- **Database:** clickhouse 25.9.3.48


## Database Configuration

No setup details were captured for this benchmark run.

## Performance Summary


**Key Findings:**
- **exasol** was the fastest overall with **22.3ms** median runtime
- **clickhouse** was **3.8×** slower
- Tested **308** total query executions across 22 different query types

### Summary Statistics




## Query-by-Query Results

The following table shows the median execution time for each query across all systems:



## Performance Visualizations

### Query Performance Comparison

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

The performance patterns observed across these query types provide insights into each system's optimization strategies and architectural trade-offs.

### System Rankings

Based on median query execution time:

**#1. Exasol**
- Median: 22.3ms
- Average: 25.7ms
- Range: 7.3ms - 116.8ms

**#2. Clickhouse**
- Median: 84.9ms
- Average: 102.7ms
- Range: 21.1ms - 560.8ms


## Benchmark Methodology

### Workload Configuration

**TPC-H Benchmark:**
- **Scale Factor:** 
- **Data Format:** CSV
- **Data Generator:** dbgen

**Execution Parameters:**
- **Warmup Runs:** 1
- **Measured Runs:** 7
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