# Concurrency Cliff - 10 Streams

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 14:15:56

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 497.8ms median runtime
- clickhouse was 18.2x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 10 concurrent streams (randomized distribution)

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS247AF616BB87B41E1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS247AF616BB87B41E1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS247AF616BB87B41E1 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS247AF616BB87B41E1 /data

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
    &lt;max_server_memory_usage&gt;106335639961&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;20&lt;/max_concurrent_queries&gt;
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
- Memory limit: `100g`
- Max threads: `16`
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
- **Execution mode:** Multiuser (10 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip scalability_conc_10-benchmark.zip
cd scalability_conc_10

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
| Q01     | clickhouse |   1423.3 |      5 |     12533.4 |   10749.9 |   4612.8 |   3277.9 |  15449.5 |
| Q01     | exasol     |    477.1 |      5 |      3497.5 |    3319.8 |   1072.6 |   1833.6 |   4771.5 |
| Q02     | clickhouse |    600.8 |      5 |      7882.2 |    8343   |   1091.3 |   7058.8 |   9786.6 |
| Q02     | exasol     |     53.1 |      5 |       177.3 |     167.8 |     57.9 |     70.7 |    223.3 |
| Q03     | clickhouse |   1129.2 |      5 |      9010.6 |   11416.2 |   4125.2 |   7489.3 |  15934.4 |
| Q03     | exasol     |    189.5 |      5 |       768.3 |     805.3 |    501.5 |    243.4 |   1375   |
| Q04     | clickhouse |   4009   |      5 |     14696.4 |   14423.9 |   2233.1 |  11208.8 |  17330.6 |
| Q04     | exasol     |     39.7 |      5 |       298   |     244.7 |    120.6 |     68.1 |    368.6 |
| Q05     | clickhouse |    945.6 |      5 |     13852.7 |   14316.6 |   1829.7 |  11804.4 |  16640   |
| Q05     | exasol     |    164.8 |      5 |       986.5 |     993.6 |     45.5 |    941.3 |   1067   |
| Q06     | clickhouse |    111   |      5 |      2306.1 |    2326.4 |    462.8 |   1925.7 |   3081.3 |
| Q06     | exasol     |     25.8 |      5 |       112.8 |     134.6 |     61   |     71.4 |    212.2 |
| Q07     | clickhouse |   4223.1 |      5 |     24615.6 |   23178.3 |   4143.5 |  16799.4 |  27651.8 |
| Q07     | exasol     |    152.2 |      5 |      1382.6 |    1271.7 |    309.6 |    725   |   1462.2 |
| Q08     | clickhouse |   1745.8 |      5 |     14625.9 |   15329.8 |   2824   |  11466.5 |  18757   |
| Q08     | exasol     |     70.2 |      5 |       362.7 |     364.8 |    112.7 |    191.7 |    467.3 |
| Q09     | clickhouse |   1062.3 |      5 |     12982.6 |   11908.2 |   1692   |  10050.2 |  13347.8 |
| Q09     | exasol     |    548.5 |      5 |      4049.4 |    4087.6 |    489   |   3545.3 |   4696.7 |
| Q10     | clickhouse |   2689.5 |      5 |     23090.9 |   22476.3 |   1958.5 |  20068.8 |  24311.3 |
| Q10     | exasol     |    284.9 |      5 |      1909.1 |    1905.3 |    155.1 |   1727.6 |   2103.6 |
| Q11     | clickhouse |    387.6 |      5 |      5542.3 |    5207.1 |    956.8 |   3512.2 |   5854.3 |
| Q11     | exasol     |     88.4 |      5 |       229.1 |     262.6 |    118.7 |    154.5 |    405.7 |
| Q12     | clickhouse |   1093.3 |      5 |      6296.6 |    7031.2 |   2434.3 |   4331.4 |  10601   |
| Q12     | exasol     |     52.9 |      5 |       432.5 |     440.2 |     46.6 |    396.2 |    512.1 |
| Q13     | clickhouse |   1822.9 |      5 |     11499.5 |   11240.7 |   4426.3 |   5071.1 |  16188.9 |
| Q13     | exasol     |    377.8 |      5 |      3044.2 |    2679.5 |    722.7 |   1431.5 |   3127.8 |
| Q14     | clickhouse |    104.7 |      5 |      3560.4 |    3198   |    851.6 |   2136.7 |   3980.9 |
| Q14     | exasol     |     46.2 |      5 |       395.6 |     400.9 |     44   |    362.1 |    473.1 |
| Q15     | clickhouse |    174.8 |      5 |      2257.4 |    2474.8 |    670.1 |   1719.5 |   3499.7 |
| Q15     | exasol     |    164   |      5 |       914.9 |     852.8 |    217.5 |    483.5 |   1058.3 |
| Q16     | clickhouse |    373.7 |      5 |      5618.4 |    5872.6 |    558.5 |   5546   |   6863.5 |
| Q16     | exasol     |    301.6 |      5 |      1552.4 |    1634.1 |    204.3 |   1414.8 |   1903.3 |
| Q17     | clickhouse |    562   |      5 |      8595.3 |    7931.6 |   1387.5 |   5838.2 |   9112.4 |
| Q17     | exasol     |     18.3 |      5 |        95.2 |      90.9 |     13   |     69.3 |    102.6 |
| Q18     | clickhouse |   1045.9 |      5 |     14022   |   13746.5 |   1886.6 |  11617.8 |  15624   |
| Q18     | exasol     |    321.1 |      5 |      2650   |    2389.2 |    787.3 |   1076.1 |   3113.2 |
| Q19     | clickhouse |   2968.5 |      5 |     18631.5 |   16001.9 |   5764.2 |   7351.7 |  21619.2 |
| Q19     | exasol     |     17.8 |      5 |        88.2 |      85.6 |     17.6 |     56.4 |    104.3 |
| Q20     | clickhouse |    826.8 |      5 |      8448.2 |    7546.4 |   1665.2 |   5538   |   8949.5 |
| Q20     | exasol     |    194.1 |      5 |       606.4 |     671.4 |    405.3 |    267.8 |   1330.4 |
| Q21     | clickhouse |   1296.4 |      5 |      9652.3 |   10646.8 |   3072.3 |   7662.5 |  15475.5 |
| Q21     | exasol     |    225.8 |      5 |      1561.8 |    1335.4 |    616.2 |    393.2 |   1842   |
| Q22     | clickhouse |    274   |      5 |      6735   |    5360.8 |   2334.3 |   1703.7 |   7158.9 |
| Q22     | exasol     |     61.5 |      5 |       434   |     370.1 |    148.1 |    105.7 |    450   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3497.5 |         12533.4 |    3.58 |      0.28 | False    |
| Q02     | exasol            | clickhouse          |         177.3 |          7882.2 |   44.46 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         768.3 |          9010.6 |   11.73 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |         298   |         14696.4 |   49.32 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         986.5 |         13852.7 |   14.04 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         112.8 |          2306.1 |   20.44 |      0.05 | False    |
| Q07     | exasol            | clickhouse          |        1382.6 |         24615.6 |   17.8  |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         362.7 |         14625.9 |   40.33 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        4049.4 |         12982.6 |    3.21 |      0.31 | False    |
| Q10     | exasol            | clickhouse          |        1909.1 |         23090.9 |   12.1  |      0.08 | False    |
| Q11     | exasol            | clickhouse          |         229.1 |          5542.3 |   24.19 |      0.04 | False    |
| Q12     | exasol            | clickhouse          |         432.5 |          6296.6 |   14.56 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        3044.2 |         11499.5 |    3.78 |      0.26 | False    |
| Q14     | exasol            | clickhouse          |         395.6 |          3560.4 |    9    |      0.11 | False    |
| Q15     | exasol            | clickhouse          |         914.9 |          2257.4 |    2.47 |      0.41 | False    |
| Q16     | exasol            | clickhouse          |        1552.4 |          5618.4 |    3.62 |      0.28 | False    |
| Q17     | exasol            | clickhouse          |          95.2 |          8595.3 |   90.29 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2650   |         14022   |    5.29 |      0.19 | False    |
| Q19     | exasol            | clickhouse          |          88.2 |         18631.5 |  211.24 |      0    | False    |
| Q20     | exasol            | clickhouse          |         606.4 |          8448.2 |   13.93 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1561.8 |          9652.3 |    6.18 |      0.16 | False    |
| Q22     | exasol            | clickhouse          |         434   |          6735   |   15.52 |      0.06 | False    |

### Per-Stream Statistics

This benchmark was executed using **10 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 11 | 10399.6 | 8801.7 | 1972.4 | 24311.3 |
| 1 | 11 | 11291.7 | 7158.9 | 1703.7 | 25114.8 |
| 2 | 11 | 11215.5 | 11617.8 | 2700.4 | 21709.7 |
| 3 | 11 | 9511.0 | 8212.9 | 1925.7 | 24615.6 |
| 4 | 11 | 11154.3 | 8949.5 | 2346.6 | 23090.9 |
| 5 | 11 | 10651.0 | 11466.5 | 2257.4 | 15844.9 |
| 6 | 11 | 11456.1 | 11499.5 | 2196.8 | 27651.8 |
| 7 | 11 | 9471.6 | 9115.3 | 3560.4 | 19328.2 |
| 8 | 11 | 11086.2 | 8957.3 | 4331.4 | 20752.1 |
| 9 | 11 | 8638.9 | 6735.0 | 2306.1 | 17328.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 6735.0ms
- Slowest stream median: 11617.8ms
- Stream performance variation: 72.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 11 | 1297.0 | 713.4 | 71.4 | 3692.7 |
| 1 | 11 | 728.5 | 434.0 | 70.7 | 2004.9 |
| 2 | 11 | 1324.8 | 1076.1 | 68.1 | 3597.6 |
| 3 | 11 | 1220.9 | 396.2 | 69.3 | 4696.7 |
| 4 | 11 | 1201.7 | 1067.0 | 91.0 | 3124.2 |
| 5 | 11 | 917.8 | 875.1 | 95.2 | 2319.5 |
| 6 | 11 | 1165.1 | 932.0 | 56.4 | 3044.2 |
| 7 | 11 | 940.9 | 369.5 | 102.6 | 3497.5 |
| 8 | 11 | 1321.7 | 986.5 | 243.4 | 4453.9 |
| 9 | 11 | 1021.5 | 437.7 | 97.8 | 4771.5 |

**Performance Analysis for Exasol:**
- Fastest stream median: 369.5ms
- Slowest stream median: 1076.1ms
- Stream performance variation: 191.2% difference between fastest and slowest streams
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
- Median runtime: 497.8ms
- Average runtime: 1114.0ms
- Fastest query: 56.4ms
- Slowest query: 4771.5ms

**clickhouse:**
- Median runtime: 9061.5ms
- Average runtime: 10487.6ms
- Fastest query: 1703.7ms
- Slowest query: 27651.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_conc_10-benchmark.zip`](scalability_conc_10-benchmark.zip)

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
- Measured runs executed across 10 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts