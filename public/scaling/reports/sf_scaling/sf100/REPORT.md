# Exasol 1N vs 2N: TPC-H SF100 with Replication Border

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / m6i.8xlarge
**Date:** 2026-02-10 13:06:25

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol_1n**
- **exasol_2n**

**Key Findings:**
- exasol_1n was the fastest overall with 242.4ms median runtime
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
- **Instance Type:** m6i.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-73

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
  - exasol_2n-node1: ip-10-0-1-197
  - exasol_2n-node0: ip-10-0-1-18


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

# [All 2 Nodes] Create 132GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# [All 2 Nodes] Create raw partition for Exasol (368GB)
sudo parted -s /dev/nvme1n1 mkpart primary 132GiB 100%

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
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;,&#39;-replicationborder=1100000&#39;]&#34;

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
  - `-replicationborder=1100000`

**Data Directory:** `None`



#### Exasol_1n 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 132GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Create raw partition for Exasol (368GB)
sudo parted -s /dev/nvme1n1 mkpart primary 132GiB 100%

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
unzip exa_1n2n_sf100-benchmark.zip
cd exa_1n2n_sf100

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
| Exasol_1n | 1007.67s | 2.02s | 980.39s | 2339.93s | 95.7 GB | 22.9 GB | 4.2x |
| Exasol_2n | 1012.58s | 2.39s | 700.85s | 1887.34s | 95.7 GB | 23.0 GB | 4.2x |

**Key Observations:**
- Exasol_2n had the fastest preparation time at 1887.34s
- Exasol_1n took 2339.93s (1.2x slower)

### Performance Summary

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol_1n |    794.9 |      5 |       792.1 |     793   |      2.3 |    790.4 |    796.4 |
| Q01     | exasol_2n |    427.8 |      5 |       418.4 |     418.7 |      0.8 |    418.1 |    420   |
| Q02     | exasol_1n |    109.2 |      5 |        76.9 |      76.6 |      1.1 |     74.8 |     77.7 |
| Q02     | exasol_2n |    231.8 |      5 |       109.8 |     109.9 |      0.5 |    109.2 |    110.5 |
| Q03     | exasol_1n |    347.1 |      5 |       338   |     339.3 |      2.9 |    337.4 |    344.3 |
| Q03     | exasol_2n |    393.5 |      5 |       385.6 |     388.8 |      8.1 |    380.8 |    400.1 |
| Q04     | exasol_1n |     63   |      5 |        60.6 |      60.6 |      0.2 |     60.4 |     60.9 |
| Q04     | exasol_2n |    115.1 |      5 |       114.7 |     115   |      1.9 |    113.2 |    118   |
| Q05     | exasol_1n |    292.8 |      5 |       208.3 |     208.3 |      0.3 |    207.9 |    208.6 |
| Q05     | exasol_2n |    494   |      5 |       330.6 |     331   |      2.5 |    327.7 |    334.7 |
| Q06     | exasol_1n |     41.7 |      5 |        41.7 |      41.7 |      0.2 |     41.5 |     42.1 |
| Q06     | exasol_2n |     37.4 |      5 |        36.6 |      36.6 |      0.3 |     36.2 |     36.9 |
| Q07     | exasol_1n |    278.7 |      5 |       277.3 |     277   |      0.7 |    276.3 |    277.7 |
| Q07     | exasol_2n |    443.4 |      5 |       446.8 |     445.4 |      7.7 |    432   |    451   |
| Q08     | exasol_1n |     76.7 |      5 |        76.2 |      86.9 |     24.7 |     74.9 |    131   |
| Q08     | exasol_2n |    273.7 |      5 |       265.9 |     281.9 |     38.3 |    262.1 |    350.4 |
| Q09     | exasol_1n |    986.4 |      5 |       957.9 |     960.9 |      7.1 |    957.3 |    973.6 |
| Q09     | exasol_2n |   1607.2 |      5 |      1599.5 |    1601.5 |      3.7 |   1597.9 |   1606.7 |
| Q10     | exasol_1n |    577.5 |      5 |       582.2 |     583.7 |      6.4 |    575.5 |    592.3 |
| Q10     | exasol_2n |    557.9 |      5 |       508.4 |     511.2 |      5.6 |    505.9 |    519.7 |
| Q11     | exasol_1n |    149.7 |      5 |       153.8 |     152.7 |      3.1 |    148.9 |    156.7 |
| Q11     | exasol_2n |    170.5 |      5 |       162   |     163.3 |      2.7 |    161.3 |    167.8 |
| Q12     | exasol_1n |    106.5 |      5 |        83.7 |      83.7 |      0.2 |     83.4 |     84   |
| Q12     | exasol_2n |    132   |      5 |       121.3 |     121.3 |      0.9 |    120.1 |    122.5 |
| Q13     | exasol_1n |    701.1 |      5 |       688   |     688.3 |      2.6 |    685.8 |    691.1 |
| Q13     | exasol_2n |    465.3 |      5 |       430.4 |     430.1 |      0.6 |    429.4 |    430.7 |
| Q14     | exasol_1n |    112.3 |      5 |        83.1 |      83.1 |      0.2 |     82.8 |     83.3 |
| Q14     | exasol_2n |    194.3 |      5 |       193.8 |     193.5 |      0.9 |    192.5 |    194.4 |
| Q15     | exasol_1n |    380.8 |      5 |       370.9 |     385.9 |     35.6 |    367.3 |    449.5 |
| Q15     | exasol_2n |    324.5 |      5 |       322.7 |     330.9 |     14.6 |    318   |    348.1 |
| Q16     | exasol_1n |    462.4 |      5 |       465.4 |     468.8 |      9.3 |    460.2 |    484.2 |
| Q16     | exasol_2n |    436.7 |      5 |       427.3 |     429.7 |     10.1 |    419.4 |    446.5 |
| Q17     | exasol_1n |     31.6 |      5 |        29   |      29.1 |      0.2 |     28.8 |     29.4 |
| Q17     | exasol_2n |     73.3 |      5 |        71.2 |      71.6 |      1.2 |     70.6 |     73.6 |
| Q18     | exasol_1n |    637.6 |      5 |       632.2 |     633.1 |      3.4 |    629.7 |    638.7 |
| Q18     | exasol_2n |    373.6 |      5 |       367.3 |     367.6 |      1.4 |    366.1 |    369.9 |
| Q19     | exasol_1n |     46.4 |      5 |        28.1 |      28.1 |      0.3 |     27.8 |     28.6 |
| Q19     | exasol_2n |     61.5 |      5 |        58.9 |      60   |      1.6 |     58.8 |     61.7 |
| Q20     | exasol_1n |    279.7 |      5 |       279.3 |     281.2 |      3.6 |    278   |    286.1 |
| Q20     | exasol_2n |    285.9 |      5 |       283.7 |     295.8 |     22   |    283.1 |    334   |
| Q21     | exasol_1n |    419.6 |      5 |       418.4 |     418.4 |      0.3 |    418.1 |    418.9 |
| Q21     | exasol_2n |    293.5 |      5 |       293.1 |     293.7 |      4.1 |    290.2 |    300.5 |
| Q22     | exasol_1n |     96.1 |      5 |        94.5 |      94.3 |      0.5 |     93.6 |     94.7 |
| Q22     | exasol_2n |     78.3 |      5 |        75.8 |      75.6 |      1   |     74.2 |     76.9 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol_1n         | exasol_2n           |         792.1 |           418.4 |    0.53 |      1.89 | True     |
| Q02     | exasol_1n         | exasol_2n           |          76.9 |           109.8 |    1.43 |      0.7  | False    |
| Q03     | exasol_1n         | exasol_2n           |         338   |           385.6 |    1.14 |      0.88 | False    |
| Q04     | exasol_1n         | exasol_2n           |          60.6 |           114.7 |    1.89 |      0.53 | False    |
| Q05     | exasol_1n         | exasol_2n           |         208.3 |           330.6 |    1.59 |      0.63 | False    |
| Q06     | exasol_1n         | exasol_2n           |          41.7 |            36.6 |    0.88 |      1.14 | True     |
| Q07     | exasol_1n         | exasol_2n           |         277.3 |           446.8 |    1.61 |      0.62 | False    |
| Q08     | exasol_1n         | exasol_2n           |          76.2 |           265.9 |    3.49 |      0.29 | False    |
| Q09     | exasol_1n         | exasol_2n           |         957.9 |          1599.5 |    1.67 |      0.6  | False    |
| Q10     | exasol_1n         | exasol_2n           |         582.2 |           508.4 |    0.87 |      1.15 | True     |
| Q11     | exasol_1n         | exasol_2n           |         153.8 |           162   |    1.05 |      0.95 | False    |
| Q12     | exasol_1n         | exasol_2n           |          83.7 |           121.3 |    1.45 |      0.69 | False    |
| Q13     | exasol_1n         | exasol_2n           |         688   |           430.4 |    0.63 |      1.6  | True     |
| Q14     | exasol_1n         | exasol_2n           |          83.1 |           193.8 |    2.33 |      0.43 | False    |
| Q15     | exasol_1n         | exasol_2n           |         370.9 |           322.7 |    0.87 |      1.15 | True     |
| Q16     | exasol_1n         | exasol_2n           |         465.4 |           427.3 |    0.92 |      1.09 | True     |
| Q17     | exasol_1n         | exasol_2n           |          29   |            71.2 |    2.46 |      0.41 | False    |
| Q18     | exasol_1n         | exasol_2n           |         632.2 |           367.3 |    0.58 |      1.72 | True     |
| Q19     | exasol_1n         | exasol_2n           |          28.1 |            58.9 |    2.1  |      0.48 | False    |
| Q20     | exasol_1n         | exasol_2n           |         279.3 |           283.7 |    1.02 |      0.98 | False    |
| Q21     | exasol_1n         | exasol_2n           |         418.4 |           293.1 |    0.7  |      1.43 | True     |
| Q22     | exasol_1n         | exasol_2n           |          94.5 |            75.8 |    0.8  |      1.25 | True     |


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
- Median runtime: 242.4ms
- Average runtime: 307.9ms
- Fastest query: 27.8ms
- Slowest query: 973.6ms

**exasol_2n:**
- Median runtime: 293.5ms
- Average runtime: 321.5ms
- Fastest query: 36.2ms
- Slowest query: 1606.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_1n2n_sf100-benchmark.zip`](exa_1n2n_sf100-benchmark.zip)

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
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;, &#39;-replicationborder=1100000&#39;]


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