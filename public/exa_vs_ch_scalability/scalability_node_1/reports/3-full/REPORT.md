# Node Scaling - 1 Node (32GB)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-19 16:08:07

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 1520.7ms median runtime
- clickhouse was 8.2x slower- Tested 220 total query executions across 22 different TPC-H queries
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
- **Hostname:** ip-10-0-1-208

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-242


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.xlarge
- **Clickhouse Instance:** r6id.xlarge


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
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;SERVER_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=24000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS20821D897AC3CAEC9 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS20821D897AC3CAEC9

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS20821D897AC3CAEC9 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS20821D897AC3CAEC9 /data

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
    &lt;max_server_memory_usage&gt;26472841216&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;15&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;4&lt;/background_schedule_pool_size&gt;
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
            &lt;max_threads&gt;4&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;4000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;2000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;2000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `24g`
- Max threads: `4`
- Max memory usage: `4.0GB`

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
unzip scalability_node_1-benchmark.zip
cd scalability_node_1

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
| Q01     | clickhouse |   5625.6 |      5 |     20651.9 |   20410.7 |   4177   |  16781.9 |  26997.8 |
| Q01     | exasol     |   1893.6 |      5 |      7676.2 |    6922.5 |   3112.7 |   3105.4 |  10689   |
| Q02     | clickhouse |   2326   |      5 |     11944.5 |   12361.8 |   2300.3 |  10186.6 |  16140.6 |
| Q02     | exasol     |     81.8 |      5 |       342.8 |     644.5 |    744.3 |    234.8 |   1969.1 |
| Q03     | clickhouse |   2821.2 |      5 |     13385.9 |   12357.5 |   4452.9 |   5305.5 |  17257.5 |
| Q03     | exasol     |    707.7 |      5 |      3386.3 |    2821.3 |   1699.9 |    686.2 |   4433.9 |
| Q04     | clickhouse |   4699   |      5 |     23112   |   23120.1 |   2980.7 |  19978.7 |  27705.5 |
| Q04     | exasol     |    131.7 |      5 |       638   |     617.5 |    216.4 |    260.5 |    807   |
| Q05     | clickhouse |   2433.8 |      5 |     12482.1 |   13348.7 |   1588.6 |  11913.2 |  15695.9 |
| Q05     | exasol     |    558.2 |      5 |      2413.6 |    2482   |    240.8 |   2291.3 |   2896.8 |
| Q06     | clickhouse |    345.4 |      5 |      3389.3 |    3481.6 |    999.8 |   2227.8 |   4497.2 |
| Q06     | exasol     |     87.1 |      5 |       390.4 |     378.4 |    303.4 |     85.4 |    862.2 |
| Q07     | clickhouse |   1814.5 |      5 |     10736.3 |   11918.6 |   2484.5 |   9206.8 |  14691.6 |
| Q07     | exasol     |    694.7 |      5 |      3532.8 |    4900.4 |   3362.9 |   2832.3 |  10870.4 |
| Q08     | clickhouse |   1584.4 |      5 |     11338.7 |   10436.5 |   2445.9 |   6457.8 |  12940.6 |
| Q08     | exasol     |    165.5 |      5 |       844.4 |    1148   |    993.9 |    336.9 |   2882.6 |
| Q09     | clickhouse |   1903   |      5 |     12932.6 |   13068   |   3204.9 |  10489.4 |  18386.8 |
| Q09     | exasol     |   2510.2 |      5 |     12093.8 |   13594.1 |   3325.1 |  11658.7 |  19497.1 |
| Q10     | clickhouse |   3088.5 |      5 |     16809.9 |   17621.9 |   2743.4 |  14845.1 |  22079.6 |
| Q10     | exasol     |    787.7 |      5 |      3327.4 |    3355.2 |    447.1 |   2860.9 |   3995.2 |
| Q11     | clickhouse |   1397.3 |      5 |     10898.1 |   10109.6 |   2283.7 |   6065.8 |  11645.1 |
| Q11     | exasol     |    149.9 |      5 |       738.8 |     693.8 |    131.1 |    554.7 |    855.3 |
| Q12     | clickhouse |   1903.6 |      5 |      8844.4 |   11000.5 |   3802.2 |   8031.1 |  16325.3 |
| Q12     | exasol     |    178.7 |      5 |      1050.9 |    1170.5 |    415.7 |    732.5 |   1831   |
| Q13     | clickhouse |   4541   |      5 |     18824.6 |   20782   |   4074.1 |  17347.2 |  26533.8 |
| Q13     | exasol     |   1827.8 |      5 |      7831.7 |    6887.3 |   1955.9 |   4101.1 |   8558.8 |
| Q14     | clickhouse |    349.2 |      5 |      4107.9 |    3569.7 |   1167.1 |   2171   |   4760.2 |
| Q14     | exasol     |    175.4 |      5 |      1013.9 |     957.3 |    162.5 |    673.9 |   1069.1 |
| Q15     | clickhouse |    361.4 |      5 |      4068.1 |    4078.3 |    489   |   3317   |   4615.2 |
| Q15     | exasol     |    388   |      5 |      1505.9 |    2140.3 |   1651.2 |   1186.4 |   5084.4 |
| Q16     | clickhouse |   1175   |      5 |      8651.8 |    9040.3 |   1989.2 |   7584   |  12474.2 |
| Q16     | exasol     |    699   |      5 |      2698.3 |    3292.2 |   1766   |   1379.7 |   6112.5 |
| Q17     | clickhouse |   2113.3 |      5 |     12737.2 |   13181.2 |   1060.2 |  12533.6 |  15049.9 |
| Q17     | exasol     |     28.2 |      5 |       112.6 |     132.2 |     45.3 |     92.3 |    197.2 |
| Q18     | clickhouse |   3534.3 |      5 |     15750   |   16495.4 |   1473.7 |  15654.8 |  19101.6 |
| Q18     | exasol     |   1125.4 |      5 |      4730.9 |    4657.1 |    380.5 |   4154.3 |   5147   |
| Q19     | clickhouse |  11806.1 |      5 |     42695.6 |   36737.5 |  14097.5 |  11699.3 |  45535.4 |
| Q19     | exasol     |     53   |      5 |       394.8 |     371.2 |     74.3 |    290.5 |    465.9 |
| Q20     | clickhouse |   2758.1 |      5 |     13505.7 |   13014.1 |   2453.6 |   9168.7 |  15896.9 |
| Q20     | exasol     |    429.3 |      5 |      1683.7 |    1644.5 |    472.8 |    912.6 |   2107.5 |
| Q21     | clickhouse |   1882.4 |      5 |     11051.5 |   11286.4 |   2076.2 |   9066   |  14678.4 |
| Q21     | exasol     |   1063.3 |      5 |      5745.1 |    5235.4 |   2516.1 |   1014.6 |   7598.5 |
| Q22     | clickhouse |    966.7 |      5 |     10009.9 |    8496.3 |   4579.4 |    966.2 |  12793.2 |
| Q22     | exasol     |    215.2 |      5 |       898.3 |    1308.2 |    976.9 |    828.7 |   3054.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        7676.2 |         20651.9 |    2.69 |      0.37 | False    |
| Q02     | exasol            | clickhouse          |         342.8 |         11944.5 |   34.84 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        3386.3 |         13385.9 |    3.95 |      0.25 | False    |
| Q04     | exasol            | clickhouse          |         638   |         23112   |   36.23 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2413.6 |         12482.1 |    5.17 |      0.19 | False    |
| Q06     | exasol            | clickhouse          |         390.4 |          3389.3 |    8.68 |      0.12 | False    |
| Q07     | exasol            | clickhouse          |        3532.8 |         10736.3 |    3.04 |      0.33 | False    |
| Q08     | exasol            | clickhouse          |         844.4 |         11338.7 |   13.43 |      0.07 | False    |
| Q09     | exasol            | clickhouse          |       12093.8 |         12932.6 |    1.07 |      0.94 | False    |
| Q10     | exasol            | clickhouse          |        3327.4 |         16809.9 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse          |         738.8 |         10898.1 |   14.75 |      0.07 | False    |
| Q12     | exasol            | clickhouse          |        1050.9 |          8844.4 |    8.42 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |        7831.7 |         18824.6 |    2.4  |      0.42 | False    |
| Q14     | exasol            | clickhouse          |        1013.9 |          4107.9 |    4.05 |      0.25 | False    |
| Q15     | exasol            | clickhouse          |        1505.9 |          4068.1 |    2.7  |      0.37 | False    |
| Q16     | exasol            | clickhouse          |        2698.3 |          8651.8 |    3.21 |      0.31 | False    |
| Q17     | exasol            | clickhouse          |         112.6 |         12737.2 |  113.12 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        4730.9 |         15750   |    3.33 |      0.3  | False    |
| Q19     | exasol            | clickhouse          |         394.8 |         42695.6 |  108.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        1683.7 |         13505.7 |    8.02 |      0.12 | False    |
| Q21     | exasol            | clickhouse          |        5745.1 |         11051.5 |    1.92 |      0.52 | False    |
| Q22     | exasol            | clickhouse          |         898.3 |         10009.9 |   11.14 |      0.09 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 13649.8 | 12004.1 | 4497.2 | 45535.4 |
| 1 | 22 | 14327.0 | 11413.2 | 966.2 | 42695.6 |
| 2 | 22 | 13680.1 | 12740.5 | 2171.0 | 42948.1 |
| 3 | 22 | 12551.8 | 12503.9 | 3389.3 | 26533.8 |
| 4 | 22 | 13045.1 | 12292.9 | 2227.8 | 40808.9 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 11413.2ms
- Slowest stream median: 12740.5ms
- Stream performance variation: 11.6% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 3180.1 | 1375.8 | 112.6 | 19497.1 |
| 1 | 22 | 2643.3 | 1757.3 | 290.5 | 10689.0 |
| 2 | 22 | 3002.0 | 1227.8 | 197.2 | 11948.0 |
| 3 | 22 | 3271.1 | 1741.3 | 85.4 | 12773.0 |
| 4 | 22 | 2756.7 | 1934.5 | 92.3 | 8558.8 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1227.8ms
- Slowest stream median: 1934.5ms
- Stream performance variation: 57.6% difference between fastest and slowest streams
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
- Median runtime: 1520.7ms
- Average runtime: 2970.6ms
- Fastest query: 85.4ms
- Slowest query: 19497.1ms

**clickhouse:**
- Median runtime: 12507.9ms
- Average runtime: 13450.8ms
- Fastest query: 966.2ms
- Slowest query: 45535.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_node_1-benchmark.zip`](scalability_node_1-benchmark.zip)

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

**Clickhouse 25.10.2.65:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 24g
  - max_threads: 4
  - max_memory_usage: 4000000000
  - max_bytes_before_external_group_by: 2000000000
  - max_bytes_before_external_sort: 2000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 1000000000


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