# Concurrency Cliff - 20 Streams

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-19 17:01:20

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **clickhouse**

**Key Findings:**
- exasol was the fastest overall with 1365.2ms median runtime
- clickhouse was 8.6x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 20 concurrent streams (randomized distribution)

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F2156DF8D44DED7 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F2156DF8D44DED7

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F2156DF8D44DED7 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F2156DF8D44DED7 /data

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
    &lt;max_server_memory_usage&gt;106335636684&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;30&lt;/max_concurrent_queries&gt;
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
- Memory limit: `100g`
- Max threads: `16`
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
- **Execution mode:** Multiuser (20 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip scalability_conc_20-benchmark.zip
cd scalability_conc_20

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
| Q01     | clickhouse |   1448.3 |      5 |     18076.4 |   15740.2 |   9983.1 |   3467.5 |  26217.3 |
| Q01     | exasol     |    481.6 |      5 |      4321.4 |    4692.9 |   2276.9 |   1713.5 |   7342.1 |
| Q02     | clickhouse |    641.3 |      5 |     11379.5 |   11292.7 |   2094.2 |   7897.3 |  13280.8 |
| Q02     | exasol     |     56.7 |      5 |       539.4 |     416.2 |    201.9 |    126.3 |    579.5 |
| Q03     | clickhouse |    594.5 |      5 |      7950   |    9151.7 |   5010.7 |   3806   |  16255.9 |
| Q03     | exasol     |    177.4 |      5 |       862.2 |    1425.5 |   1206.8 |    182.2 |   2885.9 |
| Q04     | clickhouse |   2156   |      5 |     18851.3 |   18586.4 |   2937.3 |  14499.6 |  22222.6 |
| Q04     | exasol     |     39.9 |      5 |       578.9 |     456.7 |    223.3 |    193   |    684.7 |
| Q05     | clickhouse |    407.3 |      5 |     10283.4 |   10637.5 |   1164.2 |   9402.8 |  12075.5 |
| Q05     | exasol     |    169.6 |      5 |      2167.1 |    2396.4 |    495.6 |   1880.5 |   3123.2 |
| Q06     | clickhouse |    104.3 |      5 |      3758   |    3580.3 |    850.4 |   2713.4 |   4634.6 |
| Q06     | exasol     |     26.5 |      5 |       233.3 |     253.2 |    103   |    144.9 |    412   |
| Q07     | clickhouse |    512.2 |      5 |     12675.3 |   11444.6 |   3701.3 |   5014.3 |  14514.2 |
| Q07     | exasol     |    158.4 |      5 |      2435.4 |    2495.5 |    816.1 |   1392.5 |   3656.2 |
| Q08     | clickhouse |    457.4 |      5 |      9754.2 |   10110.3 |   2900.6 |   5887.2 |  13527.4 |
| Q08     | exasol     |     49.3 |      5 |      1048.2 |     965.6 |    597.7 |    276.8 |   1707.7 |
| Q09     | clickhouse |    504.2 |      5 |     10482.8 |   11061.5 |   1209.9 |   9962.7 |  12767.6 |
| Q09     | exasol     |    556.9 |      5 |      9948.7 |    8982.6 |   2432.2 |   4675.9 |  10604.9 |
| Q10     | clickhouse |    696.7 |      5 |     15183.5 |   15010.3 |   1524.5 |  13367.1 |  17315.3 |
| Q10     | exasol     |    293   |      5 |      3296.9 |    3418.6 |   1251.6 |   1900.5 |   5344.1 |
| Q11     | clickhouse |    299.9 |      5 |      9830.5 |    9830.3 |   2115.2 |   6737.9 |  11921.3 |
| Q11     | exasol     |     93.4 |      5 |       426.7 |     409.2 |    256.6 |    140.5 |    718.5 |
| Q12     | clickhouse |    482.4 |      5 |     11980.7 |   12623.8 |   1601.3 |  10783.7 |  14875   |
| Q12     | exasol     |     53.6 |      5 |       730.7 |     791.7 |    404.1 |    381.9 |   1448.8 |
| Q13     | clickhouse |   3298.9 |      5 |     23025.5 |   22257.9 |   4216.9 |  15309.4 |  26159   |
| Q13     | exasol     |    394.1 |      5 |      4541.2 |    4501.9 |   2430.6 |   2115.4 |   8251.9 |
| Q14     | clickhouse |    125.9 |      5 |      3669.9 |    3852.5 |    649.2 |   3258.8 |   4711.6 |
| Q14     | exasol     |     47.9 |      5 |       863.6 |     897.3 |    378.1 |    404.9 |   1453.9 |
| Q15     | clickhouse |    174.2 |      5 |      4600.9 |    4652.7 |    470.9 |   4120.2 |   5208.1 |
| Q15     | exasol     |    167.3 |      5 |      1728.4 |    1621.8 |    472   |    882.9 |   2140.7 |
| Q16     | clickhouse |    381   |      5 |      9190.5 |    9243   |   1214.9 |   8146   |  11219.9 |
| Q16     | exasol     |    304.3 |      5 |      3035   |    3206.2 |    494.3 |   2687.5 |   3877.9 |
| Q17     | clickhouse |    557.5 |      5 |     13735.1 |   15178.3 |   2830.5 |  12672.6 |  18284.7 |
| Q17     | exasol     |     18.8 |      5 |       141.3 |     150.2 |     38.8 |    105.7 |    194.7 |
| Q18     | clickhouse |    528.8 |      5 |     13376   |   13114.5 |   1095.2 |  11537   |  14489.8 |
| Q18     | exasol     |    328.7 |      5 |      5008.6 |    4482   |   1272.6 |   2407.3 |   5549.7 |
| Q19     | clickhouse |   2931.3 |      5 |     32450.8 |   27589.6 |  12615.7 |   5462.3 |  36939.5 |
| Q19     | exasol     |     18.4 |      5 |       201.9 |     203.6 |     82.7 |     84.9 |    288.9 |
| Q20     | clickhouse |    840.5 |      5 |     15811.1 |   15491.7 |   2950.8 |  11319.3 |  18361.7 |
| Q20     | exasol     |    200.3 |      5 |       803   |     957.2 |    530   |    424   |   1527.6 |
| Q21     | clickhouse |    575.8 |      5 |     10630.5 |   10470.9 |   2993.6 |   6111.9 |  13894.6 |
| Q21     | exasol     |    232.2 |      5 |      3451.7 |    2754.7 |   2081.2 |    234.6 |   5122.3 |
| Q22     | clickhouse |    253.8 |      5 |      8897.1 |    8929.9 |   1978.9 |   5786.9 |  10877.4 |
| Q22     | exasol     |     63.7 |      5 |       930.1 |     959   |    380.1 |    486.6 |   1547.5 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        4321.4 |         18076.4 |    4.18 |      0.24 | False    |
| Q02     | exasol            | clickhouse          |         539.4 |         11379.5 |   21.1  |      0.05 | False    |
| Q03     | exasol            | clickhouse          |         862.2 |          7950   |    9.22 |      0.11 | False    |
| Q04     | exasol            | clickhouse          |         578.9 |         18851.3 |   32.56 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2167.1 |         10283.4 |    4.75 |      0.21 | False    |
| Q06     | exasol            | clickhouse          |         233.3 |          3758   |   16.11 |      0.06 | False    |
| Q07     | exasol            | clickhouse          |        2435.4 |         12675.3 |    5.2  |      0.19 | False    |
| Q08     | exasol            | clickhouse          |        1048.2 |          9754.2 |    9.31 |      0.11 | False    |
| Q09     | exasol            | clickhouse          |        9948.7 |         10482.8 |    1.05 |      0.95 | False    |
| Q10     | exasol            | clickhouse          |        3296.9 |         15183.5 |    4.61 |      0.22 | False    |
| Q11     | exasol            | clickhouse          |         426.7 |          9830.5 |   23.04 |      0.04 | False    |
| Q12     | exasol            | clickhouse          |         730.7 |         11980.7 |   16.4  |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        4541.2 |         23025.5 |    5.07 |      0.2  | False    |
| Q14     | exasol            | clickhouse          |         863.6 |          3669.9 |    4.25 |      0.24 | False    |
| Q15     | exasol            | clickhouse          |        1728.4 |          4600.9 |    2.66 |      0.38 | False    |
| Q16     | exasol            | clickhouse          |        3035   |          9190.5 |    3.03 |      0.33 | False    |
| Q17     | exasol            | clickhouse          |         141.3 |         13735.1 |   97.21 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        5008.6 |         13376   |    2.67 |      0.37 | False    |
| Q19     | exasol            | clickhouse          |         201.9 |         32450.8 |  160.73 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         803   |         15811.1 |   19.69 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        3451.7 |         10630.5 |    3.08 |      0.32 | False    |
| Q22     | exasol            | clickhouse          |         930.1 |          8897.1 |    9.57 |      0.1  | False    |

### Per-Stream Statistics

This benchmark was executed using **20 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 6 | 12521.4 | 12506.6 | 3806.0 | 24888.2 |
| 1 | 6 | 11634.6 | 10339.3 | 5786.9 | 20179.3 |
| 10 | 5 | 13677.0 | 10482.8 | 2713.4 | 36939.5 |
| 11 | 5 | 13871.1 | 14514.2 | 4120.2 | 22222.6 |
| 12 | 5 | 10537.1 | 12018.3 | 4285.2 | 13376.0 |
| 13 | 5 | 13262.3 | 12767.6 | 3282.7 | 26217.3 |
| 14 | 5 | 13728.6 | 11632.7 | 6737.9 | 23025.5 |
| 15 | 5 | 11778.4 | 12075.5 | 9309.9 | 13565.1 |
| 16 | 5 | 14046.4 | 12159.3 | 4600.9 | 23614.3 |
| 17 | 5 | 10448.1 | 11379.5 | 4711.6 | 13735.1 |
| 18 | 5 | 13150.0 | 13894.6 | 10210.0 | 15811.1 |
| 19 | 5 | 13036.2 | 13502.0 | 8897.1 | 18076.4 |
| 2 | 6 | 12127.5 | 13236.8 | 3467.5 | 18361.7 |
| 3 | 6 | 11118.4 | 11334.2 | 3758.0 | 18284.7 |
| 4 | 6 | 12308.2 | 9388.2 | 2715.2 | 30027.9 |
| 5 | 6 | 11897.3 | 12670.2 | 5049.1 | 18851.3 |
| 6 | 6 | 12956.5 | 10691.8 | 3258.8 | 32450.8 |
| 7 | 6 | 12516.6 | 8877.7 | 3669.9 | 33067.6 |
| 8 | 6 | 12278.9 | 10038.2 | 5728.1 | 26159.0 |
| 9 | 6 | 9236.6 | 7481.2 | 4080.2 | 18215.0 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7481.2ms
- Slowest stream median: 14514.2ms
- Stream performance variation: 94.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 6 | 2711.5 | 1175.0 | 140.5 | 8251.9 |
| 1 | 6 | 1037.0 | 795.4 | 126.3 | 2961.0 |
| 10 | 5 | 2644.6 | 1453.9 | 84.9 | 10032.4 |
| 11 | 5 | 1591.1 | 1508.1 | 578.9 | 3656.2 |
| 12 | 5 | 2362.6 | 2435.4 | 486.6 | 4156.0 |
| 13 | 5 | 3008.9 | 1713.5 | 539.4 | 9651.1 |
| 14 | 5 | 2137.3 | 1880.5 | 426.7 | 4541.2 |
| 15 | 5 | 2197.8 | 2167.1 | 281.4 | 5122.3 |
| 16 | 5 | 2771.9 | 2716.1 | 862.2 | 5002.0 |
| 17 | 5 | 1597.5 | 786.9 | 141.3 | 5549.7 |
| 18 | 5 | 2959.8 | 943.6 | 524.1 | 10604.9 |
| 19 | 5 | 2492.9 | 1547.5 | 571.5 | 7342.1 |
| 2 | 6 | 2483.3 | 2372.7 | 193.0 | 5008.6 |
| 3 | 6 | 2014.4 | 209.7 | 105.7 | 9948.7 |
| 4 | 6 | 2145.2 | 2422.1 | 273.0 | 3877.9 |
| 5 | 6 | 1600.6 | 670.1 | 194.7 | 5288.2 |
| 6 | 6 | 1358.4 | 679.6 | 169.2 | 3296.9 |
| 7 | 6 | 2174.2 | 1131.0 | 288.9 | 6536.6 |
| 8 | 6 | 2494.5 | 2632.4 | 657.9 | 4021.1 |
| 9 | 6 | 875.4 | 730.1 | 123.5 | 2140.7 |

**Performance Analysis for Exasol:**
- Fastest stream median: 209.7ms
- Slowest stream median: 2716.1ms
- Stream performance variation: 1195.5% difference between fastest and slowest streams
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
- Median runtime: 1365.2ms
- Average runtime: 2110.8ms
- Fastest query: 84.9ms
- Slowest query: 10604.9ms

**clickhouse:**
- Median runtime: 11765.4ms
- Average runtime: 12265.9ms
- Fastest query: 2713.4ms
- Slowest query: 36939.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`scalability_conc_20-benchmark.zip`](scalability_conc_20-benchmark.zip)

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
- Measured runs executed across 20 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts