# Extended Scalability - Scale Factor 50 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-01-29 22:56:26

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
- exasol was the fastest overall with 847.9ms median runtime
- trino was 40.9x slower- Tested 550 total query executions across 22 different TPC-H queries
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
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-169

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
- **Hostname:** ip-10-0-1-118

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
- **Hostname:** ip-10-0-1-216

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
- **Hostname:** ip-10-0-1-191

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
- **Hostname:** ip-10-0-1-251


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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EA21E43EA1A8414 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EA21E43EA1A8414

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EA21E43EA1A8414 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EA21E43EA1A8414 /data

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
node.id=a3196be2-37b0-48cd-ba8a-2d48682553eb
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4524D4C6D10A3F55C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4524D4C6D10A3F55C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4524D4C6D10A3F55C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4524D4C6D10A3F55C /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66307875B2FA2C90A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66307875B2FA2C90A

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66307875B2FA2C90A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66307875B2FA2C90A /data

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
    &lt;max_server_memory_usage&gt;53066933862&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
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
            &lt;max_memory_usage&gt;15000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;5000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;5000000000&lt;/max_bytes_before_external_group_by&gt;
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
- Max memory usage: `15.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64BEE59760CFCA2DE with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64BEE59760CFCA2DE

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64BEE59760CFCA2DE to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64BEE59760CFCA2DE /data

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
- **Execution mode:** Multiuser (4 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip ext_scalability_sf_50-benchmark.zip
cd ext_scalability_sf_50

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
| Q01     | clickhouse |   4516   |      5 |     16859.5 |   16791.4 |   4387.6 |  10212.5 |  22466.2 |
| Q01     | duckdb     |   2267.5 |      5 |      6134.1 |    6924.1 |   1984.5 |   4548.6 |   9424   |
| Q01     | exasol     |   1564.1 |      5 |      5422.9 |    4696   |   1280.2 |   2573.9 |   5629.8 |
| Q01     | starrocks  |   7068   |      5 |     16212.7 |   19676.4 |   9540.1 |  13398.2 |  36480.4 |
| Q01     | trino      |  10170.3 |      5 |     44866.6 |   34063.3 |  18976.6 |  12537.8 |  52914.7 |
| Q02     | clickhouse |   1916.1 |      5 |     10254.7 |   11483.7 |   1981.1 |   9658.7 |  13643.5 |
| Q02     | duckdb     |    480.5 |      5 |      4224.6 |    5634.9 |   2555.4 |   3233.6 |   9275.7 |
| Q02     | exasol     |     81.6 |      5 |       208   |     208.3 |     18.8 |    188.8 |    237.7 |
| Q02     | starrocks  |    559.2 |      5 |       901.5 |    1028.7 |    264.2 |    769.1 |   1425.3 |
| Q02     | trino      |   5303   |      5 |     10695.4 |   10250.9 |   2423.3 |   6722.6 |  12448.9 |
| Q03     | clickhouse |   6890.3 |      5 |     24165.1 |   20805.9 |  11189.2 |   6018.8 |  32128.7 |
| Q03     | duckdb     |   1465.4 |      5 |      5109.2 |    5831.2 |   4174   |   1325.5 |  12594.8 |
| Q03     | exasol     |    610.1 |      5 |       593.1 |    1282.2 |    954.3 |    584.9 |   2452.4 |
| Q03     | starrocks  |   3386.7 |      5 |      3365   |    7073.8 |   5211.5 |   3234.8 |  13435   |
| Q03     | trino      |  13272.6 |      5 |     32129.5 |   33525.3 |  21204.2 |  11923.1 |  67819.3 |
| Q04     | clickhouse |   8427.3 |      5 |     22242.9 |   23048.4 |   5576.4 |  17360.4 |  30003.4 |
| Q04     | duckdb     |   1379.2 |      5 |     10608.8 |   10083.9 |   2671.5 |   6469   |  13679.9 |
| Q04     | exasol     |    111.7 |      5 |       418.6 |     439.4 |    205   |    178.5 |    744.6 |
| Q04     | starrocks  |   1688.7 |      5 |      4772.5 |    4477.8 |   1383.5 |   2474.9 |   6294.7 |
| Q04     | trino      |   9666.2 |      5 |     36089.4 |   32907.3 |  11526.9 |  13067.7 |  42998.2 |
| Q05     | clickhouse |   5261.6 |      5 |     24220.6 |   23429.1 |   6152.9 |  16738.7 |  31258.3 |
| Q05     | duckdb     |   1535.7 |      5 |      5518.8 |    6476.8 |   2594.6 |   4118.9 |  10690   |
| Q05     | exasol     |    481.8 |      5 |      1758.3 |    1564.6 |    417.8 |    825.6 |   1822.6 |
| Q05     | starrocks  |   2805.8 |      5 |      7668.8 |    7200.6 |   1290.8 |   5467.9 |   8729.1 |
| Q05     | trino      |  12392.4 |      5 |     61145.4 |   55380.7 |  13072.8 |  37396.4 |  69134.1 |
| Q06     | clickhouse |    281.8 |      5 |      1960.7 |    2259.6 |    973.4 |   1333.4 |   3726.3 |
| Q06     | duckdb     |    406.4 |      5 |      3831.9 |    4540.6 |   1157.2 |   3692.7 |   6277   |
| Q06     | exasol     |     70.8 |      5 |       261.1 |     270.7 |    193.8 |     93.5 |    588.4 |
| Q06     | starrocks  |   1491.4 |      5 |      2745.2 |    2551.7 |    964.6 |   1485.8 |   3569.2 |
| Q06     | trino      |   4262.1 |      5 |     18138.3 |   14880.2 |   7826.3 |   6291.4 |  21975.1 |
| Q07     | clickhouse |  12849.6 |      5 |     37998.2 |   33815.4 |  13358.6 |  11969.9 |  45367.3 |
| Q07     | duckdb     |   1338.1 |      5 |      4097.8 |    4390.5 |    719.3 |   3654.7 |   5260.9 |
| Q07     | exasol     |    598.7 |      5 |      2160.6 |    1916.4 |    788.8 |    560.2 |   2617.1 |
| Q07     | starrocks  |   3472.2 |      5 |      6803.2 |    6428.6 |   1758.4 |   3467.9 |   8190   |
| Q07     | trino      |   9339.4 |      5 |     38559.6 |   34338.6 |  14949.1 |  16358.7 |  52192.5 |
| Q08     | clickhouse |   6329.1 |      5 |     28236.5 |   25174   |   5814   |  17280.5 |  30962.8 |
| Q08     | duckdb     |   1448.5 |      5 |      5339.9 |    5448.5 |   1075.9 |   4419.3 |   7170.8 |
| Q08     | exasol     |    162.5 |      5 |       530   |     519.5 |    145.9 |    297.8 |    683.1 |
| Q08     | starrocks  |   2922.8 |      5 |      6552.5 |    6883   |    948.3 |   6001.3 |   8025   |
| Q08     | trino      |   9957.8 |      5 |     49258.6 |   58185.3 |  27373.9 |  29151   | 101732   |
| Q09     | clickhouse |   3881.7 |      5 |     17156.6 |   16664.3 |   1851.4 |  14379.2 |  18904.3 |
| Q09     | duckdb     |   4594.5 |      5 |      9925.9 |   10174.8 |   1883.5 |   8364.8 |  13169.1 |
| Q09     | exasol     |   2002.5 |      5 |      8295.3 |    7809.7 |   1097   |   5865   |   8500.3 |
| Q09     | starrocks  |   5971.4 |      5 |     10891.7 |   10745.1 |   2560.4 |   6860   |  13350.7 |
| Q09     | trino      |  29469   |      5 |     93514.4 |   94779.9 |   9533.5 |  82240.3 | 108398   |
| Q10     | clickhouse |   7963   |      5 |     34745   |   33311.1 |   3598.4 |  28191.4 |  37109.7 |
| Q10     | duckdb     |   2271.1 |      5 |      6014.5 |    6025.3 |   2629.7 |   2140.6 |   9389.4 |
| Q10     | exasol     |    709   |      5 |      2284.1 |    1919.7 |    641.9 |   1207.2 |   2512.8 |
| Q10     | starrocks  |   3070.8 |      5 |      6262   |    6367   |    666.4 |   5763.1 |   7497.1 |
| Q10     | trino      |  10306.4 |      5 |     67465.4 |   74087.3 |  30304.2 |  42229.3 | 121734   |
| Q11     | clickhouse |    908.8 |      5 |     11073.7 |    8601   |   4697.1 |   2669.2 |  13287.5 |
| Q11     | duckdb     |    203.8 |      5 |      7147.4 |    7083.7 |   2176.9 |   4326.3 |  10343   |
| Q11     | exasol     |    152.6 |      5 |       427.5 |     432.5 |    137.9 |    238.7 |    625.3 |
| Q11     | starrocks  |    336.6 |      5 |       770.9 |     824.1 |    322.2 |    537.8 |   1300   |
| Q11     | trino      |   1954.6 |      5 |      6010.5 |    5850.3 |   2242.7 |   2218.8 |   8027.3 |
| Q12     | clickhouse |   3148.5 |      5 |      9076   |    8215   |   3642.9 |   3084.8 |  11927   |
| Q12     | duckdb     |   1550.4 |      5 |      8521.2 |    8604.5 |   2007.2 |   5604.8 |  10636.6 |
| Q12     | exasol     |    148.9 |      5 |       580.4 |     687.2 |    202.7 |    493   |    939.7 |
| Q12     | starrocks  |   2060.5 |      5 |      4598.8 |    4675.7 |   1198   |   3068.5 |   5860.8 |
| Q12     | trino      |   4716.2 |      5 |     34469.4 |   36137.6 |   6740.7 |  29864.3 |  44391.2 |
| Q13     | clickhouse |   4146.6 |      5 |     11789.2 |   13700   |   4171.4 |  10607.5 |  20852.3 |
| Q13     | duckdb     |   3717.4 |      5 |      7374.4 |    7567.3 |   2631.9 |   3692.1 |  10404.5 |
| Q13     | exasol     |   1483.2 |      5 |      5472.2 |    4941.8 |   1254.1 |   2702   |   5589.9 |
| Q13     | starrocks  |   3331.4 |      5 |      8357.9 |    8176.5 |   3450.1 |   3377.3 |  12550.1 |
| Q13     | trino      |  15069.5 |      5 |     55334.1 |   52514.4 |  10367.8 |  35429.3 |  63251.5 |
| Q14     | clickhouse |    332.9 |      5 |      3026.9 |    3628.8 |   2174.2 |   1376.9 |   6041.9 |
| Q14     | duckdb     |   1077.9 |      5 |      4811.1 |    6169.8 |   3124.9 |   3268.4 |  11072   |
| Q14     | exasol     |    145.2 |      5 |       696.8 |     697.7 |    183.5 |    526.6 |    974.7 |
| Q14     | starrocks  |   1533.9 |      5 |      3258.7 |    3211.9 |    932.7 |   1696.6 |   4008.8 |
| Q14     | trino      |   6023   |      5 |     21432.7 |   22873.9 |   8625.7 |  14038.4 |  36902.7 |
| Q15     | clickhouse |    320.6 |      5 |      1940.2 |    2827.7 |   1528.4 |   1496.8 |   4653.2 |
| Q15     | duckdb     |    917.1 |      5 |      8257.2 |    7554.9 |   3568.8 |   3417   |  11778.7 |
| Q15     | exasol     |    398.1 |      5 |      1277.9 |    1297.7 |     64.7 |   1230.4 |   1398.7 |
| Q15     | starrocks  |    802.9 |      5 |      3757.7 |    3673.2 |   1056.5 |   2506.6 |   5280.2 |
| Q15     | trino      |  11224.6 |      5 |     34756.5 |   33791.6 |   3530.9 |  28421.7 |  38015.2 |
| Q16     | clickhouse |    973.7 |      5 |      6426.6 |    7267   |   3534   |   2839.1 |  11406.6 |
| Q16     | duckdb     |    683.8 |      5 |      4405.5 |    4742.1 |   1685.4 |   3515.5 |   7631.8 |
| Q16     | exasol     |    577   |      5 |      1940.6 |    1970.4 |    108.2 |   1874.5 |   2154   |
| Q16     | starrocks  |    731.7 |      5 |      1446.1 |    1443.4 |    128.7 |   1288.5 |   1598.5 |
| Q16     | trino      |   3400.7 |      5 |     11472.6 |   15442.5 |   8235.5 |   8456.8 |  28646.8 |
| Q17     | clickhouse |   1819   |      5 |      8387.1 |    8703.7 |   1680.1 |   6979.7 |  10692.5 |
| Q17     | duckdb     |   1628.4 |      5 |      9051.2 |    8734.6 |   1958.5 |   6312.8 |  10692.6 |
| Q17     | exasol     |     28.3 |      5 |        96   |     115.2 |     32.1 |     91.1 |    163.2 |
| Q17     | starrocks  |   1170.4 |      5 |      2740.7 |    2762.6 |   1050.2 |   1300.4 |   4265.8 |
| Q17     | trino      |  11931.2 |      5 |     42701.7 |   39332.8 |   9987.7 |  22629.7 |  49005.1 |
| Q18     | clickhouse |   6421.3 |      5 |     28194.6 |   26853.3 |   5098.6 |  18777.1 |  31620.4 |
| Q18     | duckdb     |   3106.4 |      5 |      7531.2 |    8817.3 |   2739.5 |   6334.2 |  12590.9 |
| Q18     | exasol     |    980.3 |      5 |      3440.2 |    3162.4 |    790.3 |   1755.2 |   3607.8 |
| Q18     | starrocks  |   4637.1 |      5 |     31875.6 |   29884.6 |   8356.2 |  17946.4 |  40353.8 |
| Q18     | trino      |  12700   |      5 |     44852.6 |   45884.7 |  17533.8 |  23515.2 |  70169.1 |
| Q19     | clickhouse |   9573.7 |      5 |     26180.7 |   25511.7 |   3872.8 |  20439   |  30991.5 |
| Q19     | duckdb     |   1553.7 |      5 |      6297.5 |    7013.1 |   2816.3 |   4480.1 |  11153.6 |
| Q19     | exasol     |     59.2 |      5 |        87.5 |     132.7 |     87.3 |     50.2 |    266.6 |
| Q19     | starrocks  |   2089.3 |      5 |      2489.7 |    2875.4 |    786.3 |   2141.4 |   3950   |
| Q19     | trino      |   7122   |      5 |     17227.6 |   19845.3 |  12485.5 |   8095.3 |  35026.2 |
| Q20     | clickhouse |   2485.5 |      5 |     11507.1 |   10825.2 |   2020.7 |   8078.5 |  13013.2 |
| Q20     | duckdb     |   1402.7 |      5 |      5965.5 |    7185.3 |   3094.1 |   3581.5 |  10487.5 |
| Q20     | exasol     |    342.8 |      5 |       615   |     824.4 |    346   |    528.6 |   1317.3 |
| Q20     | starrocks  |   1582   |      5 |      4279.6 |    4128.7 |   1013   |   3087.2 |   5646.8 |
| Q20     | trino      |   7196.8 |      5 |     24974.3 |   24940.1 |   7850   |  12312.5 |  32830.8 |
| Q21     | clickhouse |   4528.3 |      5 |     17827.8 |   16787.1 |   2859.3 |  13166.8 |  20328.4 |
| Q21     | duckdb     |   7102   |      5 |     10275.9 |   12136.4 |   4142.2 |   9751.5 |  19508.5 |
| Q21     | exasol     |    833.7 |      5 |      2233.4 |    2386.1 |    807.8 |   1426.5 |   3340.8 |
| Q21     | starrocks  |   5272.8 |      5 |     13840.8 |   15632.7 |   6679.3 |   8369.8 |  24806.4 |
| Q21     | trino      |  31516.6 |      5 |     83160.1 |   79294.6 |  21061.7 |  48182.6 |  99509.1 |
| Q22     | clickhouse |    799   |      5 |      6035.7 |    5549.9 |   1501.1 |   3724.5 |   7484.5 |
| Q22     | duckdb     |    811.6 |      5 |      6796.9 |    7546.1 |   3652   |   3077.1 |  12361.3 |
| Q22     | exasol     |    176.6 |      5 |       615   |     566.9 |    199.8 |    225.5 |    751.5 |
| Q22     | starrocks  |    660.2 |      5 |      2080.6 |    1954.4 |    924.4 |    563.5 |   3084.9 |
| Q22     | trino      |   4021.7 |      5 |     17547.1 |   17889.1 |   7673.2 |  10240.6 |  26800.5 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        5422.9 |         16859.5 |    3.11 |      0.32 | False    |
| Q02     | exasol            | clickhouse          |         208   |         10254.7 |   49.3  |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         593.1 |         24165.1 |   40.74 |      0.02 | False    |
| Q04     | exasol            | clickhouse          |         418.6 |         22242.9 |   53.14 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1758.3 |         24220.6 |   13.78 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         261.1 |          1960.7 |    7.51 |      0.13 | False    |
| Q07     | exasol            | clickhouse          |        2160.6 |         37998.2 |   17.59 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         530   |         28236.5 |   53.28 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        8295.3 |         17156.6 |    2.07 |      0.48 | False    |
| Q10     | exasol            | clickhouse          |        2284.1 |         34745   |   15.21 |      0.07 | False    |
| Q11     | exasol            | clickhouse          |         427.5 |         11073.7 |   25.9  |      0.04 | False    |
| Q12     | exasol            | clickhouse          |         580.4 |          9076   |   15.64 |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        5472.2 |         11789.2 |    2.15 |      0.46 | False    |
| Q14     | exasol            | clickhouse          |         696.8 |          3026.9 |    4.34 |      0.23 | False    |
| Q15     | exasol            | clickhouse          |        1277.9 |          1940.2 |    1.52 |      0.66 | False    |
| Q16     | exasol            | clickhouse          |        1940.6 |          6426.6 |    3.31 |      0.3  | False    |
| Q17     | exasol            | clickhouse          |          96   |          8387.1 |   87.37 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3440.2 |         28194.6 |    8.2  |      0.12 | False    |
| Q19     | exasol            | clickhouse          |          87.5 |         26180.7 |  299.21 |      0    | False    |
| Q20     | exasol            | clickhouse          |         615   |         11507.1 |   18.71 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        2233.4 |         17827.8 |    7.98 |      0.13 | False    |
| Q22     | exasol            | clickhouse          |         615   |          6035.7 |    9.81 |      0.1  | False    |
| Q01     | exasol            | duckdb              |        5422.9 |          6134.1 |    1.13 |      0.88 | False    |
| Q02     | exasol            | duckdb              |         208   |          4224.6 |   20.31 |      0.05 | False    |
| Q03     | exasol            | duckdb              |         593.1 |          5109.2 |    8.61 |      0.12 | False    |
| Q04     | exasol            | duckdb              |         418.6 |         10608.8 |   25.34 |      0.04 | False    |
| Q05     | exasol            | duckdb              |        1758.3 |          5518.8 |    3.14 |      0.32 | False    |
| Q06     | exasol            | duckdb              |         261.1 |          3831.9 |   14.68 |      0.07 | False    |
| Q07     | exasol            | duckdb              |        2160.6 |          4097.8 |    1.9  |      0.53 | False    |
| Q08     | exasol            | duckdb              |         530   |          5339.9 |   10.08 |      0.1  | False    |
| Q09     | exasol            | duckdb              |        8295.3 |          9925.9 |    1.2  |      0.84 | False    |
| Q10     | exasol            | duckdb              |        2284.1 |          6014.5 |    2.63 |      0.38 | False    |
| Q11     | exasol            | duckdb              |         427.5 |          7147.4 |   16.72 |      0.06 | False    |
| Q12     | exasol            | duckdb              |         580.4 |          8521.2 |   14.68 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        5472.2 |          7374.4 |    1.35 |      0.74 | False    |
| Q14     | exasol            | duckdb              |         696.8 |          4811.1 |    6.9  |      0.14 | False    |
| Q15     | exasol            | duckdb              |        1277.9 |          8257.2 |    6.46 |      0.15 | False    |
| Q16     | exasol            | duckdb              |        1940.6 |          4405.5 |    2.27 |      0.44 | False    |
| Q17     | exasol            | duckdb              |          96   |          9051.2 |   94.28 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3440.2 |          7531.2 |    2.19 |      0.46 | False    |
| Q19     | exasol            | duckdb              |          87.5 |          6297.5 |   71.97 |      0.01 | False    |
| Q20     | exasol            | duckdb              |         615   |          5965.5 |    9.7  |      0.1  | False    |
| Q21     | exasol            | duckdb              |        2233.4 |         10275.9 |    4.6  |      0.22 | False    |
| Q22     | exasol            | duckdb              |         615   |          6796.9 |   11.05 |      0.09 | False    |
| Q01     | exasol            | starrocks           |        5422.9 |         16212.7 |    2.99 |      0.33 | False    |
| Q02     | exasol            | starrocks           |         208   |           901.5 |    4.33 |      0.23 | False    |
| Q03     | exasol            | starrocks           |         593.1 |          3365   |    5.67 |      0.18 | False    |
| Q04     | exasol            | starrocks           |         418.6 |          4772.5 |   11.4  |      0.09 | False    |
| Q05     | exasol            | starrocks           |        1758.3 |          7668.8 |    4.36 |      0.23 | False    |
| Q06     | exasol            | starrocks           |         261.1 |          2745.2 |   10.51 |      0.1  | False    |
| Q07     | exasol            | starrocks           |        2160.6 |          6803.2 |    3.15 |      0.32 | False    |
| Q08     | exasol            | starrocks           |         530   |          6552.5 |   12.36 |      0.08 | False    |
| Q09     | exasol            | starrocks           |        8295.3 |         10891.7 |    1.31 |      0.76 | False    |
| Q10     | exasol            | starrocks           |        2284.1 |          6262   |    2.74 |      0.36 | False    |
| Q11     | exasol            | starrocks           |         427.5 |           770.9 |    1.8  |      0.55 | False    |
| Q12     | exasol            | starrocks           |         580.4 |          4598.8 |    7.92 |      0.13 | False    |
| Q13     | exasol            | starrocks           |        5472.2 |          8357.9 |    1.53 |      0.65 | False    |
| Q14     | exasol            | starrocks           |         696.8 |          3258.7 |    4.68 |      0.21 | False    |
| Q15     | exasol            | starrocks           |        1277.9 |          3757.7 |    2.94 |      0.34 | False    |
| Q16     | exasol            | starrocks           |        1940.6 |          1446.1 |    0.75 |      1.34 | True     |
| Q17     | exasol            | starrocks           |          96   |          2740.7 |   28.55 |      0.04 | False    |
| Q18     | exasol            | starrocks           |        3440.2 |         31875.6 |    9.27 |      0.11 | False    |
| Q19     | exasol            | starrocks           |          87.5 |          2489.7 |   28.45 |      0.04 | False    |
| Q20     | exasol            | starrocks           |         615   |          4279.6 |    6.96 |      0.14 | False    |
| Q21     | exasol            | starrocks           |        2233.4 |         13840.8 |    6.2  |      0.16 | False    |
| Q22     | exasol            | starrocks           |         615   |          2080.6 |    3.38 |      0.3  | False    |
| Q01     | exasol            | trino               |        5422.9 |         44866.6 |    8.27 |      0.12 | False    |
| Q02     | exasol            | trino               |         208   |         10695.4 |   51.42 |      0.02 | False    |
| Q03     | exasol            | trino               |         593.1 |         32129.5 |   54.17 |      0.02 | False    |
| Q04     | exasol            | trino               |         418.6 |         36089.4 |   86.21 |      0.01 | False    |
| Q05     | exasol            | trino               |        1758.3 |         61145.4 |   34.78 |      0.03 | False    |
| Q06     | exasol            | trino               |         261.1 |         18138.3 |   69.47 |      0.01 | False    |
| Q07     | exasol            | trino               |        2160.6 |         38559.6 |   17.85 |      0.06 | False    |
| Q08     | exasol            | trino               |         530   |         49258.6 |   92.94 |      0.01 | False    |
| Q09     | exasol            | trino               |        8295.3 |         93514.4 |   11.27 |      0.09 | False    |
| Q10     | exasol            | trino               |        2284.1 |         67465.4 |   29.54 |      0.03 | False    |
| Q11     | exasol            | trino               |         427.5 |          6010.5 |   14.06 |      0.07 | False    |
| Q12     | exasol            | trino               |         580.4 |         34469.4 |   59.39 |      0.02 | False    |
| Q13     | exasol            | trino               |        5472.2 |         55334.1 |   10.11 |      0.1  | False    |
| Q14     | exasol            | trino               |         696.8 |         21432.7 |   30.76 |      0.03 | False    |
| Q15     | exasol            | trino               |        1277.9 |         34756.5 |   27.2  |      0.04 | False    |
| Q16     | exasol            | trino               |        1940.6 |         11472.6 |    5.91 |      0.17 | False    |
| Q17     | exasol            | trino               |          96   |         42701.7 |  444.81 |      0    | False    |
| Q18     | exasol            | trino               |        3440.2 |         44852.6 |   13.04 |      0.08 | False    |
| Q19     | exasol            | trino               |          87.5 |         17227.6 |  196.89 |      0.01 | False    |
| Q20     | exasol            | trino               |         615   |         24974.3 |   40.61 |      0.02 | False    |
| Q21     | exasol            | trino               |        2233.4 |         83160.1 |   37.23 |      0.03 | False    |
| Q22     | exasol            | trino               |         615   |         17547.1 |   28.53 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 16351.0 | 15140.0 | 1725.0 | 45367.3 |
| 1 | 28 | 15290.0 | 11080.4 | 1940.2 | 37998.2 |
| 2 | 27 | 16203.5 | 14379.2 | 1563.3 | 35386.6 |
| 3 | 27 | 14919.4 | 11406.6 | 1333.4 | 42657.6 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 11080.4ms
- Slowest stream median: 15140.0ms
- Stream performance variation: 36.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7109.6 | 6808.0 | 2140.6 | 19508.5 |
| 1 | 28 | 7167.9 | 6294.9 | 1325.5 | 13679.9 |
| 2 | 27 | 7255.2 | 7036.7 | 3581.5 | 13169.1 |
| 3 | 27 | 7324.8 | 7147.4 | 3233.6 | 12590.9 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6294.9ms
- Slowest stream median: 7147.4ms
- Stream performance variation: 13.5% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1976.7 | 1868.9 | 93.5 | 5589.9 |
| 1 | 28 | 1396.6 | 608.5 | 91.1 | 8500.3 |
| 2 | 27 | 1946.3 | 825.6 | 50.2 | 8295.3 |
| 3 | 27 | 1563.2 | 640.6 | 96.0 | 8302.4 |

**Performance Analysis for Exasol:**
- Fastest stream median: 608.5ms
- Slowest stream median: 1868.9ms
- Stream performance variation: 207.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7631.3 | 6143.4 | 563.5 | 26226.4 |
| 1 | 28 | 6519.8 | 3452.4 | 538.2 | 40353.8 |
| 2 | 27 | 7154.3 | 5467.9 | 537.8 | 36480.4 |
| 3 | 27 | 6258.5 | 3345.9 | 769.1 | 33020.7 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3345.9ms
- Slowest stream median: 6143.4ms
- Stream performance variation: 83.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 39598.8 | 34805.6 | 7312.6 | 99509.1 |
| 1 | 28 | 35435.6 | 34735.3 | 8027.3 | 82240.3 |
| 2 | 27 | 40432.3 | 29909.6 | 2218.8 | 121734.2 |
| 3 | 27 | 36605.3 | 36089.4 | 5682.1 | 101731.9 |

**Performance Analysis for Trino:**
- Fastest stream median: 29909.6ms
- Slowest stream median: 36089.4ms
- Stream performance variation: 20.7% difference between fastest and slowest streams
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
- Median runtime: 13227.1ms
- Average runtime: 15693.3ms
- Fastest query: 1333.4ms
- Slowest query: 45367.3ms

**duckdb:**
- Median runtime: 6796.4ms
- Average runtime: 7213.0ms
- Fastest query: 1325.5ms
- Slowest query: 19508.5ms

**exasol:**
- Median runtime: 847.9ms
- Average runtime: 1720.1ms
- Fastest query: 50.2ms
- Slowest query: 8500.3ms

**starrocks:**
- Median runtime: 4272.7ms
- Average runtime: 6894.4ms
- Fastest query: 537.8ms
- Slowest query: 40353.8ms

**trino:**
- Median runtime: 34649.6ms
- Average runtime: 38008.9ms
- Fastest query: 2218.8ms
- Slowest query: 121734.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_sf_50-benchmark.zip`](ext_scalability_sf_50-benchmark.zip)

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
  - max_memory_usage: 15000000000
  - max_bytes_before_external_group_by: 5000000000
  - max_bytes_before_external_sort: 5000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 10000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 48GB
  - query_max_memory_per_node: 35GB

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts