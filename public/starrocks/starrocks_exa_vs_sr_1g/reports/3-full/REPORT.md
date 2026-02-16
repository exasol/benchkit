# Exasol vs StarRocks: TPC-H SF1 (Single-Node, Single-User)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 10:32:20

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 32.8ms median runtime
- starrocks was 5.7x slower- Tested 220 total query executions across 22 different TPC-H queries

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

# Create 3GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# Create raw partition for Exasol (106GB)
sudo parted /dev/nvme1n1 mkpart primary 3GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 3GiB 100%

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
CCC_PLAY_DB_MEM_SIZE=8000
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




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 1
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_1g-benchmark.zip
cd starrocks_exa_vs_sr_1g

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
| Q01     | exasol    |    134.9 |      5 |       135   |     152.3 |     31.3 |    134.1 |    206.9 |
| Q01     | starrocks |    980.1 |      5 |       388.5 |     392.7 |     27.3 |    365.1 |    431.5 |
| Q02     | exasol    |     59.3 |      5 |        32.9 |      34.6 |      3.9 |     32.5 |     41.6 |
| Q02     | starrocks |    533.9 |      5 |       266.2 |     270.7 |     37.1 |    221.2 |    325.3 |
| Q03     | exasol    |     49.1 |      5 |        47.3 |      47.2 |      0.1 |     47   |     47.3 |
| Q03     | starrocks |    305.3 |      5 |       203.4 |     186   |     42.9 |    136   |    231.6 |
| Q04     | exasol    |     17.8 |      5 |        17.1 |      17.1 |      0.6 |     16.5 |     18.1 |
| Q04     | starrocks |    280.2 |      5 |       115.6 |     129.6 |     34   |     98.9 |    167.2 |
| Q05     | exasol    |     57.5 |      5 |        45.5 |      47.9 |      5.6 |     45   |     57.8 |
| Q05     | starrocks |    247.4 |      5 |       223.6 |     220.5 |     23.9 |    180.8 |    240   |
| Q06     | exasol    |     11.4 |      5 |        11.2 |      11.2 |      0.1 |     11   |     11.3 |
| Q06     | starrocks |     84.1 |      5 |        81.1 |      80.7 |     16.6 |     54.9 |     95.4 |
| Q07     | exasol    |     50.7 |      5 |        48.9 |      48.7 |      0.5 |     48.1 |     49.4 |
| Q07     | starrocks |    349.1 |      5 |       265.6 |     263.8 |     37.6 |    207.5 |    306.8 |
| Q08     | exasol    |     35.7 |      5 |        27.2 |      27.8 |      1.9 |     26.4 |     31.1 |
| Q08     | starrocks |    370.9 |      5 |       260.8 |     258.4 |     48.1 |    195.6 |    328.7 |
| Q09     | exasol    |    113.6 |      5 |       112.3 |     112.9 |      2.5 |    109.8 |    115.6 |
| Q09     | starrocks |    307.9 |      5 |       305.5 |     309.2 |     53.7 |    260.6 |    397.1 |
| Q10     | exasol    |     57.5 |      5 |        55.3 |      55.2 |      0.3 |     54.9 |     55.6 |
| Q10     | starrocks |    212.7 |      5 |       188   |     198.4 |     27.1 |    172.5 |    242.2 |
| Q11     | exasol    |     23   |      5 |        24.4 |      29.3 |      7.7 |     23.7 |     40.9 |
| Q11     | starrocks |     96   |      5 |       109.2 |     100.8 |     16.4 |     82.8 |    116.6 |
| Q12     | exasol    |     25.9 |      5 |        21.5 |      21.5 |      0.3 |     21.2 |     21.8 |
| Q12     | starrocks |    184.3 |      5 |       123.6 |     120.2 |     13.3 |    103.6 |    136.3 |
| Q13     | exasol    |    122.2 |      5 |       120   |     120.2 |      1.1 |    118.5 |    121.3 |
| Q13     | starrocks |    294.7 |      5 |       208.1 |     218.8 |     25.3 |    196.3 |    257.4 |
| Q14     | exasol    |     19.5 |      5 |        17.2 |      17.1 |      0.2 |     16.9 |     17.3 |
| Q14     | starrocks |    109.7 |      5 |        86.9 |      85.7 |     20.4 |     62.3 |    106.7 |
| Q15     | exasol    |     25.8 |      5 |        23.8 |      23.9 |      0.3 |     23.5 |     24.2 |
| Q15     | starrocks |    152.6 |      5 |        98.5 |      92.5 |     13.7 |     76.9 |    108.8 |
| Q16     | exasol    |    103   |      5 |        94.4 |      96.8 |      7.2 |     92.3 |    109.6 |
| Q16     | starrocks |    269.8 |      5 |       232.1 |     263.3 |     64.5 |    199.8 |    348.6 |
| Q17     | exasol    |     13   |      5 |        11.8 |      11.9 |      0.4 |     11.7 |     12.6 |
| Q17     | starrocks |    103.7 |      5 |        85.3 |      95.1 |     26.1 |     68.1 |    125.7 |
| Q18     | exasol    |     83.4 |      5 |        79.4 |      79.4 |      0.3 |     79.1 |     79.8 |
| Q18     | starrocks |    233.3 |      5 |       237.1 |     248.1 |     28.5 |    221.3 |    285.5 |
| Q19     | exasol    |     12.7 |      5 |        11.5 |      11.5 |      0.3 |     11.1 |     11.8 |
| Q19     | starrocks |     92.3 |      5 |        87.3 |      85.6 |      9.8 |     71.4 |     98.3 |
| Q20     | exasol    |     35   |      5 |        31.4 |      31.4 |      0.1 |     31.3 |     31.6 |
| Q20     | starrocks |    114.9 |      5 |       110.2 |     122.9 |     29   |    102   |    170.6 |
| Q21     | exasol    |     70   |      5 |        67.4 |      67.3 |      0.1 |     67.1 |     67.4 |
| Q21     | starrocks |    549.8 |      5 |       407.3 |     409.7 |     50.9 |    358   |    491.1 |
| Q22     | exasol    |     24.2 |      5 |        23.9 |      24   |      0.3 |     23.8 |     24.4 |
| Q22     | starrocks |     95.7 |      5 |        91.5 |      84.8 |     13.2 |     62   |     93.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         135   |           388.5 |    2.88 |      0.35 | False    |
| Q02     | exasol            | starrocks           |          32.9 |           266.2 |    8.09 |      0.12 | False    |
| Q03     | exasol            | starrocks           |          47.3 |           203.4 |    4.3  |      0.23 | False    |
| Q04     | exasol            | starrocks           |          17.1 |           115.6 |    6.76 |      0.15 | False    |
| Q05     | exasol            | starrocks           |          45.5 |           223.6 |    4.91 |      0.2  | False    |
| Q06     | exasol            | starrocks           |          11.2 |            81.1 |    7.24 |      0.14 | False    |
| Q07     | exasol            | starrocks           |          48.9 |           265.6 |    5.43 |      0.18 | False    |
| Q08     | exasol            | starrocks           |          27.2 |           260.8 |    9.59 |      0.1  | False    |
| Q09     | exasol            | starrocks           |         112.3 |           305.5 |    2.72 |      0.37 | False    |
| Q10     | exasol            | starrocks           |          55.3 |           188   |    3.4  |      0.29 | False    |
| Q11     | exasol            | starrocks           |          24.4 |           109.2 |    4.48 |      0.22 | False    |
| Q12     | exasol            | starrocks           |          21.5 |           123.6 |    5.75 |      0.17 | False    |
| Q13     | exasol            | starrocks           |         120   |           208.1 |    1.73 |      0.58 | False    |
| Q14     | exasol            | starrocks           |          17.2 |            86.9 |    5.05 |      0.2  | False    |
| Q15     | exasol            | starrocks           |          23.8 |            98.5 |    4.14 |      0.24 | False    |
| Q16     | exasol            | starrocks           |          94.4 |           232.1 |    2.46 |      0.41 | False    |
| Q17     | exasol            | starrocks           |          11.8 |            85.3 |    7.23 |      0.14 | False    |
| Q18     | exasol            | starrocks           |          79.4 |           237.1 |    2.99 |      0.33 | False    |
| Q19     | exasol            | starrocks           |          11.5 |            87.3 |    7.59 |      0.13 | False    |
| Q20     | exasol            | starrocks           |          31.4 |           110.2 |    3.51 |      0.28 | False    |
| Q21     | exasol            | starrocks           |          67.4 |           407.3 |    6.04 |      0.17 | False    |
| Q22     | exasol            | starrocks           |          23.9 |            91.5 |    3.83 |      0.26 | False    |


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
- Median runtime: 32.8ms
- Average runtime: 49.5ms
- Fastest query: 11.0ms
- Slowest query: 206.9ms

**starrocks:**
- Median runtime: 186.2ms
- Average runtime: 192.6ms
- Fastest query: 54.9ms
- Slowest query: 491.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_1g-benchmark.zip`](starrocks_exa_vs_sr_1g-benchmark.zip)

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