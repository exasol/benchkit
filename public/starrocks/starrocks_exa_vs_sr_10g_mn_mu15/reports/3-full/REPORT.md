# Exasol vs StarRocks: TPC-H SF10 (Multi-Node 3, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:35:12

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 1581.2ms median runtime
- starrocks was 5.6x slower- Tested 220 total query executions across 22 different TPC-H queries
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

# [All 3 Nodes] Create 20GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# [All 3 Nodes] Create raw partition for Exasol (89GB)
sudo parted /dev/nvme1n1 mkpart primary 20GiB 100%

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 20GiB 100%

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
CCC_PLAY_DB_MEM_SIZE=36000
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
CCC_PLAY_DB_MEM_SIZE=36000
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
# [All 3 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4726A8B957D7DD0DB with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4726A8B957D7DD0DB

# [All 3 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 3 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4726A8B957D7DD0DB to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4726A8B957D7DD0DB /data

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
- **Scale factor:** 10
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
unzip starrocks_exa_vs_sr_10g_mn_mu15-benchmark.zip
cd starrocks_exa_vs_sr_10g_mn_mu15

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
| Q01     | exasol    |    452.5 |      5 |      8308.2 |    8800.4 |   5277.7 |   3522.7 |  14741.2 |
| Q01     | starrocks |   6022.1 |      5 |     85849.7 |   80030.6 |  50655.2 |   5222.9 | 147037   |
| Q02     | exasol    |    170.1 |      5 |       760.7 |     891   |    243.1 |    687.1 |   1267.2 |
| Q02     | starrocks |    494.6 |      5 |      2087.5 |    3476.9 |   2829.4 |   1258.6 |   7860.3 |
| Q03     | exasol    |    356.4 |      5 |      1896.5 |    2330.8 |    732.4 |   1777   |   3477.1 |
| Q03     | starrocks |   1822.3 |      5 |      9155.7 |   14236.8 |   7434.9 |   8781.2 |  24833.6 |
| Q04     | exasol    |    128   |      5 |       993   |     955.9 |    476.7 |    255.5 |   1595.1 |
| Q04     | starrocks |    845.7 |      5 |      6024.7 |   10010.3 |   6607.1 |   3864.5 |  18492.2 |
| Q05     | exasol    |    388.6 |      5 |      2970.1 |    2629.3 |   1640.2 |    321.1 |   4304.6 |
| Q05     | starrocks |   1437.5 |      5 |      9069.6 |    8673.1 |   2087.2 |   6379.9 |  11203.2 |
| Q06     | exasol    |     42.9 |      5 |       464.9 |     429.3 |    372.9 |     47.2 |    911.2 |
| Q06     | starrocks |    515.1 |      5 |      2423.5 |    4432.2 |   3428.9 |   1762.6 |   9166.2 |
| Q07     | exasol    |    504.3 |      5 |     14719.8 |   12139.5 |   5569.4 |   2606.7 |  15987.7 |
| Q07     | starrocks |   1265.5 |      5 |     11958.9 |   15475.7 |  10152   |   3848.6 |  27075.4 |
| Q08     | exasol    |    224.1 |      5 |      1287   |    1359.5 |    784.2 |    238   |   2115.1 |
| Q08     | starrocks |   1593.9 |      5 |      4371.3 |    5054.7 |   3026.6 |   1923.8 |   9572.9 |
| Q09     | exasol    |   1317.3 |      5 |     18024.4 |   16586.1 |   3175   |  11935.6 |  19882.6 |
| Q09     | starrocks |   2634   |      5 |     20254.2 |   23102.2 |  12298.6 |   9331.3 |  42864.8 |
| Q10     | exasol    |    329.2 |      5 |      3440.5 |    8923   |   9163   |   1567.2 |  19999.1 |
| Q10     | starrocks |   2585.7 |      5 |     14085.9 |   13241.1 |   4452.8 |   6536.8 |  17564   |
| Q11     | exasol    |     97.3 |      5 |       596.9 |     583   |    368.5 |     96.6 |   1004.8 |
| Q11     | starrocks |    367.4 |      5 |      1672.7 |    2896.2 |   3024.6 |    870.6 |   8148.4 |
| Q12     | exasol    |    238.8 |      5 |      1739.8 |    3789.3 |   4659.8 |    170.3 |  11574.3 |
| Q12     | starrocks |    988   |      5 |     11904.3 |   11439.9 |   6857.1 |   3208.2 |  19758.2 |
| Q13     | exasol    |    902.2 |      5 |     17134.3 |   19083.9 |  14381.7 |   2496.3 |  41918.7 |
| Q13     | starrocks |   2075.2 |      5 |     45158   |   41771.4 |  10622.7 |  25198.2 |  53862.5 |
| Q14     | exasol    |    343.3 |      5 |       899.9 |    1064.7 |    800   |    201.8 |   2097.7 |
| Q14     | starrocks |   1078.1 |      5 |      5900.4 |    6967.5 |   4769.2 |   1679.2 |  14678.8 |
| Q15     | exasol    |    262.3 |      5 |      1032   |    1312.6 |    929.5 |    563   |   2901.8 |
| Q15     | starrocks |    528.8 |      5 |      4521   |    5505.1 |   3591   |   1161.3 |   9547.4 |
| Q16     | exasol    |    673.9 |      5 |      2492.9 |    2680.5 |   2080.2 |    562.7 |   5436.4 |
| Q16     | starrocks |    643.8 |      5 |      2766   |    3387.5 |   1931.8 |   2149.1 |   6781.5 |
| Q17     | exasol    |    104.1 |      5 |       678.5 |     752.4 |    451.1 |    207   |   1453   |
| Q17     | starrocks |   1025.5 |      5 |      4311.3 |    6692.9 |   4915.1 |   1906.8 |  12560.5 |
| Q18     | exasol    |    299.3 |      5 |      4279.5 |    5916.4 |   7179.1 |    313.7 |  18128.8 |
| Q18     | starrocks |   2572.8 |      5 |     39779.7 |   50227.5 |  39948.1 |  16458.2 | 118473   |
| Q19     | exasol    |     72.1 |      5 |       476.6 |     533   |    211.1 |    262.5 |    796   |
| Q19     | starrocks |   1026.7 |      5 |      2785.2 |    5054.2 |   5542.8 |   1461.1 |  14753.1 |
| Q20     | exasol    |    192.7 |      5 |      1499   |    1832.9 |   1706.9 |    564.1 |   4732.3 |
| Q20     | starrocks |   1502.9 |      5 |      5154.3 |    9068.6 |   9198.7 |   1970.2 |  24517.7 |
| Q21     | exasol    |    283.8 |      5 |      2508.4 |    3435.3 |   2546.5 |   1810.3 |   7949   |
| Q21     | starrocks |   4400.7 |      5 |     51328.6 |   58719.7 |  50643   |  13805.7 | 135869   |
| Q22     | exasol    |     89.4 |      5 |       897.7 |    1065.8 |    342.7 |    682.1 |   1445.4 |
| Q22     | starrocks |    486   |      5 |      5448.5 |    5454   |   5154.8 |    411.4 |  12133.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        8308.2 |         85849.7 |   10.33 |      0.1  | False    |
| Q02     | exasol            | starrocks           |         760.7 |          2087.5 |    2.74 |      0.36 | False    |
| Q03     | exasol            | starrocks           |        1896.5 |          9155.7 |    4.83 |      0.21 | False    |
| Q04     | exasol            | starrocks           |         993   |          6024.7 |    6.07 |      0.16 | False    |
| Q05     | exasol            | starrocks           |        2970.1 |          9069.6 |    3.05 |      0.33 | False    |
| Q06     | exasol            | starrocks           |         464.9 |          2423.5 |    5.21 |      0.19 | False    |
| Q07     | exasol            | starrocks           |       14719.8 |         11958.9 |    0.81 |      1.23 | True     |
| Q08     | exasol            | starrocks           |        1287   |          4371.3 |    3.4  |      0.29 | False    |
| Q09     | exasol            | starrocks           |       18024.4 |         20254.2 |    1.12 |      0.89 | False    |
| Q10     | exasol            | starrocks           |        3440.5 |         14085.9 |    4.09 |      0.24 | False    |
| Q11     | exasol            | starrocks           |         596.9 |          1672.7 |    2.8  |      0.36 | False    |
| Q12     | exasol            | starrocks           |        1739.8 |         11904.3 |    6.84 |      0.15 | False    |
| Q13     | exasol            | starrocks           |       17134.3 |         45158   |    2.64 |      0.38 | False    |
| Q14     | exasol            | starrocks           |         899.9 |          5900.4 |    6.56 |      0.15 | False    |
| Q15     | exasol            | starrocks           |        1032   |          4521   |    4.38 |      0.23 | False    |
| Q16     | exasol            | starrocks           |        2492.9 |          2766   |    1.11 |      0.9  | False    |
| Q17     | exasol            | starrocks           |         678.5 |          4311.3 |    6.35 |      0.16 | False    |
| Q18     | exasol            | starrocks           |        4279.5 |         39779.7 |    9.3  |      0.11 | False    |
| Q19     | exasol            | starrocks           |         476.6 |          2785.2 |    5.84 |      0.17 | False    |
| Q20     | exasol            | starrocks           |        1499   |          5154.3 |    3.44 |      0.29 | False    |
| Q21     | exasol            | starrocks           |        2508.4 |         51328.6 |   20.46 |      0.05 | False    |
| Q22     | exasol            | starrocks           |         897.7 |          5448.5 |    6.07 |      0.16 | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 5413.4 | 219.9 | 47.2 | 41918.7 |
| 1 | 8 | 4617.4 | 1130.1 | 262.5 | 17134.3 |
| 10 | 7 | 4301.9 | 803.1 | 476.6 | 19911.2 |
| 11 | 7 | 3752.1 | 903.5 | 796.0 | 15987.7 |
| 12 | 7 | 5460.3 | 1130.0 | 255.5 | 18024.4 |
| 13 | 7 | 5336.0 | 1821.5 | 72.1 | 15551.1 |
| 14 | 7 | 5137.5 | 1499.0 | 440.9 | 14719.8 |
| 2 | 8 | 4276.6 | 2104.2 | 620.2 | 14741.2 |
| 3 | 8 | 4669.2 | 2686.1 | 564.1 | 19882.6 |
| 4 | 8 | 2380.6 | 1513.4 | 596.9 | 7949.0 |
| 5 | 7 | 5521.6 | 2188.7 | 859.6 | 17786.7 |
| 6 | 7 | 5284.1 | 1567.2 | 356.1 | 19999.1 |
| 7 | 7 | 1680.5 | 1291.0 | 688.9 | 4279.5 |
| 8 | 7 | 4410.0 | 1810.3 | 207.0 | 18240.4 |
| 9 | 7 | 4060.9 | 1032.0 | 651.1 | 18128.8 |

**Performance Analysis for Exasol:**
- Fastest stream median: 219.9ms
- Slowest stream median: 2686.1ms
- Stream performance variation: 1121.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 14497.6 | 8111.4 | 1057.7 | 45158.0 |
| 1 | 8 | 20195.5 | 6907.0 | 1461.1 | 72596.5 |
| 10 | 7 | 15100.5 | 12560.5 | 2087.5 | 39283.2 |
| 11 | 7 | 10165.2 | 9378.0 | 6024.7 | 14753.1 |
| 12 | 7 | 16363.1 | 16458.2 | 1258.6 | 39779.7 |
| 13 | 7 | 14015.4 | 14085.9 | 1762.6 | 25198.2 |
| 14 | 7 | 22567.7 | 5154.3 | 1810.6 | 89447.3 |
| 2 | 8 | 21395.0 | 3662.1 | 411.4 | 147036.6 |
| 3 | 8 | 19681.2 | 9743.8 | 5425.8 | 85849.7 |
| 4 | 8 | 19823.7 | 3251.3 | 870.6 | 135869.4 |
| 5 | 7 | 20042.9 | 11384.6 | 2225.7 | 77331.5 |
| 6 | 7 | 14933.6 | 17564.0 | 2731.8 | 24833.6 |
| 7 | 7 | 20371.5 | 1831.5 | 1161.3 | 118473.0 |
| 8 | 7 | 18978.5 | 11391.4 | 1906.8 | 51328.6 |
| 9 | 7 | 13154.1 | 9166.2 | 3015.3 | 47902.2 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1831.5ms
- Slowest stream median: 17564.0ms
- Stream performance variation: 859.0% difference between fastest and slowest streams
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
- Median runtime: 1581.2ms
- Average runtime: 4413.4ms
- Fastest query: 47.2ms
- Slowest query: 41918.7ms

**starrocks:**
- Median runtime: 8832.0ms
- Average runtime: 17496.3ms
- Fastest query: 411.4ms
- Slowest query: 147036.6ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_10g_mn_mu15-benchmark.zip`](starrocks_exa_vs_sr_10g_mn_mu15-benchmark.zip)

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
  - bucket_count: 12
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