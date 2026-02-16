# Exasol 1N vs 2N: TPC-H SF500 with Replication Border

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6i.12xlarge
**Date:** 2026-02-10 20:04:43

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol_1n**
- **exasol_2n**

**Key Findings:**
- exasol_1n was the fastest overall with 819.5ms median runtime
- exasol_2n was 1.2x slower- Tested 220 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol_1n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6i.12xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 48 vCPUs
- **Memory:** 371.7GB RAM
- **Hostname:** ip-10-0-1-71

### Exasol_2n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6i.12xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 48 vCPUs (96 total vCPUs)
- **Memory per node:** 371.7GB RAM (743.4GB total RAM)
- **Node hostnames:**
  - exasol_2n-node1: ip-10-0-1-211
  - exasol_2n-node0: ip-10-0-1-21


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol_1n Instance:** r6i.12xlarge
- **Exasol_2n Instance:** r6i.12xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol_2n 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 2 Nodes] Create 650GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 650GiB

# [All 2 Nodes] Create raw partition for Exasol (850GB)
sudo parted -s /dev/nvme1n1 mkpart primary 650GiB 100%

# [All 2 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 2 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 2 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# [All 2 Nodes] Add exasol user to sudo group
sudo usermod -aG sudo exasol || true

# Set password for exasol user (interactive)
sudo passwd exasol

```

**Tool Setup:**
```bash
# Download c4 cluster management tool v4.28.5
wget -q --tries=3 --retry-connrefused --waitretry=5 https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

```

**Configuration:**
```bash
# Create c4 configuration file on remote system
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.2.0
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=288000
CCC_ADMINUI_START_SERVER=true&#34; | tee /tmp/exasol_c4.conf &gt; /dev/null

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
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;,&#39;-replicationborder=5500000&#39;]&#34;

# Starting database with new parameters
confd_client db_start db_name: Exasol

```

**Setup:**
```bash
# [All 2 Nodes] Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

```

**Cluster Management:**
```bash
# Get cluster play ID for confd_client operations
c4 ps

```

**Redundancy:**
```bash
# Stop database for redundancy change
confd_client db_stop db_name: Exasol

# Decrease volume redundancy to 1
confd_client st_volume_decrease_redundancy vname: DataVolume1 delta: 1

# Restart database after redundancy change
confd_client db_start db_name: Exasol

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
  - `-replicationborder=5500000`

**Data Directory:** `None`



#### Exasol_1n 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 650GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 650GiB

# Create raw partition for Exasol (850GB)
sudo parted -s /dev/nvme1n1 mkpart primary 650GiB 100%

# Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

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
- **Scale factor:** 500
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_1n2n_sf500-benchmark.zip
cd exa_1n2n_sf500

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
| Exasol_1n | 1602.42s | 2.03s | 2836.68s | 5753.39s | 478.6 GB | 116.7 GB | 4.1x |
| Exasol_2n | 1598.91s | 2.38s | 2614.30s | 4855.64s | 478.6 GB | 117.3 GB | 4.1x |

**Key Observations:**
- Exasol_2n had the fastest preparation time at 4855.64s
- Exasol_1n took 5753.39s (1.2x slower)

### Performance Summary

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol_1n |   2795.5 |      5 |      2859.1 |    2864.1 |     42.5 |   2811.5 |   2919.4 |
| Q01     | exasol_2n |   1400.5 |      5 |      1428.6 |    1424.9 |      7.6 |   1415.2 |   1431.9 |
| Q02     | exasol_1n |    193.3 |      5 |       166.4 |     164.9 |      5.2 |    157.5 |    171.4 |
| Q02     | exasol_2n |    600.8 |      5 |       169.9 |     170.6 |      2.5 |    168.7 |    174.9 |
| Q03     | exasol_1n |   1220.8 |      5 |      1215   |    1218.5 |     14.4 |   1198.4 |   1234.8 |
| Q03     | exasol_2n |   1630.7 |      5 |      1655.1 |    1662.2 |     17.1 |   1647.3 |   1690.6 |
| Q04     | exasol_1n |    200.2 |      5 |       195.4 |     196.5 |      2.5 |    195.2 |    201   |
| Q04     | exasol_2n |    460.5 |      5 |       466.8 |     466.4 |      4.9 |    458.5 |    472   |
| Q05     | exasol_1n |    885.9 |      5 |       768.6 |     764.9 |     11.2 |    745.8 |    773.7 |
| Q05     | exasol_2n |   2128.6 |      5 |      1817.9 |    1806.3 |     56.3 |   1715.5 |   1860.6 |
| Q06     | exasol_1n |    145.9 |      5 |       145.4 |     145.3 |      0.3 |    145   |    145.7 |
| Q06     | exasol_2n |     91.5 |      5 |        90.7 |      90.4 |      0.6 |     89.7 |     91   |
| Q07     | exasol_1n |   1126   |      5 |      1136.8 |    1147.2 |     24.8 |   1124.4 |   1175.4 |
| Q07     | exasol_2n |   2106.8 |      5 |      2083.5 |    2077.3 |    139.2 |   1884   |   2253.4 |
| Q08     | exasol_1n |    267.6 |      5 |       252.5 |     259.6 |     16.9 |    250.5 |    289.9 |
| Q08     | exasol_2n |   1030.4 |      5 |      1030   |    1042.5 |     30.6 |   1027.4 |   1097.2 |
| Q09     | exasol_1n |   3627.5 |      5 |      3613.3 |    3613.5 |     10.7 |   3598.1 |   3626.4 |
| Q09     | exasol_2n |   9912   |      5 |      9960.4 |    9939.7 |     83.8 |   9819.3 |  10015   |
| Q10     | exasol_1n |   2327.3 |      5 |      2310   |    2335.4 |     52.6 |   2283.9 |   2394.8 |
| Q10     | exasol_2n |   1889.6 |      5 |      1708.7 |    1687.8 |     44.6 |   1638.5 |   1734.9 |
| Q11     | exasol_1n |    560.3 |      5 |       536.3 |     544.9 |     15.7 |    534.4 |    571.9 |
| Q11     | exasol_2n |    349.1 |      5 |       339.1 |     338.4 |      4.5 |    331.7 |    343.9 |
| Q12     | exasol_1n |    311.2 |      5 |       286.1 |     286   |      1.3 |    284.3 |    288   |
| Q12     | exasol_2n |    486.7 |      5 |       483.1 |     483.3 |      1.1 |    482.4 |    485.1 |
| Q13     | exasol_1n |   2600.5 |      5 |      2554.2 |    2554.8 |     11.4 |   2537.8 |   2569.1 |
| Q13     | exasol_2n |   1325   |      5 |      1314   |    1312.6 |      5.2 |   1304.1 |   1318.1 |
| Q14     | exasol_1n |    334.7 |      5 |       320.6 |     323.1 |      5.4 |    320.1 |    332.7 |
| Q14     | exasol_2n |    865.8 |      5 |       867.3 |     866.5 |      1.8 |    864.5 |    868.4 |
| Q15     | exasol_1n |   1689.3 |      5 |      1692.5 |    1695.3 |     24.3 |   1668.3 |   1729   |
| Q15     | exasol_2n |   1059.7 |      5 |      1060.5 |    1100.9 |     85.5 |   1056.7 |   1253.5 |
| Q16     | exasol_1n |   1380.5 |      5 |      1368.4 |    1360.4 |     16.4 |   1332.4 |   1371.8 |
| Q16     | exasol_2n |   1046.9 |      5 |      1055.4 |    1054.4 |      8.5 |   1044   |   1065.5 |
| Q17     | exasol_1n |     94.3 |      5 |        92.9 |      92.8 |      0.3 |     92.4 |     93.2 |
| Q17     | exasol_2n |    151.7 |      5 |       149.1 |     149.3 |      1   |    148.3 |    150.6 |
| Q18     | exasol_1n |   2807.8 |      5 |      2778.9 |    2779.4 |     22.7 |   2745.6 |   2805.6 |
| Q18     | exasol_2n |   1427.2 |      5 |      1452.1 |    1454.2 |     11.8 |   1439.1 |   1471.6 |
| Q19     | exasol_1n |     90.9 |      5 |        82.4 |      82.5 |      0.5 |     81.7 |     83   |
| Q19     | exasol_2n |    196.8 |      5 |       195.2 |     195.4 |      1.5 |    193.5 |    197   |
| Q20     | exasol_1n |    894   |      5 |       881.8 |     887.6 |     20.4 |    865.2 |    920.4 |
| Q20     | exasol_2n |    763.3 |      5 |       761.9 |     765.6 |      8.5 |    756.9 |    777.2 |
| Q21     | exasol_1n |   1481.9 |      5 |      1517.7 |    1512.9 |     16   |   1490.6 |   1529.2 |
| Q21     | exasol_2n |    891.8 |      5 |       900.6 |     900.4 |      6.6 |    891.9 |    909.2 |
| Q22     | exasol_1n |    321.2 |      5 |       307.1 |     308.8 |      2.7 |    306.5 |    312.4 |
| Q22     | exasol_2n |    192   |      5 |       184.4 |     184.5 |      1.1 |    183.3 |    186.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol_1n         | exasol_2n           |        2859.1 |          1428.6 |    0.5  |      2    | True     |
| Q02     | exasol_1n         | exasol_2n           |         166.4 |           169.9 |    1.02 |      0.98 | False    |
| Q03     | exasol_1n         | exasol_2n           |        1215   |          1655.1 |    1.36 |      0.73 | False    |
| Q04     | exasol_1n         | exasol_2n           |         195.4 |           466.8 |    2.39 |      0.42 | False    |
| Q05     | exasol_1n         | exasol_2n           |         768.6 |          1817.9 |    2.37 |      0.42 | False    |
| Q06     | exasol_1n         | exasol_2n           |         145.4 |            90.7 |    0.62 |      1.6  | True     |
| Q07     | exasol_1n         | exasol_2n           |        1136.8 |          2083.5 |    1.83 |      0.55 | False    |
| Q08     | exasol_1n         | exasol_2n           |         252.5 |          1030   |    4.08 |      0.25 | False    |
| Q09     | exasol_1n         | exasol_2n           |        3613.3 |          9960.4 |    2.76 |      0.36 | False    |
| Q10     | exasol_1n         | exasol_2n           |        2310   |          1708.7 |    0.74 |      1.35 | True     |
| Q11     | exasol_1n         | exasol_2n           |         536.3 |           339.1 |    0.63 |      1.58 | True     |
| Q12     | exasol_1n         | exasol_2n           |         286.1 |           483.1 |    1.69 |      0.59 | False    |
| Q13     | exasol_1n         | exasol_2n           |        2554.2 |          1314   |    0.51 |      1.94 | True     |
| Q14     | exasol_1n         | exasol_2n           |         320.6 |           867.3 |    2.71 |      0.37 | False    |
| Q15     | exasol_1n         | exasol_2n           |        1692.5 |          1060.5 |    0.63 |      1.6  | True     |
| Q16     | exasol_1n         | exasol_2n           |        1368.4 |          1055.4 |    0.77 |      1.3  | True     |
| Q17     | exasol_1n         | exasol_2n           |          92.9 |           149.1 |    1.6  |      0.62 | False    |
| Q18     | exasol_1n         | exasol_2n           |        2778.9 |          1452.1 |    0.52 |      1.91 | True     |
| Q19     | exasol_1n         | exasol_2n           |          82.4 |           195.2 |    2.37 |      0.42 | False    |
| Q20     | exasol_1n         | exasol_2n           |         881.8 |           761.9 |    0.86 |      1.16 | True     |
| Q21     | exasol_1n         | exasol_2n           |        1517.7 |           900.6 |    0.59 |      1.69 | True     |
| Q22     | exasol_1n         | exasol_2n           |         307.1 |           184.4 |    0.6  |      1.67 | True     |


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

**exasol_1n:**
- Median runtime: 819.5ms
- Average runtime: 1142.7ms
- Fastest query: 81.7ms
- Slowest query: 3626.4ms

**exasol_2n:**
- Median runtime: 968.3ms
- Average runtime: 1326.1ms
- Fastest query: 89.7ms
- Slowest query: 10015.0ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_1n2n_sf500-benchmark.zip`](exa_1n2n_sf500-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 48 logical cores
- **Memory:** 371.7GB RAM
- **Storage:** NVMe SSD recommended for optimal performance
- **OS:** Linux

### Configuration Files

The exact configuration used for this benchmark is available at:
[`attachments/config.yaml`](attachments/config.yaml)

### System Specifications

**Exasol_1n 2025.2.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Exasol_2n 2025.2.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;, &#39;-replicationborder=5500000&#39;]


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