# Extended Scalability - Scale Factor 100 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-01-30 02:11:12

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
- exasol was the fastest overall with 702.3ms median runtime
- trino was 43.8x slower- Tested 550 total query executions across 22 different TPC-H queries
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
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-205

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
- **Hostname:** ip-10-0-1-97

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
- **Hostname:** ip-10-0-1-111

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
- **Hostname:** ip-10-0-1-174

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
- **Hostname:** ip-10-0-1-189


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

# Create 132GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Create raw partition for Exasol (752GB)
sudo parted /dev/nvme1n1 mkpart primary 132GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 132GiB 100%

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS652F0614FCC8AAE6C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS652F0614FCC8AAE6C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS652F0614FCC8AAE6C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS652F0614FCC8AAE6C /data

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
node.id=61de262a-f3ba-4df3-8ae5-b3f1b9958716
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648FD7FA37837C8C6 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648FD7FA37837C8C6

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648FD7FA37837C8C6 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648FD7FA37837C8C6 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS653A42D16094BE0B1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS653A42D16094BE0B1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS653A42D16094BE0B1 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS653A42D16094BE0B1 /data

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
    &lt;max_server_memory_usage&gt;106335639961&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;16&lt;/max_concurrent_queries&gt;
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
            &lt;max_memory_usage&gt;30000000000&lt;/max_memory_usage&gt;
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
- Memory limit: `96g`
- Max threads: `16`
- Max memory usage: `30.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22E7F1D52C622284A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22E7F1D52C622284A

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22E7F1D52C622284A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22E7F1D52C622284A /data

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
- **Scale factor:** 100
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
unzip ext_scalability_sf_100-benchmark.zip
cd ext_scalability_sf_100

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
| Q01     | clickhouse |   4747.3 |      5 |     11045.7 |   13991.4 |   8092.8 |   8476   |  28164.9 |
| Q01     | duckdb     |   2243.8 |      5 |      5802.6 |    6219.2 |   1774.2 |   4213.1 |   9070.6 |
| Q01     | exasol     |   1579.8 |      5 |      5403   |    4744.9 |   1250.3 |   2641.8 |   5637.9 |
| Q01     | starrocks  |   7184.2 |      5 |     47266.5 |   36403.1 |  16313.1 |  13535   |  48821.1 |
| Q01     | trino      |   9547.5 |      5 |     20817.1 |   33288.8 |  23323.2 |  13879.3 |  61094.8 |
| Q02     | clickhouse |   2020.8 |      5 |      9160.6 |   13829.9 |   8522.7 |   6729.1 |  27381.9 |
| Q02     | duckdb     |    482.8 |      5 |      4427.7 |    5842.4 |   2677   |   3283.4 |   9844.7 |
| Q02     | exasol     |    108.5 |      5 |       196.9 |     204.4 |     34.2 |    169.7 |    259.8 |
| Q02     | starrocks  |    448.3 |      5 |       995.5 |    1125.3 |    359.2 |    811.2 |   1689.6 |
| Q02     | trino      |   5171.2 |      5 |      9493.4 |    9570   |   3289.1 |   4987.7 |  12970.2 |
| Q03     | clickhouse |   8235.1 |      5 |     23284.1 |   21476.6 |   9027.1 |   7797.1 |  30874.5 |
| Q03     | duckdb     |   1522.4 |      5 |      4197.1 |    6130.8 |   4000.2 |   3716   |  13185.6 |
| Q03     | exasol     |    610.4 |      5 |       742   |    1332.8 |    940.6 |    595.9 |   2458.1 |
| Q03     | starrocks  |   3741.1 |      5 |      3577.8 |    7232.4 |   6635.7 |   3491.4 |  18845.3 |
| Q03     | trino      |  16849.6 |      5 |     18009.7 |   29041.6 |  17468.8 |  15500.9 |  51862.9 |
| Q04     | clickhouse |  15700.8 |      5 |     32477   |   32342.8 |   2874.2 |  28117   |  35869.8 |
| Q04     | duckdb     |   1441   |      5 |      8975   |    9902.9 |   2740.5 |   7507.1 |  14075   |
| Q04     | exasol     |    111.5 |      5 |       422.5 |     393.9 |    124   |    188.9 |    526.1 |
| Q04     | starrocks  |   1411.8 |      5 |      3351   |    3357.9 |   1243.5 |   2238.7 |   5313.6 |
| Q04     | trino      |   9442.4 |      5 |     36009.3 |   38301.3 |  21597.9 |  16344   |  70665.7 |
| Q05     | clickhouse |   5963.8 |      5 |     22121.5 |   21495.2 |   4112.5 |  16931   |  27063.5 |
| Q05     | duckdb     |   1656.4 |      5 |      5722.8 |    5745.1 |   1276   |   4203.2 |   7695.3 |
| Q05     | exasol     |    472.1 |      5 |      1485.7 |    1334.2 |    358.5 |    701.1 |   1577.6 |
| Q05     | starrocks  |   3222.5 |      5 |      5725.7 |    5542.9 |    518.6 |   4810.1 |   6159.2 |
| Q05     | trino      |  17072   |      5 |     57154.9 |   70130.4 |  35058.3 |  44717   | 128752   |
| Q06     | clickhouse |    288.8 |      5 |      1791.3 |    3652.3 |   2732.4 |   1573.5 |   7277.7 |
| Q06     | duckdb     |    407.8 |      5 |      3811.4 |    3712.7 |    686.8 |   2884.8 |   4434.6 |
| Q06     | exasol     |     75.3 |      5 |       208.7 |     278.6 |    197.3 |    141   |    616.6 |
| Q06     | starrocks  |    799.2 |      5 |      2062.7 |    2130.4 |   1085.1 |   1188.8 |   3823.8 |
| Q06     | trino      |   4359.9 |      5 |     27357   |   21148.1 |  10963.2 |   7782.5 |  30914.5 |
| Q07     | clickhouse |  15995.6 |      5 |     38772.3 |   40449.5 |  17326.3 |  18143.1 |  66562.7 |
| Q07     | duckdb     |   1432.5 |      5 |      5240.9 |    6560.9 |   4191.6 |   3795.3 |  13945.1 |
| Q07     | exasol     |    596.1 |      5 |      2265.6 |    1979.6 |    781.7 |    591.3 |   2433.4 |
| Q07     | starrocks  |   2874.8 |      5 |      6450   |    6224.7 |   2137.1 |   2763.3 |   8234.4 |
| Q07     | trino      |   9866   |      5 |     21556   |   28477.3 |  19562.6 |   9651.2 |  59534.8 |
| Q08     | clickhouse |   7693.9 |      5 |     31923   |   30768.2 |   3548.2 |  24906.2 |  34219.4 |
| Q08     | duckdb     |   1533.1 |      5 |      5874.5 |    6133.3 |    993.3 |   4998.5 |   7680   |
| Q08     | exasol     |    138.7 |      5 |       512.8 |     464   |    116.9 |    257.6 |    543   |
| Q08     | starrocks  |   2194.9 |      5 |      5403.3 |    5328.4 |   2119.5 |   2683   |   8175.8 |
| Q08     | trino      |   9781.9 |      5 |     44018.1 |   38665.9 |  13298.3 |  16097.6 |  50317.8 |
| Q09     | clickhouse |   5067.2 |      5 |     24340.3 |   25437.4 |   3766.8 |  21026.1 |  30327.7 |
| Q09     | duckdb     |   4415.4 |      5 |      9672.9 |   10265.1 |   1994.4 |   8581.3 |  13651.8 |
| Q09     | exasol     |   2000.9 |      5 |      7775.1 |    7541.6 |    677.3 |   6470.2 |   8280.5 |
| Q09     | starrocks  |   5567.3 |      5 |     14840.3 |   15405.5 |   2050.4 |  13187.5 |  18577.2 |
| Q09     | trino      |  40991.7 |      5 |    142128   |  162083   |  40202.8 | 129125   | 218969   |
| Q10     | clickhouse |   9529.1 |      5 |     28610.1 |   27579   |   3422   |  23019   |  31376   |
| Q10     | duckdb     |   2282.8 |      5 |      6134.8 |    7577.5 |   5214.5 |   2260.3 |  16221   |
| Q10     | exasol     |    799.8 |      5 |      2573.4 |    2091.8 |    680.8 |   1316.1 |   2609   |
| Q10     | starrocks  |   3152.3 |      5 |      4111.4 |    5178.2 |   1585.4 |   3906.4 |   7162.5 |
| Q10     | trino      |  12398.4 |      5 |     32799.8 |   32628.6 |   5496.8 |  23742.2 |  37952.7 |
| Q11     | clickhouse |   1379.3 |      5 |      4499.2 |    8072.8 |   8842.4 |   2876.4 |  23703   |
| Q11     | duckdb     |    199.8 |      5 |      6548.2 |    5828.4 |   2061.8 |   3485.4 |   7835.5 |
| Q11     | exasol     |    184.3 |      5 |       452.2 |     445.4 |    115.6 |    264   |    584.9 |
| Q11     | starrocks  |    344.1 |      5 |       715.7 |     651.1 |    153.1 |    444.3 |    782.8 |
| Q11     | trino      |   1904.9 |      5 |      3928   |    4338.9 |   1879   |   2665.8 |   7282.5 |
| Q12     | clickhouse |   4356.5 |      5 |      5453.1 |    7771.9 |   5407.4 |   4764.4 |  17410.7 |
| Q12     | duckdb     |   1597.2 |      5 |     10867   |   11004.8 |   2938.3 |   8429.6 |  15834   |
| Q12     | exasol     |    151.4 |      5 |       598.5 |     603.1 |     60.6 |    547   |    703.5 |
| Q12     | starrocks  |   1583.9 |      5 |      5467.2 |    5110.5 |   2039.4 |   2582.2 |   7858.4 |
| Q12     | trino      |   5542.7 |      5 |     42720.7 |   39792   |  26718.8 |  12556.7 |  75159.6 |
| Q13     | clickhouse |   6797.2 |      5 |     17756.1 |   18667.5 |   3753.4 |  15051.1 |  24808.3 |
| Q13     | duckdb     |   4050.6 |      5 |      7737.3 |    7998.1 |   2682.9 |   3989.7 |  10999.6 |
| Q13     | exasol     |   1396.5 |      5 |      4931.8 |    4361.4 |   1191.8 |   2233.5 |   4940   |
| Q13     | starrocks  |   3588.1 |      5 |      9995   |    9290.7 |   3904   |   3667.7 |  13568.9 |
| Q13     | trino      |  16497.8 |      5 |     35733.3 |   43903.2 |  15106.6 |  31163.1 |  63642.6 |
| Q14     | clickhouse |    337.2 |      5 |      4962.1 |    5509.8 |   2152   |   2955.2 |   8427.6 |
| Q14     | duckdb     |   1118.7 |      5 |      7752.9 |    8597.6 |   4072.8 |   4589.8 |  13840.8 |
| Q14     | exasol     |    162.6 |      5 |       613.5 |     582.4 |     60.5 |    482   |    628.8 |
| Q14     | starrocks  |   1188   |      5 |      3848.8 |    3920   |   1817.9 |   1918.7 |   6794.7 |
| Q14     | trino      |   6509.3 |      5 |     15351.9 |   24901.5 |  16934.2 |  10848.6 |  49097.1 |
| Q15     | clickhouse |    524.3 |      5 |      6960.6 |    7886.3 |   3790.3 |   3941.6 |  13659.9 |
| Q15     | duckdb     |    933.3 |      5 |      7389.6 |    7409.2 |   2545.4 |   3493.9 |  10530.6 |
| Q15     | exasol     |    522.3 |      5 |      1532.5 |    1545.3 |     57   |   1505.6 |   1644.7 |
| Q15     | starrocks  |    665.5 |      5 |      2780   |    4869.1 |   4530.8 |   1728.2 |  12515.1 |
| Q15     | trino      |  11438.9 |      5 |     46412.3 |   46304.9 |  11312.3 |  30552.2 |  62468.1 |
| Q16     | clickhouse |   1078.7 |      5 |      7516.3 |    6534.4 |   2126.8 |   3465.9 |   8441.6 |
| Q16     | duckdb     |    736.3 |      5 |      4709.5 |    5359.3 |   2040   |   2740.4 |   8065.8 |
| Q16     | exasol     |    641.7 |      5 |      2000.9 |    1990.8 |     45.9 |   1933   |   2053.6 |
| Q16     | starrocks  |    837.9 |      5 |      1324.9 |    1441.5 |    346.6 |   1217.1 |   2052.6 |
| Q16     | trino      |   3434.3 |      5 |      8454.7 |   10749.8 |   6006.4 |   6926.4 |  21381.3 |
| Q17     | clickhouse |   2350.6 |      5 |      7827.4 |   10944.1 |   6847.4 |   4341.9 |  21303.2 |
| Q17     | duckdb     |   1710.8 |      5 |      7590.9 |    6881.6 |   3879.9 |   1663.7 |  11262.3 |
| Q17     | exasol     |     34   |      5 |        83.4 |      89.2 |     22.4 |     65.1 |    123.2 |
| Q17     | starrocks  |    882.7 |      5 |      1769.9 |    1895.9 |   1036   |    836.5 |   3468.9 |
| Q17     | trino      |  15424.4 |      5 |     24370.8 |   40377.8 |  25556.8 |  22374.8 |  80430.3 |
| Q18     | clickhouse |   7006.8 |      5 |     34776.6 |   31913.4 |   9093.1 |  15959.5 |  38914.3 |
| Q18     | duckdb     |   3441.9 |      5 |      8621.9 |    9828.7 |   3064.8 |   6888.7 |  14543.8 |
| Q18     | exasol     |   1055.5 |      5 |      3702.4 |    3356.6 |    829.5 |   1879.8 |   3856.1 |
| Q18     | starrocks  |   6630.9 |      5 |     33817.6 |   30865.6 |   7740.5 |  18270.6 |  38288.3 |
| Q18     | trino      |  14541   |      5 |     53569.2 |   52727.3 |  17944.2 |  28911.4 |  77227.2 |
| Q19     | clickhouse |   9945.6 |      5 |     27032.9 |   26934   |   5244.6 |  20832.9 |  34230.9 |
| Q19     | duckdb     |   1585.8 |      5 |      8010.3 |    8327.3 |   3203.4 |   4268.5 |  13217.9 |
| Q19     | exasol     |     47   |      5 |        90.2 |     126.8 |     63.5 |     81.7 |    229.3 |
| Q19     | starrocks  |   1621.2 |      5 |      2464   |    3039.5 |   1601.8 |   1736   |   5805.3 |
| Q19     | trino      |   7867.5 |      5 |     26898.2 |   23102.1 |  10104.8 |   9833.2 |  35496   |
| Q20     | clickhouse |   3460.5 |      5 |     14012.5 |   14437.1 |   4697.6 |   7082.1 |  18669   |
| Q20     | duckdb     |   1469   |      5 |      4227   |    6628.4 |   5225.5 |   3666   |  15861.5 |
| Q20     | exasol     |    413.3 |      5 |       761.9 |     902.5 |    318.7 |    572.7 |   1285.2 |
| Q20     | starrocks  |   1423.7 |      5 |      2205.7 |    3025.1 |   1742.9 |   1410.7 |   5676.9 |
| Q20     | trino      |   7196.7 |      5 |     17398.6 |   20996.2 |  14200.6 |  10509.3 |  45811.7 |
| Q21     | clickhouse |   5923.6 |      5 |     23333   |   22986.5 |   5139.4 |  16415.9 |  30207.4 |
| Q21     | duckdb     |   7709.6 |      5 |     11782.4 |   12885.4 |   2614.9 |  10274.4 |  15838.8 |
| Q21     | exasol     |    788.8 |      5 |      2364.4 |    2155.4 |    804.5 |   1140.7 |   3037   |
| Q21     | starrocks  |   9254.4 |      5 |     25471.3 |   31955.2 |  20975.5 |   9649.6 |  64083.4 |
| Q21     | trino      |  38695.5 |      5 |    152280   |  153367   |  22810.9 | 123144   | 183198   |
| Q22     | clickhouse |    909.1 |      5 |     11023.8 |   11379.8 |   3596.4 |   6958.5 |  15955.1 |
| Q22     | duckdb     |    794.2 |      5 |      6704.3 |    7408.8 |   3573.8 |   4065.9 |  11937.6 |
| Q22     | exasol     |    180.1 |      5 |       680.8 |     615.1 |    151.9 |    344.3 |    695.3 |
| Q22     | starrocks  |    582.2 |      5 |      1292.7 |    2059.3 |   1590   |    521.2 |   4533   |
| Q22     | trino      |   4930.5 |      5 |     14982.4 |   14197.7 |   5850.9 |   4730.2 |  19244.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        5403   |         11045.7 |    2.04 |      0.49 | False    |
| Q02     | exasol            | clickhouse          |         196.9 |          9160.6 |   46.52 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         742   |         23284.1 |   31.38 |      0.03 | False    |
| Q04     | exasol            | clickhouse          |         422.5 |         32477   |   76.87 |      0.01 | False    |
| Q05     | exasol            | clickhouse          |        1485.7 |         22121.5 |   14.89 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         208.7 |          1791.3 |    8.58 |      0.12 | False    |
| Q07     | exasol            | clickhouse          |        2265.6 |         38772.3 |   17.11 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         512.8 |         31923   |   62.25 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        7775.1 |         24340.3 |    3.13 |      0.32 | False    |
| Q10     | exasol            | clickhouse          |        2573.4 |         28610.1 |   11.12 |      0.09 | False    |
| Q11     | exasol            | clickhouse          |         452.2 |          4499.2 |    9.95 |      0.1  | False    |
| Q12     | exasol            | clickhouse          |         598.5 |          5453.1 |    9.11 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |        4931.8 |         17756.1 |    3.6  |      0.28 | False    |
| Q14     | exasol            | clickhouse          |         613.5 |          4962.1 |    8.09 |      0.12 | False    |
| Q15     | exasol            | clickhouse          |        1532.5 |          6960.6 |    4.54 |      0.22 | False    |
| Q16     | exasol            | clickhouse          |        2000.9 |          7516.3 |    3.76 |      0.27 | False    |
| Q17     | exasol            | clickhouse          |          83.4 |          7827.4 |   93.85 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3702.4 |         34776.6 |    9.39 |      0.11 | False    |
| Q19     | exasol            | clickhouse          |          90.2 |         27032.9 |  299.7  |      0    | False    |
| Q20     | exasol            | clickhouse          |         761.9 |         14012.5 |   18.39 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        2364.4 |         23333   |    9.87 |      0.1  | False    |
| Q22     | exasol            | clickhouse          |         680.8 |         11023.8 |   16.19 |      0.06 | False    |
| Q01     | exasol            | duckdb              |        5403   |          5802.6 |    1.07 |      0.93 | False    |
| Q02     | exasol            | duckdb              |         196.9 |          4427.7 |   22.49 |      0.04 | False    |
| Q03     | exasol            | duckdb              |         742   |          4197.1 |    5.66 |      0.18 | False    |
| Q04     | exasol            | duckdb              |         422.5 |          8975   |   21.24 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1485.7 |          5722.8 |    3.85 |      0.26 | False    |
| Q06     | exasol            | duckdb              |         208.7 |          3811.4 |   18.26 |      0.05 | False    |
| Q07     | exasol            | duckdb              |        2265.6 |          5240.9 |    2.31 |      0.43 | False    |
| Q08     | exasol            | duckdb              |         512.8 |          5874.5 |   11.46 |      0.09 | False    |
| Q09     | exasol            | duckdb              |        7775.1 |          9672.9 |    1.24 |      0.8  | False    |
| Q10     | exasol            | duckdb              |        2573.4 |          6134.8 |    2.38 |      0.42 | False    |
| Q11     | exasol            | duckdb              |         452.2 |          6548.2 |   14.48 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         598.5 |         10867   |   18.16 |      0.06 | False    |
| Q13     | exasol            | duckdb              |        4931.8 |          7737.3 |    1.57 |      0.64 | False    |
| Q14     | exasol            | duckdb              |         613.5 |          7752.9 |   12.64 |      0.08 | False    |
| Q15     | exasol            | duckdb              |        1532.5 |          7389.6 |    4.82 |      0.21 | False    |
| Q16     | exasol            | duckdb              |        2000.9 |          4709.5 |    2.35 |      0.42 | False    |
| Q17     | exasol            | duckdb              |          83.4 |          7590.9 |   91.02 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3702.4 |          8621.9 |    2.33 |      0.43 | False    |
| Q19     | exasol            | duckdb              |          90.2 |          8010.3 |   88.81 |      0.01 | False    |
| Q20     | exasol            | duckdb              |         761.9 |          4227   |    5.55 |      0.18 | False    |
| Q21     | exasol            | duckdb              |        2364.4 |         11782.4 |    4.98 |      0.2  | False    |
| Q22     | exasol            | duckdb              |         680.8 |          6704.3 |    9.85 |      0.1  | False    |
| Q01     | exasol            | starrocks           |        5403   |         47266.5 |    8.75 |      0.11 | False    |
| Q02     | exasol            | starrocks           |         196.9 |           995.5 |    5.06 |      0.2  | False    |
| Q03     | exasol            | starrocks           |         742   |          3577.8 |    4.82 |      0.21 | False    |
| Q04     | exasol            | starrocks           |         422.5 |          3351   |    7.93 |      0.13 | False    |
| Q05     | exasol            | starrocks           |        1485.7 |          5725.7 |    3.85 |      0.26 | False    |
| Q06     | exasol            | starrocks           |         208.7 |          2062.7 |    9.88 |      0.1  | False    |
| Q07     | exasol            | starrocks           |        2265.6 |          6450   |    2.85 |      0.35 | False    |
| Q08     | exasol            | starrocks           |         512.8 |          5403.3 |   10.54 |      0.09 | False    |
| Q09     | exasol            | starrocks           |        7775.1 |         14840.3 |    1.91 |      0.52 | False    |
| Q10     | exasol            | starrocks           |        2573.4 |          4111.4 |    1.6  |      0.63 | False    |
| Q11     | exasol            | starrocks           |         452.2 |           715.7 |    1.58 |      0.63 | False    |
| Q12     | exasol            | starrocks           |         598.5 |          5467.2 |    9.13 |      0.11 | False    |
| Q13     | exasol            | starrocks           |        4931.8 |          9995   |    2.03 |      0.49 | False    |
| Q14     | exasol            | starrocks           |         613.5 |          3848.8 |    6.27 |      0.16 | False    |
| Q15     | exasol            | starrocks           |        1532.5 |          2780   |    1.81 |      0.55 | False    |
| Q16     | exasol            | starrocks           |        2000.9 |          1324.9 |    0.66 |      1.51 | True     |
| Q17     | exasol            | starrocks           |          83.4 |          1769.9 |   21.22 |      0.05 | False    |
| Q18     | exasol            | starrocks           |        3702.4 |         33817.6 |    9.13 |      0.11 | False    |
| Q19     | exasol            | starrocks           |          90.2 |          2464   |   27.32 |      0.04 | False    |
| Q20     | exasol            | starrocks           |         761.9 |          2205.7 |    2.89 |      0.35 | False    |
| Q21     | exasol            | starrocks           |        2364.4 |         25471.3 |   10.77 |      0.09 | False    |
| Q22     | exasol            | starrocks           |         680.8 |          1292.7 |    1.9  |      0.53 | False    |
| Q01     | exasol            | trino               |        5403   |         20817.1 |    3.85 |      0.26 | False    |
| Q02     | exasol            | trino               |         196.9 |          9493.4 |   48.21 |      0.02 | False    |
| Q03     | exasol            | trino               |         742   |         18009.7 |   24.27 |      0.04 | False    |
| Q04     | exasol            | trino               |         422.5 |         36009.3 |   85.23 |      0.01 | False    |
| Q05     | exasol            | trino               |        1485.7 |         57154.9 |   38.47 |      0.03 | False    |
| Q06     | exasol            | trino               |         208.7 |         27357   |  131.08 |      0.01 | False    |
| Q07     | exasol            | trino               |        2265.6 |         21556   |    9.51 |      0.11 | False    |
| Q08     | exasol            | trino               |         512.8 |         44018.1 |   85.84 |      0.01 | False    |
| Q09     | exasol            | trino               |        7775.1 |        142128   |   18.28 |      0.05 | False    |
| Q10     | exasol            | trino               |        2573.4 |         32799.8 |   12.75 |      0.08 | False    |
| Q11     | exasol            | trino               |         452.2 |          3928   |    8.69 |      0.12 | False    |
| Q12     | exasol            | trino               |         598.5 |         42720.7 |   71.38 |      0.01 | False    |
| Q13     | exasol            | trino               |        4931.8 |         35733.3 |    7.25 |      0.14 | False    |
| Q14     | exasol            | trino               |         613.5 |         15351.9 |   25.02 |      0.04 | False    |
| Q15     | exasol            | trino               |        1532.5 |         46412.3 |   30.29 |      0.03 | False    |
| Q16     | exasol            | trino               |        2000.9 |          8454.7 |    4.23 |      0.24 | False    |
| Q17     | exasol            | trino               |          83.4 |         24370.8 |  292.22 |      0    | False    |
| Q18     | exasol            | trino               |        3702.4 |         53569.2 |   14.47 |      0.07 | False    |
| Q19     | exasol            | trino               |          90.2 |         26898.2 |  298.21 |      0    | False    |
| Q20     | exasol            | trino               |         761.9 |         17398.6 |   22.84 |      0.04 | False    |
| Q21     | exasol            | trino               |        2364.4 |        152280   |   64.41 |      0.02 | False    |
| Q22     | exasol            | trino               |         680.8 |         14982.4 |   22.01 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 19205.7 | 18657.2 | 1573.5 | 38914.3 |
| 1 | 28 | 18430.5 | 14896.3 | 1701.5 | 42235.0 |
| 2 | 27 | 18262.8 | 18423.4 | 1791.3 | 35869.8 |
| 3 | 27 | 17533.0 | 14279.8 | 2876.4 | 66562.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 14279.8ms
- Slowest stream median: 18657.2ms
- Stream performance variation: 30.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7318.8 | 6620.9 | 2260.3 | 15838.8 |
| 1 | 28 | 7553.6 | 7073.9 | 1663.7 | 14075.0 |
| 2 | 27 | 7647.0 | 7610.7 | 2884.8 | 16221.0 |
| 3 | 27 | 7716.4 | 7493.2 | 2740.4 | 15834.0 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6620.9ms
- Slowest stream median: 7610.7ms
- Stream performance variation: 15.0% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1925.9 | 1906.4 | 141.0 | 4935.9 |
| 1 | 28 | 1400.8 | 578.2 | 65.1 | 8280.5 |
| 2 | 27 | 1896.2 | 703.5 | 81.7 | 7775.1 |
| 3 | 27 | 1531.5 | 598.5 | 76.3 | 7793.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 578.2ms
- Slowest stream median: 1906.4ms
- Stream performance variation: 229.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 9179.5 | 4583.9 | 521.2 | 64083.4 |
| 1 | 28 | 7983.0 | 3692.5 | 444.3 | 47798.4 |
| 2 | 27 | 8241.4 | 3848.8 | 534.9 | 47266.5 |
| 3 | 27 | 8414.6 | 4533.0 | 777.7 | 48821.1 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3692.5ms
- Slowest stream median: 4583.9ms
- Stream performance variation: 24.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 48854.2 | 33448.2 | 2665.8 | 183198.1 |
| 1 | 28 | 34820.8 | 29135.8 | 3928.0 | 129125.0 |
| 2 | 27 | 47904.6 | 28911.4 | 2879.7 | 218968.8 |
| 3 | 27 | 39042.5 | 30552.2 | 4938.7 | 152280.1 |

**Performance Analysis for Trino:**
- Fastest stream median: 28911.4ms
- Slowest stream median: 33448.2ms
- Stream performance variation: 15.7% difference between fastest and slowest streams
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
- Median runtime: 17583.4ms
- Average runtime: 18366.4ms
- Fastest query: 1573.5ms
- Slowest query: 66562.7ms

**duckdb:**
- Median runtime: 7349.6ms
- Average runtime: 7556.7ms
- Fastest query: 1663.7ms
- Slowest query: 16221.0ms

**exasol:**
- Median runtime: 702.3ms
- Average runtime: 1688.2ms
- Fastest query: 65.1ms
- Slowest query: 8280.5ms

**starrocks:**
- Median runtime: 3888.0ms
- Average runtime: 8456.9ms
- Fastest query: 444.3ms
- Slowest query: 64083.4ms

**trino:**
- Median runtime: 30733.3ms
- Average runtime: 42640.6ms
- Fastest query: 2665.8ms
- Slowest query: 218968.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_sf_100-benchmark.zip`](ext_scalability_sf_100-benchmark.zip)

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
  - max_memory_usage: 30000000000
  - max_bytes_before_external_group_by: 10000000000
  - max_bytes_before_external_sort: 10000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 20000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 96GB
  - query_max_memory_per_node: 71GB

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts