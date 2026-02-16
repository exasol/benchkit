# Exasol vs StarRocks: TPC-H SF10 (Single-Node, Single-User)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 13:14:48

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 210.0ms median runtime
- starrocks was 4.6x slower- Tested 220 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol 2025.1.8

**Software Configuration:**
- **Database:** exasol 2025.1.8
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM
- **Hostname:** ip-10-0-1-203

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM
- **Hostname:** ip-10-0-1-76


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.large
- **Starrocks Instance:** r6id.large


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.8 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 20GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# Create raw partition for Exasol (89GB)
sudo parted /dev/nvme1n1 mkpart primary 20GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 20GiB 100%

# Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

# Create storage symlink: /dev/exasol.storage -&gt; /dev/nvme1n1p2
sudo ln -sf /dev/nvme1n1p2 /dev/exasol.storage

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m -s /bin/bash exasol

# Add exasol user to sudo group
sudo usermod -aG sudo exasol

# Set password for exasol user (interactive)
sudo passwd exasol

```

**Tool Setup:**
```bash
# Download c4 cluster management tool v4.28.5
wget https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

```

**Configuration:**
```bash
# Create c4 configuration file on remote system
cat &gt; /tmp/exasol_c4.conf &lt;&lt; &#39;EOF&#39;
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=12000
CCC_ADMINUI_START_SERVER=true
EOF

```

**Cluster Deployment:**
```bash
# Deploy Exasol cluster using c4
./c4 host play -i /tmp/exasol_c4.conf

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
# Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

```

**Cluster Management:**
```bash
# Get cluster play ID for confd_client operations
c4 ps

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



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3B01EEE0E0B03973C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3B01EEE0E0B03973C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3B01EEE0E0B03973C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3B01EEE0E0B03973C /data

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




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 10
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_10g-benchmark.zip
cd starrocks_exa_vs_sr_10g

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


### Performance Summary

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |   1251.2 |      5 |      1244.5 |    1248.7 |      6.4 |   1243.5 |   1256.4 |
| Q01     | starrocks |   5800.7 |      5 |      4221   |    4197.3 |     56.2 |   4118.6 |   4257   |
| Q02     | exasol    |     96.8 |      5 |        41.6 |      41.5 |      0.3 |     41.2 |     41.9 |
| Q02     | starrocks |    637.5 |      5 |       312   |     307.9 |     39.8 |    241.4 |    343.9 |
| Q03     | exasol    |    434.2 |      5 |       422.9 |     422.1 |      2.7 |    417.5 |    424.2 |
| Q03     | starrocks |   1892.1 |      5 |      1811   |    1849.8 |     85.6 |   1783.1 |   1987.9 |
| Q04     | exasol    |     89.8 |      5 |        88.1 |      88.2 |      0.5 |     87.7 |     89   |
| Q04     | starrocks |   1055.9 |      5 |       620.3 |     634.7 |     94   |    551.7 |    795   |
| Q05     | exasol    |    387.2 |      5 |       328.1 |     328.5 |      2.3 |    325.6 |    331.3 |
| Q05     | starrocks |   1735.2 |      5 |      1645.1 |    1670.7 |    106.8 |   1592   |   1856.3 |
| Q06     | exasol    |     57.3 |      5 |        58.4 |      60   |      3.7 |     57.8 |     66.5 |
| Q06     | starrocks |    584.1 |      5 |       321.8 |     314.4 |     23   |    282.8 |    339.3 |
| Q07     | exasol    |    402.1 |      5 |       389.6 |     391   |      6.4 |    383.6 |    398.6 |
| Q07     | starrocks |   2183.6 |      5 |      2556.2 |    2541.2 |    109   |   2425.4 |   2685.9 |
| Q08     | exasol    |    110.4 |      5 |       107.9 |     156.4 |    107   |    106.3 |    347.7 |
| Q08     | starrocks |   1846.3 |      5 |      1629.6 |    1640.7 |     20   |   1628   |   1674.8 |
| Q09     | exasol    |   1139   |      5 |      1111.5 |    1112.3 |      8.8 |   1101.4 |   1121.2 |
| Q09     | starrocks |   3167.7 |      5 |      3131.8 |    3167.1 |    171.7 |   3020.9 |   3459.9 |
| Q10     | exasol    |    473.6 |      5 |       463.4 |     462.8 |      3.9 |    456.4 |    466.6 |
| Q10     | starrocks |   1825.3 |      5 |      1776.6 |    1833   |    138.3 |   1739.9 |   2071.2 |
| Q11     | exasol    |     85.2 |      5 |        82.6 |      84.9 |      6.5 |     80.4 |     96.4 |
| Q11     | starrocks |    251.2 |      5 |       198   |     198.6 |      5.9 |    193.1 |    208.4 |
| Q12     | exasol    |    168.9 |      5 |       118.6 |     119.9 |      3.5 |    117.4 |    125.9 |
| Q12     | starrocks |   1520.8 |      5 |       476   |     483.9 |     39.7 |    453.4 |    552.2 |
| Q13     | exasol    |   1197.9 |      5 |      1108.8 |    1108.4 |      6.3 |   1098.9 |   1114   |
| Q13     | starrocks |   2092.7 |      5 |      1663.7 |    1673.5 |     38   |   1637.5 |   1738.1 |
| Q14     | exasol    |    148.8 |      5 |       104.2 |     104   |      0.6 |    103.2 |    104.6 |
| Q14     | starrocks |    861.1 |      5 |       339.9 |     359.7 |     42.1 |    328.7 |    431.4 |
| Q15     | exasol    |    121.3 |      5 |       110.5 |     110.7 |      0.8 |    109.8 |    112   |
| Q15     | starrocks |    558.6 |      5 |       390.3 |     403.2 |     41   |    362.8 |    462.5 |
| Q16     | exasol    |    457.2 |      5 |       438.1 |     441.2 |     10.2 |    430.9 |    455.7 |
| Q16     | starrocks |    673   |      5 |       448.4 |     455.8 |     66.8 |    384   |    531   |
| Q17     | exasol    |     29.9 |      5 |        19.8 |      19.7 |      0.5 |     19   |     20.1 |
| Q17     | starrocks |    769.6 |      5 |       486.2 |     497.3 |     38.6 |    470.5 |    564.9 |
| Q18     | exasol    |    692.1 |      5 |       679.5 |     679.5 |      0.7 |    678.3 |    680.1 |
| Q18     | starrocks |   2693.6 |      5 |      2388.6 |    2413.2 |     75.8 |   2337.3 |   2536.1 |
| Q19     | exasol    |     46   |      5 |        34.2 |      63.3 |     53.8 |     33.8 |    157.9 |
| Q19     | starrocks |   1581.2 |      5 |      1190.9 |    1181.5 |     55.9 |   1117.3 |   1252.9 |
| Q20     | exasol    |    247   |      5 |       210.9 |     210.7 |      0.7 |    209.9 |    211.5 |
| Q20     | starrocks |    908.6 |      5 |       543   |     554.8 |     33   |    529.2 |    612.3 |
| Q21     | exasol    |    623.9 |      5 |       627.7 |     625.9 |      5.4 |    619   |    632.5 |
| Q21     | starrocks |   3773.3 |      5 |      3171.3 |    3158   |     36.8 |   3094.3 |   3185   |
| Q22     | exasol    |    146.6 |      5 |       141.9 |     142.1 |      0.5 |    141.6 |    142.9 |
| Q22     | starrocks |    469.5 |      5 |       427.5 |     410.2 |     32.2 |    354.6 |    431   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1244.5 |          4221   |    3.39 |      0.29 | False    |
| Q02     | exasol            | starrocks           |          41.6 |           312   |    7.5  |      0.13 | False    |
| Q03     | exasol            | starrocks           |         422.9 |          1811   |    4.28 |      0.23 | False    |
| Q04     | exasol            | starrocks           |          88.1 |           620.3 |    7.04 |      0.14 | False    |
| Q05     | exasol            | starrocks           |         328.1 |          1645.1 |    5.01 |      0.2  | False    |
| Q06     | exasol            | starrocks           |          58.4 |           321.8 |    5.51 |      0.18 | False    |
| Q07     | exasol            | starrocks           |         389.6 |          2556.2 |    6.56 |      0.15 | False    |
| Q08     | exasol            | starrocks           |         107.9 |          1629.6 |   15.1  |      0.07 | False    |
| Q09     | exasol            | starrocks           |        1111.5 |          3131.8 |    2.82 |      0.35 | False    |
| Q10     | exasol            | starrocks           |         463.4 |          1776.6 |    3.83 |      0.26 | False    |
| Q11     | exasol            | starrocks           |          82.6 |           198   |    2.4  |      0.42 | False    |
| Q12     | exasol            | starrocks           |         118.6 |           476   |    4.01 |      0.25 | False    |
| Q13     | exasol            | starrocks           |        1108.8 |          1663.7 |    1.5  |      0.67 | False    |
| Q14     | exasol            | starrocks           |         104.2 |           339.9 |    3.26 |      0.31 | False    |
| Q15     | exasol            | starrocks           |         110.5 |           390.3 |    3.53 |      0.28 | False    |
| Q16     | exasol            | starrocks           |         438.1 |           448.4 |    1.02 |      0.98 | False    |
| Q17     | exasol            | starrocks           |          19.8 |           486.2 |   24.56 |      0.04 | False    |
| Q18     | exasol            | starrocks           |         679.5 |          2388.6 |    3.52 |      0.28 | False    |
| Q19     | exasol            | starrocks           |          34.2 |          1190.9 |   34.82 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         210.9 |           543   |    2.57 |      0.39 | False    |
| Q21     | exasol            | starrocks           |         627.7 |          3171.3 |    5.05 |      0.2  | False    |
| Q22     | exasol            | starrocks           |         141.9 |           427.5 |    3.01 |      0.33 | False    |


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

![Performance Speedup Comparison](attachments/figures/speedup_comparison.png)

*Speedup factor comparing each system against the baseline. Values above 1.0 indicate faster performance than the baseline, while values below 1.0 indicate slower performance.*

**Interactive version:** [View interactive chart](attachments/figures/speedup_comparison.html) to compare performance across queries.

![Performance Heatmap](attachments/figures/performance_heatmap.png)

*Heatmap showing relative performance across queries and systems. Values are normalized so that 1.0 represents the fastest system for each query. Darker colors indicate better performance.*

**Interactive version:** [View interactive chart](attachments/figures/performance_heatmap.html) for detailed heat map analysis.


> **Note:** All visualizations are available as both static PNG images (shown above) and interactive HTML charts (linked). The interactive versions allow you to zoom, pan, and hover for detailed information.

### Key Observations

**exasol:**
- Median runtime: 210.0ms
- Average runtime: 364.6ms
- Fastest query: 19.0ms
- Slowest query: 1256.4ms

**starrocks:**
- Median runtime: 956.1ms
- Average runtime: 1361.2ms
- Fastest query: 193.1ms
- Slowest query: 4257.0ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_10g-benchmark.zip`](starrocks_exa_vs_sr_10g-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 2 logical cores
- **Memory:** 15.3GB RAM
- **Storage:** NVMe SSD recommended for optimal performance
- **OS:** Linux

### Configuration Files

The exact configuration used for this benchmark is available at:
[`attachments/config.yaml`](attachments/config.yaml)

### System Specifications

**Exasol 2025.1.8:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 


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