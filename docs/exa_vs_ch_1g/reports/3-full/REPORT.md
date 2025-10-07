# Exasol vs ClickHouse Performance Comparison on TPC-H

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-09 08:31:14

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **clickhouse**
- **exasol**

**Key Findings:**
- exasol was the fastest overall with 22.3ms median runtime
- clickhouse was 3.8x slower
- Tested 308 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol 2025.1.0

**Software Configuration:**
- **Database:** exasol 2025.1.0
- **Setup method:** installer

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-169

### Clickhouse 25.9.3.48

**Software Configuration:**
- **Database:** clickhouse 25.9.3.48
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-134


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r5d.4xlarge
- **Clickhouse Instance:** r5d.4xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.0 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme1n1
sudo mdadm --zero-superblock /dev/nvme1n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme2n1
sudo mdadm --zero-superblock /dev/nvme2n1 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/nvme1n1 /dev/nvme2n1

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Create GPT partition table
sudo parted /dev/md0 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/md0 mklabel gpt

# Create 3GB partition for data generation
sudo parted /dev/md0 mkpart primary ext4 1MiB 3GiB

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary ext4 1MiB 3GiB

# Create raw partition for Exasol (555GB)
sudo parted /dev/md0 mkpart primary 3GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary 3GiB 100%

# Format /dev/md0p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0p1

# Create mount point /data/tpch_gen
sudo mkdir -p /data/tpch_gen

# Mount /dev/md0p1 to /data/tpch_gen
sudo mount /dev/md0p1 /data/tpch_gen

# Set ownership of /data/tpch_gen to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data/tpch_gen

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m exasol

# Add exasol user to sudo group
sudo usermod -aG sudo exasol

# Set password for exasol user (interactive)
sudo passwd exasol

```

**Tool Setup:**
```bash
# Download c4 cluster management tool v4.28.2
wget https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.2/c4 -O c4 &amp;&amp; chmod +x c4

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
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;SERVER_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/md0p2
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.0
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
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

**Cluster Management:**
```bash
# Get cluster play ID for confd_client operations
c4 ps

```


**Tuning Parameters:**
- Database RAM: `32g`
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



#### Clickhouse 25.9.3.48 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme1n1
sudo mdadm --zero-superblock /dev/nvme1n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme2n1
sudo mdadm --zero-superblock /dev/nvme2n1 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/nvme1n1 /dev/nvme2n1

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create ClickHouse data directory under /data
sudo mkdir -p /data/clickhouse

# Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# Update package lists
sudo apt-get update

# Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# Install ClickHouse server and client version &lt;SERVER_IP&gt;
sudo apt-get install -y clickhouse-server=25.9.3.48 clickhouse-client=25.9.3.48

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;max_server_memory_usage&gt;106897745510&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;8&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;16&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# Configure ClickHouse user profile with password and query settings
sudo tee /etc/clickhouse-server/users.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;users&gt;
        &lt;default replace=&#34;true&#34;&gt;
            &lt;password_sha256_hex&gt;2cca9d8714615f4132390a3db9296d39ec051b3faff87be7ea5f7fe0e2de14c9&lt;/password_sha256_hex&gt;
            &lt;networks&gt;
                &lt;ip&gt;::/0&lt;/ip&gt;
            &lt;/networks&gt;
        &lt;/default&gt;
    &lt;/users&gt;
    &lt;profiles&gt;
        &lt;default&gt;
            &lt;max_threads&gt;16&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;30000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492200038&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492200038&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# Start ClickHouse server service
sudo systemctl start clickhouse-server

# Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```


**Tuning Parameters:**
- Memory limit: `32g`
- Max threads: `16`
- Max memory usage: `30.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 1
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 7

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_1g-benchmark.zip
cd exa_vs_ch_1g

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

The following table shows the time taken to provision cloud instances and install database software:

| System | Instance Provisioning | Software Installation | Total Setup Time | Notes |
|--------|----------------------|----------------------|------------------|-------|
| Clickhouse | 140.68s | 32.66s | 173.34s | New infrastructure |
| Exasol | 140.68s | 582.25s | 722.94s | New infrastructure |

**Infrastructure Provisioning:** 140.68s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse had the fastest software installation at 32.66s
- Exasol took 582.25s to install (17.8x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system     |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |      7 |        75.4 |      80   |     10.2 |     74.5 |    102.5 |
| Q01     | exasol     |      7 |        30.2 |      30.1 |      0.3 |     29.6 |     30.5 |
| Q02     | clickhouse |      7 |        59.3 |      60.8 |      2.9 |     58.2 |     65.7 |
| Q02     | exasol     |      7 |        25.6 |      25.6 |      0.5 |     24.7 |     26.1 |
| Q03     | clickhouse |      7 |        87.7 |      89.6 |      4.2 |     86.5 |     96.8 |
| Q03     | exasol     |      7 |        23.7 |      23.7 |      0.3 |     23.3 |     24.1 |
| Q04     | clickhouse |      7 |        66.3 |      66.8 |      2   |     65.7 |     71.3 |
| Q04     | exasol     |      7 |        10.8 |      10.9 |      0.3 |     10.7 |     11.4 |
| Q05     | clickhouse |      7 |       182.8 |     183   |      3.9 |    177.2 |    188.2 |
| Q05     | exasol     |      7 |        22.4 |      22.5 |      0.6 |     21.8 |     23.3 |
| Q06     | clickhouse |      7 |        21.3 |      21.6 |      0.7 |     21.1 |     23.1 |
| Q06     | exasol     |      7 |         7.5 |       7.5 |      0.2 |      7.3 |      7.8 |
| Q07     | clickhouse |      7 |       102.4 |     102.4 |      0.4 |    101.7 |    103.1 |
| Q07     | exasol     |      7 |        21.9 |      22   |      0.5 |     21.4 |     23   |
| Q08     | clickhouse |      7 |       141.4 |     145.2 |      8.5 |    137.1 |    162.8 |
| Q08     | exasol     |      7 |        20.6 |      22.9 |      6.1 |     20   |     36.6 |
| Q09     | clickhouse |      7 |       201.3 |     199.8 |     15.1 |    184   |    223.3 |
| Q09     | exasol     |      7 |        34.2 |      34.8 |      2.2 |     33.6 |     39.8 |
| Q10     | clickhouse |      7 |        95.5 |      95.8 |      2.6 |     91.8 |     98.4 |
| Q10     | exasol     |      7 |        47.7 |      47.5 |      0.7 |     46.3 |     48.2 |
| Q11     | clickhouse |      7 |        37.3 |      37.4 |      0.3 |     37   |     37.8 |
| Q11     | exasol     |      7 |        22.6 |      22.6 |      0.5 |     21.7 |     23.3 |
| Q12     | clickhouse |      7 |        37.5 |      40.2 |      6.8 |     35.9 |     55.3 |
| Q12     | exasol     |      7 |        12.2 |      12.2 |      0.3 |     11.7 |     12.7 |
| Q13     | clickhouse |      7 |       106.3 |     105   |     12.9 |     87.2 |    122.5 |
| Q13     | exasol     |      7 |        38.4 |      38   |      1.1 |     36.5 |     39.6 |
| Q14     | clickhouse |      7 |        29   |      29.7 |      2.8 |     26.3 |     33.7 |
| Q14     | exasol     |      7 |        10.2 |      10.2 |      0.2 |     10   |     10.5 |
| Q15     | clickhouse |      7 |        31.3 |      31.1 |      1.7 |     29.5 |     34.2 |
| Q15     | exasol     |      7 |        20.9 |      20.9 |      0.4 |     20.4 |     21.5 |
| Q16     | clickhouse |      7 |        84   |      83.9 |      1.9 |     81.9 |     87.5 |
| Q16     | exasol     |      7 |        94.3 |      98   |      8.4 |     94   |    116.8 |
| Q17     | clickhouse |      7 |        92.5 |      92.5 |      1.7 |     90.3 |     95.3 |
| Q17     | exasol     |      7 |        12.6 |      12.6 |      0.2 |     12.3 |     12.8 |
| Q18     | clickhouse |      7 |        94.9 |      96.3 |      4.1 |     93.6 |    105.4 |
| Q18     | exasol     |      7 |        28.3 |      28.5 |      0.6 |     27.9 |     29.7 |
| Q19     | clickhouse |      7 |        85.3 |      85.1 |      2.7 |     80.7 |     88.6 |
| Q19     | exasol     |      7 |        11.2 |      11.4 |      0.4 |     10.8 |     11.9 |
| Q20     | clickhouse |      7 |        36.2 |      38.6 |      6.9 |     35.1 |     54.1 |
| Q20     | exasol     |      7 |        22.2 |      22.2 |      0.5 |     21.7 |     22.8 |
| Q21     | clickhouse |      7 |       522.2 |     522.9 |     31.5 |    465.4 |    560.8 |
| Q21     | exasol     |      7 |        24   |      25.9 |      5   |     23.5 |     37.2 |
| Q22     | clickhouse |      7 |        49.5 |      51.6 |      5.7 |     48.8 |     64.5 |
| Q22     | exasol     |      7 |        14.5 |      14.4 |      0.3 |     13.9 |     14.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | clickhouse        | exasol              |          75.4 |            30.2 |    0.4  |      2.5  | True     |
| Q02     | clickhouse        | exasol              |          59.3 |            25.6 |    0.43 |      2.32 | True     |
| Q03     | clickhouse        | exasol              |          87.7 |            23.7 |    0.27 |      3.7  | True     |
| Q04     | clickhouse        | exasol              |          66.3 |            10.8 |    0.16 |      6.14 | True     |
| Q05     | clickhouse        | exasol              |         182.8 |            22.4 |    0.12 |      8.16 | True     |
| Q06     | clickhouse        | exasol              |          21.3 |             7.5 |    0.35 |      2.84 | True     |
| Q07     | clickhouse        | exasol              |         102.4 |            21.9 |    0.21 |      4.68 | True     |
| Q08     | clickhouse        | exasol              |         141.4 |            20.6 |    0.15 |      6.86 | True     |
| Q09     | clickhouse        | exasol              |         201.3 |            34.2 |    0.17 |      5.89 | True     |
| Q10     | clickhouse        | exasol              |          95.5 |            47.7 |    0.5  |      2    | True     |
| Q11     | clickhouse        | exasol              |          37.3 |            22.6 |    0.61 |      1.65 | True     |
| Q12     | clickhouse        | exasol              |          37.5 |            12.2 |    0.33 |      3.07 | True     |
| Q13     | clickhouse        | exasol              |         106.3 |            38.4 |    0.36 |      2.77 | True     |
| Q14     | clickhouse        | exasol              |          29   |            10.2 |    0.35 |      2.84 | True     |
| Q15     | clickhouse        | exasol              |          31.3 |            20.9 |    0.67 |      1.5  | True     |
| Q16     | clickhouse        | exasol              |          84   |            94.3 |    1.12 |      0.89 | False    |
| Q17     | clickhouse        | exasol              |          92.5 |            12.6 |    0.14 |      7.34 | True     |
| Q18     | clickhouse        | exasol              |          94.9 |            28.3 |    0.3  |      3.35 | True     |
| Q19     | clickhouse        | exasol              |          85.3 |            11.2 |    0.13 |      7.62 | True     |
| Q20     | clickhouse        | exasol              |          36.2 |            22.2 |    0.61 |      1.63 | True     |
| Q21     | clickhouse        | exasol              |         522.2 |            24   |    0.05 |     21.76 | True     |
| Q22     | clickhouse        | exasol              |          49.5 |            14.5 |    0.29 |      3.41 | True     |

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

![Runtime Distribution (CDF)](attachments/figures/query_runtime_cdf.png)

*Cumulative distribution function showing the probability that a query completes within a given time. Curves closer to the left indicate better performance.*

**Interactive version:** [View interactive chart](attachments/figures/query_runtime_cdf.html) for interactive exploration.

> **Note:** All visualizations are available as both static PNG images (shown above) and interactive HTML charts (linked). The interactive versions allow you to zoom, pan, and hover for detailed information.

### Key Observations

**clickhouse:**
- Median runtime: 84.9ms
- Average runtime: 102.7ms
- Fastest query: 21.1ms
- Slowest query: 560.8ms

**exasol:**
- Median runtime: 22.3ms
- Average runtime: 25.7ms
- Fastest query: 7.3ms
- Slowest query: 116.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_1g-benchmark.zip`](exa_vs_ch_1g-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 16 logical cores
- **Memory:** 124.4GB RAM
- **Storage:** NVMe SSD recommended for optimal performance
- **OS:** Linux

### Configuration Files

The exact configuration used for this benchmark is available at:
[`attachments/config.yaml`](attachments/config.yaml)

### System Specifications

**Exasol 2025.1.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - dbram: 32g
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Clickhouse 25.9.3.48:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 32g
  - max_threads: 16
  - max_memory_usage: 30000000000


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (results discarded)
- 7 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts