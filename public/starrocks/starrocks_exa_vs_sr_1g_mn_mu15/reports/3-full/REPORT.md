# Exasol vs StarRocks: TPC-H SF1 (Multi-Node 3, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:50:43

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 724.2ms median runtime
- starrocks was 2.5x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 15 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.1.8

**Software Configuration:**
- **Database:** exasol 2025.1.8
- **Setup method:** installer
- **Data device:** /dev/exasol.storage
- **Cluster configuration:** 3-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM
- **Hostname:** ip-10-0-1-203

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native
- **Cluster configuration:** 3-node cluster


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.large
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 2 vCPUs
- **Memory:** 15.3GB RAM
- **Hostname:** ip-10-0-1-76


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.large
- **Starrocks Instance:** r6id.large


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.8 Setup

**Storage Configuration:**
```bash
# [All 3 Nodes] Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# [All 3 Nodes] Create 3GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# [All 3 Nodes] Create raw partition for Exasol (106GB)
sudo parted /dev/nvme1n1 mkpart primary 3GiB 100%

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 3GiB 100%

# [All 3 Nodes] Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# [All 3 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 3 Nodes] Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# [All 3 Nodes] Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# [All 3 Nodes] Create Exasol system user
sudo useradd -m -s /bin/bash exasol

# [All 3 Nodes] Add exasol user to sudo group
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
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=24000
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
# [All 3 Nodes] Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# [All 3 Nodes] Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# [All 3 Nodes] Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

# Execute wget command on remote system
wget -q https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.5/c4 -O c4 &amp;&amp; chmod +x c4

# Execute echo command on remote system
echo &#34;CCC_HOST_ADDRS=\&#34;&lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt; &lt;PRIVATE_IP&gt;\&#34;
CCC_HOST_EXTERNAL_ADDRS=\&#34;&lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt; &lt;PUBLIC_IP&gt;\&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=24000
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



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# [All 3 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B4149542FBC47C4 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B4149542FBC47C4

# [All 3 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 3 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B4149542FBC47C4 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B4149542FBC47C4 /data

# [All 3 Nodes] Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# [All 3 Nodes] Create StarRocks data directory
sudo mkdir -p /data/starrocks

# [All 3 Nodes] Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# [All 3 Nodes] Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 3 Nodes] Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# [All 3 Nodes] Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 3 Nodes] Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 3 Nodes] Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# [All 3 Nodes] Configure StarRocks FE
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

# [All 3 Nodes] Configure StarRocks BE
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
# [All 3 Nodes] Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 3 Nodes] Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# [All 3 Nodes] Execute sudo command on remote system
sudo mkdir -p /data/starrocks

# [All 3 Nodes] Execute sudo command on remote system
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# [All 3 Nodes] Execute echo command on remote system
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

# [All 3 Nodes] Execute wget command on remote system
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# [All 3 Nodes] Execute sudo command on remote system
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# [All 3 Nodes] Execute sudo command on remote system
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

# [All 3 Nodes] Execute sudo command on remote system
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

# [All 3 Nodes] Execute sudo command on remote system
sudo chown -R $(whoami):$(whoami) /opt/starrocks

# [All 3 Nodes] Execute export command on remote system
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 &amp;&amp; cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# [All 3 Nodes] Execute export command on remote system
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




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 1
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (15 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_1g_mn_mu15-benchmark.zip
cd starrocks_exa_vs_sr_1g_mn_mu15

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

| query   | system    |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|-----------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | exasol    |     65   |      5 |       561.3 |     593.6 |    346.8 |     62.9 |    969.2 |
| Q01     | starrocks |    843.9 |      5 |      1292   |    1295.9 |    329.8 |    942.8 |   1752.8 |
| Q02     | exasol    |    124.8 |      5 |      1066.5 |    3116.3 |   4794.2 |    805.2 |  11690.1 |
| Q02     | starrocks |    351.7 |      5 |      3166.3 |    2952.9 |    525.1 |   2286   |   3411.6 |
| Q03     | exasol    |     61.5 |      5 |       672.5 |     620.1 |    278.5 |    237.5 |    972.3 |
| Q03     | starrocks |    221.4 |      5 |      1216   |    1465.2 |    378.6 |   1173   |   2012.1 |
| Q04     | exasol    |     36.2 |      5 |       391   |     318.9 |    286.2 |     34.1 |    722.5 |
| Q04     | starrocks |    131.7 |      5 |      1650.7 |    1490   |    833.5 |    116.4 |   2393.8 |
| Q05     | exasol    |    115.5 |      5 |      1542.5 |    1535.3 |    400.8 |   1156.5 |   2174.4 |
| Q05     | starrocks |    167.4 |      5 |      1859.2 |    1796.2 |    667.8 |    696.5 |   2332.2 |
| Q06     | exasol    |     17.7 |      5 |       180.5 |     204.4 |    120.6 |     71.8 |    387.5 |
| Q06     | starrocks |     71.2 |      5 |       763.5 |     921.9 |    415.9 |    600   |   1621.5 |
| Q07     | exasol    |     89.8 |      5 |      1538.9 |    1420.5 |    828.4 |     88.3 |   2260.5 |
| Q07     | starrocks |    148.5 |      5 |      2219.2 |    2192.3 |    279.6 |   1728.9 |   2441.9 |
| Q08     | exasol    |     76.7 |      5 |      1031.5 |    1017   |    470.5 |    578.5 |   1733.1 |
| Q08     | starrocks |    237   |      5 |      1854.5 |    1624.2 |    605.4 |    548.3 |   2009.6 |
| Q09     | exasol    |    164.7 |      5 |      2682.1 |    2951   |    824.9 |   2222.7 |   4201.1 |
| Q09     | starrocks |    275.6 |      5 |      2427.9 |    2460.3 |    264.5 |   2127.1 |   2774   |
| Q10     | exasol    |     79.4 |      5 |      1291.5 |    1287.1 |    572.6 |    717.6 |   2137.5 |
| Q10     | starrocks |    318.6 |      5 |      2486.3 |    2438   |    631.3 |   1419.2 |   3108   |
| Q11     | exasol    |     50   |      5 |       398.2 |     541.1 |    282.9 |    282   |    876.9 |
| Q11     | starrocks |    120.7 |      5 |      2360   |    2249.2 |   1101.9 |    581.3 |   3674.8 |
| Q12     | exasol    |     37   |      5 |       390.7 |     455   |    299.8 |    164.8 |    963.6 |
| Q12     | starrocks |    154.9 |      5 |      2086.9 |    1903.5 |    714.6 |    801.2 |   2650.2 |
| Q13     | exasol    |     61.6 |      5 |       749.8 |     997.9 |   1033.6 |     99.7 |   2742.4 |
| Q13     | starrocks |    228.1 |      5 |      1769.7 |    1751.3 |    417.4 |   1370.6 |   2398.8 |
| Q14     | exasol    |     33.1 |      5 |       418.3 |     478.2 |    344   |     33.3 |    991.2 |
| Q14     | starrocks |     88.4 |      5 |      1532.9 |    1687.6 |    809.3 |    621.7 |   2688.4 |
| Q15     | exasol    |     47.4 |      5 |       681.3 |     805.5 |    372.5 |    426   |   1396.7 |
| Q15     | starrocks |    126.4 |      5 |      1027   |    1192.4 |    396.8 |    868.1 |   1791.9 |
| Q16     | exasol    |    116.9 |      5 |      1295.1 |    1479.8 |   1254.6 |    325.9 |   3275.2 |
| Q16     | starrocks |    257.5 |      5 |      1499.2 |    1809.7 |    911.3 |   1190   |   3383.2 |
| Q17     | exasol    |     44.1 |      5 |       475.2 |     398.6 |    186.1 |    138.4 |    580.8 |
| Q17     | starrocks |    118.8 |      5 |      1393.9 |    1236.4 |    695.4 |    222.3 |   1931.1 |
| Q18     | exasol    |    125   |      5 |      2205.7 |    1839.7 |    926.5 |    846.6 |   2868.4 |
| Q18     | starrocks |    268.1 |      5 |      4287.6 |    4469.7 |    886.3 |   3584.5 |   5419.1 |
| Q19     | exasol    |     27.5 |      5 |       347   |     319.3 |    209.7 |     27.2 |    595.4 |
| Q19     | starrocks |    111.8 |      5 |      1484.6 |    1467.5 |    484.3 |    686.1 |   1993.1 |
| Q20     | exasol    |     60.3 |      5 |       719.7 |     719.2 |    412.9 |     61   |   1121.2 |
| Q20     | starrocks |    169   |      5 |      2089.3 |    2188.8 |    805.4 |   1357.8 |   3482   |
| Q21     | exasol    |     58.8 |      5 |      1016.6 |     848   |    363.2 |    267   |   1160.6 |
| Q21     | starrocks |    466.3 |      5 |      4765.1 |    4494.8 |   2561.8 |   1249.4 |   8088.4 |
| Q22     | exasol    |     31.5 |      5 |       563.3 |     564.1 |    191.2 |    354.7 |    763.6 |
| Q22     | starrocks |     77.8 |      5 |      1638.4 |    1630.9 |    485.9 |   1066.4 |   2130.5 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |         561.3 |          1292   |    2.3  |      0.43 | False    |
| Q02     | exasol            | starrocks           |        1066.5 |          3166.3 |    2.97 |      0.34 | False    |
| Q03     | exasol            | starrocks           |         672.5 |          1216   |    1.81 |      0.55 | False    |
| Q04     | exasol            | starrocks           |         391   |          1650.7 |    4.22 |      0.24 | False    |
| Q05     | exasol            | starrocks           |        1542.5 |          1859.2 |    1.21 |      0.83 | False    |
| Q06     | exasol            | starrocks           |         180.5 |           763.5 |    4.23 |      0.24 | False    |
| Q07     | exasol            | starrocks           |        1538.9 |          2219.2 |    1.44 |      0.69 | False    |
| Q08     | exasol            | starrocks           |        1031.5 |          1854.5 |    1.8  |      0.56 | False    |
| Q09     | exasol            | starrocks           |        2682.1 |          2427.9 |    0.91 |      1.1  | True     |
| Q10     | exasol            | starrocks           |        1291.5 |          2486.3 |    1.93 |      0.52 | False    |
| Q11     | exasol            | starrocks           |         398.2 |          2360   |    5.93 |      0.17 | False    |
| Q12     | exasol            | starrocks           |         390.7 |          2086.9 |    5.34 |      0.19 | False    |
| Q13     | exasol            | starrocks           |         749.8 |          1769.7 |    2.36 |      0.42 | False    |
| Q14     | exasol            | starrocks           |         418.3 |          1532.9 |    3.66 |      0.27 | False    |
| Q15     | exasol            | starrocks           |         681.3 |          1027   |    1.51 |      0.66 | False    |
| Q16     | exasol            | starrocks           |        1295.1 |          1499.2 |    1.16 |      0.86 | False    |
| Q17     | exasol            | starrocks           |         475.2 |          1393.9 |    2.93 |      0.34 | False    |
| Q18     | exasol            | starrocks           |        2205.7 |          4287.6 |    1.94 |      0.51 | False    |
| Q19     | exasol            | starrocks           |         347   |          1484.6 |    4.28 |      0.23 | False    |
| Q20     | exasol            | starrocks           |         719.7 |          2089.3 |    2.9  |      0.34 | False    |
| Q21     | exasol            | starrocks           |        1016.6 |          4765.1 |    4.69 |      0.21 | False    |
| Q22     | exasol            | starrocks           |         563.3 |          1638.4 |    2.91 |      0.34 | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 852.2 | 664.1 | 180.5 | 2405.3 |
| 1 | 8 | 1512.1 | 62.0 | 27.2 | 11690.1 |
| 10 | 7 | 953.7 | 744.7 | 231.5 | 2742.4 |
| 11 | 7 | 884.6 | 563.3 | 392.6 | 2260.5 |
| 12 | 7 | 1238.5 | 1084.7 | 49.8 | 2222.7 |
| 13 | 7 | 1109.4 | 1235.8 | 71.8 | 2312.5 |
| 14 | 7 | 963.8 | 1000.9 | 387.5 | 1538.9 |
| 2 | 8 | 837.9 | 787.4 | 354.7 | 1733.1 |
| 3 | 8 | 921.8 | 614.2 | 237.5 | 2682.1 |
| 4 | 8 | 943.4 | 709.6 | 138.4 | 3275.2 |
| 5 | 7 | 1133.6 | 1016.6 | 356.3 | 3336.4 |
| 6 | 7 | 887.1 | 717.6 | 164.8 | 2137.5 |
| 7 | 7 | 916.4 | 426.0 | 347.0 | 2868.4 |
| 8 | 7 | 1201.4 | 726.0 | 267.0 | 4201.1 |
| 9 | 7 | 999.2 | 763.6 | 135.6 | 2174.4 |

**Performance Analysis for Exasol:**
- Fastest stream median: 62.0ms
- Slowest stream median: 1235.8ms
- Stream performance variation: 1894.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 2077.4 | 2292.9 | 548.3 | 5370.5 |
| 1 | 8 | 1793.5 | 1507.0 | 1292.0 | 3398.7 |
| 10 | 7 | 1976.9 | 1756.4 | 868.1 | 3482.0 |
| 11 | 7 | 1668.3 | 1728.9 | 1066.4 | 2130.5 |
| 12 | 7 | 2458.6 | 2427.9 | 116.4 | 4287.6 |
| 13 | 7 | 1980.9 | 2332.2 | 970.1 | 2670.8 |
| 14 | 7 | 1713.4 | 1769.7 | 763.5 | 2441.9 |
| 2 | 8 | 1741.0 | 1904.2 | 1026.1 | 2092.3 |
| 3 | 8 | 2009.9 | 1926.4 | 942.8 | 3674.8 |
| 4 | 8 | 2118.4 | 1594.4 | 222.3 | 8088.4 |
| 5 | 7 | 2448.5 | 2393.8 | 1173.0 | 4765.1 |
| 6 | 7 | 2162.2 | 2360.0 | 1210.8 | 3108.0 |
| 7 | 7 | 2221.7 | 2089.3 | 621.7 | 5419.1 |
| 8 | 7 | 2400.7 | 2286.0 | 878.3 | 5312.5 |
| 9 | 7 | 1779.3 | 1621.5 | 654.6 | 3686.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1507.0ms
- Slowest stream median: 2427.9ms
- Stream performance variation: 61.1% difference between fastest and slowest streams
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
- Median runtime: 724.2ms
- Average runtime: 1023.2ms
- Fastest query: 27.2ms
- Slowest query: 11690.1ms

**starrocks:**
- Median runtime: 1807.4ms
- Average runtime: 2032.7ms
- Fastest query: 116.4ms
- Slowest query: 8088.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_1g_mn_mu15-benchmark.zip`](starrocks_exa_vs_sr_1g_mn_mu15-benchmark.zip)

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

**Exasol 2025.1.8:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Starrocks 4.0.4:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 9
  - replication_num: 1


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 15 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts