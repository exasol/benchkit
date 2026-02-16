# Exasol vs StarRocks: TPC-H SF1 (Single-Node, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.large
**Date:** 2026-01-21 11:11:04

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 561.7ms median runtime
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

# Create 3GB partition for data generation
sudo parted /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 3GiB

# Create raw partition for Exasol (106GB)
sudo parted /dev/nvme1n1 mkpart primary 3GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme1n1 mkpart primary 3GiB 100%

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
CCC_PLAY_DB_MEM_SIZE=8000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4EC833FD20D46B898 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4EC833FD20D46B898

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4EC833FD20D46B898 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4EC833FD20D46B898 /data

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
unzip starrocks_exa_vs_sr_1g_mu15-benchmark.zip
cd starrocks_exa_vs_sr_1g_mu15

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
| Q01     | exasol    |    135.4 |      5 |      1771.3 |    1852.1 |    711.9 |   1034.3 |   2915   |
| Q01     | starrocks |    803.2 |      5 |      2234.5 |    2344.1 |   1437   |    865.7 |   4300.1 |
| Q02     | exasol    |     60   |      5 |       580.7 |     707.6 |    440.3 |    239.1 |   1184.1 |
| Q02     | starrocks |    464.4 |      5 |      1318.4 |    1242.7 |    646.1 |    485.4 |   2012.8 |
| Q03     | exasol    |     53.1 |      5 |       587.9 |     861.7 |    627.8 |    384.2 |   1921.8 |
| Q03     | starrocks |    272.5 |      5 |      1049.7 |    1238.3 |    577.3 |    708.5 |   2160.2 |
| Q04     | exasol    |     19.2 |      5 |       388.5 |     422.5 |    238.3 |    105   |    715.4 |
| Q04     | starrocks |    183.1 |      5 |      1078.3 |    1345.7 |   1131.6 |    177.1 |   3154.8 |
| Q05     | exasol    |     59.6 |      5 |      1161   |    1163.1 |    925.5 |     46.7 |   2384.2 |
| Q05     | starrocks |    294.8 |      5 |      1929.5 |    1541.2 |   1015.7 |    375   |   2549   |
| Q06     | exasol    |     11.6 |      5 |       100.4 |     103.9 |     84.4 |     11.5 |    207.7 |
| Q06     | starrocks |     84.3 |      5 |      1184.6 |    1628.5 |   1268.8 |    539.9 |   3468.1 |
| Q07     | exasol    |     51.1 |      5 |       912.2 |     849   |    296.1 |    366.6 |   1151.6 |
| Q07     | starrocks |    272.9 |      5 |      3971.3 |    3665.4 |    900   |   2391.5 |   4713.3 |
| Q08     | exasol    |     26.4 |      5 |       542.7 |     610.1 |    467.7 |     26.6 |   1211.9 |
| Q08     | starrocks |    287.6 |      5 |      2564.4 |    2050.8 |    849.8 |    908.9 |   2826.9 |
| Q09     | exasol    |    114.6 |      5 |      2465.3 |    2410.5 |    659.4 |   1360.8 |   3165.7 |
| Q09     | starrocks |    379.6 |      5 |      2571.3 |    2134.8 |    781.5 |    938   |   2750.5 |
| Q10     | exasol    |     57.1 |      5 |      1229.2 |    1290.1 |    385.9 |    765.1 |   1701.9 |
| Q10     | starrocks |    318.1 |      5 |      2671.1 |    2134.8 |   1538.2 |    368.8 |   3843.4 |
| Q11     | exasol    |     24.5 |      5 |       216.4 |     261   |    187.6 |     23.7 |    510.9 |
| Q11     | starrocks |    123.1 |      5 |       609.9 |     810.8 |    510.8 |    308.3 |   1453.3 |
| Q12     | exasol    |     22.1 |      5 |       539.1 |     450   |    269.8 |     21.5 |    694   |
| Q12     | starrocks |    190.4 |      5 |      2657.5 |    2394.6 |   1222.5 |    861.9 |   3982   |
| Q13     | exasol    |    121.3 |      5 |      3578.1 |    4786   |   4037.2 |   1062   |  11682.7 |
| Q13     | starrocks |    389.1 |      5 |      1527   |    1440.6 |    432   |    736   |   1868.3 |
| Q14     | exasol    |     17.9 |      5 |       311   |     299.9 |    178.9 |     17.7 |    504   |
| Q14     | starrocks |    117.8 |      5 |      1913.3 |    2352.9 |   1294.5 |   1092.5 |   3885.5 |
| Q15     | exasol    |     25.4 |      5 |       434.1 |     634.4 |    618.7 |    172   |   1720.1 |
| Q15     | starrocks |    149.7 |      5 |      1964   |    1983.9 |   1115.1 |    380.7 |   3236.6 |
| Q16     | exasol    |    101.7 |      5 |      1182.5 |    1477.5 |   1368.4 |    464.5 |   3815.4 |
| Q16     | starrocks |    349.9 |      5 |       874.6 |     909.7 |    454.2 |    283.6 |   1390.3 |
| Q17     | exasol    |     12.2 |      5 |       238.2 |     193   |     85.2 |     82.5 |    280.2 |
| Q17     | starrocks |    178.9 |      5 |      2125.2 |    1748   |   1385.3 |    233.6 |   3170.9 |
| Q18     | exasol    |     82   |      5 |      1284.6 |    1241.9 |    792.5 |     81.4 |   1985.5 |
| Q18     | starrocks |    275.4 |      5 |      5408.4 |    5560.1 |   1229.8 |   4364.3 |   7411.9 |
| Q19     | exasol    |     12   |      5 |       242.8 |     264.8 |    179.6 |     20.5 |    462.4 |
| Q19     | starrocks |    135.4 |      5 |      1747.5 |    1673.1 |    659.1 |    619.3 |   2239.3 |
| Q20     | exasol    |     32.7 |      5 |       459.2 |     442.3 |    172.2 |    245   |    694.4 |
| Q20     | starrocks |    222.6 |      5 |      1728.6 |    2250.2 |    818.7 |   1687   |   3533.5 |
| Q21     | exasol    |     69.1 |      5 |      1306.1 |    1190.3 |    511.6 |    640.9 |   1901.1 |
| Q21     | starrocks |    486.2 |      5 |      7698.2 |    6297.8 |   4997   |   1035.7 |  12984.7 |
| Q22     | exasol    |     24.2 |      5 |       478.4 |     647.3 |    379.6 |    344.9 |   1270.6 |
| Q22     | starrocks |     84.8 |      5 |       533   |     662.8 |    446.8 |    246.5 |   1425.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        1771.3 |          2234.5 |    1.26 |      0.79 | False    |
| Q02     | exasol            | starrocks           |         580.7 |          1318.4 |    2.27 |      0.44 | False    |
| Q03     | exasol            | starrocks           |         587.9 |          1049.7 |    1.79 |      0.56 | False    |
| Q04     | exasol            | starrocks           |         388.5 |          1078.3 |    2.78 |      0.36 | False    |
| Q05     | exasol            | starrocks           |        1161   |          1929.5 |    1.66 |      0.6  | False    |
| Q06     | exasol            | starrocks           |         100.4 |          1184.6 |   11.8  |      0.08 | False    |
| Q07     | exasol            | starrocks           |         912.2 |          3971.3 |    4.35 |      0.23 | False    |
| Q08     | exasol            | starrocks           |         542.7 |          2564.4 |    4.73 |      0.21 | False    |
| Q09     | exasol            | starrocks           |        2465.3 |          2571.3 |    1.04 |      0.96 | False    |
| Q10     | exasol            | starrocks           |        1229.2 |          2671.1 |    2.17 |      0.46 | False    |
| Q11     | exasol            | starrocks           |         216.4 |           609.9 |    2.82 |      0.35 | False    |
| Q12     | exasol            | starrocks           |         539.1 |          2657.5 |    4.93 |      0.2  | False    |
| Q13     | exasol            | starrocks           |        3578.1 |          1527   |    0.43 |      2.34 | True     |
| Q14     | exasol            | starrocks           |         311   |          1913.3 |    6.15 |      0.16 | False    |
| Q15     | exasol            | starrocks           |         434.1 |          1964   |    4.52 |      0.22 | False    |
| Q16     | exasol            | starrocks           |        1182.5 |           874.6 |    0.74 |      1.35 | True     |
| Q17     | exasol            | starrocks           |         238.2 |          2125.2 |    8.92 |      0.11 | False    |
| Q18     | exasol            | starrocks           |        1284.6 |          5408.4 |    4.21 |      0.24 | False    |
| Q19     | exasol            | starrocks           |         242.8 |          1747.5 |    7.2  |      0.14 | False    |
| Q20     | exasol            | starrocks           |         459.2 |          1728.6 |    3.76 |      0.27 | False    |
| Q21     | exasol            | starrocks           |        1306.1 |          7698.2 |    5.89 |      0.17 | False    |
| Q22     | exasol            | starrocks           |         478.4 |           533   |    1.11 |      0.9  | False    |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 1489.0 | 25.1 | 11.5 | 11682.7 |
| 1 | 8 | 1079.0 | 484.5 | 20.5 | 4235.3 |
| 10 | 7 | 883.7 | 462.4 | 238.2 | 3578.1 |
| 11 | 7 | 736.2 | 715.4 | 182.0 | 1270.6 |
| 12 | 7 | 1153.2 | 995.9 | 105.0 | 2465.3 |
| 13 | 7 | 1131.8 | 1062.0 | 32.3 | 2384.2 |
| 14 | 7 | 1243.8 | 416.1 | 100.4 | 3371.7 |
| 2 | 8 | 969.9 | 663.2 | 280.2 | 2093.0 |
| 3 | 8 | 951.7 | 599.0 | 178.1 | 2663.6 |
| 4 | 8 | 719.3 | 526.8 | 82.5 | 1398.8 |
| 5 | 7 | 1152.8 | 640.9 | 314.6 | 2397.1 |
| 6 | 7 | 827.4 | 765.1 | 216.4 | 1720.1 |
| 7 | 7 | 708.9 | 488.0 | 242.8 | 1985.5 |
| 8 | 7 | 1049.1 | 744.9 | 123.0 | 3165.7 |
| 9 | 7 | 987.7 | 527.4 | 167.6 | 3815.4 |

**Performance Analysis for Exasol:**
- Fastest stream median: 25.1ms
- Slowest stream median: 1062.0ms
- Stream performance variation: 4122.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 2130.0 | 1700.4 | 573.3 | 5408.4 |
| 1 | 8 | 1811.6 | 1619.0 | 736.0 | 4713.3 |
| 10 | 7 | 2073.6 | 1747.5 | 1318.4 | 3533.5 |
| 11 | 7 | 1980.6 | 2208.2 | 533.0 | 3236.6 |
| 12 | 7 | 2526.1 | 1743.1 | 177.1 | 6029.1 |
| 13 | 7 | 2072.4 | 2313.3 | 539.9 | 4085.2 |
| 14 | 7 | 2107.7 | 2239.3 | 1184.6 | 2612.3 |
| 2 | 8 | 1954.6 | 2365.9 | 246.5 | 3201.4 |
| 3 | 8 | 1924.7 | 1571.5 | 375.0 | 4300.1 |
| 4 | 8 | 2194.6 | 646.6 | 308.3 | 12984.7 |
| 5 | 7 | 2590.0 | 1035.7 | 283.6 | 8165.7 |
| 6 | 7 | 2080.1 | 1572.9 | 609.9 | 3982.0 |
| 7 | 7 | 2229.1 | 1092.5 | 380.7 | 7411.9 |
| 8 | 7 | 2533.7 | 2012.8 | 233.6 | 7698.2 |
| 9 | 7 | 2225.3 | 2376.4 | 515.4 | 4586.6 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 646.6ms
- Slowest stream median: 2376.4ms
- Stream performance variation: 267.5% difference between fastest and slowest streams
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
- Median runtime: 561.7ms
- Average runtime: 1007.2ms
- Fastest query: 11.5ms
- Slowest query: 11682.7ms

**starrocks:**
- Median runtime: 1688.3ms
- Average runtime: 2155.0ms
- Fastest query: 177.1ms
- Slowest query: 12984.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_1g_mu15-benchmark.zip`](starrocks_exa_vs_sr_1g_mu15-benchmark.zip)

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