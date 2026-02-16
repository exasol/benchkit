# Streamlined Scalability - Node Scaling (8 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-02-10 16:14:40

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **starrocks**
- **exasol**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 1762.7ms median runtime
- trino was 33.2x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 8-node cluster

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 8-node cluster

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 8-node cluster

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 8-node cluster


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.large
- **Clickhouse Instance:** r6id.large
- **Trino Instance:** r6id.large
- **Starrocks Instance:** r6id.large


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 8 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 8 Nodes] Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 8 Nodes] Create raw partition for Exasol (39GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 8 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 8 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 8 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# [All 8 Nodes] Add exasol user to sudo group
sudo usermod -aG sudo exasol || true

# Set password for exasol user (interactive)
sudo passwd exasol

```

**Tool Setup:**
```bash
# Download c4 cluster management tool v4.28.5
wget -q --tries=3 --retry-connrefused --waitretry=5 https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

```

**Configuration:**
```bash
# Create c4 configuration file on remote system
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.2.0
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=96000
CCC_ADMINUI_START_SERVER=true&#34; | tee /tmp/exasol_c4.conf &gt; /dev/null

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
# [All 8 Nodes] Configuring passwordless sudo on all nodes
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
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2D1FA9C1B68681DD8 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2D1FA9C1B68681DD8

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2D1FA9C1B68681DD8 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2D1FA9C1B68681DD8 /data

# [All 8 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 8 Nodes] Create trino data directory
sudo mkdir -p /data/trino

```

**Prerequisites:**
```bash
# [All 8 Nodes] Add Eclipse Temurin (Adoptium) repository for Java 22
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg 2&gt;/dev/null || true
echo &#34;deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(lsb_release -sc) main&#34; | sudo tee /etc/apt/sources.list.d/adoptium.list

# [All 8 Nodes] Install Java 25 (required by Trino 479+)
sudo apt-get update &amp;&amp; sudo apt-get install -y temurin-25-jdk

# [All 8 Nodes] Install python symlink (required by Trino launcher)
sudo apt-get install -y python-is-python3

```

**User Setup:**
```bash
# [All 8 Nodes] Create Trino system user
sudo useradd -r -s /bin/false trino || true

```

**Installation:**
```bash
# [All 8 Nodes] Download Trino server version 479
wget -q --tries=3 --retry-connrefused --waitretry=5 https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

# [All 8 Nodes] Extract Trino server to /opt
sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/

# [All 8 Nodes] Create symlink /opt/trino-server
sudo ln -sf /opt/trino-server-479 /opt/trino-server

# [All 8 Nodes] Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

# [All 8 Nodes] Create etc symlink for Trino launcher
sudo ln -sf /etc/trino /opt/trino-server/etc

```

**Configuration:**
```bash
# [All 8 Nodes] Configure Trino node properties
sudo tee /etc/trino/node.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
node.environment=production
node.id=4c7c727a-c809-4d3d-a8b7-5bd7a01a2559
node.data-dir=/var/trino/data
EOF

# [All 8 Nodes] Configure JVM with 12G heap (80% of 15.3G total RAM)
sudo tee /etc/trino/jvm.config &gt; /dev/null &lt;&lt; &#39;EOF&#39;
-server
-Xmx12G
-Xms12G
-XX:+UseG1GC
-XX:G1HeapRegionSize=32M
-XX:+ExplicitGCInvokesConcurrent
-XX:+HeapDumpOnOutOfMemoryError
-XX:+ExitOnOutOfMemoryError
-XX:ReservedCodeCacheSize=512M
-Djdk.attach.allowAttachSelf=true
-Djdk.nio.maxCachedBufferSize=2000000
EOF

# [All 8 Nodes] Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
discovery.uri=http://&lt;PRIVATE_IP&gt;:8080
query.max-memory=72GB
query.max-memory-per-node=8GB
EOF

# [All 8 Nodes] Configure Hive catalog with file metastore at local:///data/trino/hive-metastore
sudo tee /etc/trino/catalog/hive.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
connector.name=hive
hive.metastore=file
hive.metastore.catalog.dir=local:///data/trino/hive-metastore
hive.storage-format=PARQUET
hive.compression-codec=SNAPPY
fs.native-local.enabled=true
local.location=/
fs.native-s3.enabled=true
s3.region=eu-west-1
EOF

# [All 8 Nodes] Create Trino systemd service
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
# [All 8 Nodes] Reload systemd daemon
sudo systemctl daemon-reload

```

**Setup:**
```bash
# [All 8 Nodes] Execute sudo command on remote system
sudo mkdir -p /data/trino/hive-metastore

# [All 8 Nodes] Execute sudo command on remote system
sudo chown -R trino:trino /data/trino/hive-metastore

# [All 8 Nodes] Execute sudo command on remote system
sudo chmod -R 755 /data/trino/hive-metastore

# [All 8 Nodes] Execute sudo command on remote system
sudo mkdir -p /etc/trino/catalog

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS284A7FF278FF42D11 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS284A7FF278FF42D11

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS284A7FF278FF42D11 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS284A7FF278FF42D11 /data

# [All 8 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 8 Nodes] Create starrocks data directory
sudo mkdir -p /data/starrocks

# [All 8 Nodes] Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# [All 8 Nodes] Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 8 Nodes] Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# [All 8 Nodes] Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 8 Nodes] Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# [All 8 Nodes] Configure StarRocks FE
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

# [All 8 Nodes] Configure StarRocks BE
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
# [All 8 Nodes] Start StarRocks FE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 8 Nodes] Start StarRocks BE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 8 Nodes] Execute test command on remote system
test -f /tmp/starrocks-4.0.4.tar.gz &amp;&amp; echo exists

```

**Cluster Configuration:**
```bash
# Add FE follower node 1
mysql -h &lt;PRIVATE_IP&gt; -P 9030 -u root -e &#34;ALTER SYSTEM ADD FOLLOWER &#39;&lt;PRIVATE_IP&gt;:9010&#39;&#34;

# Register BE on node 0
mysql -h &lt;PRIVATE_IP&gt; -P 9030 -u root -e &#34;ALTER SYSTEM ADD BACKEND &#39;&lt;PRIVATE_IP&gt;:9050&#39;&#34;

```


**Tuning Parameters:**

**Data Directory:** `/data/starrocks`



#### Clickhouse 25.10.2.65 Setup

**Storage Configuration:**
```bash
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2AF5B5371836C725A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2AF5B5371836C725A

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2AF5B5371836C725A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2AF5B5371836C725A /data

# [All 8 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 8 Nodes] Create clickhouse data directory
sudo mkdir -p /data/clickhouse

# [All 8 Nodes] Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# [All 8 Nodes] Update package lists
sudo apt-get update

# [All 8 Nodes] Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# [All 8 Nodes] Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 8 Nodes] Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 8 Nodes] Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# [All 8 Nodes] Install ClickHouse server and client version &lt;PUBLIC_IP&gt;
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 8 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;13175799808&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# [All 8 Nodes] Configure ClickHouse user profile with password and query settings
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
            &lt;max_threads&gt;2&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;3000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;1000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;1000000000&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
            &lt;distributed_product_mode&gt;global&lt;/distributed_product_mode&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# [All 8 Nodes] Start ClickHouse server service
sudo systemctl start clickhouse-server

# [All 8 Nodes] Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```

**Cluster Configuration:**
```bash
# Create cluster configuration (remote_servers.xml) on all nodes
sudo tee /etc/clickhouse-server/config.d/remote_servers.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;remote_servers&gt;
        &lt;benchmark_cluster&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;shard&gt;
            &lt;replica&gt;
                &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
                &lt;port&gt;9000&lt;/port&gt;
                &lt;user&gt;default&lt;/user&gt;
                &lt;password&gt;&lt;DATABASE_PASSWORD&gt;&lt;/password&gt;
            &lt;/replica&gt;
        &lt;/shard&gt;
        &lt;/benchmark_cluster&gt;
    &lt;/remote_servers&gt;
&lt;/clickhouse&gt;
EOF

# Create node-specific macros (example for node 0)
sudo tee /etc/clickhouse-server/config.d/macros.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;macros&gt;
        &lt;cluster&gt;benchmark_cluster&lt;/cluster&gt;
        &lt;shard&gt;1&lt;/shard&gt;
        &lt;replica&gt;node1&lt;/replica&gt;
    &lt;/macros&gt;
&lt;/clickhouse&gt;
EOF

# Restart ClickHouse on all nodes (parallel for Keeper quorum)
sudo systemctl restart clickhouse-server

```

**Keeper Configuration:**
```bash
# Create ClickHouse Keeper server config (example for node 0)
sudo tee /etc/clickhouse-server/config.d/keeper.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;keeper_server&gt;
        &lt;tcp_port&gt;9181&lt;/tcp_port&gt;
        &lt;server_id&gt;1&lt;/server_id&gt;
        &lt;log_storage_path&gt;/var/lib/clickhouse/coordination/log&lt;/log_storage_path&gt;
        &lt;snapshot_storage_path&gt;/var/lib/clickhouse/coordination/snapshots&lt;/snapshot_storage_path&gt;
        &lt;coordination_settings&gt;
            &lt;operation_timeout_ms&gt;10000&lt;/operation_timeout_ms&gt;
            &lt;session_timeout_ms&gt;30000&lt;/session_timeout_ms&gt;
            &lt;raft_logs_level&gt;warning&lt;/raft_logs_level&gt;
        &lt;/coordination_settings&gt;
        &lt;raft_configuration&gt;
            &lt;server&gt;
                &lt;id&gt;1&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;2&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;3&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;4&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;5&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;6&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;7&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;8&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
        &lt;/raft_configuration&gt;
    &lt;/keeper_server&gt;
&lt;/clickhouse&gt;
EOF

# Create ZooKeeper client config pointing to Keeper cluster
sudo tee /etc/clickhouse-server/config.d/use_keeper.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;zookeeper&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
        &lt;node&gt;
            &lt;host&gt;&lt;PRIVATE_IP&gt;&lt;/host&gt;
            &lt;port&gt;9181&lt;/port&gt;
        &lt;/node&gt;
    &lt;/zookeeper&gt;
    &lt;distributed_ddl&gt;
        &lt;path&gt;/clickhouse/task_queue/ddl&lt;/path&gt;
    &lt;/distributed_ddl&gt;
&lt;/clickhouse&gt;
EOF

```


**Tuning Parameters:**
- Memory limit: `12g`
- Max threads: `2`
- Max memory usage: `3.0GB`

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
unzip extscal_nodes_8-benchmark.zip
cd extscal_nodes_8

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

The following table shows the time taken for data generation, schema creation, and data loading for each system:

| System | Data Generation | Schema Creation | Data Loading | Total Preparation | Raw Size | Stored Size | Compression |
|--------|----------------|-----------------|--------------|-------------------|----------|-------------|-------------|
| Clickhouse | 1544.04s | 1.81s | 629.88s | 2201.45s | N/A | N/A | N/A |
| Starrocks | 1540.89s | 0.26s | 460.64s | 2047.13s | 5.5 GB | 5.5 GB | 1.0x |
| Trino | 444.82s | 1.68s | 0.00s | 509.32s | N/A | N/A | N/A |
| Exasol | 988.61s | 2.36s | 600.77s | 1664.85s | 47.9 GB | 10.8 GB | 4.4x |

**Key Observations:**
- Trino had the fastest preparation time at 509.32s
- Clickhouse took 2201.45s (4.3x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2704   |      5 |     10515.6 |    8023   |   4283.9 |   2645.4 |  11820.1 |
| Q01     | exasol     |   1025.8 |      5 |      3897.2 |    3745.9 |    581.6 |   2871.9 |   4297.5 |
| Q01     | starrocks  |   3971.9 |      5 |      5386   |    5627.8 |   2554.7 |   2707.7 |   9225.7 |
| Q01     | trino      |  21742.1 |      5 |     35582.4 |   41801   |  15657   |  25139.8 |  62554.4 |
| Q02     | clickhouse |  72583.4 |      5 |    246923   |  244003   |   8266.3 | 232326   | 251930   |
| Q02     | exasol     |    164.7 |      5 |      1274.9 |    2886.5 |   2761.6 |    693.5 |   6642.1 |
| Q02     | starrocks  |    618   |      5 |      1089.4 |    1650   |   1168.6 |   1027.2 |   3728.9 |
| Q02     | trino      |  14871.3 |      5 |     89605.6 |   79073.5 |  23112.9 |  50594.9 | 102521   |
| Q03     | clickhouse |  14526   |      5 |     53620.5 |   46736.3 |  19261.5 |  12813.2 |  59576.4 |
| Q03     | exasol     |    878.6 |      5 |      1482.9 |    3597.2 |   3320.3 |    845.4 |   8034.7 |
| Q03     | starrocks  |    709.2 |      5 |       618.8 |    1291.9 |   1109.1 |    416.8 |   2605.8 |
| Q03     | trino      |  30922.9 |      5 |     71917   |   73172.7 |  26013.4 |  42339.5 | 108649   |
| Q04     | clickhouse |  11649.8 |      5 |     48703.2 |   43199.3 |  15440.9 |  21249.8 |  58206.1 |
| Q04     | exasol     |    246.4 |      5 |      1763.6 |    1633.3 |    805.5 |    625.6 |   2483.8 |
| Q04     | starrocks  |    590.2 |      5 |      2232.8 |    2527.5 |   1068.8 |   1280.4 |   4195.7 |
| Q04     | trino      |  15615.7 |      5 |     41573.3 |   46974.2 |  16958   |  25191.9 |  66653.7 |
| Q05     | clickhouse |  13681.7 |      5 |     50120.8 |   49076.7 |   4917.1 |  40636.7 |  53196.9 |
| Q05     | exasol     |    996.5 |      5 |      4754.3 |    5958.9 |   3761   |   2752.5 |  12079.8 |
| Q05     | starrocks  |   1030.4 |      5 |      2709.6 |    3437.3 |   2142.7 |   1962.3 |   7197.3 |
| Q05     | trino      |  16819   |      5 |     53993.4 |   50956.8 |  13069.6 |  33121.3 |  68506.6 |
| Q06     | clickhouse |    190.9 |      5 |       860.6 |     702.4 |    330.5 |    313.3 |    996.5 |
| Q06     | exasol     |     62.1 |      5 |       358.4 |     429.9 |    183.7 |    248.8 |    715.2 |
| Q06     | starrocks  |    129.5 |      5 |       261.8 |     292.8 |    177.4 |     74   |    562   |
| Q06     | trino      |  17658.5 |      5 |     58622.3 |   53379.5 |  15531.4 |  36815.6 |  73146.7 |
| Q07     | clickhouse |   3346.6 |      5 |     13983.5 |   13998.7 |    589.6 |  13406   |  14612.6 |
| Q07     | exasol     |   1556.5 |      5 |      6050.7 |    5863.8 |   1790.6 |   3207.8 |   7690.8 |
| Q07     | starrocks  |    816.1 |      5 |      2755.8 |    2828.6 |   1289.3 |    911.6 |   4336.1 |
| Q07     | trino      |  21435.9 |      5 |     65940.6 |   67091   |  17600.2 |  49838.7 |  91090.3 |
| Q08     | clickhouse |   3844.9 |      5 |     14043.9 |   12156.6 |   4663.5 |   3834.6 |  14709.3 |
| Q08     | exasol     |    496.5 |      5 |      1761.7 |    2085.7 |   1341.2 |   1135.4 |   4407   |
| Q08     | starrocks  |    903.8 |      5 |      3855.7 |    4212.6 |   1080.8 |   3335   |   6059.1 |
| Q08     | trino      |  21388.4 |      5 |     75473   |   65496   |  26660.6 |  20399.4 |  90016.9 |
| Q09     | clickhouse |   3288.6 |      5 |     15209.7 |   12881.9 |   5318.4 |   3375   |  15502.2 |
| Q09     | exasol     |   4986.8 |      5 |     20341.2 |   22219   |   5000.2 |  17997.6 |  30751.9 |
| Q09     | starrocks  |   3044.8 |      5 |      9449.4 |    9446.3 |   1167.4 |   7572.2 |  10478.2 |
| Q09     | trino      |  25306.9 |      5 |     51282.8 |   58776.7 |  15458.5 |  44492.7 |  77597.2 |
| Q10     | clickhouse |  13751.6 |      5 |     52425   |   55077   |   4131.9 |  51444.1 |  59775.2 |
| Q10     | exasol     |    741.2 |      5 |      2765.4 |    2834.8 |   1195.7 |   1101.4 |   4181.3 |
| Q10     | starrocks  |   1052.8 |      5 |      3180.1 |    3662.8 |   2274.3 |   1855.5 |   7456.8 |
| Q10     | trino      |  34386   |      5 |    113199   |  148374   |  74407.6 |  79690.3 | 262920   |
| Q11     | clickhouse |   1379.2 |      5 |      5666.9 |    5057.2 |   1885.8 |   1739.4 |   6330.3 |
| Q11     | exasol     |   1406.7 |      5 |       898.7 |     864   |    269   |    444   |   1191.9 |
| Q11     | starrocks  |    235.1 |      5 |       813.8 |    1550.9 |   1226.6 |    522.4 |   3294.4 |
| Q11     | trino      |   6886.6 |      5 |     25286.4 |   24934.7 |  11722.6 |   7688.3 |  38935.2 |
| Q12     | clickhouse |   3330.8 |      5 |     13385.5 |   13658.3 |    830.9 |  12844.9 |  14579   |
| Q12     | exasol     |    242.1 |      5 |      1305   |    2149.9 |   2144.5 |    873.8 |   5968.3 |
| Q12     | starrocks  |    356.7 |      5 |      1061   |    1270.6 |    492.7 |    928.9 |   2136.1 |
| Q12     | trino      |  23369.8 |      5 |     80818.2 |   80473   |  20372.6 |  60822.7 | 111710   |
| Q13     | clickhouse |   2947.3 |      5 |     15062.5 |   15133.1 |   2755.1 |  11803.3 |  19232.5 |
| Q13     | exasol     |   1218.7 |      5 |      4588.1 |    5277   |   2997.9 |   2015.1 |  10202.8 |
| Q13     | starrocks  |   1983.7 |      5 |      4127.6 |    3873.4 |   1230.9 |   1997.8 |   5361   |
| Q13     | trino      |  10812.8 |      5 |     23315   |   23017.5 |   2753.4 |  18466.9 |  25272.9 |
| Q14     | clickhouse |   3561.2 |      5 |     14593.7 |   12814.8 |   5442.3 |   3548.9 |  17578.4 |
| Q14     | exasol     |    312.9 |      5 |      1565.6 |    1492   |    392.7 |   1104.1 |   2057   |
| Q14     | starrocks  |    129.8 |      5 |       904.7 |     834.6 |    309.5 |    341.7 |   1190   |
| Q14     | trino      |  14070.4 |      5 |     41008.6 |   45366.3 |  15499   |  26872.8 |  66410.8 |
| Q15     | clickhouse |    732.2 |      5 |      2906.4 |    2365.2 |   1523.2 |    721.8 |   3959.5 |
| Q15     | exasol     |    316.2 |      5 |      1526   |    1549.4 |    462.9 |   1114.1 |   2303.9 |
| Q15     | starrocks  |    245.4 |      5 |      1125.7 |    1577.2 |    841.7 |    779.9 |   2772.3 |
| Q15     | trino      |  25279.9 |      5 |     53942.4 |   57066.9 |  11894.4 |  42217.4 |  73619.8 |
| Q16     | clickhouse |   7178.5 |      5 |     27097.9 |   22907.4 |  11254.1 |   9570.3 |  35692.7 |
| Q16     | exasol     |    517.8 |      5 |      2330.5 |    2579.2 |    636.6 |   1948.7 |   3600.6 |
| Q16     | starrocks  |    599.7 |      5 |      1360   |    1566.1 |    502.9 |   1106.7 |   2406.2 |
| Q16     | trino      |   5152.8 |      5 |     22169.5 |   23710.3 |  12922.9 |   8734.2 |  40250.7 |
| Q17     | clickhouse |   7224.9 |      5 |     11829.6 |   11645.8 |   2854.6 |   6999.1 |  14515.6 |
| Q17     | exasol     |     99   |      5 |       465.3 |     750.6 |    594.6 |    329.3 |   1773.1 |
| Q17     | starrocks  |    531.3 |      5 |      1448.6 |    1486.7 |    706.6 |    532.6 |   2312.2 |
| Q17     | trino      |  27785.3 |      5 |     70554.6 |   63110.2 |  22269.5 |  26956.6 |  85962.5 |
| Q18     | clickhouse |   5438.9 |      5 |     21486   |   18367.3 |   7759.2 |   8866.8 |  27728.5 |
| Q18     | exasol     |    510.8 |      5 |      1664.5 |    2863.7 |   1895.5 |   1350.1 |   5557.3 |
| Q18     | starrocks  |   3150.4 |      5 |     11074.9 |   11778.5 |   1288.7 |  10725.2 |  13354.6 |
| Q18     | trino      |  23381.3 |      5 |     81886.4 |   86378.9 |  14068   |  73902   | 105151   |
| Q19     | clickhouse |  29235.9 |      5 |    123688   |  124614   |  14441.7 | 102026   | 139011   |
| Q19     | exasol     |    119.8 |      5 |       342   |     554.2 |    409.2 |    172.5 |   1035   |
| Q19     | starrocks  |    612.7 |      5 |      1255   |    1456.6 |    345.3 |   1141.7 |   1879.1 |
| Q19     | trino      |  16269.3 |      5 |     46371.6 |   48151.9 |  16456.2 |  32569.2 |  70362.7 |
| Q20     | clickhouse |   6840.1 |      5 |     21370.3 |   19917.8 |   6169.2 |   9542.3 |  26146.9 |
| Q20     | exasol     |    392   |      5 |      1198.5 |    1274.9 |    713.5 |    555.9 |   2358.1 |
| Q20     | starrocks  |    412.5 |      5 |      1215.8 |    1267.6 |    255.9 |    920.5 |   1555   |
| Q20     | trino      |  20389.7 |      5 |     63332.4 |   64423.2 |   4535.3 |  58773.5 |  70635.7 |
| Q21     | clickhouse |   3942.4 |      5 |     17274.4 |   17973.9 |   3248.5 |  15052.2 |  23462.9 |
| Q21     | exasol     |  11876   |      5 |      4136.3 |    3944.4 |   1499.2 |   2139.9 |   5772.5 |
| Q21     | starrocks  |   6413   |      5 |     16366.2 |   15384.6 |   5430.5 |   6265.8 |  19807.2 |
| Q21     | trino      |  36705.3 |      5 |     81497   |   82448.6 |  17291.9 |  55272.6 |  98098.1 |
| Q22     | clickhouse |   3146.9 |      5 |     15085.8 |   12100.3 |   8330.4 |   3061   |  19798.5 |
| Q22     | exasol     |    134.2 |      5 |       553.8 |     605.2 |    297   |    344.2 |   1112.2 |
| Q22     | starrocks  |    447   |      5 |      1934   |    1724.2 |    959.2 |    447.7 |   2969.6 |
| Q22     | trino      |   5088.9 |      5 |      9755.3 |   11972.7 |   6092.4 |   4526.3 |  19683.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        3897.2 |          5386   |    1.38 |      0.72 | False    |
| Q02     | exasol            | starrocks           |        1274.9 |          1089.4 |    0.85 |      1.17 | True     |
| Q03     | exasol            | starrocks           |        1482.9 |           618.8 |    0.42 |      2.4  | True     |
| Q04     | exasol            | starrocks           |        1763.6 |          2232.8 |    1.27 |      0.79 | False    |
| Q05     | exasol            | starrocks           |        4754.3 |          2709.6 |    0.57 |      1.75 | True     |
| Q06     | exasol            | starrocks           |         358.4 |           261.8 |    0.73 |      1.37 | True     |
| Q07     | exasol            | starrocks           |        6050.7 |          2755.8 |    0.46 |      2.2  | True     |
| Q08     | exasol            | starrocks           |        1761.7 |          3855.7 |    2.19 |      0.46 | False    |
| Q09     | exasol            | starrocks           |       20341.2 |          9449.4 |    0.46 |      2.15 | True     |
| Q10     | exasol            | starrocks           |        2765.4 |          3180.1 |    1.15 |      0.87 | False    |
| Q11     | exasol            | starrocks           |         898.7 |           813.8 |    0.91 |      1.1  | True     |
| Q12     | exasol            | starrocks           |        1305   |          1061   |    0.81 |      1.23 | True     |
| Q13     | exasol            | starrocks           |        4588.1 |          4127.6 |    0.9  |      1.11 | True     |
| Q14     | exasol            | starrocks           |        1565.6 |           904.7 |    0.58 |      1.73 | True     |
| Q15     | exasol            | starrocks           |        1526   |          1125.7 |    0.74 |      1.36 | True     |
| Q16     | exasol            | starrocks           |        2330.5 |          1360   |    0.58 |      1.71 | True     |
| Q17     | exasol            | starrocks           |         465.3 |          1448.6 |    3.11 |      0.32 | False    |
| Q18     | exasol            | starrocks           |        1664.5 |         11074.9 |    6.65 |      0.15 | False    |
| Q19     | exasol            | starrocks           |         342   |          1255   |    3.67 |      0.27 | False    |
| Q20     | exasol            | starrocks           |        1198.5 |          1215.8 |    1.01 |      0.99 | False    |
| Q21     | exasol            | starrocks           |        4136.3 |         16366.2 |    3.96 |      0.25 | False    |
| Q22     | exasol            | starrocks           |         553.8 |          1934   |    3.49 |      0.29 | False    |
| Q01     | exasol            | clickhouse          |        3897.2 |         10515.6 |    2.7  |      0.37 | False    |
| Q02     | exasol            | clickhouse          |        1274.9 |        246923   |  193.68 |      0.01 | False    |
| Q03     | exasol            | clickhouse          |        1482.9 |         53620.5 |   36.16 |      0.03 | False    |
| Q04     | exasol            | clickhouse          |        1763.6 |         48703.2 |   27.62 |      0.04 | False    |
| Q05     | exasol            | clickhouse          |        4754.3 |         50120.8 |   10.54 |      0.09 | False    |
| Q06     | exasol            | clickhouse          |         358.4 |           860.6 |    2.4  |      0.42 | False    |
| Q07     | exasol            | clickhouse          |        6050.7 |         13983.5 |    2.31 |      0.43 | False    |
| Q08     | exasol            | clickhouse          |        1761.7 |         14043.9 |    7.97 |      0.13 | False    |
| Q09     | exasol            | clickhouse          |       20341.2 |         15209.7 |    0.75 |      1.34 | True     |
| Q10     | exasol            | clickhouse          |        2765.4 |         52425   |   18.96 |      0.05 | False    |
| Q11     | exasol            | clickhouse          |         898.7 |          5666.9 |    6.31 |      0.16 | False    |
| Q12     | exasol            | clickhouse          |        1305   |         13385.5 |   10.26 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        4588.1 |         15062.5 |    3.28 |      0.3  | False    |
| Q14     | exasol            | clickhouse          |        1565.6 |         14593.7 |    9.32 |      0.11 | False    |
| Q15     | exasol            | clickhouse          |        1526   |          2906.4 |    1.9  |      0.53 | False    |
| Q16     | exasol            | clickhouse          |        2330.5 |         27097.9 |   11.63 |      0.09 | False    |
| Q17     | exasol            | clickhouse          |         465.3 |         11829.6 |   25.42 |      0.04 | False    |
| Q18     | exasol            | clickhouse          |        1664.5 |         21486   |   12.91 |      0.08 | False    |
| Q19     | exasol            | clickhouse          |         342   |        123688   |  361.66 |      0    | False    |
| Q20     | exasol            | clickhouse          |        1198.5 |         21370.3 |   17.83 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |        4136.3 |         17274.4 |    4.18 |      0.24 | False    |
| Q22     | exasol            | clickhouse          |         553.8 |         15085.8 |   27.24 |      0.04 | False    |
| Q01     | exasol            | trino               |        3897.2 |         35582.4 |    9.13 |      0.11 | False    |
| Q02     | exasol            | trino               |        1274.9 |         89605.6 |   70.28 |      0.01 | False    |
| Q03     | exasol            | trino               |        1482.9 |         71917   |   48.5  |      0.02 | False    |
| Q04     | exasol            | trino               |        1763.6 |         41573.3 |   23.57 |      0.04 | False    |
| Q05     | exasol            | trino               |        4754.3 |         53993.4 |   11.36 |      0.09 | False    |
| Q06     | exasol            | trino               |         358.4 |         58622.3 |  163.57 |      0.01 | False    |
| Q07     | exasol            | trino               |        6050.7 |         65940.6 |   10.9  |      0.09 | False    |
| Q08     | exasol            | trino               |        1761.7 |         75473   |   42.84 |      0.02 | False    |
| Q09     | exasol            | trino               |       20341.2 |         51282.8 |    2.52 |      0.4  | False    |
| Q10     | exasol            | trino               |        2765.4 |        113199   |   40.93 |      0.02 | False    |
| Q11     | exasol            | trino               |         898.7 |         25286.4 |   28.14 |      0.04 | False    |
| Q12     | exasol            | trino               |        1305   |         80818.2 |   61.93 |      0.02 | False    |
| Q13     | exasol            | trino               |        4588.1 |         23315   |    5.08 |      0.2  | False    |
| Q14     | exasol            | trino               |        1565.6 |         41008.6 |   26.19 |      0.04 | False    |
| Q15     | exasol            | trino               |        1526   |         53942.4 |   35.35 |      0.03 | False    |
| Q16     | exasol            | trino               |        2330.5 |         22169.5 |    9.51 |      0.11 | False    |
| Q17     | exasol            | trino               |         465.3 |         70554.6 |  151.63 |      0.01 | False    |
| Q18     | exasol            | trino               |        1664.5 |         81886.4 |   49.2  |      0.02 | False    |
| Q19     | exasol            | trino               |         342   |         46371.6 |  135.59 |      0.01 | False    |
| Q20     | exasol            | trino               |        1198.5 |         63332.4 |   52.84 |      0.02 | False    |
| Q21     | exasol            | trino               |        4136.3 |         81497   |   19.7  |      0.05 | False    |
| Q22     | exasol            | trino               |         553.8 |          9755.3 |   17.62 |      0.06 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 30037.6 | 17040.0 | 860.6 | 135270.7 |
| 1 | 28 | 36909.3 | 12376.5 | 313.3 | 246923.1 |
| 2 | 27 | 35089.8 | 21112.0 | 996.5 | 139010.6 |
| 3 | 27 | 36670.9 | 13420.3 | 377.4 | 251929.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 12376.5ms
- Slowest stream median: 21112.0ms
- Stream performance variation: 70.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3692.8 | 2982.4 | 344.2 | 12079.8 |
| 1 | 28 | 3254.1 | 1644.8 | 248.8 | 30751.9 |
| 2 | 27 | 3808.7 | 1565.6 | 172.5 | 22204.0 |
| 3 | 27 | 2905.6 | 1571.8 | 419.6 | 19800.3 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1565.6ms
- Slowest stream median: 2982.4ms
- Stream performance variation: 90.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3897.1 | 2200.5 | 74.0 | 19807.2 |
| 1 | 28 | 3430.5 | 2665.6 | 261.8 | 10742.2 |
| 2 | 27 | 3537.4 | 1615.0 | 236.0 | 15320.0 |
| 3 | 27 | 3446.6 | 2136.1 | 522.4 | 16366.2 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1615.0ms
- Slowest stream median: 2665.6ms
- Stream performance variation: 65.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 55411.3 | 54047.3 | 14539.9 | 113199.0 |
| 1 | 28 | 62026.4 | 61658.8 | 4526.3 | 262920.0 |
| 2 | 27 | 62502.6 | 58615.3 | 22169.5 | 181846.0 |
| 3 | 27 | 55737.9 | 58295.9 | 8734.2 | 96917.7 |

**Performance Analysis for Trino:**
- Fastest stream median: 54047.3ms
- Slowest stream median: 61658.8ms
- Stream performance variation: 14.1% difference between fastest and slowest streams
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

**starrocks:**
- Median runtime: 2119.6ms
- Average runtime: 3579.5ms
- Fastest query: 74.0ms
- Slowest query: 19807.2ms

**exasol:**
- Median runtime: 1762.7ms
- Average runtime: 3416.3ms
- Fastest query: 172.5ms
- Slowest query: 30751.9ms

**clickhouse:**
- Median runtime: 15003.8ms
- Average runtime: 34655.0ms
- Fastest query: 313.3ms
- Slowest query: 251929.7ms

**trino:**
- Median runtime: 58455.6ms
- Average runtime: 58915.9ms
- Fastest query: 4526.3ms
- Slowest query: 262920.0ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_8-benchmark.zip`](extscal_nodes_8-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- See `attachments/system.json` for detailed system specifications

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
  - memory_limit: 12g
  - max_threads: 2
  - max_memory_usage: 3000000000
  - max_bytes_before_external_group_by: 1000000000
  - max_bytes_before_external_sort: 1000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 2000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 72GB
  - query_max_memory_per_node: 9GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 32
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