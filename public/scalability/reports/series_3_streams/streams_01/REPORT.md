# Streamlined Scalability - Stream Scaling (1 Stream)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-02-17 18:31:49

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
- exasol was the fastest overall with 640.7ms median runtime
- trino was 31.5x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 1 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-145

### Clickhouse 26.1.3.52

**Software Configuration:**
- **Database:** clickhouse 26.1.3.52
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-59

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-242

### Starrocks 4.0.6

**Software Configuration:**
- **Database:** starrocks 4.0.6
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-160

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 4 vCPUs
- **Memory:** 30.8GB RAM
- **Hostname:** ip-10-0-1-176


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.xlarge
- **Clickhouse Instance:** r6id.xlarge
- **Trino Instance:** r6id.xlarge
- **Starrocks Instance:** r6id.xlarge
- **Duckdb Instance:** r6id.xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme0n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme0n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (150GB)
sudo parted -s /dev/nvme0n1 mkpart primary 70GiB 100%

# Format /dev/nvme0n1p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/nvme0n1p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/nvme0n1p1 to /data
sudo mount /dev/nvme0n1p1 /data

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
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDrekvZeD0xkH7AHfuFapTiGQcYhu33srVZvZVPpsbrBM1VffXqgqs1nKerdas/OTMukrhtzCbgu36RrL5lRvA7Upw9vz6+N/5mtBXhuerPDJmwcW1wOxm7Xewlru/faw+yC7l+XB2QdXkhlTI4gZ6toELMBB8ouNzXUH/GhjEEBEgvU4bGA0eukF6UT1gYJpDvfH5UJ1PTShSL8ZkeU9D6DTMmCOZBOs+wiruEm0ce026JAnNM4ibPPA7dMR2qTdlljBH7mUQ+b44lrnHwW4SnDAr3eBu3MqkHa9OLG7t/Y+V8inim2jqMxbbWLjPnN66bixGwCDOnkl9fFCm50UNh ubuntu@ip-10-0-1-145&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS56E339ABEC4BA12ED with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS56E339ABEC4BA12ED

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS56E339ABEC4BA12ED to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS56E339ABEC4BA12ED /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS457AE6B033340C952 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS457AE6B033340C952

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS457AE6B033340C952 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS457AE6B033340C952 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67B334FCA71B7BCE5 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67B334FCA71B7BCE5

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67B334FCA71B7BCE5 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS67B334FCA71B7BCE5 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `24g`
- Max threads: `4`
- Max memory usage: `24.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64088F8AFB7BC0E16 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64088F8AFB7BC0E16

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64088F8AFB7BC0E16 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64088F8AFB7BC0E16 /data

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
- Memory limit: `24GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (1 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip extscal_streams_1-benchmark.zip
cd extscal_streams_1

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
| Clickhouse | 809.06s | 0.12s | 440.20s | 1481.55s | 57.2 GB | 21.9 GB | 2.6x |
| Starrocks | 798.57s | 0.18s | 432.46s | 1402.91s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 290.34s | 0.69s | 0.00s | 415.20s | N/A | N/A | N/A |
| Duckdb | 798.10s | 0.07s | 385.35s | 1236.60s | 412.9 MB | N/A | N/A |
| Exasol | 493.91s | 2.01s | 516.77s | 1382.54s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 415.20s
- Clickhouse took 1481.55s (3.6x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   9306.6 |      5 |      8262.7 |    8507.2 |    560.5 |   7910   |   9120.2 |
| Q01     | duckdb     |   7721.4 |      5 |      3908.9 |    3911   |     20.6 |   3881   |   3937.5 |
| Q01     | exasol     |   3142.4 |      5 |      3097.8 |    3116.4 |     29.9 |   3092.1 |   3155.4 |
| Q01     | starrocks  |  13167   |      5 |     10227.5 |   10199.9 |     62.7 |  10114.1 |  10258.6 |
| Q01     | trino      |  20974.8 |      5 |     17727.7 |   17953.6 |    347   |  17657.2 |  18348.2 |
| Q02     | clickhouse |   3946.6 |      5 |      2027.6 |    2125.1 |    276.2 |   1956.7 |   2616.1 |
| Q02     | duckdb     |   1041.1 |      5 |       800   |     799.9 |      3.6 |    796.1 |    803.8 |
| Q02     | exasol     |    104.7 |      5 |        87.1 |      87.3 |      0.6 |     86.6 |     88.1 |
| Q02     | starrocks  |    840.3 |      5 |       409.7 |     407.5 |     17.6 |    378.3 |    425.3 |
| Q02     | trino      |  12047   |      5 |      5978.2 |    6055.5 |    224.8 |   5802.1 |   6405.5 |
| Q03     | clickhouse |  14915   |      5 |      4688.8 |    4701.5 |     76.1 |   4607.7 |   4814.6 |
| Q03     | duckdb     |   3548.5 |      5 |      2720.7 |    2717.4 |     26.7 |   2683.1 |   2751.5 |
| Q03     | exasol     |   1167.1 |      5 |      1141.3 |    1138.7 |     10.6 |   1126.6 |   1149.3 |
| Q03     | starrocks  |   3478.5 |      5 |      3704.7 |    3676.5 |     69.2 |   3572.9 |   3752.5 |
| Q03     | trino      |  24758.3 |      5 |     22360.8 |   22241.7 |    290.1 |  21889.5 |  22575.7 |
| Q04     | clickhouse |  15265.7 |      5 |      9899.1 |    9981.2 |    501.9 |   9533.1 |  10786.4 |
| Q04     | duckdb     |   3072.7 |      5 |      2647.5 |    2644   |     10.8 |   2629.8 |   2655.7 |
| Q04     | exasol     |    208.9 |      5 |       207.9 |     208   |      0.5 |    207.3 |    208.7 |
| Q04     | starrocks  |   2878.6 |      5 |      2973.4 |    2955.1 |    104.4 |   2842.7 |   3074.5 |
| Q04     | trino      |  21290.8 |      5 |     20069.2 |   20003.3 |    204.8 |  19773.4 |  20276.3 |
| Q05     | clickhouse |  20879.8 |      5 |     15642.7 |   15696.1 |    447.1 |  15326.1 |  16435.7 |
| Q05     | duckdb     |   3418.1 |      5 |      2973   |    2978.5 |     13   |   2966.6 |   2999.8 |
| Q05     | exasol     |    930.3 |      5 |       869.7 |     864.5 |      8.4 |    855.3 |    871   |
| Q05     | starrocks  |   5774.6 |      5 |      6043.5 |    6061.2 |    158.6 |   5845   |   6265   |
| Q05     | trino      |  24571.6 |      5 |     23669.6 |   23402.7 |    801.5 |  22423.9 |  24172.2 |
| Q06     | clickhouse |    951.3 |      5 |       528.1 |     590.7 |     96.4 |    514.2 |    699.9 |
| Q06     | duckdb     |    834.7 |      5 |       835.1 |     834.2 |      3.7 |    828.5 |    838.1 |
| Q06     | exasol     |    137.2 |      5 |       136.5 |     136.6 |      0.7 |    135.7 |    137.7 |
| Q06     | starrocks  |    362.7 |      5 |       149.4 |     149   |      2.4 |    146.2 |    152.1 |
| Q06     | trino      |   9181.9 |      5 |      7783.6 |    7825.4 |    117.4 |   7754   |   8032.8 |
| Q07     | clickhouse |  28660.3 |      5 |      2916.8 |    2972.6 |    186.4 |   2741.1 |   3238.4 |
| Q07     | duckdb     |   2754.9 |      5 |      2751.4 |    2748.7 |      7.5 |   2736.1 |   2755.4 |
| Q07     | exasol     |   1181.3 |      5 |      1170.7 |    1169   |      8.9 |   1154.3 |   1177   |
| Q07     | starrocks  |   3632.5 |      5 |      2658.1 |    2664.8 |     60.5 |   2613.4 |   2762.6 |
| Q07     | trino      |  19859.9 |      5 |     18248.2 |   18387.2 |    277.8 |  18144.7 |  18747.1 |
| Q08     | clickhouse |  26692.1 |      5 |     23731.4 |   23535   |    456.9 |  22855.2 |  24004.2 |
| Q08     | duckdb     |   3067.5 |      5 |      2763.3 |    2763.1 |      9.1 |   2752.3 |   2773.5 |
| Q08     | exasol     |    268.9 |      5 |       267.8 |     329.3 |    138.5 |    264.4 |    577.1 |
| Q08     | starrocks  |   4836.6 |      5 |      4968.6 |    5041.6 |    204   |   4899.4 |   5402.6 |
| Q08     | trino      |  18811.6 |      5 |     18366.1 |   18305.6 |    233.1 |  18047.1 |  18580   |
| Q09     | clickhouse |  19532.1 |      5 |     13422.7 |   13389.1 |    269.9 |  12977.5 |  13713.1 |
| Q09     | duckdb     |   9654.2 |      5 |      9605.1 |    9595.1 |     38.5 |   9536.8 |   9637   |
| Q09     | exasol     |   4617.1 |      5 |      4112.9 |    4152.6 |     66.1 |   4093.9 |   4232.4 |
| Q09     | starrocks  |  10057.2 |      5 |     10586.8 |   10568.2 |    172.9 |  10316.8 |  10787   |
| Q09     | trino      |  58989.9 |      5 |     60678.5 |   62635.8 |   5405.9 |  59077   |  72169   |
| Q10     | clickhouse |  20180.3 |      5 |      6473.2 |    6461.1 |    207   |   6235.7 |   6685   |
| Q10     | duckdb     |   4591.1 |      5 |      4324.5 |    4322.3 |     13.9 |   4301.1 |   4337.5 |
| Q10     | exasol     |   1321.1 |      5 |      1223   |    1222.8 |     12   |   1205.2 |   1239.2 |
| Q10     | starrocks  |   4005.6 |      5 |      4072.8 |    4059.1 |     41.6 |   3989.9 |   4099.8 |
| Q10     | trino      |  26606.6 |      5 |     23221.6 |   22946.9 |    588.2 |  22306.6 |  23452.6 |
| Q11     | clickhouse |   2510.5 |      5 |       765.3 |     774.2 |     31.4 |    745.4 |    825.9 |
| Q11     | duckdb     |    423.6 |      5 |       407.4 |     407.1 |      4.8 |    401.5 |    414   |
| Q11     | exasol     |    245.5 |      5 |       230   |     229.1 |      2   |    226.6 |    231   |
| Q11     | starrocks  |    654.1 |      5 |       399.9 |     404.6 |     17   |    384.1 |    426.6 |
| Q11     | trino      |   4246   |      5 |      3221.9 |    3195.2 |     73.6 |   3079.9 |   3265.7 |
| Q12     | clickhouse |   7965.3 |      5 |      2435.4 |    2498.1 |    166   |   2395.4 |   2792.9 |
| Q12     | duckdb     |   3274.6 |      5 |      3234.2 |    3243   |     31.8 |   3209.9 |   3290.9 |
| Q12     | exasol     |    422.7 |      5 |       282.7 |     282.6 |      1.3 |    280.6 |    284.1 |
| Q12     | starrocks  |   1326   |      5 |       658.5 |     670.8 |     50.1 |    628.1 |    755.9 |
| Q12     | trino      |  12644.4 |      5 |      8718.8 |    8771.5 |    134.2 |   8648.5 |   8991.8 |
| Q13     | clickhouse |   8952.3 |      5 |      5628.6 |    5637.4 |    270.2 |   5359.7 |   5923.9 |
| Q13     | duckdb     |   7836.1 |      5 |      7481.2 |    7491.9 |     29.4 |   7461.4 |   7529.4 |
| Q13     | exasol     |   3058.9 |      5 |      2955.3 |    2958.5 |     13.9 |   2939.1 |   2973.1 |
| Q13     | starrocks  |   5969.6 |      5 |      6164.4 |    6183.6 |     75.8 |   6113.5 |   6307.5 |
| Q13     | trino      |  35531.3 |      5 |     34246.2 |   34271.4 |    533.4 |  33582.5 |  35058.8 |
| Q14     | clickhouse |    712.5 |      5 |       505.8 |     509.4 |     10.3 |    502.4 |    527.5 |
| Q14     | duckdb     |   2267.9 |      5 |      2201   |    2204.8 |     17.3 |   2188.1 |   2230.1 |
| Q14     | exasol     |    347.2 |      5 |       281.9 |     282.4 |      2.5 |    280.1 |    286.4 |
| Q14     | starrocks  |    347.2 |      5 |       347.8 |     346.2 |      3.5 |    340.2 |    348.6 |
| Q14     | trino      |  36979.1 |      5 |     22707.2 |   22705.7 |    118.4 |  22575.5 |  22834.6 |
| Q15     | clickhouse |    631.7 |      5 |       410.9 |     406.8 |     10.4 |    395.9 |    420   |
| Q15     | duckdb     |   1824.2 |      5 |      1823.7 |    1830.2 |     18.5 |   1809.5 |   1851   |
| Q15     | exasol     |    681   |      5 |       684.7 |     685.6 |      2.9 |    682.4 |    690   |
| Q15     | starrocks  |    381.1 |      5 |       363.3 |     357.2 |     21.1 |    321.2 |    376   |
| Q15     | trino      |  24601.8 |      5 |     22752.9 |   22955.8 |    340.1 |  22661.2 |  23423.8 |
| Q16     | clickhouse |   2344.7 |      5 |      1738.9 |    1749.8 |     77.5 |   1665.3 |   1877   |
| Q16     | duckdb     |   1410.2 |      5 |      1348.5 |    1349.6 |      4.6 |   1343.5 |   1355.2 |
| Q16     | exasol     |   1013.1 |      5 |       982.7 |     986.3 |      8.7 |    976   |    996.9 |
| Q16     | starrocks  |   1245.9 |      5 |       705   |     714.7 |     24.4 |    687.5 |    744.3 |
| Q16     | trino      |   7619   |      5 |      5060.1 |    5896.8 |   1944.2 |   4848.9 |   9353.8 |
| Q17     | clickhouse |   4152.9 |      5 |      3338.2 |    3376.2 |    103.1 |   3292.6 |   3554.7 |
| Q17     | duckdb     |   3389.8 |      5 |      3377.8 |    3380.7 |     23.9 |   3349.3 |   3405.6 |
| Q17     | exasol     |     41.5 |      5 |        35.7 |      35.8 |      0.3 |     35.5 |     36.2 |
| Q17     | starrocks  |   2085.5 |      5 |      2084.2 |    2082.5 |     38   |   2039.9 |   2141.3 |
| Q17     | trino      |  26393   |      5 |     24930.4 |   25303.8 |   1713.5 |  23549.6 |  28121.4 |
| Q18     | clickhouse |  26394.5 |      5 |     21506.1 |   21486.6 |    333.7 |  21057.1 |  21893   |
| Q18     | duckdb     |   6312.1 |      5 |      6322.6 |    6285.2 |     72.3 |   6196.3 |   6347   |
| Q18     | exasol     |   1847.7 |      5 |      1844.9 |    1844.2 |      8.3 |   1833.2 |   1854.9 |
| Q18     | starrocks  |  11839.9 |      5 |     12166.3 |   12246.8 |    197.9 |  12058.3 |  12561   |
| Q18     | trino      |  66512.5 |      5 |     27572.7 |   32457.8 |  10605.8 |  25309.3 |  50639.3 |
| Q19     | clickhouse |  21120   |      5 |     17683   |   17635.5 |     93.7 |  17521.3 |  17738.2 |
| Q19     | duckdb     |   3118.3 |      5 |      3069.7 |    3074.9 |      9.5 |   3065.5 |   3085.3 |
| Q19     | exasol     |    118.7 |      5 |        85   |      85   |      0.4 |     84.4 |     85.5 |
| Q19     | starrocks  |   2834.3 |      5 |      2811.8 |    2807.2 |     23.3 |   2782.4 |   2832.9 |
| Q19     | trino      |  26448.7 |      5 |     27762.3 |   27115.3 |   8961.5 |  16138.4 |  40683.5 |
| Q20     | clickhouse |   5497.7 |      5 |      2972.4 |    2993   |     86.3 |   2913.3 |   3140.8 |
| Q20     | duckdb     |   2910.3 |      5 |      2918.8 |    2923.7 |     10.6 |   2913.9 |   2936.3 |
| Q20     | exasol     |    597.3 |      5 |       594   |     594.2 |      3   |    590.7 |    599   |
| Q20     | starrocks  |    981   |      5 |       580.9 |     582.2 |     17.9 |    561.7 |    607.8 |
| Q20     | trino      |  15374.7 |      5 |     13294.5 |   14042.8 |   1653.3 |  13162.9 |  16982.7 |
| Q21     | clickhouse |  17221.7 |      5 |     16006.9 |   16160.8 |    625.1 |  15463.9 |  17102.6 |
| Q21     | duckdb     |  14438.4 |      5 |     14294.7 |   14294   |     33.7 |  14258.4 |  14338.2 |
| Q21     | exasol     |   1751.6 |      5 |      1743.3 |    1754.8 |     22.3 |   1736.1 |   1785.2 |
| Q21     | starrocks  |  12960.2 |      5 |     14382.4 |   14499.8 |    283.7 |  14232.5 |  14880.4 |
| Q21     | trino      | 135832   |      5 |     62120.1 |   62091.1 |    201.7 |  61766.5 |  62310.6 |
| Q22     | clickhouse |   2956.4 |      5 |      1517.4 |    1519.8 |     32.3 |   1479.9 |   1556.9 |
| Q22     | duckdb     |   1671   |      5 |      1660.8 |    1656.4 |      7.4 |   1645   |   1662.6 |
| Q22     | exasol     |    357.9 |      5 |       345.2 |     345.3 |      0.7 |    344.4 |    346.2 |
| Q22     | starrocks  |   1139.2 |      5 |       902.7 |     923.2 |     35.6 |    888.9 |    964.6 |
| Q22     | trino      |  12833.9 |      5 |     11300.9 |   11311.5 |    267.4 |  10946.5 |  11692.2 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3097.8 |          8262.7 |    2.67 |      0.37 | False    |
| Q02     | exasol            | clickhouse          |          87.1 |          2027.6 |   23.28 |      0.04 | False    |
| Q03     | exasol            | clickhouse          |        1141.3 |          4688.8 |    4.11 |      0.24 | False    |
| Q04     | exasol            | clickhouse          |         207.9 |          9899.1 |   47.61 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         869.7 |         15642.7 |   17.99 |      0.06 | False    |
| Q06     | exasol            | clickhouse          |         136.5 |           528.1 |    3.87 |      0.26 | False    |
| Q07     | exasol            | clickhouse          |        1170.7 |          2916.8 |    2.49 |      0.4  | False    |
| Q08     | exasol            | clickhouse          |         267.8 |         23731.4 |   88.62 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        4112.9 |         13422.7 |    3.26 |      0.31 | False    |
| Q10     | exasol            | clickhouse          |        1223   |          6473.2 |    5.29 |      0.19 | False    |
| Q11     | exasol            | clickhouse          |         230   |           765.3 |    3.33 |      0.3  | False    |
| Q12     | exasol            | clickhouse          |         282.7 |          2435.4 |    8.61 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |        2955.3 |          5628.6 |    1.9  |      0.53 | False    |
| Q14     | exasol            | clickhouse          |         281.9 |           505.8 |    1.79 |      0.56 | False    |
| Q15     | exasol            | clickhouse          |         684.7 |           410.9 |    0.6  |      1.67 | True     |
| Q16     | exasol            | clickhouse          |         982.7 |          1738.9 |    1.77 |      0.57 | False    |
| Q17     | exasol            | clickhouse          |          35.7 |          3338.2 |   93.51 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        1844.9 |         21506.1 |   11.66 |      0.09 | False    |
| Q19     | exasol            | clickhouse          |          85   |         17683   |  208.04 |      0    | False    |
| Q20     | exasol            | clickhouse          |         594   |          2972.4 |    5    |      0.2  | False    |
| Q21     | exasol            | clickhouse          |        1743.3 |         16006.9 |    9.18 |      0.11 | False    |
| Q22     | exasol            | clickhouse          |         345.2 |          1517.4 |    4.4  |      0.23 | False    |
| Q01     | exasol            | duckdb              |        3097.8 |          3908.9 |    1.26 |      0.79 | False    |
| Q02     | exasol            | duckdb              |          87.1 |           800   |    9.18 |      0.11 | False    |
| Q03     | exasol            | duckdb              |        1141.3 |          2720.7 |    2.38 |      0.42 | False    |
| Q04     | exasol            | duckdb              |         207.9 |          2647.5 |   12.73 |      0.08 | False    |
| Q05     | exasol            | duckdb              |         869.7 |          2973   |    3.42 |      0.29 | False    |
| Q06     | exasol            | duckdb              |         136.5 |           835.1 |    6.12 |      0.16 | False    |
| Q07     | exasol            | duckdb              |        1170.7 |          2751.4 |    2.35 |      0.43 | False    |
| Q08     | exasol            | duckdb              |         267.8 |          2763.3 |   10.32 |      0.1  | False    |
| Q09     | exasol            | duckdb              |        4112.9 |          9605.1 |    2.34 |      0.43 | False    |
| Q10     | exasol            | duckdb              |        1223   |          4324.5 |    3.54 |      0.28 | False    |
| Q11     | exasol            | duckdb              |         230   |           407.4 |    1.77 |      0.56 | False    |
| Q12     | exasol            | duckdb              |         282.7 |          3234.2 |   11.44 |      0.09 | False    |
| Q13     | exasol            | duckdb              |        2955.3 |          7481.2 |    2.53 |      0.4  | False    |
| Q14     | exasol            | duckdb              |         281.9 |          2201   |    7.81 |      0.13 | False    |
| Q15     | exasol            | duckdb              |         684.7 |          1823.7 |    2.66 |      0.38 | False    |
| Q16     | exasol            | duckdb              |         982.7 |          1348.5 |    1.37 |      0.73 | False    |
| Q17     | exasol            | duckdb              |          35.7 |          3377.8 |   94.62 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        1844.9 |          6322.6 |    3.43 |      0.29 | False    |
| Q19     | exasol            | duckdb              |          85   |          3069.7 |   36.11 |      0.03 | False    |
| Q20     | exasol            | duckdb              |         594   |          2918.8 |    4.91 |      0.2  | False    |
| Q21     | exasol            | duckdb              |        1743.3 |         14294.7 |    8.2  |      0.12 | False    |
| Q22     | exasol            | duckdb              |         345.2 |          1660.8 |    4.81 |      0.21 | False    |
| Q01     | exasol            | starrocks           |        3097.8 |         10227.5 |    3.3  |      0.3  | False    |
| Q02     | exasol            | starrocks           |          87.1 |           409.7 |    4.7  |      0.21 | False    |
| Q03     | exasol            | starrocks           |        1141.3 |          3704.7 |    3.25 |      0.31 | False    |
| Q04     | exasol            | starrocks           |         207.9 |          2973.4 |   14.3  |      0.07 | False    |
| Q05     | exasol            | starrocks           |         869.7 |          6043.5 |    6.95 |      0.14 | False    |
| Q06     | exasol            | starrocks           |         136.5 |           149.4 |    1.09 |      0.91 | False    |
| Q07     | exasol            | starrocks           |        1170.7 |          2658.1 |    2.27 |      0.44 | False    |
| Q08     | exasol            | starrocks           |         267.8 |          4968.6 |   18.55 |      0.05 | False    |
| Q09     | exasol            | starrocks           |        4112.9 |         10586.8 |    2.57 |      0.39 | False    |
| Q10     | exasol            | starrocks           |        1223   |          4072.8 |    3.33 |      0.3  | False    |
| Q11     | exasol            | starrocks           |         230   |           399.9 |    1.74 |      0.58 | False    |
| Q12     | exasol            | starrocks           |         282.7 |           658.5 |    2.33 |      0.43 | False    |
| Q13     | exasol            | starrocks           |        2955.3 |          6164.4 |    2.09 |      0.48 | False    |
| Q14     | exasol            | starrocks           |         281.9 |           347.8 |    1.23 |      0.81 | False    |
| Q15     | exasol            | starrocks           |         684.7 |           363.3 |    0.53 |      1.88 | True     |
| Q16     | exasol            | starrocks           |         982.7 |           705   |    0.72 |      1.39 | True     |
| Q17     | exasol            | starrocks           |          35.7 |          2084.2 |   58.38 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        1844.9 |         12166.3 |    6.59 |      0.15 | False    |
| Q19     | exasol            | starrocks           |          85   |          2811.8 |   33.08 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         594   |           580.9 |    0.98 |      1.02 | True     |
| Q21     | exasol            | starrocks           |        1743.3 |         14382.4 |    8.25 |      0.12 | False    |
| Q22     | exasol            | starrocks           |         345.2 |           902.7 |    2.62 |      0.38 | False    |
| Q01     | exasol            | trino               |        3097.8 |         17727.7 |    5.72 |      0.17 | False    |
| Q02     | exasol            | trino               |          87.1 |          5978.2 |   68.64 |      0.01 | False    |
| Q03     | exasol            | trino               |        1141.3 |         22360.8 |   19.59 |      0.05 | False    |
| Q04     | exasol            | trino               |         207.9 |         20069.2 |   96.53 |      0.01 | False    |
| Q05     | exasol            | trino               |         869.7 |         23669.6 |   27.22 |      0.04 | False    |
| Q06     | exasol            | trino               |         136.5 |          7783.6 |   57.02 |      0.02 | False    |
| Q07     | exasol            | trino               |        1170.7 |         18248.2 |   15.59 |      0.06 | False    |
| Q08     | exasol            | trino               |         267.8 |         18366.1 |   68.58 |      0.01 | False    |
| Q09     | exasol            | trino               |        4112.9 |         60678.5 |   14.75 |      0.07 | False    |
| Q10     | exasol            | trino               |        1223   |         23221.6 |   18.99 |      0.05 | False    |
| Q11     | exasol            | trino               |         230   |          3221.9 |   14.01 |      0.07 | False    |
| Q12     | exasol            | trino               |         282.7 |          8718.8 |   30.84 |      0.03 | False    |
| Q13     | exasol            | trino               |        2955.3 |         34246.2 |   11.59 |      0.09 | False    |
| Q14     | exasol            | trino               |         281.9 |         22707.2 |   80.55 |      0.01 | False    |
| Q15     | exasol            | trino               |         684.7 |         22752.9 |   33.23 |      0.03 | False    |
| Q16     | exasol            | trino               |         982.7 |          5060.1 |    5.15 |      0.19 | False    |
| Q17     | exasol            | trino               |          35.7 |         24930.4 |  698.33 |      0    | False    |
| Q18     | exasol            | trino               |        1844.9 |         27572.7 |   14.95 |      0.07 | False    |
| Q19     | exasol            | trino               |          85   |         27762.3 |  326.62 |      0    | False    |
| Q20     | exasol            | trino               |         594   |         13294.5 |   22.38 |      0.04 | False    |
| Q21     | exasol            | trino               |        1743.3 |         62120.1 |   35.63 |      0.03 | False    |
| Q22     | exasol            | trino               |         345.2 |         11300.9 |   32.74 |      0.03 | False    |


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
- Median runtime: 640.7ms
- Average runtime: 1023.1ms
- Fastest query: 35.5ms
- Slowest query: 4232.4ms

**duckdb:**
- Median runtime: 2843.7ms
- Average runtime: 3702.5ms
- Fastest query: 401.5ms
- Slowest query: 14338.2ms

**starrocks:**
- Median runtime: 2606.3ms
- Average runtime: 3791.2ms
- Fastest query: 133.9ms
- Slowest query: 13655.5ms

**clickhouse:**
- Median runtime: 7803.8ms
- Average runtime: 10012.7ms
- Fastest query: 59.6ms
- Slowest query: 27589.4ms

**trino:**
- Median runtime: 20173.8ms
- Average runtime: 22267.1ms
- Fastest query: 3079.9ms
- Slowest query: 72169.0ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_1-benchmark.zip`](extscal_streams_1-benchmark.zip)

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
  - memory_limit: 24g
  - max_threads: 4
  - max_memory_usage: 24000000000
  - max_bytes_before_external_group_by: 8000000000
  - max_bytes_before_external_sort: 8000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 16000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 18GB
  - query_max_memory_per_node: 18GB

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
  - memory_limit: 24GB
  - threads: 4


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 1 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts