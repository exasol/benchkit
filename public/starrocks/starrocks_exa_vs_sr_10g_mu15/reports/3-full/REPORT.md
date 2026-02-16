# Exasol vs StarRocks: TPC-H SF10 (Single-Node, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 14:05:37

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 2766.6ms median runtime
- starrocks was 3.0x slower- Tested 220 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 15 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.1.8

**Software Configuration:**
- **Database:** exasol 2025.1.8
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


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
# Create GPT partition table
sudo parted /dev/nvme1n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 20GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 20GiB

# Create raw partition for Exasol (89GB)
sudo parted /dev/nvme1n1 mkpart primary 20GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 20GiB 100%

# Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

# Create storage symlink: /dev/exasol.storage -&gt; /dev/nvme1n1p2
sudo ln -sf /dev/nvme1n1p2 /dev/exasol.storage

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m -s /bin/bash exasol

# Add exasol user to sudo group
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
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;PUBLIC_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/exasol.storage
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.8
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_PLAY_DB_MEM_SIZE=12000
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
# Creating exasol user on all nodes
sudo useradd -m -s /bin/bash exasol || true

# Adding exasol to sudo group on all nodes
sudo usermod -aG sudo exasol || true

# Configuring passwordless sudo on all nodes
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



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4821CB580A22C27EE with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4821CB580A22C27EE

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4821CB580A22C27EE to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4821CB580A22C27EE /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create StarRocks data directory
sudo mkdir -p /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```

**Prerequisites:**
```bash
# Install Java, MySQL client, and utilities
sudo apt-get update &amp;&amp; sudo apt-get install -y openjdk-17-jdk curl wget mysql-client

# Set JAVA_HOME environment variable
echo &#34;export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64&#34; | sudo tee -a /etc/profile.d/java.sh

```

**Installation:**
```bash
# Download StarRocks 4.0.4
wget -q -O /tmp/starrocks-4.0.4.tar.gz https://releases.starrocks.io/starrocks/StarRocks-4.0.4-ubuntu-amd64.tar.gz

# Extract StarRocks to installation directory
sudo mkdir -p /opt/starrocks &amp;&amp; sudo tar -xzf /tmp/starrocks-4.0.4.tar.gz -C /opt/starrocks --strip-components=1

# Set StarRocks directory ownership
sudo chown -R $(whoami):$(whoami) /opt/starrocks

```

**Configuration:**
```bash
# Configure StarRocks FE
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

# Configure StarRocks BE
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
# Start StarRocks FE
cd /opt/starrocks/fe &amp;&amp; ./bin/start_fe.sh --daemon

# Start StarRocks BE
cd /opt/starrocks/be &amp;&amp; ./bin/start_be.sh --daemon

```

**Setup:**
```bash
# Execute sudo command on remote system
sudo mkdir -p /data/starrocks

```



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
unzip starrocks_exa_vs_sr_10g_mu15-benchmark.zip
cd starrocks_exa_vs_sr_10g_mu15

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
| Q01     | exasol    |   1254.4 |      5 |     11432.3 |   11448.7 |   8880.9 |   2734   |  24626.5 |
| Q01     | starrocks |   6057.6 |      5 |     31155.1 |   38366.2 |  18850.3 |  22182.3 |  69103.3 |
| Q02     | exasol    |     98.2 |      5 |       523.1 |    4337.9 |   8591.1 |    379.2 |  19705.5 |
| Q02     | starrocks |    707.9 |      5 |      1966.9 |    2327   |   1245.8 |    805.4 |   3763.8 |
| Q03     | exasol    |    447   |      5 |      3115.5 |    4274.2 |   4063.5 |   1497.2 |  11382.2 |
| Q03     | starrocks |   1744.8 |      5 |      5939.9 |    6035.2 |   1223.7 |   4276.1 |   7647.5 |
| Q04     | exasol    |     90.1 |      5 |      1550.5 |    1311.8 |    790   |    187.9 |   2300.3 |
| Q04     | starrocks |   1031.4 |      5 |      9226.2 |    7549.5 |   4477.3 |    836.6 |  12045.3 |
| Q05     | exasol    |    388.5 |      5 |      3631.7 |    6096.2 |   6092   |   2936.8 |  16974   |
| Q05     | starrocks |   1714.1 |      5 |      7086.2 |    8123   |   4143.8 |   3348   |  13818.5 |
| Q06     | exasol    |     59.2 |      5 |       591.6 |     959.4 |    900.7 |    184.2 |   2331.6 |
| Q06     | starrocks |    601.2 |      5 |      3747.8 |    6287.5 |   7083.4 |    984.7 |  18607.7 |
| Q07     | exasol    |    400.3 |      5 |     14219.6 |    9767.3 |   6969.2 |   1775.5 |  15687.5 |
| Q07     | starrocks |   2063.4 |      5 |     26109.1 |   24876.5 |   7391.2 |  13303.8 |  32230.8 |
| Q08     | exasol    |    110   |      5 |      1101.7 |    1655.1 |   1075.2 |    682.7 |   3147.7 |
| Q08     | starrocks |   1690.6 |      5 |      6835.6 |    9617.2 |   5294.5 |   5323.1 |  18142.6 |
| Q09     | exasol    |   1152.1 |      5 |     15278   |   11127.8 |   6483   |   4035.3 |  16507.1 |
| Q09     | starrocks |   3341.7 |      5 |     38198.6 |   39350.2 |   9112.6 |  27615.4 |  51258.3 |
| Q10     | exasol    |    487.5 |      5 |      4905.4 |   11173   |   9734.2 |   3447.7 |  22372.3 |
| Q10     | starrocks |   1907.5 |      5 |      6230.6 |    7571.5 |   4797.4 |   2733.5 |  12684.2 |
| Q11     | exasol    |     85.6 |      5 |       771.8 |    4181.3 |   7668.4 |    665   |  17898.5 |
| Q11     | starrocks |    404.4 |      5 |      1941.5 |    2702.5 |   2839.3 |    484.9 |   7555.6 |
| Q12     | exasol    |    120.7 |      5 |      2472.7 |    2281.3 |   1181.8 |    759.9 |   3449.8 |
| Q12     | starrocks |   1146.6 |      5 |      9312.9 |    8425   |   3418.8 |   2919.9 |  11545.2 |
| Q13     | exasol    |   1141.8 |      5 |     19279.1 |   18071.4 |   3354.3 |  13952.9 |  21045.1 |
| Q13     | starrocks |   1927.7 |      5 |     47022.2 |   42941.9 |   8846.9 |  32743.6 |  50465.7 |
| Q14     | exasol    |    108.9 |      5 |      3455.5 |    5367.5 |   5573.7 |    720.7 |  14919.6 |
| Q14     | starrocks |    845   |      5 |     13573.7 |   11808.1 |   4694.2 |   5486.5 |  17404   |
| Q15     | exasol    |    118.7 |      5 |      1861.9 |    2081.9 |   1286.9 |    621   |   4160.6 |
| Q15     | starrocks |    777.7 |      5 |      8273   |    9541   |   5720.9 |   2827.1 |  16546.1 |
| Q16     | exasol    |    453.5 |      5 |     12548.4 |   10764.6 |   9253.4 |    995.2 |  22807.5 |
| Q16     | starrocks |    697.8 |      5 |      1031.9 |    3061.7 |   3164.7 |    418   |   7120.7 |
| Q17     | exasol    |     20.3 |      5 |       312.3 |     263.4 |    130.1 |     95.4 |    387.4 |
| Q17     | starrocks |    755   |      5 |      8213.1 |    9677.6 |   5217.1 |   4706.6 |  17415.1 |
| Q18     | exasol    |    679.6 |      5 |      5013.8 |    8787.7 |   9028.5 |   1658.7 |  23654.9 |
| Q18     | starrocks |   2492.2 |      5 |     59770   |   61562.3 |  27544.8 |  20742.7 |  94639.8 |
| Q19     | exasol    |     35.7 |      5 |       730.9 |     898.3 |    785.3 |     63.3 |   2190.9 |
| Q19     | starrocks |   1461.6 |      5 |      4370.1 |    6029.3 |   4015.6 |   3064.2 |  12735.3 |
| Q20     | exasol    |    213.2 |      5 |      1612.5 |    2418.8 |   2336.7 |    451.4 |   6190.4 |
| Q20     | starrocks |    989.8 |      5 |      4877.6 |    7123.3 |   6505.7 |   1920.6 |  17970.6 |
| Q21     | exasol    |    642.9 |      5 |     12553.4 |   10326.4 |   6130   |   3140   |  15765   |
| Q21     | starrocks |   3593.2 |      5 |     55024.1 |   57175.9 |  45010.7 |   6540.8 | 112296   |
| Q22     | exasol    |    145.2 |      5 |      1473.4 |    2099.7 |   1411.2 |    557.6 |   3822.3 |
| Q22     | starrocks |    504   |      5 |      7376.4 |    7010.6 |   2609.4 |   3094.2 |   9402.2 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |       11432.3 |         31155.1 |    2.73 |      0.37 | False    |
| Q02     | exasol            | starrocks           |         523.1 |          1966.9 |    3.76 |      0.27 | False    |
| Q03     | exasol            | starrocks           |        3115.5 |          5939.9 |    1.91 |      0.52 | False    |
| Q04     | exasol            | starrocks           |        1550.5 |          9226.2 |    5.95 |      0.17 | False    |
| Q05     | exasol            | starrocks           |        3631.7 |          7086.2 |    1.95 |      0.51 | False    |
| Q06     | exasol            | starrocks           |         591.6 |          3747.8 |    6.34 |      0.16 | False    |
| Q07     | exasol            | starrocks           |       14219.6 |         26109.1 |    1.84 |      0.54 | False    |
| Q08     | exasol            | starrocks           |        1101.7 |          6835.6 |    6.2  |      0.16 | False    |
| Q09     | exasol            | starrocks           |       15278   |         38198.6 |    2.5  |      0.4  | False    |
| Q10     | exasol            | starrocks           |        4905.4 |          6230.6 |    1.27 |      0.79 | False    |
| Q11     | exasol            | starrocks           |         771.8 |          1941.5 |    2.52 |      0.4  | False    |
| Q12     | exasol            | starrocks           |        2472.7 |          9312.9 |    3.77 |      0.27 | False    |
| Q13     | exasol            | starrocks           |       19279.1 |         47022.2 |    2.44 |      0.41 | False    |
| Q14     | exasol            | starrocks           |        3455.5 |         13573.7 |    3.93 |      0.25 | False    |
| Q15     | exasol            | starrocks           |        1861.9 |          8273   |    4.44 |      0.23 | False    |
| Q16     | exasol            | starrocks           |       12548.4 |          1031.9 |    0.08 |     12.16 | True     |
| Q17     | exasol            | starrocks           |         312.3 |          8213.1 |   26.3  |      0.04 | False    |
| Q18     | exasol            | starrocks           |        5013.8 |         59770   |   11.92 |      0.08 | False    |
| Q19     | exasol            | starrocks           |         730.9 |          4370.1 |    5.98 |      0.17 | False    |
| Q20     | exasol            | starrocks           |        1612.5 |          4877.6 |    3.02 |      0.33 | False    |
| Q21     | exasol            | starrocks           |       12553.4 |         55024.1 |    4.38 |      0.23 | False    |
| Q22     | exasol            | starrocks           |        1473.4 |          7376.4 |    5.01 |      0.2  | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 3706.0 | 2270.1 | 720.7 | 13952.9 |
| 1 | 8 | 6931.3 | 2152.8 | 63.3 | 21018.4 |
| 10 | 7 | 6011.9 | 1738.0 | 387.4 | 21045.1 |
| 11 | 7 | 1993.3 | 1473.4 | 557.6 | 4160.6 |
| 12 | 7 | 8044.6 | 2799.2 | 187.9 | 19705.5 |
| 13 | 7 | 7692.1 | 3888.6 | 184.2 | 15769.3 |
| 14 | 7 | 7284.5 | 1775.5 | 591.6 | 24626.5 |
| 2 | 8 | 4772.8 | 3234.9 | 156.7 | 14516.8 |
| 3 | 8 | 6699.9 | 3984.7 | 780.5 | 17898.5 |
| 4 | 8 | 5000.0 | 2450.4 | 365.2 | 15765.0 |
| 5 | 7 | 7374.2 | 4049.2 | 1840.5 | 21251.0 |
| 6 | 7 | 5269.0 | 3447.7 | 665.0 | 22372.3 |
| 7 | 7 | 5168.8 | 2587.4 | 523.1 | 23654.9 |
| 8 | 7 | 6922.1 | 3140.0 | 95.4 | 16507.1 |
| 9 | 7 | 5895.1 | 2331.6 | 297.2 | 22807.5 |

**Performance Analysis for Exasol:**
- Fastest stream median: 1473.4ms
- Slowest stream median: 4049.2ms
- Stream performance variation: 174.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 17211.8 | 7776.9 | 916.6 | 55703.0 |
| 1 | 8 | 18040.3 | 9474.2 | 2802.5 | 47022.2 |
| 10 | 7 | 13799.2 | 14193.7 | 3282.8 | 34028.5 |
| 11 | 7 | 14225.4 | 12045.3 | 5951.0 | 32230.8 |
| 12 | 7 | 21663.2 | 20742.7 | 836.6 | 59770.0 |
| 13 | 7 | 16524.2 | 7086.2 | 2733.5 | 34797.2 |
| 14 | 7 | 17203.5 | 11364.1 | 2579.9 | 50449.4 |
| 2 | 8 | 18170.1 | 8721.2 | 3094.2 | 69103.3 |
| 3 | 8 | 13271.7 | 8679.0 | 2614.0 | 38198.6 |
| 4 | 8 | 17724.2 | 5996.9 | 484.9 | 112296.5 |
| 5 | 7 | 21860.5 | 10264.4 | 418.0 | 91324.1 |
| 6 | 7 | 8650.8 | 8273.0 | 3624.2 | 12684.2 |
| 7 | 7 | 19837.6 | 5865.0 | 805.4 | 94639.8 |
| 8 | 7 | 21683.9 | 12290.1 | 1966.9 | 55024.1 |
| 9 | 7 | 17475.8 | 7120.7 | 2827.1 | 76955.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 5865.0ms
- Slowest stream median: 20742.7ms
- Stream performance variation: 253.7% difference between fastest and slowest streams
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
- Median runtime: 2766.6ms
- Average runtime: 5895.2ms
- Fastest query: 63.3ms
- Slowest query: 24626.5ms

**starrocks:**
- Median runtime: 8243.0ms
- Average runtime: 17143.8ms
- Fastest query: 418.0ms
- Slowest query: 112296.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_10g_mu15-benchmark.zip`](starrocks_exa_vs_sr_10g_mu15-benchmark.zip)

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