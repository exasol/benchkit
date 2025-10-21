# Exasol vs ClickHouse Performance Comparison on TPC-H SF100 - Initial Performance Assessment

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2025-10-24 17:28:50


> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document.

## Overview

We conducted performance testing of **clickhouse** against **exasol** using the TPC-H benchmark at scale factor .

**Key Finding:** Clickhouse demonstrated 10.3× slower median query performance compared to Exasol, highlighting significant optimization opportunities.

## The Baseline: Exasol

Exasol achieved a median query runtime of **242.5ms** across all TPC-H queries, establishing a competitive performance baseline for analytical workload processing.

## Clickhouse 25.9.4.58 - System Under Test

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup Method:** native
- **Data Directory:** /data/clickhouse

### Installation & Configuration


The following steps were performed to install and configure Clickhouse:

**Storage Configuration:**
```bash
# Format /dev/nvme1n1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1 to /data
sudo mount /dev/nvme1n1 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create ClickHouse data directory under /data
sudo mkdir -p /data/clickhouse

# Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# Update package lists
sudo apt-get update

# Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# Install ClickHouse server and client version &lt;SERVER_IP&gt;
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;212792564121&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;16&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;32&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;32&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# Configure ClickHouse user profile with password and query settings
sudo tee /etc/clickhouse-server/users.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;users&gt;
        &lt;default replace=&#34;true&#34;&gt;
            &lt;password_sha256_hex&gt;2cca9d8714615f4132390a3db9296d39ec051b3faff87be7ea5f7fe0e2de14c9&lt;/password_sha256_hex&gt;
            &lt;networks&gt;
                &lt;ip&gt;::/0&lt;/ip&gt;
            &lt;/networks&gt;
        &lt;/default&gt;
    &lt;/users&gt;
    &lt;profiles&gt;
        &lt;default&gt;
            &lt;max_threads&gt;32&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;200000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;100000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;100000000000&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# Start ClickHouse server service
sudo systemctl start clickhouse-server

# Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```


**Tuning Parameters:**
- Memory limit: `230g`
- Max threads: `32`
- Max memory usage: `200.0GB`

**Data Directory:** `/data/clickhouse`




## Performance Results

### Overall Performance Summary


| Metric | Clickhouse | Exasol | Difference |
|--------|--------------------|------------|------------|
| Median Runtime | 2504.5ms | 242.5ms | 10.3× slower |
| Average Runtime | 5181.1ms | 307.6ms | 16.8× slower |
| Fastest Query | 161.8ms | 26.5ms | 6.1× slower |
| Slowest Query | 47354.7ms | 968.3ms | 48.9× slower |


### Selected Query Highlights

The following queries demonstrate the performance characteristics observed during testing:

**Queries with Largest Performance Gaps:**

- **Q17**: Clickhouse 5394.8ms vs Exasol 30.9ms (174.6× slower)
- **Q21**: Clickhouse 46498.2ms vs Exasol 384.7ms (120.9× slower)
- **Q08**: Clickhouse 7765.6ms vs Exasol 76.4ms (101.6× slower)

**Queries with Competitive Performance:**

- **Q15**: Clickhouse 280.5ms vs Exasol 380.9ms (0.7× slower)
- **Q16**: Clickhouse 450.5ms vs Exasol 486.1ms (0.9× slower)

## Analysis & Optimization Opportunities

Based on these initial results, several areas for investigation and potential optimization emerge:

1. **Query Execution Planning**: The significant performance variance across different query types suggests opportunities for query optimizer tuning and execution strategy refinement.

2. **Resource Utilization**: Analyzing memory allocation, CPU utilization patterns, and I/O characteristics could reveal bottlenecks limiting performance on analytical workloads.

3. **Configuration Tuning**: Database-specific parameters, cache settings, and parallelism configurations warrant detailed examination to maximize hardware utilization.

4. **Data Structure Optimization**: Table layout, partitioning strategies, and index usage patterns may offer substantial performance improvements for specific query patterns.

### Key Questions

- What specific query execution patterns lead to the largest performance differences?
- How do different query types (aggregations, joins, scans) perform comparatively?
- What configuration changes could narrow the performance gap?
- Are there workload-specific tuning opportunities that weren't explored in this initial assessment?

## Next Steps

This initial performance assessment establishes a baseline and identifies key areas for optimization. Our next publication will present the complete query-by-query performance analysis across all tested systems.

For readers interested in:
- **Detailed query-by-query results** → See our upcoming detailed results post
- **Complete reproduction steps** → See our full benchmark report with installation instructions for all systems

---

*This benchmark was conducted to provide transparent, reproducible performance comparisons. All configuration details and setup commands are included to enable independent verification of these results.*