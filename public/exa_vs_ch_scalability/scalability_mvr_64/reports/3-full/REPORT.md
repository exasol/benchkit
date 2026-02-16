# Minimum Viable Resources - 64GB

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-01-19 16:37:21

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 861.0ms median runtime
- clickhouse was 13.7x slower- Tested 220 total query executions across 22 different TPC-H queries
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
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-18

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-180


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.2xlarge
- **Clickhouse Instance:** r6id.2xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.8 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 48GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 48GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 48GiB

# Create raw partition for Exasol (393GB)
sudo parted /dev/nvme1n1 mkpart primary 48GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 48GiB 100%

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
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;SERVER_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=48000
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



#### Clickhouse 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4FAC2AEC4379B8573 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4FAC2AEC4379B8573

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4FAC2AEC4379B8573 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4FAC2AEC4379B8573 /data

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
sudo apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;53066930585&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;15&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;8&lt;/background_schedule_pool_size&gt;
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
            &lt;max_threads&gt;8&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;8000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;4000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;4000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `8.0GB`

**Data Directory:** `/data/clickhouse`




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
unzip scalability_mvr_64-benchmark.zip
cd scalability_mvr_64

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

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2813.4 |      5 |     13185.1 |   12912.8 |   4235.1 |   6336.2 |  17572.3 |
| Q01     | exasol     |    938.9 |      5 |      3775.5 |    3198.2 |   1716   |    948.9 |   5135.1 |
| Q02     | clickhouse |   1077.5 |      5 |     10485.6 |   10666.5 |   1520.5 |   9184.7 |  13158.8 |
| Q02     | exasol     |     63.8 |      5 |       179.9 |     180.9 |     11.5 |    167.8 |    192.7 |
| Q03     | clickhouse |   3354   |      5 |     16781.1 |   14967.4 |   6981.7 |   3038.2 |  21280.1 |
| Q03     | exasol     |    384.7 |      5 |      1311.8 |    1167.6 |    569   |    359.7 |   1731.9 |
| Q04     | clickhouse |   4663.3 |      5 |     17866.9 |   16309.2 |   3499.4 |  12226.4 |  19931.1 |
| Q04     | exasol     |     72.5 |      5 |       317.9 |     302.8 |     95   |    169.7 |    432.6 |
| Q05     | clickhouse |   2761.6 |      5 |     14976.4 |   14731.5 |   1769.4 |  12206.3 |  17082.9 |
| Q05     | exasol     |    292.3 |      5 |      1210.1 |    1233.8 |    177.9 |   1072   |   1506.2 |
| Q06     | clickhouse |    196.8 |      5 |      3225.8 |    3039.5 |    677.8 |   1911.8 |   3687.1 |
| Q06     | exasol     |     47.2 |      5 |       192.5 |     194.9 |    130.3 |     46.6 |    401.3 |
| Q07     | clickhouse |   7808.9 |      5 |     23838.7 |   24982.4 |   4018.5 |  20529   |  30518.7 |
| Q07     | exasol     |    339.4 |      5 |      1509.6 |    1532.2 |    225.1 |   1198.2 |   1785.5 |
| Q08     | clickhouse |   3740.5 |      5 |     18864   |   18870.3 |   1311.8 |  17359.9 |  20726.6 |
| Q08     | exasol     |    101.6 |      5 |       428   |     417.9 |     94.8 |    262.1 |    508.8 |
| Q09     | clickhouse |   2175   |      5 |     11944.9 |   12136.2 |   1698.7 |  10609.9 |  14727.6 |
| Q09     | exasol     |   1183.7 |      5 |      5245.7 |    5185.6 |   1130   |   3499   |   6684.4 |
| Q10     | clickhouse |   5264.9 |      5 |     21171.6 |   22152.1 |   2680.6 |  19906.8 |  26742.7 |
| Q10     | exasol     |    460.1 |      5 |      2263   |    2346   |    392.2 |   1959.9 |   2971.5 |
| Q11     | clickhouse |    654.1 |      5 |      4549.4 |    4614.2 |   1898.9 |   2636.8 |   7620.4 |
| Q11     | exasol     |    110.8 |      5 |       389.9 |     387.3 |     45.3 |    322.3 |    440.4 |
| Q12     | clickhouse |   1781.3 |      5 |      6458.3 |    7434.9 |   1858.1 |   5698   |   9572.8 |
| Q12     | exasol     |     96.4 |      5 |       466.4 |     488.6 |    109.5 |    365.3 |    622.1 |
| Q13     | clickhouse |   2877.8 |      5 |     11800.6 |   10620.7 |   3060.6 |   7218.5 |  13885.5 |
| Q13     | exasol     |    871.3 |      5 |      3592.1 |    3345.7 |   1038.6 |   1539.7 |   4150.8 |
| Q14     | clickhouse |    197.7 |      5 |      2780.8 |    2517.3 |    476.8 |   1756.4 |   2864.9 |
| Q14     | exasol     |     87.3 |      5 |       465.8 |     503.7 |    246.9 |    206   |    891.6 |
| Q15     | clickhouse |    240.3 |      5 |      3941   |    3513.8 |   1143.2 |   1875.8 |   4483.7 |
| Q15     | exasol     |    233.2 |      5 |       922.4 |     923.3 |    146   |    699.5 |   1074.6 |
| Q16     | clickhouse |    625   |      5 |      6218.8 |    5492.6 |   1725.7 |   2777.2 |   6843.4 |
| Q16     | exasol     |    418.9 |      5 |      1406.5 |    1306.5 |    293.9 |    931.7 |   1572.1 |
| Q17     | clickhouse |   1123.5 |      5 |      8588.7 |    9433.7 |   2513.5 |   7072.8 |  12421.3 |
| Q17     | exasol     |     22.5 |      5 |        68.3 |      69.1 |     32.2 |     36.1 |    120.2 |
| Q18     | clickhouse |   3247.1 |      5 |     15526.6 |   15922.6 |   1179.2 |  14860   |  17920.6 |
| Q18     | exasol     |    600.1 |      5 |      2539.5 |    2804.9 |    674.3 |   2274   |   3951.3 |
| Q19     | clickhouse |   5970   |      5 |     24494.9 |   20834.5 |   8459.3 |   5847.2 |  25959   |
| Q19     | exasol     |     37.7 |      5 |       171   |     178.5 |     43.4 |    132.8 |    248.7 |
| Q20     | clickhouse |   1559.7 |      5 |     10375.1 |   10182.3 |   2494   |   7277.5 |  13039   |
| Q20     | exasol     |    236.1 |      5 |       904.2 |     831.8 |    181   |    612.9 |   1004.4 |
| Q21     | clickhouse |   2251.9 |      5 |     12376.2 |   12118.2 |   3318.6 |   7693.4 |  16601.1 |
| Q21     | exasol     |    491.8 |      5 |      2350.6 |    1952.7 |    835   |    496.5 |   2496.5 |
| Q22     | clickhouse |    539.6 |      5 |      4165.7 |    3638.6 |   1817.4 |    581.5 |   5376.1 |
| Q22     | exasol     |    111.6 |      5 |       469.2 |     439.7 |     62.3 |    333.9 |    482   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3775.5 |         13185.1 |    3.49 |      0.29 | False    |
| Q02     | exasol            | clickhouse          |         179.9 |         10485.6 |   58.29 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |        1311.8 |         16781.1 |   12.79 |      0.08 | False    |
| Q04     | exasol            | clickhouse          |         317.9 |         17866.9 |   56.2  |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1210.1 |         14976.4 |   12.38 |      0.08 | False    |
| Q06     | exasol            | clickhouse          |         192.5 |          3225.8 |   16.76 |      0.06 | False    |
| Q07     | exasol            | clickhouse          |        1509.6 |         23838.7 |   15.79 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         428   |         18864   |   44.07 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        5245.7 |         11944.9 |    2.28 |      0.44 | False    |
| Q10     | exasol            | clickhouse          |        2263   |         21171.6 |    9.36 |      0.11 | False    |
| Q11     | exasol            | clickhouse          |         389.9 |          4549.4 |   11.67 |      0.09 | False    |
| Q12     | exasol            | clickhouse          |         466.4 |          6458.3 |   13.85 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3592.1 |         11800.6 |    3.29 |      0.3  | False    |
| Q14     | exasol            | clickhouse          |         465.8 |          2780.8 |    5.97 |      0.17 | False    |
| Q15     | exasol            | clickhouse          |         922.4 |          3941   |    4.27 |      0.23 | False    |
| Q16     | exasol            | clickhouse          |        1406.5 |          6218.8 |    4.42 |      0.23 | False    |
| Q17     | exasol            | clickhouse          |          68.3 |          8588.7 |  125.75 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2539.5 |         15526.6 |    6.11 |      0.16 | False    |
| Q19     | exasol            | clickhouse          |         171   |         24494.9 |  143.25 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         904.2 |         10375.1 |   11.47 |      0.09 | False    |
| Q21     | exasol            | clickhouse          |        2350.6 |         12376.2 |    5.27 |      0.19 | False    |
| Q22     | exasol            | clickhouse          |         469.2 |          4165.7 |    8.88 |      0.11 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 11651.3 | 11872.8 | 2777.2 | 25102.5 |
| 1 | 22 | 12103.3 | 10931.5 | 581.5 | 27542.6 |
| 2 | 22 | 11640.2 | 11945.8 | 1756.4 | 22769.1 |
| 3 | 22 | 11428.3 | 10492.5 | 2845.9 | 30518.7 |
| 4 | 22 | 11606.7 | 12257.7 | 1911.8 | 24494.9 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 10492.5ms
- Slowest stream median: 12257.7ms
- Stream performance variation: 16.8% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 1351.2 | 881.5 | 68.3 | 5245.7 |
| 1 | 22 | 1147.0 | 763.2 | 157.3 | 4205.8 |
| 2 | 22 | 1392.7 | 777.5 | 72.4 | 5300.3 |
| 3 | 22 | 1486.0 | 780.9 | 36.1 | 6684.4 |
| 4 | 22 | 1212.0 | 756.6 | 48.3 | 3895.7 |

**Performance Analysis for Exasol:**
- Fastest stream median: 756.6ms
- Slowest stream median: 881.5ms
- Stream performance variation: 16.5% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams

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
- Median runtime: 861.0ms
- Average runtime: 1317.8ms
- Fastest query: 36.1ms
- Slowest query: 6684.4ms

**clickhouse:**
- Median runtime: 11791.7ms
- Average runtime: 11686.0ms
- Fastest query: 581.5ms
- Slowest query: 30518.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_mvr_64-benchmark.zip`](scalability_mvr_64-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 8 logical cores
- **Memory:** 61.8GB RAM
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

**Clickhouse 25.10.2.65:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 48g
  - max_threads: 8
  - max_memory_usage: 8000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 2000000000


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