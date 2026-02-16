# Extended Scalability - Single Node Stream Scaling (16 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-30 11:18:08

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
- exasol was the fastest overall with 1697.7ms median runtime
- trino was 31.6x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 16 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-45

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
- **Hostname:** ip-10-0-1-132

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-70

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-181

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-112


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.4xlarge
- **Clickhouse Instance:** r6id.4xlarge
- **Trino Instance:** r6id.4xlarge
- **Starrocks Instance:** r6id.4xlarge
- **Duckdb Instance:** r6id.4xlarge


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

# Create raw partition for Exasol (814GB)
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
CCC_PLAY_DB_MEM_SIZE=96000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6412452B7780FE3AE with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6412452B7780FE3AE

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6412452B7780FE3AE to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6412452B7780FE3AE /data

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
node.id=11759e18-61af-4969-b498-250882ff3fc6
node.data-dir=/var/trino/data
EOF

# Configure JVM with 99G heap (80% of 123.8G total RAM)
sudo tee /etc/trino/jvm.config &gt; /dev/null &lt;&lt; &#39;EOF&#39;
-server
-Xmx99G
-Xms99G
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
query.max-memory=96GB
query.max-memory-per-node=69GB
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22CBA4BFF59671B07 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22CBA4BFF59671B07

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22CBA4BFF59671B07 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22CBA4BFF59671B07 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443AE4E13D9A366EB with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443AE4E13D9A366EB

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443AE4E13D9A366EB to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443AE4E13D9A366EB /data

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
    &lt;max_server_memory_usage&gt;106335630131&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;26&lt;/max_concurrent_queries&gt;
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
- Memory limit: `96g`
- Max threads: `16`
- Max memory usage: `7.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66938D0E8EBD2FEB7 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66938D0E8EBD2FEB7

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66938D0E8EBD2FEB7 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66938D0E8EBD2FEB7 /data

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
- Memory limit: `96GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (16 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_single_streams_16-benchmark.zip
cd ext_scalability_single_streams_16

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
| Q01     | clickhouse |   2358.8 |      5 |     24951.7 |   25284.5 |   2887.3 |  20841.5 |  28145.3 |
| Q01     | duckdb     |   1142.8 |      5 |     15549   |   12360.7 |   5901.4 |   3048.2 |  17203.7 |
| Q01     | exasol     |    797.8 |      5 |      6375.3 |    7247.4 |   2430.9 |   5665.7 |  11561.2 |
| Q01     | starrocks  |   3722.3 |      5 |     60867.2 |   50950.9 |  33027   |   6622.2 |  89654.4 |
| Q01     | trino      |   5529.4 |      5 |     51711.5 |   52330.1 |   3389.5 |  48107.9 |  56661.8 |
| Q02     | clickhouse |    981   |      5 |     18017.8 |   15475.1 |   7405.9 |   2402.6 |  20203.6 |
| Q02     | duckdb     |    269   |      5 |     14985.2 |   13055.1 |   6419   |   2124.9 |  18410.4 |
| Q02     | exasol     |     68.9 |      5 |       382.6 |     358.5 |     60.2 |    290.4 |    414.4 |
| Q02     | starrocks  |    376.5 |      5 |      1993.9 |    2846.4 |   2002.6 |   1194.3 |   6152   |
| Q02     | trino      |   3370.5 |      5 |     43331.4 |   41349.7 |   5587.9 |  32080.4 |  46603.5 |
| Q03     | clickhouse |    993.3 |      5 |     19538.3 |   17716.5 |   6013   |  10017.9 |  23461.3 |
| Q03     | duckdb     |    709.8 |      5 |     16237   |   15113.7 |   2274.9 |  12462.4 |  17660   |
| Q03     | exasol     |    296.2 |      5 |      1879.8 |    2239.1 |   1649.3 |    364.2 |   4903.3 |
| Q03     | starrocks  |   1124.3 |      5 |      5636.7 |    5848.2 |   3800.8 |   1679.4 |  10428.1 |
| Q03     | trino      |   8797.8 |      5 |     55129.4 |   68860.7 |  56798.2 |   8072.9 | 129492   |
| Q04     | clickhouse |   4824.7 |      5 |     32122.2 |   27872   |  12124   |   6366   |  34826.4 |
| Q04     | duckdb     |    690.7 |      5 |     15237.2 |   13492.8 |   5663.3 |   3796.7 |  18413.3 |
| Q04     | exasol     |     61.4 |      5 |       912.7 |     739.9 |    360.4 |    233.5 |   1120.3 |
| Q04     | starrocks  |    594.8 |      5 |      9432.6 |    7342.5 |   3804   |   2863   |  10870.9 |
| Q04     | trino      |   4983.6 |      5 |     60708.8 |   62494.4 |  27092.6 |  27600.2 | 103681   |
| Q05     | clickhouse |    837.8 |      5 |     18475.7 |   18047.2 |   1561.2 |  16215.9 |  20134.3 |
| Q05     | duckdb     |    746.1 |      5 |     14140.2 |   14759.7 |   1728.7 |  13130.2 |  16817.6 |
| Q05     | exasol     |    262.9 |      5 |      1803   |    2080.5 |   1132.8 |   1017.9 |   3801.2 |
| Q05     | starrocks  |    774.3 |      5 |      6732.8 |    7111   |   3352.1 |   2897.7 |  11049.3 |
| Q05     | trino      |   6879.8 |      5 |     74908.9 |   66528.1 |  27358.3 |  21015.3 |  87016.6 |
| Q06     | clickhouse |    157.5 |      5 |      5874.6 |    5601.7 |   1036   |   4184.5 |   6924.1 |
| Q06     | duckdb     |    203.9 |      5 |     10218.8 |   11515.4 |   2795.1 |   8947.2 |  15943.9 |
| Q06     | exasol     |     39.5 |      5 |       276.3 |     342.5 |    233.2 |    136.8 |    735.4 |
| Q06     | starrocks  |    335.7 |      5 |      5969.3 |    5166.8 |   2536.3 |   1103.7 |   7478.8 |
| Q06     | trino      |   2422.8 |      5 |     40194.6 |   31004.7 |  15030.3 |   9110.6 |  42401.9 |
| Q07     | clickhouse |   1025.1 |      5 |     19461.6 |   18743.4 |   2729.9 |  14102.9 |  21345.5 |
| Q07     | duckdb     |    670   |      5 |     11846.4 |   11124.7 |   6257.5 |    704.3 |  16639.3 |
| Q07     | exasol     |    249.6 |      5 |      2742.6 |    2355.4 |   1144.6 |    375.6 |   3194.7 |
| Q07     | starrocks  |    880.4 |      5 |      9951.3 |    8466.2 |   3702   |   2111.7 |  11041   |
| Q07     | trino      |   5679.9 |      5 |     74257.5 |   61868.6 |  26877.4 |  15067.7 |  79568.5 |
| Q08     | clickhouse |    930.9 |      5 |     18104.6 |   17819.3 |   1322.1 |  16065.3 |  19536.9 |
| Q08     | duckdb     |    717.2 |      5 |     14061.5 |   15208.6 |   2762.4 |  12915.7 |  19470.4 |
| Q08     | exasol     |     73.3 |      5 |      1235.3 |    1331.5 |    643.1 |    444.7 |   2174.5 |
| Q08     | starrocks  |    705.4 |      5 |     10334.9 |    8539.8 |   4252.3 |   1876.2 |  12068.3 |
| Q08     | trino      |   6011.3 |      5 |     72517.7 |   64778.7 |  25686.4 |  19680.3 |  82894.1 |
| Q09     | clickhouse |    955.6 |      5 |     19885.6 |   19583   |   2164.7 |  15997   |  21289.4 |
| Q09     | duckdb     |   2327.2 |      5 |     17415.8 |   17871   |   2555.6 |  15130.1 |  21463.8 |
| Q09     | exasol     |    926.4 |      5 |     14624.3 |   13612.4 |   3167.2 |   8067.4 |  15644.2 |
| Q09     | starrocks  |   2747.3 |      5 |     11180.9 |   15118.3 |   8365.3 |   6163.9 |  26689.8 |
| Q09     | trino      |  21163   |      5 |    131965   |  133582   |   5257.4 | 128003   | 139536   |
| Q10     | clickhouse |   1441   |      5 |     23733.1 |   23867.1 |   1561.6 |  22303.6 |  26216.4 |
| Q10     | duckdb     |   1135.8 |      5 |     14165.2 |   13943   |   2597.5 |  11195.1 |  17365.4 |
| Q10     | exasol     |    415.1 |      5 |      2152.2 |    3468.5 |   1898.4 |   2055.7 |   5899.4 |
| Q10     | starrocks  |   1140.7 |      5 |      8681.4 |    8202.2 |   3962.5 |   1971   |  11983.8 |
| Q10     | trino      |   5475   |      5 |     82332.7 |   68762.1 |  35984.1 |   6367.1 |  94943.2 |
| Q11     | clickhouse |    508.7 |      5 |     14895.5 |   13065.6 |   4012   |   6361.6 |  16236.9 |
| Q11     | duckdb     |    105.7 |      5 |     13685   |   11511.8 |   5336   |   3208.1 |  16440.9 |
| Q11     | exasol     |    109.7 |      5 |       812.7 |     951.7 |    361.4 |    604.6 |   1549.3 |
| Q11     | starrocks  |    153.8 |      5 |       830.4 |     919.6 |    509.6 |    482.7 |   1736.9 |
| Q11     | trino      |   1227.3 |      5 |     23045.6 |   19792.7 |   6347.3 |   9292.7 |  24428   |
| Q12     | clickhouse |    966.8 |      5 |     17488.6 |   17504.5 |    953.1 |  15996.9 |  18364.8 |
| Q12     | duckdb     |    758.5 |      5 |     13742.8 |   13374.8 |   3525.3 |   8195.6 |  17936.9 |
| Q12     | exasol     |     80.5 |      5 |      1252.1 |    1133.1 |    536.2 |    440.9 |   1743.1 |
| Q12     | starrocks  |    689.6 |      5 |      9511.8 |    6903   |   4141   |   1078.7 |  10102   |
| Q12     | trino      |   4680.8 |      5 |     61588.9 |   58935.2 |   7360.8 |  49923.6 |  66783.9 |
| Q13     | clickhouse |   3295.9 |      5 |     29188.6 |   26533.8 |   8430.8 |  11848.8 |  33225.7 |
| Q13     | duckdb     |   1887.1 |      5 |     13746.9 |   13495   |   8574.3 |   1890.8 |  25551.1 |
| Q13     | exasol     |    623.3 |      5 |      6208.2 |    7848.3 |   4727.6 |   2390.6 |  14494.1 |
| Q13     | starrocks  |   1679.3 |      5 |     21400.1 |   21332.2 |   7514.5 |  10715.3 |  31524.6 |
| Q13     | trino      |   8363.6 |      5 |    228666   |  191050   |  82276.1 |  45205.8 | 238474   |
| Q14     | clickhouse |    214.3 |      5 |      6268.3 |    6116.5 |   1302.2 |   4724.6 |   8093.5 |
| Q14     | duckdb     |    533.1 |      5 |     12089.9 |   12825.5 |   3699.4 |   8750.8 |  18867.4 |
| Q14     | exasol     |     73.9 |      5 |       791.9 |    1015.1 |    400.7 |    669.6 |   1526.1 |
| Q14     | starrocks  |    572.4 |      5 |      9030.9 |    9667.9 |   1777.6 |   8121.4 |  12716.3 |
| Q14     | trino      |   3328.1 |      5 |     46308.7 |   46361.3 |   4381.3 |  40784.8 |  51279.4 |
| Q15     | clickhouse |    236   |      5 |      5383.4 |    5988.4 |   1582.2 |   4313.1 |   8033.4 |
| Q15     | duckdb     |    478.1 |      5 |     14368   |   14195.9 |   3255.6 |  10482.3 |  18420.2 |
| Q15     | exasol     |    259.5 |      5 |      2890.8 |    2551.8 |    594.4 |   1731   |   3021.5 |
| Q15     | starrocks  |    361.5 |      5 |      6313.5 |    6728.9 |   2657.2 |   3431.9 |  10511.3 |
| Q15     | trino      |   5988.9 |      5 |     58057   |   56316.3 |   3619.8 |  52161.4 |  59787.3 |
| Q16     | clickhouse |    822   |      5 |     16221.4 |   15913.2 |   1213.2 |  13791.4 |  16828.5 |
| Q16     | duckdb     |    355.4 |      5 |     12378.2 |   12848.9 |   2755.7 |   9308.2 |  16973.2 |
| Q16     | exasol     |    379   |      5 |      3747.4 |    3372.9 |   1195.9 |   1539.8 |   4441.4 |
| Q16     | starrocks  |    568.7 |      5 |      2359   |    2183.4 |    833.4 |    982.9 |   3260   |
| Q16     | trino      |   2353.7 |      5 |     26005.9 |   26558.7 |   3514.1 |  22585.5 |  31993.5 |
| Q17     | clickhouse |    954.3 |      5 |     21442.8 |   17476.6 |   6424.3 |   9668.4 |  23054.3 |
| Q17     | duckdb     |    821.5 |      5 |     13941.3 |   14450.8 |   1600   |  12697.2 |  16141.7 |
| Q17     | exasol     |     22.7 |      5 |       122.9 |     159.9 |     85.1 |     64.5 |    261.7 |
| Q17     | starrocks  |    400.3 |      5 |      7800.9 |    5581   |   3451.2 |    947.5 |   8476.3 |
| Q17     | trino      |   7766.5 |      5 |     85342.1 |   81526.7 |  18223.1 |  50729.9 |  99275.6 |
| Q18     | clickhouse |    876.5 |      5 |     16337.4 |   15433.4 |   2356   |  12256.7 |  17454.6 |
| Q18     | duckdb     |   1563.6 |      5 |     16925.2 |   16367.1 |   2490.4 |  12399.8 |  18889.6 |
| Q18     | exasol     |    533.2 |      5 |      5578.5 |    5765.6 |   1677.8 |   3327.5 |   7560   |
| Q18     | starrocks  |   3251.5 |      5 |     35763.2 |   38735.1 |  12999.4 |  20275.4 |  52209   |
| Q18     | trino      |   7354.1 |      5 |    117924   |  116038   |  43871.3 |  50657   | 162042   |
| Q19     | clickhouse |   4838.5 |      5 |     40733.5 |   35011.8 |  10855.9 |  20746.7 |  44121.5 |
| Q19     | duckdb     |    774.5 |      5 |     14862.8 |   14533.4 |   2625.1 |  11344.8 |  18003.6 |
| Q19     | exasol     |     23.5 |      5 |       109.4 |     144.5 |     73.9 |     73.3 |    251.1 |
| Q19     | starrocks  |    437.3 |      5 |      5088.5 |    6091.8 |   3135.5 |   2518.7 |  10778.6 |
| Q19     | trino      |   4058   |      5 |     37161.3 |   38537.3 |   6732.4 |  29779.9 |  47912.1 |
| Q20     | clickhouse |   1906.7 |      5 |     25114.4 |   23843   |   2274.1 |  20000.2 |  25323.7 |
| Q20     | duckdb     |    730.3 |      5 |     16074.6 |   13937.5 |   3610.5 |   9982.9 |  17044.5 |
| Q20     | exasol     |    212.2 |      5 |      2084.4 |    1713.7 |    833.6 |    743.7 |   2541.6 |
| Q20     | starrocks  |    603   |      5 |      2812.1 |    4886.3 |   5014.1 |    781.5 |  13030.7 |
| Q20     | trino      |   4190.3 |      5 |     54509.3 |   51050.1 |   7324   |  38247   |  55787.7 |
| Q21     | clickhouse |   1119.5 |      5 |     15773.1 |   15551.9 |   2447.8 |  11872.2 |  18317.9 |
| Q21     | duckdb     |   3645.3 |      5 |     14940.6 |   13056.1 |   3454.4 |   7450.8 |  15806   |
| Q21     | exasol     |    375.8 |      5 |      3243.2 |    3446.8 |   2598.7 |    707.7 |   7535.4 |
| Q21     | starrocks  |   4343.8 |      5 |     16418   |   22434.7 |  14777.1 |   4465.9 |  38649.3 |
| Q21     | trino      |  18565.6 |      5 |    144849   |  134230   |  73779.8 |  18502.5 | 221266   |
| Q22     | clickhouse |    452.9 |      5 |     13457.3 |   12368.3 |   3259.9 |   6954.9 |  15212   |
| Q22     | duckdb     |    415.5 |      5 |     14687.4 |   14235   |   2866.9 |   9469.6 |  16997.4 |
| Q22     | exasol     |     94.8 |      5 |       826.2 |    1141.3 |    535   |    651.3 |   1870.3 |
| Q22     | starrocks  |    344.5 |      5 |      7611.2 |    6774.2 |   2574.2 |   2909   |   9184.9 |
| Q22     | trino      |   2566.4 |      5 |     46965.7 |   43550   |  11047.2 |  24791.2 |  52647.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        6375.3 |         24951.7 |    3.91 |      0.26 | False    |
| Q02     | exasol            | clickhouse          |         382.6 |         18017.8 |   47.09 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |        1879.8 |         19538.3 |   10.39 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |         912.7 |         32122.2 |   35.19 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        1803   |         18475.7 |   10.25 |      0.1  | False    |
| Q06     | exasol            | clickhouse          |         276.3 |          5874.6 |   21.26 |      0.05 | False    |
| Q07     | exasol            | clickhouse          |        2742.6 |         19461.6 |    7.1  |      0.14 | False    |
| Q08     | exasol            | clickhouse          |        1235.3 |         18104.6 |   14.66 |      0.07 | False    |
| Q09     | exasol            | clickhouse          |       14624.3 |         19885.6 |    1.36 |      0.74 | False    |
| Q10     | exasol            | clickhouse          |        2152.2 |         23733.1 |   11.03 |      0.09 | False    |
| Q11     | exasol            | clickhouse          |         812.7 |         14895.5 |   18.33 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |        1252.1 |         17488.6 |   13.97 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        6208.2 |         29188.6 |    4.7  |      0.21 | False    |
| Q14     | exasol            | clickhouse          |         791.9 |          6268.3 |    7.92 |      0.13 | False    |
| Q15     | exasol            | clickhouse          |        2890.8 |          5383.4 |    1.86 |      0.54 | False    |
| Q16     | exasol            | clickhouse          |        3747.4 |         16221.4 |    4.33 |      0.23 | False    |
| Q17     | exasol            | clickhouse          |         122.9 |         21442.8 |  174.47 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        5578.5 |         16337.4 |    2.93 |      0.34 | False    |
| Q19     | exasol            | clickhouse          |         109.4 |         40733.5 |  372.34 |      0    | False    |
| Q20     | exasol            | clickhouse          |        2084.4 |         25114.4 |   12.05 |      0.08 | False    |
| Q21     | exasol            | clickhouse          |        3243.2 |         15773.1 |    4.86 |      0.21 | False    |
| Q22     | exasol            | clickhouse          |         826.2 |         13457.3 |   16.29 |      0.06 | False    |
| Q01     | exasol            | duckdb              |        6375.3 |         15549   |    2.44 |      0.41 | False    |
| Q02     | exasol            | duckdb              |         382.6 |         14985.2 |   39.17 |      0.03 | False    |
| Q03     | exasol            | duckdb              |        1879.8 |         16237   |    8.64 |      0.12 | False    |
| Q04     | exasol            | duckdb              |         912.7 |         15237.2 |   16.69 |      0.06 | False    |
| Q05     | exasol            | duckdb              |        1803   |         14140.2 |    7.84 |      0.13 | False    |
| Q06     | exasol            | duckdb              |         276.3 |         10218.8 |   36.98 |      0.03 | False    |
| Q07     | exasol            | duckdb              |        2742.6 |         11846.4 |    4.32 |      0.23 | False    |
| Q08     | exasol            | duckdb              |        1235.3 |         14061.5 |   11.38 |      0.09 | False    |
| Q09     | exasol            | duckdb              |       14624.3 |         17415.8 |    1.19 |      0.84 | False    |
| Q10     | exasol            | duckdb              |        2152.2 |         14165.2 |    6.58 |      0.15 | False    |
| Q11     | exasol            | duckdb              |         812.7 |         13685   |   16.84 |      0.06 | False    |
| Q12     | exasol            | duckdb              |        1252.1 |         13742.8 |   10.98 |      0.09 | False    |
| Q13     | exasol            | duckdb              |        6208.2 |         13746.9 |    2.21 |      0.45 | False    |
| Q14     | exasol            | duckdb              |         791.9 |         12089.9 |   15.27 |      0.07 | False    |
| Q15     | exasol            | duckdb              |        2890.8 |         14368   |    4.97 |      0.2  | False    |
| Q16     | exasol            | duckdb              |        3747.4 |         12378.2 |    3.3  |      0.3  | False    |
| Q17     | exasol            | duckdb              |         122.9 |         13941.3 |  113.44 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        5578.5 |         16925.2 |    3.03 |      0.33 | False    |
| Q19     | exasol            | duckdb              |         109.4 |         14862.8 |  135.86 |      0.01 | False    |
| Q20     | exasol            | duckdb              |        2084.4 |         16074.6 |    7.71 |      0.13 | False    |
| Q21     | exasol            | duckdb              |        3243.2 |         14940.6 |    4.61 |      0.22 | False    |
| Q22     | exasol            | duckdb              |         826.2 |         14687.4 |   17.78 |      0.06 | False    |
| Q01     | exasol            | starrocks           |        6375.3 |         60867.2 |    9.55 |      0.1  | False    |
| Q02     | exasol            | starrocks           |         382.6 |          1993.9 |    5.21 |      0.19 | False    |
| Q03     | exasol            | starrocks           |        1879.8 |          5636.7 |    3    |      0.33 | False    |
| Q04     | exasol            | starrocks           |         912.7 |          9432.6 |   10.33 |      0.1  | False    |
| Q05     | exasol            | starrocks           |        1803   |          6732.8 |    3.73 |      0.27 | False    |
| Q06     | exasol            | starrocks           |         276.3 |          5969.3 |   21.6  |      0.05 | False    |
| Q07     | exasol            | starrocks           |        2742.6 |          9951.3 |    3.63 |      0.28 | False    |
| Q08     | exasol            | starrocks           |        1235.3 |         10334.9 |    8.37 |      0.12 | False    |
| Q09     | exasol            | starrocks           |       14624.3 |         11180.9 |    0.76 |      1.31 | True     |
| Q10     | exasol            | starrocks           |        2152.2 |          8681.4 |    4.03 |      0.25 | False    |
| Q11     | exasol            | starrocks           |         812.7 |           830.4 |    1.02 |      0.98 | False    |
| Q12     | exasol            | starrocks           |        1252.1 |          9511.8 |    7.6  |      0.13 | False    |
| Q13     | exasol            | starrocks           |        6208.2 |         21400.1 |    3.45 |      0.29 | False    |
| Q14     | exasol            | starrocks           |         791.9 |          9030.9 |   11.4  |      0.09 | False    |
| Q15     | exasol            | starrocks           |        2890.8 |          6313.5 |    2.18 |      0.46 | False    |
| Q16     | exasol            | starrocks           |        3747.4 |          2359   |    0.63 |      1.59 | True     |
| Q17     | exasol            | starrocks           |         122.9 |          7800.9 |   63.47 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        5578.5 |         35763.2 |    6.41 |      0.16 | False    |
| Q19     | exasol            | starrocks           |         109.4 |          5088.5 |   46.51 |      0.02 | False    |
| Q20     | exasol            | starrocks           |        2084.4 |          2812.1 |    1.35 |      0.74 | False    |
| Q21     | exasol            | starrocks           |        3243.2 |         16418   |    5.06 |      0.2  | False    |
| Q22     | exasol            | starrocks           |         826.2 |          7611.2 |    9.21 |      0.11 | False    |
| Q01     | exasol            | trino               |        6375.3 |         51711.5 |    8.11 |      0.12 | False    |
| Q02     | exasol            | trino               |         382.6 |         43331.4 |  113.26 |      0.01 | False    |
| Q03     | exasol            | trino               |        1879.8 |         55129.4 |   29.33 |      0.03 | False    |
| Q04     | exasol            | trino               |         912.7 |         60708.8 |   66.52 |      0.02 | False    |
| Q05     | exasol            | trino               |        1803   |         74908.9 |   41.55 |      0.02 | False    |
| Q06     | exasol            | trino               |         276.3 |         40194.6 |  145.47 |      0.01 | False    |
| Q07     | exasol            | trino               |        2742.6 |         74257.5 |   27.08 |      0.04 | False    |
| Q08     | exasol            | trino               |        1235.3 |         72517.7 |   58.7  |      0.02 | False    |
| Q09     | exasol            | trino               |       14624.3 |        131965   |    9.02 |      0.11 | False    |
| Q10     | exasol            | trino               |        2152.2 |         82332.7 |   38.26 |      0.03 | False    |
| Q11     | exasol            | trino               |         812.7 |         23045.6 |   28.36 |      0.04 | False    |
| Q12     | exasol            | trino               |        1252.1 |         61588.9 |   49.19 |      0.02 | False    |
| Q13     | exasol            | trino               |        6208.2 |        228666   |   36.83 |      0.03 | False    |
| Q14     | exasol            | trino               |         791.9 |         46308.7 |   58.48 |      0.02 | False    |
| Q15     | exasol            | trino               |        2890.8 |         58057   |   20.08 |      0.05 | False    |
| Q16     | exasol            | trino               |        3747.4 |         26005.9 |    6.94 |      0.14 | False    |
| Q17     | exasol            | trino               |         122.9 |         85342.1 |  694.4  |      0    | False    |
| Q18     | exasol            | trino               |        5578.5 |        117924   |   21.14 |      0.05 | False    |
| Q19     | exasol            | trino               |         109.4 |         37161.3 |  339.68 |      0    | False    |
| Q20     | exasol            | trino               |        2084.4 |         54509.3 |   26.15 |      0.04 | False    |
| Q21     | exasol            | trino               |        3243.2 |        144849   |   44.66 |      0.02 | False    |
| Q22     | exasol            | trino               |         826.2 |         46965.7 |   56.85 |      0.02 | False    |

### Per-Stream Statistics

This benchmark was executed using **16 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 18920.7 | 16804.6 | 10017.9 | 33225.7 |
| 1 | 7 | 13436.0 | 16236.9 | 2402.6 | 23054.3 |
| 10 | 7 | 20422.9 | 20746.7 | 6924.1 | 26216.4 |
| 11 | 7 | 18378.5 | 20203.6 | 4313.1 | 27560.5 |
| 12 | 7 | 20240.2 | 18475.7 | 6954.9 | 40733.5 |
| 13 | 7 | 19150.0 | 18347.7 | 9668.4 | 34826.4 |
| 14 | 6 | 16778.4 | 15970.0 | 5181.5 | 30340.8 |
| 15 | 6 | 18328.4 | 18324.2 | 16065.3 | 21276.4 |
| 2 | 7 | 19449.7 | 20000.2 | 11872.2 | 24951.7 |
| 3 | 7 | 19686.8 | 15431.1 | 6361.6 | 44121.5 |
| 4 | 7 | 13696.2 | 15773.1 | 5383.4 | 23733.1 |
| 5 | 7 | 16754.0 | 18017.8 | 4959.1 | 32122.2 |
| 6 | 7 | 20985.4 | 17488.6 | 6366.0 | 43447.2 |
| 7 | 7 | 16433.6 | 16205.4 | 4724.6 | 34750.1 |
| 8 | 7 | 19951.3 | 16828.5 | 13791.4 | 29188.6 |
| 9 | 7 | 14415.0 | 17453.7 | 4184.5 | 21442.8 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 15431.1ms
- Slowest stream median: 20746.7ms
- Stream performance variation: 34.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 14510.3 | 14140.2 | 1890.8 | 25551.1 |
| 1 | 7 | 12735.5 | 12619.0 | 2124.9 | 19470.4 |
| 10 | 7 | 14074.1 | 15401.8 | 9968.2 | 17415.8 |
| 11 | 7 | 14207.0 | 15549.0 | 9982.9 | 17936.9 |
| 12 | 7 | 14299.7 | 14869.2 | 9469.6 | 18003.6 |
| 13 | 7 | 14415.2 | 13906.4 | 9989.3 | 18889.6 |
| 14 | 6 | 14146.1 | 13904.2 | 9355.8 | 18867.4 |
| 15 | 6 | 12818.4 | 13696.0 | 704.3 | 19318.5 |
| 2 | 7 | 13263.9 | 13742.8 | 3048.2 | 21463.8 |
| 3 | 7 | 13487.0 | 15806.0 | 3208.1 | 18413.3 |
| 4 | 7 | 13643.3 | 14368.0 | 7450.8 | 18420.2 |
| 5 | 7 | 13547.0 | 14985.2 | 3796.7 | 18410.4 |
| 6 | 7 | 13736.2 | 14862.8 | 8195.6 | 16817.6 |
| 7 | 7 | 13763.8 | 14687.4 | 8750.8 | 16652.2 |
| 8 | 7 | 13965.8 | 15260.8 | 9308.2 | 16925.2 |
| 9 | 7 | 13864.9 | 14258.7 | 8947.2 | 17810.8 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 12619.0ms
- Slowest stream median: 15806.0ms
- Stream performance variation: 25.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 3754.6 | 1879.8 | 364.2 | 14494.1 |
| 1 | 7 | 1519.8 | 812.7 | 261.7 | 4903.3 |
| 10 | 7 | 3508.9 | 2079.0 | 73.3 | 15644.2 |
| 11 | 7 | 3074.8 | 2541.6 | 297.4 | 6451.0 |
| 12 | 7 | 3012.1 | 1873.2 | 251.1 | 11561.2 |
| 13 | 7 | 2666.8 | 1235.3 | 64.5 | 7107.3 |
| 14 | 6 | 1993.1 | 968.1 | 719.6 | 6208.2 |
| 15 | 6 | 3922.6 | 1602.0 | 440.9 | 15603.8 |
| 2 | 7 | 3586.9 | 2152.2 | 896.0 | 8067.4 |
| 3 | 7 | 2311.7 | 925.6 | 122.9 | 7535.4 |
| 4 | 7 | 2767.1 | 2890.8 | 276.3 | 5156.0 |
| 5 | 7 | 1933.7 | 912.7 | 382.6 | 5899.4 |
| 6 | 7 | 3483.1 | 737.8 | 98.7 | 14624.3 |
| 7 | 7 | 1353.1 | 1120.3 | 237.0 | 4441.4 |
| 8 | 7 | 3674.3 | 2859.8 | 375.6 | 10589.9 |
| 9 | 7 | 3297.0 | 735.4 | 113.2 | 14122.5 |

**Performance Analysis for Exasol:**
- Fastest stream median: 735.4ms
- Slowest stream median: 2890.8ms
- Stream performance variation: 293.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 13235.1 | 8860.0 | 1679.4 | 31524.6 |
| 1 | 7 | 7090.1 | 8121.4 | 1028.5 | 11592.5 |
| 10 | 7 | 10160.1 | 7250.2 | 2812.1 | 26689.8 |
| 11 | 7 | 14402.1 | 6622.2 | 1542.4 | 68712.5 |
| 12 | 7 | 14257.3 | 10778.6 | 519.7 | 60867.2 |
| 13 | 7 | 14017.3 | 9951.3 | 947.5 | 35763.2 |
| 14 | 6 | 9438.5 | 7883.4 | 482.7 | 21400.1 |
| 15 | 6 | 9524.4 | 9248.4 | 1887.6 | 20751.3 |
| 2 | 7 | 15014.0 | 1971.0 | 781.5 | 89654.4 |
| 3 | 7 | 11404.8 | 7374.3 | 830.4 | 36838.5 |
| 4 | 7 | 12290.8 | 6313.5 | 3431.9 | 38649.3 |
| 5 | 7 | 7113.2 | 9184.9 | 1194.3 | 11983.8 |
| 6 | 7 | 12350.8 | 5088.5 | 2518.7 | 50235.2 |
| 7 | 7 | 6993.0 | 6152.0 | 2427.4 | 10870.9 |
| 8 | 7 | 12589.5 | 10715.3 | 2111.7 | 35192.9 |
| 9 | 7 | 12707.1 | 7611.2 | 1103.7 | 52209.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1971.0ms
- Slowest stream median: 10778.6ms
- Stream performance variation: 446.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 79555.3 | 21015.3 | 6367.1 | 238474.5 |
| 1 | 7 | 64017.9 | 44006.8 | 23875.7 | 129492.5 |
| 10 | 7 | 66293.5 | 54509.3 | 36220.3 | 128003.3 |
| 11 | 7 | 57071.2 | 54688.6 | 40726.5 | 87016.6 |
| 12 | 7 | 61595.9 | 51711.5 | 18321.5 | 127028.3 |
| 13 | 7 | 73200.4 | 62336.1 | 50480.7 | 148775.6 |
| 14 | 6 | 77544.9 | 50627.7 | 9292.7 | 233580.4 |
| 15 | 6 | 72124.2 | 65353.9 | 27399.1 | 138709.5 |
| 2 | 7 | 73848.2 | 55030.3 | 22585.5 | 131964.6 |
| 3 | 7 | 73337.0 | 50657.0 | 23045.6 | 221265.5 |
| 4 | 7 | 74523.3 | 59787.3 | 9110.6 | 159541.1 |
| 5 | 7 | 64641.9 | 58057.0 | 43331.4 | 103680.8 |
| 6 | 7 | 71509.1 | 61588.9 | 27600.2 | 139535.5 |
| 7 | 7 | 46830.5 | 42401.9 | 24791.2 | 99275.6 |
| 8 | 7 | 75328.6 | 45205.8 | 15067.7 | 228666.3 |
| 9 | 7 | 72463.9 | 50015.3 | 19680.3 | 162042.0 |

**Performance Analysis for Trino:**
- Fastest stream median: 21015.3ms
- Slowest stream median: 65353.9ms
- Stream performance variation: 211.0% difference between fastest and slowest streams
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
- Median runtime: 17471.6ms
- Average runtime: 17946.2ms
- Fastest query: 2402.6ms
- Slowest query: 44121.5ms

**duckdb:**
- Median runtime: 14313.4ms
- Average runtime: 13785.3ms
- Fastest query: 704.3ms
- Slowest query: 25551.1ms

**exasol:**
- Median runtime: 1697.7ms
- Average runtime: 2864.6ms
- Fastest query: 64.5ms
- Slowest query: 15644.2ms

**starrocks:**
- Median runtime: 7832.9ms
- Average runtime: 11446.8ms
- Fastest query: 482.7ms
- Slowest query: 89654.4ms

**trino:**
- Median runtime: 53586.8ms
- Average runtime: 68886.7ms
- Fastest query: 6367.1ms
- Slowest query: 238474.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_single_streams_16-benchmark.zip`](ext_scalability_single_streams_16-benchmark.zip)

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
  - memory_limit: 96g
  - max_threads: 16
  - max_memory_usage: 7000000000
  - max_bytes_before_external_group_by: 2500000000
  - max_bytes_before_external_sort: 2500000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 5000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 96GB
  - query_max_memory_per_node: 96GB

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
  - memory_limit: 96GB
  - threads: 16


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 16 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts