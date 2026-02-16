# Exasol vs StarRocks: TPC-H SF30 (Single-Node, 15 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-01-21 15:13:11

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **exasol**
- **starrocks**

**Key Findings:**
- exasol was the fastest overall with 4532.4ms median runtime
- starrocks was 1.8x slower- Tested 220 total query executions across 22 different TPC-H queries
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
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-250

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-251


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.xlarge
- **Starrocks Instance:** r6id.xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.8 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted /dev/nvme0n1 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mklabel gpt

# Create 48GB partition for data generation
sudo parted /dev/nvme0n1 mkpart primary ext4 1MiB 48GiB

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary ext4 1MiB 48GiB

# Create raw partition for Exasol (172GB)
sudo parted /dev/nvme0n1 mkpart primary 48GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/nvme0n1 mkpart primary 48GiB 100%

# Format /dev/nvme0n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme0n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme0n1p1 to /data
sudo mount /dev/nvme0n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

# Create storage symlink: /dev/exasol.storage -&gt; /dev/nvme0n1p2
sudo ln -sf /dev/nvme0n1p2 /dev/exasol.storage

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
CCC_PLAY_DB_MEM_SIZE=28000
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS469AAFA40E79D7C5D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS469AAFA40E79D7C5D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS469AAFA40E79D7C5D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS469AAFA40E79D7C5D /data

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
unzip starrocks_exa_vs_sr_30g_mu15-benchmark.zip
cd starrocks_exa_vs_sr_30g_mu15

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
| Q01     | exasol    |   1886.2 |      5 |     20282.5 |   18852.6 |   5254.6 |  11569.5 |  24712.8 |
| Q01     | starrocks |   8645   |      5 |    109887   |  107173   |  66694.6 |  27156.3 | 203874   |
| Q02     | exasol    |     88.5 |      5 |       669.2 |     680.1 |    136   |    559.3 |    904.5 |
| Q02     | starrocks |    606.9 |      5 |      1835.6 |    2024.9 |    588.1 |   1615.7 |   3056.7 |
| Q03     | exasol    |    733.3 |      5 |     17468   |   13871.6 |   7186.2 |   3485.3 |  20076.1 |
| Q03     | starrocks |   3110.1 |      5 |     12973.6 |   15272.6 |   4767.5 |  11034.1 |  23061.7 |
| Q04     | exasol    |    132.3 |      5 |      2456.7 |    2422.6 |   1119.1 |    790.5 |   3933.9 |
| Q04     | starrocks |   1596.1 |      5 |      3956.3 |    7771.6 |   8457.9 |   2071.2 |  22498.6 |
| Q05     | exasol    |    578.8 |      5 |     15414.4 |   13266.9 |   7242.7 |    550   |  18212.4 |
| Q05     | starrocks |   2827.3 |      5 |     19796   |   41550.4 |  38142.8 |  11406.8 |  92309.1 |
| Q06     | exasol    |     86.7 |      5 |      1840.9 |    1652.5 |   1401.8 |     85.1 |   3253   |
| Q06     | starrocks |   1327   |      5 |      2996.4 |    6960.1 |   7971   |   1812.9 |  20931.6 |
| Q07     | exasol    |    739.8 |      5 |     20826.6 |   18208.8 |   4661.1 |  11352.9 |  21884.2 |
| Q07     | starrocks |   3634.3 |      5 |     19369.9 |   21031.1 |  13250.7 |   8238   |  36746.1 |
| Q08     | exasol    |    168.6 |      5 |      2753.8 |    2362.5 |   1276.1 |    195.6 |   3379.2 |
| Q08     | starrocks |   2667.4 |      5 |      6262.9 |    6922   |   4179   |   2785.7 |  13845.3 |
| Q09     | exasol    |   2544.6 |      5 |     33013.6 |   34024.4 |   8801.9 |  24829.1 |  43571.1 |
| Q09     | starrocks |   5941.6 |      5 |     90882   |   77326.4 |  49751.2 |  10944.6 | 139073   |
| Q10     | exasol    |    796.6 |      5 |     17804.2 |   18856.9 |   2392.9 |  16688.8 |  22772.5 |
| Q10     | starrocks |   2766.3 |      5 |     18506.5 |   21646   |  17666.5 |   3850   |  51013.8 |
| Q11     | exasol    |    151.2 |      5 |      1540.8 |    1393.7 |    736.1 |    166   |   2042.9 |
| Q11     | starrocks |    365.5 |      5 |      1301.1 |    1628.3 |   1134.6 |    551   |   3198.6 |
| Q12     | exasol    |    178.5 |      5 |      5152.2 |    5159.4 |   3954.2 |    308.5 |  11137   |
| Q12     | starrocks |   1773.6 |      5 |     10671.9 |   13323.1 |   9174.1 |   2146.9 |  22804.6 |
| Q13     | exasol    |   1792.4 |      5 |     27910.7 |   35756.7 |  31681.1 |   8330.3 |  90350.8 |
| Q13     | starrocks |   3903.7 |      5 |     80256.9 |   63855.4 |  27283.2 |  23270.2 |  84196.7 |
| Q14     | exasol    |    176.2 |      5 |      3175.4 |    3018.7 |   2200.3 |    274.2 |   6249.9 |
| Q14     | starrocks |   1374   |      5 |      7840.3 |   11794   |  10402.3 |   2315.7 |  28550.7 |
| Q15     | exasol    |    408.4 |      5 |      5012.5 |    8386.6 |   6790   |   3119.7 |  18904.3 |
| Q15     | starrocks |   1350.6 |      5 |      4893.5 |    8440.7 |  11287   |   1498.9 |  28342   |
| Q16     | exasol    |    678.2 |      5 |     11545.6 |    9369.1 |   6587.5 |   1901   |  15399.3 |
| Q16     | starrocks |    933.8 |      5 |      1315.5 |    3154.5 |   3980.9 |   1067.4 |  10247.1 |
| Q17     | exasol    |     28.3 |      5 |       364.5 |     402.8 |    200.9 |    155.4 |    681.5 |
| Q17     | starrocks |   1360.6 |      5 |      1984.8 |    2683.3 |   1225.2 |   1502   |   4287.2 |
| Q18     | exasol    |   1141   |      5 |     18005.4 |   13353.5 |   9175.7 |   1187.2 |  21300.2 |
| Q18     | starrocks |   4639.7 |      5 |     23613.1 |   49998.9 |  63319.5 |  12546.4 | 162713   |
| Q19     | exasol    |     53.5 |      5 |      1428.1 |    1373.7 |    257.9 |   1120.7 |   1735.2 |
| Q19     | starrocks |   2250.1 |      5 |      3218.3 |    4309   |   2333.2 |   2029.9 |   7178   |
| Q20     | exasol    |    370   |      5 |      4872.1 |    6913.5 |   5846.9 |   1806.3 |  16430.9 |
| Q20     | starrocks |   1952.3 |      5 |      3996.2 |    9267.1 |  13458.2 |   2073.2 |  33287.3 |
| Q21     | exasol    |   1062.7 |      5 |     19181.3 |   15049.9 |   7837.1 |   6401.7 |  23308.4 |
| Q21     | starrocks |   9566.9 |      5 |     59616.1 |  102182   |  86402.6 |  43454.8 | 249316   |
| Q22     | exasol    |    229.7 |      5 |      2831   |    2847.7 |    859.1 |   1953   |   4192.7 |
| Q22     | starrocks |    659.5 |      5 |      1893.1 |    2341.4 |   1149.6 |   1368.5 |   4235.5 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |       20282.5 |        109887   |    5.42 |      0.18 | False    |
| Q02     | exasol            | starrocks           |         669.2 |          1835.6 |    2.74 |      0.36 | False    |
| Q03     | exasol            | starrocks           |       17468   |         12973.6 |    0.74 |      1.35 | True     |
| Q04     | exasol            | starrocks           |        2456.7 |          3956.3 |    1.61 |      0.62 | False    |
| Q05     | exasol            | starrocks           |       15414.4 |         19796   |    1.28 |      0.78 | False    |
| Q06     | exasol            | starrocks           |        1840.9 |          2996.4 |    1.63 |      0.61 | False    |
| Q07     | exasol            | starrocks           |       20826.6 |         19369.9 |    0.93 |      1.08 | True     |
| Q08     | exasol            | starrocks           |        2753.8 |          6262.9 |    2.27 |      0.44 | False    |
| Q09     | exasol            | starrocks           |       33013.6 |         90882   |    2.75 |      0.36 | False    |
| Q10     | exasol            | starrocks           |       17804.2 |         18506.5 |    1.04 |      0.96 | False    |
| Q11     | exasol            | starrocks           |        1540.8 |          1301.1 |    0.84 |      1.18 | True     |
| Q12     | exasol            | starrocks           |        5152.2 |         10671.9 |    2.07 |      0.48 | False    |
| Q13     | exasol            | starrocks           |       27910.7 |         80256.9 |    2.88 |      0.35 | False    |
| Q14     | exasol            | starrocks           |        3175.4 |          7840.3 |    2.47 |      0.41 | False    |
| Q15     | exasol            | starrocks           |        5012.5 |          4893.5 |    0.98 |      1.02 | True     |
| Q16     | exasol            | starrocks           |       11545.6 |          1315.5 |    0.11 |      8.78 | True     |
| Q17     | exasol            | starrocks           |         364.5 |          1984.8 |    5.45 |      0.18 | False    |
| Q18     | exasol            | starrocks           |       18005.4 |         23613.1 |    1.31 |      0.76 | False    |
| Q19     | exasol            | starrocks           |        1428.1 |          3218.3 |    2.25 |      0.44 | False    |
| Q20     | exasol            | starrocks           |        4872.1 |          3996.2 |    0.82 |      1.22 | True     |
| Q21     | exasol            | starrocks           |       19181.3 |         59616.1 |    3.11 |      0.32 | False    |
| Q22     | exasol            | starrocks           |        2831   |          1893.1 |    0.67 |      1.5  | True     |

### Per-Stream Statistics

This benchmark was executed using **15 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 11639.7 | 291.4 | 85.1 | 90350.8 |
| 1 | 8 | 9762.7 | 2733.3 | 559.3 | 27910.7 |
| 10 | 7 | 9051.7 | 3119.7 | 364.5 | 30208.7 |
| 11 | 7 | 8347.5 | 4192.7 | 1735.2 | 21602.9 |
| 12 | 7 | 11876.8 | 5930.7 | 669.2 | 43571.1 |
| 13 | 7 | 12419.5 | 15377.3 | 362.3 | 26200.6 |
| 14 | 7 | 11061.6 | 4872.1 | 1126.1 | 22090.4 |
| 2 | 8 | 8522.9 | 3181.1 | 303.7 | 24712.8 |
| 3 | 8 | 11095.5 | 7311.1 | 1806.3 | 33013.6 |
| 4 | 8 | 8019.8 | 4154.1 | 681.5 | 19448.7 |
| 5 | 7 | 12724.0 | 9311.9 | 1901.0 | 24829.1 |
| 6 | 7 | 10286.9 | 5751.5 | 1858.6 | 22772.5 |
| 7 | 7 | 9738.6 | 6249.9 | 681.6 | 21300.2 |
| 8 | 7 | 11627.8 | 6909.5 | 155.4 | 42507.8 |
| 9 | 7 | 9122.3 | 3391.9 | 1840.9 | 20343.9 |

**Performance Analysis for Exasol:**
- Fastest stream median: 291.4ms
- Slowest stream median: 15377.3ms
- Stream performance variation: 5177.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 8 | 18942.8 | 9256.1 | 1301.1 | 83667.7 |
| 1 | 8 | 30522.2 | 4778.8 | 2029.9 | 127833.2 |
| 10 | 7 | 15719.8 | 7178.0 | 1835.6 | 47885.7 |
| 11 | 7 | 19898.3 | 3088.7 | 1893.1 | 92309.1 |
| 12 | 7 | 25059.0 | 12546.4 | 1161.4 | 99866.2 |
| 13 | 7 | 20930.0 | 19796.0 | 2960.0 | 45866.2 |
| 14 | 7 | 33281.9 | 8238.0 | 4271.5 | 109887.2 |
| 2 | 8 | 32752.7 | 6575.1 | 1368.5 | 203873.5 |
| 3 | 8 | 28829.5 | 15535.6 | 3198.6 | 90882.0 |
| 4 | 8 | 32740.9 | 1824.5 | 551.0 | 249315.6 |
| 5 | 7 | 36475.4 | 22498.6 | 1315.5 | 110097.8 |
| 6 | 7 | 13768.6 | 18506.5 | 1498.9 | 23061.7 |
| 7 | 7 | 28971.2 | 2707.1 | 1615.7 | 162713.0 |
| 8 | 7 | 37438.9 | 10247.1 | 1703.9 | 139073.0 |
| 9 | 7 | 18881.3 | 5791.3 | 1981.3 | 72619.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1824.5ms
- Slowest stream median: 22498.6ms
- Stream performance variation: 1133.2% difference between fastest and slowest streams
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
- Median runtime: 4532.4ms
- Average runtime: 10328.4ms
- Fastest query: 85.1ms
- Slowest query: 90350.8ms

**starrocks:**
- Median runtime: 8237.7ms
- Average runtime: 26393.4ms
- Fastest query: 551.0ms
- Slowest query: 249315.6ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`starrocks_exa_vs_sr_30g_mu15-benchmark.zip`](starrocks_exa_vs_sr_30g_mu15-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 4 logical cores
- **Memory:** 30.8GB RAM
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