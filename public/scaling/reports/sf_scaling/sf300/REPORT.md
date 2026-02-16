# Exasol 1N vs 2N: TPC-H SF300 with Replication Border

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6i.8xlarge
**Date:** 2026-02-10 19:36:18

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol_2n**
- **exasol_1n**

**Key Findings:**
- exasol_2n was the fastest overall with 591.5ms median runtime
- exasol_1n was 1.2x slower- Tested 220 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol_1n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6i.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-145

### Exasol_2n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6i.8xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 32 vCPUs (64 total vCPUs)
- **Memory per node:** 247.7GB RAM (495.4GB total RAM)
- **Node hostnames:**
  - exasol_2n-node1: ip-10-0-1-153
  - exasol_2n-node0: ip-10-0-1-200


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol_1n Instance:** r6i.8xlarge
- **Exasol_2n Instance:** r6i.8xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol_2n 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 2 Nodes] Create 390GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 390GiB

# [All 2 Nodes] Create raw partition for Exasol (610GB)
sudo parted -s /dev/nvme1n1 mkpart primary 390GiB 100%

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
CCC_PLAY_DB_MEM_SIZE=192000
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
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;,&#39;-replicationborder=3300000&#39;]&#34;

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
  - `-replicationborder=3300000`

**Data Directory:** `None`



#### Exasol_1n 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 390GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 390GiB

# Create raw partition for Exasol (610GB)
sudo parted -s /dev/nvme1n1 mkpart primary 390GiB 100%

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
- **Scale factor:** 300
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_1n2n_sf300-benchmark.zip
cd exa_1n2n_sf300

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
| Exasol_1n | 1401.11s | 2.03s | 1808.06s | 4110.58s | 287.2 GB | 69.5 GB | 4.1x |
| Exasol_2n | 1403.77s | 2.19s | 1590.76s | 3423.02s | 287.2 GB | 69.8 GB | 4.1x |

**Key Observations:**
- Exasol_2n had the fastest preparation time at 3423.02s
- Exasol_1n took 4110.58s (1.2x slower)

### Performance Summary

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol_1n |   2374.1 |      5 |      2363.3 |    2364   |      5.8 |   2356.1 |   2372.5 |
| Q01     | exasol_2n |   1203.8 |      5 |      1198.9 |    1198.5 |      1.5 |   1196.1 |   1199.7 |
| Q02     | exasol_1n |    151.9 |      5 |       124.4 |     125.3 |      4.8 |    119.8 |    132   |
| Q02     | exasol_2n |    282.1 |      5 |       116.1 |     117.2 |      2   |    115.5 |    120.3 |
| Q03     | exasol_1n |    970.7 |      5 |       962.6 |     962.9 |      6.6 |    957.4 |    973.7 |
| Q03     | exasol_2n |    960   |      5 |       945.8 |     947.6 |      4.7 |    943   |    953.3 |
| Q04     | exasol_1n |    170.6 |      5 |       167   |     168   |      2.1 |    166.8 |    171.8 |
| Q04     | exasol_2n |    236.2 |      5 |       234.1 |     235.5 |      2.7 |    233.2 |    238.9 |
| Q05     | exasol_1n |    771.8 |      5 |       650.4 |     651   |      1.5 |    650   |    653.7 |
| Q05     | exasol_2n |    825.4 |      5 |       601.8 |     606   |     10.2 |    600.2 |    624.1 |
| Q06     | exasol_1n |    117.6 |      5 |       117.2 |     117.1 |      0.3 |    116.7 |    117.5 |
| Q06     | exasol_2n |     66.5 |      5 |        66   |      66   |      0.2 |     65.7 |     66.2 |
| Q07     | exasol_1n |    902   |      5 |       898.1 |     898.5 |      2   |    896.5 |    901.9 |
| Q07     | exasol_2n |   1177.1 |      5 |      1174.4 |    1175.9 |      2.4 |   1174   |   1179.3 |
| Q08     | exasol_1n |    210   |      5 |       207.7 |     220.7 |     29.3 |    207.1 |    273.2 |
| Q08     | exasol_2n |    400.8 |      5 |       407.4 |     426.5 |     46.9 |    400.1 |    510.1 |
| Q09     | exasol_1n |   3244.6 |      5 |      3123.2 |    3128.2 |      9.3 |   3120.6 |   3143.6 |
| Q09     | exasol_2n |   3969   |      5 |      3868.5 |    3869.8 |     57.4 |   3789.6 |   3944.7 |
| Q10     | exasol_1n |   1566.7 |      5 |      1584.9 |    1581.1 |     14.4 |   1561.1 |   1598   |
| Q10     | exasol_2n |   1103.4 |      5 |      1077.3 |    1081.7 |     16.7 |   1067.3 |   1109.1 |
| Q11     | exasol_1n |    376.4 |      5 |       376.3 |     375.2 |      3.8 |    369.3 |    379.6 |
| Q11     | exasol_2n |    246.3 |      5 |       232.7 |     232.5 |      6.8 |    223.3 |    242.4 |
| Q12     | exasol_1n |    236.5 |      5 |       231.9 |     232.1 |      0.6 |    231.5 |    233.1 |
| Q12     | exasol_2n |    268.7 |      5 |       208.8 |     209.5 |      1.7 |    207.9 |    211.9 |
| Q13     | exasol_1n |   2101.2 |      5 |      2078.3 |    2077.2 |      5   |   2071.3 |   2083   |
| Q13     | exasol_2n |   1135.1 |      5 |      1095.6 |    1096.8 |      4.5 |   1093.6 |   1104.6 |
| Q14     | exasol_1n |    300.5 |      5 |       271.7 |     272.1 |      0.7 |    271.5 |    273.1 |
| Q14     | exasol_2n |    424   |      5 |       472.8 |     447.4 |     40.2 |    396.2 |    478.3 |
| Q15     | exasol_1n |   1091.7 |      5 |      1093.9 |    1095.3 |      5.8 |   1088.6 |   1103.4 |
| Q15     | exasol_2n |    645   |      5 |       646.1 |     648   |      9.3 |    638.1 |    662.8 |
| Q16     | exasol_1n |   1111.1 |      5 |      1087.6 |    1086.9 |     14.7 |   1072.2 |   1109   |
| Q16     | exasol_2n |    708.7 |      5 |       726.3 |     724.1 |     15.9 |    704.3 |    745.3 |
| Q17     | exasol_1n |     67.6 |      5 |        65.3 |      65.3 |      0.4 |     64.8 |     65.8 |
| Q17     | exasol_2n |     75.4 |      5 |        74.8 |      76.1 |      2.1 |     74.3 |     78.8 |
| Q18     | exasol_1n |   1924.3 |      5 |      1930.1 |    1928.9 |      8.8 |   1916.1 |   1940.3 |
| Q18     | exasol_2n |    992   |      5 |       981   |     980   |      4.3 |    973.4 |    984.1 |
| Q19     | exasol_1n |     75.6 |      5 |        75.2 |      75.4 |      0.5 |     75   |     76.2 |
| Q19     | exasol_2n |     99.5 |      5 |        97   |      99.2 |      3.5 |     96   |    103.2 |
| Q20     | exasol_1n |    733.3 |      5 |       721.8 |     723.9 |      5.9 |    718.4 |    733.7 |
| Q20     | exasol_2n |    588.7 |      5 |       573   |     576.5 |      5.9 |    570.9 |    582.9 |
| Q21     | exasol_1n |   1266.3 |      5 |      1268   |    1269.4 |      3.3 |   1267.1 |   1275.2 |
| Q21     | exasol_2n |    756.3 |      5 |       751.6 |     755.6 |     10.9 |    746.6 |    774.1 |
| Q22     | exasol_1n |    265.9 |      5 |       263.6 |     263.3 |      0.5 |    262.5 |    263.8 |
| Q22     | exasol_2n |    153.7 |      5 |       152.6 |     151.6 |      2.2 |    147.7 |    153.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol_1n         | exasol_2n           |        2363.3 |          1198.9 |    0.51 |      1.97 | True     |
| Q02     | exasol_1n         | exasol_2n           |         124.4 |           116.1 |    0.93 |      1.07 | True     |
| Q03     | exasol_1n         | exasol_2n           |         962.6 |           945.8 |    0.98 |      1.02 | True     |
| Q04     | exasol_1n         | exasol_2n           |         167   |           234.1 |    1.4  |      0.71 | False    |
| Q05     | exasol_1n         | exasol_2n           |         650.4 |           601.8 |    0.93 |      1.08 | True     |
| Q06     | exasol_1n         | exasol_2n           |         117.2 |            66   |    0.56 |      1.78 | True     |
| Q07     | exasol_1n         | exasol_2n           |         898.1 |          1174.4 |    1.31 |      0.76 | False    |
| Q08     | exasol_1n         | exasol_2n           |         207.7 |           407.4 |    1.96 |      0.51 | False    |
| Q09     | exasol_1n         | exasol_2n           |        3123.2 |          3868.5 |    1.24 |      0.81 | False    |
| Q10     | exasol_1n         | exasol_2n           |        1584.9 |          1077.3 |    0.68 |      1.47 | True     |
| Q11     | exasol_1n         | exasol_2n           |         376.3 |           232.7 |    0.62 |      1.62 | True     |
| Q12     | exasol_1n         | exasol_2n           |         231.9 |           208.8 |    0.9  |      1.11 | True     |
| Q13     | exasol_1n         | exasol_2n           |        2078.3 |          1095.6 |    0.53 |      1.9  | True     |
| Q14     | exasol_1n         | exasol_2n           |         271.7 |           472.8 |    1.74 |      0.57 | False    |
| Q15     | exasol_1n         | exasol_2n           |        1093.9 |           646.1 |    0.59 |      1.69 | True     |
| Q16     | exasol_1n         | exasol_2n           |        1087.6 |           726.3 |    0.67 |      1.5  | True     |
| Q17     | exasol_1n         | exasol_2n           |          65.3 |            74.8 |    1.15 |      0.87 | False    |
| Q18     | exasol_1n         | exasol_2n           |        1930.1 |           981   |    0.51 |      1.97 | True     |
| Q19     | exasol_1n         | exasol_2n           |          75.2 |            97   |    1.29 |      0.78 | False    |
| Q20     | exasol_1n         | exasol_2n           |         721.8 |           573   |    0.79 |      1.26 | True     |
| Q21     | exasol_1n         | exasol_2n           |        1268   |           751.6 |    0.59 |      1.69 | True     |
| Q22     | exasol_1n         | exasol_2n           |         263.6 |           152.6 |    0.58 |      1.73 | True     |


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

**exasol_2n:**
- Median runtime: 591.5ms
- Average runtime: 714.6ms
- Fastest query: 65.7ms
- Slowest query: 3944.7ms

**exasol_1n:**
- Median runtime: 686.0ms
- Average runtime: 894.6ms
- Fastest query: 64.8ms
- Slowest query: 3143.6ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_1n2n_sf300-benchmark.zip`](exa_1n2n_sf300-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 32 logical cores
- **Memory:** 247.7GB RAM
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
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;, &#39;-replicationborder=3300000&#39;]


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