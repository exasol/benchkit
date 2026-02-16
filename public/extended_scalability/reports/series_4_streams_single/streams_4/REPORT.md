# Extended Scalability - Single Node Stream Scaling (4 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-30 11:26:16

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
- exasol was the fastest overall with 2073.3ms median runtime
- trino was 41.5x slower- Tested 550 total query executions across 22 different TPC-H queries
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
- **Hostname:** ip-10-0-1-145

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
- **Hostname:** ip-10-0-1-194

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
- **Hostname:** ip-10-0-1-249

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
- **Hostname:** ip-10-0-1-197

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
- **Hostname:** ip-10-0-1-92


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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64633E788F5908EA4 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64633E788F5908EA4

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64633E788F5908EA4 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64633E788F5908EA4 /data

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
node.id=c0ad3a48-5160-48e3-86ad-dcbd9538f7b0
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64539C714D90C12D3 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64539C714D90C12D3

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64539C714D90C12D3 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64539C714D90C12D3 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22940DB2F649646E8 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22940DB2F649646E8

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22940DB2F649646E8 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22940DB2F649646E8 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS69DAB45D388F78945 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS69DAB45D388F78945

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS69DAB45D388F78945 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS69DAB45D388F78945 /data

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
- **Execution mode:** Multiuser (4 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_single_streams_4-benchmark.zip
cd ext_scalability_single_streams_4

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
| Q01     | clickhouse |   9279.8 |      5 |     30897.9 |   30148   |   4476.1 |  25089.1 |  35025.6 |
| Q01     | duckdb     |   7809.7 |      5 |     13283   |   14281.1 |   3496.6 |  10495.2 |  18842.1 |
| Q01     | exasol     |   3116   |      5 |      8061   |    8790.7 |   3066.6 |   5193.5 |  12111.7 |
| Q01     | starrocks  |  13754.4 |      5 |     47643.9 |   60728.7 |  32762.9 |  23872.9 | 109060   |
| Q01     | trino      |  20800.8 |      5 |     69315.6 |   75567   |  17165.9 |  62106   | 104504   |
| Q02     | clickhouse |   3910.5 |      5 |     19471.2 |   18059.4 |   3220.2 |  12547.6 |  20305.2 |
| Q02     | duckdb     |    959.3 |      5 |      8312.2 |   10942.1 |   4827.2 |   6256.8 |  17580.3 |
| Q02     | exasol     |    105.3 |      5 |       516.3 |     819   |    763.6 |    417.1 |   2181.9 |
| Q02     | starrocks  |    820.4 |      5 |      1618.1 |    1643.7 |    318.4 |   1341.8 |   2158.1 |
| Q02     | trino      |  11205.6 |      5 |     35258.8 |   40641.3 |  14059.5 |  27268.8 |  63575.2 |
| Q03     | clickhouse |   4710.4 |      5 |     19406.6 |   17439.6 |   3983   |  10424.7 |  19708.1 |
| Q03     | duckdb     |   3507.8 |      5 |     10218.7 |   13505.5 |   8106.7 |   5940.1 |  24854.9 |
| Q03     | exasol     |   1145   |      5 |      2148.1 |    2957.3 |   2087.6 |   1118.4 |   5365.5 |
| Q03     | starrocks  |   4833.4 |      5 |      6079.5 |   13901.4 |  11776.4 |   5668.4 |  31725.5 |
| Q03     | trino      |  26538.9 |      5 |     41917.5 |   70612.6 |  58448.5 |  24161.8 | 163729   |
| Q04     | clickhouse |  10479.5 |      5 |     36127.8 |   31528   |  10743.3 |  12469.2 |  37693.8 |
| Q04     | duckdb     |   2864.7 |      5 |     17529.5 |   15543.6 |   5909.3 |   7611.3 |  21108.1 |
| Q04     | exasol     |    208.8 |      5 |       848.4 |    1060   |    747.2 |    418.4 |   2355.4 |
| Q04     | starrocks  |   4285.3 |      5 |     54762.7 |   48048.1 |  18285   |  28091.5 |  65473   |
| Q04     | trino      |  22120.1 |      5 |    104454   |   93451   |  27909.9 |  43731.3 | 110067   |
| Q05     | clickhouse |   4370.5 |      5 |     23263.5 |   23195   |   3300.4 |  19994   |  27922.3 |
| Q05     | duckdb     |   3208.1 |      5 |     10913.1 |   12775.2 |   5114.2 |   8076.5 |  21079.4 |
| Q05     | exasol     |    914.4 |      5 |      3746   |    3498.2 |    966.6 |   1835.6 |   4290.1 |
| Q05     | starrocks  |   6036.9 |      5 |     14337.8 |   14782.9 |    926.6 |  13832.5 |  15855.7 |
| Q05     | trino      |  24573.9 |      5 |     98143.2 |  106979   |  20577.5 |  86462   | 139731   |
| Q06     | clickhouse |    527.2 |      5 |      3716.4 |    3981.3 |   2435.4 |   1140.8 |   6516.7 |
| Q06     | duckdb     |    824.9 |      5 |      7424.2 |   10601.9 |   5845.9 |   5298.8 |  19532.7 |
| Q06     | exasol     |    138.5 |      5 |       315.1 |     438.2 |    277.3 |    257.3 |    915.8 |
| Q06     | starrocks  |   2286.5 |      5 |      2673.6 |    3104.6 |    868.4 |   2140.1 |   4051.6 |
| Q06     | trino      |   8578.8 |      5 |     73839.2 |   81939.3 |  19655.9 |  64259.8 | 106294   |
| Q07     | clickhouse |   3805.6 |      5 |     17031.9 |   17063.5 |   3547.5 |  11566.4 |  20915.6 |
| Q07     | duckdb     |   2666.3 |      5 |      9987.4 |    9584.3 |   1987.1 |   7137.8 |  12195.1 |
| Q07     | exasol     |   1150   |      5 |      5151.9 |    4766.9 |   2190.8 |   1145   |   6890.4 |
| Q07     | starrocks  |   5053.7 |      5 |      8171   |    8228.7 |   3004.1 |   5130.7 |  13028.9 |
| Q07     | trino      |  19197.9 |      5 |     82114.2 |   76336.7 |  30607.8 |  25052.1 | 100117   |
| Q08     | clickhouse |   3431.2 |      5 |     15989.2 |   17853.2 |   4537   |  15365.6 |  25925.6 |
| Q08     | duckdb     |   2932.8 |      5 |     10636.6 |   11077.3 |   1939.5 |   9241.5 |  14123.1 |
| Q08     | exasol     |    268.5 |      5 |      1226   |    1211   |    474.5 |    465.3 |   1673.6 |
| Q08     | starrocks  |   4058.3 |      5 |      5442.8 |    7137.2 |   2978.9 |   4683.7 |  11486.1 |
| Q08     | trino      |  21443.3 |      5 |    104010   |  106676   |  20262.2 |  86220.2 | 140118   |
| Q09     | clickhouse |   4096.4 |      5 |     17302.1 |   17403.8 |   2465.7 |  14834.2 |  20862.7 |
| Q09     | duckdb     |   9043.4 |      5 |     20115.7 |   19877   |   3913.2 |  15152.1 |  25643.1 |
| Q09     | exasol     |   4027.7 |      5 |     18532.7 |   18787.4 |    449.6 |  18428.3 |  19401   |
| Q09     | starrocks  |  10541.6 |      5 |     20651.3 |   20739.3 |   4152.3 |  14814.4 |  26490.6 |
| Q09     | trino      |  55093.9 |      5 |    163774   |  173763   |  29660.7 | 146436   | 207290   |
| Q10     | clickhouse |   5406.9 |      5 |     25580.5 |   25914.7 |   3341.5 |  22779.4 |  30842.2 |
| Q10     | duckdb     |   4294.5 |      5 |     13843.5 |   15216.6 |   4267.8 |  10977.7 |  20461.4 |
| Q10     | exasol     |   1223.8 |      5 |      4348.6 |    3907.6 |   1416.4 |   2410.5 |   5678.9 |
| Q10     | starrocks  |   4675.4 |      5 |      9577.9 |   11027.1 |   3789.8 |   6585.8 |  15056.9 |
| Q10     | trino      |  21320   |      5 |    110380   |  121804   |  38454.4 |  85485.3 | 175030   |
| Q11     | clickhouse |   1967.1 |      5 |     10026.6 |    9450.6 |   3907.7 |   4028.4 |  14798.5 |
| Q11     | duckdb     |    406.6 |      5 |     14272.3 |   14848.8 |   3135.1 |  12271.9 |  20180.9 |
| Q11     | exasol     |    219.1 |      5 |       776.4 |     858.6 |    350.6 |    433.3 |   1392.2 |
| Q11     | starrocks  |    690.6 |      5 |      1151.7 |    1182.1 |    175.3 |   1033.6 |   1482.5 |
| Q11     | trino      |   3521.6 |      5 |     19965   |   19469.2 |   2905   |  15003.8 |  23007.8 |
| Q12     | clickhouse |   4073.7 |      5 |     16320.3 |   17036.4 |   2373.7 |  14152.7 |  20536.7 |
| Q12     | duckdb     |   3125   |      5 |     17064.2 |   17122.6 |   3903.1 |  11414.8 |  21648.8 |
| Q12     | exasol     |    282.4 |      5 |      1238.5 |    1256.2 |    419   |    738.9 |   1896.8 |
| Q12     | starrocks  |   3002   |      5 |      5081.7 |    6267.8 |   1854.8 |   4889.8 |   9112.6 |
| Q12     | trino      |  12110.8 |      5 |     80420.9 |   85047.9 |  16832.9 |  72415.8 | 114555   |
| Q13     | clickhouse |   7459.6 |      5 |     25098.2 |   25989.2 |   3349   |  21993.5 |  30225   |
| Q13     | duckdb     |   7602.1 |      5 |     14446.4 |   14674.7 |   5466.5 |   7262.9 |  20598.8 |
| Q13     | exasol     |   3001.5 |      5 |     11125   |   10267   |   3508.3 |   5267.7 |  13704.6 |
| Q13     | starrocks  |   5918.5 |      5 |     13888.8 |   16880.7 |  10412   |   5945.6 |  32612.6 |
| Q13     | trino      |  32349.8 |      5 |    144667   |  138259   |  24869.6 | 101223   | 162728   |
| Q14     | clickhouse |    703.8 |      5 |      6670.9 |    6171.4 |   1887.7 |   3426.5 |   8002.5 |
| Q14     | duckdb     |   2137.8 |      5 |     10306.1 |   12893.8 |   5263.8 |   8542.5 |  21367.1 |
| Q14     | exasol     |    287.4 |      5 |      1573   |    1557.8 |    342.4 |   1203.1 |   1998.5 |
| Q14     | starrocks  |   2055   |      5 |      5432.6 |    4729.6 |   1688.3 |   2871.1 |   6242.9 |
| Q14     | trino      |  16027.6 |      5 |     75086.5 |   72470.4 |  22826.1 |  50168.2 | 104131   |
| Q15     | clickhouse |    545.6 |      5 |      4849.6 |    4496.5 |   1448.3 |   2892.9 |   6304.9 |
| Q15     | duckdb     |   1767.5 |      5 |     16429.1 |   14843.1 |   6753.3 |   6693.1 |  22915.5 |
| Q15     | exasol     |    671.4 |      5 |      2466.1 |    3218.8 |   1722.5 |   2384.9 |   6298.9 |
| Q15     | starrocks  |   2300.4 |      5 |      3686   |    3718.4 |    669.1 |   2892.1 |   4656.7 |
| Q15     | trino      |  23674.3 |      5 |     81657.1 |   79843.1 |  10477.4 |  66917.1 |  92874.7 |
| Q16     | clickhouse |   2556.5 |      5 |     14193.8 |   13184.8 |   2510   |   8835.8 |  15076.6 |
| Q16     | duckdb     |   1308.8 |      5 |      9017.6 |    8850.2 |   4874.8 |   1326.4 |  14875.4 |
| Q16     | exasol     |    983   |      5 |      3569.2 |    3374   |    609.8 |   2304.3 |   3812.7 |
| Q16     | starrocks  |   1272.2 |      5 |      2150.2 |    2168.2 |    218.8 |   1926.7 |   2462.5 |
| Q16     | trino      |   7384.2 |      5 |     26869.9 |   29534.4 |   7262.5 |  23931.4 |  41305.8 |
| Q17     | clickhouse |   3693.1 |      5 |     18967.9 |   18508.3 |   3145.6 |  13277.6 |  21333.1 |
| Q17     | duckdb     |   3287.6 |      5 |     17667.3 |   16442.3 |   5035.2 |   8978.5 |  21244.2 |
| Q17     | exasol     |     36.1 |      5 |       159.2 |     183.5 |    101.2 |     62.2 |    288.5 |
| Q17     | starrocks  |   2139.6 |      5 |      3084   |    3260.6 |    453.8 |   2855.3 |   3792.9 |
| Q17     | trino      |  26488.1 |      5 |    104209   |  135471   |  54613.9 |  83357.7 | 210268   |
| Q18     | clickhouse |   5908   |      5 |     24263.3 |   24296.7 |   3365.7 |  18823.6 |  27112.3 |
| Q18     | duckdb     |   6027.4 |      5 |     13465.8 |   14857.9 |   3952.9 |  11950.4 |  21680.6 |
| Q18     | exasol     |   1858.2 |      5 |      6994.9 |    6491.3 |   1208.2 |   4337.4 |   7195.3 |
| Q18     | starrocks  |   9831.9 |      5 |     41378.6 |   41953.9 |   9663.3 |  30200   |  54453.3 |
| Q18     | trino      |  27777.7 |      5 |    197387   |  197476   |  24693.7 | 164526   | 227092   |
| Q19     | clickhouse |  19408.6 |      5 |     64343.8 |   53854.5 |  19545.3 |  19677.2 |  64993.2 |
| Q19     | duckdb     |   3058.4 |      5 |     14236.7 |   14939.7 |   4747.3 |   9344.7 |  21676.8 |
| Q19     | exasol     |     90.9 |      5 |       182.4 |     279.1 |    155.2 |    168.4 |    527.2 |
| Q19     | starrocks  |   2960.4 |      5 |      3803.4 |    3858.9 |    808.1 |   3089.5 |   5013.4 |
| Q19     | trino      |  17032.3 |      5 |     75488.9 |   69413.3 |  22512   |  37229   |  95035.5 |
| Q20     | clickhouse |   6157.6 |      5 |     23117.6 |   22761.8 |   2780.9 |  19687.9 |  26888.5 |
| Q20     | duckdb     |   2810.3 |      5 |     11158.7 |   13502.5 |   6518.8 |   7062.3 |  20717.3 |
| Q20     | exasol     |    589.3 |      5 |      1171.4 |    1653.4 |    792.6 |    955.5 |   2725.6 |
| Q20     | starrocks  |   2872.9 |      5 |      3231.1 |    3275   |    179   |   3050.5 |   3531   |
| Q20     | trino      |  16570.1 |      5 |     76574.3 |   83718.4 |  20581.6 |  67240.1 | 118258   |
| Q21     | clickhouse |   3696.2 |      5 |     15018.5 |   14527.5 |   5185.8 |   6594.6 |  21009.3 |
| Q21     | duckdb     |  13708.2 |      5 |     21386.8 |   21430.9 |   2303.3 |  18612.2 |  23742.4 |
| Q21     | exasol     |   1669.7 |      5 |      4866.6 |    5847.5 |   2873.6 |   3095.8 |   9145.1 |
| Q21     | starrocks  |  15965.8 |      5 |     67577.5 |   65191   |  29202.2 |  22026.9 | 103849   |
| Q21     | trino      |  60663.8 |      5 |    205453   |  190003   |  41916.8 | 140123   | 239360   |
| Q22     | clickhouse |   1748.3 |      5 |     11416.9 |   11211.2 |   2984   |   6757   |  15006.1 |
| Q22     | duckdb     |   1539.7 |      5 |     13659.4 |   14207.2 |   5412.2 |   7084.1 |  20151.8 |
| Q22     | exasol     |    344.4 |      5 |      1347.7 |    1265.8 |    341.3 |    679.4 |   1570.8 |
| Q22     | starrocks  |   1043.7 |      5 |      2138.4 |    3115.3 |   2911.9 |    943.3 |   8239.2 |
| Q22     | trino      |  11567.8 |      5 |     46801.5 |   51398.9 |  25998.3 |  20682.2 |  85912   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        8061   |         30897.9 |    3.83 |      0.26 | False    |
| Q02     | exasol            | clickhouse          |         516.3 |         19471.2 |   37.71 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        2148.1 |         19406.6 |    9.03 |      0.11 | False    |
| Q04     | exasol            | clickhouse          |         848.4 |         36127.8 |   42.58 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        3746   |         23263.5 |    6.21 |      0.16 | False    |
| Q06     | exasol            | clickhouse          |         315.1 |          3716.4 |   11.79 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        5151.9 |         17031.9 |    3.31 |      0.3  | False    |
| Q08     | exasol            | clickhouse          |        1226   |         15989.2 |   13.04 |      0.08 | False    |
| Q09     | exasol            | clickhouse          |       18532.7 |         17302.1 |    0.93 |      1.07 | True     |
| Q10     | exasol            | clickhouse          |        4348.6 |         25580.5 |    5.88 |      0.17 | False    |
| Q11     | exasol            | clickhouse          |         776.4 |         10026.6 |   12.91 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |        1238.5 |         16320.3 |   13.18 |      0.08 | False    |
| Q13     | exasol            | clickhouse          |       11125   |         25098.2 |    2.26 |      0.44 | False    |
| Q14     | exasol            | clickhouse          |        1573   |          6670.9 |    4.24 |      0.24 | False    |
| Q15     | exasol            | clickhouse          |        2466.1 |          4849.6 |    1.97 |      0.51 | False    |
| Q16     | exasol            | clickhouse          |        3569.2 |         14193.8 |    3.98 |      0.25 | False    |
| Q17     | exasol            | clickhouse          |         159.2 |         18967.9 |  119.15 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        6994.9 |         24263.3 |    3.47 |      0.29 | False    |
| Q19     | exasol            | clickhouse          |         182.4 |         64343.8 |  352.76 |      0    | False    |
| Q20     | exasol            | clickhouse          |        1171.4 |         23117.6 |   19.74 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        4866.6 |         15018.5 |    3.09 |      0.32 | False    |
| Q22     | exasol            | clickhouse          |        1347.7 |         11416.9 |    8.47 |      0.12 | False    |
| Q01     | exasol            | duckdb              |        8061   |         13283   |    1.65 |      0.61 | False    |
| Q02     | exasol            | duckdb              |         516.3 |          8312.2 |   16.1  |      0.06 | False    |
| Q03     | exasol            | duckdb              |        2148.1 |         10218.7 |    4.76 |      0.21 | False    |
| Q04     | exasol            | duckdb              |         848.4 |         17529.5 |   20.66 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        3746   |         10913.1 |    2.91 |      0.34 | False    |
| Q06     | exasol            | duckdb              |         315.1 |          7424.2 |   23.56 |      0.04 | False    |
| Q07     | exasol            | duckdb              |        5151.9 |          9987.4 |    1.94 |      0.52 | False    |
| Q08     | exasol            | duckdb              |        1226   |         10636.6 |    8.68 |      0.12 | False    |
| Q09     | exasol            | duckdb              |       18532.7 |         20115.7 |    1.09 |      0.92 | False    |
| Q10     | exasol            | duckdb              |        4348.6 |         13843.5 |    3.18 |      0.31 | False    |
| Q11     | exasol            | duckdb              |         776.4 |         14272.3 |   18.38 |      0.05 | False    |
| Q12     | exasol            | duckdb              |        1238.5 |         17064.2 |   13.78 |      0.07 | False    |
| Q13     | exasol            | duckdb              |       11125   |         14446.4 |    1.3  |      0.77 | False    |
| Q14     | exasol            | duckdb              |        1573   |         10306.1 |    6.55 |      0.15 | False    |
| Q15     | exasol            | duckdb              |        2466.1 |         16429.1 |    6.66 |      0.15 | False    |
| Q16     | exasol            | duckdb              |        3569.2 |          9017.6 |    2.53 |      0.4  | False    |
| Q17     | exasol            | duckdb              |         159.2 |         17667.3 |  110.98 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        6994.9 |         13465.8 |    1.93 |      0.52 | False    |
| Q19     | exasol            | duckdb              |         182.4 |         14236.7 |   78.05 |      0.01 | False    |
| Q20     | exasol            | duckdb              |        1171.4 |         11158.7 |    9.53 |      0.1  | False    |
| Q21     | exasol            | duckdb              |        4866.6 |         21386.8 |    4.39 |      0.23 | False    |
| Q22     | exasol            | duckdb              |        1347.7 |         13659.4 |   10.14 |      0.1  | False    |
| Q01     | exasol            | starrocks           |        8061   |         47643.9 |    5.91 |      0.17 | False    |
| Q02     | exasol            | starrocks           |         516.3 |          1618.1 |    3.13 |      0.32 | False    |
| Q03     | exasol            | starrocks           |        2148.1 |          6079.5 |    2.83 |      0.35 | False    |
| Q04     | exasol            | starrocks           |         848.4 |         54762.7 |   64.55 |      0.02 | False    |
| Q05     | exasol            | starrocks           |        3746   |         14337.8 |    3.83 |      0.26 | False    |
| Q06     | exasol            | starrocks           |         315.1 |          2673.6 |    8.48 |      0.12 | False    |
| Q07     | exasol            | starrocks           |        5151.9 |          8171   |    1.59 |      0.63 | False    |
| Q08     | exasol            | starrocks           |        1226   |          5442.8 |    4.44 |      0.23 | False    |
| Q09     | exasol            | starrocks           |       18532.7 |         20651.3 |    1.11 |      0.9  | False    |
| Q10     | exasol            | starrocks           |        4348.6 |          9577.9 |    2.2  |      0.45 | False    |
| Q11     | exasol            | starrocks           |         776.4 |          1151.7 |    1.48 |      0.67 | False    |
| Q12     | exasol            | starrocks           |        1238.5 |          5081.7 |    4.1  |      0.24 | False    |
| Q13     | exasol            | starrocks           |       11125   |         13888.8 |    1.25 |      0.8  | False    |
| Q14     | exasol            | starrocks           |        1573   |          5432.6 |    3.45 |      0.29 | False    |
| Q15     | exasol            | starrocks           |        2466.1 |          3686   |    1.49 |      0.67 | False    |
| Q16     | exasol            | starrocks           |        3569.2 |          2150.2 |    0.6  |      1.66 | True     |
| Q17     | exasol            | starrocks           |         159.2 |          3084   |   19.37 |      0.05 | False    |
| Q18     | exasol            | starrocks           |        6994.9 |         41378.6 |    5.92 |      0.17 | False    |
| Q19     | exasol            | starrocks           |         182.4 |          3803.4 |   20.85 |      0.05 | False    |
| Q20     | exasol            | starrocks           |        1171.4 |          3231.1 |    2.76 |      0.36 | False    |
| Q21     | exasol            | starrocks           |        4866.6 |         67577.5 |   13.89 |      0.07 | False    |
| Q22     | exasol            | starrocks           |        1347.7 |          2138.4 |    1.59 |      0.63 | False    |
| Q01     | exasol            | trino               |        8061   |         69315.6 |    8.6  |      0.12 | False    |
| Q02     | exasol            | trino               |         516.3 |         35258.8 |   68.29 |      0.01 | False    |
| Q03     | exasol            | trino               |        2148.1 |         41917.5 |   19.51 |      0.05 | False    |
| Q04     | exasol            | trino               |         848.4 |        104454   |  123.12 |      0.01 | False    |
| Q05     | exasol            | trino               |        3746   |         98143.2 |   26.2  |      0.04 | False    |
| Q06     | exasol            | trino               |         315.1 |         73839.2 |  234.34 |      0    | False    |
| Q07     | exasol            | trino               |        5151.9 |         82114.2 |   15.94 |      0.06 | False    |
| Q08     | exasol            | trino               |        1226   |        104010   |   84.84 |      0.01 | False    |
| Q09     | exasol            | trino               |       18532.7 |        163774   |    8.84 |      0.11 | False    |
| Q10     | exasol            | trino               |        4348.6 |        110380   |   25.38 |      0.04 | False    |
| Q11     | exasol            | trino               |         776.4 |         19965   |   25.71 |      0.04 | False    |
| Q12     | exasol            | trino               |        1238.5 |         80420.9 |   64.93 |      0.02 | False    |
| Q13     | exasol            | trino               |       11125   |        144667   |   13    |      0.08 | False    |
| Q14     | exasol            | trino               |        1573   |         75086.5 |   47.73 |      0.02 | False    |
| Q15     | exasol            | trino               |        2466.1 |         81657.1 |   33.11 |      0.03 | False    |
| Q16     | exasol            | trino               |        3569.2 |         26869.9 |    7.53 |      0.13 | False    |
| Q17     | exasol            | trino               |         159.2 |        104209   |  654.58 |      0    | False    |
| Q18     | exasol            | trino               |        6994.9 |        197387   |   28.22 |      0.04 | False    |
| Q19     | exasol            | trino               |         182.4 |         75488.9 |  413.86 |      0    | False    |
| Q20     | exasol            | trino               |        1171.4 |         76574.3 |   65.37 |      0.02 | False    |
| Q21     | exasol            | trino               |        4866.6 |        205453   |   42.22 |      0.02 | False    |
| Q22     | exasol            | trino               |        1347.7 |         46801.5 |   34.73 |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 19438.3 | 19475.4 | 3152.6 | 64984.8 |
| 1 | 28 | 17002.0 | 16262.6 | 2892.9 | 37693.8 |
| 2 | 27 | 21219.0 | 19687.9 | 1140.8 | 64993.2 |
| 3 | 27 | 19523.5 | 18448.2 | 2145.4 | 64343.8 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 16262.6ms
- Slowest stream median: 19687.9ms
- Stream performance variation: 21.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 14157.5 | 13721.2 | 5940.1 | 24854.9 |
| 1 | 28 | 14063.5 | 12170.2 | 7326.1 | 22915.5 |
| 2 | 27 | 14364.0 | 13843.5 | 5298.8 | 25643.1 |
| 3 | 27 | 14151.0 | 14236.7 | 1326.4 | 21648.8 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 12170.2ms
- Slowest stream median: 14236.7ms
- Stream performance variation: 17.0% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 4207.1 | 3671.2 | 257.3 | 13704.6 |
| 1 | 28 | 3104.2 | 1481.8 | 159.2 | 19401.0 |
| 2 | 27 | 4213.4 | 1835.6 | 168.4 | 18532.7 |
| 3 | 27 | 3480.3 | 1392.2 | 62.2 | 19132.6 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1392.2ms
- Slowest stream median: 3671.2ms
- Stream performance variation: 163.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 16841.8 | 8874.5 | 943.3 | 103849.1 |
| 1 | 28 | 14415.5 | 4354.1 | 1151.7 | 63010.0 |
| 2 | 27 | 15407.2 | 5432.6 | 1033.6 | 76142.0 |
| 3 | 27 | 16056.2 | 5081.7 | 1086.8 | 109060.3 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 4354.1ms
- Slowest stream median: 8874.5ms
- Stream performance variation: 103.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 98638.3 | 95265.6 | 20375.7 | 239359.6 |
| 1 | 28 | 93094.6 | 86066.1 | 23007.8 | 203418.9 |
| 2 | 27 | 98728.6 | 86462.0 | 15003.8 | 227091.5 |
| 3 | 27 | 91303.0 | 82386.7 | 18993.7 | 214524.7 |

**Performance Analysis for Trino:**
- Fastest stream median: 82386.7ms
- Slowest stream median: 95265.6ms
- Stream performance variation: 15.6% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams

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
- Median runtime: 18553.1ms
- Average runtime: 19276.2ms
- Fastest query: 1140.8ms
- Slowest query: 64993.2ms

**duckdb:**
- Median runtime: 13751.5ms
- Average runtime: 14182.7ms
- Fastest query: 1326.4ms
- Slowest query: 25643.1ms

**exasol:**
- Median runtime: 2073.3ms
- Average runtime: 3749.5ms
- Fastest query: 62.2ms
- Slowest query: 19401.0ms

**starrocks:**
- Median runtime: 5693.9ms
- Average runtime: 15679.2ms
- Fastest query: 943.3ms
- Slowest query: 109060.3ms

**trino:**
- Median runtime: 85946.9ms
- Average runtime: 95448.8ms
- Fastest query: 15003.8ms
- Slowest query: 239359.6ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_single_streams_4-benchmark.zip`](ext_scalability_single_streams_4-benchmark.zip)

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts