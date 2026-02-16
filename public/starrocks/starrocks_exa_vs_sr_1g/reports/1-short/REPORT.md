# Exasol vs StarRocks: TPC-H SF1 (Single-Node, Single-User) - Initial Performance Assessment

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 10:32:20


> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document.

## Overview

We conducted performance testing of **starrocks** against **exasol** using the TPC-H benchmark at scale factor .

**Key Finding:** Starrocks demonstrated 5.7× slower median query performance compared to Exasol, highlighting significant optimization opportunities.

## The Baseline: Exasol

Exasol achieved a median query runtime of **32.8ms** across all TPC-H queries, establishing a competitive performance baseline for analytical workload processing.

## Starrocks 4.0.4 - System Under Test

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup Method:** native

### Installation & Configuration


The following steps were performed to install and configure Starrocks:

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS47CF015ED0F597702 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS47CF015ED0F597702

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS47CF015ED0F597702 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS47CF015ED0F597702 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create StarRocks data directory
sudo mkdir -p /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# Configure StarRocks FE
sudo tee /opt/starrocks/fe/conf/fe.conf &gt; /dev/null &lt;&lt; &#39;EOF&#39;
# StarRocks FE Configuration
LOG_DIR = /opt/starrocks/fe/log
meta_dir = /opt/starrocks/fe/meta
http_port = 8030
rpc_port = 9020
query_port = 9030
edit_log_port = 9010
priority_networks = &lt;PRIVATE_IP&gt;/24
# Performance tuning
qe_max_connection = 1024
# Memory settings
metadata_memory_limit = 8G

EOF

# Configure StarRocks BE
sudo tee /opt/starrocks/be/conf/be.conf &gt; /dev/null &lt;&lt; &#39;EOF&#39;
# StarRocks BE Configuration
LOG_DIR = /opt/starrocks/be/log
be_port = 9060
be_http_port = 8040
heartbeat_service_port = 9050
brpc_port = 8060
priority_networks = &lt;PRIVATE_IP&gt;/24
storage_root_path = /data/starrocks
# Performance tuning
mem_limit = 80%
# Parallel execution
parallel_fragment_exec_instance_num = 16

EOF

```

**Service Management:**
```bash
# Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# Execute sudo command on remote system
sudo mkdir -p /data/starrocks

```



**Data Directory:** `/data/starrocks`




## Performance Results

### Overall Performance Summary


| Metric | Starrocks | Exasol | Difference |
|--------|------------------|------------|------------|
| Median Runtime | 186.2ms | 32.8ms | 5.7× slower |
| Average Runtime | 192.6ms | 49.5ms | 3.9× slower |
| Fastest Query | 54.9ms | 11.0ms | 5.0× slower |
| Slowest Query | 491.1ms | 206.9ms | 2.4× slower |


### Selected Query Highlights

The following queries demonstrate the performance characteristics observed during testing:

**Queries with Largest Performance Gaps:**

- **Q08**: Starrocks 260.8ms vs Exasol 27.2ms (9.6× slower)
- **Q02**: Starrocks 266.2ms vs Exasol 32.9ms (8.1× slower)
- **Q19**: Starrocks 87.3ms vs Exasol 11.5ms (7.6× slower)

**Queries with Competitive Performance:**

- **Q13**: Starrocks 208.1ms vs Exasol 120.0ms (1.7× slower)
- **Q16**: Starrocks 232.1ms vs Exasol 94.4ms (2.5× slower)

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