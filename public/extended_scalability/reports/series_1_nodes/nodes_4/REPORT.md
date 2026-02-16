# Extended Scalability - Node Scaling (4 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-29 21:19:22

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **clickhouse**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 2297.1ms median runtime
- trino was 61.6x slower- Tested 440 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 4-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **Node Count:** 4 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (8 total vCPUs)
- **Memory per node:** 15.3GB RAM (61.2GB total RAM)
- **Node hostnames:**
  - exasol-node3: ip-10-0-1-182
  - exasol-node0: ip-10-0-1-219
  - exasol-node1: ip-10-0-1-176
  - exasol-node2: ip-10-0-1-235

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 4-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **Node Count:** 4 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (8 total vCPUs)
- **Memory per node:** 15.3GB RAM (61.2GB total RAM)
- **Node hostnames:**
  - clickhouse-node3: ip-10-0-1-200
  - clickhouse-node1: ip-10-0-1-130
  - clickhouse-node2: ip-10-0-1-46
  - clickhouse-node0: ip-10-0-1-58

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 4-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **Node Count:** 4 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (8 total vCPUs)
- **Memory per node:** 15.3GB RAM (61.2GB total RAM)
- **Node hostnames:**
  - trino-node3: ip-10-0-1-222
  - trino-node2: ip-10-0-1-194
  - trino-node1: ip-10-0-1-183
  - trino-node0: ip-10-0-1-204

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 4-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **Node Count:** 4 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 2 vCPUs (8 total vCPUs)
- **Memory per node:** 15.3GB RAM (61.2GB total RAM)
- **Node hostnames:**
  - starrocks-node0: ip-10-0-1-176
  - starrocks-node2: ip-10-0-1-103
  - starrocks-node3: ip-10-0-1-243
  - starrocks-node1: ip-10-0-1-248


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
# [All 4 Nodes] Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# [All 4 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 4 Nodes] Create 70GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 4 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# [All 4 Nodes] Create raw partition for Exasol (39GB)
sudo parted /dev/nvme1n1 mkpart primary 70GiB 100%

# [All 4 Nodes] Execute sudo command on remote system
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
sudo useradd -m -s /bin/bash exasol

# [All 4 Nodes] Add exasol user to sudo group
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
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;&#34;
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
# [All 4 Nodes] Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# [All 4 Nodes] Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# [All 4 Nodes] Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

# Execute wget command on remote system
wget -q https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

# Execute echo command on remote system
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS676B0F0FAC64255CF with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS676B0F0FAC64255CF

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS676B0F0FAC64255CF to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS676B0F0FAC64255CF /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create trino data directory
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
sudo useradd -r -s /bin/false trino

```

**Installation:**
```bash
# [All 4 Nodes] Download Trino server version 479
wget https://github.com/trinodb/trino/releases/download/479/trino-server-479.tar.gz -O /tmp/trino-server.tar.gz

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
node.id=1d077808-b780-4443-b22d-7ef0b7f23851
node.data-dir=/var/trino/data
EOF

# [All 4 Nodes] Configure JVM with 12G heap (80% of 15.3G total RAM)
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

# [All 4 Nodes] Configure Trino as coordinator
sudo tee /etc/trino/config.properties &gt; /dev/null &lt;&lt; &#39;EOF&#39;
coordinator=true
node-scheduler.include-coordinator=false
http-server.http.port=8080
discovery.uri=http://&lt;PRIVATE_IP&gt;:8080
query.max-memory=36GB
query.max-memory-per-node=8GB
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS48499D97386784DD2 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS48499D97386784DD2

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS48499D97386784DD2 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS48499D97386784DD2 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create starrocks data directory
sudo mkdir -p /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
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
# [All 4 Nodes] Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

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
# Performance tuning
mem_limit = 80%
# Parallel execution
parallel_fragment_exec_instance_num = 16

EOF

```

**Service Management:**
```bash
# [All 4 Nodes] Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 4 Nodes] Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 4 Nodes] Execute sudo command on remote system
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 4 Nodes] Execute echo command on remote system
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

# [All 4 Nodes] Execute wget command on remote system
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 4 Nodes] Execute sudo command on remote system
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 4 Nodes] Execute sudo command on remote system
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

# [All 4 Nodes] Execute sudo command on remote system
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

# [All 4 Nodes] Execute sudo command on remote system
sudo chown -R $(whoami):$(whoami) /opt/starrocks

# [All 4 Nodes] Execute export command on remote system
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 4 Nodes] Execute export command on remote system
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
# [All 4 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2742C00627BB808BD with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2742C00627BB808BD

# [All 4 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 4 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2742C00627BB808BD to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2742C00627BB808BD /data

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
sudo apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

```

**Configuration:**
```bash
# [All 4 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;13175793254&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
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
            &lt;max_threads&gt;2&lt;/max_threads&gt;
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

**Setup:**
```bash
# [All 4 Nodes] Execute sudo command on remote system
sudo apt-get update

# [All 4 Nodes] Execute sudo command on remote system
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

# [All 4 Nodes] Execute curl command on remote system
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# [All 4 Nodes] Execute ARCH=$(dpkg command on remote system
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# [All 4 Nodes] Execute DEBIAN_FRONTEND=noninteractive command on remote system
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=25.10.2.65 clickhouse-server=25.10.2.65 clickhouse-client=25.10.2.65

# [All 4 Nodes] Execute sudo command on remote system
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;13175793254&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;14&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;2&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

# [All 4 Nodes] Execute sudo command on remote system
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

# [All 4 Nodes] Execute sudo command on remote system
sudo systemctl start clickhouse-server

# [All 4 Nodes] Execute sudo command on remote system
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
- Memory limit: `12g`
- Max threads: `2`
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
unzip ext_scalability_nodes_4-benchmark.zip
cd ext_scalability_nodes_4

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
| Q01     | clickhouse |   5107.6 |      5 |     18066.6 |   17056.8 |   5625.9 |   8251.1 |  23153.3 |
| Q01     | exasol     |   1587.1 |      5 |      5500   |    6435.8 |   2094.8 |   4740.7 |  10022.3 |
| Q01     | starrocks  |  27502.6 |      5 |    100583   |   98149.9 |  22780.6 |  67866   | 127026   |
| Q01     | trino      |  40220   |      5 |    116763   |  121186   |  16276   | 100088   | 141178   |
| Q02     | clickhouse |  38326   |      5 |    125479   |  124888   |  12417.1 | 104271   | 135470   |
| Q02     | exasol     |    137.8 |      5 |       613.2 |    1877   |   3047.1 |    314   |   7322.7 |
| Q02     | starrocks  |   1462.4 |      5 |      3926.7 |    4298.1 |    939.3 |   3152.9 |   5354.3 |
| Q02     | trino      |  23457.7 |      5 |     99396.2 |   97074.3 |   6495.9 |  88325.8 | 104231   |
| Q03     | clickhouse |  11049.5 |      5 |     27337.1 |   27458.6 |   5246.5 |  21354   |  34184.7 |
| Q03     | exasol     |   1338.3 |      5 |      2689.2 |    3005.9 |    952.1 |   2278.1 |   4669.3 |
| Q03     | starrocks  |  10966.4 |      5 |     10605.2 |   23321   |  17809.7 |  10129.8 |  45060.6 |
| Q03     | trino      |  62038.6 |      5 |    189322   |  186012   |  65372.7 |  88423.9 | 259343   |
| Q04     | clickhouse |  19853.6 |      5 |     47225.3 |   53555.6 |  15463.4 |  39076.6 |  74845.6 |
| Q04     | exasol     |    375.3 |      5 |      1400.4 |    1354   |    712.1 |    380   |   2316.2 |
| Q04     | starrocks  |   8419   |      5 |    160231   |  147162   |  39754.5 |  99071.3 | 195553   |
| Q04     | trino      |  30015.8 |      5 |    101817   |   94241.8 |  27186.9 |  51275.8 | 123124   |
| Q05     | clickhouse |  11029.8 |      5 |     26649.5 |   20863.9 |  19372.1 |    171.2 |  38717   |
| Q05     | exasol     |   1372.1 |      5 |      3908.3 |    4192.2 |   1702.3 |   2185.8 |   6406.3 |
| Q05     | starrocks  |  10404.6 |      5 |     24787   |   24242.5 |   2802.7 |  21275.3 |  27835.4 |
| Q05     | trino      |  36269.8 |      5 |    144164   |  156069   |  29775   | 124097   | 199838   |
| Q06     | clickhouse |    415.6 |      5 |      1524.8 |    1618.1 |   1026.5 |    611.3 |   3293.1 |
| Q06     | exasol     |     84   |      5 |       351.1 |     605   |    647.3 |    266.7 |   1759.7 |
| Q06     | starrocks  |   3954.8 |      5 |      4495.3 |    5706.3 |   1927.4 |   4234.7 |   8385.7 |
| Q06     | trino      |  37794.9 |      5 |    151612   |  153062   |  14014.2 | 133506   | 169784   |
| Q07     | clickhouse |   5891   |      5 |     11578.4 |   12314.6 |   4660.8 |   6455.6 |  19175.4 |
| Q07     | exasol     |   1850.8 |      5 |      5472.2 |    6875.9 |   3865.6 |   4662.2 |  13741.9 |
| Q07     | starrocks  |   9996.3 |      5 |     24361.1 |   23018.5 |   8429.4 |   9247.5 |  30154.4 |
| Q07     | trino      |  42358.8 |      5 |    156746   |  140276   |  28207   |  99353.1 | 162198   |
| Q08     | clickhouse |   6320.9 |      5 |     25783.4 |   23500.3 |   4837   |  15168.7 |  26784   |
| Q08     | exasol     |    791.9 |      5 |      2220.5 |    2119.8 |    736.3 |    884   |   2783.1 |
| Q08     | starrocks  |  10270.6 |      5 |     29318.7 |   28209.2 |   3738.2 |  21750.3 |  31439.1 |
| Q08     | trino      |  43691.1 |      5 |    161536   |  153874   |  15431.7 | 133974   | 170589   |
| Q09     | clickhouse |   5444.4 |      5 |     19420.3 |   18237.7 |   8440.3 |   5303.9 |  27352   |
| Q09     | exasol     |   5537.6 |      5 |     16034.9 |   16852.4 |   5539.5 |  11323.3 |  23128.6 |
| Q09     | starrocks  |  16686.4 |      5 |     36489   |   40331.2 |   6617.6 |  35912.4 |  51503.4 |
| Q09     | trino      |  49711.1 |      5 |    133416   |  138281   |  20231.3 | 113567   | 162583   |
| Q10     | clickhouse |  10515.3 |      5 |     37538.2 |   38038.2 |   5065.3 |  30791.7 |  44619.9 |
| Q10     | exasol     |   1888.1 |      5 |      2746.6 |    3665.8 |   1614.1 |   2357.5 |   5912.9 |
| Q10     | starrocks  |  15765.1 |      5 |     40515.3 |   40448.3 |   4415.4 |  33665.2 |  44930.8 |
| Q10     | trino      |  64806.7 |      5 |    216701   |  218321   |  22744.2 | 198438   | 254560   |
| Q11     | clickhouse |   1706.1 |      5 |      6114   |    6299.9 |   1106   |   4755.9 |   7784.8 |
| Q11     | exasol     |   2312.3 |      5 |      1000   |    1181.3 |    528.6 |    665.5 |   1811.7 |
| Q11     | starrocks  |   1079   |      5 |      2135   |    2212.4 |    335.7 |   1835.1 |   2718.8 |
| Q11     | trino      |  13976.6 |      5 |     50084.7 |   54062.2 |   9784.6 |  47696.4 |  71044   |
| Q12     | clickhouse |   6342.6 |      5 |     16940.1 |   15966.6 |  12442.2 |    274   |  29219   |
| Q12     | exasol     |    339.3 |      5 |       940.2 |    1088.1 |    244   |    879.3 |   1389.7 |
| Q12     | starrocks  |   6929.4 |      5 |     18652.6 |   18704.8 |   3728.8 |  13660.4 |  23387.2 |
| Q12     | trino      |  53974   |      5 |    207880   |  205352   |  11578.8 | 185418   | 213530   |
| Q13     | clickhouse |  23242.8 |      5 |     74151.6 |   68847.4 |  36957.4 |   7789   | 102067   |
| Q13     | exasol     |   1485.2 |      5 |      6422   |    9782   |   8577.2 |   3115.5 |  24571.5 |
| Q13     | starrocks  |  11512.3 |      5 |     25027.4 |   29174.1 |  16553.9 |  11746   |  47835.1 |
| Q13     | trino      |  24564.3 |      5 |     66469.7 |   68036.7 |  10730.8 |  56310.1 |  82419.5 |
| Q14     | clickhouse |   2515.7 |      5 |      9053.9 |    9188.7 |   3334.7 |   5126   |  14399.8 |
| Q14     | exasol     |    479.9 |      5 |      1879.4 |    2496.8 |   1403.6 |   1592.1 |   4942.6 |
| Q14     | starrocks  |   4990.1 |      5 |      9276.7 |    8696.6 |   1595   |   6223.4 |  10416.9 |
| Q14     | trino      |  40360.1 |      5 |    125295   |  122424   |  20155.4 |  95713.4 | 145497   |
| Q15     | clickhouse |    609.2 |      5 |      2623.1 |    2525.6 |    702.3 |   1809.1 |   3365.3 |
| Q15     | exasol     |    422.2 |      5 |      1976.5 |    2515.2 |   1040.4 |   1631.8 |   3814.1 |
| Q15     | starrocks  |   4198.3 |      5 |      9991.7 |    8316.9 |   3143.6 |   4907.3 |  11577.4 |
| Q15     | trino      |  56281.9 |      5 |    152137   |  144881   |  11634.5 | 128007   | 154070   |
| Q16     | clickhouse |   5487.8 |      5 |     22714.9 |   22594   |   3499.4 |  17010.5 |  25584.2 |
| Q16     | exasol     |    649.4 |      5 |      1744.9 |    2602.6 |   1484.2 |   1419.2 |   4927.4 |
| Q16     | starrocks  |   2606.5 |      5 |      6000.1 |    6563.1 |    929.8 |   5826.5 |   7842.9 |
| Q16     | trino      |   9052.4 |      5 |     39022.1 |   45700.3 |  13628   |  34571.4 |  68259.5 |
| Q17     | clickhouse |   4630.5 |      5 |     11777.5 |   10921.4 |   2386.1 |   6890.9 |  13009.7 |
| Q17     | exasol     |     98.6 |      5 |       450.7 |     465.6 |    111.4 |    312.8 |    608.5 |
| Q17     | starrocks  |   4981.2 |      5 |      6557.3 |    7778.7 |   3131.2 |   5167.4 |  12562.3 |
| Q17     | trino      |  59676   |      5 |    164500   |  161576   |  14683.1 | 141361   | 180629   |
| Q18     | clickhouse |   9514.6 |      5 |     41779.2 |   39890   |  11253.8 |  21067.7 |  50451.7 |
| Q18     | exasol     |    911.2 |      5 |      6851.5 |    6525   |   2623.6 |   4005.2 |  10419.7 |
| Q18     | starrocks  |  17481.9 |      5 |     59005.4 |   65541.2 |  24194.4 |  45922.5 | 104378   |
| Q18     | trino      |  51573.6 |      5 |    203611   |  202042   |  28568.6 | 161677   | 241948   |
| Q19     | clickhouse |  20881.1 |      5 |     88133.4 |   71334   |  39850.9 |    381.6 |  92585.7 |
| Q19     | exasol     |    167.6 |      5 |       538   |     508.3 |    216.1 |    166.8 |    711.5 |
| Q19     | starrocks  |   5441.7 |      5 |      7644.3 |    7968.9 |   1793.5 |   6069.2 |  10130.2 |
| Q19     | trino      |  36321.3 |      5 |    137050   |  131233   |  44009.7 |  57577.8 | 169792   |
| Q20     | clickhouse |   9435.8 |      5 |     31173.9 |   30977.3 |   1860.8 |  27996.2 |  32607.2 |
| Q20     | exasol     |    788.5 |      5 |      2165.4 |    1950.3 |    846.3 |    935.1 |   2881.7 |
| Q20     | starrocks  |   5000.2 |      5 |      6052.3 |    6498.4 |    967   |   5765.7 |   8167.3 |
| Q20     | trino      |  44902.3 |      5 |    167082   |  182865   |  32402.1 | 154278   | 224988   |
| Q21     | clickhouse |   6162.8 |      5 |      9922.6 |   10253.1 |   6148.3 |   3860.4 |  19671   |
| Q21     | exasol     |  21438.4 |      5 |      4021   |    4481   |   1945.4 |   2450.1 |   7584.7 |
| Q21     | starrocks  |  30865.6 |      5 |    112914   |  112145   |   7003.4 | 101955   | 121614   |
| Q21     | trino      |  80448.2 |      5 |    222298   |  211310   |  27776.4 | 169095   | 235276   |
| Q22     | clickhouse |   3494.6 |      5 |     10820.8 |   11248.8 |   3719.3 |   6215.6 |  16223.7 |
| Q22     | exasol     |    200.9 |      5 |      1236.5 |    1197.5 |    524.5 |    629.7 |   1824.3 |
| Q22     | starrocks  |   2506.8 |      5 |      4042.8 |    3600.2 |   1122.5 |   1832   |   4490.1 |
| Q22     | trino      |   9348.2 |      5 |     43275.2 |   41589.5 |   3699.1 |  37158.1 |  45895.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        5500   |         18066.6 |    3.28 |      0.3  | False    |
| Q02     | exasol            | clickhouse          |         613.2 |        125479   |  204.63 |      0    | False    |
| Q03     | exasol            | clickhouse          |        2689.2 |         27337.1 |   10.17 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |        1400.4 |         47225.3 |   33.72 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        3908.3 |         26649.5 |    6.82 |      0.15 | False    |
| Q06     | exasol            | clickhouse          |         351.1 |          1524.8 |    4.34 |      0.23 | False    |
| Q07     | exasol            | clickhouse          |        5472.2 |         11578.4 |    2.12 |      0.47 | False    |
| Q08     | exasol            | clickhouse          |        2220.5 |         25783.4 |   11.61 |      0.09 | False    |
| Q09     | exasol            | clickhouse          |       16034.9 |         19420.3 |    1.21 |      0.83 | False    |
| Q10     | exasol            | clickhouse          |        2746.6 |         37538.2 |   13.67 |      0.07 | False    |
| Q11     | exasol            | clickhouse          |        1000   |          6114   |    6.11 |      0.16 | False    |
| Q12     | exasol            | clickhouse          |         940.2 |         16940.1 |   18.02 |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        6422   |         74151.6 |   11.55 |      0.09 | False    |
| Q14     | exasol            | clickhouse          |        1879.4 |          9053.9 |    4.82 |      0.21 | False    |
| Q15     | exasol            | clickhouse          |        1976.5 |          2623.1 |    1.33 |      0.75 | False    |
| Q16     | exasol            | clickhouse          |        1744.9 |         22714.9 |   13.02 |      0.08 | False    |
| Q17     | exasol            | clickhouse          |         450.7 |         11777.5 |   26.13 |      0.04 | False    |
| Q18     | exasol            | clickhouse          |        6851.5 |         41779.2 |    6.1  |      0.16 | False    |
| Q19     | exasol            | clickhouse          |         538   |         88133.4 |  163.82 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        2165.4 |         31173.9 |   14.4  |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        4021   |          9922.6 |    2.47 |      0.41 | False    |
| Q22     | exasol            | clickhouse          |        1236.5 |         10820.8 |    8.75 |      0.11 | False    |
| Q01     | exasol            | starrocks           |        5500   |        100583   |   18.29 |      0.05 | False    |
| Q02     | exasol            | starrocks           |         613.2 |          3926.7 |    6.4  |      0.16 | False    |
| Q03     | exasol            | starrocks           |        2689.2 |         10605.2 |    3.94 |      0.25 | False    |
| Q04     | exasol            | starrocks           |        1400.4 |        160231   |  114.42 |      0.01 | False    |
| Q05     | exasol            | starrocks           |        3908.3 |         24787   |    6.34 |      0.16 | False    |
| Q06     | exasol            | starrocks           |         351.1 |          4495.3 |   12.8  |      0.08 | False    |
| Q07     | exasol            | starrocks           |        5472.2 |         24361.1 |    4.45 |      0.22 | False    |
| Q08     | exasol            | starrocks           |        2220.5 |         29318.7 |   13.2  |      0.08 | False    |
| Q09     | exasol            | starrocks           |       16034.9 |         36489   |    2.28 |      0.44 | False    |
| Q10     | exasol            | starrocks           |        2746.6 |         40515.3 |   14.75 |      0.07 | False    |
| Q11     | exasol            | starrocks           |        1000   |          2135   |    2.13 |      0.47 | False    |
| Q12     | exasol            | starrocks           |         940.2 |         18652.6 |   19.84 |      0.05 | False    |
| Q13     | exasol            | starrocks           |        6422   |         25027.4 |    3.9  |      0.26 | False    |
| Q14     | exasol            | starrocks           |        1879.4 |          9276.7 |    4.94 |      0.2  | False    |
| Q15     | exasol            | starrocks           |        1976.5 |          9991.7 |    5.06 |      0.2  | False    |
| Q16     | exasol            | starrocks           |        1744.9 |          6000.1 |    3.44 |      0.29 | False    |
| Q17     | exasol            | starrocks           |         450.7 |          6557.3 |   14.55 |      0.07 | False    |
| Q18     | exasol            | starrocks           |        6851.5 |         59005.4 |    8.61 |      0.12 | False    |
| Q19     | exasol            | starrocks           |         538   |          7644.3 |   14.21 |      0.07 | False    |
| Q20     | exasol            | starrocks           |        2165.4 |          6052.3 |    2.8  |      0.36 | False    |
| Q21     | exasol            | starrocks           |        4021   |        112914   |   28.08 |      0.04 | False    |
| Q22     | exasol            | starrocks           |        1236.5 |          4042.8 |    3.27 |      0.31 | False    |
| Q01     | exasol            | trino               |        5500   |        116763   |   21.23 |      0.05 | False    |
| Q02     | exasol            | trino               |         613.2 |         99396.2 |  162.09 |      0.01 | False    |
| Q03     | exasol            | trino               |        2689.2 |        189322   |   70.4  |      0.01 | False    |
| Q04     | exasol            | trino               |        1400.4 |        101817   |   72.71 |      0.01 | False    |
| Q05     | exasol            | trino               |        3908.3 |        144164   |   36.89 |      0.03 | False    |
| Q06     | exasol            | trino               |         351.1 |        151612   |  431.82 |      0    | False    |
| Q07     | exasol            | trino               |        5472.2 |        156746   |   28.64 |      0.03 | False    |
| Q08     | exasol            | trino               |        2220.5 |        161536   |   72.75 |      0.01 | False    |
| Q09     | exasol            | trino               |       16034.9 |        133416   |    8.32 |      0.12 | False    |
| Q10     | exasol            | trino               |        2746.6 |        216701   |   78.9  |      0.01 | False    |
| Q11     | exasol            | trino               |        1000   |         50084.7 |   50.08 |      0.02 | False    |
| Q12     | exasol            | trino               |         940.2 |        207880   |  221.1  |      0    | False    |
| Q13     | exasol            | trino               |        6422   |         66469.7 |   10.35 |      0.1  | False    |
| Q14     | exasol            | trino               |        1879.4 |        125295   |   66.67 |      0.01 | False    |
| Q15     | exasol            | trino               |        1976.5 |        152137   |   76.97 |      0.01 | False    |
| Q16     | exasol            | trino               |        1744.9 |         39022.1 |   22.36 |      0.04 | False    |
| Q17     | exasol            | trino               |         450.7 |        164500   |  364.99 |      0    | False    |
| Q18     | exasol            | trino               |        6851.5 |        203611   |   29.72 |      0.03 | False    |
| Q19     | exasol            | trino               |         538   |        137050   |  254.74 |      0    | False    |
| Q20     | exasol            | trino               |        2165.4 |        167082   |   77.16 |      0.01 | False    |
| Q21     | exasol            | trino               |        4021   |        222298   |   55.28 |      0.02 | False    |
| Q22     | exasol            | trino               |        1236.5 |         43275.2 |   35    |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 29755.3 | 22640.5 | 1524.8 | 102067.3 |
| 1 | 28 | 29710.8 | 13407.4 | 611.3 | 135470.1 |
| 2 | 27 | 27157.1 | 23411.4 | 171.2 | 92422.8 |
| 3 | 27 | 29244.5 | 17010.5 | 997.7 | 133777.3 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 13407.4ms
- Slowest stream median: 23411.4ms
- Stream performance variation: 74.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 4191.1 | 3956.8 | 351.1 | 13741.9 |
| 1 | 28 | 3414.8 | 2022.4 | 271.9 | 23128.6 |
| 2 | 27 | 4383.9 | 2165.4 | 166.8 | 24571.5 |
| 3 | 27 | 2872.4 | 1672.5 | 266.7 | 16034.9 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1672.5ms
- Slowest stream median: 3956.8ms
- Stream performance variation: 136.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 33893.2 | 18830.7 | 1832.0 | 127026.5 |
| 1 | 28 | 31592.8 | 9704.9 | 1835.1 | 167001.7 |
| 2 | 27 | 31068.6 | 18652.6 | 2335.8 | 112913.7 |
| 3 | 27 | 32888.0 | 10416.9 | 2135.0 | 195553.4 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 9704.9ms
- Slowest stream median: 18830.7ms
- Stream performance variation: 94.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 139742.7 | 139107.2 | 34571.4 | 259343.1 |
| 1 | 28 | 134311.3 | 144536.2 | 38309.7 | 222121.4 |
| 2 | 27 | 144037.8 | 155030.4 | 47897.7 | 216701.3 |
| 3 | 27 | 132770.8 | 137050.2 | 38117.1 | 232005.5 |

**Performance Analysis for Trino:**
- Fastest stream median: 137050.2ms
- Slowest stream median: 155030.4ms
- Stream performance variation: 13.1% difference between fastest and slowest streams
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
- Median runtime: 19874.6ms
- Average runtime: 28980.9ms
- Fastest query: 171.2ms
- Slowest query: 135470.1ms

**exasol:**
- Median runtime: 2297.1ms
- Average runtime: 3717.2ms
- Fastest query: 166.8ms
- Slowest query: 24571.5ms

**starrocks:**
- Median runtime: 13111.3ms
- Average runtime: 32367.6ms
- Fastest query: 1832.0ms
- Slowest query: 195553.4ms

**trino:**
- Median runtime: 141394.2ms
- Average runtime: 137703.1ms
- Fastest query: 34571.4ms
- Slowest query: 259343.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`ext_scalability_nodes_4-benchmark.zip`](ext_scalability_nodes_4-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 2 logical cores
- **Memory:** 15.3GB RAM
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
  - memory_limit: 12g
  - max_threads: 2
  - max_memory_usage: 6000000000
  - max_bytes_before_external_group_by: 2000000000
  - max_bytes_before_external_sort: 2000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 4000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 36GB
  - query_max_memory_per_node: 9GB

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