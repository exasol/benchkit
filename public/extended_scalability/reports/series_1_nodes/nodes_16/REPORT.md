# Extended Scalability - Node Scaling (16 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / m6id.large
**Date:** 2026-01-30 07:54:22

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **clickhouse**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 1086.4ms median runtime
- trino was 26.5x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 16-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 16 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (32 total vCPUs)
- **Memory per node:** 7.6GB RAM (121.6GB total RAM)
- **Node hostnames:**
  - exasol-node5: ip-10-0-1-176
  - exasol-node11: ip-10-0-1-39
  - exasol-node3: ip-10-0-1-71
  - exasol-node8: ip-10-0-1-220
  - exasol-node4: ip-10-0-1-253
  - exasol-node14: ip-10-0-1-88
  - exasol-node0: ip-10-0-1-63
  - exasol-node13: ip-10-0-1-118
  - exasol-node10: ip-10-0-1-19
  - exasol-node9: ip-10-0-1-112
  - exasol-node1: ip-10-0-1-203
  - exasol-node12: ip-10-0-1-23
  - exasol-node15: ip-10-0-1-80
  - exasol-node7: ip-10-0-1-196
  - exasol-node2: ip-10-0-1-50
  - exasol-node6: ip-10-0-1-191

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 16-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 16 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (32 total vCPUs)
- **Memory per node:** 7.6GB RAM (121.6GB total RAM)
- **Node hostnames:**
  - clickhouse-node7: ip-10-0-1-50
  - clickhouse-node3: ip-10-0-1-161
  - clickhouse-node6: ip-10-0-1-48
  - clickhouse-node9: ip-10-0-1-16
  - clickhouse-node15: ip-10-0-1-227
  - clickhouse-node12: ip-10-0-1-85
  - clickhouse-node10: ip-10-0-1-176
  - clickhouse-node1: ip-10-0-1-235
  - clickhouse-node5: ip-10-0-1-72
  - clickhouse-node14: ip-10-0-1-37
  - clickhouse-node4: ip-10-0-1-25
  - clickhouse-node13: ip-10-0-1-146
  - clickhouse-node8: ip-10-0-1-47
  - clickhouse-node11: ip-10-0-1-152
  - clickhouse-node2: ip-10-0-1-137
  - clickhouse-node0: ip-10-0-1-10

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 16-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 16 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (32 total vCPUs)
- **Memory per node:** 7.6GB RAM (121.6GB total RAM)
- **Node hostnames:**
  - trino-node3: ip-10-0-1-228
  - trino-node4: ip-10-0-1-35
  - trino-node2: ip-10-0-1-10
  - trino-node5: ip-10-0-1-88
  - trino-node1: ip-10-0-1-251
  - trino-node10: ip-10-0-1-249
  - trino-node15: ip-10-0-1-212
  - trino-node9: ip-10-0-1-168
  - trino-node0: ip-10-0-1-56
  - trino-node8: ip-10-0-1-99
  - trino-node7: ip-10-0-1-189
  - trino-node13: ip-10-0-1-161
  - trino-node11: ip-10-0-1-156
  - trino-node6: ip-10-0-1-177
  - trino-node14: ip-10-0-1-240
  - trino-node12: ip-10-0-1-229

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 16-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** m6id.large
- **Node Count:** 16 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (32 total vCPUs)
- **Memory per node:** 7.6GB RAM (121.6GB total RAM)
- **Node hostnames:**
  - starrocks-node0: ip-10-0-1-119
  - starrocks-node8: ip-10-0-1-24
  - starrocks-node15: ip-10-0-1-237
  - starrocks-node13: ip-10-0-1-254
  - starrocks-node6: ip-10-0-1-45
  - starrocks-node4: ip-10-0-1-18
  - starrocks-node12: ip-10-0-1-137
  - starrocks-node2: ip-10-0-1-36
  - starrocks-node3: ip-10-0-1-43
  - starrocks-node1: ip-10-0-1-247
  - starrocks-node11: ip-10-0-1-81
  - starrocks-node5: ip-10-0-1-7
  - starrocks-node10: ip-10-0-1-112
  - starrocks-node7: ip-10-0-1-181
  - starrocks-node9: ip-10-0-1-90
  - starrocks-node14: ip-10-0-1-147


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
# [All 16 Nodes] Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# [All 16 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 16 Nodes] Create 70GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 16 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 16 Nodes] Create raw partition for Exasol (39GB)
sudo parted /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 16 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 16 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 16 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 16 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 16 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 16 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol

# [All 16 Nodes] Add exasol user to sudo group
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
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;&#34;
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
# [All 16 Nodes] Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# [All 16 Nodes] Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# [All 16 Nodes] Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

# Execute wget command on remote system
wget -q https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

# Execute echo command on remote system
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS5814A7EF98B111929 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS5814A7EF98B111929

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS5814A7EF98B111929 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS5814A7EF98B111929 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create trino data directory
sudo mkdir -p /data/trino

```

**Prerequisites:**
```bash
# [All 16 Nodes] Add Eclipse Temurin (Adoptium) repository for Java 22
wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | sudo gpg --dearmor -o /usr/share/keyrings/adoptium.gpg 2&gt;/dev/null || true
echo &#34;deb [signed-by=/usr/share/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(lsb_release -sc) main&#34; | sudo tee /etc/apt/sources.list.d/adoptium.list

# [All 16 Nodes] Install Java 25 (required by Trino 479+)
sudo apt-get update &amp;&amp; sudo apt-get install -y temurin-25-jdk

# [All 16 Nodes] Install python symlink (required by Trino launcher)
sudo apt-get install -y python-is-python3

```

**User Setup:**
```bash
# [All 16 Nodes] Create Trino system user
sudo useradd -r -s /bin/false trino

```

**Installation:**
```bash
# [All 16 Nodes] Download Trino server version 479
wget https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

# [All 16 Nodes] Extract Trino server to /opt
sudo tar -xzf /tmp/trino-server.tar.gz -C /opt/

# [All 16 Nodes] Create symlink /opt/trino-server
sudo ln -sf /opt/trino-server-479 /opt/trino-server

# [All 16 Nodes] Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

# [All 16 Nodes] Create etc symlink for Trino launcher
sudo ln -sf /etc/trino /opt/trino-server/etc

```

**Configuration:**
```bash
# [All 16 Nodes] Configure Trino node properties
sudo tee /etc/trino/node.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
node.environment=production
node.id=0e142414-d3cf-469e-888a-64c662caa0bf
node.data-dir=/var/trino/data
EOF

# [All 16 Nodes] Configure JVM with 6G heap (80% of 7.6G total RAM)
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

# [All 16 Nodes] Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
discovery.uri=http://&lt;PRIVATE_IP&gt;:8080
query.max-memory=72GB
query.max-memory-per-node=4GB
EOF

# [All 16 Nodes] Configure Hive catalog with file metastore at local:///data/trino/hive-metastore
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

# [All 16 Nodes] Create Trino systemd service
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
# [All 16 Nodes] Reload systemd daemon
sudo systemctl daemon-reload

```

**Setup:**
```bash
# [All 16 Nodes] Execute sudo command on remote system
sudo mkdir -p /data/trino/hive-metastore

# [All 16 Nodes] Execute sudo command on remote system
sudo chown -R trino:trino /data/trino/hive-metastore

# [All 16 Nodes] Execute sudo command on remote system
sudo chmod -R 755 /data/trino/hive-metastore

# [All 16 Nodes] Execute sudo command on remote system
sudo mkdir -p /etc/trino/catalog

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# [All 16 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7BE79AC7DDE218CCA with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7BE79AC7DDE218CCA

# [All 16 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 16 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7BE79AC7DDE218CCA to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS7BE79AC7DDE218CCA /data

# [All 16 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 16 Nodes] Create starrocks data directory
sudo mkdir -p /data/starrocks

# [All 16 Nodes] Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# [All 16 Nodes] Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 16 Nodes] Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# [All 16 Nodes] Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 16 Nodes] Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 16 Nodes] Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# [All 16 Nodes] Configure StarRocks FE
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

# [All 16 Nodes] Configure StarRocks BE
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
# [All 16 Nodes] Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 16 Nodes] Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 16 Nodes] Execute sudo command on remote system
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 16 Nodes] Execute echo command on remote system
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

# [All 16 Nodes] Execute wget command on remote system
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 16 Nodes] Execute sudo command on remote system
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 16 Nodes] Execute sudo command on remote system
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

# [All 16 Nodes] Execute sudo command on remote system
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

# [All 16 Nodes] Execute sudo command on remote system
sudo chown -R $(whoami):$(whoami) /opt/starrocks

# [All 16 Nodes] Execute export command on remote system
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 16 Nodes] Execute export command on remote system
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
# [All 16 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS97E6B863AB5146FF6 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS97E6B863AB5146FF6

# [All 16 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 16 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS97E6B863AB5146FF6 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS97E6B863AB5146FF6 /data

# [All 16 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 16 Nodes] Create clickhouse data directory
sudo mkdir -p /data/clickhouse

# [All 16 Nodes] Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# [All 16 Nodes] Update package lists
sudo apt-get update

# [All 16 Nodes] Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# [All 16 Nodes] Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 16 Nodes] Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 16 Nodes] Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# [All 16 Nodes] Install ClickHouse server and client version &lt;PUBLIC_IP&gt;
sudo apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 16 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;6526989107&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# [All 16 Nodes] Configure ClickHouse user profile with password and query settings
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
# [All 16 Nodes] Start ClickHouse server service
sudo systemctl start clickhouse-server

# [All 16 Nodes] Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```

**Setup:**
```bash
# [All 16 Nodes] Execute sudo command on remote system
sudo apt-get update

# [All 16 Nodes] Execute sudo command on remote system
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

# [All 16 Nodes] Execute curl command on remote system
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 16 Nodes] Execute ARCH=$(dpkg command on remote system
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 16 Nodes] Execute DEBIAN_FRONTEND=noninteractive command on remote system
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

# [All 16 Nodes] Execute sudo command on remote system
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;6526989107&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

# [All 16 Nodes] Execute sudo command on remote system
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

# [All 16 Nodes] Execute sudo command on remote system
sudo systemctl start clickhouse-server

# [All 16 Nodes] Execute sudo command on remote system
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
            &lt;server&gt;
                &lt;id&gt;9&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;10&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;11&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;12&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;13&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;14&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;15&lt;/id&gt;
                &lt;hostname&gt;&lt;PRIVATE_IP&gt;&lt;/hostname&gt;
                &lt;port&gt;9234&lt;/port&gt;
            &lt;/server&gt;
            &lt;server&gt;
                &lt;id&gt;16&lt;/id&gt;
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
unzip ext_scalability_nodes_16-benchmark.zip
cd ext_scalability_nodes_16

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
| Q01     | clickhouse |   1485   |      5 |      2969.5 |    2785.7 |   2141.6 |    448.1 |   6066.7 |
| Q01     | exasol     |    701.5 |      5 |      1399   |    1654.6 |    629.7 |   1010.5 |   2365.8 |
| Q01     | starrocks  |  28922.3 |      5 |     93324.2 |   89538.4 |  32584.3 |  41538   | 130209   |
| Q01     | trino      |  10979.5 |      5 |     19276.1 |   20158.4 |  10751.1 |   6890   |  36724.7 |
| Q02     | clickhouse | 121370   |      5 |    329557   |  247454   | 230762   |    369.1 | 458251   |
| Q02     | exasol     |    241.6 |      5 |       908.7 |     981   |    250.5 |    724   |   1371.1 |
| Q02     | starrocks  |   1676.5 |      5 |      5576.9 |    5223.7 |   1194.7 |   3178.2 |   6217.1 |
| Q02     | trino      |   9834.2 |      5 |     31848.4 |   34639.6 |  12195.3 |  20179.6 |  51289   |
| Q03     | clickhouse |     79.8 |      5 |     46453.1 |   63456.4 |  26452.9 |  40383   |  95759.3 |
| Q03     | exasol     |    457.2 |      5 |       745   |    1551.3 |   1633.9 |    445.1 |   4298.5 |
| Q03     | starrocks  |  13159.5 |      5 |     42771.4 |   41197.9 |  21289.6 |  10537.5 |  63069.9 |
| Q03     | trino      |  15375.6 |      5 |     36580   |   37422.4 |   9566.4 |  27116.8 |  51491.3 |
| Q04     | clickhouse |     25.8 |      5 |      5865.8 |    8558   |  11258.6 |     10.6 |  27443.8 |
| Q04     | exasol     |    161   |      5 |      1497.6 |    1769.6 |   1472.9 |    199.8 |   3959   |
| Q04     | starrocks  |   9556.9 |      5 |    180540   |  182931   |  84545.2 |  56998.7 | 288260   |
| Q04     | trino      |   7796.7 |      5 |     32192.2 |   27787.2 |   9974.3 |  13449.1 |  37734.4 |
| Q05     | clickhouse |     23.4 |      5 |     89365.9 |   76860.4 |  29920.9 |  23391.9 |  92381.5 |
| Q05     | exasol     |    636.5 |      5 |      2047.3 |    2354.2 |    950.3 |   1652.5 |   3965   |
| Q05     | starrocks  |  12695.3 |      5 |     31086.3 |   30126.3 |   5070.3 |  23217.6 |  36707.4 |
| Q05     | trino      |  10585.5 |      5 |     31896.6 |   33691   |   7877.6 |  24591.6 |  46272.4 |
| Q06     | clickhouse |     27.4 |      5 |       234.5 |     222.3 |    138.5 |     34.3 |    418.1 |
| Q06     | exasol     |     66.1 |      5 |       330.7 |     250.5 |    141.3 |     48.6 |    367   |
| Q06     | starrocks  |   9586.1 |      5 |      6325.3 |    8272.2 |   4479.8 |   4345.9 |  14374.9 |
| Q06     | trino      |   8645.7 |      5 |     28249.4 |   28433.6 |   4425.4 |  22849.2 |  35033   |
| Q07     | clickhouse |      1.9 |      5 |      9101.4 |    8930.1 |   2686.7 |   4983.4 |  11809.5 |
| Q07     | exasol     |    879.2 |      5 |      2301.5 |    2149   |    792.9 |    871.9 |   2940.4 |
| Q07     | starrocks  |  14260   |      5 |     27499.6 |   25228.3 |   5810.3 |  14912.6 |  28732.9 |
| Q07     | trino      |  12061.5 |      5 |     28954.8 |   30196.6 |   5116.7 |  26145.2 |  39026.1 |
| Q08     | clickhouse |      1.7 |      5 |      9739.1 |   10280.9 |   1865.4 |   8153.3 |  13203.3 |
| Q08     | exasol     |    432.5 |      5 |      1484.7 |    1452.2 |    298.5 |    976.8 |   1736.5 |
| Q08     | starrocks  |  17412.9 |      5 |     26885.7 |   28178.9 |   3578.4 |  25370.9 |  34215.3 |
| Q08     | trino      |  13604.3 |      5 |     38152.6 |   35375.4 |  10965.4 |  23757   |  46282   |
| Q09     | clickhouse |      1.3 |      5 |      9950   |    9466.8 |   5440.8 |   1113.3 |  14720.7 |
| Q09     | exasol     |   2603.7 |      5 |     11668.6 |   10537.7 |   3193.8 |   6533   |  14486.5 |
| Q09     | starrocks  |  23054.6 |      5 |     54534.4 |   46461.6 |  21026   |  10147   |  62800.3 |
| Q09     | trino      |  13437.9 |      5 |     29696.4 |   32754.7 |   8426.6 |  24589.9 |  44231.1 |
| Q10     | clickhouse |     19.7 |      5 |     88969.5 |   54905.6 |  49651.3 |    257.9 |  92371.5 |
| Q10     | exasol     |    436.8 |      5 |      1219.9 |    1554.7 |    717.8 |   1081.3 |   2783   |
| Q10     | starrocks  |  17247.3 |      5 |     35246.4 |   25986.3 |  17404.8 |   3296.5 |  41668.8 |
| Q10     | trino      |  14583.4 |      5 |     41708.7 |   39366.1 |  13136.1 |  20572.4 |  54847.1 |
| Q11     | clickhouse |      6.3 |      5 |      4677.4 |    3583   |   3272.7 |     15.1 |   7295.9 |
| Q11     | exasol     |    823.8 |      5 |       702.5 |     639.7 |    280.8 |    265.8 |    952.7 |
| Q11     | starrocks  |   1177.1 |      5 |      4699.5 |    6058   |   3569.9 |   2891.5 |  11109.8 |
| Q11     | trino      |   4239.3 |      5 |     21514   |   19704.5 |   4163   |  13302.9 |  23627   |
| Q12     | clickhouse |     16.8 |      5 |      4359.5 |    5878.9 |   4900.5 |    263.5 |  12186.5 |
| Q12     | exasol     |    169.4 |      5 |       857.1 |     835.7 |    498.6 |    334.7 |   1621.7 |
| Q12     | starrocks  |  11165.6 |      5 |     14283.2 |   17015.6 |   4541.8 |  13287.2 |  23849.1 |
| Q12     | trino      |  12821.9 |      5 |     32642.4 |   40100.9 |  11948.7 |  30934.9 |  58648.6 |
| Q13     | clickhouse |      1.6 |      5 |      1897.7 |    3805.1 |   4350.4 |    215   |  10200.6 |
| Q13     | exasol     |    492.6 |      5 |      2063.1 |    4144.7 |   3657.4 |    473   |   8401.3 |
| Q13     | starrocks  |  12410.8 |      5 |     41439.8 |   38055.5 |  12133.1 |  21465.5 |  52514.3 |
| Q13     | trino      |   4464.9 |      5 |     13520.6 |   14520.8 |   3207.8 |  11781.9 |  20058   |
| Q14     | clickhouse |     82.4 |      5 |     22814   |   18464.4 |  10188.9 |    247   |  23404.6 |
| Q14     | exasol     |    181.7 |      5 |       806.5 |     826.1 |    299.8 |    504.9 |   1290.8 |
| Q14     | starrocks  |   5583.3 |      5 |     20392.1 |   17697.9 |   6186.6 |  10672.6 |  23667.7 |
| Q14     | trino      |   7312.4 |      5 |     22910.4 |   23250   |   7457.5 |  12410.4 |  33353.3 |
| Q15     | clickhouse |      5   |      5 |      4034.1 |    3937.8 |    796.5 |   2968.5 |   5049.9 |
| Q15     | exasol     |    231.8 |      5 |      1443.1 |    1630.8 |    838.8 |    845.8 |   2668.9 |
| Q15     | starrocks  |   4371.8 |      5 |     10965.8 |   11553.2 |   4062.8 |   6790   |  17554.4 |
| Q15     | trino      |  12946.1 |      5 |     27805   |   32097.7 |   9748.9 |  23978.2 |  48737.6 |
| Q16     | clickhouse |      5.8 |      5 |      9279.7 |   16643.6 |  15582.4 |    168   |  39230   |
| Q16     | exasol     |    440.3 |      5 |      1614.2 |    1794.8 |    588.1 |   1229.5 |   2608.9 |
| Q16     | starrocks  |   2646.6 |      5 |      9401.5 |   10396.2 |   2705.8 |   7168.3 |  13834.7 |
| Q16     | trino      |   5231.6 |      5 |     14349   |   16912.5 |   8326   |  11119.9 |  31425.8 |
| Q17     | clickhouse |      4.6 |      5 |      1014.3 |    1333.3 |    907.1 |    586.4 |   2908.8 |
| Q17     | exasol     |    116.1 |      5 |       280.3 |     318.9 |     75.8 |    240.2 |    407.3 |
| Q17     | starrocks  |   5310.6 |      5 |     13330.6 |   14583.9 |   4364.8 |  10000.1 |  20422.7 |
| Q17     | trino      |  13818.4 |      5 |     35099.7 |   33527.4 |   7974.7 |  22471.9 |  41716.1 |
| Q18     | clickhouse |      3.2 |      5 |     13312.6 |   13561.2 |   7053.9 |   3920.5 |  23251.7 |
| Q18     | exasol     |    316.4 |      5 |      1850.4 |    2023.2 |   1574.8 |    541.5 |   4489.6 |
| Q18     | starrocks  |  16704.5 |      5 |     59338.1 |   60055   |   7879.3 |  47911.4 |  68720.6 |
| Q18     | trino      |  11259.8 |      5 |     39373.4 |   36300.1 |   8835.4 |  22077.3 |  44157.5 |
| Q19     | clickhouse |     14.8 |      5 |     71560.9 |  100606   | 108303   |     50.9 | 215496   |
| Q19     | exasol     |     95.2 |      5 |       347.8 |     437.5 |    315.5 |    149.2 |    943.4 |
| Q19     | starrocks  |   5779.3 |      5 |     16715.8 |   13407.2 |   5698.9 |   6959.1 |  18935.5 |
| Q19     | trino      |   9357.8 |      5 |     27358.6 |   27967.6 |   5990.8 |  22088.2 |  34481.8 |
| Q20     | clickhouse |     12.3 |      5 |     24501.2 |   20530.6 |  16739.4 |    186.5 |  42703.6 |
| Q20     | exasol     |    336.1 |      5 |      1441.1 |    1415.7 |    317.7 |    959.5 |   1850   |
| Q20     | starrocks  |   5642.2 |      5 |     13134.4 |   12904.3 |   2130.1 |   9386.2 |  14819.8 |
| Q20     | trino      |  11046   |      5 |     27281.4 |   29831.3 |   8375.3 |  20260.2 |  41026.7 |
| Q21     | clickhouse |      2.3 |      5 |      8194.6 |    5677.6 |   5104   |     12   |  10344.8 |
| Q21     | exasol     |   5140.1 |      5 |       960.3 |    1613.1 |   1334.4 |    763.2 |   3921.1 |
| Q21     | starrocks  |  33198.7 |      5 |    111601   |  100555   |  27723.2 |  52584.5 | 118930   |
| Q21     | trino      |  18921.9 |      5 |     49431.6 |   49532.3 |   7262.1 |  40476.8 |  59625.1 |
| Q22     | clickhouse |     12.8 |      5 |     13470.7 |   12503.2 |   3230.3 |   6885.4 |  15211.3 |
| Q22     | exasol     |    100   |      5 |       346.1 |     331.9 |    146.1 |     98.9 |    496   |
| Q22     | starrocks  |   2272.7 |      5 |      4829.1 |    6689   |   4150.5 |   2938.8 |  13368.8 |
| Q22     | trino      |   3230.1 |      5 |     13550.6 |   14711.1 |   4728.5 |   9418   |  20209.4 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        1399   |          2969.5 |    2.12 |      0.47 | False    |
| Q02     | exasol            | clickhouse          |         908.7 |        329557   |  362.67 |      0    | False    |
| Q03     | exasol            | clickhouse          |         745   |         46453.1 |   62.35 |      0.02 | False    |
| Q04     | exasol            | clickhouse          |        1497.6 |          5865.8 |    3.92 |      0.26 | False    |
| Q05     | exasol            | clickhouse          |        2047.3 |         89365.9 |   43.65 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |         330.7 |           234.5 |    0.71 |      1.41 | True     |
| Q07     | exasol            | clickhouse          |        2301.5 |          9101.4 |    3.95 |      0.25 | False    |
| Q08     | exasol            | clickhouse          |        1484.7 |          9739.1 |    6.56 |      0.15 | False    |
| Q09     | exasol            | clickhouse          |       11668.6 |          9950   |    0.85 |      1.17 | True     |
| Q10     | exasol            | clickhouse          |        1219.9 |         88969.5 |   72.93 |      0.01 | False    |
| Q11     | exasol            | clickhouse          |         702.5 |          4677.4 |    6.66 |      0.15 | False    |
| Q12     | exasol            | clickhouse          |         857.1 |          4359.5 |    5.09 |      0.2  | False    |
| Q13     | exasol            | clickhouse          |        2063.1 |          1897.7 |    0.92 |      1.09 | True     |
| Q14     | exasol            | clickhouse          |         806.5 |         22814   |   28.29 |      0.04 | False    |
| Q15     | exasol            | clickhouse          |        1443.1 |          4034.1 |    2.8  |      0.36 | False    |
| Q16     | exasol            | clickhouse          |        1614.2 |          9279.7 |    5.75 |      0.17 | False    |
| Q17     | exasol            | clickhouse          |         280.3 |          1014.3 |    3.62 |      0.28 | False    |
| Q18     | exasol            | clickhouse          |        1850.4 |         13312.6 |    7.19 |      0.14 | False    |
| Q19     | exasol            | clickhouse          |         347.8 |         71560.9 |  205.75 |      0    | False    |
| Q20     | exasol            | clickhouse          |        1441.1 |         24501.2 |   17    |      0.06 | False    |
| Q21     | exasol            | clickhouse          |         960.3 |          8194.6 |    8.53 |      0.12 | False    |
| Q22     | exasol            | clickhouse          |         346.1 |         13470.7 |   38.92 |      0.03 | False    |
| Q01     | exasol            | starrocks           |        1399   |         93324.2 |   66.71 |      0.01 | False    |
| Q02     | exasol            | starrocks           |         908.7 |          5576.9 |    6.14 |      0.16 | False    |
| Q03     | exasol            | starrocks           |         745   |         42771.4 |   57.41 |      0.02 | False    |
| Q04     | exasol            | starrocks           |        1497.6 |        180540   |  120.55 |      0.01 | False    |
| Q05     | exasol            | starrocks           |        2047.3 |         31086.3 |   15.18 |      0.07 | False    |
| Q06     | exasol            | starrocks           |         330.7 |          6325.3 |   19.13 |      0.05 | False    |
| Q07     | exasol            | starrocks           |        2301.5 |         27499.6 |   11.95 |      0.08 | False    |
| Q08     | exasol            | starrocks           |        1484.7 |         26885.7 |   18.11 |      0.06 | False    |
| Q09     | exasol            | starrocks           |       11668.6 |         54534.4 |    4.67 |      0.21 | False    |
| Q10     | exasol            | starrocks           |        1219.9 |         35246.4 |   28.89 |      0.03 | False    |
| Q11     | exasol            | starrocks           |         702.5 |          4699.5 |    6.69 |      0.15 | False    |
| Q12     | exasol            | starrocks           |         857.1 |         14283.2 |   16.66 |      0.06 | False    |
| Q13     | exasol            | starrocks           |        2063.1 |         41439.8 |   20.09 |      0.05 | False    |
| Q14     | exasol            | starrocks           |         806.5 |         20392.1 |   25.28 |      0.04 | False    |
| Q15     | exasol            | starrocks           |        1443.1 |         10965.8 |    7.6  |      0.13 | False    |
| Q16     | exasol            | starrocks           |        1614.2 |          9401.5 |    5.82 |      0.17 | False    |
| Q17     | exasol            | starrocks           |         280.3 |         13330.6 |   47.56 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        1850.4 |         59338.1 |   32.07 |      0.03 | False    |
| Q19     | exasol            | starrocks           |         347.8 |         16715.8 |   48.06 |      0.02 | False    |
| Q20     | exasol            | starrocks           |        1441.1 |         13134.4 |    9.11 |      0.11 | False    |
| Q21     | exasol            | starrocks           |         960.3 |        111601   |  116.21 |      0.01 | False    |
| Q22     | exasol            | starrocks           |         346.1 |          4829.1 |   13.95 |      0.07 | False    |
| Q01     | exasol            | trino               |        1399   |         19276.1 |   13.78 |      0.07 | False    |
| Q02     | exasol            | trino               |         908.7 |         31848.4 |   35.05 |      0.03 | False    |
| Q03     | exasol            | trino               |         745   |         36580   |   49.1  |      0.02 | False    |
| Q04     | exasol            | trino               |        1497.6 |         32192.2 |   21.5  |      0.05 | False    |
| Q05     | exasol            | trino               |        2047.3 |         31896.6 |   15.58 |      0.06 | False    |
| Q06     | exasol            | trino               |         330.7 |         28249.4 |   85.42 |      0.01 | False    |
| Q07     | exasol            | trino               |        2301.5 |         28954.8 |   12.58 |      0.08 | False    |
| Q08     | exasol            | trino               |        1484.7 |         38152.6 |   25.7  |      0.04 | False    |
| Q09     | exasol            | trino               |       11668.6 |         29696.4 |    2.54 |      0.39 | False    |
| Q10     | exasol            | trino               |        1219.9 |         41708.7 |   34.19 |      0.03 | False    |
| Q11     | exasol            | trino               |         702.5 |         21514   |   30.62 |      0.03 | False    |
| Q12     | exasol            | trino               |         857.1 |         32642.4 |   38.08 |      0.03 | False    |
| Q13     | exasol            | trino               |        2063.1 |         13520.6 |    6.55 |      0.15 | False    |
| Q14     | exasol            | trino               |         806.5 |         22910.4 |   28.41 |      0.04 | False    |
| Q15     | exasol            | trino               |        1443.1 |         27805   |   19.27 |      0.05 | False    |
| Q16     | exasol            | trino               |        1614.2 |         14349   |    8.89 |      0.11 | False    |
| Q17     | exasol            | trino               |         280.3 |         35099.7 |  125.22 |      0.01 | False    |
| Q18     | exasol            | trino               |        1850.4 |         39373.4 |   21.28 |      0.05 | False    |
| Q19     | exasol            | trino               |         347.8 |         27358.6 |   78.66 |      0.01 | False    |
| Q20     | exasol            | trino               |        1441.1 |         27281.4 |   18.93 |      0.05 | False    |
| Q21     | exasol            | trino               |         960.3 |         49431.6 |   51.48 |      0.02 | False    |
| Q22     | exasol            | trino               |         346.1 |         13550.6 |   39.15 |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 32984.3 | 9873.4 | 168.0 | 214392.5 |
| 1 | 28 | 26711.4 | 6966.0 | 217.4 | 458250.6 |
| 2 | 27 | 27689.8 | 13203.3 | 10.6 | 215496.3 |
| 3 | 27 | 38078.5 | 8072.7 | 175.6 | 447849.1 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 6966.0ms
- Slowest stream median: 13203.3ms
- Stream performance variation: 89.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1993.8 | 1045.9 | 48.6 | 8401.3 |
| 1 | 28 | 1672.4 | 934.1 | 240.2 | 14486.5 |
| 2 | 27 | 1938.9 | 1229.5 | 149.2 | 11668.6 |
| 3 | 27 | 1715.9 | 1290.8 | 280.3 | 11912.3 |

**Performance Analysis for Exasol:**
- Fastest stream median: 934.1ms
- Slowest stream median: 1290.8ms
- Stream performance variation: 38.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 36524.5 | 28116.2 | 4829.1 | 118930.1 |
| 1 | 28 | 34008.8 | 19050.2 | 2938.8 | 220583.7 |
| 2 | 27 | 36270.9 | 16901.7 | 3201.7 | 168270.6 |
| 3 | 27 | 37271.3 | 14334.8 | 2891.5 | 288260.1 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 14334.8ms
- Slowest stream median: 28116.2ms
- Stream performance variation: 96.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 29502.4 | 28602.1 | 11119.9 | 54847.1 |
| 1 | 28 | 29280.2 | 27957.3 | 9418.0 | 51289.0 |
| 2 | 27 | 30322.0 | 27358.6 | 13449.1 | 59625.1 |
| 3 | 27 | 30622.2 | 32598.2 | 6890.0 | 58648.6 |

**Performance Analysis for Trino:**
- Fastest stream median: 27358.6ms
- Slowest stream median: 32598.2ms
- Stream performance variation: 19.2% difference between fastest and slowest streams
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
- Median runtime: 8630.0ms
- Average runtime: 31338.4ms
- Fastest query: 10.6ms
- Slowest query: 458250.6ms

**exasol:**
- Median runtime: 1086.4ms
- Average runtime: 1830.3ms
- Fastest query: 48.6ms
- Slowest query: 14486.5ms

**starrocks:**
- Median runtime: 19951.3ms
- Average runtime: 36005.2ms
- Fastest query: 2891.5ms
- Slowest query: 288260.1ms

**trino:**
- Median runtime: 28785.4ms
- Average runtime: 29921.9ms
- Fastest query: 6890.0ms
- Slowest query: 59625.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_nodes_16-benchmark.zip`](ext_scalability_nodes_16-benchmark.zip)

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
  - query_max_memory: 72GB
  - query_max_memory_per_node: 4GB

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 64
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