# Extended Scalability - Node Scaling (8 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / m6id.large
**Date:** 2026-01-30 00:47:21

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **clickhouse**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 1390.2ms median runtime
- trino was 41.7x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 8-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 8 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (16 total vCPUs)
- **Memory per node:** 7.6GB RAM (60.8GB total RAM)
- **Node hostnames:**
  - exasol-node5: ip-10-0-1-161
  - exasol-node3: ip-10-0-1-167
  - exasol-node4: ip-10-0-1-232
  - exasol-node0: ip-10-0-1-222
  - exasol-node1: ip-10-0-1-202
  - exasol-node7: ip-10-0-1-215
  - exasol-node2: ip-10-0-1-252
  - exasol-node6: ip-10-0-1-139

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 8-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 8 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (16 total vCPUs)
- **Memory per node:** 7.6GB RAM (60.8GB total RAM)
- **Node hostnames:**
  - clickhouse-node7: ip-10-0-1-57
  - clickhouse-node3: ip-10-0-1-141
  - clickhouse-node6: ip-10-0-1-20
  - clickhouse-node1: ip-10-0-1-170
  - clickhouse-node5: ip-10-0-1-12
  - clickhouse-node4: ip-10-0-1-139
  - clickhouse-node2: ip-10-0-1-197
  - clickhouse-node0: ip-10-0-1-100

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 8-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 8 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (16 total vCPUs)
- **Memory per node:** 7.6GB RAM (60.8GB total RAM)
- **Node hostnames:**
  - trino-node3: ip-10-0-1-94
  - trino-node4: ip-10-0-1-82
  - trino-node2: ip-10-0-1-216
  - trino-node5: ip-10-0-1-194
  - trino-node1: ip-10-0-1-214
  - trino-node0: ip-10-0-1-102
  - trino-node7: ip-10-0-1-37
  - trino-node6: ip-10-0-1-4

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 8-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 8 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (16 total vCPUs)
- **Memory per node:** 7.6GB RAM (60.8GB total RAM)
- **Node hostnames:**
  - starrocks-node0: ip-10-0-1-167
  - starrocks-node6: ip-10-0-1-188
  - starrocks-node4: ip-10-0-1-52
  - starrocks-node2: ip-10-0-1-203
  - starrocks-node3: ip-10-0-1-177
  - starrocks-node1: ip-10-0-1-200
  - starrocks-node5: ip-10-0-1-130
  - starrocks-node7: ip-10-0-1-180


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** m6id.large
- **Clickhouse Instance:** m6id.large
- **Trino Instance:** m6id.large
- **Starrocks Instance:** m6id.large


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# [All 8 Nodes] Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# [All 8 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 8 Nodes] Create 70GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 8 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 8 Nodes] Create raw partition for Exasol (39GB)
sudo parted /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 8 Nodes] Execute sudo command on remote system
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
sudo useradd -m -s /bin/bash exasol

# [All 8 Nodes] Add exasol user to sudo group
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
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;&#34;
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
# [All 8 Nodes] Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# [All 8 Nodes] Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# [All 8 Nodes] Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

# Execute wget command on remote system
wget -q https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

# Execute echo command on remote system
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
CCC_PLAY_DB_MEM_SIZE=48000
CCC_ADMINUI_START_SERVER=true&#34; | tee /tmp/exasol_c4.conf &gt; /dev/null

# Execute ./c4 command on remote system
./c4 host play -i /tmp/exasol_c4.conf

# Execute c4 command on remote system
c4 ps

# Execute cat command on remote system
cat /tmp/exasol.license | c4 connect -s cos -i 1 -- confd_client license_upload license: &#39;\&#34;&#34;{&lt; -}&#34;\&#34;&#39;

# Execute c4 command on remote system
c4 connect -s cos -i 1 -- confd_client db_stop db_name: Exasol

# Execute c4 command on remote system
c4 connect -s cos -i 1 -- confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;]&#34;

# Execute c4 command on remote system
c4 connect -s cos -i 1 -- confd_client db_start db_name: Exasol

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
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS8CB849DAB0F345BDA with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS8CB849DAB0F345BDA

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS8CB849DAB0F345BDA to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS8CB849DAB0F345BDA /data

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
sudo useradd -r -s /bin/false trino

```

**Installation:**
```bash
# [All 8 Nodes] Download Trino server version 479
wget https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

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
node.id=c1d75240-219a-47fb-a933-a5eef5aafa1d
node.data-dir=/var/trino/data
EOF

# [All 8 Nodes] Configure JVM with 6G heap (80% of 7.6G total RAM)
sudo tee /etc/trino/jvm.config &gt; /dev/null &lt;&lt; &#39;EOF&#39;
-server
-Xmx6G
-Xms6G
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
query.max-memory=36GB
query.max-memory-per-node=4GB
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
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS18360BB9A1EC0EEC3 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS18360BB9A1EC0EEC3

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS18360BB9A1EC0EEC3 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS18360BB9A1EC0EEC3 /data

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
# [All 8 Nodes] Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

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
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 8 Nodes] Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 8 Nodes] Execute sudo command on remote system
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 8 Nodes] Execute echo command on remote system
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

# [All 8 Nodes] Execute wget command on remote system
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 8 Nodes] Execute sudo command on remote system
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 8 Nodes] Execute sudo command on remote system
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

# [All 8 Nodes] Execute sudo command on remote system
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

# [All 8 Nodes] Execute sudo command on remote system
sudo chown -R $(whoami):$(whoami) /opt/starrocks

# [All 8 Nodes] Execute export command on remote system
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 8 Nodes] Execute export command on remote system
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

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
# [All 8 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7DEE09DDC7B4C7B7A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7DEE09DDC7B4C7B7A

# [All 8 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 8 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7DEE09DDC7B4C7B7A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7DEE09DDC7B4C7B7A /data

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
sudo apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 8 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;6526985830&lt;/max_server_memory_usage&gt;
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

**Setup:**
```bash
# [All 8 Nodes] Execute sudo command on remote system
sudo apt-get update

# [All 8 Nodes] Execute sudo command on remote system
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

# [All 8 Nodes] Execute curl command on remote system
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 8 Nodes] Execute ARCH=$(dpkg command on remote system
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 8 Nodes] Execute DEBIAN_FRONTEND=noninteractive command on remote system
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

# [All 8 Nodes] Execute sudo command on remote system
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;6526985830&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

# [All 8 Nodes] Execute sudo command on remote system
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

# [All 8 Nodes] Execute sudo command on remote system
sudo systemctl start clickhouse-server

# [All 8 Nodes] Execute sudo command on remote system
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
- Memory limit: `6g`
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
unzip ext_scalability_nodes_8-benchmark.zip
cd ext_scalability_nodes_8

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
| Q01     | clickhouse |   2587.4 |      5 |      8701   |    8403.7 |   4094.5 |   4353.2 |  14382.2 |
| Q01     | exasol     |    820   |      5 |      3015.2 |    2669.1 |   1073.2 |   1229.2 |   3645.4 |
| Q01     | starrocks  |  26496.5 |      5 |    128456   |  128875   |  62926.9 |  35046.3 | 207795   |
| Q01     | trino      |  17056.3 |      5 |     39837   |   42531.5 |   7039.5 |  33884.3 |  51477.5 |
| Q02     | clickhouse |  61460.6 |      5 |    223713   |  216125   |  28914.6 | 171961   | 244008   |
| Q02     | exasol     |    194.2 |      5 |       830.6 |    1217.7 |    815.9 |    434.1 |   2146.7 |
| Q02     | starrocks  |   1576.8 |      5 |      3472.3 |    4067.6 |   1898.4 |   2247.8 |   6448.5 |
| Q02     | trino      |  13213.4 |      5 |     61562.3 |   56667.5 |  17224.5 |  36974   |  73046.7 |
| Q03     | clickhouse |  12851.8 |      5 |     37141   |   39107.6 |   9109.5 |  27014.7 |  50426.2 |
| Q03     | exasol     |    736.4 |      5 |      1981   |    1886.9 |    912.2 |    736   |   2871.6 |
| Q03     | starrocks  |  13141   |      5 |     26482.4 |   33066.5 |  19458.1 |  11403.1 |  60062.2 |
| Q03     | trino      |  26148.7 |      5 |     72412   |   75037.8 |  12137.2 |  63526.3 |  92317.8 |
| Q04     | clickhouse |   8858.4 |      5 |     18847.4 |   22899   |  10501.8 |  17170   |  41629.4 |
| Q04     | exasol     |    234.4 |      5 |      1371   |    1363.8 |    685   |    571.7 |   2268.5 |
| Q04     | starrocks  |   9229.1 |      5 |     92326.7 |  113471   |  86720.6 |  29288.9 | 227539   |
| Q04     | trino      |  13468.9 |      5 |     35340.7 |   36716.9 |  10619.5 |  24744.9 |  48785.5 |
| Q05     | clickhouse |  12287.8 |      5 |     39249.4 |   30102.9 |  18911.7 |    808   |  45698.1 |
| Q05     | exasol     |    884.7 |      5 |      4103   |    4236.9 |   2004   |   2016.3 |   6393.3 |
| Q05     | starrocks  |  12539.1 |      5 |     31028.4 |   30790.7 |   3995.5 |  24725.4 |  35281.6 |
| Q05     | trino      |  15551.4 |      5 |     55925   |   57893.6 |  14957.5 |  35569.6 |  75436   |
| Q06     | clickhouse |    275.6 |      5 |       894.9 |     740.9 |    342.5 |    333.4 |   1073.6 |
| Q06     | exasol     |     61.6 |      5 |       383.5 |     354.9 |    243.3 |     95.1 |    626.2 |
| Q06     | starrocks  |   9960.5 |      5 |      4639.1 |    8306.6 |   6536.7 |   3971.5 |  19298.6 |
| Q06     | trino      |  16662.8 |      5 |     46966   |   49024.7 |  11418.4 |  32693.1 |  60936.3 |
| Q07     | clickhouse |   2762.1 |      5 |     11736.8 |   11357.8 |   1630.6 |   9586.2 |  13386.2 |
| Q07     | exasol     |   1313.7 |      5 |      3677.2 |    3408.1 |   1267.2 |   1345.6 |   4779.8 |
| Q07     | starrocks  |  14279.1 |      5 |     28576.2 |   31724.1 |   8055.8 |  24877.4 |  44134.2 |
| Q07     | trino      |  20625.6 |      5 |     62125.5 |   61076.6 |  14888   |  38061.5 |  76348.6 |
| Q08     | clickhouse |   3232.6 |      5 |     11796.9 |    8986.4 |   6704.5 |    232.2 |  14782.3 |
| Q08     | exasol     |    456.4 |      5 |      1855.9 |    2439.7 |   1380   |   1058.2 |   4388.9 |
| Q08     | starrocks  |  17436.5 |      5 |     29169.3 |   27750.6 |   6167.6 |  18475.4 |  35338.5 |
| Q08     | trino      |  21617.2 |      5 |     62587.7 |   58674.4 |  21352.9 |  31705.1 |  85617.6 |
| Q09     | clickhouse |   2889.3 |      5 |     10996   |   10094.9 |   1951.2 |   7750.3 |  12316.3 |
| Q09     | exasol     |   3733.7 |      5 |     12865.1 |   13794   |   3099.8 |  10212.4 |  18410.4 |
| Q09     | starrocks  |  22765.9 |      5 |     47584.7 |   47257.4 |   5058.8 |  39004   |  52275.6 |
| Q09     | trino      |  23625   |      5 |     69169.7 |   71521.6 |  12448.4 |  60997   |  92942.9 |
| Q10     | clickhouse |  12106.1 |      5 |     46684.8 |   31336   |  26103.5 |    277.4 |  56187.8 |
| Q10     | exasol     |    654.2 |      5 |      1311.5 |    2815.7 |   2566.7 |   1177.4 |   7176.2 |
| Q10     | starrocks  |  17945.5 |      5 |     39742.4 |   30411.7 |  20039.2 |   5648.5 |  47843   |
| Q10     | trino      |  32805.1 |      5 |    139737   |  129464   |  43087.5 |  70467   | 178986   |
| Q11     | clickhouse |   1023   |      5 |      4935.5 |    4427.2 |   1160   |   2367.6 |   5117.7 |
| Q11     | exasol     |   1359.4 |      5 |       688.1 |     881.5 |    443.6 |    576.4 |   1660.5 |
| Q11     | starrocks  |   1072.9 |      5 |      2811.3 |    3255.8 |   1383.3 |   2257.2 |   5646.6 |
| Q11     | trino      |   6576   |      5 |     43602.9 |   46946.2 |  12056.3 |  31742.3 |  64004.8 |
| Q12     | clickhouse |   2965.1 |      5 |      8080.8 |    8918.8 |   2840.3 |   6201.3 |  12037.5 |
| Q12     | exasol     |    227.6 |      5 |       828.4 |     839.1 |    208.9 |    539.1 |   1124.1 |
| Q12     | starrocks  |  11429.6 |      5 |     18052.1 |   22868   |   8733.6 |  15955.1 |  34736.5 |
| Q12     | trino      |  23480   |      5 |     82292.4 |   76568.1 |  10090.3 |  59910.7 |  83822.5 |
| Q13     | clickhouse |   2834   |      5 |      7547.9 |    7296.9 |   5030.3 |    135.5 |  13792.7 |
| Q13     | exasol     |    847.6 |      5 |      3309.5 |    6104.8 |   4848   |   1409.3 |  11787.1 |
| Q13     | starrocks  |  12115.2 |      5 |     25663.1 |   32092.4 |  11954.8 |  24411.9 |  52806.3 |
| Q13     | trino      |   8828.4 |      5 |     23074.9 |   24722.8 |   4997   |  21507.5 |  33487.2 |
| Q14     | clickhouse |   3419.1 |      5 |     12090.9 |    9072.2 |   5320   |    856.2 |  13051.7 |
| Q14     | exasol     |    280.4 |      5 |      1092.1 |    1017   |    157.3 |    801.8 |   1152.2 |
| Q14     | starrocks  |   5877.5 |      5 |     12125.2 |   12920.8 |   2964   |  10284.8 |  17740.9 |
| Q14     | trino      |  13822.2 |      5 |     51375.9 |   48820   |  12910.1 |  31763.4 |  64624.1 |
| Q15     | clickhouse |    620.3 |      5 |      2592.1 |    2277.4 |    873.8 |   1270.1 |   3065.3 |
| Q15     | exasol     |    290.8 |      5 |      1946.7 |    1919.3 |    721.6 |    913.7 |   2911.9 |
| Q15     | starrocks  |   4533.6 |      5 |     11464   |    9322.2 |   4084.9 |   4784.1 |  13459.3 |
| Q15     | trino      |  24855   |      5 |     52748   |   55941.9 |   8945.7 |  47224.2 |  67582.2 |
| Q16     | clickhouse |   6398.7 |      5 |     25467.4 |   20840.1 |   7065.5 |  12550.2 |  26913.1 |
| Q16     | exasol     |    454.9 |      5 |      1673.7 |    2282.4 |   1072.1 |   1290.9 |   3476.1 |
| Q16     | starrocks  |   2771.5 |      5 |      7887.1 |    7495.5 |   2017.3 |   4304.5 |   9874.3 |
| Q16     | trino      |   4960.1 |      5 |     23802.8 |   27603.9 |  14727.2 |  15640.8 |  53201.7 |
| Q17     | clickhouse |   5201.1 |      5 |      9959   |    8485.5 |   2565.6 |   5089   |  10678.4 |
| Q17     | exasol     |    192   |      5 |       423.3 |     488.3 |    215.6 |    312.6 |    839.3 |
| Q17     | starrocks  |   5437.2 |      5 |      7086.6 |   10196   |   5816.8 |   6183.9 |  19746.9 |
| Q17     | trino      |  26419.9 |      5 |     68428.8 |   59005.1 |  21288.8 |  27671.4 |  77129.9 |
| Q18     | clickhouse |   4430.3 |      5 |     12143.4 |   12874.4 |   4223.6 |   8638.5 |  19096.9 |
| Q18     | exasol     |    869.4 |      5 |      3954.1 |    3315.4 |   1459   |   1022.1 |   4486.7 |
| Q18     | starrocks  |  18027.9 |      5 |     68539   |   57991.4 |  24159.2 |  28565.8 |  83458.1 |
| Q18     | trino      |  23110.9 |      5 |     82906.6 |   82425.7 |  17118.7 |  62219.6 | 107457   |
| Q19     | clickhouse |  28436.5 |      5 |    119246   |   89044.2 |  53338.8 |    487.8 | 128494   |
| Q19     | exasol     |    194   |      5 |       331   |     367.6 |    138.8 |    177.3 |    515.2 |
| Q19     | starrocks  |   6045.6 |      5 |      9366   |    8986.5 |   1880.8 |   6198.6 |  11334.5 |
| Q19     | trino      |  16324.7 |      5 |     49564.4 |   49489.3 |  15149.1 |  27823.4 |  69255.4 |
| Q20     | clickhouse |   6704   |      5 |     22879.7 |   20964.6 |   6546.5 |  10338.3 |  26697.8 |
| Q20     | exasol     |    706   |      5 |      1118.2 |    1290.7 |    682.3 |    665.8 |   2440.7 |
| Q20     | starrocks  |   5623.3 |      5 |     10007.8 |   14537.5 |   9803.3 |   5967   |  25588.1 |
| Q20     | trino      |  19467   |      5 |     68265.1 |   65301.8 |  10627.9 |  51144.3 |  78450.8 |
| Q21     | clickhouse |   2844.1 |      5 |     14486.2 |   14022.8 |   2915.6 |   9141.8 |  16941.5 |
| Q21     | exasol     |  11317.8 |      5 |      2148.9 |    2227.2 |    737.2 |   1470.2 |   3153.5 |
| Q21     | starrocks  |  32660.1 |      5 |    106027   |   99022.6 |  37442.5 |  44888.6 | 146254   |
| Q21     | trino      |  35730.8 |      5 |     88669.8 |   85364   |  14927.6 |  64922.5 | 102058   |
| Q22     | clickhouse |   2956   |      5 |     12760   |   10714.7 |   3975.2 |   6029.8 |  14088.1 |
| Q22     | exasol     |    163.3 |      5 |       585.9 |     587   |     41.5 |    539.9 |    642.8 |
| Q22     | starrocks  |   2356.7 |      5 |      7156.9 |    7562.6 |   4551.6 |   2893   |  13480.7 |
| Q22     | trino      |   4540.6 |      5 |     15121.4 |   23241.4 |  16977.7 |  12461.4 |  52999.2 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3015.2 |          8701   |    2.89 |      0.35 | False    |
| Q02     | exasol            | clickhouse          |         830.6 |        223713   |  269.34 |      0    | False    |
| Q03     | exasol            | clickhouse          |        1981   |         37141   |   18.75 |      0.05 | False    |
| Q04     | exasol            | clickhouse          |        1371   |         18847.4 |   13.75 |      0.07 | False    |
| Q05     | exasol            | clickhouse          |        4103   |         39249.4 |    9.57 |      0.1  | False    |
| Q06     | exasol            | clickhouse          |         383.5 |           894.9 |    2.33 |      0.43 | False    |
| Q07     | exasol            | clickhouse          |        3677.2 |         11736.8 |    3.19 |      0.31 | False    |
| Q08     | exasol            | clickhouse          |        1855.9 |         11796.9 |    6.36 |      0.16 | False    |
| Q09     | exasol            | clickhouse          |       12865.1 |         10996   |    0.85 |      1.17 | True     |
| Q10     | exasol            | clickhouse          |        1311.5 |         46684.8 |   35.6  |      0.03 | False    |
| Q11     | exasol            | clickhouse          |         688.1 |          4935.5 |    7.17 |      0.14 | False    |
| Q12     | exasol            | clickhouse          |         828.4 |          8080.8 |    9.75 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        3309.5 |          7547.9 |    2.28 |      0.44 | False    |
| Q14     | exasol            | clickhouse          |        1092.1 |         12090.9 |   11.07 |      0.09 | False    |
| Q15     | exasol            | clickhouse          |        1946.7 |          2592.1 |    1.33 |      0.75 | False    |
| Q16     | exasol            | clickhouse          |        1673.7 |         25467.4 |   15.22 |      0.07 | False    |
| Q17     | exasol            | clickhouse          |         423.3 |          9959   |   23.53 |      0.04 | False    |
| Q18     | exasol            | clickhouse          |        3954.1 |         12143.4 |    3.07 |      0.33 | False    |
| Q19     | exasol            | clickhouse          |         331   |        119246   |  360.26 |      0    | False    |
| Q20     | exasol            | clickhouse          |        1118.2 |         22879.7 |   20.46 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |        2148.9 |         14486.2 |    6.74 |      0.15 | False    |
| Q22     | exasol            | clickhouse          |         585.9 |         12760   |   21.78 |      0.05 | False    |
| Q01     | exasol            | starrocks           |        3015.2 |        128456   |   42.6  |      0.02 | False    |
| Q02     | exasol            | starrocks           |         830.6 |          3472.3 |    4.18 |      0.24 | False    |
| Q03     | exasol            | starrocks           |        1981   |         26482.4 |   13.37 |      0.07 | False    |
| Q04     | exasol            | starrocks           |        1371   |         92326.7 |   67.34 |      0.01 | False    |
| Q05     | exasol            | starrocks           |        4103   |         31028.4 |    7.56 |      0.13 | False    |
| Q06     | exasol            | starrocks           |         383.5 |          4639.1 |   12.1  |      0.08 | False    |
| Q07     | exasol            | starrocks           |        3677.2 |         28576.2 |    7.77 |      0.13 | False    |
| Q08     | exasol            | starrocks           |        1855.9 |         29169.3 |   15.72 |      0.06 | False    |
| Q09     | exasol            | starrocks           |       12865.1 |         47584.7 |    3.7  |      0.27 | False    |
| Q10     | exasol            | starrocks           |        1311.5 |         39742.4 |   30.3  |      0.03 | False    |
| Q11     | exasol            | starrocks           |         688.1 |          2811.3 |    4.09 |      0.24 | False    |
| Q12     | exasol            | starrocks           |         828.4 |         18052.1 |   21.79 |      0.05 | False    |
| Q13     | exasol            | starrocks           |        3309.5 |         25663.1 |    7.75 |      0.13 | False    |
| Q14     | exasol            | starrocks           |        1092.1 |         12125.2 |   11.1  |      0.09 | False    |
| Q15     | exasol            | starrocks           |        1946.7 |         11464   |    5.89 |      0.17 | False    |
| Q16     | exasol            | starrocks           |        1673.7 |          7887.1 |    4.71 |      0.21 | False    |
| Q17     | exasol            | starrocks           |         423.3 |          7086.6 |   16.74 |      0.06 | False    |
| Q18     | exasol            | starrocks           |        3954.1 |         68539   |   17.33 |      0.06 | False    |
| Q19     | exasol            | starrocks           |         331   |          9366   |   28.3  |      0.04 | False    |
| Q20     | exasol            | starrocks           |        1118.2 |         10007.8 |    8.95 |      0.11 | False    |
| Q21     | exasol            | starrocks           |        2148.9 |        106027   |   49.34 |      0.02 | False    |
| Q22     | exasol            | starrocks           |         585.9 |          7156.9 |   12.22 |      0.08 | False    |
| Q01     | exasol            | trino               |        3015.2 |         39837   |   13.21 |      0.08 | False    |
| Q02     | exasol            | trino               |         830.6 |         61562.3 |   74.12 |      0.01 | False    |
| Q03     | exasol            | trino               |        1981   |         72412   |   36.55 |      0.03 | False    |
| Q04     | exasol            | trino               |        1371   |         35340.7 |   25.78 |      0.04 | False    |
| Q05     | exasol            | trino               |        4103   |         55925   |   13.63 |      0.07 | False    |
| Q06     | exasol            | trino               |         383.5 |         46966   |  122.47 |      0.01 | False    |
| Q07     | exasol            | trino               |        3677.2 |         62125.5 |   16.89 |      0.06 | False    |
| Q08     | exasol            | trino               |        1855.9 |         62587.7 |   33.72 |      0.03 | False    |
| Q09     | exasol            | trino               |       12865.1 |         69169.7 |    5.38 |      0.19 | False    |
| Q10     | exasol            | trino               |        1311.5 |        139737   |  106.55 |      0.01 | False    |
| Q11     | exasol            | trino               |         688.1 |         43602.9 |   63.37 |      0.02 | False    |
| Q12     | exasol            | trino               |         828.4 |         82292.4 |   99.34 |      0.01 | False    |
| Q13     | exasol            | trino               |        3309.5 |         23074.9 |    6.97 |      0.14 | False    |
| Q14     | exasol            | trino               |        1092.1 |         51375.9 |   47.04 |      0.02 | False    |
| Q15     | exasol            | trino               |        1946.7 |         52748   |   27.1  |      0.04 | False    |
| Q16     | exasol            | trino               |        1673.7 |         23802.8 |   14.22 |      0.07 | False    |
| Q17     | exasol            | trino               |         423.3 |         68428.8 |  161.66 |      0.01 | False    |
| Q18     | exasol            | trino               |        3954.1 |         82906.6 |   20.97 |      0.05 | False    |
| Q19     | exasol            | trino               |         331   |         49564.4 |  149.74 |      0.01 | False    |
| Q20     | exasol            | trino               |        1118.2 |         68265.1 |   61.05 |      0.02 | False    |
| Q21     | exasol            | trino               |        2148.9 |         88669.8 |   41.26 |      0.02 | False    |
| Q22     | exasol            | trino               |         585.9 |         15121.4 |   25.81 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 24445.5 | 14376.6 | 135.5 | 128493.7 |
| 1 | 28 | 29666.3 | 9480.5 | 413.6 | 223713.0 |
| 2 | 27 | 22358.6 | 12090.9 | 232.2 | 119600.7 |
| 3 | 27 | 30431.5 | 11062.9 | 333.4 | 244007.8 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 9480.5ms
- Slowest stream median: 14376.6ms
- Stream performance variation: 51.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 2847.5 | 1667.1 | 95.1 | 11787.1 |
| 1 | 28 | 2095.1 | 1350.7 | 312.6 | 10212.4 |
| 2 | 27 | 2855.1 | 1152.2 | 177.3 | 18410.4 |
| 3 | 27 | 2298.3 | 1290.9 | 118.0 | 15050.1 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1152.2ms
- Slowest stream median: 1667.1ms
- Stream performance variation: 44.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 35746.9 | 25695.2 | 3165.5 | 155103.3 |
| 1 | 28 | 30336.7 | 18108.2 | 2247.8 | 178014.5 |
| 2 | 27 | 32166.3 | 25588.1 | 2257.2 | 117972.6 |
| 3 | 27 | 36704.8 | 12125.2 | 2811.3 | 227538.6 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 12125.2ms
- Slowest stream median: 25695.2ms
- Stream performance variation: 111.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 57832.1 | 56635.7 | 14182.3 | 139737.0 |
| 1 | 28 | 59942.7 | 61249.3 | 12461.4 | 155400.7 |
| 2 | 27 | 61570.2 | 60997.0 | 23868.0 | 178986.3 |
| 3 | 27 | 54078.0 | 52748.0 | 21442.7 | 83822.5 |

**Performance Analysis for Trino:**
- Fastest stream median: 52748.0ms
- Slowest stream median: 61249.3ms
- Stream performance variation: 16.1% difference between fastest and slowest streams
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
- Median runtime: 12064.2ms
- Average runtime: 26731.5ms
- Fastest query: 135.5ms
- Slowest query: 244007.8ms

**exasol:**
- Median runtime: 1390.2ms
- Average runtime: 2523.0ms
- Fastest query: 95.1ms
- Slowest query: 18410.4ms

**starrocks:**
- Median runtime: 20885.9ms
- Average runtime: 33726.0ms
- Fastest query: 2247.8ms
- Slowest query: 227538.6ms

**trino:**
- Median runtime: 57924.5ms
- Average runtime: 58365.4ms
- Fastest query: 12461.4ms
- Slowest query: 178986.3ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_nodes_8-benchmark.zip`](ext_scalability_nodes_8-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 2 logical cores
- **Memory:** 7.6GB RAM
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
  - memory_limit: 6g
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
  - query_max_memory: 36GB
  - query_max_memory_per_node: 4GB

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