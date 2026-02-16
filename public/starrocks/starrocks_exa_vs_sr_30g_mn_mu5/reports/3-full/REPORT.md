# Exasol vs StarRocks: TPC-H SF30 (Multi-Node 3, 5 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 16:07:27

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 2204.8ms median runtime
- starrocks was 3.8x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 5 concurrent streams (randomized distribution)

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

# [All 3 Nodes] Create 48GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 48GiB

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 48GiB

# [All 3 Nodes] Create raw partition for Exasol (61GB)
sudo parted /dev/nvme1n1 mkpart primary 48GiB 100%

# [All 3 Nodes] Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 48GiB 100%

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
# [All 3 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2438B2442A28A8402 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2438B2442A28A8402

# [All 3 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 3 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2438B2442A28A8402 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2438B2442A28A8402 /data

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
- **Scale factor:** 30
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (5 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_30g_mn_mu5-benchmark.zip
cd starrocks_exa_vs_sr_30g_mn_mu5

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
| Q01     | exasol    |   1268   |      5 |      6507.6 |    5730.6 |   2882   |   1286.7 |   8341   |
| Q01     | starrocks |  16160.3 |      5 |     79180.9 |   95120.5 |  52652.8 |  48541.7 | 185595   |
| Q02     | exasol    |    115.2 |      5 |       557   |    3729.5 |   5703.2 |    299.5 |  13598.1 |
| Q02     | starrocks |   1032.7 |      5 |      2141.5 |    3006.5 |   2150.5 |   1388.3 |   6753.1 |
| Q03     | exasol    |   1020.1 |      5 |      4292.4 |    7487.6 |   8202   |   1788.8 |  21783.7 |
| Q03     | starrocks |   6643.1 |      5 |     28039.7 |   22216   |  11967.1 |   6153.4 |  34818.7 |
| Q04     | exasol    |    288.5 |      5 |      1181.2 |    1162.7 |    667.5 |    322.5 |   1938.5 |
| Q04     | starrocks |   4842.3 |      5 |     61306.7 |   94458.6 |  79140.2 |  17905.6 | 184738   |
| Q05     | exasol    |   1068.8 |      5 |      4776.5 |    5434.4 |   1816.6 |   3480.9 |   8300.6 |
| Q05     | starrocks |   6213   |      5 |     34220.2 |   29528.7 |  10618.9 |  16467.4 |  41031.5 |
| Q06     | exasol    |     68.9 |      5 |       341.4 |     377.9 |    163.3 |    229.2 |    650.2 |
| Q06     | starrocks |   2428.6 |      5 |      4103.5 |    4064.3 |   1735   |   2313.8 |   6837.5 |
| Q07     | exasol    |   1369.1 |      5 |      7067   |    8182.9 |   3753.2 |   5822.8 |  14774.8 |
| Q07     | starrocks |   4491.2 |      5 |      7231   |    7666.2 |   1007.8 |   6572.6 |   9143.9 |
| Q08     | exasol    |    722.4 |      5 |      1671.4 |    1991.2 |    593.1 |   1476.9 |   2787.6 |
| Q08     | starrocks |   5699.5 |      5 |     14230.4 |   14047   |   4825.5 |   6137.5 |  18295.3 |
| Q09     | exasol    |   5581   |      5 |     17644.7 |   19557.9 |   5156.1 |  15660.8 |  28564.3 |
| Q09     | starrocks |   9872.3 |      5 |     25264   |   27145.2 |   6313.2 |  22026.4 |  37764.3 |
| Q10     | exasol    |    884.7 |      5 |      4488.1 |    6223.1 |   4201.6 |   3553.9 |  13641.9 |
| Q10     | starrocks |   9023.3 |      5 |     21979.5 |   22430.7 |   2330.5 |  19499.7 |  25440.4 |
| Q11     | exasol    |   1741.6 |      5 |      1326.8 |    1363.1 |    608   |    766.1 |   2260.1 |
| Q11     | starrocks |    724.9 |      5 |      1576.8 |    2546.5 |   2147   |   1252.4 |   6340.7 |
| Q12     | exasol    |    292.4 |      5 |      1296.3 |    1468.1 |    553.7 |    963.3 |   2058.8 |
| Q12     | starrocks |   3561.2 |      5 |      8436.8 |   10376.1 |   5117.6 |   6263.7 |  18564.8 |
| Q13     | exasol    |   1213.6 |      5 |      8908.6 |    8326.2 |   2752.2 |   4327.8 |  11903.1 |
| Q13     | starrocks |   6572.6 |      5 |     20548.2 |   22888.8 |  12957.1 |  13126   |  45123.4 |
| Q14     | exasol    |    400.5 |      5 |      1427   |    1469.2 |    737.5 |    390.9 |   2422.4 |
| Q14     | starrocks |   2876.9 |      5 |      4663.7 |    5282.1 |   2510.2 |   3430.1 |   9654.2 |
| Q15     | exasol    |    324.9 |      5 |      1425.8 |    1494.6 |    398.1 |    956   |   1961.6 |
| Q15     | starrocks |   2539.8 |      5 |      4766.4 |    4466.6 |   1567.8 |   2534.6 |   6441.9 |
| Q16     | exasol    |    564.6 |      5 |      2406.4 |    2378.7 |    825.5 |   1345.2 |   3555.4 |
| Q16     | starrocks |   1331.9 |      5 |      2572.5 |    2747.3 |   1001   |   1325.3 |   3864.7 |
| Q17     | exasol    |     79.4 |      5 |       395.8 |     482.8 |    257.2 |    258.6 |    922.5 |
| Q17     | starrocks |   3135.1 |      5 |      5475.8 |    6819.1 |   3456.6 |   3871.8 |  12756   |
| Q18     | exasol    |    726.8 |      5 |      2586.4 |    6933.3 |   8627.2 |   2149.5 |  22183.9 |
| Q18     | starrocks |  10515.5 |      5 |     33756.7 |   32971.4 |   5742.5 |  23349   |  38578.5 |
| Q19     | exasol    |    109.8 |      5 |       648.4 |     583.1 |    136   |    435.7 |    727.3 |
| Q19     | starrocks |   3537.4 |      5 |      4697   |    5168.4 |   1708.1 |   3628.3 |   7740.1 |
| Q20     | exasol    |    395.3 |      5 |      2495.4 |    2253.7 |    821.2 |    834.9 |   2975.9 |
| Q20     | starrocks |   3103.4 |      5 |      5350   |    6251   |   2540   |   3680   |   9810.1 |
| Q21     | exasol    |  16117.6 |      5 |      5373   |    6681   |   4260.7 |   2503.9 |  13805.2 |
| Q21     | starrocks |  16816.9 |      5 |     69623.8 |   66094.6 |  30065   |  22138.7 | 103828   |
| Q22     | exasol    |    323   |      5 |       976.4 |     789.2 |    488.9 |    176   |   1366.9 |
| Q22     | starrocks |   1321.6 |      5 |      2068.5 |    2690.1 |   1374.6 |   1644.8 |   4973.9 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6507.6 |         79180.9 |   12.17 |      0.08 | False    |
| Q02     | exasol            | starrocks           |         557   |          2141.5 |    3.84 |      0.26 | False    |
| Q03     | exasol            | starrocks           |        4292.4 |         28039.7 |    6.53 |      0.15 | False    |
| Q04     | exasol            | starrocks           |        1181.2 |         61306.7 |   51.9  |      0.02 | False    |
| Q05     | exasol            | starrocks           |        4776.5 |         34220.2 |    7.16 |      0.14 | False    |
| Q06     | exasol            | starrocks           |         341.4 |          4103.5 |   12.02 |      0.08 | False    |
| Q07     | exasol            | starrocks           |        7067   |          7231   |    1.02 |      0.98 | False    |
| Q08     | exasol            | starrocks           |        1671.4 |         14230.4 |    8.51 |      0.12 | False    |
| Q09     | exasol            | starrocks           |       17644.7 |         25264   |    1.43 |      0.7  | False    |
| Q10     | exasol            | starrocks           |        4488.1 |         21979.5 |    4.9  |      0.2  | False    |
| Q11     | exasol            | starrocks           |        1326.8 |          1576.8 |    1.19 |      0.84 | False    |
| Q12     | exasol            | starrocks           |        1296.3 |          8436.8 |    6.51 |      0.15 | False    |
| Q13     | exasol            | starrocks           |        8908.6 |         20548.2 |    2.31 |      0.43 | False    |
| Q14     | exasol            | starrocks           |        1427   |          4663.7 |    3.27 |      0.31 | False    |
| Q15     | exasol            | starrocks           |        1425.8 |          4766.4 |    3.34 |      0.3  | False    |
| Q16     | exasol            | starrocks           |        2406.4 |          2572.5 |    1.07 |      0.94 | False    |
| Q17     | exasol            | starrocks           |         395.8 |          5475.8 |   13.83 |      0.07 | False    |
| Q18     | exasol            | starrocks           |        2586.4 |         33756.7 |   13.05 |      0.08 | False    |
| Q19     | exasol            | starrocks           |         648.4 |          4697   |    7.24 |      0.14 | False    |
| Q20     | exasol            | starrocks           |        2495.4 |          5350   |    2.14 |      0.47 | False    |
| Q21     | exasol            | starrocks           |        5373   |         69623.8 |   12.96 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         976.4 |          2068.5 |    2.12 |      0.47 | False    |

### Per-Stream Statistics

This benchmark was executed using **5 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 4504.4 | 2640.2 | 386.0 | 18756.8 |
| 1 | 22 | 4115.3 | 1869.6 | 439.8 | 13641.9 |
| 2 | 22 | 4786.4 | 1343.6 | 176.0 | 28564.3 |
| 3 | 22 | 4621.7 | 2992.4 | 229.2 | 17644.7 |
| 4 | 22 | 3358.8 | 2379.2 | 258.6 | 14774.8 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1343.6ms
- Slowest stream median: 2992.4ms
- Stream performance variation: 122.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 22 | 25100.1 | 8120.5 | 1325.3 | 174007.0 |
| 1 | 22 | 23713.3 | 7709.6 | 1252.4 | 184738.5 |
| 2 | 22 | 23023.8 | 7156.4 | 1801.8 | 185595.1 |
| 3 | 22 | 23014.1 | 16127.9 | 1388.3 | 87820.4 |
| 4 | 22 | 16054.5 | 7016.5 | 1576.8 | 79180.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 7016.5ms
- Slowest stream median: 16127.9ms
- Stream performance variation: 129.9% difference between fastest and slowest streams
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
- Median runtime: 2204.8ms
- Average runtime: 4277.3ms
- Fastest query: 176.0ms
- Slowest query: 28564.3ms

**starrocks:**
- Median runtime: 8312.5ms
- Average runtime: 22181.2ms
- Fastest query: 1252.4ms
- Slowest query: 185595.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_30g_mn_mu5-benchmark.zip`](starrocks_exa_vs_sr_30g_mn_mu5-benchmark.zip)

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
  - bucket_count: 15
  - replication_num: 1


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 5 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts