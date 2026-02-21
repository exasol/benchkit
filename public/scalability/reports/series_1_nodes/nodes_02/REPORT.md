# Streamlined Scalability - Node Scaling (2 Nodes)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-02-18 12:33:08

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **clickhouse**
- **exasol**
- **starrocks**
- **trino**


## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 8 vCPUs (16 total vCPUs)
- **Memory per node:** 61.8GB RAM (123.6GB total RAM)
- **Node hostnames:**
  - exasol-node0: ip-10-0-1-195
  - exasol-node1: ip-10-0-1-216

### Clickhouse 26.1.3.52

**Software Configuration:**
- **Database:** clickhouse 26.1.3.52
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 8 vCPUs (16 total vCPUs)
- **Memory per node:** 61.8GB RAM (123.6GB total RAM)
- **Node hostnames:**
  - clickhouse-node1: ip-10-0-1-252
  - clickhouse-node0: ip-10-0-1-196

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 8 vCPUs (16 total vCPUs)
- **Memory per node:** 61.8GB RAM (123.6GB total RAM)
- **Node hostnames:**
  - trino-node1: ip-10-0-1-245
  - trino-node0: ip-10-0-1-153

### Starrocks 4.0.6

**Software Configuration:**
- **Database:** starrocks 4.0.6
- **Setup method:** native
- **Cluster configuration:** 2-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **Node Count:** 2 nodes
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores per node:** 8 vCPUs (16 total vCPUs)
- **Memory per node:** 61.8GB RAM (123.6GB total RAM)
- **Node hostnames:**
  - starrocks-node0: ip-10-0-1-226
  - starrocks-node1: ip-10-0-1-97


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

# [All 2 Nodes] Distribute ubuntu SSH key to exasol user
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCxlfKJq1ot4z9oMpQ05GxqZW252FzNpcx2IsuBQAcoBaXznIPDDymt7J2S4TlFhKJAbxSKQiuL4zYZChgLISS6YndVMlkmJxAKV+Kl4DlhlSusY2Yvxq22vJwD57JkcvBywKdt7qLgK8TyVM/wyY6okpfxdg0H3aR6HTp9CA4J0gO+aFCTCn7z3u96HAyayceEJ/yWhj0qigJttRUQdgUNYMARgKG+FIBO9kncjp9eWjTscah83AnxupvrcWhvd5vUXxe9JIzvSBGxsyy51fcLiCCcgkjgjPiUZnwyATOnzYoP/3aOaPNxP/N4xbueSW7rnzLqaT7Kyl8iB7zdO5cb ubuntu@ip-10-0-1-195&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# [All 2 Nodes] Configure localhost SSH access to exasol user
ssh-keyscan -H localhost &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
ssh-keyscan -H 127.0.0.1 &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
mkdir -p ~/.ssh
touch ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; &#39;SSHEOF&#39;

Host localhost 127.0.0.1
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
chmod 600 ~/.ssh/config

# [All 2 Nodes] Generate SSH key pair for exasol user
sudo -u exasol bash -c &#39;mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh &amp;&amp; if [ ! -f ~/.ssh/id_rsa ]; then ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34; -q; fi&#39;

# [All 2 Nodes] Cross-distribute exasol SSH keys for cluster communication
# Collect exasol public keys from all nodes, distribute to all authorized_keys
sudo cat ~exasol/.ssh/id_rsa.pub  # on each node
echo &#39;&lt;KEY&gt;&#39; | sudo tee -a ~exasol/.ssh/authorized_keys &gt; /dev/null
sudo chown exasol:exasol ~exasol/.ssh/authorized_keys &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# [All 2 Nodes] Configure exasol SSH config for cluster nodes
sudo -u exasol bash -c &#39;
mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh
touch ~/.ssh/config &amp;&amp; chmod 600 ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; SSHEOF

Host localhost 127.0.0.1 &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
&#39;

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
confd_client db_configure db_name: Exasol params_add: &#34;[&#39;-writeTouchInit=1&#39;,&#39;-cacheMonitorLimit=0&#39;,&#39;-maxOverallSlbUsageRatio=0.95&#39;,&#39;-useQueryCache=0&#39;,&#39;-query_log_timeout=0&#39;,&#39;-joinOrderMethod=0&#39;,&#39;-etlCheckCertsDefault=0&#39;,&#39;-replicationborder=550000&#39;]&#34;

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
  - `-replicationborder=550000`

**Data Directory:** `None`



#### Trino 479 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67DF398BC5BB293AB with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67DF398BC5BB293AB

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67DF398BC5BB293AB to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67DF398BC5BB293AB /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create trino data directory
sudo mkdir -p /data/trino &amp;&amp; sudo chmod 1777 /data/trino

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
node.id=c6bf4f77-39a7-4975-aca4-53932bde6ee7
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
node-scheduler.include-coordinator=true
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

# [All 2 Nodes] Start and enable Trino service
sudo systemctl start trino &amp;&amp; sudo systemctl enable trino

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



#### Starrocks 4.0.6 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43A6B4504B468D58B with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43A6B4504B468D58B

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43A6B4504B468D58B to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43A6B4504B468D58B /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create starrocks data directory
sudo mkdir -p /data/starrocks &amp;&amp; sudo chmod 1777 /data/starrocks

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
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.6.tar.gz -C /opt/starrocks --strip-components=1

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

# Start FE on follower nodes to join cluster
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --helper &lt;PRIVATE_IP&gt;:9010 --daemon

```

**Setup:**
```bash
# [All 2 Nodes] Execute test command on remote system
test -f /tmp/starrocks-4.0.6.tar.gz &amp;&amp; echo exists

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



#### Clickhouse 26.1.3.52 Setup

**Storage Configuration:**
```bash
# [All 2 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS65E3AB031C42BA31D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS65E3AB031C42BA31D

# [All 2 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 2 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS65E3AB031C42BA31D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS65E3AB031C42BA31D /data

# [All 2 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 2 Nodes] Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

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
DEBIAN_FRONTEND=noninteractive sudo -E apt-get install -y clickhouse-common-static=26.1.3.52 clickhouse-server=26.1.3.52 clickhouse-client=26.1.3.52

```

**Configuration:**
```bash
# [All 2 Nodes] Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;53066920755&lt;/max_server_memory_usage&gt;
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
| Clickhouse | 541.59s | 1.43s | 254.30s | 881.13s | N/A | N/A | N/A |
| Starrocks | 554.96s | 0.18s | 343.25s | 981.59s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 183.95s | 1.01s | 0.00s | 225.69s | N/A | N/A | N/A |
| Exasol | 275.14s | 2.30s | 314.12s | 663.12s | 47.9 GB | 10.5 GB | 4.5x |

**Key Observations:**
- Trino had the fastest preparation time at 225.69s
- Starrocks took 981.59s (4.3x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |    nan   |      5 |      3926.8 |    4679   |   1800.8 |   3703.5 |   7895.5 |
| Q01     | exasol     |    nan   |      5 |      2566   |    2374.3 |    570.8 |   1369.2 |   2799.3 |
| Q01     | starrocks  |    nan   |      5 |      5927.4 |    6892   |   3602.9 |   4212.8 |  13180.8 |
| Q01     | trino      |  22580.1 |      5 |     44115.7 |   44661.4 |   8157.8 |  33157.8 |  55720.1 |
| Q02     | clickhouse |    nan   |      5 |     21363.6 |   21106.5 |   2233.2 |  17737.4 |  23910.9 |
| Q02     | exasol     |    nan   |      5 |       219.1 |     223.9 |     34.8 |    179.4 |    275.5 |
| Q02     | starrocks  |    nan   |      5 |       717.2 |     709.8 |    234.7 |    471.2 |   1000.2 |
| Q02     | trino      |  14228.6 |      5 |     28191.9 |   29824.8 |   5469   |  22815.9 |  35555.3 |
| Q03     | clickhouse |    nan   |      5 |     21447.1 |   22245.4 |   2703.3 |  20157.4 |  26915   |
| Q03     | exasol     |    nan   |      5 |       816.8 |    1418   |    933.4 |    632.9 |   2560.5 |
| Q03     | starrocks  |    nan   |      5 |       586.3 |     947.6 |    700.1 |    390.9 |   2012.8 |
| Q03     | trino      |  36668.7 |      5 |    107146   |  107482   |  16802.3 |  85643.7 | 129951   |
| Q04     | clickhouse |    nan   |      5 |     19582.2 |   19684.7 |   2694.3 |  16763.4 |  23698   |
| Q04     | exasol     |    nan   |      5 |       580.8 |     568.1 |    198.6 |    237.8 |    724.7 |
| Q04     | starrocks  |    nan   |      5 |      1704.8 |    1575.5 |    613.7 |    510.6 |   2057.5 |
| Q04     | trino      |  20444.9 |      5 |     30734.5 |   31513.1 |  17300   |  10499.1 |  57720.1 |
| Q05     | clickhouse |    nan   |      5 |     68178.2 |   67799.1 |   5800.2 |  61165.1 |  74765.1 |
| Q05     | exasol     |    nan   |      5 |      1495.3 |    1400.7 |    407.4 |    744.8 |   1839.7 |
| Q05     | starrocks  |    nan   |      5 |      3362.7 |    3302.2 |    701.1 |   2337   |   4183.4 |
| Q05     | trino      |  22957.8 |      5 |     54275.5 |   55863.9 |  13569.2 |  39722.2 |  76765.3 |
| Q06     | clickhouse |    nan   |      5 |       834.3 |     906.3 |    573.7 |    335.8 |   1832.9 |
| Q06     | exasol     |    nan   |      5 |       156.1 |     150.1 |     61.2 |     91.3 |    238.3 |
| Q06     | starrocks  |    nan   |      5 |       282.3 |     242.2 |    169.7 |     76.1 |    479.8 |
| Q06     | trino      |  28420   |      5 |     45817.1 |   42925.1 |  20333.8 |  22361.5 |  73615.2 |
| Q07     | clickhouse |    nan   |      5 |     84982   |   81324.3 |   7721.4 |  67578.2 |  85373.4 |
| Q07     | exasol     |    nan   |      5 |      2575.4 |    2415   |    658.5 |   1277.8 |   2932.3 |
| Q07     | starrocks  |    nan   |      5 |      1562.8 |    1454.4 |    518.5 |    579.2 |   1845.7 |
| Q07     | trino      |  32340.7 |      5 |     52722.7 |   50514.7 |   4291.3 |  43079.1 |  53281.3 |
| Q08     | clickhouse |    nan   |      5 |    120587   |  119184   |   6991.6 | 107635   | 126672   |
| Q08     | exasol     |    nan   |      5 |       721.7 |     668   |    232.7 |    270.6 |    879.8 |
| Q08     | starrocks  |    nan   |      5 |      1948.2 |    1973.2 |    541.2 |   1359.3 |   2709   |
| Q08     | trino      |  31901.5 |      5 |     95141.5 |   93172.4 |  10391   |  77240.4 | 104547   |
| Q09     | clickhouse |    nan   |      5 |     14052.1 |   21054.3 |  16087.5 |  13237.6 |  49817.6 |
| Q09     | exasol     |    nan   |      5 |      7736.2 |    7384.5 |   1125.5 |   5415.5 |   8169.6 |
| Q09     | starrocks  |    nan   |      5 |      4984.7 |    5082.1 |    967.7 |   3963.9 |   6550   |
| Q09     | trino      |  35780.7 |      5 |     57376.5 |   68353.7 |  34276.3 |  35274.5 | 115905   |
| Q10     | clickhouse |    nan   |      5 |     43668.1 |   43195.3 |   4937.7 |  36188.4 |  47998.7 |
| Q10     | exasol     |    nan   |      5 |      1874   |    1543.4 |    504.2 |    950.6 |   1971.2 |
| Q10     | starrocks  |    nan   |      5 |      2288.5 |    2748.7 |   1011.6 |   1696.3 |   4038.7 |
| Q10     | trino      |  61091.3 |      5 |     84269.8 |   88842.3 |  27338.2 |  52845.7 | 126491   |
| Q11     | clickhouse |    nan   |      5 |      2666   |    2790.3 |   1231.4 |   1447.5 |   4139.4 |
| Q11     | exasol     |    nan   |      5 |       365.5 |     310.8 |    101.1 |    146.1 |    389.7 |
| Q11     | starrocks  |    nan   |      5 |       476.9 |     497.6 |    274.9 |    161.6 |    927.3 |
| Q11     | trino      |   9563.8 |      5 |     14607   |   14387.2 |   2206.7 |  10697.3 |  16355.4 |
| Q12     | clickhouse |    nan   |      5 |     29303.7 |   29621.5 |   2563.1 |  26638.2 |  32825.7 |
| Q12     | exasol     |    nan   |      5 |       518   |     530.1 |     68.3 |    445.1 |    627.5 |
| Q12     | starrocks  |    nan   |      5 |       885.9 |     870   |    137   |    715.9 |   1034.1 |
| Q12     | trino      |  39664.9 |      5 |     85839.2 |   88595.8 |  10178.3 |  79304.6 | 105054   |
| Q13     | clickhouse |    nan   |      5 |     33480.7 |   33656.6 |   2661.9 |  29624.8 |  36865.1 |
| Q13     | exasol     |    nan   |      5 |      2689.3 |    2534.1 |    672.7 |   1396.3 |   3145.8 |
| Q13     | starrocks  |    nan   |      5 |      3893.2 |    3611.4 |   1116.1 |   1840.1 |   4753.2 |
| Q13     | trino      |  16200.6 |      5 |     23607.2 |   24738.7 |   8498.6 |  14248.2 |  37163   |
| Q14     | clickhouse |    nan   |      5 |      2033.7 |    2173.1 |    371.6 |   1779.2 |   2689.4 |
| Q14     | exasol     |    nan   |      5 |       689.4 |     732.3 |    118.9 |    611.9 |    925.7 |
| Q14     | starrocks  |    nan   |      5 |       668.5 |     670.9 |    207.3 |    460.2 |    883.7 |
| Q14     | trino      |  21875.2 |      5 |     66363.8 |   64012.8 |   6803.1 |  53078.9 |  71039   |
| Q15     | clickhouse |    nan   |      5 |      1016.1 |    1404.9 |   1123.6 |    604.5 |   3388.3 |
| Q15     | exasol     |    nan   |      5 |       921.3 |     930.3 |     65.8 |    845.2 |   1018.9 |
| Q15     | starrocks  |    nan   |      5 |       788.8 |     654.7 |    237.6 |    307   |    866.6 |
| Q15     | trino      |  40763.4 |      5 |     56973   |   52818.8 |  10396   |  34650.3 |  60223.9 |
| Q16     | clickhouse |    nan   |      5 |      3855.9 |    4230.7 |   1273.3 |   2684.4 |   5943   |
| Q16     | exasol     |    nan   |      5 |      1211.9 |    1244.4 |     67.8 |   1176.2 |   1347   |
| Q16     | starrocks  |    nan   |      5 |       921.8 |    1127.7 |    379.1 |    822.6 |   1736.4 |
| Q16     | trino      |   5292.6 |      5 |      8908.1 |   22888.7 |  28600.7 |   8720.4 |  73890.2 |
| Q17     | clickhouse |    nan   |      5 |      3694.2 |    3456   |    967.4 |   1792.3 |   4240.7 |
| Q17     | exasol     |    nan   |      5 |       143.6 |     145.5 |     14.4 |    130.3 |    163.8 |
| Q17     | starrocks  |    nan   |      5 |      1895.6 |    2059.9 |    836.7 |   1018.2 |   3202.1 |
| Q17     | trino      |  42482.7 |      5 |     65764.9 |   68233.2 |   8859.6 |  60338.7 |  83215.4 |
| Q18     | clickhouse |    nan   |      5 |      8681.1 |    8865.9 |   1343.3 |   7504   |  10668.9 |
| Q18     | exasol     |    nan   |      5 |      1736.4 |    1696.5 |    275.3 |   1233.6 |   1907.3 |
| Q18     | starrocks  |    nan   |      5 |     10201.8 |   10395.4 |   2628.9 |   6551.7 |  13287.5 |
| Q18     | trino      |  34820.3 |      5 |     76058.4 |   71169.9 |  16689.9 |  45329.7 |  86185.6 |
| Q19     | clickhouse |    nan   |      5 |     14059.7 |   14352.8 |   1452   |  12507.1 |  15937.1 |
| Q19     | exasol     |    nan   |      5 |       127.1 |     175.2 |     86.3 |     97.7 |    285.5 |
| Q19     | starrocks  |    nan   |      5 |      1239.3 |    1069.6 |    383.6 |    424.8 |   1398.7 |
| Q19     | trino      |  27128.1 |      5 |     52448.8 |   46628.5 |  25233.3 |  14094   |  72007.4 |
| Q20     | clickhouse |    nan   |      5 |      8768   |    7370.7 |   2454   |   4472.9 |   9496.3 |
| Q20     | exasol     |    nan   |      5 |       503.7 |     607.2 |    258.2 |    384.1 |    987.2 |
| Q20     | starrocks  |    nan   |      5 |       464.3 |     811.4 |    627.9 |    343.7 |   1772.2 |
| Q20     | trino      |  33604.4 |      5 |     69170.8 |   67421.8 |   9615.8 |  53277.8 |  78946.3 |
| Q21     | clickhouse |    nan   |      5 |      8297.3 |    7872.8 |   1095   |   5941   |   8580.6 |
| Q21     | exasol     |    nan   |      5 |      1599.1 |    1386.1 |    459.5 |    850.1 |   1790.1 |
| Q21     | starrocks  |    nan   |      5 |     11138.1 |   10467.8 |   3643   |   5343   |  13941.7 |
| Q21     | trino      |  61936.7 |      5 |     66651.3 |   70180.6 |  18229   |  53666.6 | 100206   |
| Q22     | clickhouse |    nan   |      5 |      3301.4 |    3029.8 |   1179.2 |   1028.7 |   4161.6 |
| Q22     | exasol     |    nan   |      5 |       360.5 |     322.1 |     87.7 |    199.9 |    418.3 |
| Q22     | starrocks  |    nan   |      5 |      1016.1 |    1117.4 |    589.5 |    387.4 |   2021.3 |
| Q22     | trino      |   6714   |      5 |      9689   |   11635   |   3818.9 |   8227   |  16845.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        2566   |          3926.8 |    1.53 |      0.65 | False    |
| Q02     | exasol            | clickhouse          |         219.1 |         21363.6 |   97.51 |      0.01 | False    |
| Q03     | exasol            | clickhouse          |         816.8 |         21447.1 |   26.26 |      0.04 | False    |
| Q04     | exasol            | clickhouse          |         580.8 |         19582.2 |   33.72 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        1495.3 |         68178.2 |   45.59 |      0.02 | False    |
| Q06     | exasol            | clickhouse          |         156.1 |           834.3 |    5.34 |      0.19 | False    |
| Q07     | exasol            | clickhouse          |        2575.4 |         84982   |   33    |      0.03 | False    |
| Q08     | exasol            | clickhouse          |         721.7 |        120587   |  167.09 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        7736.2 |         14052.1 |    1.82 |      0.55 | False    |
| Q10     | exasol            | clickhouse          |        1874   |         43668.1 |   23.3  |      0.04 | False    |
| Q11     | exasol            | clickhouse          |         365.5 |          2666   |    7.29 |      0.14 | False    |
| Q12     | exasol            | clickhouse          |         518   |         29303.7 |   56.57 |      0.02 | False    |
| Q13     | exasol            | clickhouse          |        2689.3 |         33480.7 |   12.45 |      0.08 | False    |
| Q14     | exasol            | clickhouse          |         689.4 |          2033.7 |    2.95 |      0.34 | False    |
| Q15     | exasol            | clickhouse          |         921.3 |          1016.1 |    1.1  |      0.91 | False    |
| Q16     | exasol            | clickhouse          |        1211.9 |          3855.9 |    3.18 |      0.31 | False    |
| Q17     | exasol            | clickhouse          |         143.6 |          3694.2 |   25.73 |      0.04 | False    |
| Q18     | exasol            | clickhouse          |        1736.4 |          8681.1 |    5    |      0.2  | False    |
| Q19     | exasol            | clickhouse          |         127.1 |         14059.7 |  110.62 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         503.7 |          8768   |   17.41 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |        1599.1 |          8297.3 |    5.19 |      0.19 | False    |
| Q22     | exasol            | clickhouse          |         360.5 |          3301.4 |    9.16 |      0.11 | False    |
| Q01     | exasol            | starrocks           |        2566   |          5927.4 |    2.31 |      0.43 | False    |
| Q02     | exasol            | starrocks           |         219.1 |           717.2 |    3.27 |      0.31 | False    |
| Q03     | exasol            | starrocks           |         816.8 |           586.3 |    0.72 |      1.39 | True     |
| Q04     | exasol            | starrocks           |         580.8 |          1704.8 |    2.94 |      0.34 | False    |
| Q05     | exasol            | starrocks           |        1495.3 |          3362.7 |    2.25 |      0.44 | False    |
| Q06     | exasol            | starrocks           |         156.1 |           282.3 |    1.81 |      0.55 | False    |
| Q07     | exasol            | starrocks           |        2575.4 |          1562.8 |    0.61 |      1.65 | True     |
| Q08     | exasol            | starrocks           |         721.7 |          1948.2 |    2.7  |      0.37 | False    |
| Q09     | exasol            | starrocks           |        7736.2 |          4984.7 |    0.64 |      1.55 | True     |
| Q10     | exasol            | starrocks           |        1874   |          2288.5 |    1.22 |      0.82 | False    |
| Q11     | exasol            | starrocks           |         365.5 |           476.9 |    1.3  |      0.77 | False    |
| Q12     | exasol            | starrocks           |         518   |           885.9 |    1.71 |      0.58 | False    |
| Q13     | exasol            | starrocks           |        2689.3 |          3893.2 |    1.45 |      0.69 | False    |
| Q14     | exasol            | starrocks           |         689.4 |           668.5 |    0.97 |      1.03 | True     |
| Q15     | exasol            | starrocks           |         921.3 |           788.8 |    0.86 |      1.17 | True     |
| Q16     | exasol            | starrocks           |        1211.9 |           921.8 |    0.76 |      1.31 | True     |
| Q17     | exasol            | starrocks           |         143.6 |          1895.6 |   13.2  |      0.08 | False    |
| Q18     | exasol            | starrocks           |        1736.4 |         10201.8 |    5.88 |      0.17 | False    |
| Q19     | exasol            | starrocks           |         127.1 |          1239.3 |    9.75 |      0.1  | False    |
| Q20     | exasol            | starrocks           |         503.7 |           464.3 |    0.92 |      1.08 | True     |
| Q21     | exasol            | starrocks           |        1599.1 |         11138.1 |    6.97 |      0.14 | False    |
| Q22     | exasol            | starrocks           |         360.5 |          1016.1 |    2.82 |      0.35 | False    |
| Q01     | exasol            | trino               |        2566   |         44115.7 |   17.19 |      0.06 | False    |
| Q02     | exasol            | trino               |         219.1 |         28191.9 |  128.67 |      0.01 | False    |
| Q03     | exasol            | trino               |         816.8 |        107146   |  131.18 |      0.01 | False    |
| Q04     | exasol            | trino               |         580.8 |         30734.5 |   52.92 |      0.02 | False    |
| Q05     | exasol            | trino               |        1495.3 |         54275.5 |   36.3  |      0.03 | False    |
| Q06     | exasol            | trino               |         156.1 |         45817.1 |  293.51 |      0    | False    |
| Q07     | exasol            | trino               |        2575.4 |         52722.7 |   20.47 |      0.05 | False    |
| Q08     | exasol            | trino               |         721.7 |         95141.5 |  131.83 |      0.01 | False    |
| Q09     | exasol            | trino               |        7736.2 |         57376.5 |    7.42 |      0.13 | False    |
| Q10     | exasol            | trino               |        1874   |         84269.8 |   44.97 |      0.02 | False    |
| Q11     | exasol            | trino               |         365.5 |         14607   |   39.96 |      0.03 | False    |
| Q12     | exasol            | trino               |         518   |         85839.2 |  165.71 |      0.01 | False    |
| Q13     | exasol            | trino               |        2689.3 |         23607.2 |    8.78 |      0.11 | False    |
| Q14     | exasol            | trino               |         689.4 |         66363.8 |   96.26 |      0.01 | False    |
| Q15     | exasol            | trino               |         921.3 |         56973   |   61.84 |      0.02 | False    |
| Q16     | exasol            | trino               |        1211.9 |          8908.1 |    7.35 |      0.14 | False    |
| Q17     | exasol            | trino               |         143.6 |         65764.9 |  457.97 |      0    | False    |
| Q18     | exasol            | trino               |        1736.4 |         76058.4 |   43.8  |      0.02 | False    |
| Q19     | exasol            | trino               |         127.1 |         52448.8 |  412.66 |      0    | False    |
| Q20     | exasol            | trino               |         503.7 |         69170.8 |  137.33 |      0.01 | False    |
| Q21     | exasol            | trino               |        1599.1 |         66651.3 |   41.68 |      0.02 | False    |
| Q22     | exasol            | trino               |         360.5 |          9689   |   26.88 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 101838.5 | 86351.2 | 8383.7 | 311007.8 |
| 1 | 28 | 92822.2 | 82221.1 | 16479.3 | 219050.6 |
| 2 | 27 | 104753.4 | 114789.8 | 13549.6 | 258248.5 |
| 3 | 27 | 89065.6 | 92859.9 | 15864.6 | 210458.9 |

**Performance Analysis for Trino:**
- Fastest stream median: 82221.1ms
- Slowest stream median: 114789.8ms
- Stream performance variation: 39.6% difference between fastest and slowest streams
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

**trino:**
- Median runtime: 89671.1ms
- Average runtime: 97123.7ms
- Fastest query: 8383.7ms
- Slowest query: 311007.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_2-benchmark.zip`](extscal_nodes_2-benchmark.zip)

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
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;, &#39;-replicationborder=550000&#39;]

**Clickhouse 26.1.3.52:**
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

**Starrocks 4.0.6:**
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