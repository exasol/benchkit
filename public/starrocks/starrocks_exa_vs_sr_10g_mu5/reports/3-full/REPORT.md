# Exasol vs StarRocks: TPC-H SF10 (Single-Node, 5 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:05:26

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 1092.8ms median runtime
- starrocks was 2.8x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 5 concurrent streams (randomized distribution)

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25A652D2774808BD4 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25A652D2774808BD4

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25A652D2774808BD4 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25A652D2774808BD4 /data

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
- **Execution mode:** Multiuser (5 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_10g_mu5-benchmark.zip
cd starrocks_exa_vs_sr_10g_mu5

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
| Q01     | exasol    |   1267.5 |      5 |      6470.2 |    6287.5 |   1531.8 |   3887.8 |   7695.8 |
| Q01     | starrocks |   5946.3 |      5 |     47219.6 |   44617.6 |  29946.4 |   3963.3 |  85941.4 |
| Q02     | exasol    |    101.1 |      5 |       245.5 |     224.2 |    111.3 |     52.1 |    335.7 |
| Q02     | starrocks |    741.5 |      5 |       722.6 |     919   |    373.5 |    659   |   1541.6 |
| Q03     | exasol    |    482   |      5 |      1004.6 |    1379.7 |   1061.7 |    453.2 |   2791.9 |
| Q03     | starrocks |   2113.1 |      5 |      4275.6 |    4446.2 |    801   |   3588.6 |   5530.5 |
| Q04     | exasol    |     94.8 |      5 |       558.3 |     570.3 |    229.3 |    274.4 |    908   |
| Q04     | starrocks |    915.8 |      5 |      2206.4 |    2132.6 |    895.1 |    954.1 |   3214.5 |
| Q05     | exasol    |    423.3 |      5 |      1790.1 |    1777.6 |   1031   |    349.1 |   3179.8 |
| Q05     | starrocks |   1792.6 |      5 |      3694.2 |    3764   |    609.3 |   3006.9 |   4514.7 |
| Q06     | exasol    |    237.5 |      5 |       325.1 |     277.3 |    144.2 |     61.9 |    415   |
| Q06     | starrocks |    571   |      5 |      1181.8 |    1672.3 |    801.2 |    924.1 |   2654.6 |
| Q07     | exasol    |    451.5 |      5 |      2785.9 |    2684.9 |    559   |   1797.7 |   3211.9 |
| Q07     | starrocks |   2326.6 |      5 |      7757.5 |    7831.4 |   1434.5 |   5669.6 |   9562.7 |
| Q08     | exasol    |    119.9 |      5 |       582.9 |     708   |    491   |    125   |   1351.9 |
| Q08     | starrocks |   1843.9 |      5 |      3431.5 |    3052.4 |   1182.6 |   1671.6 |   4614.7 |
| Q09     | exasol    |   1287.8 |      5 |      5088.6 |    4315.9 |   1742.6 |   1248.1 |   5359.3 |
| Q09     | starrocks |   3375.5 |      5 |      7629.6 |    8104.1 |   2650   |   4477.8 |  10783.1 |
| Q10     | exasol    |    516.4 |      5 |      2554.9 |    2553   |    567.4 |   1907.8 |   3312.5 |
| Q10     | starrocks |   1949.2 |      5 |      3907.8 |    4163.3 |    762.3 |   3456.3 |   5431.9 |
| Q11     | exasol    |     93.6 |      5 |       513.1 |     564.9 |    441.5 |     93.3 |   1281.2 |
| Q11     | starrocks |    355.7 |      5 |       979.5 |    1226.9 |    535.8 |    874.9 |   2170.7 |
| Q12     | exasol    |    125.4 |      5 |       909.3 |     937.2 |    410.7 |    408.1 |   1465.8 |
| Q12     | starrocks |   1150.5 |      5 |      4476.3 |    4164.3 |   1729.4 |   2250   |   6124.4 |
| Q13     | exasol    |   1228.1 |      5 |      5526.4 |   11580.9 |  14791.8 |   2494.9 |  37904.7 |
| Q13     | starrocks |   2231.8 |      5 |      7942.6 |    8835.9 |   3148.1 |   5503.4 |  12604.6 |
| Q14     | exasol    |    119.3 |      5 |       951   |     956.1 |    237.6 |    657   |   1205.1 |
| Q14     | starrocks |    871.9 |      5 |      1903.8 |    1855.9 |   1016.8 |    620.3 |   3100.7 |
| Q15     | exasol    |    135   |      5 |       532.3 |     740.2 |    560.3 |    133.6 |   1611.3 |
| Q15     | starrocks |    567.3 |      5 |      2217.3 |    2446.5 |   1039.4 |   1370.5 |   3966.3 |
| Q16     | exasol    |    495.3 |      5 |      2881.9 |    2495.1 |   1294.6 |    477   |   3789.3 |
| Q16     | starrocks |    725.6 |      5 |      1326.2 |    1491.3 |    839.3 |    391.7 |   2709.3 |
| Q17     | exasol    |     23.5 |      5 |       119.3 |     165.5 |     70.6 |    116.5 |    275.6 |
| Q17     | starrocks |    881.1 |      5 |      2164   |    2251.2 |    715.8 |   1366.3 |   3016.2 |
| Q18     | exasol    |    696.4 |      5 |      3270.3 |    2866.6 |   1063   |   1016.8 |   3579.2 |
| Q18     | starrocks |   3352.6 |      5 |      8650.4 |    8679.8 |   2918.7 |   4857.4 |  12624.1 |
| Q19     | exasol    |     38.6 |      5 |       315   |     391.4 |    263.3 |     57.9 |    699.4 |
| Q19     | starrocks |   1167.1 |      5 |      2238.8 |    2124.3 |    396.3 |   1486.8 |   2465   |
| Q20     | exasol    |    225.6 |      5 |      1232.2 |    1236.8 |    578.4 |    694.6 |   2157.5 |
| Q20     | starrocks |    972.4 |      5 |      1670.9 |    1919.7 |    726.2 |   1083.7 |   2940.8 |
| Q21     | exasol    |    747   |      5 |      2888.7 |    2596.2 |   1436.2 |    682.6 |   4424.2 |
| Q21     | starrocks |   3887.1 |      5 |     24165.2 |   25100.7 |  10589.7 |   9949.4 |  38439.5 |
| Q22     | exasol    |    148.1 |      5 |       774.1 |     882.3 |    261.4 |    648.9 |   1189.9 |
| Q22     | starrocks |    616.1 |      5 |       918.3 |    1596.5 |   1423.7 |    467   |   3770.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6470.2 |         47219.6 |    7.3  |      0.14 | False    |
| Q02     | exasol            | starrocks           |         245.5 |           722.6 |    2.94 |      0.34 | False    |
| Q03     | exasol            | starrocks           |        1004.6 |          4275.6 |    4.26 |      0.23 | False    |
| Q04     | exasol            | starrocks           |         558.3 |          2206.4 |    3.95 |      0.25 | False    |
| Q05     | exasol            | starrocks           |        1790.1 |          3694.2 |    2.06 |      0.48 | False    |
| Q06     | exasol            | starrocks           |         325.1 |          1181.8 |    3.64 |      0.28 | False    |
| Q07     | exasol            | starrocks           |        2785.9 |          7757.5 |    2.78 |      0.36 | False    |
| Q08     | exasol            | starrocks           |         582.9 |          3431.5 |    5.89 |      0.17 | False    |
| Q09     | exasol            | starrocks           |        5088.6 |          7629.6 |    1.5  |      0.67 | False    |
| Q10     | exasol            | starrocks           |        2554.9 |          3907.8 |    1.53 |      0.65 | False    |
| Q11     | exasol            | starrocks           |         513.1 |           979.5 |    1.91 |      0.52 | False    |
| Q12     | exasol            | starrocks           |         909.3 |          4476.3 |    4.92 |      0.2  | False    |
| Q13     | exasol            | starrocks           |        5526.4 |          7942.6 |    1.44 |      0.7  | False    |
| Q14     | exasol            | starrocks           |         951   |          1903.8 |    2    |      0.5  | False    |
| Q15     | exasol            | starrocks           |         532.3 |          2217.3 |    4.17 |      0.24 | False    |
| Q16     | exasol            | starrocks           |        2881.9 |          1326.2 |    0.46 |      2.17 | True     |
| Q17     | exasol            | starrocks           |         119.3 |          2164   |   18.14 |      0.06 | False    |
| Q18     | exasol            | starrocks           |        3270.3 |          8650.4 |    2.65 |      0.38 | False    |
| Q19     | exasol            | starrocks           |         315   |          2238.8 |    7.11 |      0.14 | False    |
| Q20     | exasol            | starrocks           |        1232.2 |          1670.9 |    1.36 |      0.74 | False    |
| Q21     | exasol            | starrocks           |        2888.7 |         24165.2 |    8.37 |      0.12 | False    |
| Q22     | exasol            | starrocks           |         774.1 |           918.3 |    1.19 |      0.84 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 2518.7 | 579.8 | 52.1 | 37904.7 |
| 1 | 22 | 1690.6 | 746.2 | 274.4 | 7492.9 |
| 2 | 22 | 2038.5 | 1182.2 | 116.5 | 6470.2 |
| 3 | 22 | 2213.6 | 1763.9 | 119.3 | 5526.4 |
| 4 | 22 | 2036.8 | 1481.6 | 118.4 | 7695.8 |

**Performance Analysis for Exasol:**
- Fastest stream median: 579.8ms
- Slowest stream median: 1763.9ms
- Stream performance variation: 204.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 6046.7 | 3677.9 | 994.8 | 30742.7 |
| 1 | 22 | 5384.7 | 2383.6 | 918.3 | 53340.6 |
| 2 | 22 | 7281.0 | 3031.9 | 391.7 | 85941.4 |
| 3 | 22 | 6836.2 | 3641.4 | 722.6 | 32623.3 |
| 4 | 22 | 6814.2 | 2537.6 | 874.9 | 47219.6 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2383.6ms
- Slowest stream median: 3677.9ms
- Stream performance variation: 54.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams

**Query Distribution Method:**
- Queries were randomized across streams (seed: 42) for realistic multi-user simulation


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
- Median runtime: 1092.8ms
- Average runtime: 2099.6ms
- Fastest query: 52.1ms
- Slowest query: 37904.7ms

**starrocks:**
- Median runtime: 3011.6ms
- Average runtime: 6472.5ms
- Fastest query: 391.7ms
- Slowest query: 85941.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_10g_mu5-benchmark.zip`](starrocks_exa_vs_sr_10g_mu5-benchmark.zip)

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
- Measured runs executed across 5 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts