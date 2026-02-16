# Streamlined Scalability - Node Scaling (2 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-02-10 13:08:38

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **starrocks**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 871.5ms median runtime
- trino was 91.3x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 2-node cluster

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 2-node cluster

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 2-node cluster

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 2-node cluster


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
# [All 2 Nodes] Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 2 Nodes] Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 2 Nodes] Create raw partition for Exasol (371GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 2 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 2 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 2 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# [All 2 Nodes] Add exasol user to sudo group
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
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
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
# [All 2 Nodes] Configuring passwordless sudo on all nodes
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
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24861EE38EB01DF18 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24861EE38EB01DF18

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24861EE38EB01DF18 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24861EE38EB01DF18 /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create trino data directory
sudo mkdir -p /data/trino

```

**Prerequisites:**
```bash
# [All 2 Nodes] Add Eclipse Temurin (Adoptium) repository for Java 22
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg 2&gt;/dev/null || true
echo &#34;deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(lsb_release -sc) main&#34; | sudo tee /etc/apt/sources.list.d/adoptium.list

# [All 2 Nodes] Install Java 25 (required by Trino 479+)
sudo apt-get update &amp;&amp; sudo apt-get install -y temurin-25-jdk

# [All 2 Nodes] Install python symlink (required by Trino launcher)
sudo apt-get install -y python-is-python3

```

**User Setup:**
```bash
# [All 2 Nodes] Create Trino system user
sudo useradd -r -s /bin/false trino || true

```

**Installation:**
```bash
# [All 2 Nodes] Download Trino server version 479
wget -q --tries=3 --retry-connrefused --waitretry=5 https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

# [All 2 Nodes] Extract Trino server to /opt
sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/

# [All 2 Nodes] Create symlink /opt/trino-server
sudo ln -sf /opt/trino-server-479 /opt/trino-server

# [All 2 Nodes] Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

# [All 2 Nodes] Create etc symlink for Trino launcher
sudo ln -sf /etc/trino /opt/trino-server/etc

```

**Configuration:**
```bash
# [All 2 Nodes] Configure Trino node properties
sudo tee /etc/trino/node.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
node.environment=production
node.id=3d98bde7-c4b8-4df5-a212-d361d7d642dd
node.data-dir=/var/trino/data
EOF

# [All 2 Nodes] Configure JVM with 49G heap (80% of 61.8G total RAM)
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

# [All 2 Nodes] Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
discovery.uri=http://&lt;PRIVATE_IP&gt;:8080
query.max-memory=70GB
query.max-memory-per-node=34GB
EOF

# [All 2 Nodes] Configure Hive catalog with file metastore at local:///data/trino/hive-metastore
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

# [All 2 Nodes] Create Trino systemd service
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
# [All 2 Nodes] Reload systemd daemon
sudo systemctl daemon-reload

```

**Setup:**
```bash
# [All 2 Nodes] Execute sudo command on remote system
sudo mkdir -p /data/trino/hive-metastore

# [All 2 Nodes] Execute sudo command on remote system
sudo chown -R trino:trino /data/trino/hive-metastore

# [All 2 Nodes] Execute sudo command on remote system
sudo chmod -R 755 /data/trino/hive-metastore

# [All 2 Nodes] Execute sudo command on remote system
sudo mkdir -p /etc/trino/catalog

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS664E2DFA3170C0601 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS664E2DFA3170C0601

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS664E2DFA3170C0601 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS664E2DFA3170C0601 /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create starrocks data directory
sudo mkdir -p /data/starrocks

# [All 2 Nodes] Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# [All 2 Nodes] Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 2 Nodes] Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# [All 2 Nodes] Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 2 Nodes] Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# [All 2 Nodes] Configure StarRocks FE
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

# [All 2 Nodes] Configure StarRocks BE
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
# [All 2 Nodes] Start StarRocks FE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 2 Nodes] Start StarRocks BE
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 2 Nodes] Execute test command on remote system
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
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44E14895DD2C6C843 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44E14895DD2C6C843

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44E14895DD2C6C843 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44E14895DD2C6C843 /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create clickhouse data directory
sudo mkdir -p /data/clickhouse

# [All 2 Nodes] Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# [All 2 Nodes] Update package lists
sudo apt-get update

# [All 2 Nodes] Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# [All 2 Nodes] Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 2 Nodes] Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 2 Nodes] Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# [All 2 Nodes] Install ClickHouse server and client version &lt;PUBLIC_IP&gt;
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 2 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;53066937139&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;8&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# [All 2 Nodes] Configure ClickHouse user profile with password and query settings
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
            &lt;max_memory_usage&gt;12000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;4000000000&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;4000000000&lt;/max_bytes_before_external_group_by&gt;
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
# [All 2 Nodes] Start ClickHouse server service
sudo systemctl start clickhouse-server

# [All 2 Nodes] Enable ClickHouse server to start on boot
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
    &lt;/zookeeper&gt;
    &lt;distributed_ddl&gt;
        &lt;path&gt;/clickhouse/task_queue/ddl&lt;/path&gt;
    &lt;/distributed_ddl&gt;
&lt;/clickhouse&gt;
EOF

```


**Tuning Parameters:**
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `12.0GB`

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
unzip extscal_nodes_2-benchmark.zip
cd extscal_nodes_2

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
| Clickhouse | 551.08s | 1.44s | 272.83s | 918.84s | N/A | N/A | N/A |
| Starrocks | 541.64s | 0.17s | 332.10s | 955.20s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 195.03s | 1.09s | 0.00s | 265.68s | N/A | N/A | N/A |
| Exasol | 273.83s | 2.28s | 308.10s | 655.32s | 47.9 GB | 10.5 GB | 4.5x |

**Key Observations:**
- Trino had the fastest preparation time at 265.68s
- Starrocks took 955.20s (3.6x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2390.7 |      5 |      6183.7 |    5923.3 |   1574   |   4124.6 |   7743.6 |
| Q01     | exasol     |    848.9 |      5 |      2692.3 |    2468.7 |    726.9 |   1309.1 |   3069.6 |
| Q01     | starrocks  |   3483.8 |      5 |      8233.9 |    7267.9 |   3785.1 |   2679.9 |  12232.9 |
| Q01     | trino      |  32736.4 |      5 |     56020.5 |   57053.8 |  18163.1 |  41367   |  86328.8 |
| Q02     | clickhouse |  13095   |      5 |     23668.5 |   22931.9 |   3288.6 |  17474.2 |  26414.1 |
| Q02     | exasol     |     92.8 |      5 |       219.4 |     215.9 |     36.8 |    158.1 |    259   |
| Q02     | starrocks  |    359.7 |      5 |       574.6 |     681.6 |    320.7 |    454.1 |   1247.2 |
| Q02     | trino      |  39957.7 |      5 |     34310.3 |   38417.4 |  16808.6 |  17586.9 |  63202.6 |
| Q03     | clickhouse |  21432.5 |      5 |     24091.4 |   25028.9 |   3505.3 |  21702   |  29507   |
| Q03     | exasol     |    625.4 |      5 |      1048.7 |    1548.8 |   1012   |    566   |   2732.5 |
| Q03     | starrocks  |    668.8 |      5 |       538.3 |    1252.5 |   1192.3 |    393.3 |   3091   |
| Q03     | trino      |  49397.9 |      5 |     37295.1 |   86960.5 |  70442.4 |  35339.6 | 179827   |
| Q04     | clickhouse |  12446.9 |      5 |     22893   |   21657   |   3814.3 |  15044.1 |  24878.5 |
| Q04     | exasol     |    162   |      5 |       573.7 |     551.5 |    189.1 |    258.1 |    783.1 |
| Q04     | starrocks  |    742.2 |      5 |      1645.6 |    1724.5 |    501.8 |   1094.8 |   2460.5 |
| Q04     | trino      |  24187.2 |      5 |     36406.7 |   56528   |  33623.7 |  28977.2 | 106638   |
| Q05     | clickhouse |  53920.4 |      5 |     77332.9 |   76000.3 |   4631.4 |  69442.1 |  81742.5 |
| Q05     | exasol     |    616.1 |      5 |      2142   |    1973.8 |    577.9 |    961   |   2387.5 |
| Q05     | starrocks  |   1166.5 |      5 |      3039.1 |    2930.3 |    216.5 |   2567.4 |   3078.6 |
| Q05     | trino      |  22572.2 |      5 |    222387   |  187691   |  86768.3 |  75737.7 | 276408   |
| Q06     | clickhouse |    285.9 |      5 |       554.5 |     760.8 |    406.1 |    419.6 |   1207.2 |
| Q06     | exasol     |     47.9 |      5 |       155   |     168   |    104.6 |     82.1 |    342.7 |
| Q06     | starrocks  |    108.1 |      5 |       216.6 |     223.7 |    113.4 |     83.9 |    387.9 |
| Q06     | trino      |  27814.2 |      5 |     94226.7 |   77589.9 |  41891.7 |  30429.8 | 128853   |
| Q07     | clickhouse |  66639.2 |      5 |     86753.4 |   85165.4 |  10625.2 |  69172.4 |  98939.9 |
| Q07     | exasol     |    725.7 |      5 |      2788.8 |    2445.2 |    917.9 |    811.9 |   3013.6 |
| Q07     | starrocks  |    584.9 |      5 |      1785   |    1533.1 |    550.7 |    573.3 |   1900.1 |
| Q07     | trino      |  32495   |      5 |    102260   |  105133   |  47049.3 |  33144.5 | 150978   |
| Q08     | clickhouse | 100062   |      5 |    133513   |  129826   |   5918.6 | 121813   | 135048   |
| Q08     | exasol     |    262.6 |      5 |       919.8 |     842   |    245.7 |    420.4 |   1061.9 |
| Q08     | starrocks  |    719.9 |      5 |      2449.8 |    2657.1 |    611.6 |   1934.4 |   3426   |
| Q08     | trino      |  33569.1 |      5 |    102746   |  126181   |  77067.8 |  61431.7 | 256745   |
| Q09     | clickhouse |   8998.9 |      5 |     23151.9 |   24979.6 |   9534.6 |  15623.5 |  35767.3 |
| Q09     | exasol     |   1839   |      5 |      7744.3 |    7684.4 |    879.6 |   6446   |   8701.2 |
| Q09     | starrocks  |   1997.3 |      5 |      4627   |    4624.8 |    622.2 |   3791.8 |   5506.5 |
| Q09     | trino      |  40415.3 |      5 |    106284   |  105269   |  34968.7 |  69325.4 | 153022   |
| Q10     | clickhouse |  26279.6 |      5 |     42102.7 |   41127   |   4171   |  34984.8 |  46462.1 |
| Q10     | exasol     |    688.9 |      5 |      1921.4 |    1564.9 |    588.6 |    876.3 |   2059.2 |
| Q10     | starrocks  |    854.9 |      5 |      2374.6 |    2240.2 |    484.6 |   1711.7 |   2772.3 |
| Q10     | trino      |  96925.7 |      5 |    180595   |  236802   | 168263   |  85620.8 | 479894   |
| Q11     | clickhouse |    742.3 |      5 |      3051.2 |    3394.2 |    642.9 |   2801.3 |   4191.5 |
| Q11     | exasol     |   1188   |      5 |       523.3 |     527.5 |    165.3 |    292   |    747.6 |
| Q11     | starrocks  |    141   |      5 |       437.2 |     483.8 |    116.9 |    396.4 |    685.3 |
| Q11     | trino      |  11542.4 |      5 |     19908.9 |   22291.1 |   8454.5 |  12682.7 |  34306.1 |
| Q12     | clickhouse |  20064.2 |      5 |     31761.1 |   30927.8 |   3012.9 |  27838.1 |  35066.4 |
| Q12     | exasol     |    206.5 |      5 |       543   |     592.4 |    111.3 |    485.8 |    713.5 |
| Q12     | starrocks  |    358.3 |      5 |       928.4 |     954.6 |    260.1 |    680.1 |   1309   |
| Q12     | trino      |  38675.4 |      5 |    103676   |  108588   |  57633.3 |  44386.5 | 167611   |
| Q13     | clickhouse |  23665.4 |      5 |     32631.5 |   32423.2 |   2542.8 |  29589.2 |  35130.6 |
| Q13     | exasol     |    787.2 |      5 |      3177.4 |    2843.3 |   1027.7 |   1084.4 |   3770.8 |
| Q13     | starrocks  |   1770.4 |      5 |      4215.8 |    3568.8 |   1139.3 |   1709.7 |   4370   |
| Q13     | trino      |  17866.1 |      5 |     33834.3 |   47179.7 |  27429.1 |  18903.9 |  80163.5 |
| Q14     | clickhouse |   1086.2 |      5 |      2911.7 |    2851.2 |    650.2 |   2086.5 |   3721.6 |
| Q14     | exasol     |    215.3 |      5 |       693.6 |     703.6 |    144.8 |    555.5 |    895.9 |
| Q14     | starrocks  |    126.3 |      5 |       397.1 |     490.2 |    270.1 |    287.9 |    965.2 |
| Q14     | trino      |  24808.6 |      5 |     76573.7 |   86345.3 |  35454.5 |  45053.5 | 125524   |
| Q15     | clickhouse |    319.5 |      5 |      1187.5 |    1334.9 |    386.6 |    983.5 |   1862.5 |
| Q15     | exasol     |    303.2 |      5 |       941.6 |     878.5 |    128.3 |    717.4 |    999.7 |
| Q15     | starrocks  |    162.2 |      5 |       514.8 |     579.1 |    259.3 |    246.8 |    927.1 |
| Q15     | trino      |  42091.3 |      5 |    108027   |  113672   |  29643.4 |  79040.4 | 161043   |
| Q16     | clickhouse |   1820.7 |      5 |      3847   |    5009.1 |   1999   |   3438.2 |   7852.5 |
| Q16     | exasol     |    481   |      5 |      1344   |    1316.9 |     49.8 |   1233.8 |   1353.7 |
| Q16     | starrocks  |    481.7 |      5 |       866.8 |     948.2 |    301.6 |    741.3 |   1477   |
| Q16     | trino      |  10215.9 |      5 |     26376.4 |   31872.1 |  17584.9 |   9090.2 |  51619.5 |
| Q17     | clickhouse |   1491.9 |      5 |      3360.1 |    3934.6 |   1894   |   2312.2 |   7189.8 |
| Q17     | exasol     |     70.1 |      5 |       137.2 |     137   |      6.9 |    128.2 |    144.1 |
| Q17     | starrocks  |    717.5 |      5 |      1355.7 |    1434.5 |    424.2 |   1025.3 |   2018.8 |
| Q17     | trino      |  44683.1 |      5 |    124693   |  122907   |  39541.3 |  64593.9 | 160265   |
| Q18     | clickhouse |   4410.5 |      5 |     12620.2 |   14476.1 |   5798.7 |   9295.2 |  23533.4 |
| Q18     | exasol     |    541.8 |      5 |      1813.7 |    1671.8 |    429.4 |    922.3 |   2013.5 |
| Q18     | starrocks  |   3150.1 |      5 |     10625.2 |   11956.1 |   2751.5 |  10599.2 |  16865.4 |
| Q18     | trino      |  37785.1 |      5 |    134668   |  133234   |  18969.2 | 113919   | 156167   |
| Q19     | clickhouse |   8330.2 |      5 |     14840.1 |   15480.3 |   3428.2 |  12492.9 |  21338.2 |
| Q19     | exasol     |     80.3 |      5 |       129.2 |     173.8 |     90.5 |     98.6 |    305.5 |
| Q19     | starrocks  |    686.4 |      5 |      1843.2 |    2125.5 |    916.5 |   1127.2 |   3580.6 |
| Q19     | trino      |  27676.3 |      5 |     42780.9 |   50625.5 |  26240.8 |  29108.5 |  96082.9 |
| Q20     | clickhouse |   3618   |      5 |      7956   |   10037.3 |   3430.4 |   7110.6 |  14817.8 |
| Q20     | exasol     |    311.8 |      5 |       580.2 |     593.5 |    224.9 |    348.1 |    867.4 |
| Q20     | starrocks  |    286   |      5 |      1369   |    1456   |    701.2 |    767.8 |   2381   |
| Q20     | trino      |  33038.6 |      5 |    116152   |  101213   |  47686.7 |  48211.9 | 160214   |
| Q21     | clickhouse |   4258.4 |      5 |     11584.4 |   11711.5 |   2511.9 |   8292.2 |  15133.5 |
| Q21     | exasol     |  10098.2 |      5 |      1554.5 |    1656.8 |    601.8 |   1034   |   2324.6 |
| Q21     | starrocks  |   4775.7 |      5 |     10331   |   10358.5 |   3250.5 |   6144.7 |  13993.7 |
| Q21     | trino      |  66425.4 |      5 |     92023   |  118030   |  45577.3 |  82425.9 | 188940   |
| Q22     | clickhouse |    898.5 |      5 |      4611   |    4613.5 |   2161.5 |   1850.5 |   7714.6 |
| Q22     | exasol     |    115.5 |      5 |       363.8 |     339.7 |     95.1 |    174.4 |    407.1 |
| Q22     | starrocks  |    405.7 |      5 |       896   |     819.6 |    247.8 |    384.8 |   1007.7 |
| Q22     | trino      |  10925.4 |      5 |     16194.6 |   14092.5 |   4206.3 |   7103.8 |  17397.4 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        2692.3 |          8233.9 |    3.06 |      0.33 | False    |
| Q02     | exasol            | starrocks           |         219.4 |           574.6 |    2.62 |      0.38 | False    |
| Q03     | exasol            | starrocks           |        1048.7 |           538.3 |    0.51 |      1.95 | True     |
| Q04     | exasol            | starrocks           |         573.7 |          1645.6 |    2.87 |      0.35 | False    |
| Q05     | exasol            | starrocks           |        2142   |          3039.1 |    1.42 |      0.7  | False    |
| Q06     | exasol            | starrocks           |         155   |           216.6 |    1.4  |      0.72 | False    |
| Q07     | exasol            | starrocks           |        2788.8 |          1785   |    0.64 |      1.56 | True     |
| Q08     | exasol            | starrocks           |         919.8 |          2449.8 |    2.66 |      0.38 | False    |
| Q09     | exasol            | starrocks           |        7744.3 |          4627   |    0.6  |      1.67 | True     |
| Q10     | exasol            | starrocks           |        1921.4 |          2374.6 |    1.24 |      0.81 | False    |
| Q11     | exasol            | starrocks           |         523.3 |           437.2 |    0.84 |      1.2  | True     |
| Q12     | exasol            | starrocks           |         543   |           928.4 |    1.71 |      0.58 | False    |
| Q13     | exasol            | starrocks           |        3177.4 |          4215.8 |    1.33 |      0.75 | False    |
| Q14     | exasol            | starrocks           |         693.6 |           397.1 |    0.57 |      1.75 | True     |
| Q15     | exasol            | starrocks           |         941.6 |           514.8 |    0.55 |      1.83 | True     |
| Q16     | exasol            | starrocks           |        1344   |           866.8 |    0.64 |      1.55 | True     |
| Q17     | exasol            | starrocks           |         137.2 |          1355.7 |    9.88 |      0.1  | False    |
| Q18     | exasol            | starrocks           |        1813.7 |         10625.2 |    5.86 |      0.17 | False    |
| Q19     | exasol            | starrocks           |         129.2 |          1843.2 |   14.27 |      0.07 | False    |
| Q20     | exasol            | starrocks           |         580.2 |          1369   |    2.36 |      0.42 | False    |
| Q21     | exasol            | starrocks           |        1554.5 |         10331   |    6.65 |      0.15 | False    |
| Q22     | exasol            | starrocks           |         363.8 |           896   |    2.46 |      0.41 | False    |
| Q01     | exasol            | clickhouse          |        2692.3 |          6183.7 |    2.3  |      0.44 | False    |
| Q02     | exasol            | clickhouse          |         219.4 |         23668.5 |  107.88 |      0.01 | False    |
| Q03     | exasol            | clickhouse          |        1048.7 |         24091.4 |   22.97 |      0.04 | False    |
| Q04     | exasol            | clickhouse          |         573.7 |         22893   |   39.9  |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        2142   |         77332.9 |   36.1  |      0.03 | False    |
| Q06     | exasol            | clickhouse          |         155   |           554.5 |    3.58 |      0.28 | False    |
| Q07     | exasol            | clickhouse          |        2788.8 |         86753.4 |   31.11 |      0.03 | False    |
| Q08     | exasol            | clickhouse          |         919.8 |        133513   |  145.15 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        7744.3 |         23151.9 |    2.99 |      0.33 | False    |
| Q10     | exasol            | clickhouse          |        1921.4 |         42102.7 |   21.91 |      0.05 | False    |
| Q11     | exasol            | clickhouse          |         523.3 |          3051.2 |    5.83 |      0.17 | False    |
| Q12     | exasol            | clickhouse          |         543   |         31761.1 |   58.49 |      0.02 | False    |
| Q13     | exasol            | clickhouse          |        3177.4 |         32631.5 |   10.27 |      0.1  | False    |
| Q14     | exasol            | clickhouse          |         693.6 |          2911.7 |    4.2  |      0.24 | False    |
| Q15     | exasol            | clickhouse          |         941.6 |          1187.5 |    1.26 |      0.79 | False    |
| Q16     | exasol            | clickhouse          |        1344   |          3847   |    2.86 |      0.35 | False    |
| Q17     | exasol            | clickhouse          |         137.2 |          3360.1 |   24.49 |      0.04 | False    |
| Q18     | exasol            | clickhouse          |        1813.7 |         12620.2 |    6.96 |      0.14 | False    |
| Q19     | exasol            | clickhouse          |         129.2 |         14840.1 |  114.86 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         580.2 |          7956   |   13.71 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1554.5 |         11584.4 |    7.45 |      0.13 | False    |
| Q22     | exasol            | clickhouse          |         363.8 |          4611   |   12.67 |      0.08 | False    |
| Q01     | exasol            | trino               |        2692.3 |         56020.5 |   20.81 |      0.05 | False    |
| Q02     | exasol            | trino               |         219.4 |         34310.3 |  156.38 |      0.01 | False    |
| Q03     | exasol            | trino               |        1048.7 |         37295.1 |   35.56 |      0.03 | False    |
| Q04     | exasol            | trino               |         573.7 |         36406.7 |   63.46 |      0.02 | False    |
| Q05     | exasol            | trino               |        2142   |        222387   |  103.82 |      0.01 | False    |
| Q06     | exasol            | trino               |         155   |         94226.7 |  607.91 |      0    | False    |
| Q07     | exasol            | trino               |        2788.8 |        102260   |   36.67 |      0.03 | False    |
| Q08     | exasol            | trino               |         919.8 |        102746   |  111.71 |      0.01 | False    |
| Q09     | exasol            | trino               |        7744.3 |        106284   |   13.72 |      0.07 | False    |
| Q10     | exasol            | trino               |        1921.4 |        180595   |   93.99 |      0.01 | False    |
| Q11     | exasol            | trino               |         523.3 |         19908.9 |   38.04 |      0.03 | False    |
| Q12     | exasol            | trino               |         543   |        103676   |  190.93 |      0.01 | False    |
| Q13     | exasol            | trino               |        3177.4 |         33834.3 |   10.65 |      0.09 | False    |
| Q14     | exasol            | trino               |         693.6 |         76573.7 |  110.4  |      0.01 | False    |
| Q15     | exasol            | trino               |         941.6 |        108027   |  114.73 |      0.01 | False    |
| Q16     | exasol            | trino               |        1344   |         26376.4 |   19.63 |      0.05 | False    |
| Q17     | exasol            | trino               |         137.2 |        124693   |  908.84 |      0    | False    |
| Q18     | exasol            | trino               |        1813.7 |        134668   |   74.25 |      0.01 | False    |
| Q19     | exasol            | trino               |         129.2 |         42780.9 |  331.12 |      0    | False    |
| Q20     | exasol            | trino               |         580.2 |        116152   |  200.19 |      0    | False    |
| Q21     | exasol            | trino               |        1554.5 |         92023   |   59.2  |      0.02 | False    |
| Q22     | exasol            | trino               |         363.8 |         16194.6 |   44.52 |      0.02 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 28845.6 | 23812.4 | 426.3 | 98939.9 |
| 1 | 28 | 26899.6 | 8504.9 | 554.5 | 135047.6 |
| 2 | 27 | 25219.6 | 14817.8 | 419.6 | 133512.9 |
| 3 | 27 | 22450.7 | 14840.1 | 983.5 | 121812.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 8504.9ms
- Slowest stream median: 23812.4ms
- Stream performance variation: 180.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1570.0 | 1326.5 | 82.1 | 3770.8 |
| 1 | 28 | 1193.0 | 729.1 | 128.2 | 8701.2 |
| 2 | 27 | 1586.6 | 711.0 | 92.5 | 7744.3 |
| 3 | 27 | 1269.9 | 747.6 | 137.2 | 8270.6 |

**Performance Analysis for Exasol:**
- Fastest stream median: 711.0ms
- Slowest stream median: 1326.5ms
- Stream performance variation: 86.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3028.8 | 1836.0 | 83.9 | 13993.7 |
| 1 | 28 | 2538.3 | 1158.7 | 216.6 | 16865.4 |
| 2 | 27 | 2916.4 | 1843.2 | 166.5 | 12232.9 |
| 3 | 27 | 2478.9 | 1355.7 | 263.4 | 10599.2 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1158.7ms
- Slowest stream median: 1843.2ms
- Stream performance variation: 59.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 104554.9 | 75914.6 | 7103.8 | 479894.5 |
| 1 | 28 | 84562.3 | 79210.8 | 16194.6 | 179826.9 |
| 2 | 27 | 101026.9 | 96082.9 | 9090.2 | 256744.7 |
| 3 | 27 | 78347.2 | 60690.7 | 13249.3 | 160264.9 |

**Performance Analysis for Trino:**
- Fastest stream median: 60690.7ms
- Slowest stream median: 96082.9ms
- Stream performance variation: 58.3% difference between fastest and slowest streams
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

**exasol:**
- Median runtime: 871.5ms
- Average runtime: 1404.5ms
- Fastest query: 82.1ms
- Slowest query: 8701.2ms

**starrocks:**
- Median runtime: 1674.2ms
- Average runtime: 2741.4ms
- Fastest query: 83.9ms
- Slowest query: 16865.4ms

**clickhouse:**
- Median runtime: 14933.4ms
- Average runtime: 25890.6ms
- Fastest query: 419.6ms
- Slowest query: 135047.6ms

**trino:**
- Median runtime: 79601.9ms
- Average runtime: 92167.1ms
- Fastest query: 7103.8ms
- Slowest query: 479894.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_2-benchmark.zip`](extscal_nodes_2-benchmark.zip)

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
  - memory_limit: 48g
  - max_threads: 8
  - max_memory_usage: 12000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 8000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 70GB
  - query_max_memory_per_node: 35GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 8
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