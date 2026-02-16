# Exasol vs StarRocks: TPC-H SF30 (Single-Node, 5 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:12:46

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 1482.6ms median runtime
- starrocks was 2.7x slower- Tested 220 total query executions across 22 different TPC-H queries
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24E611236C3EA408F with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24E611236C3EA408F

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24E611236C3EA408F to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24E611236C3EA408F /data

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
- **Execution mode:** Multiuser (5 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_30g_mu5-benchmark.zip
cd starrocks_exa_vs_sr_30g_mu5

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
| Q01     | exasol    |   1870.2 |      5 |      5230.3 |    6061.8 |   2072.9 |   3575   |   8263.2 |
| Q01     | starrocks |   8279.7 |      5 |     35293.4 |   47015.9 |  29629.2 |  27573.3 |  99495.1 |
| Q02     | exasol    |     79.6 |      5 |       303.1 |     301.6 |     43.8 |    243.9 |    362.7 |
| Q02     | starrocks |    625.9 |      5 |      1419.8 |    1410.6 |    250.1 |   1044   |   1732.7 |
| Q03     | exasol    |    657.7 |      5 |      1318.9 |    1944.3 |   1259.5 |    646.7 |   3605.2 |
| Q03     | starrocks |   2943.1 |      5 |      7787.7 |    8149.8 |   3267.5 |   3609.7 |  11678.6 |
| Q04     | exasol    |    128.5 |      5 |       814.9 |    1038.5 |    731.4 |    599.3 |   2332.4 |
| Q04     | starrocks |   1525.7 |      5 |      2856.8 |    2888.7 |    464.9 |   2275.7 |   3559.3 |
| Q05     | exasol    |    531.2 |      5 |      2123.3 |    2030.6 |    633.7 |    969.8 |   2659.5 |
| Q05     | starrocks |   2708.5 |      5 |      7215.1 |    7300.3 |   2161.8 |   4405.8 |  10105.4 |
| Q06     | exasol    |     82.9 |      5 |       507.2 |     450.3 |    319.9 |     82.8 |    817.8 |
| Q06     | starrocks |   1246   |      5 |      2260.7 |    2290.6 |    906.9 |   1388.1 |   3505   |
| Q07     | exasol    |    647.6 |      5 |      3204.4 |    3253.3 |    380.1 |   2821   |   3856   |
| Q07     | starrocks |   3218.7 |      5 |      4062.4 |    5502.4 |   2960.1 |   3815.7 |  10752.8 |
| Q08     | exasol    |    153.4 |      5 |       813.7 |     733.5 |    242.1 |    313   |    928.6 |
| Q08     | starrocks |   2397.8 |      5 |      4246.1 |    4233.5 |   1332   |   2266.9 |   5950.5 |
| Q09     | exasol    |   2297.6 |      5 |     11026.6 |    9852.3 |   2643.6 |   5299   |  11625.1 |
| Q09     | starrocks |   5841.2 |      5 |     24735.3 |   20114.9 |   8385.2 |  10332.9 |  28188.4 |
| Q10     | exasol    |    743.2 |      5 |      3129.3 |    3200.6 |    254.3 |   2929.1 |   3547.6 |
| Q10     | starrocks |   2709.4 |      5 |      5313.8 |    6331.2 |   2561.2 |   4128.6 |  10559.4 |
| Q11     | exasol    |    139.3 |      5 |       597.4 |     703.7 |    301.8 |    329.3 |   1028.5 |
| Q11     | starrocks |    384.6 |      5 |       836.2 |     969   |    496.8 |    549.3 |   1831.1 |
| Q12     | exasol    |    173   |      5 |       829.1 |     944.7 |    425.7 |    517.9 |   1650.1 |
| Q12     | starrocks |   1700.8 |      5 |      2437.8 |    3259.2 |   1827.9 |   2144.9 |   6504.4 |
| Q13     | exasol    |   1693.6 |      5 |      8203.7 |   10276.7 |   7355   |   3284.8 |  22733.3 |
| Q13     | starrocks |   3630.8 |      5 |     15953.1 |   17863.7 |   7319.2 |   7847.9 |  26569.5 |
| Q14     | exasol    |    160.4 |      5 |      1037.6 |     996.6 |    188.6 |    669.9 |   1128.9 |
| Q14     | starrocks |   1318.1 |      5 |      2424.4 |    3222.4 |   1904.9 |   1702.4 |   6455.8 |
| Q15     | exasol    |    353   |      5 |      1581.5 |    1565.2 |    571.6 |    676.4 |   2202.9 |
| Q15     | starrocks |   1328.4 |      5 |      2323   |    2195.5 |    807.1 |   1420.4 |   3341.6 |
| Q16     | exasol    |    619.3 |      5 |      2460.5 |    2513.6 |    970.5 |   1062.5 |   3602.3 |
| Q16     | starrocks |    843.6 |      5 |      1494.8 |    1660.1 |    786.4 |    850.8 |   2845.4 |
| Q17     | exasol    |     24.7 |      5 |       202.5 |     205.1 |    146.5 |     78.6 |    442.1 |
| Q17     | starrocks |   1327.1 |      5 |      1620.8 |    2234.8 |    955.3 |   1495.4 |   3586.5 |
| Q18     | exasol    |   1095.1 |      5 |      4468.8 |    4602   |    443.4 |   4201.3 |   5343.6 |
| Q18     | starrocks |   4457.3 |      5 |     12834.9 |   13563.2 |   2077.6 |  12140.4 |  17225.1 |
| Q19     | exasol    |     49.7 |      5 |       348.3 |     283.4 |    124.1 |    107.8 |    408.4 |
| Q19     | starrocks |   1685.8 |      5 |      3481.5 |    3496.9 |   1384.3 |   2083.1 |   5227.3 |
| Q20     | exasol    |    351.2 |      5 |      1722.9 |    1615.7 |    459.7 |    814.3 |   1964.5 |
| Q20     | starrocks |   1538   |      5 |      4402.7 |    4843   |   1362.3 |   3639.9 |   7089.4 |
| Q21     | exasol    |    950.6 |      5 |      4580.1 |    4250.1 |   2780.7 |   1485.4 |   8032.4 |
| Q21     | starrocks |   8980.9 |      5 |     48064.6 |   66975.4 |  36762.7 |  35601.8 | 113098   |
| Q22     | exasol    |    207.8 |      5 |       950   |    1261.8 |    735.8 |    806.2 |   2559.9 |
| Q22     | starrocks |    687.3 |      5 |      2652.6 |    3174.1 |   2090.9 |   1621.1 |   6761.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        5230.3 |         35293.4 |    6.75 |      0.15 | False    |
| Q02     | exasol            | starrocks           |         303.1 |          1419.8 |    4.68 |      0.21 | False    |
| Q03     | exasol            | starrocks           |        1318.9 |          7787.7 |    5.9  |      0.17 | False    |
| Q04     | exasol            | starrocks           |         814.9 |          2856.8 |    3.51 |      0.29 | False    |
| Q05     | exasol            | starrocks           |        2123.3 |          7215.1 |    3.4  |      0.29 | False    |
| Q06     | exasol            | starrocks           |         507.2 |          2260.7 |    4.46 |      0.22 | False    |
| Q07     | exasol            | starrocks           |        3204.4 |          4062.4 |    1.27 |      0.79 | False    |
| Q08     | exasol            | starrocks           |         813.7 |          4246.1 |    5.22 |      0.19 | False    |
| Q09     | exasol            | starrocks           |       11026.6 |         24735.3 |    2.24 |      0.45 | False    |
| Q10     | exasol            | starrocks           |        3129.3 |          5313.8 |    1.7  |      0.59 | False    |
| Q11     | exasol            | starrocks           |         597.4 |           836.2 |    1.4  |      0.71 | False    |
| Q12     | exasol            | starrocks           |         829.1 |          2437.8 |    2.94 |      0.34 | False    |
| Q13     | exasol            | starrocks           |        8203.7 |         15953.1 |    1.94 |      0.51 | False    |
| Q14     | exasol            | starrocks           |        1037.6 |          2424.4 |    2.34 |      0.43 | False    |
| Q15     | exasol            | starrocks           |        1581.5 |          2323   |    1.47 |      0.68 | False    |
| Q16     | exasol            | starrocks           |        2460.5 |          1494.8 |    0.61 |      1.65 | True     |
| Q17     | exasol            | starrocks           |         202.5 |          1620.8 |    8    |      0.12 | False    |
| Q18     | exasol            | starrocks           |        4468.8 |         12834.9 |    2.87 |      0.35 | False    |
| Q19     | exasol            | starrocks           |         348.3 |          3481.5 |   10    |      0.1  | False    |
| Q20     | exasol            | starrocks           |        1722.9 |          4402.7 |    2.56 |      0.39 | False    |
| Q21     | exasol            | starrocks           |        4580.1 |         48064.6 |   10.49 |      0.1  | False    |
| Q22     | exasol            | starrocks           |         950   |          2652.6 |    2.79 |      0.36 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 2992.5 | 1050.0 | 107.8 | 22733.3 |
| 1 | 22 | 2354.2 | 2033.2 | 202.5 | 8203.7 |
| 2 | 22 | 2596.5 | 1425.8 | 202.5 | 11625.1 |
| 3 | 22 | 3023.8 | 1892.1 | 82.8 | 11495.0 |
| 4 | 22 | 2234.1 | 1255.0 | 78.6 | 8263.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1050.0ms
- Slowest stream median: 2033.2ms
- Stream performance variation: 93.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 11758.6 | 3598.1 | 549.3 | 100106.2 |
| 1 | 22 | 6309.4 | 3771.9 | 836.2 | 33628.4 |
| 2 | 22 | 11305.8 | 4022.2 | 1044.0 | 99495.1 |
| 3 | 22 | 11517.0 | 5190.8 | 778.9 | 48064.6 |
| 4 | 22 | 11085.3 | 3660.3 | 849.7 | 113097.5 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3598.1ms
- Slowest stream median: 5190.8ms
- Stream performance variation: 44.3% difference between fastest and slowest streams
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
- Median runtime: 1482.6ms
- Average runtime: 2640.2ms
- Fastest query: 78.6ms
- Slowest query: 22733.3ms

**starrocks:**
- Median runtime: 4005.6ms
- Average runtime: 10395.2ms
- Fastest query: 549.3ms
- Slowest query: 113097.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_30g_mu5-benchmark.zip`](starrocks_exa_vs_sr_30g_mu5-benchmark.zip)

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
- Measured runs executed across 5 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts