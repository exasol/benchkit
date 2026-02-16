# Concurrency Cliff - 15 Streams

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 15:33:26

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 813.3ms median runtime
- clickhouse was 12.6x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 15 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.1.8

**Software Configuration:**
- **Database:** exasol 2025.1.8
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-79

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-164


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.4xlarge
- **Clickhouse Instance:** r6id.4xlarge


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

# Create raw partition for Exasol (836GB)
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
CCC_PLAY_DB_MEM_SIZE=100000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1F27033CD076C35A7 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1F27033CD076C35A7

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1F27033CD076C35A7 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1F27033CD076C35A7 /data

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
    &lt;max_server_memory_usage&gt;106335626854&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;25&lt;/max_concurrent_queries&gt;
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
            &lt;max_memory_usage&gt;5300000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;2650000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;2650000000&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `100g`
- Max threads: `16`
- Max memory usage: `5.3GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 30
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (15 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip scalability_conc_15-benchmark.zip
cd scalability_conc_15

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
| Q01     | clickhouse |   1419   |      5 |     14824   |   12979.6 |   5769.3 |   3325.8 |  18401.7 |
| Q01     | exasol     |    479.5 |      5 |      4689.1 |    5137.5 |   4721.1 |    514.8 |  12946   |
| Q02     | clickhouse |    594.6 |      5 |      9436.7 |   10121.2 |   1673.7 |   8936.1 |  12989.5 |
| Q02     | exasol     |     51.9 |      5 |       245.6 |     223   |     78.4 |     92.4 |    283.5 |
| Q03     | clickhouse |    661   |      5 |      9723.9 |    8838.7 |   2963.2 |   4643.2 |  11863   |
| Q03     | exasol     |    176.1 |      5 |      1092.1 |    1332.3 |    699.7 |    703.7 |   2473.3 |
| Q04     | clickhouse |   2224.4 |      5 |     15662.5 |   16110.5 |   1670.1 |  14795.8 |  18982.7 |
| Q04     | exasol     |     39.7 |      5 |       356.8 |     310.3 |    170.5 |     82   |    513.4 |
| Q05     | clickhouse |    584.5 |      5 |     10330.8 |    9967.4 |    628.9 |   9053.3 |  10477.8 |
| Q05     | exasol     |    166.5 |      5 |      1466.5 |    1483.9 |    130.5 |   1367.6 |   1698.2 |
| Q06     | clickhouse |    103.2 |      5 |      3272.3 |    2604.7 |   1436.9 |    511.4 |   3813.6 |
| Q06     | exasol     |     25.6 |      5 |       265.1 |     230   |    109.7 |     82.6 |    350.9 |
| Q07     | clickhouse |    594.8 |      5 |      9981.2 |    8664   |   4067.3 |   1581.8 |  11322.7 |
| Q07     | exasol     |    150.6 |      5 |      1780.6 |    1663.7 |    479   |    916.1 |   2218.1 |
| Q08     | clickhouse |    919   |      5 |     14526.7 |   14372.3 |    961.4 |  13231.2 |  15543.6 |
| Q08     | exasol     |     51   |      5 |       337.2 |     415.1 |    216.3 |    159.2 |    686.5 |
| Q09     | clickhouse |    668.6 |      5 |     10611.8 |   10954.3 |   1313.6 |   9621.8 |  12829.3 |
| Q09     | exasol     |    548.2 |      5 |      5784.2 |    6020.8 |    786.6 |   5296.1 |   7156.5 |
| Q10     | clickhouse |    848.4 |      5 |     13751.3 |   13128.7 |   1969.8 |  11106.8 |  15696.8 |
| Q10     | exasol     |    279   |      5 |      3064   |    2991.1 |    125.4 |   2802.5 |   3084.1 |
| Q11     | clickhouse |    300.5 |      5 |      7452.8 |    8058.5 |   1607.3 |   6978   |  10833.2 |
| Q11     | exasol     |     92.6 |      5 |       533.6 |     518.6 |     47.9 |    462.2 |    574.3 |
| Q12     | clickhouse |    566.4 |      5 |     10204.8 |   10455.5 |    693.7 |   9653.6 |  11428.2 |
| Q12     | exasol     |     53.1 |      5 |       707   |     702.9 |     89.5 |    582.5 |    832   |
| Q13     | clickhouse |   1764.7 |      5 |     15598.8 |   14154.4 |   4939.5 |   5653.3 |  17717.4 |
| Q13     | exasol     |    379.4 |      5 |      3959.6 |    3760.2 |   1502.2 |   1712.5 |   5529.2 |
| Q14     | clickhouse |    107   |      5 |      3139.4 |    3183.9 |    374.3 |   2706.4 |   3717.6 |
| Q14     | exasol     |     46.8 |      5 |       531.8 |     574.9 |    151.9 |    412.6 |    793.5 |
| Q15     | clickhouse |    168.9 |      5 |      3458.1 |    3492.2 |    623   |   2657.1 |   4224.1 |
| Q15     | exasol     |    157.1 |      5 |      1484   |    1340.3 |    296.2 |    888.6 |   1576.8 |
| Q16     | clickhouse |    363.6 |      5 |      6661.7 |    6441.1 |   1814.7 |   4498.8 |   8349.3 |
| Q16     | exasol     |    302.5 |      5 |      2291.7 |    1798.4 |    970.9 |    735.6 |   2861.3 |
| Q17     | clickhouse |    556.2 |      5 |      9768.9 |    9708.2 |   2161   |   6310.5 |  12142.1 |
| Q17     | exasol     |     17.4 |      5 |       120.5 |     112.5 |     24.2 |     76.8 |    139.2 |
| Q18     | clickhouse |    664.3 |      5 |     11617.6 |   11681.1 |   2460.8 |   8626.6 |  15436.7 |
| Q18     | exasol     |    321.5 |      5 |      3914.2 |    3640   |   1036.2 |   1840.8 |   4408.7 |
| Q19     | clickhouse |   2928.3 |      5 |     25347.6 |   21840.8 |   8379.1 |   6914.8 |  26380.7 |
| Q19     | exasol     |     18.1 |      5 |       191.1 |     173.6 |     50.7 |    113.1 |    237.4 |
| Q20     | clickhouse |    785.7 |      5 |     10928.8 |    9961.6 |   3508.5 |   5485.3 |  14591.3 |
| Q20     | exasol     |    194.9 |      5 |       778   |    1013.1 |    379.6 |    713.7 |   1499.6 |
| Q21     | clickhouse |    796.4 |      5 |     11676   |   12499.6 |   1895.6 |  10623.3 |  14792   |
| Q21     | exasol     |    226.8 |      5 |      1810.6 |    1800   |    585.6 |   1187.4 |   2619.1 |
| Q22     | clickhouse |    286.2 |      5 |      7371.3 |    7259   |   1082.9 |   5714.5 |   8756.7 |
| Q22     | exasol     |     62.4 |      5 |       600   |     522.1 |    301.5 |    170.8 |    853.4 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        4689.1 |         14824   |    3.16 |      0.32 | False    |
| Q02     | exasol            | clickhouse          |         245.6 |          9436.7 |   38.42 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        1092.1 |          9723.9 |    8.9  |      0.11 | False    |
| Q04     | exasol            | clickhouse          |         356.8 |         15662.5 |   43.9  |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1466.5 |         10330.8 |    7.04 |      0.14 | False    |
| Q06     | exasol            | clickhouse          |         265.1 |          3272.3 |   12.34 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        1780.6 |          9981.2 |    5.61 |      0.18 | False    |
| Q08     | exasol            | clickhouse          |         337.2 |         14526.7 |   43.08 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        5784.2 |         10611.8 |    1.83 |      0.55 | False    |
| Q10     | exasol            | clickhouse          |        3064   |         13751.3 |    4.49 |      0.22 | False    |
| Q11     | exasol            | clickhouse          |         533.6 |          7452.8 |   13.97 |      0.07 | False    |
| Q12     | exasol            | clickhouse          |         707   |         10204.8 |   14.43 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3959.6 |         15598.8 |    3.94 |      0.25 | False    |
| Q14     | exasol            | clickhouse          |         531.8 |          3139.4 |    5.9  |      0.17 | False    |
| Q15     | exasol            | clickhouse          |        1484   |          3458.1 |    2.33 |      0.43 | False    |
| Q16     | exasol            | clickhouse          |        2291.7 |          6661.7 |    2.91 |      0.34 | False    |
| Q17     | exasol            | clickhouse          |         120.5 |          9768.9 |   81.07 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3914.2 |         11617.6 |    2.97 |      0.34 | False    |
| Q19     | exasol            | clickhouse          |         191.1 |         25347.6 |  132.64 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         778   |         10928.8 |   14.05 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1810.6 |         11676   |    6.45 |      0.16 | False    |
| Q22     | exasol            | clickhouse          |         600   |          7371.3 |   12.29 |      0.08 | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 8016.1 | 7818.5 | 2706.4 | 14526.7 |
| 1 | 8 | 10637.2 | 9648.8 | 3027.3 | 18982.7 |
| 10 | 7 | 11704.8 | 10928.8 | 2657.1 | 25347.6 |
| 11 | 7 | 11360.2 | 9981.2 | 4224.1 | 26140.7 |
| 12 | 7 | 11447.1 | 10823.8 | 8349.3 | 15436.7 |
| 13 | 7 | 10749.9 | 10611.8 | 1726.6 | 17391.8 |
| 14 | 7 | 11951.1 | 13579.1 | 511.4 | 26380.7 |
| 2 | 8 | 10024.7 | 9625.6 | 3325.8 | 15543.6 |
| 3 | 8 | 9818.3 | 9629.0 | 3328.7 | 15638.5 |
| 4 | 8 | 10119.7 | 10243.4 | 6310.5 | 14980.9 |
| 5 | 7 | 11323.5 | 11172.1 | 4660.8 | 14795.8 |
| 6 | 7 | 10952.6 | 11106.8 | 3458.1 | 15696.8 |
| 7 | 7 | 9451.6 | 8936.1 | 3139.4 | 24420.1 |
| 8 | 7 | 10422.8 | 10792.3 | 4498.8 | 14792.0 |
| 9 | 7 | 6844.8 | 7371.3 | 3272.3 | 11900.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7371.3ms
- Slowest stream median: 13579.1ms
- Stream performance variation: 84.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 1384.8 | 627.1 | 265.1 | 4408.7 |
| 1 | 8 | 1527.4 | 619.8 | 92.4 | 4689.1 |
| 10 | 7 | 1428.9 | 888.6 | 125.1 | 5529.2 |
| 11 | 7 | 1054.1 | 853.4 | 237.4 | 2218.1 |
| 12 | 7 | 2058.3 | 1834.3 | 82.0 | 5784.2 |
| 13 | 7 | 2014.0 | 1712.5 | 82.6 | 5296.1 |
| 14 | 7 | 1751.3 | 713.7 | 113.1 | 4965.4 |
| 2 | 8 | 1921.2 | 275.2 | 120.5 | 12946.0 |
| 3 | 8 | 1772.6 | 805.0 | 462.2 | 6476.0 |
| 4 | 8 | 1250.5 | 652.2 | 139.2 | 3064.0 |
| 5 | 7 | 2043.9 | 1187.4 | 198.3 | 5391.0 |
| 6 | 7 | 1543.4 | 1191.8 | 356.8 | 2921.5 |
| 7 | 7 | 1250.8 | 793.5 | 131.3 | 4247.9 |
| 8 | 7 | 1931.7 | 1302.8 | 76.8 | 7156.5 |
| 9 | 7 | 1490.5 | 1484.0 | 298.3 | 3914.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 275.2ms
- Slowest stream median: 1834.3ms
- Stream performance variation: 566.4% difference between fastest and slowest streams
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
- Median runtime: 813.3ms
- Average runtime: 1625.6ms
- Fastest query: 76.8ms
- Slowest query: 12946.0ms

**clickhouse:**
- Median runtime: 10267.8ms
- Average runtime: 10294.4ms
- Fastest query: 511.4ms
- Slowest query: 26380.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_conc_15-benchmark.zip`](scalability_conc_15-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 16 logical cores
- **Memory:** 123.8GB RAM
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
  - memory_limit: 100g
  - max_threads: 16
  - max_memory_usage: 5300000000
  - max_bytes_before_external_group_by: 2650000000
  - max_bytes_before_external_sort: 2650000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 1500000000


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 15 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts