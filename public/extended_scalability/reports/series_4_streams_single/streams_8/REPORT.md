# Extended Scalability - Single Node Stream Scaling (8 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-01-30 10:11:22

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
- exasol was the fastest overall with 1815.4ms median runtime
- trino was 36.9x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 8 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-222

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
- **Hostname:** ip-10-0-1-168

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-59

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-97

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-103


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.2xlarge
- **Clickhouse Instance:** r6id.2xlarge
- **Trino Instance:** r6id.2xlarge
- **Starrocks Instance:** r6id.2xlarge
- **Duckdb Instance:** r6id.2xlarge


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

# Create raw partition for Exasol (371GB)
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



#### Trino 479 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS252DF31E34E27367E with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS252DF31E34E27367E

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS252DF31E34E27367E to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS252DF31E34E27367E /data

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
node.id=4220b6f8-d722-453e-8e6f-0ec00dd28d37
node.data-dir=/var/trino/data
EOF

# Configure JVM with 49G heap (80% of 61.8G total RAM)
sudo tee /etc/trino/jvm.config &gt; /dev/null &lt;&lt; &#39;EOF&#39;
-server
-Xmx49G
-Xms49G
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
query.max-memory=48GB
query.max-memory-per-node=34GB
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3C4EB5BED9D665C43 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3C4EB5BED9D665C43

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3C4EB5BED9D665C43 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3C4EB5BED9D665C43 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24C717EF801CB106D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24C717EF801CB106D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24C717EF801CB106D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24C717EF801CB106D /data

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
    &lt;max_server_memory_usage&gt;53066930585&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;18&lt;/max_concurrent_queries&gt;
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
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `7.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS142B4E250DFC6E615 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS142B4E250DFC6E615

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS142B4E250DFC6E615 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS142B4E250DFC6E615 /data

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
- Memory limit: `48GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (8 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_single_streams_8-benchmark.zip
cd ext_scalability_single_streams_8

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
| Q01     | clickhouse |   4521.7 |      5 |     26469.6 |   25676.9 |  11395.7 |  10677.1 |  38880.7 |
| Q01     | duckdb     |   2251.2 |      5 |     13089.2 |   11657.7 |   8156.7 |   1889.1 |  22967.5 |
| Q01     | exasol     |   1568.5 |      5 |     11293.2 |    9596.5 |   2834   |   5737.9 |  11881.9 |
| Q01     | starrocks  |   6916.5 |      5 |     60128.1 |   48397.8 |  33067.8 |   8694.2 |  82807.2 |
| Q01     | trino      |  10405.1 |      5 |     65787.1 |   64422   |   5732.5 |  57105.9 |  71618.9 |
| Q02     | clickhouse |   1887.4 |      5 |     17446.9 |   17833   |   3976.1 |  12709   |  23380.6 |
| Q02     | duckdb     |    466.9 |      5 |     13258.7 |   11887.7 |   4881.5 |   4078.3 |  16262.7 |
| Q02     | exasol     |     86.6 |      5 |       438   |     400.4 |     71.9 |    297.5 |    464.6 |
| Q02     | starrocks  |    496   |      5 |       972.2 |    1007.5 |    207.3 |    804.8 |   1348.7 |
| Q02     | trino      |   4734.1 |      5 |     39338.1 |   42518.5 |  14731.6 |  28936.1 |  66902.1 |
| Q03     | clickhouse |   1885.4 |      5 |     16034.1 |   14534.4 |   4192.9 |   7235.8 |  17649   |
| Q03     | duckdb     |   1388.1 |      5 |     13222.6 |   12171.7 |   4350.4 |   7210.9 |  16570.3 |
| Q03     | exasol     |    614.1 |      5 |      2638.2 |    2973.1 |   1883.3 |   1159.1 |   6102.2 |
| Q03     | starrocks  |   3279.1 |      5 |      6632.7 |   11361.6 |  10912.4 |   5151.8 |  30784   |
| Q03     | trino      |  13373.7 |      5 |    108241   |   87561.1 |  48981.7 |  12355.6 | 132707   |
| Q04     | clickhouse |   5524.7 |      5 |     27795.8 |   25972.4 |   6039.6 |  18769.8 |  33213.5 |
| Q04     | duckdb     |   1322.5 |      5 |     14086.4 |   16397.4 |   8071.9 |   8267.2 |  28835   |
| Q04     | exasol     |    110.5 |      5 |      1064.3 |     930.2 |    315   |    445.1 |   1262.4 |
| Q04     | starrocks  |   1553   |      5 |      4315.3 |    6277.5 |   5254.9 |   2466.1 |  15517.6 |
| Q04     | trino      |   9484   |      5 |     71834.5 |   72612   |  10911   |  62389.4 |  90496.9 |
| Q05     | clickhouse |   1947.4 |      5 |     20593.6 |   19704.8 |   2386   |  16527.6 |  22413.1 |
| Q05     | duckdb     |   1455.7 |      5 |     13067.8 |   12884.2 |   7118.8 |   1359.9 |  19693.9 |
| Q05     | exasol     |    482.4 |      5 |      3851.7 |    3184.6 |   1263.7 |   1666.5 |   4492.8 |
| Q05     | starrocks  |   2682.3 |      5 |     12741   |   11752.4 |   3929   |   7642.4 |  16924.1 |
| Q05     | trino      |  12420.9 |      5 |     95962.5 |   90893.2 |   9551   |  78128.4 | 100744   |
| Q06     | clickhouse |    303.3 |      5 |      6178.7 |    5813.5 |   1627   |   4056.9 |   7556.2 |
| Q06     | duckdb     |    407.7 |      5 |      8486   |    9920.6 |   5969.2 |   2536.6 |  17920.3 |
| Q06     | exasol     |     71.1 |      5 |       641.2 |     695.4 |    630.3 |    132.8 |   1739.8 |
| Q06     | starrocks  |   1448.6 |      5 |      3937.3 |    3783.4 |    997.3 |   2618.5 |   5142.5 |
| Q06     | trino      |   4290.3 |      5 |     46852.5 |   46786.1 |   6066.2 |  37901.8 |  54881.5 |
| Q07     | clickhouse |   1841.8 |      5 |     13807.5 |   15795   |   3720.8 |  12892.2 |  21311.9 |
| Q07     | duckdb     |   1313.8 |      5 |      8561.5 |    9267.5 |   1384.6 |   8365.9 |  11673.7 |
| Q07     | exasol     |    602.1 |      5 |      4547.5 |    4037.8 |   2524.4 |    569.7 |   6763.3 |
| Q07     | starrocks  |   3279.6 |      5 |      7816.9 |    9510.5 |   3875.9 |   6237.8 |  14856.1 |
| Q07     | trino      |   9774.6 |      5 |     61810.6 |   54835.4 |  26261.4 |  10257.6 |  75431   |
| Q08     | clickhouse |   1595.7 |      5 |     15546.4 |   15310   |   1977.5 |  13160.2 |  17523.7 |
| Q08     | duckdb     |   1408.2 |      5 |     14050.6 |   16983.8 |   8971.8 |   5417.5 |  27746.8 |
| Q08     | exasol     |    160   |      5 |      1506.7 |    1267.6 |    554.1 |    642.4 |   1791   |
| Q08     | starrocks  |   2908.5 |      5 |      6046.2 |    6849.9 |   2150.3 |   4807   |   9767.2 |
| Q08     | trino      |  13249.6 |      5 |     93432.1 |   87810.1 |   9536.6 |  74377.6 |  96276.9 |
| Q09     | clickhouse |   1599.8 |      5 |     20077.2 |   19810   |   3008.1 |  15328.6 |  22731.6 |
| Q09     | duckdb     |   4323   |      5 |     18391.5 |   18012.3 |   3866.5 |  11776.1 |  21379.6 |
| Q09     | exasol     |   2002.3 |      5 |     18692.3 |   17515   |   2629.3 |  12829   |  18991.8 |
| Q09     | starrocks  |   5861.1 |      5 |     13584   |   16292.3 |   4722   |  13018.4 |  24093.2 |
| Q09     | trino      |  29603.5 |      5 |    152891   |  141461   |  18459.5 | 116708   | 156893   |
| Q10     | clickhouse |   2545.9 |      5 |     21846.1 |   23734.7 |   3935   |  20965.9 |  30523.3 |
| Q10     | duckdb     |   2114.7 |      5 |     14757.3 |   15195.6 |   2398.4 |  12365.3 |  18996   |
| Q10     | exasol     |    712.7 |      5 |      1891.4 |    2611   |   1709.9 |   1156.2 |   5065.9 |
| Q10     | starrocks  |   2982   |      5 |      6193.5 |    6090.7 |    804.1 |   4951.6 |   7088.5 |
| Q10     | trino      |  11886.2 |      5 |     79392.9 |   85852.5 |  14658.8 |  70132.2 | 106922   |
| Q11     | clickhouse |    957.2 |      5 |     12324.7 |   12941.1 |   3661   |   8260.8 |  17311.1 |
| Q11     | duckdb     |    197.1 |      5 |     13202.3 |   11637.1 |   3458.8 |   6132.8 |  14553.4 |
| Q11     | exasol     |    151.8 |      5 |      1022.3 |    1850   |   2299.6 |    540.5 |   5939.6 |
| Q11     | starrocks  |    342.4 |      5 |       944.6 |     899.3 |    347.2 |    454.8 |   1366.3 |
| Q11     | trino      |   2009.7 |      5 |     18049.9 |   16948.6 |   3843.1 |  11591.2 |  20519.3 |
| Q12     | clickhouse |   1964.8 |      5 |     20312.9 |   20981.6 |   3196.7 |  16359.8 |  24110.8 |
| Q12     | duckdb     |   1501.4 |      5 |     14559.8 |   12950.1 |   3744.9 |   7221.5 |  16201.9 |
| Q12     | exasol     |    147.9 |      5 |      1576.9 |    1535.7 |    342.1 |   1114.8 |   1885   |
| Q12     | starrocks  |   2027.9 |      5 |      5858.8 |    6419.1 |   3700   |   3443.7 |  12634.7 |
| Q12     | trino      |   6311.1 |      5 |     63715.4 |   64922.2 |   7828.5 |  54797.6 |  74670.8 |
| Q13     | clickhouse |   5260.4 |      5 |     26464.6 |   26623   |   5399.9 |  19416.8 |  34498.3 |
| Q13     | duckdb     |   3617.5 |      5 |     11591.2 |   10897.2 |   4343.9 |   3667.7 |  14319.8 |
| Q13     | exasol     |   1468.8 |      5 |     11466.7 |    9507.5 |   4671.4 |   2481.5 |  14061.1 |
| Q13     | starrocks  |   3243.6 |      5 |     11856.2 |   17517.2 |  11633.1 |   6562   |  35385.5 |
| Q13     | trino      |  15278.1 |      5 |    174204   |  145950   |  73992   |  14909.9 | 195950   |
| Q14     | clickhouse |    339.2 |      5 |      6449.8 |    6076.4 |    989.1 |   4352.9 |   6851.5 |
| Q14     | duckdb     |   1043.8 |      5 |     15096.9 |   14530.3 |   4142.3 |   9550.1 |  19961.8 |
| Q14     | exasol     |    144.7 |      5 |      1840   |    1806.8 |    987.6 |    508.6 |   3095.7 |
| Q14     | starrocks  |   1473.2 |      5 |      3419.1 |    4799   |   4259.9 |   2214.4 |  12357.6 |
| Q14     | trino      |   6414.6 |      5 |     59286   |   57448.9 |  11109.4 |  47014.5 |  73953.1 |
| Q15     | clickhouse |    322.7 |      5 |      5654.1 |    5918.5 |   1545.3 |   3767.6 |   7502.6 |
| Q15     | duckdb     |    905.8 |      5 |     13801.3 |   11148   |   7246.2 |    901.4 |  19381.3 |
| Q15     | exasol     |    390.4 |      5 |      2628.6 |    2736   |    418.9 |   2425.2 |   3466.4 |
| Q15     | starrocks  |    792.6 |      5 |      3786.8 |    3840.4 |   1362.3 |   2351.4 |   5567.8 |
| Q15     | trino      |  11479.2 |      5 |     60539.4 |   67133.5 |  10806.6 |  57933   |  79621.3 |
| Q16     | clickhouse |   1343.9 |      5 |     12314.1 |   13149.5 |   2398.8 |  10981.6 |  15837.2 |
| Q16     | duckdb     |    642   |      5 |     10890.5 |    9455.8 |   6588.5 |    619.3 |  17028.9 |
| Q16     | exasol     |    574.3 |      5 |      3920.7 |    3585.7 |    682.3 |   2388.4 |   4010.8 |
| Q16     | starrocks  |    736.3 |      5 |      1517   |    1521.8 |    431.1 |   1063.7 |   2199.2 |
| Q16     | trino      |   3131.8 |      5 |     26707.8 |   26456.7 |   4764.5 |  20271.8 |  32960.7 |
| Q17     | clickhouse |   1807.6 |      5 |     16190.8 |   14951.6 |   3553.3 |   9268   |  18644.7 |
| Q17     | duckdb     |   1601.9 |      5 |     14595.9 |   13381.3 |   8936   |   2023.5 |  26416.8 |
| Q17     | exasol     |     28.3 |      5 |       256.5 |     277.4 |    183.3 |    100.8 |    527   |
| Q17     | starrocks  |   1089.3 |      5 |      3123.6 |    5194.3 |   3095.2 |   2888.8 |   9385.5 |
| Q17     | trino      |  12940.6 |      5 |     95633.4 |   97351.8 |  12080.4 |  85134.6 | 117528   |
| Q18     | clickhouse |   2256.4 |      5 |     19626.9 |   19043.8 |   4453.5 |  13634.8 |  24674.9 |
| Q18     | duckdb     |   2952.2 |      5 |     16861.4 |   16480.1 |   2215.3 |  13899   |  19009.7 |
| Q18     | exasol     |    979.4 |      5 |      6835.1 |    5606.9 |   2315.6 |   1699.2 |   7298.6 |
| Q18     | starrocks  |   4574.7 |      5 |     41782.3 |   47600.2 |  25074.7 |  12450.5 |  77478.4 |
| Q18     | trino      |  12577.5 |      5 |    120054   |  138924   |  37083.7 | 110386   | 201606   |
| Q19     | clickhouse |   9490.5 |      5 |     44462   |   41088.6 |   9365.8 |  29944   |  49858.7 |
| Q19     | duckdb     |   1523.6 |      5 |     16414.4 |   15086   |   4160.5 |   8217.9 |  18636.9 |
| Q19     | exasol     |     58.7 |      5 |       205.1 |     254.6 |    111   |    154.2 |    405.7 |
| Q19     | starrocks  |   2114.8 |      5 |      3529.1 |    3402.1 |    932.7 |   2132.2 |   4368.2 |
| Q19     | trino      |   7275.5 |      5 |     48417.9 |   51398   |  21483.5 |  19805.2 |  74653.7 |
| Q20     | clickhouse |   3217.8 |      5 |     25025.1 |   22979.1 |   6399   |  14772.8 |  31300.4 |
| Q20     | duckdb     |   1367.1 |      5 |     14321.7 |   14474.9 |   5102.6 |   6791.6 |  19830.3 |
| Q20     | exasol     |    341.7 |      5 |      1717   |    1635.1 |    969.1 |    611   |   2910   |
| Q20     | starrocks  |   1606.1 |      5 |      2979.3 |    3343.1 |    835.6 |   2509.1 |   4663.2 |
| Q20     | trino      |   7298.8 |      5 |     61472.6 |   55758.6 |  11940   |  39511.9 |  66659.7 |
| Q21     | clickhouse |   1838.8 |      5 |     15956.8 |   16474.6 |   4567.5 |  10622.9 |  22388.8 |
| Q21     | duckdb     |   6772.9 |      5 |     17194.1 |   16588.3 |   2798.9 |  12892.6 |  20455.5 |
| Q21     | exasol     |    831   |      5 |      5475.1 |    4613.1 |   2942.4 |   1511.9 |   8131.6 |
| Q21     | starrocks  |   5120.8 |      5 |     47230.9 |   43534.2 |  25837.7 |  15867.6 |  69628.7 |
| Q21     | trino      |  30402.2 |      5 |    139878   |  131773   |  53918.4 |  42245.3 | 184119   |
| Q22     | clickhouse |    824.9 |      5 |     10525.5 |   11806.2 |   3044.6 |   9258.1 |  16574.7 |
| Q22     | duckdb     |    778.1 |      5 |     11713.4 |   10049.5 |   8220.2 |    760.6 |  20504.3 |
| Q22     | exasol     |    176.7 |      5 |      1348.5 |    1295.1 |    231.7 |   1042.2 |   1607.3 |
| Q22     | starrocks  |    611.1 |      5 |      3169.4 |    3559.2 |   2005.3 |   1430.7 |   6885   |
| Q22     | trino      |   4546.6 |      5 |     43930.2 |   46440   |   6059.9 |  41891.5 |  56491.4 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |       11293.2 |         26469.6 |    2.34 |      0.43 | False    |
| Q02     | exasol            | clickhouse          |         438   |         17446.9 |   39.83 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        2638.2 |         16034.1 |    6.08 |      0.16 | False    |
| Q04     | exasol            | clickhouse          |        1064.3 |         27795.8 |   26.12 |      0.04 | False    |
| Q05     | exasol            | clickhouse          |        3851.7 |         20593.6 |    5.35 |      0.19 | False    |
| Q06     | exasol            | clickhouse          |         641.2 |          6178.7 |    9.64 |      0.1  | False    |
| Q07     | exasol            | clickhouse          |        4547.5 |         13807.5 |    3.04 |      0.33 | False    |
| Q08     | exasol            | clickhouse          |        1506.7 |         15546.4 |   10.32 |      0.1  | False    |
| Q09     | exasol            | clickhouse          |       18692.3 |         20077.2 |    1.07 |      0.93 | False    |
| Q10     | exasol            | clickhouse          |        1891.4 |         21846.1 |   11.55 |      0.09 | False    |
| Q11     | exasol            | clickhouse          |        1022.3 |         12324.7 |   12.06 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |        1576.9 |         20312.9 |   12.88 |      0.08 | False    |
| Q13     | exasol            | clickhouse          |       11466.7 |         26464.6 |    2.31 |      0.43 | False    |
| Q14     | exasol            | clickhouse          |        1840   |          6449.8 |    3.51 |      0.29 | False    |
| Q15     | exasol            | clickhouse          |        2628.6 |          5654.1 |    2.15 |      0.46 | False    |
| Q16     | exasol            | clickhouse          |        3920.7 |         12314.1 |    3.14 |      0.32 | False    |
| Q17     | exasol            | clickhouse          |         256.5 |         16190.8 |   63.12 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |        6835.1 |         19626.9 |    2.87 |      0.35 | False    |
| Q19     | exasol            | clickhouse          |         205.1 |         44462   |  216.78 |      0    | False    |
| Q20     | exasol            | clickhouse          |        1717   |         25025.1 |   14.57 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        5475.1 |         15956.8 |    2.91 |      0.34 | False    |
| Q22     | exasol            | clickhouse          |        1348.5 |         10525.5 |    7.81 |      0.13 | False    |
| Q01     | exasol            | duckdb              |       11293.2 |         13089.2 |    1.16 |      0.86 | False    |
| Q02     | exasol            | duckdb              |         438   |         13258.7 |   30.27 |      0.03 | False    |
| Q03     | exasol            | duckdb              |        2638.2 |         13222.6 |    5.01 |      0.2  | False    |
| Q04     | exasol            | duckdb              |        1064.3 |         14086.4 |   13.24 |      0.08 | False    |
| Q05     | exasol            | duckdb              |        3851.7 |         13067.8 |    3.39 |      0.29 | False    |
| Q06     | exasol            | duckdb              |         641.2 |          8486   |   13.23 |      0.08 | False    |
| Q07     | exasol            | duckdb              |        4547.5 |          8561.5 |    1.88 |      0.53 | False    |
| Q08     | exasol            | duckdb              |        1506.7 |         14050.6 |    9.33 |      0.11 | False    |
| Q09     | exasol            | duckdb              |       18692.3 |         18391.5 |    0.98 |      1.02 | True     |
| Q10     | exasol            | duckdb              |        1891.4 |         14757.3 |    7.8  |      0.13 | False    |
| Q11     | exasol            | duckdb              |        1022.3 |         13202.3 |   12.91 |      0.08 | False    |
| Q12     | exasol            | duckdb              |        1576.9 |         14559.8 |    9.23 |      0.11 | False    |
| Q13     | exasol            | duckdb              |       11466.7 |         11591.2 |    1.01 |      0.99 | False    |
| Q14     | exasol            | duckdb              |        1840   |         15096.9 |    8.2  |      0.12 | False    |
| Q15     | exasol            | duckdb              |        2628.6 |         13801.3 |    5.25 |      0.19 | False    |
| Q16     | exasol            | duckdb              |        3920.7 |         10890.5 |    2.78 |      0.36 | False    |
| Q17     | exasol            | duckdb              |         256.5 |         14595.9 |   56.9  |      0.02 | False    |
| Q18     | exasol            | duckdb              |        6835.1 |         16861.4 |    2.47 |      0.41 | False    |
| Q19     | exasol            | duckdb              |         205.1 |         16414.4 |   80.03 |      0.01 | False    |
| Q20     | exasol            | duckdb              |        1717   |         14321.7 |    8.34 |      0.12 | False    |
| Q21     | exasol            | duckdb              |        5475.1 |         17194.1 |    3.14 |      0.32 | False    |
| Q22     | exasol            | duckdb              |        1348.5 |         11713.4 |    8.69 |      0.12 | False    |
| Q01     | exasol            | starrocks           |       11293.2 |         60128.1 |    5.32 |      0.19 | False    |
| Q02     | exasol            | starrocks           |         438   |           972.2 |    2.22 |      0.45 | False    |
| Q03     | exasol            | starrocks           |        2638.2 |          6632.7 |    2.51 |      0.4  | False    |
| Q04     | exasol            | starrocks           |        1064.3 |          4315.3 |    4.05 |      0.25 | False    |
| Q05     | exasol            | starrocks           |        3851.7 |         12741   |    3.31 |      0.3  | False    |
| Q06     | exasol            | starrocks           |         641.2 |          3937.3 |    6.14 |      0.16 | False    |
| Q07     | exasol            | starrocks           |        4547.5 |          7816.9 |    1.72 |      0.58 | False    |
| Q08     | exasol            | starrocks           |        1506.7 |          6046.2 |    4.01 |      0.25 | False    |
| Q09     | exasol            | starrocks           |       18692.3 |         13584   |    0.73 |      1.38 | True     |
| Q10     | exasol            | starrocks           |        1891.4 |          6193.5 |    3.27 |      0.31 | False    |
| Q11     | exasol            | starrocks           |        1022.3 |           944.6 |    0.92 |      1.08 | True     |
| Q12     | exasol            | starrocks           |        1576.9 |          5858.8 |    3.72 |      0.27 | False    |
| Q13     | exasol            | starrocks           |       11466.7 |         11856.2 |    1.03 |      0.97 | False    |
| Q14     | exasol            | starrocks           |        1840   |          3419.1 |    1.86 |      0.54 | False    |
| Q15     | exasol            | starrocks           |        2628.6 |          3786.8 |    1.44 |      0.69 | False    |
| Q16     | exasol            | starrocks           |        3920.7 |          1517   |    0.39 |      2.58 | True     |
| Q17     | exasol            | starrocks           |         256.5 |          3123.6 |   12.18 |      0.08 | False    |
| Q18     | exasol            | starrocks           |        6835.1 |         41782.3 |    6.11 |      0.16 | False    |
| Q19     | exasol            | starrocks           |         205.1 |          3529.1 |   17.21 |      0.06 | False    |
| Q20     | exasol            | starrocks           |        1717   |          2979.3 |    1.74 |      0.58 | False    |
| Q21     | exasol            | starrocks           |        5475.1 |         47230.9 |    8.63 |      0.12 | False    |
| Q22     | exasol            | starrocks           |        1348.5 |          3169.4 |    2.35 |      0.43 | False    |
| Q01     | exasol            | trino               |       11293.2 |         65787.1 |    5.83 |      0.17 | False    |
| Q02     | exasol            | trino               |         438   |         39338.1 |   89.81 |      0.01 | False    |
| Q03     | exasol            | trino               |        2638.2 |        108241   |   41.03 |      0.02 | False    |
| Q04     | exasol            | trino               |        1064.3 |         71834.5 |   67.49 |      0.01 | False    |
| Q05     | exasol            | trino               |        3851.7 |         95962.5 |   24.91 |      0.04 | False    |
| Q06     | exasol            | trino               |         641.2 |         46852.5 |   73.07 |      0.01 | False    |
| Q07     | exasol            | trino               |        4547.5 |         61810.6 |   13.59 |      0.07 | False    |
| Q08     | exasol            | trino               |        1506.7 |         93432.1 |   62.01 |      0.02 | False    |
| Q09     | exasol            | trino               |       18692.3 |        152891   |    8.18 |      0.12 | False    |
| Q10     | exasol            | trino               |        1891.4 |         79392.9 |   41.98 |      0.02 | False    |
| Q11     | exasol            | trino               |        1022.3 |         18049.9 |   17.66 |      0.06 | False    |
| Q12     | exasol            | trino               |        1576.9 |         63715.4 |   40.41 |      0.02 | False    |
| Q13     | exasol            | trino               |       11466.7 |        174204   |   15.19 |      0.07 | False    |
| Q14     | exasol            | trino               |        1840   |         59286   |   32.22 |      0.03 | False    |
| Q15     | exasol            | trino               |        2628.6 |         60539.4 |   23.03 |      0.04 | False    |
| Q16     | exasol            | trino               |        3920.7 |         26707.8 |    6.81 |      0.15 | False    |
| Q17     | exasol            | trino               |         256.5 |         95633.4 |  372.84 |      0    | False    |
| Q18     | exasol            | trino               |        6835.1 |        120054   |   17.56 |      0.06 | False    |
| Q19     | exasol            | trino               |         205.1 |         48417.9 |  236.07 |      0    | False    |
| Q20     | exasol            | trino               |        1717   |         61472.6 |   35.8  |      0.03 | False    |
| Q21     | exasol            | trino               |        5475.1 |        139878   |   25.55 |      0.04 | False    |
| Q22     | exasol            | trino               |        1348.5 |         43930.2 |   32.58 |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **8 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 19533.6 | 18079.4 | 7235.8 | 34498.3 |
| 1 | 14 | 14433.7 | 16012.0 | 4176.6 | 24674.9 |
| 2 | 14 | 19104.8 | 19441.3 | 7099.1 | 31300.4 |
| 3 | 14 | 19512.9 | 16216.9 | 5654.1 | 49858.7 |
| 4 | 14 | 17528.2 | 15522.5 | 3767.6 | 44462.0 |
| 5 | 14 | 16335.7 | 16060.5 | 7334.1 | 29315.7 |
| 6 | 13 | 20954.6 | 21616.3 | 4352.9 | 48892.2 |
| 7 | 13 | 16799.9 | 16498.4 | 6178.7 | 33213.5 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 15522.5ms
- Slowest stream median: 21616.3ms
- Stream performance variation: 39.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 12246.5 | 13421.4 | 619.3 | 20455.5 |
| 1 | 14 | 13614.6 | 13833.9 | 4078.3 | 26416.8 |
| 2 | 14 | 13334.1 | 13100.7 | 5909.8 | 21379.6 |
| 3 | 14 | 13100.5 | 13846.5 | 1889.1 | 19693.9 |
| 4 | 14 | 12027.2 | 13817.6 | 760.6 | 17920.3 |
| 5 | 14 | 13812.5 | 14274.4 | 2023.5 | 27746.8 |
| 6 | 13 | 13048.8 | 14390.0 | 1359.9 | 21035.6 |
| 7 | 13 | 14750.4 | 16262.7 | 2536.6 | 28835.0 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 13100.7ms
- Slowest stream median: 16262.7ms
- Stream performance variation: 24.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 4189.5 | 2470.3 | 569.7 | 12334.9 |
| 1 | 14 | 2983.0 | 1387.7 | 256.5 | 18709.1 |
| 2 | 14 | 4096.7 | 1675.8 | 132.8 | 18352.8 |
| 3 | 14 | 3485.6 | 2824.7 | 100.8 | 11293.2 |
| 4 | 14 | 3549.0 | 2647.3 | 272.7 | 11881.9 |
| 5 | 14 | 3044.9 | 1542.3 | 111.5 | 11671.1 |
| 6 | 13 | 3766.4 | 1576.9 | 154.2 | 18692.3 |
| 7 | 13 | 3210.3 | 1348.5 | 464.6 | 18991.8 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1348.5ms
- Slowest stream median: 2824.7ms
- Stream performance variation: 109.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 14363.6 | 7990.8 | 1517.0 | 65216.1 |
| 1 | 14 | 10276.3 | 4501.9 | 1041.6 | 41782.3 |
| 2 | 14 | 11883.7 | 4807.4 | 1253.9 | 72154.0 |
| 3 | 14 | 14421.1 | 3695.7 | 893.5 | 82807.2 |
| 4 | 14 | 14240.0 | 6280.1 | 689.1 | 69628.7 |
| 5 | 14 | 12270.8 | 5265.9 | 804.8 | 60128.1 |
| 6 | 13 | 12209.4 | 5132.5 | 454.8 | 77478.4 |
| 7 | 13 | 5512.9 | 5142.5 | 1018.4 | 13305.8 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3695.7ms
- Slowest stream median: 7990.8ms
- Stream performance variation: 116.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 82751.5 | 71123.4 | 10257.6 | 195950.1 |
| 1 | 14 | 78686.2 | 70457.1 | 11591.2 | 201605.8 |
| 2 | 14 | 77833.6 | 65187.6 | 19805.2 | 160187.4 |
| 3 | 14 | 71245.4 | 64915.3 | 18049.9 | 139877.5 |
| 4 | 14 | 79539.4 | 71655.6 | 20135.5 | 184118.7 |
| 5 | 14 | 70165.5 | 69260.5 | 33714.0 | 143218.5 |
| 6 | 13 | 81895.3 | 73953.1 | 14447.2 | 168084.2 |
| 7 | 13 | 66811.4 | 59286.0 | 28410.1 | 152891.4 |

**Performance Analysis for Trino:**
- Fastest stream median: 59286.0ms
- Slowest stream median: 73953.1ms
- Stream performance variation: 24.7% difference between fastest and slowest streams
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
- Median runtime: 16818.2ms
- Average runtime: 18009.9ms
- Fastest query: 3767.6ms
- Slowest query: 49858.7ms

**duckdb:**
- Median runtime: 13974.8ms
- Average runtime: 13229.9ms
- Fastest query: 619.3ms
- Slowest query: 28835.0ms

**exasol:**
- Median runtime: 1815.4ms
- Average runtime: 3541.6ms
- Fastest query: 100.8ms
- Slowest query: 18991.8ms

**starrocks:**
- Median runtime: 5388.0ms
- Average runtime: 11952.4ms
- Fastest query: 454.8ms
- Slowest query: 82807.2ms

**trino:**
- Median runtime: 67064.0ms
- Average runtime: 76148.1ms
- Fastest query: 10257.6ms
- Slowest query: 201605.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_single_streams_8-benchmark.zip`](ext_scalability_single_streams_8-benchmark.zip)

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
  - memory_limit: 48g
  - max_threads: 8
  - max_memory_usage: 7000000000
  - max_bytes_before_external_group_by: 2500000000
  - max_bytes_before_external_sort: 2500000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 5000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 48GB
  - query_max_memory_per_node: 48GB

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
  - memory_limit: 48GB
  - threads: 8


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 8 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts