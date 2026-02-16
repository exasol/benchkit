# Streamlined Scalability - Node Scaling (4 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-02-10 14:30:49

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **starrocks**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 1198.8ms median runtime
- trino was 47.3x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 4-node cluster

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 4-node cluster

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 4-node cluster

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 4-node cluster


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


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 4 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 4 Nodes] Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 4 Nodes] Create raw partition for Exasol (150GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 4 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 4 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 4 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 4 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 4 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# [All 4 Nodes] Add exasol user to sudo group
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
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
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
# [All 4 Nodes] Configuring passwordless sudo on all nodes
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
# [All 4 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS16DC7EB3F276F405B with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS16DC7EB3F276F405B

# [All 4 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 4 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS16DC7EB3F276F405B to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS16DC7EB3F276F405B /data

# [All 4 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 4 Nodes] Create trino data directory
sudo mkdir -p /data/trino

```

**Prerequisites:**
```bash
# [All 4 Nodes] Add Eclipse Temurin (Adoptium) repository for Java 22
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg 2&gt;/dev/null || true
echo &#34;deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(lsb_release -sc) main&#34; | sudo tee /etc/apt/sources.list.d/adoptium.list

# [All 4 Nodes] Install Java 25 (required by Trino 479+)
sudo apt-get update &amp;&amp; sudo apt-get install -y temurin-25-jdk

# [All 4 Nodes] Install python symlink (required by Trino launcher)
sudo apt-get install -y python-is-python3

```

**User Setup:**
```bash
# [All 4 Nodes] Create Trino system user
sudo useradd -r -s /bin/false trino || true

```

**Installation:**
```bash
# [All 4 Nodes] Download Trino server version 479
wget -q --tries=3 --retry-connrefused --waitretry=5 https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

# [All 4 Nodes] Extract Trino server to /opt
sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/

# [All 4 Nodes] Create symlink /opt/trino-server
sudo ln -sf /opt/trino-server-479 /opt/trino-server

# [All 4 Nodes] Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

# [All 4 Nodes] Create etc symlink for Trino launcher
sudo ln -sf /etc/trino /opt/trino-server/etc

```

**Configuration:**
```bash
# [All 4 Nodes] Configure Trino node properties
sudo tee /etc/trino/node.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
node.environment=production
node.id=2757fa5c-375b-4e01-bd71-88c8b1492578
node.data-dir=/var/trino/data
EOF

# [All 4 Nodes] Configure JVM with 24G heap (80% of 30.8G total RAM)
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

# [All 4 Nodes] Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
discovery.uri=http://&lt;PRIVATE_IP&gt;:8080
query.max-memory=72GB
query.max-memory-per-node=16GB
EOF

# [All 4 Nodes] Configure Hive catalog with file metastore at local:///data/trino/hive-metastore
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

# [All 4 Nodes] Create Trino systemd service
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
# [All 4 Nodes] Reload systemd daemon
sudo systemctl daemon-reload

```

**Setup:**
```bash
# [All 4 Nodes] Execute sudo command on remote system
sudo mkdir -p /data/trino/hive-metastore

# [All 4 Nodes] Execute sudo command on remote system
sudo chown -R trino:trino /data/trino/hive-metastore

# [All 4 Nodes] Execute sudo command on remote system
sudo chmod -R 755 /data/trino/hive-metastore

# [All 4 Nodes] Execute sudo command on remote system
sudo mkdir -p /etc/trino/catalog

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# [All 4 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS238BDFC2C5C3A4CEA with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS238BDFC2C5C3A4CEA

# [All 4 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 4 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS238BDFC2C5C3A4CEA to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS238BDFC2C5C3A4CEA /data

# [All 4 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 4 Nodes] Create starrocks data directory
sudo mkdir -p /data/starrocks

# [All 4 Nodes] Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# [All 4 Nodes] Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 4 Nodes] Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# [All 4 Nodes] Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 4 Nodes] Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# [All 4 Nodes] Configure StarRocks FE
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

# [All 4 Nodes] Configure StarRocks BE
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
# [All 4 Nodes] Start StarRocks FE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 4 Nodes] Start StarRocks BE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 4 Nodes] Execute test command on remote system
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
# [All 4 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43D907644C6D8237D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43D907644C6D8237D

# [All 4 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 4 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43D907644C6D8237D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43D907644C6D8237D /data

# [All 4 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 4 Nodes] Create clickhouse data directory
sudo mkdir -p /data/clickhouse

# [All 4 Nodes] Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# [All 4 Nodes] Update package lists
sudo apt-get update

# [All 4 Nodes] Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# [All 4 Nodes] Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 4 Nodes] Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 4 Nodes] Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# [All 4 Nodes] Install ClickHouse server and client version &lt;PUBLIC_IP&gt;
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 4 Nodes] Create custom ClickHouse configuration file
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
# [All 4 Nodes] Configure ClickHouse user profile with password and query settings
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
            &lt;max_memory_usage&gt;6000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;2000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;2000000000&lt;/max_bytes_before_external_group_by&gt;
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
# [All 4 Nodes] Start ClickHouse server service
sudo systemctl start clickhouse-server

# [All 4 Nodes] Enable ClickHouse server to start on boot
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
    &lt;/zookeeper&gt;
    &lt;distributed_ddl&gt;
        &lt;path&gt;/clickhouse/task_queue/ddl&lt;/path&gt;
    &lt;/distributed_ddl&gt;
&lt;/clickhouse&gt;
EOF

```


**Tuning Parameters:**
- Memory limit: `24g`
- Max threads: `4`
- Max memory usage: `6.0GB`

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
unzip extscal_nodes_4-benchmark.zip
cd extscal_nodes_4

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
| Clickhouse | 804.39s | 1.62s | 344.70s | 1199.60s | N/A | N/A | N/A |
| Starrocks | 801.34s | 0.20s | 353.78s | 1204.78s | 15.1 GB | 15.1 GB | 1.0x |
| Trino | 268.64s | 1.20s | 0.00s | 327.28s | N/A | N/A | N/A |
| Exasol | 494.16s | 2.44s | 381.65s | 950.14s | 47.9 GB | 10.6 GB | 4.5x |

**Key Observations:**
- Trino had the fastest preparation time at 327.28s
- Starrocks took 1204.78s (3.7x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2344.6 |      5 |      8159   |    8945   |   3687.9 |   5767.1 |  15271.9 |
| Q01     | exasol     |    913.9 |      5 |      3525.1 |    3111.5 |    868   |   1789.9 |   3872.3 |
| Q01     | starrocks  |   3566.2 |      5 |      4216.3 |    5258.6 |   2303.2 |   3566.9 |   9205.3 |
| Q01     | trino      |  21786.6 |      5 |     46268   |   44291.4 |   9482.3 |  29400.6 |  53727.4 |
| Q02     | clickhouse |  21058.2 |      5 |     78955.5 |   78139.7 |   4905.6 |  70199.4 |  83630.3 |
| Q02     | exasol     |    128.2 |      5 |       329.5 |     312.7 |     49.3 |    227.4 |    352.9 |
| Q02     | starrocks  |    460.9 |      5 |      1388.7 |    1491.8 |    905.9 |    505.9 |   2795.2 |
| Q02     | trino      |  12390.2 |      5 |     41490.1 |   45245.6 |  17387.7 |  29680.1 |  70049.6 |
| Q03     | clickhouse |   5570.9 |      5 |     17714.7 |   18042.5 |   2211.3 |  15377.9 |  21106.3 |
| Q03     | exasol     |    891.2 |      5 |      1474.4 |    1735.8 |    751.3 |   1094.9 |   2997   |
| Q03     | starrocks  |    645.3 |      5 |       531.8 |    1273.6 |   1267   |    379.4 |   3285.5 |
| Q03     | trino      |  31042.6 |      5 |     60252.7 |   59031.7 |  23268.8 |  24905.6 |  86657.4 |
| Q04     | clickhouse |  13821.1 |      5 |     38588.4 |   38088.5 |   2422.1 |  34469.9 |  40327.3 |
| Q04     | exasol     |    264.3 |      5 |       821   |     757   |    338.4 |    211.1 |   1144.5 |
| Q04     | starrocks  |    668.5 |      5 |      2211.6 |    1984.5 |    831.4 |    519   |   2521.9 |
| Q04     | trino      |  14984.2 |      5 |     35033.6 |   35647.9 |  11987.8 |  19722.2 |  52789   |
| Q05     | clickhouse |   5654   |      5 |     19400.2 |   21548.7 |   4902.3 |  17770.4 |  29841.2 |
| Q05     | exasol     |    933   |      5 |      3079.2 |    2697.5 |    741.5 |   1419   |   3216.7 |
| Q05     | starrocks  |   1234.4 |      5 |      3986.6 |    4091   |    501   |   3477.4 |   4783.9 |
| Q05     | trino      |  18203.7 |      5 |    124558   |  149333   |  96618.5 |  60310.8 | 304246   |
| Q06     | clickhouse |    180.9 |      5 |      1021.3 |    1232.9 |    561.4 |    716.9 |   1953.6 |
| Q06     | exasol     |     61.4 |      5 |       249.4 |     218.2 |    138.2 |     51.9 |    378.4 |
| Q06     | starrocks  |    113.3 |      5 |       120.6 |     159.6 |    126.4 |     56.4 |    376.8 |
| Q06     | trino      |  19719   |      5 |     56690   |   55633.2 |  21862.5 |  32099.6 |  83843.7 |
| Q07     | clickhouse |   3221.3 |      5 |     11576.7 |   12779.9 |   3955.4 |   9141.4 |  18525.6 |
| Q07     | exasol     |   1023.3 |      5 |      3947.7 |    3534.3 |   1171.6 |   1916.6 |   4963.2 |
| Q07     | starrocks  |    709.5 |      5 |      1685.4 |    1847.2 |    924.1 |    587.7 |   3081.3 |
| Q07     | trino      |  23180.7 |      5 |     71652.8 |   72545   |  27826.6 |  43633.5 | 107798   |
| Q08     | clickhouse |   3678.4 |      5 |     13108.7 |   13164.6 |   4901.2 |   5925.5 |  19509.9 |
| Q08     | exasol     |    401.7 |      5 |      1222.3 |    1189   |    389   |    606.9 |   1601.4 |
| Q08     | starrocks  |    908   |      5 |      3082.2 |    3431.9 |   1752.7 |   2096.9 |   6431   |
| Q08     | trino      |  23187.9 |      5 |     56874   |   61122.2 |  12536.5 |  48500.8 |  77719.5 |
| Q09     | clickhouse |   3461.3 |      5 |     12501.7 |   13149.1 |   1743.7 |  11661.5 |  16053.9 |
| Q09     | exasol     |   2761.6 |      5 |     11118.6 |   10214.4 |   1594.4 |   7778.6 |  11577.1 |
| Q09     | starrocks  |   2137.3 |      5 |      5971.6 |    6209.1 |   1358   |   4770.2 |   8426.3 |
| Q09     | trino      |  24638.4 |      5 |     61337.7 |   63329.8 |  10285   |  55389.4 |  80949.2 |
| Q10     | clickhouse |   5547.6 |      5 |     20117.5 |   19913.9 |   1839.7 |  17687.8 |  22395   |
| Q10     | exasol     |    636.5 |      5 |      2431.8 |    2010.5 |    646.2 |   1298.1 |   2516.7 |
| Q10     | starrocks  |    980.9 |      5 |      2308   |    2413.1 |    668.7 |   1729.6 |   3221.2 |
| Q10     | trino      |  36272.8 |      5 |    135689   |  161120   |  53556.1 | 119813   | 244143   |
| Q11     | clickhouse |    755.5 |      5 |      3693.9 |    3692.2 |    285.3 |   3330.3 |   3986.7 |
| Q11     | exasol     |   1353.9 |      5 |       676.3 |     696.6 |    347.5 |    209.2 |   1182.2 |
| Q11     | starrocks  |    161.1 |      5 |       622.7 |     545.5 |    219.2 |    255.6 |    744.7 |
| Q11     | trino      |   7782.5 |      5 |     22387.7 |   22605.3 |   8569   |  10832.1 |  30994.4 |
| Q12     | clickhouse |   3181.8 |      5 |     14023.8 |   13325.7 |   2780.7 |   8983   |  16480.2 |
| Q12     | exasol     |    194   |      5 |      1065.8 |    1025.7 |    240.2 |    738.9 |   1271.2 |
| Q12     | starrocks  |    293.2 |      5 |       849.9 |     880.9 |    168.9 |    697.4 |   1146.5 |
| Q12     | trino      |  50215.3 |      5 |     95789.6 |   92087.7 |  17753.5 |  67737   | 110624   |
| Q13     | clickhouse |  12872.9 |      5 |     37716   |   39138.2 |   5668.2 |  32652.6 |  47792.8 |
| Q13     | exasol     |    763.1 |      5 |      2961.9 |    3379.6 |   1737.1 |   1537.9 |   5721   |
| Q13     | starrocks  |   1670.1 |      5 |      4032.4 |    3756.9 |   1337.7 |   1651.4 |   5305.6 |
| Q13     | trino      |  14162.5 |      5 |     26056.1 |   28496.7 |  11067.8 |  16715   |  45260.7 |
| Q14     | clickhouse |   1574.8 |      5 |      4854.9 |    4976.7 |    800.1 |   3850.5 |   5982.3 |
| Q14     | exasol     |    264.1 |      5 |      1020.1 |     952   |    187.1 |    649.4 |   1125.1 |
| Q14     | starrocks  |    119.3 |      5 |       496.9 |     831.3 |    822.7 |    344.3 |   2291.9 |
| Q14     | trino      |  16826   |      5 |     50126.2 |   59011.5 |  25072.2 |  32675.6 |  98233.7 |
| Q15     | clickhouse |    364   |      5 |      2406.9 |    2521.1 |   1358.4 |   1234.2 |   4705.1 |
| Q15     | exasol     |    265.1 |      5 |      1100.9 |    1192.3 |    221.7 |   1023.4 |   1569.8 |
| Q15     | starrocks  |    185.9 |      5 |       527.3 |     588.1 |    220.9 |    336.2 |    894.1 |
| Q15     | trino      |  28263.1 |      5 |     60993.9 |   60264.1 |   6093.6 |  50820.8 |  66581.6 |
| Q16     | clickhouse |   3274.2 |      5 |     11128   |   11788.5 |   1830.4 |   9880.1 |  14246.3 |
| Q16     | exasol     |    466.9 |      5 |      1592.3 |    1594.7 |    229.5 |   1265.3 |   1895.3 |
| Q16     | starrocks  |    568.5 |      5 |      1176.1 |    1329.6 |    371.5 |    963.2 |   1880   |
| Q16     | trino      |   5103.4 |      5 |     22425.4 |   21339.2 |   6844.3 |  10789.2 |  27610.5 |
| Q17     | clickhouse |   2582   |      5 |      9325.1 |    8084.7 |   3005.4 |   3126.6 |  10353.3 |
| Q17     | exasol     |     73.8 |      5 |       192.2 |     236.4 |     73.7 |    183.1 |    355.9 |
| Q17     | starrocks  |    543.1 |      5 |      1431.9 |    1690.5 |   1017.1 |    684.1 |   3296.3 |
| Q17     | trino      |  29494   |      5 |     73352.7 |   70807.2 |  10947.2 |  55971.5 |  82257.4 |
| Q18     | clickhouse |   4338.8 |      5 |     16478.3 |   16321.2 |   3178.1 |  11498.3 |  19935.2 |
| Q18     | exasol     |    518.6 |      5 |      1794   |    1807.5 |    382.8 |   1244.1 |   2190.7 |
| Q18     | starrocks  |   2796.6 |      5 |      9523.6 |    9118.1 |   1799.8 |   6784.2 |  11029.8 |
| Q18     | trino      |  34981.7 |      5 |     80252   |   83123.2 |   9811.8 |  75825.3 |  99754.1 |
| Q19     | clickhouse |  10637.5 |      5 |     42864.8 |   41550.6 |   4537.5 |  35653.8 |  47044.1 |
| Q19     | exasol     |     87.8 |      5 |       201.7 |     243.6 |    172.3 |     86   |    469.3 |
| Q19     | starrocks  |    477.8 |      5 |      1043.9 |    1079.8 |    292.1 |    670.7 |   1441.4 |
| Q19     | trino      |  18869.1 |      5 |     48987.6 |   48838.9 |  15838.5 |  34733.5 |  73355   |
| Q20     | clickhouse |   5152.1 |      5 |     18495.3 |   17928.5 |   3656.3 |  11948.7 |  21728.1 |
| Q20     | exasol     |    326.5 |      5 |       690.3 |     805.7 |    524.8 |    331.7 |   1543.6 |
| Q20     | starrocks  |    277.4 |      5 |      1326.9 |    1763   |   1181   |    609.6 |   3619   |
| Q20     | trino      |  24232.8 |      5 |     61894.3 |   59735.2 |  21384.1 |  35655.3 |  86118.3 |
| Q21     | clickhouse |   2951.8 |      5 |     12229.8 |   12230.6 |   2209.9 |   8960.4 |  15169.5 |
| Q21     | exasol     |  11026.3 |      5 |      2172.1 |    2212.7 |   1322   |    673.3 |   3826.6 |
| Q21     | starrocks  |   5011.8 |      5 |     15042.1 |   12190.7 |   4130.5 |   6420.9 |  15269.4 |
| Q21     | trino      |  40737.4 |      5 |     73565.4 |   79143.5 |  15754.2 |  68021.3 | 106949   |
| Q22     | clickhouse |   1664.8 |      5 |      7204.1 |    7613.9 |   2591.5 |   3951.2 |  10989.4 |
| Q22     | exasol     |    115.4 |      5 |       493.8 |     473.7 |    170.5 |    201.8 |    665.8 |
| Q22     | starrocks  |    422.1 |      5 |      1442.7 |    1274.1 |    559.1 |    372.4 |   1845.9 |
| Q22     | trino      |   4738.6 |      5 |     14422.1 |   14896.2 |   5566.1 |   7746.4 |  22561.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        3525.1 |          4216.3 |    1.2  |      0.84 | False    |
| Q02     | exasol            | starrocks           |         329.5 |          1388.7 |    4.21 |      0.24 | False    |
| Q03     | exasol            | starrocks           |        1474.4 |           531.8 |    0.36 |      2.77 | True     |
| Q04     | exasol            | starrocks           |         821   |          2211.6 |    2.69 |      0.37 | False    |
| Q05     | exasol            | starrocks           |        3079.2 |          3986.6 |    1.29 |      0.77 | False    |
| Q06     | exasol            | starrocks           |         249.4 |           120.6 |    0.48 |      2.07 | True     |
| Q07     | exasol            | starrocks           |        3947.7 |          1685.4 |    0.43 |      2.34 | True     |
| Q08     | exasol            | starrocks           |        1222.3 |          3082.2 |    2.52 |      0.4  | False    |
| Q09     | exasol            | starrocks           |       11118.6 |          5971.6 |    0.54 |      1.86 | True     |
| Q10     | exasol            | starrocks           |        2431.8 |          2308   |    0.95 |      1.05 | True     |
| Q11     | exasol            | starrocks           |         676.3 |           622.7 |    0.92 |      1.09 | True     |
| Q12     | exasol            | starrocks           |        1065.8 |           849.9 |    0.8  |      1.25 | True     |
| Q13     | exasol            | starrocks           |        2961.9 |          4032.4 |    1.36 |      0.73 | False    |
| Q14     | exasol            | starrocks           |        1020.1 |           496.9 |    0.49 |      2.05 | True     |
| Q15     | exasol            | starrocks           |        1100.9 |           527.3 |    0.48 |      2.09 | True     |
| Q16     | exasol            | starrocks           |        1592.3 |          1176.1 |    0.74 |      1.35 | True     |
| Q17     | exasol            | starrocks           |         192.2 |          1431.9 |    7.45 |      0.13 | False    |
| Q18     | exasol            | starrocks           |        1794   |          9523.6 |    5.31 |      0.19 | False    |
| Q19     | exasol            | starrocks           |         201.7 |          1043.9 |    5.18 |      0.19 | False    |
| Q20     | exasol            | starrocks           |         690.3 |          1326.9 |    1.92 |      0.52 | False    |
| Q21     | exasol            | starrocks           |        2172.1 |         15042.1 |    6.93 |      0.14 | False    |
| Q22     | exasol            | starrocks           |         493.8 |          1442.7 |    2.92 |      0.34 | False    |
| Q01     | exasol            | clickhouse          |        3525.1 |          8159   |    2.31 |      0.43 | False    |
| Q02     | exasol            | clickhouse          |         329.5 |         78955.5 |  239.62 |      0    | False    |
| Q03     | exasol            | clickhouse          |        1474.4 |         17714.7 |   12.01 |      0.08 | False    |
| Q04     | exasol            | clickhouse          |         821   |         38588.4 |   47    |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        3079.2 |         19400.2 |    6.3  |      0.16 | False    |
| Q06     | exasol            | clickhouse          |         249.4 |          1021.3 |    4.1  |      0.24 | False    |
| Q07     | exasol            | clickhouse          |        3947.7 |         11576.7 |    2.93 |      0.34 | False    |
| Q08     | exasol            | clickhouse          |        1222.3 |         13108.7 |   10.72 |      0.09 | False    |
| Q09     | exasol            | clickhouse          |       11118.6 |         12501.7 |    1.12 |      0.89 | False    |
| Q10     | exasol            | clickhouse          |        2431.8 |         20117.5 |    8.27 |      0.12 | False    |
| Q11     | exasol            | clickhouse          |         676.3 |          3693.9 |    5.46 |      0.18 | False    |
| Q12     | exasol            | clickhouse          |        1065.8 |         14023.8 |   13.16 |      0.08 | False    |
| Q13     | exasol            | clickhouse          |        2961.9 |         37716   |   12.73 |      0.08 | False    |
| Q14     | exasol            | clickhouse          |        1020.1 |          4854.9 |    4.76 |      0.21 | False    |
| Q15     | exasol            | clickhouse          |        1100.9 |          2406.9 |    2.19 |      0.46 | False    |
| Q16     | exasol            | clickhouse          |        1592.3 |         11128   |    6.99 |      0.14 | False    |
| Q17     | exasol            | clickhouse          |         192.2 |          9325.1 |   48.52 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |        1794   |         16478.3 |    9.19 |      0.11 | False    |
| Q19     | exasol            | clickhouse          |         201.7 |         42864.8 |  212.52 |      0    | False    |
| Q20     | exasol            | clickhouse          |         690.3 |         18495.3 |   26.79 |      0.04 | False    |
| Q21     | exasol            | clickhouse          |        2172.1 |         12229.8 |    5.63 |      0.18 | False    |
| Q22     | exasol            | clickhouse          |         493.8 |          7204.1 |   14.59 |      0.07 | False    |
| Q01     | exasol            | trino               |        3525.1 |         46268   |   13.13 |      0.08 | False    |
| Q02     | exasol            | trino               |         329.5 |         41490.1 |  125.92 |      0.01 | False    |
| Q03     | exasol            | trino               |        1474.4 |         60252.7 |   40.87 |      0.02 | False    |
| Q04     | exasol            | trino               |         821   |         35033.6 |   42.67 |      0.02 | False    |
| Q05     | exasol            | trino               |        3079.2 |        124558   |   40.45 |      0.02 | False    |
| Q06     | exasol            | trino               |         249.4 |         56690   |  227.31 |      0    | False    |
| Q07     | exasol            | trino               |        3947.7 |         71652.8 |   18.15 |      0.06 | False    |
| Q08     | exasol            | trino               |        1222.3 |         56874   |   46.53 |      0.02 | False    |
| Q09     | exasol            | trino               |       11118.6 |         61337.7 |    5.52 |      0.18 | False    |
| Q10     | exasol            | trino               |        2431.8 |        135689   |   55.8  |      0.02 | False    |
| Q11     | exasol            | trino               |         676.3 |         22387.7 |   33.1  |      0.03 | False    |
| Q12     | exasol            | trino               |        1065.8 |         95789.6 |   89.88 |      0.01 | False    |
| Q13     | exasol            | trino               |        2961.9 |         26056.1 |    8.8  |      0.11 | False    |
| Q14     | exasol            | trino               |        1020.1 |         50126.2 |   49.14 |      0.02 | False    |
| Q15     | exasol            | trino               |        1100.9 |         60993.9 |   55.4  |      0.02 | False    |
| Q16     | exasol            | trino               |        1592.3 |         22425.4 |   14.08 |      0.07 | False    |
| Q17     | exasol            | trino               |         192.2 |         73352.7 |  381.65 |      0    | False    |
| Q18     | exasol            | trino               |        1794   |         80252   |   44.73 |      0.02 | False    |
| Q19     | exasol            | trino               |         201.7 |         48987.6 |  242.87 |      0    | False    |
| Q20     | exasol            | trino               |         690.3 |         61894.3 |   89.66 |      0.01 | False    |
| Q21     | exasol            | trino               |        2172.1 |         73565.4 |   33.87 |      0.03 | False    |
| Q22     | exasol            | trino               |         493.8 |         14422.1 |   29.21 |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 18183.1 | 16546.3 | 716.9 | 47792.8 |
| 1 | 28 | 18339.6 | 9747.3 | 772.5 | 78955.5 |
| 2 | 27 | 18410.1 | 14857.1 | 1021.3 | 47044.1 |
| 3 | 27 | 18562.1 | 12124.9 | 1234.2 | 83630.3 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 9747.3ms
- Slowest stream median: 16546.3ms
- Stream performance variation: 69.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1993.5 | 1797.6 | 101.1 | 4963.2 |
| 1 | 28 | 1519.1 | 935.5 | 183.1 | 11118.6 |
| 2 | 27 | 2157.4 | 1020.1 | 51.9 | 11577.1 |
| 3 | 27 | 1681.6 | 1123.8 | 192.2 | 11178.4 |

**Performance Analysis for Exasol:**
- Fastest stream median: 935.5ms
- Slowest stream median: 1797.6ms
- Stream performance variation: 92.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3204.7 | 1690.5 | 56.4 | 15269.4 |
| 1 | 28 | 2428.6 | 1849.3 | 152.0 | 11029.8 |
| 2 | 27 | 3148.6 | 1830.0 | 92.4 | 9205.3 |
| 3 | 27 | 2714.8 | 1685.4 | 120.6 | 15042.1 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1685.4ms
- Slowest stream median: 1849.3ms
- Stream performance variation: 9.7% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 69712.1 | 51637.1 | 7746.4 | 304245.8 |
| 1 | 28 | 56533.0 | 57752.1 | 12246.5 | 135689.0 |
| 2 | 27 | 71124.9 | 61337.7 | 10789.2 | 244142.7 |
| 3 | 27 | 54926.2 | 55389.4 | 14422.1 | 99754.1 |

**Performance Analysis for Trino:**
- Fastest stream median: 51637.1ms
- Slowest stream median: 61337.7ms
- Stream performance variation: 18.8% difference between fastest and slowest streams
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

**exasol:**
- Median runtime: 1198.8ms
- Average runtime: 1836.4ms
- Fastest query: 51.9ms
- Slowest query: 11577.1ms

**starrocks:**
- Median runtime: 1752.9ms
- Average runtime: 2873.1ms
- Fastest query: 56.4ms
- Slowest query: 15269.4ms

**clickhouse:**
- Median runtime: 13259.4ms
- Average runtime: 18371.7ms
- Fastest query: 716.9ms
- Slowest query: 83630.3ms

**trino:**
- Median runtime: 56668.6ms
- Average runtime: 63074.9ms
- Fastest query: 7746.4ms
- Slowest query: 304245.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_4-benchmark.zip`](extscal_nodes_4-benchmark.zip)

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
  - memory_limit: 24g
  - max_threads: 4
  - max_memory_usage: 6000000000
  - max_bytes_before_external_group_by: 2000000000
  - max_bytes_before_external_sort: 2000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 4000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 72GB
  - query_max_memory_per_node: 18GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 16
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