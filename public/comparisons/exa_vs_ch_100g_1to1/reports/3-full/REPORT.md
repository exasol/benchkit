# Exasol vs ClickHouse Performance Comparison on TPC-H SF100

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2025-10-31 12:15:42

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 238.1ms median runtime
- clickhouse was 10.7x slower
- Tested 308 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol 2025.1.0

**Software Configuration:**
- **Database:** exasol 2025.1.0
- **Setup method:** installer

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-103

### Clickhouse 25.9.5.21

**Software Configuration:**
- **Database:** clickhouse 25.9.5.21
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-28


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.8xlarge
- **Clickhouse Instance:** r6id.8xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 132GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Create raw partition for Exasol (1637GB)
sudo parted /dev/nvme1n1 mkpart primary 132GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 132GiB 100%

# Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# Create mount point /data/tpch_gen
sudo mkdir -p /data/tpch_gen

# Mount /dev/nvme1n1p1 to /data/tpch_gen
sudo mount /dev/nvme1n1p1 /data/tpch_gen

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
CCC_HOST_DATADISK=/dev/nvme1n1p2
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
- Database RAM: `220g`
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



#### Clickhouse 25.9.5.21 Setup

**Storage Configuration:**
```bash
# Format /dev/nvme1n1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1 to /data
sudo mount /dev/nvme1n1 /data

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
sudo apt-get install -y clickhouse-server=25.9.5.21 clickhouse-client=25.9.5.21

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;212792573952&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;16&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;32&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;32&lt;/background_schedule_pool_size&gt;
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
            &lt;max_threads&gt;32&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;200000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;100000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;100000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `230g`
- Max threads: `32`
- Max memory usage: `200.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 100
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 7
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_100g_1to1-benchmark.zip
cd exa_vs_ch_100g_1to1

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
| Clickhouse | 120.60s | 32.34s | 152.93s | New infrastructure |
| Exasol | 120.60s | 575.00s | 695.59s | New infrastructure |

**Infrastructure Provisioning:** 120.60s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse had the fastest software installation at 32.34s
- Exasol took 575.00s to install (17.8x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2542.8 |      7 |      2527.8 |    2520.5 |     34   |   2460.1 |   2556.8 |
| Q01     | exasol     |    803.5 |      7 |       791   |     793.2 |      5.2 |    789.5 |    804.5 |
| Q02     | clickhouse |   1308.4 |      7 |      1088.3 |    1094.2 |     25.1 |   1071.9 |   1146   |
| Q02     | exasol     |     94   |      7 |        74.8 |      74.8 |      0.6 |     74.2 |     75.6 |
| Q03     | clickhouse |   4527.5 |      7 |      4059.9 |    4070   |    180.4 |   3884.6 |   4396.7 |
| Q03     | exasol     |    326.5 |      7 |       324.7 |     325.1 |      4.9 |    318.3 |    333.1 |
| Q04     | clickhouse |   3266.7 |      7 |      2586.4 |    2617.8 |     84.4 |   2542.8 |   2770.4 |
| Q04     | exasol     |     63.3 |      7 |        60.7 |      60.7 |      0.3 |     60.3 |     61   |
| Q05     | clickhouse |   9544.3 |      7 |      8884.8 |    8866.6 |    117.2 |   8720.3 |   9080.4 |
| Q05     | exasol     |    267.8 |      7 |       203.1 |     204.5 |      3.4 |    202.9 |    212.2 |
| Q06     | clickhouse |    996   |      7 |       164.9 |     166   |      3.2 |    162.6 |    172.1 |
| Q06     | exasol     |     41.9 |      7 |        41.3 |      41.3 |      0.4 |     40.8 |     42   |
| Q07     | clickhouse |   6395.3 |      7 |      4894.5 |    4900.8 |     29.6 |   4876   |   4963.5 |
| Q07     | exasol     |    267.2 |      7 |       265.1 |     265.1 |      1   |    264   |    266.7 |
| Q08     | clickhouse |   7138.8 |      7 |      7908.5 |    7904.9 |    222.2 |   7575.6 |   8175.8 |
| Q08     | exasol     |     74.9 |      7 |        73.7 |      77.9 |     11.6 |     72.6 |    104.2 |
| Q09     | clickhouse |  14236.3 |      7 |     12545.6 |   12998.1 |   1180.2 |  11949.3 |  15509.6 |
| Q09     | exasol     |    943.9 |      7 |       942.8 |     943.2 |      1.7 |    941.2 |    946.5 |
| Q10     | clickhouse |   5456.7 |      7 |      3408.5 |    3431.6 |     90.9 |   3352.5 |   3616.6 |
| Q10     | exasol     |    556   |      7 |       557.4 |     558.5 |      4.5 |    553.5 |    565.1 |
| Q11     | clickhouse |   1168   |      7 |       727.3 |     736.6 |     42.8 |    684.6 |    799.4 |
| Q11     | exasol     |    143.5 |      7 |       144.2 |     145.3 |      4.2 |    140.5 |    153   |
| Q12     | clickhouse |   2507   |      7 |       770.2 |     794.6 |     46.2 |    759.9 |    878.6 |
| Q12     | exasol     |     84.7 |      7 |        82.2 |      82.1 |      0.2 |     81.9 |     82.4 |
| Q13     | clickhouse |   5648.2 |      7 |      5744.7 |    5712.2 |    265.3 |   5378.1 |   6124.7 |
| Q13     | exasol     |    659.6 |      7 |       657.9 |     659.1 |      3.4 |    655.4 |    664   |
| Q14     | clickhouse |    234.5 |      7 |       245.3 |     242.8 |      4.8 |    236.7 |    248   |
| Q14     | exasol     |     94.4 |      7 |        81   |      80.9 |      0.2 |     80.6 |     81.2 |
| Q15     | clickhouse |    410.2 |      7 |       346.4 |     352.6 |     11.2 |    345.7 |    374.5 |
| Q15     | exasol     |    376.1 |      7 |       379.6 |     406.7 |     35.2 |    377.6 |    448.2 |
| Q16     | clickhouse |    538.7 |      7 |       517.5 |     513   |     14.2 |    484.3 |    525.3 |
| Q16     | exasol     |    463.8 |      7 |       457.7 |     458.5 |      6.7 |    451.3 |    472.4 |
| Q17     | clickhouse |   7380.9 |      7 |      5821.7 |    6032.4 |    528.6 |   5580.2 |   6897.6 |
| Q17     | exasol     |     29.3 |      7 |        28   |      27.9 |      0.2 |     27.5 |     28.2 |
| Q18     | clickhouse |   5835.4 |      7 |      5352.2 |    5365.8 |     88.2 |   5289.3 |   5545.5 |
| Q18     | exasol     |    632.4 |      7 |       631.4 |     632.2 |      6.3 |    622.4 |    640.4 |
| Q19     | clickhouse |   2302.7 |      7 |      2207.7 |    2216.2 |     52.6 |   2156.6 |   2310.9 |
| Q19     | exasol     |     25.7 |      7 |        25.6 |      25.6 |      0.2 |     25.2 |     25.7 |
| Q20     | clickhouse |    421.6 |      7 |       390   |     390.4 |      6.4 |    379.2 |    397.9 |
| Q20     | exasol     |    281.6 |      7 |       277.6 |     277.8 |      1.8 |    274.8 |    280.9 |
| Q21     | clickhouse |  48541.1 |      7 |     46707.2 |   46802.5 |    770.3 |  45770.5 |  47984.7 |
| Q21     | exasol     |    384.3 |      7 |       384.5 |     390   |     14.3 |    383.8 |    422.3 |
| Q22     | clickhouse |    596.3 |      7 |       593.9 |     595.8 |     16.6 |    575.7 |    619.4 |
| Q22     | exasol     |     97.2 |      7 |        94.4 |      94.4 |      0.3 |     94.1 |     95   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |         791   |          2527.8 |    3.2  |      0.31 | False    |
| Q02     | exasol            | clickhouse          |          74.8 |          1088.3 |   14.55 |      0.07 | False    |
| Q03     | exasol            | clickhouse          |         324.7 |          4059.9 |   12.5  |      0.08 | False    |
| Q04     | exasol            | clickhouse          |          60.7 |          2586.4 |   42.61 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         203.1 |          8884.8 |   43.75 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |          41.3 |           164.9 |    3.99 |      0.25 | False    |
| Q07     | exasol            | clickhouse          |         265.1 |          4894.5 |   18.46 |      0.05 | False    |
| Q08     | exasol            | clickhouse          |          73.7 |          7908.5 |  107.31 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         942.8 |         12545.6 |   13.31 |      0.08 | False    |
| Q10     | exasol            | clickhouse          |         557.4 |          3408.5 |    6.11 |      0.16 | False    |
| Q11     | exasol            | clickhouse          |         144.2 |           727.3 |    5.04 |      0.2  | False    |
| Q12     | exasol            | clickhouse          |          82.2 |           770.2 |    9.37 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |         657.9 |          5744.7 |    8.73 |      0.11 | False    |
| Q14     | exasol            | clickhouse          |          81   |           245.3 |    3.03 |      0.33 | False    |
| Q15     | exasol            | clickhouse          |         379.6 |           346.4 |    0.91 |      1.1  | True     |
| Q16     | exasol            | clickhouse          |         457.7 |           517.5 |    1.13 |      0.88 | False    |
| Q17     | exasol            | clickhouse          |          28   |          5821.7 |  207.92 |      0    | False    |
| Q18     | exasol            | clickhouse          |         631.4 |          5352.2 |    8.48 |      0.12 | False    |
| Q19     | exasol            | clickhouse          |          25.6 |          2207.7 |   86.24 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         277.6 |           390   |    1.4  |      0.71 | False    |
| Q21     | exasol            | clickhouse          |         384.5 |         46707.2 |  121.48 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          94.4 |           593.9 |    6.29 |      0.16 | False    |


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
- Median runtime: 2546.6ms
- Average runtime: 5378.4ms
- Fastest query: 162.6ms
- Slowest query: 47984.7ms

**exasol:**
- Median runtime: 238.1ms
- Average runtime: 301.1ms
- Fastest query: 25.2ms
- Slowest query: 946.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_100g_1to1-benchmark.zip`](exa_vs_ch_100g_1to1-benchmark.zip)

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

**Exasol 2025.1.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - dbram: 220g
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Clickhouse 25.9.5.21:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 7 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts