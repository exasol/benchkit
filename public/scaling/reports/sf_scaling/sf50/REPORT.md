# Exasol 1N vs 2N: TPC-H SF50 with Replication Border

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / m6i.8xlarge
**Date:** 2026-02-10 17:59:00

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol_2n**
- **exasol_1n**

**Key Findings:**
- exasol_1n was the fastest overall with 134.8ms median runtime
- exasol_2n was 1.1x slower- Tested 220 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol_1n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6i.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-19

### Exasol_2n 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6i.8xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 32 vCPUs (64 total vCPUs)
- **Memory per node:** 123.8GB RAM (247.6GB total RAM)
- **Node hostnames:**
  - exasol_2n-node1: ip-10-0-1-8
  - exasol_2n-node0: ip-10-0-1-17


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol_1n Instance:** m6i.8xlarge
- **Exasol_2n Instance:** m6i.8xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol_2n 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 2 Nodes] Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 2 Nodes] Create raw partition for Exasol (180GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

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
CCC_PLAY_DB_MEM_SIZE=96000
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
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;,&#39;-replicationborder=550000&#39;]&#34;

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
  - `-replicationborder=550000`

**Data Directory:** `None`



#### Exasol_1n 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (180GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

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
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_1n2n_sf50-benchmark.zip
cd exa_1n2n_sf50

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
| Exasol_1n | 569.98s | 2.03s | 435.76s | 1166.27s | 47.9 GB | 10.5 GB | 4.6x |
| Exasol_2n | 577.88s | 2.17s | 254.07s | 910.16s | 47.9 GB | 10.6 GB | 4.5x |

**Key Observations:**
- Exasol_2n had the fastest preparation time at 910.16s
- Exasol_1n took 1166.27s (1.3x slower)

### Performance Summary

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol_1n |    401.2 |      5 |       401.4 |     401.8 |      0.8 |    401.1 |    402.9 |
| Q01     | exasol_2n |    213.7 |      5 |       215.8 |     216.7 |      1.5 |    215.4 |    218.7 |
| Q02     | exasol_1n |     71.5 |      5 |        49.5 |      49.6 |      0.5 |     49.1 |     50.4 |
| Q02     | exasol_2n |    126.5 |      5 |        64.9 |      66   |      2.7 |     62.9 |     68.9 |
| Q03     | exasol_1n |    213.1 |      5 |       194.1 |     194.7 |      2.3 |    192.5 |    197.9 |
| Q03     | exasol_2n |    231.4 |      5 |       201.1 |     201.9 |      4.2 |    198.7 |    209   |
| Q04     | exasol_1n |     36.8 |      5 |        34.7 |      34.6 |      0.3 |     34.3 |     34.9 |
| Q04     | exasol_2n |     58.9 |      5 |        56.5 |      57.3 |      2.2 |     54.8 |     60.2 |
| Q05     | exasol_1n |    188   |      5 |       118.7 |     118.5 |      0.5 |    117.7 |    118.9 |
| Q05     | exasol_2n |    223.1 |      5 |       142.3 |     140.5 |      6.8 |    132.5 |    149.4 |
| Q06     | exasol_1n |     24.1 |      5 |        23.8 |      23.8 |      0.2 |     23.6 |     24   |
| Q06     | exasol_2n |     21.2 |      5 |        21.3 |      21.2 |      0.4 |     20.7 |     21.6 |
| Q07     | exasol_1n |    161.7 |      5 |       146.3 |     146.6 |      0.7 |    145.9 |    147.4 |
| Q07     | exasol_2n |    216.5 |      5 |       212.8 |     212.2 |      3   |    208.4 |    215.9 |
| Q08     | exasol_1n |     60.4 |      5 |        46.4 |      58.3 |     26.8 |     45.9 |    106.2 |
| Q08     | exasol_2n |    165   |      5 |       110.9 |     121.6 |     25.7 |    108.1 |    167.5 |
| Q09     | exasol_1n |    527.4 |      5 |       488   |     487.8 |      0.9 |    486.4 |    488.7 |
| Q09     | exasol_2n |    586.6 |      5 |       603.9 |     600   |     18.9 |    568.6 |    619.6 |
| Q10     | exasol_1n |    350.1 |      5 |       340.1 |     337   |      8.8 |    324.9 |    347.6 |
| Q10     | exasol_2n |    331.3 |      5 |       319.8 |     316.8 |      4.9 |    310.4 |    320.7 |
| Q11     | exasol_1n |    125   |      5 |       122.3 |     122.4 |      1.1 |    120.7 |    123.7 |
| Q11     | exasol_2n |     95.1 |      5 |        89.7 |      89.2 |      1.2 |     87.2 |     90.4 |
| Q12     | exasol_1n |     92.7 |      5 |        46.8 |      46.8 |      0.2 |     46.5 |     47.1 |
| Q12     | exasol_2n |     74.3 |      5 |        53.7 |      55   |      3.2 |     52.7 |     60.4 |
| Q13     | exasol_1n |    426.3 |      5 |       394.5 |     394.7 |      2   |    392.3 |    397   |
| Q13     | exasol_2n |    228.8 |      5 |       212.5 |     212.3 |      1   |    211   |    213.3 |
| Q14     | exasol_1n |     52.1 |      5 |        42.8 |      42.9 |      0.5 |     42.5 |     43.7 |
| Q14     | exasol_2n |     81.6 |      5 |        75.2 |      76.1 |      2.7 |     73.5 |     80.6 |
| Q15     | exasol_1n |    206.9 |      5 |       214   |     213.8 |      1.1 |    212.1 |    215.2 |
| Q15     | exasol_2n |    203.3 |      5 |       200.7 |     199.7 |      6.3 |    192.8 |    206.5 |
| Q16     | exasol_1n |    320.9 |      5 |       313.2 |     318.4 |     12.6 |    310.7 |    340.8 |
| Q16     | exasol_2n |    290.5 |      5 |       288.7 |     290.6 |      5.6 |    286.2 |    299.9 |
| Q17     | exasol_1n |     23.2 |      5 |        20.3 |      20.3 |      0.3 |     19.9 |     20.7 |
| Q17     | exasol_2n |     43.7 |      5 |        41.9 |      41.6 |      0.7 |     40.6 |     42.4 |
| Q18     | exasol_1n |    317.6 |      5 |       320.1 |     320.2 |      4.9 |    314.9 |    328.1 |
| Q18     | exasol_2n |    190.9 |      5 |       190.4 |     190.7 |      3.8 |    185.9 |    195.4 |
| Q19     | exasol_1n |     32.3 |      5 |        18   |      18.1 |      0.3 |     17.7 |     18.5 |
| Q19     | exasol_2n |     32.4 |      5 |        32.1 |      31.7 |      0.9 |     30.2 |     32.5 |
| Q20     | exasol_1n |    154.9 |      5 |       155.9 |     156.2 |      1.3 |    154.8 |    158.4 |
| Q20     | exasol_2n |    174.3 |      5 |       171.3 |     171.2 |      2.7 |    168.3 |    175.2 |
| Q21     | exasol_1n |    229.4 |      5 |       229.7 |     229.6 |      0.3 |    229.2 |    229.9 |
| Q21     | exasol_2n |    146.9 |      5 |       144   |     144.1 |      0.5 |    143.4 |    144.6 |
| Q22     | exasol_1n |     54.1 |      5 |        52.6 |      52.7 |      0.2 |     52.5 |     53   |
| Q22     | exasol_2n |     44.7 |      5 |        43   |      43   |      0.6 |     42.3 |     43.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol_1n         | exasol_2n           |         401.4 |           215.8 |    0.54 |      1.86 | True     |
| Q02     | exasol_1n         | exasol_2n           |          49.5 |            64.9 |    1.31 |      0.76 | False    |
| Q03     | exasol_1n         | exasol_2n           |         194.1 |           201.1 |    1.04 |      0.97 | False    |
| Q04     | exasol_1n         | exasol_2n           |          34.7 |            56.5 |    1.63 |      0.61 | False    |
| Q05     | exasol_1n         | exasol_2n           |         118.7 |           142.3 |    1.2  |      0.83 | False    |
| Q06     | exasol_1n         | exasol_2n           |          23.8 |            21.3 |    0.89 |      1.12 | True     |
| Q07     | exasol_1n         | exasol_2n           |         146.3 |           212.8 |    1.45 |      0.69 | False    |
| Q08     | exasol_1n         | exasol_2n           |          46.4 |           110.9 |    2.39 |      0.42 | False    |
| Q09     | exasol_1n         | exasol_2n           |         488   |           603.9 |    1.24 |      0.81 | False    |
| Q10     | exasol_1n         | exasol_2n           |         340.1 |           319.8 |    0.94 |      1.06 | True     |
| Q11     | exasol_1n         | exasol_2n           |         122.3 |            89.7 |    0.73 |      1.36 | True     |
| Q12     | exasol_1n         | exasol_2n           |          46.8 |            53.7 |    1.15 |      0.87 | False    |
| Q13     | exasol_1n         | exasol_2n           |         394.5 |           212.5 |    0.54 |      1.86 | True     |
| Q14     | exasol_1n         | exasol_2n           |          42.8 |            75.2 |    1.76 |      0.57 | False    |
| Q15     | exasol_1n         | exasol_2n           |         214   |           200.7 |    0.94 |      1.07 | True     |
| Q16     | exasol_1n         | exasol_2n           |         313.2 |           288.7 |    0.92 |      1.08 | True     |
| Q17     | exasol_1n         | exasol_2n           |          20.3 |            41.9 |    2.06 |      0.48 | False    |
| Q18     | exasol_1n         | exasol_2n           |         320.1 |           190.4 |    0.59 |      1.68 | True     |
| Q19     | exasol_1n         | exasol_2n           |          18   |            32.1 |    1.78 |      0.56 | False    |
| Q20     | exasol_1n         | exasol_2n           |         155.9 |           171.3 |    1.1  |      0.91 | False    |
| Q21     | exasol_1n         | exasol_2n           |         229.7 |           144   |    0.63 |      1.6  | True     |
| Q22     | exasol_1n         | exasol_2n           |          52.6 |            43   |    0.82 |      1.22 | True     |


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
- Median runtime: 143.9ms
- Average runtime: 159.1ms
- Fastest query: 20.7ms
- Slowest query: 619.6ms

**exasol_1n:**
- Median runtime: 134.8ms
- Average runtime: 172.2ms
- Fastest query: 17.7ms
- Slowest query: 488.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_1n2n_sf50-benchmark.zip`](exa_1n2n_sf50-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 32 logical cores
- **Memory:** 123.8GB RAM
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
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;, &#39;-replicationborder=550000&#39;]


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