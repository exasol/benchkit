# Exasol vs ClickHouse Performance Comparison on TPC-H SF100

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2025-10-24 17:28:50

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **clickhouse**
- **clickhouse_tuned**
- **clickhouse_stat**

**Key Findings:**
- exasol was the fastest overall with 242.5ms median runtime
- clickhouse_tuned was 11.5x slower
- Tested 462 total query executions across 22 different TPC-H queries

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
- **Hostname:** ip-10-0-1-89

### Clickhouse 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-13

### Clickhouse_tuned 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-121

### Clickhouse_stat 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-142


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.8xlarge
- **Clickhouse Instance:** r6id.8xlarge
- **Clickhouse_tuned Instance:** r6id.8xlarge
- **Clickhouse_stat Instance:** r6id.8xlarge


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



#### Clickhouse_tuned 25.9.4.58 Setup

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
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;212792564121&lt;/max_server_memory_usage&gt;
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



#### Clickhouse 25.9.4.58 Setup

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
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;212792564121&lt;/max_server_memory_usage&gt;
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



#### Clickhouse_stat 25.9.4.58 Setup

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
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;212792570675&lt;/max_server_memory_usage&gt;
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
            &lt;allow_experimental_statistics&gt;1&lt;/allow_experimental_statistics&gt;
            &lt;allow_statistics_optimize&gt;1&lt;/allow_statistics_optimize&gt;
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

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_100g-benchmark.zip
cd exa_vs_ch_100g

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
| Clickhouse | 126.77s | 28.59s | 155.36s | New infrastructure |
| Clickhouse_tuned | 126.77s | 29.10s | 155.87s | New infrastructure |
| Clickhouse_stat | 126.77s | 29.80s | 156.57s | New infrastructure |
| Exasol | 126.77s | 538.85s | 665.62s | New infrastructure |

**Infrastructure Provisioning:** 126.77s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse had the fastest software installation at 28.59s
- Exasol took 538.85s to install (18.8x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |   2482.6 |      7 |      2462   |    2466.2 |     11.9 |   2456.1 |   2491.7 |
| Q01     | clickhouse_tuned |   2540.8 |      7 |      2640.6 |    2654.9 |     74.8 |   2551.8 |   2739.1 |
| Q01     | exasol           |    802.3 |      7 |       801.1 |     800.1 |      4.6 |    794.7 |    806.6 |
| Q02     | clickhouse       |   1241.4 |      7 |      1052.7 |    1066.9 |     36.1 |   1039   |   1144.4 |
| Q02     | clickhouse_tuned |   1353   |      7 |      1120.5 |    1121.6 |     26.5 |   1088.5 |   1172   |
| Q02     | exasol           |     93.7 |      7 |        78.8 |      78.8 |      2.4 |     75.2 |     82.1 |
| Q03     | clickhouse       |   4117.1 |      7 |      3986.5 |    3981.1 |     20.8 |   3953.8 |   4017.3 |
| Q03     | clickhouse_tuned |   4507.2 |      7 |      4446.6 |    4424.5 |    104.7 |   4310.3 |   4613.5 |
| Q03     | exasol           |    341.8 |      7 |       346.5 |     344.9 |      5   |    339.4 |    353   |
| Q04     | clickhouse       |   3293.6 |      7 |      2547.9 |    2583.8 |     95.2 |   2517.3 |   2792.1 |
| Q04     | clickhouse_tuned |  16957   |      7 |     14560.7 |   14683.2 |    272.3 |  14433.4 |  15122.6 |
| Q04     | exasol           |     64.7 |      7 |        63.2 |      63.4 |      0.4 |     62.9 |     64   |
| Q05     | clickhouse       |   9505.4 |      7 |      8776.7 |    8751   |    115   |   8590.8 |   8923.6 |
| Q05     | clickhouse_tuned |   9433.2 |      7 |      9282.5 |    9191.1 |    403.5 |   8309.8 |   9537.2 |
| Q05     | exasol           |    273.4 |      7 |       208.9 |     209.3 |      1.3 |    207.7 |    211.8 |
| Q06     | clickhouse       |    940.2 |      7 |       163.1 |     164.3 |      2.6 |    161.8 |    167.9 |
| Q06     | clickhouse_tuned |   1050.5 |      7 |       170   |     171.2 |      4.2 |    166.7 |    179.3 |
| Q06     | exasol           |     43.8 |      7 |        43.7 |      43.6 |      0.3 |     43.2 |     43.9 |
| Q07     | clickhouse       |   6372.7 |      7 |      4886.4 |    4882.5 |     23   |   4849.5 |   4915.3 |
| Q07     | clickhouse_tuned |   6436.7 |      7 |      5042.2 |    5054.3 |     38.4 |   5011.7 |   5116.4 |
| Q07     | exasol           |    276   |      7 |       288.6 |     286.1 |     11.3 |    273.2 |    303.4 |
| Q08     | clickhouse       |   7063.3 |      7 |      7765.6 |    7734.8 |    249.1 |   7213.6 |   7979.8 |
| Q08     | clickhouse_tuned |   7309.4 |      7 |      8082.3 |    8094.1 |     84   |   8006   |   8226.2 |
| Q08     | exasol           |     80.2 |      7 |        76.4 |      79.5 |      8.9 |     75.3 |     99.6 |
| Q09     | clickhouse       |  13474.3 |      7 |     11756.1 |   11904   |    293.8 |  11645.6 |  12456.1 |
| Q09     | clickhouse_tuned |  14229.4 |      7 |     11956.3 |   12014.1 |    214.1 |  11816   |  12414.9 |
| Q09     | exasol           |    965.2 |      7 |       960.6 |     962.4 |      3.5 |    959.4 |    968.3 |
| Q10     | clickhouse       |   4175.6 |      7 |      2846.6 |    2937.9 |    163.2 |   2801.9 |   3179   |
| Q10     | clickhouse_tuned |   4312.2 |      7 |      2895.4 |    3084.2 |    349.1 |   2831.3 |   3642.1 |
| Q10     | exasol           |    570.5 |      7 |       573   |     574.6 |      6.2 |    565.2 |    585   |
| Q11     | clickhouse       |    884.7 |      7 |       617.1 |     615.9 |     12.1 |    599   |    629.7 |
| Q11     | clickhouse_tuned |   1176.2 |      7 |       744.8 |     743.5 |     24.2 |    707.6 |    774   |
| Q11     | exasol           |    152.7 |      7 |       150   |     151.2 |      7   |    144.3 |    165   |
| Q12     | clickhouse       |   2277.1 |      7 |       749.4 |     759.7 |     25.2 |    736.1 |    811.4 |
| Q12     | clickhouse_tuned |   2734.6 |      7 |       881.8 |     895.3 |     46.1 |    856   |    987.1 |
| Q12     | exasol           |     88.1 |      7 |        85.3 |      85.2 |      0.5 |     84.6 |     85.7 |
| Q13     | clickhouse       |   5018.2 |      7 |      4735   |    4750.9 |     83.5 |   4668.9 |   4912.8 |
| Q13     | clickhouse_tuned |   5910.1 |      7 |      5423.1 |    5465   |    108.9 |   5350.9 |   5662.7 |
| Q13     | exasol           |    682.5 |      7 |       675.4 |     675.6 |      7.9 |    664.3 |    690.5 |
| Q14     | clickhouse       |    201.1 |      7 |       213.1 |     211.6 |      5.3 |    201.4 |    216.7 |
| Q14     | clickhouse_tuned |    238.3 |      7 |       230.4 |     231.7 |      3.6 |    227.8 |    237.2 |
| Q14     | exasol           |     82.7 |      7 |        82.7 |      82.8 |      0.3 |     82.4 |     83.4 |
| Q15     | clickhouse       |    335.2 |      7 |       280.5 |     289.5 |     16.5 |    277.4 |    322.7 |
| Q15     | clickhouse_tuned |    414.8 |      7 |       367.1 |     371.6 |     23.6 |    352.3 |    419.7 |
| Q15     | exasol           |    389.4 |      7 |       380.9 |     380.7 |      4.4 |    373.7 |    386.1 |
| Q16     | clickhouse       |    458.1 |      7 |       450.5 |     449.8 |      3.9 |    445.1 |    454.8 |
| Q16     | clickhouse_tuned |    760.6 |      7 |       691.5 |     690.3 |     19.3 |    669.2 |    728.6 |
| Q16     | exasol           |    470.7 |      7 |       486.1 |     485.5 |      4.4 |    479.6 |    492.8 |
| Q17     | clickhouse       |   6053.9 |      7 |      5394.8 |    5396.3 |     21.1 |   5366.9 |   5425.6 |
| Q17     | clickhouse_tuned |   1461.1 |      7 |      1317.4 |    1320   |     11.9 |   1307.5 |   1343   |
| Q17     | exasol           |     31   |      7 |        30.9 |      31   |      0.2 |     30.8 |     31.4 |
| Q18     | clickhouse       |   5538   |      7 |      5354.3 |    5369.8 |     55.8 |   5330.4 |   5490.9 |
| Q18     | clickhouse_tuned |  15523.8 |      7 |     13314.8 |   13608.1 |    594.9 |  12974.5 |  14455.8 |
| Q18     | exasol           |    649.5 |      7 |       639.4 |     638.5 |      8.3 |    626.6 |    648.1 |
| Q19     | clickhouse       |   2260.1 |      7 |      2190.9 |    2190.9 |     11.4 |   2176.9 |   2205.1 |
| Q19     | clickhouse_tuned |   7027.4 |      7 |      5623.4 |    5641.5 |     68.8 |   5538.5 |   5744.1 |
| Q19     | exasol           |     27.1 |      7 |        27   |      27.1 |      0.4 |     26.5 |     27.6 |
| Q20     | clickhouse       |    378.5 |      7 |       345.5 |     345.2 |      4.7 |    340   |    354.2 |
| Q20     | clickhouse_tuned |   3288.4 |      7 |      2660.6 |    2637.5 |     62.8 |   2532.6 |   2701.8 |
| Q20     | exasol           |    286.9 |      7 |       281.2 |     281.4 |      1.9 |    278.4 |    283.7 |
| Q21     | clickhouse       |  46792.6 |      7 |     46498.2 |   46517.8 |    463   |  45952.2 |  47354.7 |
| Q21     | clickhouse_tuned |  33517.2 |      7 |     33190.9 |   33276.7 |   2162.9 |  30555.8 |  36986.6 |
| Q21     | exasol           |    390.1 |      7 |       384.7 |     389.8 |     10.9 |    383.1 |    413.4 |
| Q22     | clickhouse       |    616.3 |      7 |       609   |     613.5 |     23.1 |    586.5 |    647.7 |
| Q22     | clickhouse_tuned |   2335.7 |      7 |       632.5 |     651.4 |     95.3 |    548.5 |    766.4 |
| Q22     | exasol           |     96.4 |      7 |        95.6 |      95.6 |      0.3 |     95   |     96   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |         801.1 |          2462   |    3.07 |      0.33 | False    |
| Q02     | exasol            | clickhouse          |          78.8 |          1052.7 |   13.36 |      0.07 | False    |
| Q03     | exasol            | clickhouse          |         346.5 |          3986.5 |   11.51 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |          63.2 |          2547.9 |   40.31 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         208.9 |          8776.7 |   42.01 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |          43.7 |           163.1 |    3.73 |      0.27 | False    |
| Q07     | exasol            | clickhouse          |         288.6 |          4886.4 |   16.93 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |          76.4 |          7765.6 |  101.64 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         960.6 |         11756.1 |   12.24 |      0.08 | False    |
| Q10     | exasol            | clickhouse          |         573   |          2846.6 |    4.97 |      0.2  | False    |
| Q11     | exasol            | clickhouse          |         150   |           617.1 |    4.11 |      0.24 | False    |
| Q12     | exasol            | clickhouse          |          85.3 |           749.4 |    8.79 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |         675.4 |          4735   |    7.01 |      0.14 | False    |
| Q14     | exasol            | clickhouse          |          82.7 |           213.1 |    2.58 |      0.39 | False    |
| Q15     | exasol            | clickhouse          |         380.9 |           280.5 |    0.74 |      1.36 | True     |
| Q16     | exasol            | clickhouse          |         486.1 |           450.5 |    0.93 |      1.08 | True     |
| Q17     | exasol            | clickhouse          |          30.9 |          5394.8 |  174.59 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |         639.4 |          5354.3 |    8.37 |      0.12 | False    |
| Q19     | exasol            | clickhouse          |          27   |          2190.9 |   81.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         281.2 |           345.5 |    1.23 |      0.81 | False    |
| Q21     | exasol            | clickhouse          |         384.7 |         46498.2 |  120.87 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          95.6 |           609   |    6.37 |      0.16 | False    |
| Q01     | exasol            | clickhouse_tuned    |         801.1 |          2640.6 |    3.3  |      0.3  | False    |
| Q02     | exasol            | clickhouse_tuned    |          78.8 |          1120.5 |   14.22 |      0.07 | False    |
| Q03     | exasol            | clickhouse_tuned    |         346.5 |          4446.6 |   12.83 |      0.08 | False    |
| Q04     | exasol            | clickhouse_tuned    |          63.2 |         14560.7 |  230.39 |      0    | False    |
| Q05     | exasol            | clickhouse_tuned    |         208.9 |          9282.5 |   44.44 |      0.02 | False    |
| Q06     | exasol            | clickhouse_tuned    |          43.7 |           170   |    3.89 |      0.26 | False    |
| Q07     | exasol            | clickhouse_tuned    |         288.6 |          5042.2 |   17.47 |      0.06 | False    |
| Q08     | exasol            | clickhouse_tuned    |          76.4 |          8082.3 |  105.79 |      0.01 | False    |
| Q09     | exasol            | clickhouse_tuned    |         960.6 |         11956.3 |   12.45 |      0.08 | False    |
| Q10     | exasol            | clickhouse_tuned    |         573   |          2895.4 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse_tuned    |         150   |           744.8 |    4.97 |      0.2  | False    |
| Q12     | exasol            | clickhouse_tuned    |          85.3 |           881.8 |   10.34 |      0.1  | False    |
| Q13     | exasol            | clickhouse_tuned    |         675.4 |          5423.1 |    8.03 |      0.12 | False    |
| Q14     | exasol            | clickhouse_tuned    |          82.7 |           230.4 |    2.79 |      0.36 | False    |
| Q15     | exasol            | clickhouse_tuned    |         380.9 |           367.1 |    0.96 |      1.04 | True     |
| Q16     | exasol            | clickhouse_tuned    |         486.1 |           691.5 |    1.42 |      0.7  | False    |
| Q17     | exasol            | clickhouse_tuned    |          30.9 |          1317.4 |   42.63 |      0.02 | False    |
| Q18     | exasol            | clickhouse_tuned    |         639.4 |         13314.8 |   20.82 |      0.05 | False    |
| Q19     | exasol            | clickhouse_tuned    |          27   |          5623.4 |  208.27 |      0    | False    |
| Q20     | exasol            | clickhouse_tuned    |         281.2 |          2660.6 |    9.46 |      0.11 | False    |
| Q21     | exasol            | clickhouse_tuned    |         384.7 |         33190.9 |   86.28 |      0.01 | False    |
| Q22     | exasol            | clickhouse_tuned    |          95.6 |           632.5 |    6.62 |      0.15 | False    |

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
- Median runtime: 2504.5ms
- Average runtime: 5181.1ms
- Fastest query: 161.8ms
- Slowest query: 47354.7ms

**clickhouse_tuned:**
- Median runtime: 2785.2ms
- Average runtime: 5728.4ms
- Fastest query: 166.7ms
- Slowest query: 36986.6ms

**exasol:**
- Median runtime: 242.5ms
- Average runtime: 307.6ms
- Fastest query: 26.5ms
- Slowest query: 968.3ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_100g-benchmark.zip`](exa_vs_ch_100g-benchmark.zip)

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

**Clickhouse 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000

**Clickhouse_tuned 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000

**Clickhouse_stat 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000
  - allow_experimental_statistics: 1
  - allow_statistics_optimize: 1


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