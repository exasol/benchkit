# Exasol vs StarRocks: TPC-H SF30 (Single-Node, Single-User)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:13:07

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 368.7ms median runtime
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
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-250

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-251


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.xlarge
- **Starrocks Instance:** r6id.xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.8 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme0n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mklabel gpt

# Create 48GB partition for data generation
sudo parted /dev/nvme0n1 mkpart primary ext4 1MiB 48GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary ext4 1MiB 48GiB

# Create raw partition for Exasol (172GB)
sudo parted /dev/nvme0n1 mkpart primary 48GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary 48GiB 100%

# Format /dev/nvme0n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme0n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme0n1p1 to /data
sudo mount /dev/nvme0n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

# Create storage symlink: /dev/exasol.storage -&gt; /dev/nvme0n1p2
sudo ln -sf /dev/nvme0n1p2 /dev/exasol.storage

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
CCC_PLAY_DB_MEM_SIZE=28000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64A16318D15C6CA4E with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64A16318D15C6CA4E

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64A16318D15C6CA4E to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64A16318D15C6CA4E /data

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
- **Scale factor:** 30
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_30g-benchmark.zip
cd starrocks_exa_vs_sr_30g

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
| Q01     | exasol    |   1874.9 |      5 |      1876   |    1875.3 |     15.7 |   1851.8 |   1893   |
| Q01     | starrocks |   8105.3 |      5 |      5984.4 |    6013   |     50   |   5965.8 |   6074.2 |
| Q02     | exasol    |     78.2 |      5 |        60.8 |      61   |      0.7 |     60.3 |     62.1 |
| Q02     | starrocks |    601.1 |      5 |       352.7 |     341.3 |     29.7 |    296.4 |    367.1 |
| Q03     | exasol    |    684   |      5 |       667.8 |     668.9 |      3.3 |    666.5 |    674.6 |
| Q03     | starrocks |   2822.7 |      5 |      2789.4 |    2780.2 |     53.3 |   2724.1 |   2856.4 |
| Q04     | exasol    |    129.4 |      5 |       127.5 |     127.5 |      0.5 |    126.9 |    128.2 |
| Q04     | starrocks |   1552.1 |      5 |       814.9 |     821.2 |     24.3 |    800.5 |    863.2 |
| Q05     | exasol    |    544.1 |      5 |       498   |     506.1 |     20.4 |    493.8 |    542.5 |
| Q05     | starrocks |   2568.1 |      5 |      2686.7 |    2704.3 |     67.3 |   2646.5 |   2819.8 |
| Q06     | exasol    |     84.4 |      5 |        84.1 |      84.1 |      0.4 |     83.7 |     84.8 |
| Q06     | starrocks |   1222.8 |      5 |      1178.8 |    1178.2 |     21.6 |   1146.5 |   1207.5 |
| Q07     | exasol    |    667.2 |      5 |       644.8 |     643.9 |      5.9 |    635   |    650.8 |
| Q07     | starrocks |   3179.7 |      5 |      3220.6 |    3231.6 |     45.7 |   3192.6 |   3308.6 |
| Q08     | exasol    |    157.1 |      5 |       158.3 |     159.1 |      2.9 |    156.3 |    164.1 |
| Q08     | starrocks |   2323.3 |      5 |      2246.1 |    2260.5 |     32   |   2224   |   2297.6 |
| Q09     | exasol    |   2364.7 |      5 |      2284   |    2290.4 |     12.8 |   2278.9 |   2307.5 |
| Q09     | starrocks |   5706.1 |      5 |      5546.6 |    5551.4 |     39.7 |   5508.1 |   5592.6 |
| Q10     | exasol    |    753.5 |      5 |       739.8 |     740.7 |      4.2 |    736   |    745.7 |
| Q10     | starrocks |   2576.4 |      5 |      2717.6 |    2704.4 |     44.6 |   2645.4 |   2761.8 |
| Q11     | exasol    |    137   |      5 |       138.6 |     151.8 |     31.3 |    136.4 |    207.7 |
| Q11     | starrocks |    333.3 |      5 |       253   |     252.5 |     26.5 |    221.1 |    291.3 |
| Q12     | exasol    |    308.8 |      5 |       171.8 |     171.5 |      0.5 |    170.9 |    172   |
| Q12     | starrocks |   1674.2 |      5 |      1602.6 |    1604.1 |     15.3 |   1585.2 |   1624.1 |
| Q13     | exasol    |   1855   |      5 |      1704.1 |    1704.9 |      2.5 |   1702.7 |   1709.1 |
| Q13     | starrocks |   3585.2 |      5 |      3027.5 |    3015.5 |     64.2 |   2911.8 |   3076.1 |
| Q14     | exasol    |    267.1 |      5 |       164   |     163.9 |      1   |    162.6 |    165.3 |
| Q14     | starrocks |   1284.7 |      5 |      1249   |    1257.7 |     19.7 |   1238   |   1287.7 |
| Q15     | exasol    |    400.1 |      5 |       369.2 |     369.8 |      1.3 |    368.5 |    371.6 |
| Q15     | starrocks |   1277.1 |      5 |      1249.1 |    1241.7 |     19.2 |   1210.6 |   1258.2 |
| Q16     | exasol    |    655.8 |      5 |       635.2 |     639.5 |     11.9 |    627.7 |    659.1 |
| Q16     | starrocks |    876.2 |      5 |       478.4 |     476.8 |     12.1 |    459.4 |    493   |
| Q17     | exasol    |     46.4 |      5 |        25.2 |      25.4 |      0.3 |     25.1 |     25.9 |
| Q17     | starrocks |   1293.9 |      5 |       662   |     682.5 |     38.5 |    653.6 |    747.2 |
| Q18     | exasol    |   1136.1 |      5 |      1101.2 |    1109.6 |     18.8 |   1097.7 |   1142.6 |
| Q18     | starrocks |   5043   |      5 |      4827.9 |    4821.4 |     55   |   4751.2 |   4900.7 |
| Q19     | exasol    |     83.4 |      5 |        50.8 |      50.9 |      0.3 |     50.5 |     51.4 |
| Q19     | starrocks |   1754.8 |      5 |      1799.9 |    1780.3 |     28.6 |   1744.9 |   1802.7 |
| Q20     | exasol    |    426.2 |      5 |       358.1 |     365.4 |     17.4 |    356.6 |    396.5 |
| Q20     | starrocks |   1579.4 |      5 |      1463.3 |    1459.6 |     26.3 |   1421.9 |   1494.2 |
| Q21     | exasol    |    986.8 |      5 |       969.3 |     969.8 |      5   |    964.3 |    976.9 |
| Q21     | starrocks |   9285.4 |      5 |      8435.3 |    8505.5 |    153   |   8369.9 |   8723.5 |
| Q22     | exasol    |    219   |      5 |       210   |     210.2 |      1.4 |    208.2 |    211.5 |
| Q22     | starrocks |    641.5 |      5 |       567.5 |     565   |      8.2 |    555.9 |    573.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1876   |          5984.4 |    3.19 |      0.31 | False    |
| Q02     | exasol            | starrocks           |          60.8 |           352.7 |    5.8  |      0.17 | False    |
| Q03     | exasol            | starrocks           |         667.8 |          2789.4 |    4.18 |      0.24 | False    |
| Q04     | exasol            | starrocks           |         127.5 |           814.9 |    6.39 |      0.16 | False    |
| Q05     | exasol            | starrocks           |         498   |          2686.7 |    5.39 |      0.19 | False    |
| Q06     | exasol            | starrocks           |          84.1 |          1178.8 |   14.02 |      0.07 | False    |
| Q07     | exasol            | starrocks           |         644.8 |          3220.6 |    4.99 |      0.2  | False    |
| Q08     | exasol            | starrocks           |         158.3 |          2246.1 |   14.19 |      0.07 | False    |
| Q09     | exasol            | starrocks           |        2284   |          5546.6 |    2.43 |      0.41 | False    |
| Q10     | exasol            | starrocks           |         739.8 |          2717.6 |    3.67 |      0.27 | False    |
| Q11     | exasol            | starrocks           |         138.6 |           253   |    1.83 |      0.55 | False    |
| Q12     | exasol            | starrocks           |         171.8 |          1602.6 |    9.33 |      0.11 | False    |
| Q13     | exasol            | starrocks           |        1704.1 |          3027.5 |    1.78 |      0.56 | False    |
| Q14     | exasol            | starrocks           |         164   |          1249   |    7.62 |      0.13 | False    |
| Q15     | exasol            | starrocks           |         369.2 |          1249.1 |    3.38 |      0.3  | False    |
| Q16     | exasol            | starrocks           |         635.2 |           478.4 |    0.75 |      1.33 | True     |
| Q17     | exasol            | starrocks           |          25.2 |           662   |   26.27 |      0.04 | False    |
| Q18     | exasol            | starrocks           |        1101.2 |          4827.9 |    4.38 |      0.23 | False    |
| Q19     | exasol            | starrocks           |          50.8 |          1799.9 |   35.43 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         358.1 |          1463.3 |    4.09 |      0.24 | False    |
| Q21     | exasol            | starrocks           |         969.3 |          8435.3 |    8.7  |      0.11 | False    |
| Q22     | exasol            | starrocks           |         210   |           567.5 |    2.7  |      0.37 | False    |


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
- Median runtime: 368.7ms
- Average runtime: 595.0ms
- Fastest query: 25.1ms
- Slowest query: 2307.5ms

**starrocks:**
- Median runtime: 1684.5ms
- Average runtime: 2420.4ms
- Fastest query: 221.1ms
- Slowest query: 8723.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_30g-benchmark.zip`](starrocks_exa_vs_sr_30g-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 4 logical cores
- **Memory:** 30.8GB RAM
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