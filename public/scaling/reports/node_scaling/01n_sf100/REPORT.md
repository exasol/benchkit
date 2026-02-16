# Exasol Node Scaling: 1N SF100

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-11 13:37:26

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 1 database systems:
- **exasol**


## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-189


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.4xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 0GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 0GiB

# Using additional disk: /dev/nvme1n1 (via /dev/exasol.storage)
lsblk /dev/nvme1n1

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# Add exasol user to sudo group
sudo usermod -aG sudo exasol || true

# Set password for exasol user (interactive)
sudo passwd exasol

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

# Distribute ubuntu SSH key to exasol user
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7B9XkUVsTF7vic8sClS3MMH0dZk2KH+u2xopF0zrn01iwEDTanXD8twap+XxsUCYHHgfJ4KCqbEssqXxbb7f8tN9cOD0jHcTMIF9J8B60V+QDh3zOPQZ6Vq0A1mW4XNB2wfgPfaVWdkmvOw8lOKXmjOchZoOAdM/+/J1YZ4/1Ypdcl4E3J9f80dCziXfRp4H4B+u0SFbZAUpjIqnzx7nqFXKiumMlOA8OSCtKcwX6chjM/TUnsVy7wTTfmyYYb2C7KiNjREsVyhASiUAQvrvEnfhWqy9HFBJ0z43JiqdaZTdcUomW7T4wHsobVONkmSHeRE49T8CJDoRAqsOZeOYV ubuntu@ip-10-0-1-189&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure localhost SSH access to exasol user
ssh-keyscan -H localhost &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
ssh-keyscan -H 127.0.0.1 &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
mkdir -p ~/.ssh
touch ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; &#39;SSHEOF&#39;

Host localhost 127.0.0.1
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
chmod 600 ~/.ssh/config

# Generate SSH key pair for exasol user
sudo -u exasol bash -c &#39;mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh &amp;&amp; if [ ! -f ~/.ssh/id_rsa ]; then ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34; -q; fi&#39;

# [All 1 Nodes] Cross-distribute exasol SSH keys for cluster communication
# Collect exasol public keys from all nodes, distribute to all authorized_keys
sudo cat ~exasol/.ssh/id_rsa.pub  # on each node
echo &#39;&lt;KEY&gt;&#39; | sudo tee -a ~exasol/.ssh/authorized_keys &gt; /dev/null
sudo chown exasol:exasol ~exasol/.ssh/authorized_keys &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure exasol SSH config for cluster nodes
sudo -u exasol bash -c &#39;
mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh
touch ~/.ssh/config &amp;&amp; chmod 600 ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; SSHEOF

Host localhost 127.0.0.1 &lt;PRIVATE_IP&gt; &lt;PUBLIC_IP&gt;
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
&#39;

```

**License Setup:**
```bash
# Install Exasol license file
confd_client license_upload license: &lt;LICENSE_CONTENT&gt;

```

**Database Tuning:**
```bash
# Stop Exasol database for parameter configuration
confd_client db_stop db_name: Exasol

# Configure Exasol database parameters for analytical workload optimization
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;]&#34;

# Starting database with new parameters
confd_client db_start db_name: Exasol

```

**Setup:**
```bash
# Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

```


**Tuning Parameters:**
- Optimizer mode: `analytical`
- Database parameters:
  - `-writeTouchInit=1`
  - `-cacheMonitorLimit=0`
  - `-maxOverallSlbUsageRatio=0.95`
  - `-useQueryCache=0`
  - `-query_log_timeout=0`
  - `-joinOrderMethod=0`
  - `-etlCheckCertsDefault=0`

**Data Directory:** `None`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 100
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_node_scaling_1n-benchmark.zip
cd exa_node_scaling_1n

# Execute the complete benchmark
./run_benchmark.sh
```

**Manual execution steps:**
```bash
# Install dependencies
pip install -r requirements.txt

# Probe system information
python -m benchkit probe --config config.yaml

# Run benchmark with all configurations applied
python -m benchkit run --config config.yaml
```

**Note:** All database tuning parameters and system configurations are embedded in the benchmark package and applied automatically during execution.

## Results

### Infrastructure Setup Timings


### Workload Preparation Timings

The following table shows the time taken for data generation, schema creation, and data loading for each system:

| System | Data Generation | Schema Creation | Data Loading | Total Preparation | Raw Size | Stored Size | Compression |
|--------|----------------|-----------------|--------------|-------------------|----------|-------------|-------------|
| Exasol | 0.00s | 1.93s | 524.75s | 686.33s | 95.7 GB | 22.9 GB | 4.2x |



### Performance Summary

| query   | system   |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol   |   1577.4 |      5 |      1576.4 |    1575.5 |      5.1 |   1566.6 |   1579.3 |
| Q02     | exasol   |    100.8 |      5 |        86.5 |      86.3 |      0.9 |     85.2 |     87.7 |
| Q03     | exasol   |    622.2 |      5 |       616.8 |     617.8 |      3.4 |    613.8 |    622.8 |
| Q04     | exasol   |    112.1 |      5 |       110.2 |     110.3 |      0.3 |    110   |    110.7 |
| Q05     | exasol   |    487.7 |      5 |       424.5 |     424   |      1   |    422.8 |    425.1 |
| Q06     | exasol   |     74.1 |      5 |        74   |      74.3 |      0.7 |     73.7 |     75.2 |
| Q07     | exasol   |    577.6 |      5 |       576.3 |     576.2 |      1.8 |    573.6 |    578.1 |
| Q08     | exasol   |    137.1 |      5 |       136.1 |     158.4 |     49.7 |    135.3 |    247.3 |
| Q09     | exasol   |   2063.6 |      5 |      2002.3 |    2005.6 |      9.5 |   1999.5 |   2022.4 |
| Q10     | exasol   |    800.2 |      5 |       785   |     785.2 |      4.9 |    778.2 |    790   |
| Q11     | exasol   |    183.5 |      5 |       177.9 |     178.5 |      7.5 |    167.1 |    187.7 |
| Q12     | exasol   |    204.4 |      5 |       150.3 |     150.1 |      0.5 |    149.4 |    150.5 |
| Q13     | exasol   |   1379.4 |      5 |      1382.1 |    1381.8 |      2.1 |   1379.7 |   1384.4 |
| Q14     | exasol   |    189.8 |      5 |       157.7 |     157.9 |      0.4 |    157.5 |    158.5 |
| Q15     | exasol   |    562.5 |      5 |       513.2 |     524.2 |     27   |    508.9 |    572.3 |
| Q16     | exasol   |    645.1 |      5 |       632.2 |     638.6 |     12.7 |    630.1 |    660.5 |
| Q17     | exasol   |     34.2 |      5 |        32.6 |      32.6 |      0.1 |     32.5 |     32.8 |
| Q18     | exasol   |   1057.8 |      5 |      1052.9 |    1053.4 |      2.5 |   1050.9 |   1057   |
| Q19     | exasol   |     47.8 |      5 |        45.9 |      46   |      0.3 |     45.6 |     46.5 |
| Q20     | exasol   |    407.8 |      5 |       406.4 |     413.6 |     18.4 |    402.4 |    446.4 |
| Q21     | exasol   |    801.6 |      5 |       801.4 |     802.2 |      2.4 |    800.2 |    805.9 |
| Q22     | exasol   |    177.3 |      5 |       178.1 |     177.8 |      0.7 |    176.9 |    178.4 |



### Visualizations

#### Performance Overview

![System Performance Overview](attachments/figures/system_performance_overview.png)

*Comprehensive dashboard showing key performance metrics: total runtime, average query time, query count, and performance variability (coefficient of variation) across all systems.*

**Interactive version:** [View interactive chart](attachments/figures/system_performance_overview.html) for detailed insights and hover information.

#### Runtime Distributions

![Query Runtime Distribution](attachments/figures/query_runtime_boxplot.png)

*Box plot showing the distribution of query runtimes. The box shows the interquartile range (25th to 75th percentile), with the median marked by the line inside the box. Whiskers extend to show the full range, excluding outliers.*

**Interactive version:** [View interactive chart](attachments/figures/query_runtime_boxplot.html) for detailed query-by-query analysis.

![Median Query Runtimes](attachments/figures/median_runtime_bar.png)

*Bar chart comparing median query runtimes across systems. Lower bars indicate better performance.*

**Interactive version:** [View interactive chart](attachments/figures/median_runtime_bar.html) to explore individual query performance.

#### Comparative Analysis


![Performance Heatmap](attachments/figures/performance_heatmap.png)

*Heatmap showing relative performance across queries and systems. Values are normalized so that 1.0 represents the fastest system for each query. Darker colors indicate better performance.*

**Interactive version:** [View interactive chart](attachments/figures/performance_heatmap.html) for detailed heat map analysis.


> **Note:** All visualizations are available as both static PNG images (shown above) and interactive HTML charts (linked). The interactive versions allow you to zoom, pan, and hover for detailed information.

### Key Observations

**exasol:**
- Median runtime: 422.9ms
- Average runtime: 544.1ms
- Fastest query: 32.5ms
- Slowest query: 2022.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_node_scaling_1n-benchmark.zip`](exa_node_scaling_1n-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 16 logical cores
- **Memory:** 123.8GB RAM
- **Storage:** NVMe SSD recommended for optimal performance
- **OS:** Linux

### Configuration Files

The exact configuration used for this benchmark is available at:
[`attachments/config.yaml`](attachments/config.yaml)

### System Specifications

**Exasol 2025.2.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts