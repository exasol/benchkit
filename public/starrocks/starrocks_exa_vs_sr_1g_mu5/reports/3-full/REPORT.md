# Exasol vs StarRocks: TPC-H SF1 (Single-Node, 5 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 10:53:32

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 178.4ms median runtime
- starrocks was 3.2x slower- Tested 220 total query executions across 22 different TPC-H queries
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4E17CAA38010D8E8C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4E17CAA38010D8E8C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4E17CAA38010D8E8C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4E17CAA38010D8E8C /data

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
- **Execution mode:** Multiuser (5 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_1g_mu5-benchmark.zip
cd starrocks_exa_vs_sr_1g_mu5

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
| Q01     | exasol    |    134.3 |      5 |       562.8 |     568.6 |    156.9 |    334.8 |    751.7 |
| Q01     | starrocks |    877.5 |      5 |       904.9 |     989.3 |    368.7 |    698.6 |   1611.6 |
| Q02     | exasol    |     55.1 |      5 |       240.5 |     238.5 |    116.3 |     93.8 |    377.7 |
| Q02     | starrocks |    568.6 |      5 |       559.7 |     653.3 |    213.9 |    519.2 |   1031.3 |
| Q03     | exasol    |     47.3 |      5 |       173.2 |     268.3 |    197.9 |     45.9 |    506.5 |
| Q03     | starrocks |    272.1 |      5 |       463   |     466.6 |     96.3 |    318.6 |    576.6 |
| Q04     | exasol    |     18.3 |      5 |        86.6 |      98.2 |     39.9 |     60.3 |    150.2 |
| Q04     | starrocks |    184.1 |      5 |       626   |     692.3 |    196.6 |    472.4 |    901.4 |
| Q05     | exasol    |     55.8 |      5 |       203.8 |     189.5 |     39.6 |    140.5 |    225.4 |
| Q05     | starrocks |    272.9 |      5 |       533.5 |     614.8 |    168.8 |    469.8 |    894.8 |
| Q06     | exasol    |     11.5 |      5 |        85.2 |      65.6 |     35   |     10.4 |     92.4 |
| Q06     | starrocks |     65   |      5 |       382.5 |     374   |    108.8 |    219.9 |    509.2 |
| Q07     | exasol    |     49.9 |      5 |       258.9 |     252.1 |    113.6 |    131.1 |    416.8 |
| Q07     | starrocks |    279.1 |      5 |       941.7 |     846.2 |    176.5 |    564   |    989.9 |
| Q08     | exasol    |     25.8 |      5 |       132   |     114.8 |     56.1 |     25.8 |    162.3 |
| Q08     | starrocks |    347.8 |      5 |       986.9 |     887.4 |    421.4 |    350   |   1340.6 |
| Q09     | exasol    |    108.9 |      5 |       539.5 |     527   |     71.2 |    424.1 |    610.9 |
| Q09     | starrocks |    379.1 |      5 |      1006.1 |     992.1 |    292.1 |    605.5 |   1419.5 |
| Q10     | exasol    |     56.5 |      5 |       473.2 |     448.9 |    198.3 |    207.1 |    720.9 |
| Q10     | starrocks |    295.5 |      5 |       866.7 |     935.2 |    520   |    332.3 |   1703.6 |
| Q11     | exasol    |     23.4 |      5 |       225.3 |     179.3 |    104.7 |     60.5 |    294.6 |
| Q11     | starrocks |    105.1 |      5 |       324   |     350.9 |    187   |    177.1 |    627   |
| Q12     | exasol    |     21.3 |      5 |       156.6 |     163.3 |     73.7 |     86.5 |    283.3 |
| Q12     | starrocks |    157.9 |      5 |       723   |     712.3 |    185.4 |    520.3 |    990.5 |
| Q13     | exasol    |    114.6 |      5 |       653.6 |    1117.4 |    875.9 |    500.2 |   2582.4 |
| Q13     | starrocks |    265.8 |      5 |       519   |     568.2 |    170.8 |    433.4 |    866.6 |
| Q14     | exasol    |     17.1 |      5 |        67.3 |     160.7 |    165.7 |     17.2 |    413.6 |
| Q14     | starrocks |    109.9 |      5 |       352.2 |     526.9 |    325.5 |    331.5 |   1094   |
| Q15     | exasol    |     24.2 |      5 |       121.8 |     125.5 |     79.1 |     23.6 |    243.9 |
| Q15     | starrocks |    161   |      5 |       380.9 |     391   |    111.1 |    271.6 |    563.7 |
| Q16     | exasol    |    102.9 |      5 |       378.1 |     381   |    194.4 |     92.7 |    594.3 |
| Q16     | starrocks |    312.6 |      5 |       851.2 |     843.6 |    249.7 |    589.2 |   1239   |
| Q17     | exasol    |     12.1 |      5 |        53.2 |      69.4 |     33.6 |     33.9 |    109.1 |
| Q17     | starrocks |    112.7 |      5 |       509.7 |     536.3 |    155.6 |    365.9 |    751.5 |
| Q18     | exasol    |     80.3 |      5 |       345.7 |     343.9 |     47   |    285.7 |    409   |
| Q18     | starrocks |    276   |      5 |      1772.8 |    2062.3 |    750.4 |   1472.5 |   3344.2 |
| Q19     | exasol    |     11.5 |      5 |        85.6 |      85.1 |     26.1 |     59.7 |    124.9 |
| Q19     | starrocks |    153.2 |      5 |       331.4 |     362.3 |    159   |    176.2 |    616.1 |
| Q20     | exasol    |     31   |      5 |       195.5 |     239.2 |     85.4 |    156.4 |    349.2 |
| Q20     | starrocks |    173   |      5 |       429.5 |     426.4 |     93.5 |    291.7 |    543.8 |
| Q21     | exasol    |     65.7 |      5 |       319.9 |     370.7 |    257.6 |     79.1 |    772.3 |
| Q21     | starrocks |    592.3 |      5 |      2133.7 |    2201.7 |    726.9 |   1205   |   2927.6 |
| Q22     | exasol    |     23.5 |      5 |       157.5 |     140.9 |     31.5 |     99.3 |    167.1 |
| Q22     | starrocks |     82.9 |      5 |       296.2 |     346.9 |    254   |    147.9 |    773.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         562.8 |           904.9 |    1.61 |      0.62 | False    |
| Q02     | exasol            | starrocks           |         240.5 |           559.7 |    2.33 |      0.43 | False    |
| Q03     | exasol            | starrocks           |         173.2 |           463   |    2.67 |      0.37 | False    |
| Q04     | exasol            | starrocks           |          86.6 |           626   |    7.23 |      0.14 | False    |
| Q05     | exasol            | starrocks           |         203.8 |           533.5 |    2.62 |      0.38 | False    |
| Q06     | exasol            | starrocks           |          85.2 |           382.5 |    4.49 |      0.22 | False    |
| Q07     | exasol            | starrocks           |         258.9 |           941.7 |    3.64 |      0.27 | False    |
| Q08     | exasol            | starrocks           |         132   |           986.9 |    7.48 |      0.13 | False    |
| Q09     | exasol            | starrocks           |         539.5 |          1006.1 |    1.86 |      0.54 | False    |
| Q10     | exasol            | starrocks           |         473.2 |           866.7 |    1.83 |      0.55 | False    |
| Q11     | exasol            | starrocks           |         225.3 |           324   |    1.44 |      0.7  | False    |
| Q12     | exasol            | starrocks           |         156.6 |           723   |    4.62 |      0.22 | False    |
| Q13     | exasol            | starrocks           |         653.6 |           519   |    0.79 |      1.26 | True     |
| Q14     | exasol            | starrocks           |          67.3 |           352.2 |    5.23 |      0.19 | False    |
| Q15     | exasol            | starrocks           |         121.8 |           380.9 |    3.13 |      0.32 | False    |
| Q16     | exasol            | starrocks           |         378.1 |           851.2 |    2.25 |      0.44 | False    |
| Q17     | exasol            | starrocks           |          53.2 |           509.7 |    9.58 |      0.1  | False    |
| Q18     | exasol            | starrocks           |         345.7 |          1772.8 |    5.13 |      0.2  | False    |
| Q19     | exasol            | starrocks           |          85.6 |           331.4 |    3.87 |      0.26 | False    |
| Q20     | exasol            | starrocks           |         195.5 |           429.5 |    2.2  |      0.46 | False    |
| Q21     | exasol            | starrocks           |         319.9 |          2133.7 |    6.67 |      0.15 | False    |
| Q22     | exasol            | starrocks           |         157.5 |           296.2 |    1.88 |      0.53 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 347.2 | 166.8 | 10.4 | 2582.4 |
| 1 | 22 | 224.6 | 157.9 | 64.7 | 653.6 |
| 2 | 22 | 278.7 | 213.4 | 53.2 | 662.8 |
| 3 | 22 | 276.9 | 232.8 | 49.4 | 594.3 |
| 4 | 22 | 270.0 | 180.7 | 60.5 | 772.3 |

**Performance Analysis for Exasol:**
- Fastest stream median: 157.9ms
- Slowest stream median: 232.8ms
- Stream performance variation: 47.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 815.2 | 570.6 | 190.9 | 2886.3 |
| 1 | 22 | 583.0 | 519.6 | 176.2 | 1129.8 |
| 2 | 22 | 820.1 | 552.6 | 161.8 | 3344.2 |
| 3 | 22 | 798.2 | 743.0 | 328.2 | 2133.7 |
| 4 | 22 | 797.1 | 553.8 | 147.9 | 2927.6 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 519.6ms
- Slowest stream median: 743.0ms
- Stream performance variation: 43.0% difference between fastest and slowest streams
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
- Median runtime: 178.4ms
- Average runtime: 279.5ms
- Fastest query: 10.4ms
- Slowest query: 2582.4ms

**starrocks:**
- Median runtime: 566.2ms
- Average runtime: 762.7ms
- Fastest query: 147.9ms
- Slowest query: 3344.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_1g_mu5-benchmark.zip`](starrocks_exa_vs_sr_1g_mu5-benchmark.zip)

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