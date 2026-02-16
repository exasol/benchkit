# Extended Scalability - Node Scaling (1 Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-01-28 22:11:23

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **clickhouse**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 758.0ms median runtime
- trino was 37.9x slower- Tested 440 total query executions across 22 different TPC-H queries
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
- **Hostname:** ip-10-0-1-33

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
- **Hostname:** ip-10-0-1-47

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
- **Hostname:** ip-10-0-1-56

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
- **Hostname:** ip-10-0-1-198


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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS449DA40D78C74D702 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS449DA40D78C74D702

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS449DA40D78C74D702 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS449DA40D78C74D702 /data

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
node.id=41ba0f4c-5f37-4e68-9022-6ee3636e5426
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
query.max-memory=35GB
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS681A9776A1E7BA607 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS681A9776A1E7BA607

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS681A9776A1E7BA607 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS681A9776A1E7BA607 /data

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
# Performance tuning
mem_limit = 80%
# Parallel execution
parallel_fragment_exec_instance_num = 16

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25C232F6CBAE8B890 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25C232F6CBAE8B890

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25C232F6CBAE8B890 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS25C232F6CBAE8B890 /data

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
    &lt;max_server_memory_usage&gt;53066924032&lt;/max_server_memory_usage&gt;
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
unzip ext_scalability_nodes_1-benchmark.zip
cd ext_scalability_nodes_1

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
| Q01     | clickhouse |   4583.4 |      5 |     17182.1 |   15892.9 |   3637.9 |  10891.4 |  20382.5 |
| Q01     | exasol     |   1562.5 |      5 |      5417   |    4674.5 |   1451.9 |   2408.9 |   5770.3 |
| Q01     | starrocks  |   6952   |      5 |     22185.8 |   22234.4 |   9083.8 |  13554.3 |  36901.8 |
| Q01     | trino      |   9804.3 |      5 |     38155.4 |   32245.7 |  12165.3 |  15277.6 |  42984   |
| Q02     | clickhouse |   2075.6 |      5 |      8676.4 |   10193.9 |   4553.8 |   4692.6 |  15778.8 |
| Q02     | exasol     |     77.9 |      5 |       181.1 |     188.1 |     35   |    158.9 |    247.8 |
| Q02     | starrocks  |    531.9 |      5 |       804.7 |     968.3 |    292.9 |    714.4 |   1387.3 |
| Q02     | trino      |   5089   |      5 |      9195.2 |    8460.7 |   2766.6 |   4073.4 |  11267.1 |
| Q03     | clickhouse |   7380.1 |      5 |     24214.1 |   19838.7 |   8870.1 |   6862.5 |  27406.4 |
| Q03     | exasol     |    614.7 |      5 |       669.9 |    1313.8 |    949.6 |    588.3 |   2413.7 |
| Q03     | starrocks  |   3380.3 |      5 |      3327.7 |    5254.1 |   3063.2 |   3150.2 |  10125.2 |
| Q03     | trino      |  12760.9 |      5 |     28013.7 |   37747.5 |  30437.3 |  11750.6 |  82343.2 |
| Q04     | clickhouse |   8810   |      5 |     27064.9 |   25955.3 |   4123.6 |  20863.2 |  29886.8 |
| Q04     | exasol     |    111.7 |      5 |       408   |     426.1 |    186.8 |    200.8 |    719.9 |
| Q04     | starrocks  |   1719.8 |      5 |      3779   |    4031.9 |   1311.1 |   2288.7 |   5693.3 |
| Q04     | trino      |   9443.9 |      5 |     22440.2 |   23458.5 |  10532.8 |  10379.2 |  34079.2 |
| Q05     | clickhouse |   5959.6 |      5 |     24708.3 |   24569.5 |   3262.9 |  21102.1 |  28370.6 |
| Q05     | exasol     |    483.7 |      5 |      1716.1 |    1557.1 |    452.2 |    757.8 |   1844.3 |
| Q05     | starrocks  |   2870   |      5 |      7047.3 |    7181.5 |   1030.6 |   5733.9 |   8468.4 |
| Q05     | trino      |  10893   |      5 |     45669.1 |   52996.1 |  26539.7 |  35167.5 |  99170.4 |
| Q06     | clickhouse |    324   |      5 |      2941.8 |    2684.3 |    486   |   1830.5 |   2961.6 |
| Q06     | exasol     |     72.1 |      5 |       208.2 |     266.2 |    190.5 |    134.3 |    593.5 |
| Q06     | starrocks  |   1535.2 |      5 |      2942.1 |    2915.7 |   1062.4 |   1492.6 |   4456.5 |
| Q06     | trino      |   4410.5 |      5 |     13713.7 |   12600.6 |   4906.5 |   5216.3 |  18662.5 |
| Q07     | clickhouse |  13609.1 |      5 |     38917   |   37343.2 |  14979.7 |  12677.7 |  53067.5 |
| Q07     | exasol     |    617.3 |      5 |      2158.1 |    1949.2 |    788.3 |    594.2 |   2572   |
| Q07     | starrocks  |   3443.8 |      5 |      7317.7 |    7090.3 |   2395.7 |   3467.5 |   9858.6 |
| Q07     | trino      |   9575.4 |      5 |     26640.3 |   26993.1 |  12211.2 |   8550.7 |  39039.3 |
| Q08     | clickhouse |   7421.7 |      5 |     31299.8 |   30331.9 |   5864.6 |  21043.3 |  37137.4 |
| Q08     | exasol     |    159.8 |      5 |       516.4 |     640.1 |    248.1 |    403.9 |   1017.9 |
| Q08     | starrocks  |   2961.4 |      5 |      5151.9 |    6243.2 |   1893.9 |   4622.1 |   8648.8 |
| Q08     | trino      |  12917   |      5 |     28814.1 |   37912.1 |  20147.3 |  20251.3 |  70025.5 |
| Q09     | clickhouse |   4602.7 |      5 |     21440   |   20385   |   3269.1 |  15014.9 |  23624.7 |
| Q09     | exasol     |   2011   |      5 |      8365.9 |    7840.1 |   1134.1 |   5889.5 |   8576.5 |
| Q09     | starrocks  |   5872.1 |      5 |     12804.3 |   12595.1 |   2205.5 |  10056.3 |  15408.9 |
| Q09     | trino      |  29519   |      5 |     83043.9 |   84030   |   3097.8 |  80726.9 |  89066.2 |
| Q10     | clickhouse |   9121   |      5 |     33075.6 |   33903.1 |   4366.5 |  29538   |  40579.8 |
| Q10     | exasol     |    709.3 |      5 |      2058   |    1933.8 |    634.6 |   1219.6 |   2568.5 |
| Q10     | starrocks  |   3001.1 |      5 |      7612.6 |    7338   |    735.4 |   6546.8 |   8037.9 |
| Q10     | trino      |   9511.7 |      5 |     50409.5 |   65209.4 |  34049   |  35692.8 | 112315   |
| Q11     | clickhouse |   1080.8 |      5 |      9346.3 |    8853.9 |   2903.6 |   4341.4 |  12026.8 |
| Q11     | exasol     |    151.7 |      5 |       445.8 |     451.5 |    163.3 |    235.2 |    691.4 |
| Q11     | starrocks  |    352.8 |      5 |       615.8 |     701.5 |    223   |    559.2 |   1097.3 |
| Q11     | trino      |   1928.3 |      5 |      6023.6 |    5739.8 |   2174.9 |   2335.9 |   8390.2 |
| Q12     | clickhouse |   3708.2 |      5 |      5529.3 |    7785   |   5537.5 |   4282.2 |  17609.4 |
| Q12     | exasol     |    149.3 |      5 |       566.3 |     619.4 |    156.2 |    492.1 |    881.7 |
| Q12     | starrocks  |   2035.8 |      5 |      4152   |    4820.3 |   1385.2 |   3715.3 |   7033.1 |
| Q12     | trino      |   6316.5 |      5 |     28536.9 |   32487.1 |   9113.4 |  24515.4 |  47469.3 |
| Q13     | clickhouse |   4893.9 |      5 |     12836.1 |   15037   |   4567.2 |  10313   |  21722   |
| Q13     | exasol     |   1528.8 |      5 |      5358.3 |    4840.6 |   1257   |   2599   |   5552   |
| Q13     | starrocks  |   3364.3 |      5 |      8759   |    8830.2 |   3563.7 |   3449.4 |  12798.5 |
| Q13     | trino      |  14485.2 |      5 |     69281   |   64903.9 |  21823   |  31236.9 |  89072   |
| Q14     | clickhouse |    340.7 |      5 |      2386.9 |    2758   |   1301.5 |   1349.6 |   4604.2 |
| Q14     | exasol     |    147.6 |      5 |       606.2 |     633.2 |     69.9 |    561.8 |    711.5 |
| Q14     | starrocks  |   1533.4 |      5 |      3324.3 |    3391.8 |    676.1 |   2421.7 |   4278.2 |
| Q14     | trino      |   6014.5 |      5 |     29454   |   29281.4 |   7425.9 |  19592.4 |  36521.6 |
| Q15     | clickhouse |    384.1 |      5 |      3334.3 |    3693.1 |   1894.6 |   1961.3 |   6883.1 |
| Q15     | exasol     |    396.5 |      5 |      1236.3 |    1248.9 |     45.9 |   1206.6 |   1303.4 |
| Q15     | starrocks  |    824.5 |      5 |      3517.3 |    3813   |    971.5 |   3010.7 |   5329.8 |
| Q15     | trino      |  11135.5 |      5 |     28592.8 |   30171.2 |   3332.1 |  27314.2 |  35406.4 |
| Q16     | clickhouse |   1069.9 |      5 |      5756   |    7594.2 |   3134.1 |   5616.4 |  12891.3 |
| Q16     | exasol     |    583.8 |      5 |      1976.2 |    2008.9 |    140.7 |   1888.9 |   2235.4 |
| Q16     | starrocks  |    751.8 |      5 |      1549.1 |    1682.6 |    603.7 |   1188.1 |   2676.3 |
| Q16     | trino      |   3352.4 |      5 |      9266.7 |   13693.2 |   7795.7 |   6275.4 |  22730.2 |
| Q17     | clickhouse |   1937.4 |      5 |      8455.7 |   10790.6 |   5042.4 |   7180.1 |  19229.3 |
| Q17     | exasol     |     29.3 |      5 |        61.4 |      70.3 |     16.9 |     55.2 |     93.9 |
| Q17     | starrocks  |   1163.8 |      5 |      2917.5 |    3047.3 |    484.3 |   2449.7 |   3757.9 |
| Q17     | trino      |  12338   |      5 |     47040.3 |   46260.9 |   6051.2 |  36957.4 |  53227.9 |
| Q18     | clickhouse |   8044.5 |      5 |     33317.7 |   35032.3 |   9111.3 |  23325.2 |  47229.2 |
| Q18     | exasol     |    984.5 |      5 |      3349.3 |    3130.2 |    788.8 |   1755.5 |   3725.7 |
| Q18     | starrocks  |   4752.4 |      5 |     29442.3 |   30039.3 |  13817.4 |  16771.1 |  51670.9 |
| Q18     | trino      |  12110.1 |      5 |     50806.6 |   47429.1 |  13961   |  25861.3 |  60564.8 |
| Q19     | clickhouse |  10028.6 |      5 |     28693.6 |   30235.9 |   2778   |  28179.7 |  34627.7 |
| Q19     | exasol     |     60.1 |      5 |       168.1 |     191.6 |    118.9 |     87.2 |    369.9 |
| Q19     | starrocks  |   2056.6 |      5 |      3678.1 |    3987   |    846.6 |   2935.1 |   5077.8 |
| Q19     | trino      |   6999.9 |      5 |      8652.5 |   15548.7 |  11032.9 |   7423.2 |  32961.2 |
| Q20     | clickhouse |   2846.7 |      5 |     12772.5 |   13291.6 |   2689.1 |   9846.1 |  17034.3 |
| Q20     | exasol     |    346.2 |      5 |       616.7 |     863.4 |    438.1 |    496.7 |   1497.5 |
| Q20     | starrocks  |   1701.2 |      5 |      3222.7 |    3305.6 |    892.1 |   2529.5 |   4710.3 |
| Q20     | trino      |   6851.9 |      5 |     15554.6 |   20438.4 |  11336.7 |   8624.3 |  36267.7 |
| Q21     | clickhouse |   5004.6 |      5 |     17830.2 |   18503.1 |   3954.3 |  13997.3 |  23877.2 |
| Q21     | exasol     |    841.3 |      5 |      2853.8 |    2658.8 |   1066.1 |   1361.2 |   3774.6 |
| Q21     | starrocks  |   5403.5 |      5 |     14611   |   15990.9 |   6066   |   8802.4 |  25443.6 |
| Q21     | trino      |  29961.2 |      5 |     71559.3 |   66024.5 |  14532.3 |  50149.5 |  81298.4 |
| Q22     | clickhouse |    901.1 |      5 |      7322.4 |    6634.4 |   3738.4 |   2317.6 |  10258.9 |
| Q22     | exasol     |    178.3 |      5 |       677   |     598.7 |    183.9 |    271.6 |    706.2 |
| Q22     | starrocks  |    645.6 |      5 |      2007.7 |    2060.7 |   1093   |    560.5 |   3461.8 |
| Q22     | trino      |   4068.7 |      5 |     12542.3 |   14110.8 |   7979   |   4163.8 |  24270.2 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        5417   |         17182.1 |    3.17 |      0.32 | False    |
| Q02     | exasol            | clickhouse          |         181.1 |          8676.4 |   47.91 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         669.9 |         24214.1 |   36.15 |      0.03 | False    |
| Q04     | exasol            | clickhouse          |         408   |         27064.9 |   66.34 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1716.1 |         24708.3 |   14.4  |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         208.2 |          2941.8 |   14.13 |      0.07 | False    |
| Q07     | exasol            | clickhouse          |        2158.1 |         38917   |   18.03 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         516.4 |         31299.8 |   60.61 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        8365.9 |         21440   |    2.56 |      0.39 | False    |
| Q10     | exasol            | clickhouse          |        2058   |         33075.6 |   16.07 |      0.06 | False    |
| Q11     | exasol            | clickhouse          |         445.8 |          9346.3 |   20.97 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |         566.3 |          5529.3 |    9.76 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        5358.3 |         12836.1 |    2.4  |      0.42 | False    |
| Q14     | exasol            | clickhouse          |         606.2 |          2386.9 |    3.94 |      0.25 | False    |
| Q15     | exasol            | clickhouse          |        1236.3 |          3334.3 |    2.7  |      0.37 | False    |
| Q16     | exasol            | clickhouse          |        1976.2 |          5756   |    2.91 |      0.34 | False    |
| Q17     | exasol            | clickhouse          |          61.4 |          8455.7 |  137.71 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3349.3 |         33317.7 |    9.95 |      0.1  | False    |
| Q19     | exasol            | clickhouse          |         168.1 |         28693.6 |  170.69 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         616.7 |         12772.5 |   20.71 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        2853.8 |         17830.2 |    6.25 |      0.16 | False    |
| Q22     | exasol            | clickhouse          |         677   |          7322.4 |   10.82 |      0.09 | False    |
| Q01     | exasol            | starrocks           |        5417   |         22185.8 |    4.1  |      0.24 | False    |
| Q02     | exasol            | starrocks           |         181.1 |           804.7 |    4.44 |      0.23 | False    |
| Q03     | exasol            | starrocks           |         669.9 |          3327.7 |    4.97 |      0.2  | False    |
| Q04     | exasol            | starrocks           |         408   |          3779   |    9.26 |      0.11 | False    |
| Q05     | exasol            | starrocks           |        1716.1 |          7047.3 |    4.11 |      0.24 | False    |
| Q06     | exasol            | starrocks           |         208.2 |          2942.1 |   14.13 |      0.07 | False    |
| Q07     | exasol            | starrocks           |        2158.1 |          7317.7 |    3.39 |      0.29 | False    |
| Q08     | exasol            | starrocks           |         516.4 |          5151.9 |    9.98 |      0.1  | False    |
| Q09     | exasol            | starrocks           |        8365.9 |         12804.3 |    1.53 |      0.65 | False    |
| Q10     | exasol            | starrocks           |        2058   |          7612.6 |    3.7  |      0.27 | False    |
| Q11     | exasol            | starrocks           |         445.8 |           615.8 |    1.38 |      0.72 | False    |
| Q12     | exasol            | starrocks           |         566.3 |          4152   |    7.33 |      0.14 | False    |
| Q13     | exasol            | starrocks           |        5358.3 |          8759   |    1.63 |      0.61 | False    |
| Q14     | exasol            | starrocks           |         606.2 |          3324.3 |    5.48 |      0.18 | False    |
| Q15     | exasol            | starrocks           |        1236.3 |          3517.3 |    2.85 |      0.35 | False    |
| Q16     | exasol            | starrocks           |        1976.2 |          1549.1 |    0.78 |      1.28 | True     |
| Q17     | exasol            | starrocks           |          61.4 |          2917.5 |   47.52 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3349.3 |         29442.3 |    8.79 |      0.11 | False    |
| Q19     | exasol            | starrocks           |         168.1 |          3678.1 |   21.88 |      0.05 | False    |
| Q20     | exasol            | starrocks           |         616.7 |          3222.7 |    5.23 |      0.19 | False    |
| Q21     | exasol            | starrocks           |        2853.8 |         14611   |    5.12 |      0.2  | False    |
| Q22     | exasol            | starrocks           |         677   |          2007.7 |    2.97 |      0.34 | False    |
| Q01     | exasol            | trino               |        5417   |         38155.4 |    7.04 |      0.14 | False    |
| Q02     | exasol            | trino               |         181.1 |          9195.2 |   50.77 |      0.02 | False    |
| Q03     | exasol            | trino               |         669.9 |         28013.7 |   41.82 |      0.02 | False    |
| Q04     | exasol            | trino               |         408   |         22440.2 |   55    |      0.02 | False    |
| Q05     | exasol            | trino               |        1716.1 |         45669.1 |   26.61 |      0.04 | False    |
| Q06     | exasol            | trino               |         208.2 |         13713.7 |   65.87 |      0.02 | False    |
| Q07     | exasol            | trino               |        2158.1 |         26640.3 |   12.34 |      0.08 | False    |
| Q08     | exasol            | trino               |         516.4 |         28814.1 |   55.8  |      0.02 | False    |
| Q09     | exasol            | trino               |        8365.9 |         83043.9 |    9.93 |      0.1  | False    |
| Q10     | exasol            | trino               |        2058   |         50409.5 |   24.49 |      0.04 | False    |
| Q11     | exasol            | trino               |         445.8 |          6023.6 |   13.51 |      0.07 | False    |
| Q12     | exasol            | trino               |         566.3 |         28536.9 |   50.39 |      0.02 | False    |
| Q13     | exasol            | trino               |        5358.3 |         69281   |   12.93 |      0.08 | False    |
| Q14     | exasol            | trino               |         606.2 |         29454   |   48.59 |      0.02 | False    |
| Q15     | exasol            | trino               |        1236.3 |         28592.8 |   23.13 |      0.04 | False    |
| Q16     | exasol            | trino               |        1976.2 |          9266.7 |    4.69 |      0.21 | False    |
| Q17     | exasol            | trino               |          61.4 |         47040.3 |  766.13 |      0    | False    |
| Q18     | exasol            | trino               |        3349.3 |         50806.6 |   15.17 |      0.07 | False    |
| Q19     | exasol            | trino               |         168.1 |          8652.5 |   51.47 |      0.02 | False    |
| Q20     | exasol            | trino               |         616.7 |         15554.6 |   25.22 |      0.04 | False    |
| Q21     | exasol            | trino               |        2853.8 |         71559.3 |   25.08 |      0.04 | False    |
| Q22     | exasol            | trino               |         677   |         12542.3 |   18.53 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 18106.6 | 16713.9 | 1830.5 | 43508.1 |
| 1 | 28 | 16988.6 | 14851.6 | 1349.6 | 40579.8 |
| 2 | 27 | 17962.1 | 15014.9 | 2386.9 | 47229.2 |
| 3 | 27 | 16255.3 | 12891.3 | 2669.0 | 53067.5 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 12891.3ms
- Slowest stream median: 16713.9ms
- Stream performance variation: 29.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1995.6 | 1873.3 | 135.1 | 5410.8 |
| 1 | 28 | 1390.1 | 669.4 | 61.4 | 8561.4 |
| 2 | 27 | 1963.2 | 757.8 | 87.2 | 8365.9 |
| 3 | 27 | 1582.1 | 677.0 | 55.2 | 8576.5 |

**Performance Analysis for Exasol:**
- Fastest stream median: 669.4ms
- Slowest stream median: 1873.3ms
- Stream performance variation: 179.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7874.8 | 6643.2 | 559.2 | 32834.2 |
| 1 | 28 | 6910.2 | 3509.4 | 636.2 | 51670.9 |
| 2 | 27 | 7398.9 | 4710.3 | 599.2 | 36901.8 |
| 3 | 27 | 6439.3 | 3507.5 | 615.8 | 22578.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3507.5ms
- Slowest stream median: 6643.2ms
- Stream performance variation: 89.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 38162.5 | 29625.3 | 4163.8 | 99170.4 |
| 1 | 28 | 31743.6 | 27126.2 | 4073.4 | 83000.9 |
| 2 | 27 | 38259.5 | 35167.5 | 2335.9 | 112315.2 |
| 3 | 27 | 31419.9 | 28034.7 | 5730.0 | 89066.2 |

**Performance Analysis for Trino:**
- Fastest stream median: 27126.2ms
- Slowest stream median: 35167.5ms
- Stream performance variation: 29.6% difference between fastest and slowest streams
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
- Median runtime: 14795.3ms
- Average runtime: 17332.1ms
- Fastest query: 1349.6ms
- Slowest query: 53067.5ms

**exasol:**
- Median runtime: 758.0ms
- Average runtime: 1732.0ms
- Fastest query: 55.2ms
- Slowest query: 8576.5ms

**starrocks:**
- Median runtime: 4227.2ms
- Average runtime: 7160.1ms
- Fastest query: 559.2ms
- Slowest query: 51670.9ms

**trino:**
- Median runtime: 28703.4ms
- Average runtime: 34897.4ms
- Fastest query: 2335.9ms
- Slowest query: 112315.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_nodes_1-benchmark.zip`](ext_scalability_nodes_1-benchmark.zip)

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
  - query_max_memory: 35GB
  - query_max_memory_per_node: 35GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 4
  - replication_num: 1


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