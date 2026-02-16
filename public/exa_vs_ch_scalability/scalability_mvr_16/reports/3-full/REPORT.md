# Minimum Viable Resources - 16GB

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-19 15:08:58

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 3035.7ms median runtime
- clickhouse was 4.9x slower- Tested 220 total query executions across 22 different TPC-H queries
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
- **Hostname:** ip-10-0-1-121

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM
- **Hostname:** ip-10-0-1-120


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.large
- **Clickhouse Instance:** r6id.large


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

# Create raw partition for Exasol (61GB)
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



#### Clickhouse 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS258BF695E953E5141 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS258BF695E953E5141

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS258BF695E953E5141 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS258BF695E953E5141 /data

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
    &lt;max_server_memory_usage&gt;13175796531&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;15&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
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
            &lt;max_threads&gt;2&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;2000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;1000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;1000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `12g`
- Max threads: `2`
- Max memory usage: `2.0GB`

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
unzip scalability_mvr_16-benchmark.zip
cd scalability_mvr_16

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
| Q01     | clickhouse |  11976.7 |      5 |     51243.4 |   49097.9 |   9514.1 |  32750.1 |  56868.3 |
| Q01     | exasol     |   3754.5 |      5 |     15961.9 |   16693.3 |   6794   |   7452.6 |  24234.1 |
| Q02     | clickhouse |   3400.1 |      5 |     18452.5 |   19233.9 |   2003.3 |  17117.8 |  21781.7 |
| Q02     | exasol     |     98.5 |      5 |       530.3 |     474.1 |    226.1 |    109.4 |    720.4 |
| Q03     | clickhouse |   2734.6 |      5 |     14462.7 |   13710.3 |   3851.6 |   8833.1 |  18344.6 |
| Q03     | exasol     |   1293.2 |      5 |      2785.9 |    7400.9 |   7844.1 |   1265.8 |  17887.6 |
| Q04     | clickhouse |   4546.9 |      5 |     23284.1 |   23406.1 |   3071.9 |  18841.8 |  27003.8 |
| Q04     | exasol     |    246.5 |      5 |      1899   |    2177.5 |   1172.6 |    866.5 |   3416   |
| Q05     | clickhouse |   2434.3 |      5 |     13128.4 |   13173.1 |   1024.6 |  11601.8 |  14259.9 |
| Q05     | exasol     |   1021.8 |      5 |      4141.5 |    5514.8 |   4222.6 |    968.8 |  11723.2 |
| Q06     | clickhouse |    930.6 |      5 |      4839.6 |    4712.5 |   1387.5 |   2812.5 |   6687.8 |
| Q06     | exasol     |    159.1 |      5 |      1001.4 |     838.7 |    599.2 |    158.9 |   1586.3 |
| Q07     | clickhouse |   1904.6 |      5 |     11284.1 |   11977.6 |   2589.4 |   9075.6 |  15999.5 |
| Q07     | exasol     |   1298.3 |      5 |      7514.9 |    6932.8 |   2057.2 |   4411.7 |   9489.7 |
| Q08     | clickhouse |   1456.9 |      5 |      8505.8 |    8452.3 |   2513.5 |   4514.1 |  11272.7 |
| Q08     | exasol     |    303.3 |      5 |      1182.4 |    1395.2 |    964.5 |    339.8 |   2965.5 |
| Q09     | clickhouse |   1502.9 |      5 |     12024.4 |   11720.3 |   2020.6 |   8994.5 |  14151   |
| Q09     | exasol     |   4677.4 |      5 |     16913.4 |   16092   |   4495   |   8893.3 |  21005   |
| Q10     | clickhouse |   3727.6 |      5 |     16824.2 |   17216.9 |   1976.5 |  15219.1 |  20280.6 |
| Q10     | exasol     |   1346.1 |      5 |      8590.5 |    9472.9 |   3208.7 |   5334.1 |  12992.7 |
| Q11     | clickhouse |   2679.2 |      5 |     13737.5 |   16889.2 |   6819.5 |  10875.3 |  27802.1 |
| Q11     | exasol     |    228.8 |      5 |      1043.9 |    1123   |    577.4 |    250.5 |   1677.8 |
| Q12     | clickhouse |   1996.6 |      5 |     10549.9 |   10954.6 |   2046   |   8816.9 |  13291.9 |
| Q12     | exasol     |    334.5 |      5 |      2738.6 |    2596.8 |    638.9 |   1899.5 |   3415   |
| Q13     | clickhouse |  11121.4 |      5 |     53894.5 |   53362.8 |   3428.1 |  49610.1 |  57795.3 |
| Q13     | exasol     |   3504.4 |      5 |     14503.1 |   28637.2 |  36145   |   7780.4 |  93092.8 |
| Q14     | clickhouse |    701.2 |      5 |      4736.4 |    4376   |   1142.4 |   2992.7 |   5663   |
| Q14     | exasol     |    319.4 |      5 |      2945.2 |    2415.1 |    945.5 |   1079   |   3191.1 |
| Q15     | clickhouse |    613.8 |      5 |      5745.8 |    4811.3 |   1527.5 |   2826   |   6078.1 |
| Q15     | exasol     |    656.2 |      5 |      2968   |    2512.2 |   1219.8 |    658.1 |   3802.8 |
| Q16     | clickhouse |   3054.6 |      5 |     17329.2 |   16832.8 |   2329.3 |  13777.1 |  19643.6 |
| Q16     | exasol     |   1115.1 |      5 |      5522.3 |    4436.6 |   2218.3 |   1074.2 |   6531   |
| Q17     | clickhouse |   5928   |      5 |     27526.2 |   28021.7 |   3833   |  24189   |  34362   |
| Q17     | exasol     |     37.6 |      5 |       343.1 |     348.5 |    114.1 |    194   |    461.9 |
| Q18     | clickhouse |   3748   |      5 |     18195   |   18693.2 |   3454.1 |  15070.8 |  23907.7 |
| Q18     | exasol     |   2018.2 |      5 |      9178   |    8988.2 |   3898   |   4461.1 |  14171.9 |
| Q19     | clickhouse |  24598   |      5 |    113511   |   99030.5 |  39204.3 |  29294.4 | 122750   |
| Q19     | exasol     |     96.4 |      5 |       978.7 |     905.5 |    522.9 |    174   |   1544.5 |
| Q20     | clickhouse |   6517.9 |      5 |     35412.8 |   34063.6 |   3523.4 |  27904.1 |  36447.9 |
| Q20     | exasol     |    655.1 |      5 |      5317.5 |    4740.6 |   1857.1 |   2102.8 |   6702.7 |
| Q21     | clickhouse |   1880   |      5 |     10112.2 |    9834.9 |   1031.1 |   8393.9 |  11173.6 |
| Q21     | exasol     |   2006   |      5 |      7895.2 |    8015.1 |   4974.3 |   1911.2 |  14424.4 |
| Q22     | clickhouse |   1943.9 |      5 |     12295.4 |   11746.2 |   4101.3 |   6778.2 |  17741.9 |
| Q22     | exasol     |    416   |      5 |      1898.2 |    2136.6 |    469.9 |   1726   |   2886.9 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |       15961.9 |         51243.4 |    3.21 |      0.31 | False    |
| Q02     | exasol            | clickhouse          |         530.3 |         18452.5 |   34.8  |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        2785.9 |         14462.7 |    5.19 |      0.19 | False    |
| Q04     | exasol            | clickhouse          |        1899   |         23284.1 |   12.26 |      0.08 | False    |
| Q05     | exasol            | clickhouse          |        4141.5 |         13128.4 |    3.17 |      0.32 | False    |
| Q06     | exasol            | clickhouse          |        1001.4 |          4839.6 |    4.83 |      0.21 | False    |
| Q07     | exasol            | clickhouse          |        7514.9 |         11284.1 |    1.5  |      0.67 | False    |
| Q08     | exasol            | clickhouse          |        1182.4 |          8505.8 |    7.19 |      0.14 | False    |
| Q09     | exasol            | clickhouse          |       16913.4 |         12024.4 |    0.71 |      1.41 | True     |
| Q10     | exasol            | clickhouse          |        8590.5 |         16824.2 |    1.96 |      0.51 | False    |
| Q11     | exasol            | clickhouse          |        1043.9 |         13737.5 |   13.16 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |        2738.6 |         10549.9 |    3.85 |      0.26 | False    |
| Q13     | exasol            | clickhouse          |       14503.1 |         53894.5 |    3.72 |      0.27 | False    |
| Q14     | exasol            | clickhouse          |        2945.2 |          4736.4 |    1.61 |      0.62 | False    |
| Q15     | exasol            | clickhouse          |        2968   |          5745.8 |    1.94 |      0.52 | False    |
| Q16     | exasol            | clickhouse          |        5522.3 |         17329.2 |    3.14 |      0.32 | False    |
| Q17     | exasol            | clickhouse          |         343.1 |         27526.2 |   80.23 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        9178   |         18195   |    1.98 |      0.5  | False    |
| Q19     | exasol            | clickhouse          |         978.7 |        113511   |  115.98 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        5317.5 |         35412.8 |    6.66 |      0.15 | False    |
| Q21     | exasol            | clickhouse          |        7895.2 |         10112.2 |    1.28 |      0.78 | False    |
| Q22     | exasol            | clickhouse          |        1898.2 |         12295.4 |    6.48 |      0.15 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 22404.9 | 14685.0 | 2812.5 | 113511.3 |
| 1 | 22 | 23648.0 | 16880.2 | 3382.2 | 112039.3 |
| 2 | 22 | 22692.8 | 16726.3 | 2992.7 | 122749.8 |
| 3 | 22 | 18940.6 | 12953.2 | 4839.6 | 57795.3 |
| 4 | 22 | 21704.0 | 13016.5 | 4335.0 | 117557.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 12953.2ms
- Slowest stream median: 16880.2ms
- Stream performance variation: 30.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 7240.0 | 1616.0 | 109.4 | 93092.8 |
| 1 | 22 | 4945.9 | 3041.0 | 720.4 | 22318.6 |
| 2 | 22 | 5736.1 | 2744.6 | 343.1 | 17887.6 |
| 3 | 22 | 6677.9 | 4426.9 | 194.0 | 21005.0 |
| 4 | 22 | 5819.9 | 3155.3 | 287.3 | 24234.1 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1616.0ms
- Slowest stream median: 4426.9ms
- Stream performance variation: 174.0% difference between fastest and slowest streams
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
- Median runtime: 3035.7ms
- Average runtime: 6084.0ms
- Fastest query: 109.4ms
- Slowest query: 93092.8ms

**clickhouse:**
- Median runtime: 14766.8ms
- Average runtime: 21878.1ms
- Fastest query: 2812.5ms
- Slowest query: 122749.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_mvr_16-benchmark.zip`](scalability_mvr_16-benchmark.zip)

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

**Clickhouse 25.10.2.65:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 12g
  - max_threads: 2
  - max_memory_usage: 2000000000
  - max_bytes_before_external_group_by: 1000000000
  - max_bytes_before_external_sort: 1000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 500000000


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