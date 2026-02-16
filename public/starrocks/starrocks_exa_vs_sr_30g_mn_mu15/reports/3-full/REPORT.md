# Exasol vs StarRocks: TPC-H SF30 (Multi-Node 3, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 16:07:06

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 4041.0ms median runtime
- starrocks was 6.3x slower- Tested 220 total query executions across 22 different TPC-H queries
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
# [All 3 Nodes] Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2A1205FC8F52438CF with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2A1205FC8F52438CF

# [All 3 Nodes] Create mount point /data
sudo mkdir -p /data

# [All 3 Nodes] Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2A1205FC8F52438CF to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2A1205FC8F52438CF /data

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
- **Execution mode:** Multiuser (15 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip starrocks_exa_vs_sr_30g_mn_mu15-benchmark.zip
cd starrocks_exa_vs_sr_30g_mn_mu15

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
| Q01     | exasol    |   1276.9 |      5 |      6866.8 |   16459.9 |  16535.9 |   4827.3 |  43663.7 |
| Q01     | starrocks |  17636.5 |      5 |    226415   |  178553   | 128537   |  22693   | 300119   |
| Q02     | exasol    |    113.6 |      5 |      1073   |     916.2 |    313.4 |    520.4 |   1190.2 |
| Q02     | starrocks |   1086.6 |      5 |      4435.5 |    6097.8 |   3426.7 |   2964.3 |  10766.9 |
| Q03     | exasol    |   1176.4 |      5 |      5297.4 |   12615   |  13120   |   3253.3 |  34114.1 |
| Q03     | starrocks |   6600.8 |      5 |     28330.8 |   32548.4 |  10151.1 |  23845.3 |  48656.7 |
| Q04     | exasol    |    290   |      5 |      2131.4 |    2593   |   1721.7 |    980.1 |   5398.6 |
| Q04     | starrocks |   4778.5 |      5 |    300032   |  270933   |  55007.4 | 173675   | 300111   |
| Q05     | exasol    |   1121.1 |      5 |     30751.5 |   21436   |  17778.5 |   2132.2 |  40632.2 |
| Q05     | starrocks |   5898   |      5 |     31095.5 |   68963.4 |  63291.4 |  15176.2 | 149061   |
| Q06     | exasol    |     69.9 |      5 |       554.9 |    1249.2 |   1828.8 |    157.7 |   4507.3 |
| Q06     | starrocks |   2416.6 |      5 |      6366.9 |   14540.7 |  19750.6 |   2838.2 |  49366.2 |
| Q07     | exasol    |   1397.2 |      5 |     29359.7 |   33462   |   9817.1 |  24700.6 |  46269.7 |
| Q07     | starrocks |   4635.1 |      5 |     45919.2 |   55023.9 |  38543.9 |   9335.7 |  97849.7 |
| Q08     | exasol    |    456.2 |      5 |      4961.1 |   10746.7 |  15617   |    641.7 |  38488.4 |
| Q08     | starrocks |   5642   |      5 |     16473.3 |   17340.9 |   4469.9 |  12876.5 |  23682.2 |
| Q09     | exasol    |   3716.1 |      5 |     45606.7 |   45170.8 |   6678.9 |  36943.8 |  54180   |
| Q09     | starrocks |   9924.8 |      5 |     39890.6 |   45252.3 |  18443.9 |  27353.3 |  66206   |
| Q10     | exasol    |    864.8 |      5 |     34500.5 |   29903.3 |  14660.4 |   4309.1 |  40045.7 |
| Q10     | starrocks |   9643.5 |      5 |     31651.7 |   31568.2 |   4974.4 |  26354.2 |  37103.5 |
| Q11     | exasol    |   1774.6 |      5 |      1969.4 |    2191.5 |   1099.4 |    605.7 |   3313.4 |
| Q11     | starrocks |    786.6 |      5 |      1898.2 |    3170.4 |   2963.3 |   1365   |   8401.1 |
| Q12     | exasol    |    431.7 |      5 |      4280.2 |    5475.4 |   5741.9 |    932.8 |  15312.2 |
| Q12     | starrocks |   3514.8 |      5 |     23592.4 |   25560.1 |  16452.3 |   9921.2 |  47120.4 |
| Q13     | exasol    |   2473.2 |      5 |     35692.7 |   51773.8 |  36342.1 |  31801.8 | 116417   |
| Q13     | starrocks |   7214.3 |      5 |    157089   |  131200   |  62315.9 |  20255.4 | 165099   |
| Q14     | exasol    |    897.6 |      5 |      2628.7 |    9397.1 |   9912.1 |   1379   |  21094   |
| Q14     | starrocks |   3256   |      5 |     17007.7 |   20038.6 |  11810.3 |   7050.4 |  35534.2 |
| Q15     | exasol    |    346.3 |      5 |      3635.8 |    5397.5 |   5380.8 |   1759.3 |  14907.6 |
| Q15     | starrocks |   2638.7 |      5 |     17646.9 |   21020.3 |  11088.5 |  13885.8 |  40557.2 |
| Q16     | exasol    |    573.1 |      5 |     14140.7 |   17233.5 |  14931   |   1513.2 |  34218.7 |
| Q16     | starrocks |   1518.9 |      5 |      5289.7 |    5306.1 |   3284   |   1229.9 |  10267.1 |
| Q17     | exasol    |     85.2 |      5 |       583.3 |     564.9 |    196.3 |    342.3 |    864.7 |
| Q17     | starrocks |   3104.4 |      5 |     36337.6 |   34307.1 |  15584.4 |  11611   |  48433.1 |
| Q18     | exasol    |    732.5 |      5 |      3939.8 |   13455.4 |  14296.4 |   2089.1 |  29180.6 |
| Q18     | starrocks |  11100   |      5 |    107288   |  100510   |  15628.9 |  75837.7 | 115660   |
| Q19     | exasol    |    111.5 |      5 |       903.6 |     773.3 |    427.4 |    190.4 |   1322.4 |
| Q19     | starrocks |   3467.6 |      5 |      9965.9 |    9132.5 |   4415.5 |   3485.6 |  15334.1 |
| Q20     | exasol    |    403   |      5 |      3869.3 |    6296.5 |   7902.9 |    888   |  20259.8 |
| Q20     | starrocks |   3404   |      5 |     15966   |   20054.6 |  22140.1 |   3984.1 |  58150.9 |
| Q21     | exasol    |  16412   |      5 |     15371.8 |   21678.6 |  16491.3 |   2844.6 |  39902.2 |
| Q21     | starrocks |  18091.8 |      5 |     91833.4 |  128740   |  68484.7 |  59895.5 | 218487   |
| Q22     | exasol    |    165.2 |      5 |      1000.7 |    1267.3 |    664   |    632.3 |   2190.2 |
| Q22     | starrocks |   1306.2 |      5 |     12311.4 |   12843.2 |   7992.1 |   4923.9 |  25374.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        6866.8 |        226415   |   32.97 |      0.03 | False    |
| Q02     | exasol            | starrocks           |        1073   |          4435.5 |    4.13 |      0.24 | False    |
| Q03     | exasol            | starrocks           |        5297.4 |         28330.8 |    5.35 |      0.19 | False    |
| Q04     | exasol            | starrocks           |        2131.4 |        300032   |  140.77 |      0.01 | False    |
| Q05     | exasol            | starrocks           |       30751.5 |         31095.5 |    1.01 |      0.99 | False    |
| Q06     | exasol            | starrocks           |         554.9 |          6366.9 |   11.47 |      0.09 | False    |
| Q07     | exasol            | starrocks           |       29359.7 |         45919.2 |    1.56 |      0.64 | False    |
| Q08     | exasol            | starrocks           |        4961.1 |         16473.3 |    3.32 |      0.3  | False    |
| Q09     | exasol            | starrocks           |       45606.7 |         39890.6 |    0.87 |      1.14 | True     |
| Q10     | exasol            | starrocks           |       34500.5 |         31651.7 |    0.92 |      1.09 | True     |
| Q11     | exasol            | starrocks           |        1969.4 |          1898.2 |    0.96 |      1.04 | True     |
| Q12     | exasol            | starrocks           |        4280.2 |         23592.4 |    5.51 |      0.18 | False    |
| Q13     | exasol            | starrocks           |       35692.7 |        157089   |    4.4  |      0.23 | False    |
| Q14     | exasol            | starrocks           |        2628.7 |         17007.7 |    6.47 |      0.15 | False    |
| Q15     | exasol            | starrocks           |        3635.8 |         17646.9 |    4.85 |      0.21 | False    |
| Q16     | exasol            | starrocks           |       14140.7 |          5289.7 |    0.37 |      2.67 | True     |
| Q17     | exasol            | starrocks           |         583.3 |         36337.6 |   62.3  |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3939.8 |        107288   |   27.23 |      0.04 | False    |
| Q19     | exasol            | starrocks           |         903.6 |          9965.9 |   11.03 |      0.09 | False    |
| Q20     | exasol            | starrocks           |        3869.3 |         15966   |    4.13 |      0.24 | False    |
| Q21     | exasol            | starrocks           |       15371.8 |         91833.4 |    5.97 |      0.17 | False    |
| Q22     | exasol            | starrocks           |        1000.7 |         12311.4 |   12.3  |      0.08 | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 15665.4 | 1639.8 | 157.7 | 116417.2 |
| 1 | 8 | 14887.8 | 3830.6 | 190.4 | 46269.7 |
| 10 | 7 | 9013.4 | 1759.3 | 587.2 | 35692.7 |
| 11 | 7 | 12922.3 | 1000.7 | 540.8 | 41486.1 |
| 12 | 7 | 12223.0 | 3939.8 | 520.4 | 40776.8 |
| 13 | 7 | 15814.6 | 4309.1 | 554.9 | 45606.7 |
| 14 | 7 | 16144.9 | 5089.9 | 457.5 | 43663.7 |
| 2 | 8 | 13495.6 | 5914.0 | 342.3 | 38488.4 |
| 3 | 8 | 13492.9 | 4553.8 | 2548.9 | 54180.0 |
| 4 | 8 | 12773.1 | 4751.7 | 583.3 | 38627.0 |
| 5 | 7 | 17285.9 | 5398.6 | 1513.2 | 38124.5 |
| 6 | 7 | 16435.9 | 15312.2 | 2131.4 | 40045.7 |
| 7 | 7 | 8685.9 | 3882.9 | 909.4 | 29018.8 |
| 8 | 7 | 16703.5 | 12150.1 | 447.1 | 48346.7 |
| 9 | 7 | 15880.0 | 4507.3 | 568.8 | 40632.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1000.7ms
- Slowest stream median: 15312.2ms
- Stream performance variation: 1430.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 43858.5 | 16740.5 | 1898.2 | 165098.9 |
| 1 | 8 | 66208.1 | 15681.1 | 3485.6 | 280774.6 |
| 10 | 7 | 47651.2 | 48433.1 | 4435.5 | 149828.4 |
| 11 | 7 | 60441.0 | 23684.4 | 6709.1 | 300072.5 |
| 12 | 7 | 69137.8 | 75837.7 | 2964.3 | 173674.8 |
| 13 | 7 | 55110.4 | 35897.1 | 6366.9 | 149060.8 |
| 14 | 7 | 71812.8 | 15334.1 | 2838.2 | 282750.8 |
| 2 | 8 | 60538.5 | 28017.1 | 4923.9 | 300119.4 |
| 3 | 8 | 63811.8 | 32845.3 | 8401.1 | 226414.9 |
| 4 | 8 | 37491.9 | 10766.1 | 1560.7 | 218487.3 |
| 5 | 7 | 76043.1 | 29525.7 | 1229.9 | 300111.2 |
| 6 | 7 | 63639.0 | 26834.7 | 1365.0 | 300032.5 |
| 7 | 7 | 31343.5 | 17150.5 | 9965.9 | 115659.8 |
| 8 | 7 | 61177.7 | 48331.6 | 3653.3 | 184050.3 |
| 9 | 7 | 33393.6 | 25374.8 | 3995.8 | 95208.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 10766.1ms
- Slowest stream median: 75837.7ms
- Stream performance variation: 604.4% difference between fastest and slowest streams
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
- Median runtime: 4041.0ms
- Average runtime: 14093.5ms
- Fastest query: 157.7ms
- Slowest query: 116417.2ms

**starrocks:**
- Median runtime: 25564.4ms
- Average runtime: 56032.0ms
- Fastest query: 1229.9ms
- Slowest query: 300119.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_30g_mn_mu15-benchmark.zip`](starrocks_exa_vs_sr_30g_mn_mu15-benchmark.zip)

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
- Measured runs executed across 15 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts