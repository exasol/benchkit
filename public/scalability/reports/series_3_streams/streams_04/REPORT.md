# Streamlined Scalability - Stream Scaling (4 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-17 17:41:42

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 5 database systems:
- **clickhouse**
- **duckdb**
- **exasol**
- **starrocks**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 425.2ms median runtime
- trino was 27.6x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-42

### Clickhouse 26.1.3.52

**Software Configuration:**
- **Database:** clickhouse 26.1.3.52
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-50

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-103

### Starrocks 4.0.6

**Software Configuration:**
- **Database:** starrocks 4.0.6
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-80

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-237


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.4xlarge
- **Clickhouse Instance:** r6id.4xlarge
- **Trino Instance:** r6id.4xlarge
- **Starrocks Instance:** r6id.4xlarge
- **Duckdb Instance:** r6id.4xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (814GB)
sudo parted -s /dev/nvme1n1 mkpart primary 70GiB 100%

# Format /dev/nvme1n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme1n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme1n1p1 to /data
sudo mount /dev/nvme1n1p1 /data

# Set ownership of /data to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m -s /bin/bash exasol || true

# Add exasol user to sudo group
sudo usermod -aG sudo exasol || true

# Set password for exasol user (interactive)
sudo passwd exasol

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

# Distribute ubuntu SSH key to exasol user
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0JZtrdCPXyXGlsQQXIcJQ/9P/VBFX1/G/hVRqr2Jwbo5c42rjPk2b4RuH7OIYzi86e/7Tl1W1n2VLlv+/w4Hyqin68pRLCXoMQwVq6ZndYYf5fgDYPXIhVz3T/yswCvZZnfK9R3nP5yWQrU6aVSH+nwedXN+f1L86UzWXLW4LzkeBr1BRlkpjX/s+tpZRt6JqNAaWIZB+uabGb64w9mn3a1jGkFXa5nzHC+hWyjAupb659vY4b1xmhx0YhZ9esCDMEM5GMnck4g7omACcvGM3FB0zoKOPJhtJf+mP15tEnGZ7kQ5IYS3qGGkL080SqQU2e9qQ8prqW1u0R6llJE3T ubuntu@ip-10-0-1-42&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure localhost SSH access to exasol user
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

# Generate SSH key pair for exasol user
sudo -u exasol bash -c &#39;mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh &amp;&amp; if [ ! -f ~/.ssh/id_rsa ]; then ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34; -q; fi&#39;

# [All 1 Nodes] Cross-distribute exasol SSH keys for cluster communication
# Collect exasol public keys from all nodes, distribute to all authorized_keys
sudo cat ~exasol/.ssh/id_rsa.pub  # on each node
echo &#39;&lt;KEY&gt;&#39; | sudo tee -a ~exasol/.ssh/authorized_keys &gt; /dev/null
sudo chown exasol:exasol ~exasol/.ssh/authorized_keys &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure exasol SSH config for cluster nodes
sudo -u exasol bash -c &#39;
mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh
touch ~/.ssh/config &amp;&amp; chmod 600 ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; SSHEOF

Host localhost 127.0.0.1 &lt;PRIVATE_IP&gt; &lt;PUBLIC_IP&gt;
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
&#39;

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
# Configuring passwordless sudo on all nodes
sudo sed -i &#34;/%sudo/s/) ALL$/) NOPASSWD: ALL/&#34; /etc/sudoers

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23B229633ED0ACE8E with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23B229633ED0ACE8E

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23B229633ED0ACE8E to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23B229633ED0ACE8E /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create trino data directory
sudo mkdir -p /data/trino

```

**Installation:**
```bash
# Create Trino directories
sudo mkdir -p /var/trino/data /etc/trino /var/log/trino

```


**Tuning Parameters:**

**Data Directory:** `/data/trino`



#### Starrocks 4.0.6 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F38472FA962D683 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F38472FA962D683

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F38472FA962D683 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23F38472FA962D683 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create starrocks data directory
sudo mkdir -p /data/starrocks &amp;&amp; sudo chmod 1777 /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```


**Tuning Parameters:**

**Data Directory:** `/data/starrocks`



#### Clickhouse 26.1.3.52 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS245268761046840FD with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS245268761046840FD

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS245268761046840FD to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS245268761046840FD /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `96g`
- Max threads: `16`
- Max memory usage: `24.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS233DDD869AAC362EF with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS233DDD869AAC362EF

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS233DDD869AAC362EF to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS233DDD869AAC362EF /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create duckdb data directory
sudo mkdir -p /data/duckdb

# Set ownership of /data/duckdb to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/duckdb

```

**Preparation:**
```bash
# Create DuckDB data directory: /data/duckdb
sudo mkdir -p /data/duckdb &amp;&amp; sudo chown ubuntu:ubuntu /data/duckdb

```


**Tuning Parameters:**
- Memory limit: `96GB`

**Data Directory:** `/data/duckdb`




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
unzip extscal_streams_4-benchmark.zip
cd extscal_streams_4

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
| Clickhouse | 427.66s | 0.11s | 215.82s | 838.98s | 57.2 GB | 21.9 GB | 2.6x |
| Starrocks | 428.07s | 0.13s | 342.95s | 929.73s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 62.97s | 0.33s | 0.00s | 96.83s | N/A | N/A | N/A |
| Duckdb | 421.72s | 0.02s | 135.92s | 570.84s | 412.9 MB | N/A | N/A |
| Exasol | 178.52s | 1.95s | 256.25s | 516.20s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 96.83s
- Starrocks took 929.73s (9.6x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2392.4 |      5 |      9829   |    9014.5 |   2089.1 |   5342.6 |  10315.1 |
| Q01     | duckdb     |   1141.5 |      5 |      3099.4 |    3484.8 |    996.3 |   2284.5 |   4741.1 |
| Q01     | exasol     |    808.5 |      5 |      2447.9 |    2174.9 |    548.2 |   1267.3 |   2580   |
| Q01     | starrocks  |   3613.3 |      5 |      7703.8 |   10746.7 |   4901.9 |   6781.9 |  17903.5 |
| Q01     | trino      |   5570   |      5 |      8358.5 |    8795.5 |   2403.9 |   6036.7 |  12111.5 |
| Q02     | clickhouse |   1001.3 |      5 |      8282   |    6231   |   3702.7 |   2002.5 |   9342   |
| Q02     | duckdb     |    264.7 |      5 |      2145.5 |    2880.5 |   1294.4 |   1671.3 |   4744.1 |
| Q02     | exasol     |     72.3 |      5 |       141.2 |     147.5 |     22.4 |    124.6 |    182.5 |
| Q02     | starrocks  |    323.7 |      5 |       825.9 |     805.8 |    184.9 |    507.9 |    977.2 |
| Q02     | trino      |   3780.4 |      5 |      5757.3 |    6198.3 |   2612.1 |   3631.4 |  10502.7 |
| Q03     | clickhouse |   3664.6 |      5 |      6758.4 |    7076.7 |   2811.7 |   4348.4 |  11769.3 |
| Q03     | duckdb     |    713.4 |      5 |      3023   |    3778.7 |   1813.1 |   2054.7 |   6445.9 |
| Q03     | exasol     |    313.6 |      5 |       556.9 |     677.4 |    342   |    315.1 |   1080.5 |
| Q03     | starrocks  |    770.5 |      5 |       699.9 |    1582   |   1421.3 |    555.4 |   3747.9 |
| Q03     | trino      |   8765   |      5 |     31341.1 |   27120.5 |  14467.8 |  11817.2 |  43042.6 |
| Q04     | clickhouse |   7135.6 |      5 |     14496   |   14235.3 |   2443.2 |  10412.8 |  17201   |
| Q04     | duckdb     |    676   |      5 |      4367.7 |    4252.1 |   1231.9 |   2741.6 |   5581.5 |
| Q04     | exasol     |     62.6 |      5 |       214.9 |     178.3 |     63.6 |     71.4 |    219.9 |
| Q04     | starrocks  |    661.9 |      5 |      2447.4 |    2107.5 |    560.3 |   1410.1 |   2547.4 |
| Q04     | trino      |   4789.3 |      5 |      8940.8 |    9161.6 |   1707.1 |   7393   |  11797.4 |
| Q05     | clickhouse |   4299.1 |      5 |     14487.9 |   15312.7 |   2066.1 |  13442.5 |  18709.3 |
| Q05     | duckdb     |    744.4 |      5 |      2760.4 |    3247.8 |   1312   |   2054.4 |   5384.6 |
| Q05     | exasol     |    274.7 |      5 |       752.9 |     736.1 |     95.3 |    577.3 |    835.4 |
| Q05     | starrocks  |    701.8 |      5 |      2389.5 |    2720.3 |   1254.9 |   1524.1 |   4275.3 |
| Q05     | trino      |   7378.8 |      5 |     15069.5 |   14697.8 |   6518.9 |   7417.9 |  24063.8 |
| Q06     | clickhouse |    180.1 |      5 |      2129   |    2250.7 |   1043.8 |   1058.8 |   3859.2 |
| Q06     | duckdb     |    204.9 |      5 |      1938.7 |    2307.8 |    604.6 |   1843.8 |   3215.6 |
| Q06     | exasol     |     41.4 |      5 |       153.7 |     152.6 |     79.1 |     75.2 |    262.8 |
| Q06     | starrocks  |    100.6 |      5 |       372.4 |     446.5 |    361.7 |     81.3 |    837   |
| Q06     | trino      |   2357.6 |      5 |      4240.3 |    5353.5 |   3849.7 |   2510.4 |  11847.5 |
| Q07     | clickhouse |   7550.9 |      5 |      3420.9 |    4221.5 |   2193   |   2655.7 |   8058   |
| Q07     | duckdb     |    681   |      5 |      2056.4 |    2220.5 |    355.3 |   1864.4 |   2643.1 |
| Q07     | exasol     |    274   |      5 |       943.8 |     824.4 |    292.2 |    312.4 |   1024.5 |
| Q07     | starrocks  |    841.9 |      5 |      2438.4 |    2267.1 |    987.1 |    868   |   3406.2 |
| Q07     | trino      |   5437.1 |      5 |     11449.3 |   11293   |   3362.3 |   7695.9 |  15943.1 |
| Q08     | clickhouse |   6814.7 |      5 |     21459   |   21305.5 |   2488.1 |  17416   |  23902.4 |
| Q08     | duckdb     |    726.2 |      5 |      2366.9 |    2647.6 |    552.2 |   2260.1 |   3601.2 |
| Q08     | exasol     |     78.9 |      5 |       270.5 |     244.1 |     51.2 |    155.7 |    279.7 |
| Q08     | starrocks  |    716.5 |      5 |      2637.7 |    2962   |   1205.8 |   1669.5 |   4908.2 |
| Q08     | trino      |  11104.6 |      5 |     10542.5 |   19081.4 |  16253   |   8282.9 |  46719.4 |
| Q09     | clickhouse |   4482.7 |      5 |     15991.1 |   15171.8 |   3304.4 |  10549.3 |  18130.4 |
| Q09     | duckdb     |   2324.9 |      5 |      5072.4 |    5075.2 |   1093.5 |   3793.7 |   6711.1 |
| Q09     | exasol     |   1017.2 |      5 |      3814.2 |    3759.2 |    274   |   3432.2 |   4101.1 |
| Q09     | starrocks  |   3006.1 |      5 |      7675   |    7732.1 |    866.5 |   6686.4 |   9034.6 |
| Q09     | trino      |  21097   |      5 |     77590.6 |   76802.9 |   7083.5 |  66330.9 |  85553.8 |
| Q10     | clickhouse |   4438   |      5 |      8337.2 |    9358.5 |   2942.6 |   6846.1 |  14359.4 |
| Q10     | duckdb     |   1133.1 |      5 |      3576.9 |    3853.7 |   1049.6 |   2790.9 |   5162.4 |
| Q10     | exasol     |    435.2 |      5 |      1266.6 |    1057.9 |    323.3 |    703.1 |   1310.8 |
| Q10     | starrocks  |   1026.3 |      5 |      3028.4 |    3031.9 |    232   |   2720.4 |   3357.9 |
| Q10     | trino      |   5524.9 |      5 |     15597.8 |   17273.3 |   7789   |  10564.5 |  29381.1 |
| Q11     | clickhouse |    595.4 |      5 |      2878.1 |    3189.8 |   1876.5 |   1008.9 |   6153.6 |
| Q11     | duckdb     |    107.4 |      5 |      3594.7 |    3582.2 |   1120   |   2197.3 |   5283.6 |
| Q11     | exasol     |    111.7 |      5 |       232.4 |     211.7 |     45.5 |    160.8 |    258.3 |
| Q11     | starrocks  |    147.7 |      5 |       655.3 |     576.6 |    261.5 |    251.1 |    817.4 |
| Q11     | trino      |   1165.3 |      5 |      4576.1 |    4534.8 |   2768.7 |   1109.4 |   8074.9 |
| Q12     | clickhouse |   1826.5 |      5 |      2779.4 |    5581.8 |   5200.5 |   2090.8 |  14306.4 |
| Q12     | duckdb     |    759.4 |      5 |      4229.2 |    4327.9 |   1031.7 |   2826.6 |   5449.5 |
| Q12     | exasol     |     82.9 |      5 |       297   |     320.8 |     51.4 |    278.5 |    395.7 |
| Q12     | starrocks  |    308.9 |      5 |      1265.8 |    1276.9 |    629.1 |    507.2 |   2120.6 |
| Q12     | trino      |   4589.9 |      5 |     13103.9 |   11427.7 |   5194   |   5651.5 |  17136.6 |
| Q13     | clickhouse |   2924.6 |      5 |      7109.6 |    7913.6 |   3162.6 |   3976   |  12323.9 |
| Q13     | duckdb     |   1888.1 |      5 |      3715.1 |    3831.8 |   1316.1 |   1883   |   5208.6 |
| Q13     | exasol     |    666.4 |      5 |      2168.1 |    2003.3 |    593   |    968.7 |   2452.7 |
| Q13     | starrocks  |   1699.1 |      5 |      4967   |    4579.9 |   1629.5 |   1866.9 |   5828.7 |
| Q13     | trino      |   8318.1 |      5 |     22626.1 |   27931.8 |  16313.6 |  13172.3 |  53614.2 |
| Q14     | clickhouse |    200   |      5 |      2621.3 |    2828   |    890.4 |   2017.1 |   4073.7 |
| Q14     | duckdb     |    528.7 |      5 |      2434.1 |    3110   |   1556.7 |   1662   |   5554.6 |
| Q14     | exasol     |     79.4 |      5 |       290.7 |     314.9 |     56.5 |    271.3 |    412.9 |
| Q14     | starrocks  |    150.2 |      5 |       897.4 |     926.5 |    510.3 |    289.5 |   1563.6 |
| Q14     | trino      |   3441.3 |      5 |      7275.6 |   13086.2 |   9308.5 |   4611.9 |  24369.7 |
| Q15     | clickhouse |    248   |      5 |      1332.4 |    1439.1 |    453.8 |    950.3 |   2079.8 |
| Q15     | duckdb     |    464.3 |      5 |      4162.5 |    3844.2 |   1817.1 |   1741.6 |   6007.3 |
| Q15     | exasol     |    272.4 |      5 |       756.1 |     733.4 |     42.3 |    664.9 |    763.1 |
| Q15     | starrocks  |    136   |      5 |      1436.4 |    1422.7 |    596.3 |    670.8 |   2191.6 |
| Q15     | trino      |   6012.2 |      5 |     17277.3 |   19305.7 |   6033.7 |  12639.6 |  27111   |
| Q16     | clickhouse |    531.1 |      5 |      3586.8 |    4188   |   2135.3 |   2254.7 |   7756   |
| Q16     | duckdb     |    375.6 |      5 |      2248.5 |    2404.4 |    831.8 |   1820.4 |   3837.3 |
| Q16     | exasol     |    432.5 |      5 |      1006.4 |    1054.1 |    101.5 |    949.6 |   1197.8 |
| Q16     | starrocks  |    580.7 |      5 |      1191.8 |    1203.8 |    407.7 |    767.1 |   1796.6 |
| Q16     | trino      |   2357.4 |      5 |      4475.9 |    5165.3 |   1490.8 |   4279   |   7790.1 |
| Q17     | clickhouse |    973.9 |      5 |      3199.8 |    5326.9 |   4180.6 |   1698.8 |  11511.6 |
| Q17     | duckdb     |    826.8 |      5 |      4561.9 |    4407.4 |   1001.9 |   3146.6 |   5363   |
| Q17     | exasol     |     24.2 |      5 |        50.2 |      53.3 |     18.7 |     39.2 |     85.5 |
| Q17     | starrocks  |    520.2 |      5 |      2918.7 |    2355.3 |   1199.1 |    787.7 |   3707   |
| Q17     | trino      |   7674   |      5 |     25309.8 |   26784.1 |   7067.7 |  16900.6 |  34313.5 |
| Q18     | clickhouse |   5621.4 |      5 |     20600.9 |   21801.2 |   3211.2 |  18661.5 |  26952.6 |
| Q18     | duckdb     |   1575.5 |      5 |      3821.9 |    4484.3 |   1411   |   3201.1 |   6438.8 |
| Q18     | exasol     |    543.8 |      5 |      1735.6 |    1777.3 |     66.3 |   1721.4 |   1863.2 |
| Q18     | starrocks  |   4543.9 |      5 |     15993.3 |   15147.5 |   1911.1 |  12701.3 |  16840.8 |
| Q18     | trino      |   8010.3 |      5 |     20186.8 |   25485.7 |   9799.8 |  18485.6 |  41984.1 |
| Q19     | clickhouse |   5028.5 |      5 |     12800.9 |   11776.9 |   5025.3 |   4523.6 |  18292.4 |
| Q19     | duckdb     |    786.8 |      5 |      3589.4 |    3669   |   1437.7 |   2297   |   5743.5 |
| Q19     | exasol     |     27.2 |      5 |        47.7 |      64.7 |     32.4 |     31.6 |    109   |
| Q19     | starrocks  |    546.5 |      5 |      1653.4 |    1527.7 |    355   |    974.1 |   1830   |
| Q19     | trino      |   4094.4 |      5 |      5849.2 |    6840.2 |   2940.9 |   4677.2 |  11792   |
| Q20     | clickhouse |   1621.1 |      5 |      4632.7 |    4430.3 |   1173.7 |   2715.9 |   5622.1 |
| Q20     | duckdb     |    735.7 |      5 |      3022.7 |    3640.8 |   1566.4 |   1817.8 |   5285.1 |
| Q20     | exasol     |    221.4 |      5 |       409.3 |     449.7 |    146.4 |    284   |    607.9 |
| Q20     | starrocks  |    280.9 |      5 |       937.2 |    1071.7 |    576   |    599.2 |   2061.2 |
| Q20     | trino      |   4219.4 |      5 |      6894.7 |    8155   |   5087   |   4365.5 |  16998.5 |
| Q21     | clickhouse |   4587.1 |      5 |     14235.9 |   13963.7 |   2270.5 |  10649.9 |  16584.7 |
| Q21     | duckdb     |   3657.8 |      5 |      5228.3 |    5436.7 |    501.5 |   4907.5 |   6218.2 |
| Q21     | exasol     |    404.2 |      5 |      1136.2 |    1043.7 |    387.6 |    607.8 |   1410.9 |
| Q21     | starrocks  |   6055.9 |      5 |     13531.8 |   12850.4 |   3459.2 |   7763.8 |  16803.1 |
| Q21     | trino      |  19128.3 |      5 |     43797.4 |   43960.9 |  11234.2 |  26173.4 |  54680.9 |
| Q22     | clickhouse |    471.3 |      5 |      3365.5 |    3370.3 |    998.2 |   1806   |   4532.2 |
| Q22     | duckdb     |    410.7 |      5 |      3471.8 |    3842.4 |   1874.7 |   1556.5 |   6326.7 |
| Q22     | exasol     |     97   |      5 |       344   |     298.8 |    110.3 |    101.6 |    354.8 |
| Q22     | starrocks  |    329.5 |      5 |      1671.9 |    1889.8 |   1570.9 |    310.1 |   4114.9 |
| Q22     | trino      |   2551.7 |      5 |      7214.1 |    7843.8 |   2232.3 |   5981   |  11723.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        2447.9 |          9829   |    4.02 |      0.25 | False    |
| Q02     | exasol            | clickhouse          |         141.2 |          8282   |   58.65 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         556.9 |          6758.4 |   12.14 |      0.08 | False    |
| Q04     | exasol            | clickhouse          |         214.9 |         14496   |   67.45 |      0.01 | False    |
| Q05     | exasol            | clickhouse          |         752.9 |         14487.9 |   19.24 |      0.05 | False    |
| Q06     | exasol            | clickhouse          |         153.7 |          2129   |   13.85 |      0.07 | False    |
| Q07     | exasol            | clickhouse          |         943.8 |          3420.9 |    3.62 |      0.28 | False    |
| Q08     | exasol            | clickhouse          |         270.5 |         21459   |   79.33 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        3814.2 |         15991.1 |    4.19 |      0.24 | False    |
| Q10     | exasol            | clickhouse          |        1266.6 |          8337.2 |    6.58 |      0.15 | False    |
| Q11     | exasol            | clickhouse          |         232.4 |          2878.1 |   12.38 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |         297   |          2779.4 |    9.36 |      0.11 | False    |
| Q13     | exasol            | clickhouse          |        2168.1 |          7109.6 |    3.28 |      0.3  | False    |
| Q14     | exasol            | clickhouse          |         290.7 |          2621.3 |    9.02 |      0.11 | False    |
| Q15     | exasol            | clickhouse          |         756.1 |          1332.4 |    1.76 |      0.57 | False    |
| Q16     | exasol            | clickhouse          |        1006.4 |          3586.8 |    3.56 |      0.28 | False    |
| Q17     | exasol            | clickhouse          |          50.2 |          3199.8 |   63.74 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |        1735.6 |         20600.9 |   11.87 |      0.08 | False    |
| Q19     | exasol            | clickhouse          |          47.7 |         12800.9 |  268.36 |      0    | False    |
| Q20     | exasol            | clickhouse          |         409.3 |          4632.7 |   11.32 |      0.09 | False    |
| Q21     | exasol            | clickhouse          |        1136.2 |         14235.9 |   12.53 |      0.08 | False    |
| Q22     | exasol            | clickhouse          |         344   |          3365.5 |    9.78 |      0.1  | False    |
| Q01     | exasol            | duckdb              |        2447.9 |          3099.4 |    1.27 |      0.79 | False    |
| Q02     | exasol            | duckdb              |         141.2 |          2145.5 |   15.19 |      0.07 | False    |
| Q03     | exasol            | duckdb              |         556.9 |          3023   |    5.43 |      0.18 | False    |
| Q04     | exasol            | duckdb              |         214.9 |          4367.7 |   20.32 |      0.05 | False    |
| Q05     | exasol            | duckdb              |         752.9 |          2760.4 |    3.67 |      0.27 | False    |
| Q06     | exasol            | duckdb              |         153.7 |          1938.7 |   12.61 |      0.08 | False    |
| Q07     | exasol            | duckdb              |         943.8 |          2056.4 |    2.18 |      0.46 | False    |
| Q08     | exasol            | duckdb              |         270.5 |          2366.9 |    8.75 |      0.11 | False    |
| Q09     | exasol            | duckdb              |        3814.2 |          5072.4 |    1.33 |      0.75 | False    |
| Q10     | exasol            | duckdb              |        1266.6 |          3576.9 |    2.82 |      0.35 | False    |
| Q11     | exasol            | duckdb              |         232.4 |          3594.7 |   15.47 |      0.06 | False    |
| Q12     | exasol            | duckdb              |         297   |          4229.2 |   14.24 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        2168.1 |          3715.1 |    1.71 |      0.58 | False    |
| Q14     | exasol            | duckdb              |         290.7 |          2434.1 |    8.37 |      0.12 | False    |
| Q15     | exasol            | duckdb              |         756.1 |          4162.5 |    5.51 |      0.18 | False    |
| Q16     | exasol            | duckdb              |        1006.4 |          2248.5 |    2.23 |      0.45 | False    |
| Q17     | exasol            | duckdb              |          50.2 |          4561.9 |   90.87 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        1735.6 |          3821.9 |    2.2  |      0.45 | False    |
| Q19     | exasol            | duckdb              |          47.7 |          3589.4 |   75.25 |      0.01 | False    |
| Q20     | exasol            | duckdb              |         409.3 |          3022.7 |    7.39 |      0.14 | False    |
| Q21     | exasol            | duckdb              |        1136.2 |          5228.3 |    4.6  |      0.22 | False    |
| Q22     | exasol            | duckdb              |         344   |          3471.8 |   10.09 |      0.1  | False    |
| Q01     | exasol            | starrocks           |        2447.9 |          7703.8 |    3.15 |      0.32 | False    |
| Q02     | exasol            | starrocks           |         141.2 |           825.9 |    5.85 |      0.17 | False    |
| Q03     | exasol            | starrocks           |         556.9 |           699.9 |    1.26 |      0.8  | False    |
| Q04     | exasol            | starrocks           |         214.9 |          2447.4 |   11.39 |      0.09 | False    |
| Q05     | exasol            | starrocks           |         752.9 |          2389.5 |    3.17 |      0.32 | False    |
| Q06     | exasol            | starrocks           |         153.7 |           372.4 |    2.42 |      0.41 | False    |
| Q07     | exasol            | starrocks           |         943.8 |          2438.4 |    2.58 |      0.39 | False    |
| Q08     | exasol            | starrocks           |         270.5 |          2637.7 |    9.75 |      0.1  | False    |
| Q09     | exasol            | starrocks           |        3814.2 |          7675   |    2.01 |      0.5  | False    |
| Q10     | exasol            | starrocks           |        1266.6 |          3028.4 |    2.39 |      0.42 | False    |
| Q11     | exasol            | starrocks           |         232.4 |           655.3 |    2.82 |      0.35 | False    |
| Q12     | exasol            | starrocks           |         297   |          1265.8 |    4.26 |      0.23 | False    |
| Q13     | exasol            | starrocks           |        2168.1 |          4967   |    2.29 |      0.44 | False    |
| Q14     | exasol            | starrocks           |         290.7 |           897.4 |    3.09 |      0.32 | False    |
| Q15     | exasol            | starrocks           |         756.1 |          1436.4 |    1.9  |      0.53 | False    |
| Q16     | exasol            | starrocks           |        1006.4 |          1191.8 |    1.18 |      0.84 | False    |
| Q17     | exasol            | starrocks           |          50.2 |          2918.7 |   58.14 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        1735.6 |         15993.3 |    9.21 |      0.11 | False    |
| Q19     | exasol            | starrocks           |          47.7 |          1653.4 |   34.66 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         409.3 |           937.2 |    2.29 |      0.44 | False    |
| Q21     | exasol            | starrocks           |        1136.2 |         13531.8 |   11.91 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         344   |          1671.9 |    4.86 |      0.21 | False    |
| Q01     | exasol            | trino               |        2447.9 |          8358.5 |    3.41 |      0.29 | False    |
| Q02     | exasol            | trino               |         141.2 |          5757.3 |   40.77 |      0.02 | False    |
| Q03     | exasol            | trino               |         556.9 |         31341.1 |   56.28 |      0.02 | False    |
| Q04     | exasol            | trino               |         214.9 |          8940.8 |   41.6  |      0.02 | False    |
| Q05     | exasol            | trino               |         752.9 |         15069.5 |   20.02 |      0.05 | False    |
| Q06     | exasol            | trino               |         153.7 |          4240.3 |   27.59 |      0.04 | False    |
| Q07     | exasol            | trino               |         943.8 |         11449.3 |   12.13 |      0.08 | False    |
| Q08     | exasol            | trino               |         270.5 |         10542.5 |   38.97 |      0.03 | False    |
| Q09     | exasol            | trino               |        3814.2 |         77590.6 |   20.34 |      0.05 | False    |
| Q10     | exasol            | trino               |        1266.6 |         15597.8 |   12.31 |      0.08 | False    |
| Q11     | exasol            | trino               |         232.4 |          4576.1 |   19.69 |      0.05 | False    |
| Q12     | exasol            | trino               |         297   |         13103.9 |   44.12 |      0.02 | False    |
| Q13     | exasol            | trino               |        2168.1 |         22626.1 |   10.44 |      0.1  | False    |
| Q14     | exasol            | trino               |         290.7 |          7275.6 |   25.03 |      0.04 | False    |
| Q15     | exasol            | trino               |         756.1 |         17277.3 |   22.85 |      0.04 | False    |
| Q16     | exasol            | trino               |        1006.4 |          4475.9 |    4.45 |      0.22 | False    |
| Q17     | exasol            | trino               |          50.2 |         25309.8 |  504.18 |      0    | False    |
| Q18     | exasol            | trino               |        1735.6 |         20186.8 |   11.63 |      0.09 | False    |
| Q19     | exasol            | trino               |          47.7 |          5849.2 |  122.62 |      0.01 | False    |
| Q20     | exasol            | trino               |         409.3 |          6894.7 |   16.85 |      0.06 | False    |
| Q21     | exasol            | trino               |        1136.2 |         43797.4 |   38.55 |      0.03 | False    |
| Q22     | exasol            | trino               |         344   |          7214.1 |   20.97 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 11115.4 | 8688.0 | 1335.6 | 28879.8 |
| 1 | 28 | 10394.7 | 7141.9 | 743.7 | 28980.9 |
| 2 | 27 | 10929.8 | 11015.2 | 1674.8 | 25896.4 |
| 3 | 27 | 10517.6 | 8232.8 | 909.1 | 27192.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7141.9ms
- Slowest stream median: 11015.2ms
- Stream performance variation: 54.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3598.4 | 3510.4 | 1556.5 | 6445.9 |
| 1 | 28 | 3627.9 | 3173.8 | 1662.0 | 6326.7 |
| 2 | 27 | 3673.7 | 3576.9 | 1817.8 | 6711.1 |
| 3 | 27 | 3708.2 | 3594.7 | 1671.3 | 6438.8 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 3173.8ms
- Slowest stream median: 3594.7ms
- Stream performance variation: 13.3% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 941.1 | 903.5 | 75.2 | 2452.7 |
| 1 | 28 | 669.3 | 284.6 | 39.2 | 3912.6 |
| 2 | 27 | 946.3 | 409.3 | 31.6 | 4101.1 |
| 3 | 27 | 768.5 | 351.4 | 50.6 | 3814.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 284.6ms
- Slowest stream median: 903.5ms
- Stream performance variation: 217.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3650.0 | 3103.8 | 94.5 | 13530.4 |
| 1 | 28 | 3043.6 | 1807.5 | 358.6 | 14939.0 |
| 2 | 27 | 3600.1 | 1731.8 | 542.8 | 16725.7 |
| 3 | 27 | 3358.3 | 1752.6 | 346.3 | 15399.8 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1731.8ms
- Slowest stream median: 3103.8ms
- Stream performance variation: 79.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 19542.6 | 15333.6 | 2573.7 | 54680.9 |
| 1 | 28 | 17683.8 | 10976.0 | 4240.3 | 79858.9 |
| 2 | 27 | 20097.1 | 10542.5 | 1109.4 | 77590.6 |
| 3 | 27 | 14686.5 | 8358.5 | 2670.3 | 85553.8 |

**Performance Analysis for Trino:**
- Fastest stream median: 8358.5ms
- Slowest stream median: 15333.6ms
- Stream performance variation: 83.4% difference between fastest and slowest streams
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
- Median runtime: 425.2ms
- Average runtime: 830.8ms
- Fastest query: 31.6ms
- Slowest query: 4101.1ms

**duckdb:**
- Median runtime: 3510.4ms
- Average runtime: 3651.4ms
- Fastest query: 1556.5ms
- Slowest query: 6711.1ms

**starrocks:**
- Median runtime: 1823.7ms
- Average runtime: 3411.8ms
- Fastest query: 94.5ms
- Slowest query: 16725.7ms

**clickhouse:**
- Median runtime: 8606.5ms
- Average runtime: 10739.6ms
- Fastest query: 743.7ms
- Slowest query: 28980.9ms

**trino:**
- Median runtime: 11757.9ms
- Average runtime: 18013.6ms
- Fastest query: 1109.4ms
- Slowest query: 85553.8ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_4-benchmark.zip`](extscal_streams_4-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 16 logical cores
- **Memory:** 123.8GB RAM
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

**Clickhouse 26.1.3.52:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 96g
  - max_threads: 16
  - max_memory_usage: 24000000000
  - max_bytes_before_external_group_by: 8000000000
  - max_bytes_before_external_sort: 8000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 16000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 71GB
  - query_max_memory_per_node: 71GB

**Starrocks 4.0.6:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - bucket_count: 4
  - replication_num: 1

**Duckdb 1.4.4:**
- **Setup method:** native
- **Data directory:** /data/duckdb
- **Applied configurations:**
  - memory_limit: 96GB
  - threads: 16


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