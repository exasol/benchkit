# Extended Scalability - Scale Factor 25 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-29 20:25:48

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
- exasol was the fastest overall with 819.0ms median runtime
- trino was 45.1x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

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
- **Hostname:** ip-10-0-1-129

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
- **Hostname:** ip-10-0-1-224

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
- **Hostname:** ip-10-0-1-75

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
- **Hostname:** ip-10-0-1-64

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
- **Hostname:** ip-10-0-1-148


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
sudo parted /dev/nvme0n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mklabel gpt

# Create 42GB partition for data generation
sudo parted /dev/nvme0n1 mkpart primary ext4 1MiB 42GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary ext4 1MiB 42GiB

# Create raw partition for Exasol (178GB)
sudo parted /dev/nvme0n1 mkpart primary 42GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary 42GiB 100%

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS458A782624240458B with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS458A782624240458B

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS458A782624240458B to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS458A782624240458B /data

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
node.id=254b7daa-6182-480e-ba10-fd22685c4a01
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222B3F7A09C528EA9 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222B3F7A09C528EA9

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222B3F7A09C528EA9 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222B3F7A09C528EA9 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2E69CCEB41CA5ADA3 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2E69CCEB41CA5ADA3

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2E69CCEB41CA5ADA3 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2E69CCEB41CA5ADA3 /data

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
    &lt;max_server_memory_usage&gt;26472841216&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
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
            &lt;max_memory_usage&gt;7000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;2500000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;2500000000&lt;/max_bytes_before_external_group_by&gt;
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
- Max memory usage: `7.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64761E174FB9E54D1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64761E174FB9E54D1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64761E174FB9E54D1 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64761E174FB9E54D1 /data

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
- **Scale factor:** 25
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (4 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_sf_25-benchmark.zip
cd ext_scalability_sf_25

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
| Q01     | clickhouse |   4633.1 |      5 |     17078.1 |   16375.6 |   3532.7 |  12050.2 |  20035.9 |
| Q01     | duckdb     |   2304.1 |      5 |      5886.6 |    6616.1 |   3269   |   4415.8 |  12319.7 |
| Q01     | exasol     |   1569.7 |      5 |      3431.7 |    3613.5 |   1587.5 |   1564.3 |   6014.2 |
| Q01     | starrocks  |   6993.9 |      5 |     36948.5 |   30990   |  12603.4 |  10353.3 |  41622.9 |
| Q01     | trino      |  12189.1 |      5 |     31689.8 |   26401.7 |   9564.8 |  13634.2 |  35380.8 |
| Q02     | clickhouse |   2015.9 |      5 |     10040   |   10607.9 |   3001.4 |   7338.9 |  15523.5 |
| Q02     | duckdb     |    463.5 |      5 |      4028.8 |    4353.3 |   1622.2 |   2975.6 |   7105.8 |
| Q02     | exasol     |     65.4 |      5 |       168.9 |     171.8 |     35.5 |    127.6 |    216.4 |
| Q02     | starrocks  |    499.9 |      5 |      1120.8 |    1169.5 |    127.6 |   1040.3 |   1377.5 |
| Q02     | trino      |   5504.7 |      5 |     21557.7 |   22921.6 |   8286   |  16044.5 |  36745.2 |
| Q03     | clickhouse |   5455.9 |      5 |     12281.5 |   14694.9 |   9622.3 |   5092   |  27163.9 |
| Q03     | duckdb     |   1371.9 |      5 |      9241.8 |    8321.1 |   3278.8 |   3991   |  11400.6 |
| Q03     | exasol     |    560.1 |      5 |       545.9 |    1305.5 |   1048.9 |    543.8 |   2621.5 |
| Q03     | starrocks  |   2173.1 |      5 |      2712.8 |    5358.1 |   3958   |   2103.6 |  10414.6 |
| Q03     | trino      |  13407.6 |      5 |     35998.5 |   36481   |   7403.6 |  26098.4 |  46823   |
| Q04     | clickhouse |   6370.7 |      5 |     20115   |   18728.6 |   3402.2 |  13410.5 |  21559   |
| Q04     | duckdb     |   1292.1 |      5 |      7495.7 |    7660.2 |   1532.8 |   5800.6 |   9642.9 |
| Q04     | exasol     |    109.6 |      5 |       406.8 |     437   |    266.6 |    197.7 |    871.7 |
| Q04     | starrocks  |   1153   |      5 |      1950.2 |    2070.9 |    341.6 |   1844.6 |   2674.5 |
| Q04     | trino      |  10977.8 |      5 |     38943.7 |   37135.8 |   3618.2 |  32979.3 |  40826.7 |
| Q05     | clickhouse |   5097.2 |      5 |     22082.7 |   23133.1 |   3416.8 |  20986.8 |  29162.4 |
| Q05     | duckdb     |   1399.7 |      5 |      5371.3 |    5880.7 |   1188.2 |   4910.6 |   7763.8 |
| Q05     | exasol     |    444.8 |      5 |      1139.9 |    1301.1 |    412.6 |    887.8 |   1760.6 |
| Q05     | starrocks  |   2239.1 |      5 |      6693.7 |    7464.7 |   2229.9 |   5252.7 |  10915   |
| Q05     | trino      |  13265.7 |      5 |     39447.1 |   44924.5 |  15409.4 |  32356.4 |  70463.4 |
| Q06     | clickhouse |    276.2 |      5 |      1933   |    2279.1 |   1119.2 |   1257.6 |   3494.1 |
| Q06     | duckdb     |    408.7 |      5 |      3647.1 |    4347.4 |   1103.5 |   3521.8 |   6000.1 |
| Q06     | exasol     |     70.2 |      5 |       154.4 |     262.3 |    217.8 |     69.8 |    618   |
| Q06     | starrocks  |    840.9 |      5 |      1875.2 |    1724.6 |    433.1 |   1047.8 |   2204.6 |
| Q06     | trino      |   5618.3 |      5 |     24892.2 |   23441.4 |  13523.8 |   9833.4 |  40079.8 |
| Q07     | clickhouse |  12613.7 |      5 |     38194.3 |   34508.3 |  13055.4 |  11691.3 |  44123.7 |
| Q07     | duckdb     |   1267   |      5 |      4786.7 |    5004.8 |   1692.8 |   3549   |   7864   |
| Q07     | exasol     |    550.4 |      5 |      1281.6 |    1700.7 |   1201.4 |    521.8 |   3081.1 |
| Q07     | starrocks  |   2582.6 |      5 |      4395.7 |    5184.2 |   2708.2 |   2452.3 |   9707.3 |
| Q07     | trino      |  11145.6 |      5 |     41089.2 |   46816.5 |  11841.5 |  37141.4 |  66623.2 |
| Q08     | clickhouse |   5722.8 |      5 |     29614.9 |   28642.9 |   4460.6 |  22908   |  34666.7 |
| Q08     | duckdb     |   1358.1 |      5 |      6532.7 |    6837.4 |   2848.8 |   4135   |  11144.9 |
| Q08     | exasol     |    131.8 |      5 |       601.8 |     555.8 |    179.1 |    265.7 |    731.3 |
| Q08     | starrocks  |   2119.2 |      5 |      4186.7 |    4007.9 |    958.9 |   2704.6 |   5051.8 |
| Q08     | trino      |  11022.4 |      5 |     40081.4 |   36037.5 |  15432.8 |   9428.1 |  49781.3 |
| Q09     | clickhouse |   3368.9 |      5 |     13441.2 |   13457.6 |    928.8 |  12089   |  14650.5 |
| Q09     | duckdb     |   4133.1 |      5 |      7625.6 |    7518.3 |   2371.8 |   4123.4 |  10149.3 |
| Q09     | exasol     |   1161.1 |      5 |      4971.3 |    5003.3 |    162.8 |   4777   |   5208.1 |
| Q09     | starrocks  |   5635.9 |      5 |     13981.8 |   16203.4 |   6626.5 |   9228.7 |  26833.3 |
| Q09     | trino      |  27500   |      5 |     60414.7 |   67405.5 |  15834.4 |  51666.4 |  84600.5 |
| Q10     | clickhouse |   8427.2 |      5 |     28944.1 |   30290.1 |   3395.8 |  27013.4 |  34121.1 |
| Q10     | duckdb     |   2069.5 |      5 |      8562.4 |    8477.8 |   4423   |   3031.5 |  13797.7 |
| Q10     | exasol     |    624.3 |      5 |      1855.2 |    1954.6 |    629.8 |   1056.8 |   2612.7 |
| Q10     | starrocks  |   2364.4 |      5 |      3873.7 |    4882.1 |   1706   |   3713.7 |   7641.3 |
| Q10     | trino      |  12614.7 |      5 |     54307.3 |   53939.9 |  18595.1 |  29654.1 |  77926.4 |
| Q11     | clickhouse |   1017.8 |      5 |      4868.9 |    5013.8 |   1172.6 |   3933.2 |   6977.4 |
| Q11     | duckdb     |    205.5 |      5 |      6145.9 |    5835.6 |   2741.3 |   2329.8 |   9537.8 |
| Q11     | exasol     |    117.5 |      5 |       408.6 |     424.6 |    111.9 |    289.6 |    601.4 |
| Q11     | starrocks  |    322.6 |      5 |       886   |     919   |    296.5 |    573.7 |   1391.7 |
| Q11     | trino      |   2224.3 |      5 |      6359.7 |    6069.3 |   2641.8 |   3243.6 |   9663.4 |
| Q12     | clickhouse |   2923.1 |      5 |      4547   |    7603.3 |   4678.4 |   4491.4 |  15075.5 |
| Q12     | duckdb     |   1550.6 |      5 |      8279.6 |    9172.9 |   3678.6 |   5466.4 |  15266.6 |
| Q12     | exasol     |    146.1 |      5 |       577.5 |     730.1 |    234.4 |    536.8 |    998.3 |
| Q12     | starrocks  |   1587.1 |      5 |      3439.5 |    3762.2 |    965.4 |   2830   |   4844.8 |
| Q12     | trino      |   5510.9 |      5 |     35862.8 |   35665.3 |  10329.6 |  21556.3 |  47431.3 |
| Q13     | clickhouse |   3888.8 |      5 |     12167.5 |   12446.7 |   4173.4 |   5851   |  16105.8 |
| Q13     | duckdb     |   3512.2 |      5 |      6469.5 |    6111.9 |   2666   |   3557.1 |   9946.3 |
| Q13     | exasol     |   1418   |      5 |      6185.4 |    5747.4 |   2680.7 |   1425.1 |   8816.9 |
| Q13     | starrocks  |   2756.7 |      5 |      8697.2 |   11522   |   8261.2 |   2851.2 |  23457.2 |
| Q13     | trino      |  17197.2 |      5 |     42931.3 |   44101.9 |   3127.3 |  41607.6 |  49492.9 |
| Q14     | clickhouse |    280.2 |      5 |      2391.7 |    2263.3 |   1022.8 |   1251   |   3695.2 |
| Q14     | duckdb     |   1020   |      5 |      6737.7 |    6785.7 |   3142.3 |   3139.2 |  10062.7 |
| Q14     | exasol     |    134.8 |      5 |       717.9 |     695.3 |    258.4 |    346.4 |   1049.2 |
| Q14     | starrocks  |   1028.8 |      5 |      2637   |    2372.7 |    574.8 |   1720.8 |   2983.1 |
| Q14     | trino      |   7244.7 |      5 |     36424.2 |   30238.6 |  12376.2 |  11921.2 |  41353.9 |
| Q15     | clickhouse |    338.6 |      5 |      3271.6 |    3286.5 |    479.9 |   2747.6 |   3949.7 |
| Q15     | duckdb     |    910.7 |      5 |      4322.6 |    4202.5 |   2233.2 |    906.3 |   6309.9 |
| Q15     | exasol     |    281.3 |      5 |       920.3 |     879   |    278.4 |    433.2 |   1184.6 |
| Q15     | starrocks  |    600.6 |      5 |      2434.7 |    2816.7 |   1383.6 |   1381.6 |   4948.6 |
| Q15     | trino      |  12745   |      5 |     35131.1 |   32887.4 |  13541.3 |  15123.9 |  48457.8 |
| Q16     | clickhouse |   1541.6 |      5 |      6134.3 |    5850.7 |   2107.7 |   3438.3 |   8945.3 |
| Q16     | duckdb     |    639.6 |      5 |      4000.8 |    4901.2 |   2508.6 |   3378.1 |   9332.6 |
| Q16     | exasol     |    541.4 |      5 |      2008.4 |    2216.9 |    435.7 |   1833.9 |   2883.8 |
| Q16     | starrocks  |    763.1 |      5 |      1404.3 |    1414   |    193.5 |   1151.2 |   1677.2 |
| Q16     | trino      |   4149.2 |      5 |     10002.1 |   11956.2 |   4656   |   7304.1 |  19394.5 |
| Q17     | clickhouse |   2044.8 |      5 |      9846.2 |    9262.2 |   2155.4 |   6308.2 |  11471.3 |
| Q17     | duckdb     |   1602.1 |      5 |      6757.5 |    6916.5 |   3469.5 |   1609.6 |  10338.6 |
| Q17     | exasol     |     22.9 |      5 |        80.2 |      88.7 |     43.4 |     48.5 |    159.6 |
| Q17     | starrocks  |    874.3 |      5 |      1581.2 |    1729.2 |    435.4 |   1247.8 |   2301.6 |
| Q17     | trino      |  35668.1 |      5 |    183908   |  163230   |  72572.3 |  35306.2 | 207987   |
| Q18     | clickhouse |   6138.5 |      5 |     28110.7 |   27303.1 |   3975.8 |  23160.1 |  32725.3 |
| Q18     | duckdb     |   2741.9 |      5 |      7507.3 |    8393.6 |   2107.1 |   6514.5 |  11417   |
| Q18     | exasol     |    923.3 |      5 |      3421.9 |    2706.9 |   1198.3 |    920   |   3662.3 |
| Q18     | starrocks  |   3960.1 |      5 |     17378.2 |   19032.4 |   6576.4 |  11025.2 |  28558.9 |
| Q18     | trino      |  14319.3 |      5 |     59378.4 |   55529.8 |  20206.2 |  26803.5 |  77211   |
| Q19     | clickhouse |   9770.6 |      5 |     34476   |   31664.1 |   7542.6 |  18449.3 |  36598.9 |
| Q19     | duckdb     |   1483.2 |      5 |      6964.3 |    6910.5 |   2775.8 |   4353.3 |  11067.6 |
| Q19     | exasol     |     43   |      5 |       166.5 |     132.3 |     68   |     49.1 |    192.4 |
| Q19     | starrocks  |   1381.2 |      5 |      2094.3 |    2349.2 |    999.3 |   1546.7 |   4065.2 |
| Q19     | trino      |   8261.4 |      5 |     38948.9 |   37989.3 |   6837.8 |  26602.6 |  43406.9 |
| Q20     | clickhouse |   2226.8 |      5 |      9266.5 |    9598.1 |   1217.7 |   8540.2 |  11688.7 |
| Q20     | duckdb     |   1383.5 |      5 |      5737.9 |    6337.6 |   2335.9 |   3453.9 |   9576.5 |
| Q20     | exasol     |    294.5 |      5 |       923.8 |     915.8 |    294.9 |    487.9 |   1286.9 |
| Q20     | starrocks  |   1232.4 |      5 |      2229.5 |    2025.2 |    955.6 |   1016.3 |   3302.8 |
| Q20     | trino      |   8144.3 |      5 |     27490.6 |   27647.2 |   5650.7 |  20835   |  33659.5 |
| Q21     | clickhouse |   3920.5 |      5 |     14313.5 |   14151.3 |   1791.6 |  11541.9 |  16468.2 |
| Q21     | duckdb     |   6378.4 |      5 |      9986.2 |   10272.3 |   1645.9 |   8894.9 |  13097.1 |
| Q21     | exasol     |    806.5 |      5 |      1270.8 |    2063.5 |   1523.2 |    807.1 |   3883.7 |
| Q21     | starrocks  |   4922.9 |      5 |     16724.3 |   17402.4 |   8253.4 |   5154.5 |  27369.4 |
| Q21     | trino      |  30409.2 |      5 |     70933.9 |   74558.2 |  14767.3 |  59088.1 |  98857.2 |
| Q22     | clickhouse |    830.2 |      5 |      4873.7 |    5787.4 |   3201   |   2046.7 |   9345.6 |
| Q22     | duckdb     |    727.2 |      5 |      5348.2 |    6456.7 |   3568   |   2958.2 |  11064.9 |
| Q22     | exasol     |    177.8 |      5 |       716.7 |     593.2 |    246.3 |    175.9 |    765.1 |
| Q22     | starrocks  |    575.7 |      5 |      2038.1 |    3138.8 |   2961.1 |    510.6 |   7629.4 |
| Q22     | trino      |   4744.5 |      5 |     15306.7 |   18055   |   7331.6 |  13237.8 |  31050.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3431.7 |         17078.1 |    4.98 |      0.2  | False    |
| Q02     | exasol            | clickhouse          |         168.9 |         10040   |   59.44 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         545.9 |         12281.5 |   22.5  |      0.04 | False    |
| Q04     | exasol            | clickhouse          |         406.8 |         20115   |   49.45 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1139.9 |         22082.7 |   19.37 |      0.05 | False    |
| Q06     | exasol            | clickhouse          |         154.4 |          1933   |   12.52 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        1281.6 |         38194.3 |   29.8  |      0.03 | False    |
| Q08     | exasol            | clickhouse          |         601.8 |         29614.9 |   49.21 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        4971.3 |         13441.2 |    2.7  |      0.37 | False    |
| Q10     | exasol            | clickhouse          |        1855.2 |         28944.1 |   15.6  |      0.06 | False    |
| Q11     | exasol            | clickhouse          |         408.6 |          4868.9 |   11.92 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |         577.5 |          4547   |    7.87 |      0.13 | False    |
| Q13     | exasol            | clickhouse          |        6185.4 |         12167.5 |    1.97 |      0.51 | False    |
| Q14     | exasol            | clickhouse          |         717.9 |          2391.7 |    3.33 |      0.3  | False    |
| Q15     | exasol            | clickhouse          |         920.3 |          3271.6 |    3.55 |      0.28 | False    |
| Q16     | exasol            | clickhouse          |        2008.4 |          6134.3 |    3.05 |      0.33 | False    |
| Q17     | exasol            | clickhouse          |          80.2 |          9846.2 |  122.77 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3421.9 |         28110.7 |    8.21 |      0.12 | False    |
| Q19     | exasol            | clickhouse          |         166.5 |         34476   |  207.06 |      0    | False    |
| Q20     | exasol            | clickhouse          |         923.8 |          9266.5 |   10.03 |      0.1  | False    |
| Q21     | exasol            | clickhouse          |        1270.8 |         14313.5 |   11.26 |      0.09 | False    |
| Q22     | exasol            | clickhouse          |         716.7 |          4873.7 |    6.8  |      0.15 | False    |
| Q01     | exasol            | duckdb              |        3431.7 |          5886.6 |    1.72 |      0.58 | False    |
| Q02     | exasol            | duckdb              |         168.9 |          4028.8 |   23.85 |      0.04 | False    |
| Q03     | exasol            | duckdb              |         545.9 |          9241.8 |   16.93 |      0.06 | False    |
| Q04     | exasol            | duckdb              |         406.8 |          7495.7 |   18.43 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1139.9 |          5371.3 |    4.71 |      0.21 | False    |
| Q06     | exasol            | duckdb              |         154.4 |          3647.1 |   23.62 |      0.04 | False    |
| Q07     | exasol            | duckdb              |        1281.6 |          4786.7 |    3.73 |      0.27 | False    |
| Q08     | exasol            | duckdb              |         601.8 |          6532.7 |   10.86 |      0.09 | False    |
| Q09     | exasol            | duckdb              |        4971.3 |          7625.6 |    1.53 |      0.65 | False    |
| Q10     | exasol            | duckdb              |        1855.2 |          8562.4 |    4.62 |      0.22 | False    |
| Q11     | exasol            | duckdb              |         408.6 |          6145.9 |   15.04 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         577.5 |          8279.6 |   14.34 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        6185.4 |          6469.5 |    1.05 |      0.96 | False    |
| Q14     | exasol            | duckdb              |         717.9 |          6737.7 |    9.39 |      0.11 | False    |
| Q15     | exasol            | duckdb              |         920.3 |          4322.6 |    4.7  |      0.21 | False    |
| Q16     | exasol            | duckdb              |        2008.4 |          4000.8 |    1.99 |      0.5  | False    |
| Q17     | exasol            | duckdb              |          80.2 |          6757.5 |   84.26 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3421.9 |          7507.3 |    2.19 |      0.46 | False    |
| Q19     | exasol            | duckdb              |         166.5 |          6964.3 |   41.83 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         923.8 |          5737.9 |    6.21 |      0.16 | False    |
| Q21     | exasol            | duckdb              |        1270.8 |          9986.2 |    7.86 |      0.13 | False    |
| Q22     | exasol            | duckdb              |         716.7 |          5348.2 |    7.46 |      0.13 | False    |
| Q01     | exasol            | starrocks           |        3431.7 |         36948.5 |   10.77 |      0.09 | False    |
| Q02     | exasol            | starrocks           |         168.9 |          1120.8 |    6.64 |      0.15 | False    |
| Q03     | exasol            | starrocks           |         545.9 |          2712.8 |    4.97 |      0.2  | False    |
| Q04     | exasol            | starrocks           |         406.8 |          1950.2 |    4.79 |      0.21 | False    |
| Q05     | exasol            | starrocks           |        1139.9 |          6693.7 |    5.87 |      0.17 | False    |
| Q06     | exasol            | starrocks           |         154.4 |          1875.2 |   12.15 |      0.08 | False    |
| Q07     | exasol            | starrocks           |        1281.6 |          4395.7 |    3.43 |      0.29 | False    |
| Q08     | exasol            | starrocks           |         601.8 |          4186.7 |    6.96 |      0.14 | False    |
| Q09     | exasol            | starrocks           |        4971.3 |         13981.8 |    2.81 |      0.36 | False    |
| Q10     | exasol            | starrocks           |        1855.2 |          3873.7 |    2.09 |      0.48 | False    |
| Q11     | exasol            | starrocks           |         408.6 |           886   |    2.17 |      0.46 | False    |
| Q12     | exasol            | starrocks           |         577.5 |          3439.5 |    5.96 |      0.17 | False    |
| Q13     | exasol            | starrocks           |        6185.4 |          8697.2 |    1.41 |      0.71 | False    |
| Q14     | exasol            | starrocks           |         717.9 |          2637   |    3.67 |      0.27 | False    |
| Q15     | exasol            | starrocks           |         920.3 |          2434.7 |    2.65 |      0.38 | False    |
| Q16     | exasol            | starrocks           |        2008.4 |          1404.3 |    0.7  |      1.43 | True     |
| Q17     | exasol            | starrocks           |          80.2 |          1581.2 |   19.72 |      0.05 | False    |
| Q18     | exasol            | starrocks           |        3421.9 |         17378.2 |    5.08 |      0.2  | False    |
| Q19     | exasol            | starrocks           |         166.5 |          2094.3 |   12.58 |      0.08 | False    |
| Q20     | exasol            | starrocks           |         923.8 |          2229.5 |    2.41 |      0.41 | False    |
| Q21     | exasol            | starrocks           |        1270.8 |         16724.3 |   13.16 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         716.7 |          2038.1 |    2.84 |      0.35 | False    |
| Q01     | exasol            | trino               |        3431.7 |         31689.8 |    9.23 |      0.11 | False    |
| Q02     | exasol            | trino               |         168.9 |         21557.7 |  127.64 |      0.01 | False    |
| Q03     | exasol            | trino               |         545.9 |         35998.5 |   65.94 |      0.02 | False    |
| Q04     | exasol            | trino               |         406.8 |         38943.7 |   95.73 |      0.01 | False    |
| Q05     | exasol            | trino               |        1139.9 |         39447.1 |   34.61 |      0.03 | False    |
| Q06     | exasol            | trino               |         154.4 |         24892.2 |  161.22 |      0.01 | False    |
| Q07     | exasol            | trino               |        1281.6 |         41089.2 |   32.06 |      0.03 | False    |
| Q08     | exasol            | trino               |         601.8 |         40081.4 |   66.6  |      0.02 | False    |
| Q09     | exasol            | trino               |        4971.3 |         60414.7 |   12.15 |      0.08 | False    |
| Q10     | exasol            | trino               |        1855.2 |         54307.3 |   29.27 |      0.03 | False    |
| Q11     | exasol            | trino               |         408.6 |          6359.7 |   15.56 |      0.06 | False    |
| Q12     | exasol            | trino               |         577.5 |         35862.8 |   62.1  |      0.02 | False    |
| Q13     | exasol            | trino               |        6185.4 |         42931.3 |    6.94 |      0.14 | False    |
| Q14     | exasol            | trino               |         717.9 |         36424.2 |   50.74 |      0.02 | False    |
| Q15     | exasol            | trino               |         920.3 |         35131.1 |   38.17 |      0.03 | False    |
| Q16     | exasol            | trino               |        2008.4 |         10002.1 |    4.98 |      0.2  | False    |
| Q17     | exasol            | trino               |          80.2 |        183908   | 2293.12 |      0    | False    |
| Q18     | exasol            | trino               |        3421.9 |         59378.4 |   17.35 |      0.06 | False    |
| Q19     | exasol            | trino               |         166.5 |         38948.9 |  233.93 |      0    | False    |
| Q20     | exasol            | trino               |         923.8 |         27490.6 |   29.76 |      0.03 | False    |
| Q21     | exasol            | trino               |        1270.8 |         70933.9 |   55.82 |      0.02 | False    |
| Q22     | exasol            | trino               |         716.7 |         15306.7 |   21.36 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 15776.9 | 12847.8 | 1257.6 | 41485.1 |
| 1 | 28 | 14229.1 | 10956.6 | 1251.0 | 37046.9 |
| 2 | 27 | 15604.0 | 13410.5 | 1269.3 | 34666.7 |
| 3 | 27 | 13824.7 | 9846.2 | 2927.9 | 44123.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 9846.2ms
- Slowest stream median: 13410.5ms
- Stream performance variation: 36.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6601.2 | 6240.2 | 906.3 | 13097.1 |
| 1 | 28 | 6658.7 | 6091.6 | 2975.6 | 11144.9 |
| 2 | 27 | 6729.7 | 6514.5 | 3031.5 | 13797.7 |
| 3 | 27 | 6799.7 | 6532.7 | 1609.6 | 15266.6 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6091.6ms
- Slowest stream median: 6532.7ms
- Stream performance variation: 7.2% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1847.7 | 1025.2 | 69.8 | 8816.9 |
| 1 | 28 | 1207.8 | 717.3 | 60.9 | 5208.1 |
| 2 | 27 | 1583.2 | 923.8 | 49.1 | 6395.3 |
| 3 | 27 | 1451.8 | 765.1 | 48.5 | 6014.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 717.3ms
- Slowest stream median: 1025.2ms
- Stream performance variation: 42.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7241.4 | 4672.1 | 510.6 | 28558.9 |
| 1 | 28 | 6130.4 | 2655.8 | 831.0 | 41622.9 |
| 2 | 27 | 6758.8 | 2830.0 | 573.7 | 38148.9 |
| 3 | 27 | 6696.3 | 2962.8 | 886.0 | 36948.5 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2655.8ms
- Slowest stream median: 4672.1ms
- Stream performance variation: 75.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 41108.5 | 40837.1 | 7304.1 | 98857.2 |
| 1 | 28 | 45010.0 | 37462.3 | 6359.7 | 207110.6 |
| 2 | 27 | 38531.5 | 37797.3 | 3243.6 | 84232.6 |
| 3 | 27 | 45018.4 | 32979.3 | 3755.3 | 207986.8 |

**Performance Analysis for Trino:**
- Fastest stream median: 32979.3ms
- Slowest stream median: 40837.1ms
- Stream performance variation: 23.8% difference between fastest and slowest streams
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

**clickhouse:**
- Median runtime: 12101.8ms
- Average runtime: 14861.3ms
- Fastest query: 1251.0ms
- Slowest query: 44123.7ms

**duckdb:**
- Median runtime: 6314.5ms
- Average runtime: 6696.1ms
- Fastest query: 906.3ms
- Slowest query: 15266.6ms

**exasol:**
- Median runtime: 819.0ms
- Average runtime: 1522.7ms
- Fastest query: 48.5ms
- Slowest query: 8816.9ms

**starrocks:**
- Median runtime: 2907.0ms
- Average runtime: 6706.3ms
- Fastest query: 510.6ms
- Slowest query: 41622.9ms

**trino:**
- Median runtime: 36943.3ms
- Average runtime: 42428.8ms
- Fastest query: 3243.6ms
- Slowest query: 207986.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_sf_25-benchmark.zip`](ext_scalability_sf_25-benchmark.zip)

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
  - max_memory_usage: 7000000000
  - max_bytes_before_external_group_by: 2500000000
  - max_bytes_before_external_sort: 2500000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 5000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 24GB
  - query_max_memory_per_node: 18GB

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts