# Extended Scalability - Single Node Stream Scaling (1 Stream)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-30 02:34:00

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 5 database systems:
- **clickhouse**
- **duckdb**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 650.9ms median runtime
- trino was 29.6x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 1 concurrent streams (round-robin distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-96

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
- **Hostname:** ip-10-0-1-223

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-35

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-178

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-38


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.xlarge
- **Clickhouse Instance:** r6id.xlarge
- **Trino Instance:** r6id.xlarge
- **Starrocks Instance:** r6id.xlarge
- **Duckdb Instance:** r6id.xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (150GB)
sudo parted /dev/nvme1n1 mkpart primary 70GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

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
CCC_PLAY_WORKING_COPY=@exasol-2025.2.0
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



#### Trino 479 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64FD1E1E8A9EB802D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64FD1E1E8A9EB802D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64FD1E1E8A9EB802D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64FD1E1E8A9EB802D /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create trino data directory
sudo mkdir -p /data/trino

```

**Prerequisites:**
```bash
# Add Eclipse Temurin (Adoptium) repository for Java 22
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg 2&gt;/dev/null || true
echo &#34;deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(lsb_release -sc) main&#34; | sudo tee /etc/apt/sources.list.d/adoptium.list

# Install Java 25 (required by Trino 479+)
sudo apt-get update &amp;&amp; sudo apt-get install -y temurin-25-jdk

# Install python symlink (required by Trino launcher)
sudo apt-get install -y python-is-python3

```

**User Setup:**
```bash
# Create Trino system user
sudo useradd -r -s /bin/false trino

```

**Installation:**
```bash
# Download Trino server version 479
wget https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

# Extract Trino server to /opt
sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/

# Create symlink /opt/trino-server
sudo ln -sf /opt/trino-server-479 /opt/trino-server

# Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

# Create etc symlink for Trino launcher
sudo ln -sf /etc/trino /opt/trino-server/etc

```

**Configuration:**
```bash
# Configure Trino node properties
sudo tee /etc/trino/node.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
node.environment=production
node.id=af165f5d-9173-4637-9600-ed8e93ab9c75
node.data-dir=/var/trino/data
EOF

# Configure JVM with 24G heap (80% of 30.8G total RAM)
sudo tee /etc/trino/jvm.config &gt; /dev/null &lt;&lt; &#39;EOF&#39;
-server
-Xmx24G
-Xms24G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
-XX:ReservedCodeCacheSize=512M
-Djdk.attach.allowAttachSelf=true
-Djdk.nio.maxCachedBufferSize=2000000
EOF

# Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
discovery.uri=http://localhost:8080
query.max-memory=24GB
query.max-memory-per-node=16GB
EOF

# Configure memory connector catalog for temporary tables
sudo tee /etc/trino/catalog/memory.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
connector.name=memory
EOF

# Configure Hive connector with file-based metastore at /data/trino/hive-warehouse
sudo tee /etc/trino/catalog/hive.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
connector.name=hive
hive.metastore=file
hive.metastore.catalog.dir=local:///data/trino/hive-warehouse
fs.native-local.enabled=true
local.location=/
EOF

# Create Trino systemd service
sudo tee /etc/systemd/system/trino.service &gt; /dev/null &lt;&lt; &#39;EOF&#39;
[Unit]
Description=Trino Server
After=network.target

[Service]
Type=forking
User=trino
Group=trino
ExecStart=/opt/trino-server/bin/launcher start
ExecStop=/opt/trino-server/bin/launcher stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

```

**Service Management:**
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Start Trino server service
sudo systemctl start trino

# Enable Trino server to start on boot
sudo systemctl enable trino

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45EB4E3E2100DA04D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45EB4E3E2100DA04D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45EB4E3E2100DA04D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45EB4E3E2100DA04D /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create starrocks data directory
sudo mkdir -p /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# Configure StarRocks FE
sudo tee /opt/starrocks/fe/conf/fe.conf &gt; /dev/null &lt;&lt; &#39;EOF&#39;
# StarRocks FE Configuration
LOG_DIR = /opt/starrocks/fe/log
meta_dir = /opt/starrocks/fe/meta
http_port = 8030
rpc_port = 9020
query_port = 9030
edit_log_port = 9010
priority_networks = &lt;PRIVATE_IP&gt;/24
# Performance tuning
qe_max_connection = 1024
# Memory settings
metadata_memory_limit = 8G

EOF

# Configure StarRocks BE
sudo tee /opt/starrocks/be/conf/be.conf &gt; /dev/null &lt;&lt; &#39;EOF&#39;
# StarRocks BE Configuration
LOG_DIR = /opt/starrocks/be/log
be_port = 9060
be_http_port = 8040
heartbeat_service_port = 9050
brpc_port = 8060
priority_networks = &lt;PRIVATE_IP&gt;/24
storage_root_path = /data/starrocks
# Performance tuning - aggressive memory use with spill fallback
mem_limit = 90%
# Parallel execution
parallel_fragment_exec_instance_num = 16
# Spill-to-disk for memory-intensive queries (safety net)
spill_local_storage_dir = /data/starrocks/spill
enable_spill = true
spill_mode = auto

EOF

```

**Service Management:**
```bash
# Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```


**Tuning Parameters:**

**Data Directory:** `/data/starrocks`



#### Clickhouse 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS320C8D3C9A19DF3A1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS320C8D3C9A19DF3A1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS320C8D3C9A19DF3A1 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS320C8D3C9A19DF3A1 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
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
    &lt;max_server_memory_usage&gt;26472837939&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;4&lt;/max_concurrent_queries&gt;
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
            &lt;max_memory_usage&gt;20000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;10000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;10000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Max memory usage: `20.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS33F7F1FA8BE40F5AE with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS33F7F1FA8BE40F5AE

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS33F7F1FA8BE40F5AE to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS33F7F1FA8BE40F5AE /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create duckdb data directory
sudo mkdir -p /data/duckdb

# Set ownership of /data/duckdb to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/duckdb

```

**Preparation:**
```bash
# Create DuckDB data directory: /data/duckdb
sudo mkdir -p /data/duckdb &amp;&amp; sudo chown ubuntu:ubuntu /data/duckdb

```


**Tuning Parameters:**
- Memory limit: `24GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (1 concurrent streams)
- **Query distribution:** Round-robin
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_single_streams_1-benchmark.zip
cd ext_scalability_single_streams_1

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
| Q01     | clickhouse |   8877.1 |      5 |      8930.6 |    8935.9 |     84.2 |   8860.7 |   9073.9 |
| Q01     | duckdb     |   7815.6 |      5 |      3755.1 |    3750.7 |     21.4 |   3718.4 |   3777.5 |
| Q01     | exasol     |   3115.1 |      5 |      3122   |    3123.1 |      9.1 |   3114.6 |   3138.3 |
| Q01     | starrocks  |  13513   |      5 |     10064.7 |   10074.2 |     95.4 |   9963.5 |  10222.3 |
| Q01     | trino      |  20212.1 |      5 |     17424.5 |   17624.3 |    429   |  17350.9 |  18365.7 |
| Q02     | clickhouse |   3916.9 |      5 |      2839.1 |    2887.2 |    165.6 |   2705.8 |   3153.4 |
| Q02     | duckdb     |    961   |      5 |       760   |     760.1 |      2.8 |    755.9 |    763.1 |
| Q02     | exasol     |     98.6 |      5 |        85.2 |      85   |      1.1 |     83.7 |     86.1 |
| Q02     | starrocks  |    850.2 |      5 |       432.4 |     426.1 |     18.6 |    393.3 |    438.9 |
| Q02     | trino      |  10653.4 |      5 |      5801.4 |    5880.3 |    239.5 |   5681.9 |   6288.4 |
| Q03     | clickhouse |  13379.6 |      5 |     11557.2 |   11652.1 |    261.4 |  11441.2 |  12106.4 |
| Q03     | duckdb     |   3434.1 |      5 |      2506.2 |    2504.2 |     10.7 |   2487.1 |   2516.8 |
| Q03     | exasol     |   1107.1 |      5 |      1105.4 |    1111.6 |     18.4 |   1097.5 |   1143.7 |
| Q03     | starrocks  |   6107.2 |      5 |      5983.4 |    6020.7 |     87.8 |   5954.6 |   6163.9 |
| Q03     | trino      |  24587.7 |      5 |     21775   |   21797   |    377.2 |  21361.2 |  22383.5 |
| Q04     | clickhouse |  12955.6 |      5 |      9770.2 |    9703.9 |    220.7 |   9467.7 |   9996.8 |
| Q04     | duckdb     |   2837   |      5 |      2451.3 |    2445.9 |     12.3 |   2428.3 |   2458.5 |
| Q04     | exasol     |    209.8 |      5 |       205.1 |     205   |      0.6 |    203.9 |    205.6 |
| Q04     | starrocks  |   4152.8 |      5 |      4100.6 |    4074.2 |     64.4 |   3985.2 |   4136.9 |
| Q04     | trino      |  19994.5 |      5 |     18546.5 |   18680.5 |    336.7 |  18415.9 |  19243.9 |
| Q05     | clickhouse |  16933.9 |      5 |     16565.5 |   16492.5 |    221.6 |  16239   |  16759.1 |
| Q05     | duckdb     |   3091.1 |      5 |      2747.3 |    2748   |      4.7 |   2743.4 |   2755   |
| Q05     | exasol     |    886   |      5 |       825.1 |     827.8 |      4.2 |    824.4 |    832.9 |
| Q05     | starrocks  |   6013.2 |      5 |      5916.8 |    5913.6 |     97.7 |   5779   |   6053.6 |
| Q05     | trino      |  23941   |      5 |     21955.3 |   22394.2 |   1170   |  21246.4 |  24223.9 |
| Q06     | clickhouse |    530.6 |      5 |       702.2 |     726.6 |    184.9 |    543.8 |    956.8 |
| Q06     | duckdb     |    812.5 |      5 |       815.7 |     816.9 |      2.9 |    814.5 |    821.8 |
| Q06     | exasol     |    137.1 |      5 |       136.1 |     135.9 |      0.5 |    135.2 |    136.4 |
| Q06     | starrocks  |   2095.9 |      5 |      1954.5 |    1978.4 |     41.9 |   1947.1 |   2046.5 |
| Q06     | trino      |   9081.1 |      5 |      7775.1 |    7792.3 |     86.8 |   7729.3 |   7941.4 |
| Q07     | clickhouse |  25675.6 |      5 |     23258   |   23418.7 |    667.9 |  22738.1 |  24385.3 |
| Q07     | duckdb     |   2655.4 |      5 |      2619.3 |    2625.4 |     16.2 |   2609.1 |   2644.5 |
| Q07     | exasol     |   1159.4 |      5 |      1116.8 |    1119.7 |      7.5 |   1111.9 |   1129.6 |
| Q07     | starrocks  |   4962.6 |      5 |      4928.9 |    4913.5 |     97.7 |   4762.4 |   5019   |
| Q07     | trino      |  19395   |      5 |     17672.7 |   17790   |    445.8 |  17453   |  18569   |
| Q08     | clickhouse |  19601.7 |      5 |     18983.3 |   19100.5 |    568.9 |  18565.4 |  19972   |
| Q08     | duckdb     |   2928.2 |      5 |      2660.3 |    2662.7 |     22.5 |   2634.5 |   2689   |
| Q08     | exasol     |    257.3 |      5 |       254.6 |     255.2 |      1.6 |    253.7 |    257.1 |
| Q08     | starrocks  |   3807.7 |      5 |      3812.6 |    3812.3 |     37   |   3767.3 |   3852.1 |
| Q08     | trino      |  18628.7 |      5 |     18151.8 |   18121.4 |    227.9 |  17803.4 |  18431.5 |
| Q09     | clickhouse |  10881   |      5 |      7427.4 |    7844.1 |    995.3 |   7050.3 |   9529.6 |
| Q09     | duckdb     |   9047.7 |      5 |      8960.5 |    8966.9 |     67.4 |   8882.7 |   9058.1 |
| Q09     | exasol     |   3970.7 |      5 |      4011.6 |    4015.4 |     18.4 |   3990.6 |   4035.9 |
| Q09     | starrocks  |  10171.7 |      5 |     10073.9 |    9974.2 |    185.7 |   9662.5 |  10097.4 |
| Q09     | trino      |  56957.9 |      5 |     57436.2 |   59402.7 |   4367.3 |  56492.8 |  67001.2 |
| Q10     | clickhouse |  11894.5 |      5 |      8443.9 |    8623   |    660.8 |   7931.7 |   9576.1 |
| Q10     | duckdb     |   4349.4 |      5 |      4077.2 |    4035.3 |     79.3 |   3920   |   4108.4 |
| Q10     | exasol     |   1238.7 |      5 |      1244.8 |    1243.1 |     22.9 |   1209.5 |   1271.4 |
| Q10     | starrocks  |   4497.9 |      5 |      4633.6 |    4624.7 |     29   |   4574.7 |   4648.7 |
| Q10     | trino      |  31521.6 |      5 |     21514.2 |   21237.4 |    860.1 |  19897.1 |  21946.3 |
| Q11     | clickhouse |   1910.6 |      5 |      1799.9 |    1863.9 |    145.8 |   1767.4 |   2120.8 |
| Q11     | duckdb     |    409.4 |      5 |       388   |     391.6 |     12   |    384.4 |    412.8 |
| Q11     | exasol     |    231.4 |      5 |       231.8 |     250.5 |     44.8 |    227.3 |    330.5 |
| Q11     | starrocks  |    681   |      5 |       357.5 |     368.9 |     37.7 |    340.2 |    432.9 |
| Q11     | trino      |   6476   |      5 |      3088.1 |    3178.5 |    236   |   2905   |   3428.3 |
| Q12     | clickhouse |   7242.9 |      5 |      2611.9 |    2572.1 |    105.5 |   2424.3 |   2681.1 |
| Q12     | duckdb     |   3084.5 |      5 |      3107.3 |    3113   |     32.9 |   3067.5 |   3152.4 |
| Q12     | exasol     |    510.4 |      5 |       287.6 |     297.2 |     14.3 |    286.4 |    318.2 |
| Q12     | starrocks  |   2915.1 |      5 |      2819.8 |    2829.5 |     56.3 |   2775.7 |   2903.5 |
| Q12     | trino      |  12407.2 |      5 |      8705   |    8900.6 |    474.6 |   8639.5 |   9745.5 |
| Q13     | clickhouse |   7821   |      5 |      6264   |    6384.7 |    295.7 |   6113.1 |   6825.1 |
| Q13     | duckdb     |   7723.4 |      5 |      7373.1 |    7383.5 |     39.6 |   7338.7 |   7446.2 |
| Q13     | exasol     |   3256.6 |      5 |      3014.7 |    3030.4 |     36.4 |   2994.6 |   3083.5 |
| Q13     | starrocks  |   5871.2 |      5 |      5874   |    5843.2 |     87   |   5707.7 |   5927.5 |
| Q13     | trino      |  35620.9 |      5 |     33873.5 |   34356.6 |   1361.3 |  33058.9 |  36339.6 |
| Q14     | clickhouse |    648.7 |      5 |       554.9 |     569.1 |     45.9 |    525.1 |    626   |
| Q14     | duckdb     |   2176.2 |      5 |      2129.8 |    2113.2 |     27.5 |   2081.7 |   2139.4 |
| Q14     | exasol     |    462   |      5 |       292   |     292.1 |      2.8 |    288.7 |    295.3 |
| Q14     | starrocks  |   2007   |      5 |      2009.5 |    2018.7 |     50   |   1978.3 |   2104.4 |
| Q14     | trino      |  19350.5 |      5 |     12068.6 |   14200.2 |   4769.9 |  11870   |  22728.9 |
| Q15     | clickhouse |    499.9 |      5 |       462.8 |     465   |      7.1 |    456.1 |    472.6 |
| Q15     | duckdb     |   1756.4 |      5 |      1768.9 |    1766   |     13   |   1743.8 |   1776.6 |
| Q15     | exasol     |    761.5 |      5 |       696   |     695.6 |      3.3 |    690.4 |    699.7 |
| Q15     | starrocks  |   2150.9 |      5 |      2183.2 |    2169.2 |     52.6 |   2108   |   2236.1 |
| Q15     | trino      |  23897.8 |      5 |     23190.4 |   23176.5 |     49.6 |  23104.3 |  23227.9 |
| Q16     | clickhouse |   1952.2 |      5 |      1661.9 |    1746.1 |    127.6 |   1655.5 |   1943.3 |
| Q16     | duckdb     |   1279.9 |      5 |      1276.5 |    1273.6 |     19.9 |   1250.7 |   1297.8 |
| Q16     | exasol     |   1069.1 |      5 |      1027.9 |    1027.9 |     15.4 |   1013   |   1052.3 |
| Q16     | starrocks  |   1248.6 |      5 |       725.7 |     723.7 |     20.9 |    701.3 |    750.7 |
| Q16     | trino      |   9349.3 |      5 |      5004.4 |    5014.6 |     45.5 |   4976.6 |   5091.2 |
| Q17     | clickhouse |   3789   |      5 |      3365.6 |    3364.8 |     62.7 |   3273.4 |   3450.6 |
| Q17     | duckdb     |   3310.5 |      5 |      3179.1 |    3201.7 |     37.6 |   3175.3 |   3261.4 |
| Q17     | exasol     |     71.2 |      5 |        37.5 |      37.5 |      0.2 |     37.3 |     37.8 |
| Q17     | starrocks  |   2041.7 |      5 |      2003.9 |    2001.5 |     11.9 |   1986.4 |   2015.2 |
| Q17     | trino      |  25250.8 |      5 |     23953.6 |   24045.4 |    910.7 |  23066.2 |  25485.8 |
| Q18     | clickhouse |  21261.9 |      5 |     20040   |   19725.4 |   1427.9 |  18113.9 |  21302.6 |
| Q18     | duckdb     |   6013.8 |      5 |      5886.1 |    5888.5 |     32.3 |   5840.4 |   5921.9 |
| Q18     | exasol     |   1928.5 |      5 |      1861.9 |    1860.2 |      5.7 |   1852.2 |   1867.4 |
| Q18     | starrocks  |   9434.9 |      5 |      9689   |    9675.6 |    229.4 |   9410.6 |   9934.2 |
| Q18     | trino      |  54927.2 |      5 |     27738.3 |   34312.8 |  16129.8 |  24705   |  63002.8 |
| Q19     | clickhouse |  20520.5 |      5 |     19083.8 |   19101.6 |     91.5 |  18989.6 |  19195.3 |
| Q19     | duckdb     |   3011.3 |      5 |      2951.1 |    2950.1 |     10.1 |   2933.1 |   2958   |
| Q19     | exasol     |    141.4 |      5 |        86.7 |      86.7 |      0.4 |     86.2 |     87.3 |
| Q19     | starrocks  |   2901.7 |      5 |      2809.6 |    2799.6 |     41.8 |   2747.9 |   2853.8 |
| Q19     | trino      |  26471.1 |      5 |     28049.9 |   28053.8 |     23.5 |  28034   |  28093.9 |
| Q20     | clickhouse |   5438.7 |      5 |      3852   |    3903.2 |    142   |   3772   |   4133.7 |
| Q20     | duckdb     |   2712.1 |      5 |      2699.9 |    2702.1 |     13.3 |   2684.1 |   2720   |
| Q20     | exasol     |    717.6 |      5 |       601.6 |     602.8 |      5.1 |    597.6 |    611.4 |
| Q20     | starrocks  |   2473.7 |      5 |      2510.9 |    2513.4 |     28.5 |   2487.9 |   2560.6 |
| Q20     | trino      |  27315.5 |      5 |     19235.2 |   20773.7 |   3465.6 |  19109.9 |  26971.7 |
| Q21     | clickhouse |  15794   |      5 |     13209.6 |   13129.4 |    233   |  12727.1 |  13314.4 |
| Q21     | duckdb     |  13293.7 |      5 |     13317.8 |   13286.1 |     65.6 |  13197.4 |  13345.4 |
| Q21     | exasol     |   1874.8 |      5 |      1841.5 |    1849.4 |     20.7 |   1831.4 |   1884   |
| Q21     | starrocks  |  15698.4 |      5 |     14646.8 |   14737.1 |    233.4 |  14574.7 |  15145.9 |
| Q21     | trino      |  63267.6 |      5 |     63096.3 |   62932.9 |   3236.8 |  59475.9 |  66960.1 |
| Q22     | clickhouse |   2281.9 |      5 |      1679.7 |    1740.4 |    179.2 |   1571.4 |   2004.2 |
| Q22     | duckdb     |   1506.2 |      5 |      1507.8 |    1501.3 |     19.5 |   1473.8 |   1519.1 |
| Q22     | exasol     |    359   |      5 |       343.4 |     344.3 |      1.9 |    342.5 |    346.3 |
| Q22     | starrocks  |    994.6 |      5 |       860.1 |     866.9 |     31.1 |    842.2 |    918.7 |
| Q22     | trino      |  10856.3 |      5 |      9589   |    9655.8 |    368   |   9280.8 |  10082.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3122   |          8930.6 |    2.86 |      0.35 | False    |
| Q02     | exasol            | clickhouse          |          85.2 |          2839.1 |   33.32 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        1105.4 |         11557.2 |   10.46 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |         205.1 |          9770.2 |   47.64 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         825.1 |         16565.5 |   20.08 |      0.05 | False    |
| Q06     | exasol            | clickhouse          |         136.1 |           702.2 |    5.16 |      0.19 | False    |
| Q07     | exasol            | clickhouse          |        1116.8 |         23258   |   20.83 |      0.05 | False    |
| Q08     | exasol            | clickhouse          |         254.6 |         18983.3 |   74.56 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        4011.6 |          7427.4 |    1.85 |      0.54 | False    |
| Q10     | exasol            | clickhouse          |        1244.8 |          8443.9 |    6.78 |      0.15 | False    |
| Q11     | exasol            | clickhouse          |         231.8 |          1799.9 |    7.76 |      0.13 | False    |
| Q12     | exasol            | clickhouse          |         287.6 |          2611.9 |    9.08 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |        3014.7 |          6264   |    2.08 |      0.48 | False    |
| Q14     | exasol            | clickhouse          |         292   |           554.9 |    1.9  |      0.53 | False    |
| Q15     | exasol            | clickhouse          |         696   |           462.8 |    0.66 |      1.5  | True     |
| Q16     | exasol            | clickhouse          |        1027.9 |          1661.9 |    1.62 |      0.62 | False    |
| Q17     | exasol            | clickhouse          |          37.5 |          3365.6 |   89.75 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        1861.9 |         20040   |   10.76 |      0.09 | False    |
| Q19     | exasol            | clickhouse          |          86.7 |         19083.8 |  220.11 |      0    | False    |
| Q20     | exasol            | clickhouse          |         601.6 |          3852   |    6.4  |      0.16 | False    |
| Q21     | exasol            | clickhouse          |        1841.5 |         13209.6 |    7.17 |      0.14 | False    |
| Q22     | exasol            | clickhouse          |         343.4 |          1679.7 |    4.89 |      0.2  | False    |
| Q01     | exasol            | duckdb              |        3122   |          3755.1 |    1.2  |      0.83 | False    |
| Q02     | exasol            | duckdb              |          85.2 |           760   |    8.92 |      0.11 | False    |
| Q03     | exasol            | duckdb              |        1105.4 |          2506.2 |    2.27 |      0.44 | False    |
| Q04     | exasol            | duckdb              |         205.1 |          2451.3 |   11.95 |      0.08 | False    |
| Q05     | exasol            | duckdb              |         825.1 |          2747.3 |    3.33 |      0.3  | False    |
| Q06     | exasol            | duckdb              |         136.1 |           815.7 |    5.99 |      0.17 | False    |
| Q07     | exasol            | duckdb              |        1116.8 |          2619.3 |    2.35 |      0.43 | False    |
| Q08     | exasol            | duckdb              |         254.6 |          2660.3 |   10.45 |      0.1  | False    |
| Q09     | exasol            | duckdb              |        4011.6 |          8960.5 |    2.23 |      0.45 | False    |
| Q10     | exasol            | duckdb              |        1244.8 |          4077.2 |    3.28 |      0.31 | False    |
| Q11     | exasol            | duckdb              |         231.8 |           388   |    1.67 |      0.6  | False    |
| Q12     | exasol            | duckdb              |         287.6 |          3107.3 |   10.8  |      0.09 | False    |
| Q13     | exasol            | duckdb              |        3014.7 |          7373.1 |    2.45 |      0.41 | False    |
| Q14     | exasol            | duckdb              |         292   |          2129.8 |    7.29 |      0.14 | False    |
| Q15     | exasol            | duckdb              |         696   |          1768.9 |    2.54 |      0.39 | False    |
| Q16     | exasol            | duckdb              |        1027.9 |          1276.5 |    1.24 |      0.81 | False    |
| Q17     | exasol            | duckdb              |          37.5 |          3179.1 |   84.78 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        1861.9 |          5886.1 |    3.16 |      0.32 | False    |
| Q19     | exasol            | duckdb              |          86.7 |          2951.1 |   34.04 |      0.03 | False    |
| Q20     | exasol            | duckdb              |         601.6 |          2699.9 |    4.49 |      0.22 | False    |
| Q21     | exasol            | duckdb              |        1841.5 |         13317.8 |    7.23 |      0.14 | False    |
| Q22     | exasol            | duckdb              |         343.4 |          1507.8 |    4.39 |      0.23 | False    |
| Q01     | exasol            | starrocks           |        3122   |         10064.7 |    3.22 |      0.31 | False    |
| Q02     | exasol            | starrocks           |          85.2 |           432.4 |    5.08 |      0.2  | False    |
| Q03     | exasol            | starrocks           |        1105.4 |          5983.4 |    5.41 |      0.18 | False    |
| Q04     | exasol            | starrocks           |         205.1 |          4100.6 |   19.99 |      0.05 | False    |
| Q05     | exasol            | starrocks           |         825.1 |          5916.8 |    7.17 |      0.14 | False    |
| Q06     | exasol            | starrocks           |         136.1 |          1954.5 |   14.36 |      0.07 | False    |
| Q07     | exasol            | starrocks           |        1116.8 |          4928.9 |    4.41 |      0.23 | False    |
| Q08     | exasol            | starrocks           |         254.6 |          3812.6 |   14.97 |      0.07 | False    |
| Q09     | exasol            | starrocks           |        4011.6 |         10073.9 |    2.51 |      0.4  | False    |
| Q10     | exasol            | starrocks           |        1244.8 |          4633.6 |    3.72 |      0.27 | False    |
| Q11     | exasol            | starrocks           |         231.8 |           357.5 |    1.54 |      0.65 | False    |
| Q12     | exasol            | starrocks           |         287.6 |          2819.8 |    9.8  |      0.1  | False    |
| Q13     | exasol            | starrocks           |        3014.7 |          5874   |    1.95 |      0.51 | False    |
| Q14     | exasol            | starrocks           |         292   |          2009.5 |    6.88 |      0.15 | False    |
| Q15     | exasol            | starrocks           |         696   |          2183.2 |    3.14 |      0.32 | False    |
| Q16     | exasol            | starrocks           |        1027.9 |           725.7 |    0.71 |      1.42 | True     |
| Q17     | exasol            | starrocks           |          37.5 |          2003.9 |   53.44 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        1861.9 |          9689   |    5.2  |      0.19 | False    |
| Q19     | exasol            | starrocks           |          86.7 |          2809.6 |   32.41 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         601.6 |          2510.9 |    4.17 |      0.24 | False    |
| Q21     | exasol            | starrocks           |        1841.5 |         14646.8 |    7.95 |      0.13 | False    |
| Q22     | exasol            | starrocks           |         343.4 |           860.1 |    2.5  |      0.4  | False    |
| Q01     | exasol            | trino               |        3122   |         17424.5 |    5.58 |      0.18 | False    |
| Q02     | exasol            | trino               |          85.2 |          5801.4 |   68.09 |      0.01 | False    |
| Q03     | exasol            | trino               |        1105.4 |         21775   |   19.7  |      0.05 | False    |
| Q04     | exasol            | trino               |         205.1 |         18546.5 |   90.43 |      0.01 | False    |
| Q05     | exasol            | trino               |         825.1 |         21955.3 |   26.61 |      0.04 | False    |
| Q06     | exasol            | trino               |         136.1 |          7775.1 |   57.13 |      0.02 | False    |
| Q07     | exasol            | trino               |        1116.8 |         17672.7 |   15.82 |      0.06 | False    |
| Q08     | exasol            | trino               |         254.6 |         18151.8 |   71.3  |      0.01 | False    |
| Q09     | exasol            | trino               |        4011.6 |         57436.2 |   14.32 |      0.07 | False    |
| Q10     | exasol            | trino               |        1244.8 |         21514.2 |   17.28 |      0.06 | False    |
| Q11     | exasol            | trino               |         231.8 |          3088.1 |   13.32 |      0.08 | False    |
| Q12     | exasol            | trino               |         287.6 |          8705   |   30.27 |      0.03 | False    |
| Q13     | exasol            | trino               |        3014.7 |         33873.5 |   11.24 |      0.09 | False    |
| Q14     | exasol            | trino               |         292   |         12068.6 |   41.33 |      0.02 | False    |
| Q15     | exasol            | trino               |         696   |         23190.4 |   33.32 |      0.03 | False    |
| Q16     | exasol            | trino               |        1027.9 |          5004.4 |    4.87 |      0.21 | False    |
| Q17     | exasol            | trino               |          37.5 |         23953.6 |  638.76 |      0    | False    |
| Q18     | exasol            | trino               |        1861.9 |         27738.3 |   14.9  |      0.07 | False    |
| Q19     | exasol            | trino               |          86.7 |         28049.9 |  323.53 |      0    | False    |
| Q20     | exasol            | trino               |         601.6 |         19235.2 |   31.97 |      0.03 | False    |
| Q21     | exasol            | trino               |        1841.5 |         63096.3 |   34.26 |      0.03 | False    |
| Q22     | exasol            | trino               |         343.4 |          9589   |   27.92 |      0.04 | False    |


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

**clickhouse:**
- Median runtime: 6937.7ms
- Average runtime: 8361.4ms
- Fastest query: 456.1ms
- Slowest query: 24385.3ms

**duckdb:**
- Median runtime: 2686.6ms
- Average runtime: 3494.9ms
- Fastest query: 384.4ms
- Slowest query: 13345.4ms

**exasol:**
- Median runtime: 650.9ms
- Average runtime: 1022.6ms
- Fastest query: 37.3ms
- Slowest query: 4035.9ms

**starrocks:**
- Median runtime: 3335.4ms
- Average runtime: 4470.9ms
- Fastest query: 340.2ms
- Slowest query: 15145.9ms

**trino:**
- Median runtime: 19234.7ms
- Average runtime: 21787.3ms
- Fastest query: 2905.0ms
- Slowest query: 67001.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_single_streams_1-benchmark.zip`](ext_scalability_single_streams_1-benchmark.zip)

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

**Exasol 2025.2.0:**
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
  - max_memory_usage: 20000000000
  - max_bytes_before_external_group_by: 10000000000
  - max_bytes_before_external_sort: 10000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 15000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 24GB
  - query_max_memory_per_node: 24GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 4
  - replication_num: 1

**Duckdb 1.4.4:**
- **Setup method:** native
- **Data directory:** /data/duckdb
- **Applied configurations:**
  - memory_limit: 24GB
  - threads: 4


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 1 concurrent streams (round-robin distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts