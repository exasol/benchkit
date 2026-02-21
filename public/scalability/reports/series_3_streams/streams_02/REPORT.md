# Streamlined Scalability - Stream Scaling (2 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-02-17 17:55:01

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
- exasol was the fastest overall with 592.4ms median runtime
- trino was 24.6x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 2 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-59

### Clickhouse 26.1.3.52

**Software Configuration:**
- **Database:** clickhouse 26.1.3.52
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-103

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-46

### Starrocks 4.0.6

**Software Configuration:**
- **Database:** starrocks 4.0.6
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-79

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.2xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 8 vCPUs
- **Memory:** 61.8GB RAM
- **Hostname:** ip-10-0-1-4


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
- **Duckdb Instance:** r6id.2xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (371GB)
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
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCMAzw9ZaNnFGYU9dGuZXEOEz2KsowsQoVyDgkPpVQSmouTS1qJ5iiL59663mbZDKvZLGPoXwPspoCXDufAqCFppNoSQXNkuXW6lCzot01yMSVupQ2avkVrdshK486Yjy1xrFNnLbRdlySYT0st1HlzpTccOOUZMXmLQctLjpK6eA3Wfiy4QbvjnhDdx6KYtnt4H3cPg5CibKFhQSIaPjuI6TtkhQFHpwE9zH4qZfIO6YRZw6C0DN5kvHYoXA2bLQV3XhJ18jk7hN50Y3qj8xVwFi6C4r8gD7YYHvCqEsOJsNt0DPrcbTTvC+5iWvdI9YGYQKisP5JCQgUDrOeGr4WB ubuntu@ip-10-0-1-59&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648579C5628E36221 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648579C5628E36221

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648579C5628E36221 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648579C5628E36221 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648D861BD8B697031 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648D861BD8B697031

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648D861BD8B697031 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS648D861BD8B697031 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2860613D42EDD27D4 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2860613D42EDD27D4

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2860613D42EDD27D4 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2860613D42EDD27D4 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `24.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B8524EEB9497A674 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B8524EEB9497A674

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B8524EEB9497A674 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B8524EEB9497A674 /data

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
- Memory limit: `48GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (2 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip extscal_streams_2-benchmark.zip
cd extscal_streams_2

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
| Clickhouse | 557.75s | 0.11s | 260.27s | 1025.14s | 57.2 GB | 21.9 GB | 2.6x |
| Starrocks | 551.59s | 0.13s | 344.11s | 1057.23s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 138.79s | 0.36s | 0.00s | 202.39s | N/A | N/A | N/A |
| Duckdb | 535.14s | 0.13s | 203.49s | 764.78s | 412.9 MB | N/A | N/A |
| Exasol | 276.94s | 1.99s | 313.84s | 736.79s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 202.39s
- Starrocks took 1057.23s (5.2x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4726.7 |      5 |      8268.1 |    7830.6 |   1133.9 |   6073.8 |   8906.5 |
| Q01     | duckdb     |   2241.3 |      5 |      2625.2 |    2662.6 |    493.1 |   2103   |   3232.7 |
| Q01     | exasol     |   1619.5 |      5 |      2842.5 |    2550.7 |    559.3 |   1587.1 |   2933.4 |
| Q01     | starrocks  |   7048.6 |      5 |      8557.8 |    8691.1 |    810   |   7907.1 |   9810.6 |
| Q01     | trino      |  10331.1 |      5 |     14436.9 |   14943.4 |   4469.7 |  10591.5 |  21453.5 |
| Q02     | clickhouse |   2225.5 |      5 |      3133.7 |    3112.5 |    371.9 |   2550.4 |   3585.6 |
| Q02     | duckdb     |    466.5 |      5 |      1758.5 |    2726.9 |   2097.4 |    414.2 |   5643.5 |
| Q02     | exasol     |     89.1 |      5 |       115.5 |     140.1 |     39.8 |    106.4 |    185.3 |
| Q02     | starrocks  |    524.3 |      5 |       565.6 |     561   |    130.1 |    357.5 |    691.3 |
| Q02     | trino      |   5012.4 |      5 |      4768.4 |    4705   |    480.8 |   4088.9 |   5402.5 |
| Q03     | clickhouse |   8227.6 |      5 |      5080.2 |    4507.9 |   1237.1 |   2341.3 |   5327.7 |
| Q03     | duckdb     |   1386.1 |      5 |      2549.7 |    2854.8 |    866.4 |   1869.6 |   4185.2 |
| Q03     | exasol     |    639.4 |      5 |       611.4 |     820.5 |    295   |    601.9 |   1181.5 |
| Q03     | starrocks  |   1669.3 |      5 |      1862.4 |    2105.1 |    642.4 |   1542.3 |   3083.6 |
| Q03     | trino      |  14173.5 |      5 |     13367.9 |   16650.5 |   5561   |  12292.1 |  24439.8 |
| Q04     | clickhouse |   9430   |      5 |     13583.2 |   11875.6 |   3047.4 |   6598.6 |  13686.3 |
| Q04     | duckdb     |   1320   |      5 |      2521.3 |    3277.6 |   2689   |   1197.7 |   7976.2 |
| Q04     | exasol     |    114.2 |      5 |       205.4 |     219.2 |     87.7 |    111.8 |    356.4 |
| Q04     | starrocks  |   1308.8 |      5 |      2744.6 |    2473.4 |    692.3 |   1309.5 |   2998.5 |
| Q04     | trino      |   9480.1 |      5 |     14618.7 |   16695.7 |   7022.7 |   8642.7 |  26253.8 |
| Q05     | clickhouse |  11046.1 |      5 |     16140   |   15606.8 |   1901.9 |  12310.9 |  17220.5 |
| Q05     | duckdb     |   1453.4 |      5 |      2708.6 |    2861.7 |   1102.1 |   1355.6 |   4345   |
| Q05     | exasol     |    514.4 |      5 |       851.5 |     854.5 |     46   |    791.1 |    900.7 |
| Q05     | starrocks  |   2775.8 |      5 |      3917.1 |    4225.2 |    963.2 |   3326.4 |   5336.5 |
| Q05     | trino      |  12901   |      5 |     16708   |   17114.3 |   3586.9 |  13169.7 |  22199.8 |
| Q06     | clickhouse |    340.6 |      5 |       544   |     559.1 |     85.5 |    453.8 |    690.8 |
| Q06     | duckdb     |    404   |      5 |      1779.8 |    2083.6 |   1187.6 |    834.4 |   4049.1 |
| Q06     | exasol     |     73.8 |      5 |       135.9 |     116.6 |     41.2 |     72.8 |    164.4 |
| Q06     | starrocks  |    247.2 |      5 |       277.6 |     329.4 |    124.7 |    210.1 |    524.8 |
| Q06     | trino      |   4303.6 |      5 |      6698.6 |    8845.7 |   6028.6 |   3941.4 |  18578.8 |
| Q07     | clickhouse |  14202.8 |      5 |      4041   |    3927.7 |   1433.2 |   1692.5 |   5467.5 |
| Q07     | duckdb     |   1324.4 |      5 |      2368.9 |    2293.9 |    381   |   1747   |   2644.1 |
| Q07     | exasol     |    637.4 |      5 |      1194.6 |    1074.7 |    300.3 |    591.1 |   1355.9 |
| Q07     | starrocks  |   1672.4 |      5 |      2842.9 |    2591.6 |    639.6 |   1663.9 |   3194.8 |
| Q07     | trino      |   9720.2 |      5 |     13469.8 |   13101.8 |   2815.4 |   8895   |  16447.6 |
| Q08     | clickhouse |  12887   |      5 |     26752.3 |   26256.4 |   1466.9 |  24534.3 |  27916.9 |
| Q08     | duckdb     |   1409.2 |      5 |      3187.6 |    3710.2 |   1279.4 |   2725.5 |   5809.3 |
| Q08     | exasol     |    165.5 |      5 |       291.3 |     260.7 |     68.8 |    146.2 |    320.6 |
| Q08     | starrocks  |   2253.2 |      5 |      3377.5 |    3451.4 |    266.1 |   3177.1 |   3892   |
| Q08     | trino      |  13012.8 |      5 |     22597.1 |   22031.6 |   2435.3 |  18017.7 |  24443.2 |
| Q09     | clickhouse |   9137.4 |      5 |     14962.9 |   14828.6 |    513.6 |  13961.3 |  15329.4 |
| Q09     | duckdb     |   4334.1 |      5 |      5698.7 |    5781.8 |   1181.2 |   4351.4 |   7366.3 |
| Q09     | exasol     |   2170.4 |      5 |      3802.4 |    4126.6 |    540.8 |   3638   |   4766   |
| Q09     | starrocks  |   6453.1 |      5 |      8282.8 |    8623.2 |    823   |   7638.6 |   9602.4 |
| Q09     | trino      |  29795.7 |      5 |     62055   |   60414.9 |   4886.2 |  54792.8 |  65946.2 |
| Q10     | clickhouse |   9741.4 |      5 |      7657   |    7415.5 |   1056   |   5974.5 |   8589.1 |
| Q10     | duckdb     |   2100.9 |      5 |      2433.9 |    3203.6 |   1794.7 |   2007.2 |   6291.5 |
| Q10     | exasol     |    743.8 |      5 |      1090.6 |    1010.7 |    281.4 |    710.8 |   1275.2 |
| Q10     | starrocks  |   2340   |      5 |      2872.2 |    3075   |    403.7 |   2801.4 |   3777.8 |
| Q10     | trino      |   9678.9 |      5 |     19590.2 |   19033.8 |   3620.7 |  14613.4 |  23712.3 |
| Q11     | clickhouse |   1358.8 |      5 |       868.9 |     805.8 |    133.6 |    615.2 |    939.4 |
| Q11     | duckdb     |    200.1 |      5 |      3188   |    3625.5 |   2042.2 |   2057.5 |   7041.2 |
| Q11     | exasol     |    162.4 |      5 |       231.5 |     211   |     54.9 |    151.2 |    275.8 |
| Q11     | starrocks  |    332   |      5 |       412.2 |     404   |     46.6 |    326.4 |    452.4 |
| Q11     | trino      |   1888.6 |      5 |      2999.4 |    3079.5 |   1049.8 |   1516.3 |   4397.6 |
| Q12     | clickhouse |   3930.2 |      5 |      2878.8 |    2807.4 |    204.6 |   2503.9 |   3001.4 |
| Q12     | duckdb     |   1503.5 |      5 |      2970.6 |    3362.5 |   1021.3 |   2692.5 |   5167.4 |
| Q12     | exasol     |    151.2 |      5 |       290.8 |     288.3 |     18.2 |    257.8 |    306.2 |
| Q12     | starrocks  |    634.4 |      5 |       925.1 |     967.9 |    255.2 |    727.3 |   1400.5 |
| Q12     | trino      |   6395.8 |      5 |      7552.3 |    8529   |   2060.9 |   6722.4 |  11589.2 |
| Q13     | clickhouse |   4880.1 |      5 |      7157.6 |    7001.6 |    316   |   6579.7 |   7323   |
| Q13     | duckdb     |   3643.8 |      5 |      4287.7 |    4430.7 |    630.4 |   3678.3 |   5162.4 |
| Q13     | exasol     |   1509.3 |      5 |      2535.4 |    2369.9 |    508.4 |   1498.2 |   2831.1 |
| Q13     | starrocks  |   3451.4 |      5 |      5329.3 |    5237.6 |   1097.4 |   3589   |   6679.2 |
| Q13     | trino      |  15667.4 |      5 |     30068.7 |   28265.3 |   7133.4 |  15766.3 |  32981.3 |
| Q14     | clickhouse |    343.5 |      5 |       675.5 |     653.6 |     78.4 |    526.4 |    738.8 |
| Q14     | duckdb     |   1050.4 |      5 |      2367   |    2538.2 |    374.6 |   2282.2 |   3186.9 |
| Q14     | exasol     |    154.6 |      5 |       314.8 |     361.4 |    111.8 |    238.2 |    514.3 |
| Q14     | starrocks  |    238.6 |      5 |       499.7 |     453.5 |     95.4 |    293   |    522.3 |
| Q14     | trino      |   6308.9 |      5 |      9648.3 |   11317.7 |   3730.5 |   9314.5 |  17951.1 |
| Q15     | clickhouse |    379.3 |      5 |       653.3 |     670.9 |     34   |    646.2 |    727.5 |
| Q15     | duckdb     |    897.3 |      5 |      2289.5 |    3985.7 |   3434.2 |    899.2 |   7774.3 |
| Q15     | exasol     |    408.9 |      5 |       601.9 |     629.3 |     63.7 |    569.4 |    730.1 |
| Q15     | starrocks  |    274   |      5 |       256.7 |     258.4 |     16.3 |    245.4 |    286   |
| Q15     | trino      |  11642   |      5 |     23083.9 |   23109.2 |   4035.3 |  17934.6 |  29108.4 |
| Q16     | clickhouse |   1068.9 |      5 |      2504   |    2487   |    104.8 |   2314.6 |   2600.8 |
| Q16     | duckdb     |    654.4 |      5 |      1703.3 |    1521.4 |    742.6 |    648.6 |   2290.8 |
| Q16     | exasol     |    629.2 |      5 |      1057.6 |    1060   |     99.8 |    952.7 |   1200   |
| Q16     | starrocks  |    796.1 |      5 |       844.1 |     820.2 |    154.6 |    652.7 |   1032   |
| Q16     | trino      |   3412.7 |      5 |      6651   |    8550.7 |   3255.2 |   5798.7 |  12882.8 |
| Q17     | clickhouse |   1948.9 |      5 |      4051.6 |    3748.3 |    512.9 |   2893.8 |   4085.8 |
| Q17     | duckdb     |   1605.4 |      5 |      2996.2 |    3351   |   1559.7 |   1608.5 |   5282.7 |
| Q17     | exasol     |     30.2 |      5 |        47.1 |      57.4 |     24.6 |     38.4 |     99.5 |
| Q17     | starrocks  |   1536.9 |      5 |      2593.3 |    2602.8 |    538.3 |   1874.2 |   3390.9 |
| Q17     | trino      |  13969.8 |      5 |     21258.8 |   22215.9 |   3630.2 |  19671.8 |  28534.4 |
| Q18     | clickhouse |  12436.5 |      5 |     23149   |   23237.2 |    494   |  22661.9 |  23985.5 |
| Q18     | duckdb     |   2960.7 |      5 |      4971.7 |    5633.5 |   2321   |   4019.7 |   9700.3 |
| Q18     | exasol     |    991.7 |      5 |      1845.8 |    1676.3 |    395.2 |    988.2 |   1923.9 |
| Q18     | starrocks  |   6960.1 |      5 |     10793.1 |   11091.7 |   1455   |   9856.3 |  13481.5 |
| Q18     | trino      |  12627.7 |      5 |     23879   |   27254.3 |   7788.6 |  20015.2 |  39292   |
| Q19     | clickhouse |  10364.4 |      5 |     18004.3 |   16674.6 |   4527.6 |   8786.6 |  19937.5 |
| Q19     | duckdb     |   1520   |      5 |      2292.3 |    2103.1 |    386.4 |   1512.2 |   2410.2 |
| Q19     | exasol     |     60   |      5 |        47.8 |      74.3 |     44.5 |     47.4 |    150.2 |
| Q19     | starrocks  |   2331.4 |      5 |      2782.3 |    2742   |    637.9 |   2032.6 |   3639.8 |
| Q19     | trino      |   7256.5 |      5 |      8761.2 |   10681.9 |   4434.5 |   6812.4 |  17318.2 |
| Q20     | clickhouse |   2864.2 |      5 |      3443   |    3209.7 |    514.8 |   2307   |   3545.8 |
| Q20     | duckdb     |   1384.2 |      5 |      2129.4 |    2703.7 |   1628.6 |   1586.1 |   5562.7 |
| Q20     | exasol     |    350.1 |      5 |       350.3 |     457.2 |    148.5 |    348.1 |    640.8 |
| Q20     | starrocks  |    509   |      5 |       698.6 |     662.9 |    245.4 |    349   |    932.9 |
| Q20     | trino      |   7108.9 |      5 |     10304.1 |   11217.2 |   3404.2 |   8041.1 |  15630.7 |
| Q21     | clickhouse |   9420.4 |      5 |     16687.6 |   15376.8 |   2065.9 |  12781.7 |  17039.6 |
| Q21     | duckdb     |   6785.6 |      5 |      7871.7 |    8044   |   1012.1 |   7005   |   9623.1 |
| Q21     | exasol     |    860.3 |      5 |       885.9 |    1179.8 |    407.8 |    875.9 |   1655.8 |
| Q21     | starrocks  |   8633.4 |      5 |     12119.2 |   10831.1 |   2747.7 |   7765   |  13914.6 |
| Q21     | trino      |  30839   |      5 |     55919.1 |   49651   |  11321.7 |  31818.7 |  59299   |
| Q22     | clickhouse |   1026.9 |      5 |      2478.9 |    2525   |    262.1 |   2236.4 |   2953.9 |
| Q22     | duckdb     |    767.3 |      5 |      3208.1 |    3491.3 |   1218.4 |   2166.1 |   5073.3 |
| Q22     | exasol     |    179.1 |      5 |       344.8 |     301.6 |     76.4 |    178   |    359   |
| Q22     | starrocks  |    623.7 |      5 |       975.7 |     942.2 |    219.4 |    575.1 |   1155.4 |
| Q22     | trino      |   4493   |      5 |     10061.9 |    9446.1 |   3275.6 |   4061.1 |  12485.5 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        2842.5 |          8268.1 |    2.91 |      0.34 | False    |
| Q02     | exasol            | clickhouse          |         115.5 |          3133.7 |   27.13 |      0.04 | False    |
| Q03     | exasol            | clickhouse          |         611.4 |          5080.2 |    8.31 |      0.12 | False    |
| Q04     | exasol            | clickhouse          |         205.4 |         13583.2 |   66.13 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |         851.5 |         16140   |   18.95 |      0.05 | False    |
| Q06     | exasol            | clickhouse          |         135.9 |           544   |    4    |      0.25 | False    |
| Q07     | exasol            | clickhouse          |        1194.6 |          4041   |    3.38 |      0.3  | False    |
| Q08     | exasol            | clickhouse          |         291.3 |         26752.3 |   91.84 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        3802.4 |         14962.9 |    3.94 |      0.25 | False    |
| Q10     | exasol            | clickhouse          |        1090.6 |          7657   |    7.02 |      0.14 | False    |
| Q11     | exasol            | clickhouse          |         231.5 |           868.9 |    3.75 |      0.27 | False    |
| Q12     | exasol            | clickhouse          |         290.8 |          2878.8 |    9.9  |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        2535.4 |          7157.6 |    2.82 |      0.35 | False    |
| Q14     | exasol            | clickhouse          |         314.8 |           675.5 |    2.15 |      0.47 | False    |
| Q15     | exasol            | clickhouse          |         601.9 |           653.3 |    1.09 |      0.92 | False    |
| Q16     | exasol            | clickhouse          |        1057.6 |          2504   |    2.37 |      0.42 | False    |
| Q17     | exasol            | clickhouse          |          47.1 |          4051.6 |   86.02 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        1845.8 |         23149   |   12.54 |      0.08 | False    |
| Q19     | exasol            | clickhouse          |          47.8 |         18004.3 |  376.66 |      0    | False    |
| Q20     | exasol            | clickhouse          |         350.3 |          3443   |    9.83 |      0.1  | False    |
| Q21     | exasol            | clickhouse          |         885.9 |         16687.6 |   18.84 |      0.05 | False    |
| Q22     | exasol            | clickhouse          |         344.8 |          2478.9 |    7.19 |      0.14 | False    |
| Q01     | exasol            | duckdb              |        2842.5 |          2625.2 |    0.92 |      1.08 | True     |
| Q02     | exasol            | duckdb              |         115.5 |          1758.5 |   15.23 |      0.07 | False    |
| Q03     | exasol            | duckdb              |         611.4 |          2549.7 |    4.17 |      0.24 | False    |
| Q04     | exasol            | duckdb              |         205.4 |          2521.3 |   12.28 |      0.08 | False    |
| Q05     | exasol            | duckdb              |         851.5 |          2708.6 |    3.18 |      0.31 | False    |
| Q06     | exasol            | duckdb              |         135.9 |          1779.8 |   13.1  |      0.08 | False    |
| Q07     | exasol            | duckdb              |        1194.6 |          2368.9 |    1.98 |      0.5  | False    |
| Q08     | exasol            | duckdb              |         291.3 |          3187.6 |   10.94 |      0.09 | False    |
| Q09     | exasol            | duckdb              |        3802.4 |          5698.7 |    1.5  |      0.67 | False    |
| Q10     | exasol            | duckdb              |        1090.6 |          2433.9 |    2.23 |      0.45 | False    |
| Q11     | exasol            | duckdb              |         231.5 |          3188   |   13.77 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         290.8 |          2970.6 |   10.22 |      0.1  | False    |
| Q13     | exasol            | duckdb              |        2535.4 |          4287.7 |    1.69 |      0.59 | False    |
| Q14     | exasol            | duckdb              |         314.8 |          2367   |    7.52 |      0.13 | False    |
| Q15     | exasol            | duckdb              |         601.9 |          2289.5 |    3.8  |      0.26 | False    |
| Q16     | exasol            | duckdb              |        1057.6 |          1703.3 |    1.61 |      0.62 | False    |
| Q17     | exasol            | duckdb              |          47.1 |          2996.2 |   63.61 |      0.02 | False    |
| Q18     | exasol            | duckdb              |        1845.8 |          4971.7 |    2.69 |      0.37 | False    |
| Q19     | exasol            | duckdb              |          47.8 |          2292.3 |   47.96 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         350.3 |          2129.4 |    6.08 |      0.16 | False    |
| Q21     | exasol            | duckdb              |         885.9 |          7871.7 |    8.89 |      0.11 | False    |
| Q22     | exasol            | duckdb              |         344.8 |          3208.1 |    9.3  |      0.11 | False    |
| Q01     | exasol            | starrocks           |        2842.5 |          8557.8 |    3.01 |      0.33 | False    |
| Q02     | exasol            | starrocks           |         115.5 |           565.6 |    4.9  |      0.2  | False    |
| Q03     | exasol            | starrocks           |         611.4 |          1862.4 |    3.05 |      0.33 | False    |
| Q04     | exasol            | starrocks           |         205.4 |          2744.6 |   13.36 |      0.07 | False    |
| Q05     | exasol            | starrocks           |         851.5 |          3917.1 |    4.6  |      0.22 | False    |
| Q06     | exasol            | starrocks           |         135.9 |           277.6 |    2.04 |      0.49 | False    |
| Q07     | exasol            | starrocks           |        1194.6 |          2842.9 |    2.38 |      0.42 | False    |
| Q08     | exasol            | starrocks           |         291.3 |          3377.5 |   11.59 |      0.09 | False    |
| Q09     | exasol            | starrocks           |        3802.4 |          8282.8 |    2.18 |      0.46 | False    |
| Q10     | exasol            | starrocks           |        1090.6 |          2872.2 |    2.63 |      0.38 | False    |
| Q11     | exasol            | starrocks           |         231.5 |           412.2 |    1.78 |      0.56 | False    |
| Q12     | exasol            | starrocks           |         290.8 |           925.1 |    3.18 |      0.31 | False    |
| Q13     | exasol            | starrocks           |        2535.4 |          5329.3 |    2.1  |      0.48 | False    |
| Q14     | exasol            | starrocks           |         314.8 |           499.7 |    1.59 |      0.63 | False    |
| Q15     | exasol            | starrocks           |         601.9 |           256.7 |    0.43 |      2.34 | True     |
| Q16     | exasol            | starrocks           |        1057.6 |           844.1 |    0.8  |      1.25 | True     |
| Q17     | exasol            | starrocks           |          47.1 |          2593.3 |   55.06 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        1845.8 |         10793.1 |    5.85 |      0.17 | False    |
| Q19     | exasol            | starrocks           |          47.8 |          2782.3 |   58.21 |      0.02 | False    |
| Q20     | exasol            | starrocks           |         350.3 |           698.6 |    1.99 |      0.5  | False    |
| Q21     | exasol            | starrocks           |         885.9 |         12119.2 |   13.68 |      0.07 | False    |
| Q22     | exasol            | starrocks           |         344.8 |           975.7 |    2.83 |      0.35 | False    |
| Q01     | exasol            | trino               |        2842.5 |         14436.9 |    5.08 |      0.2  | False    |
| Q02     | exasol            | trino               |         115.5 |          4768.4 |   41.28 |      0.02 | False    |
| Q03     | exasol            | trino               |         611.4 |         13367.9 |   21.86 |      0.05 | False    |
| Q04     | exasol            | trino               |         205.4 |         14618.7 |   71.17 |      0.01 | False    |
| Q05     | exasol            | trino               |         851.5 |         16708   |   19.62 |      0.05 | False    |
| Q06     | exasol            | trino               |         135.9 |          6698.6 |   49.29 |      0.02 | False    |
| Q07     | exasol            | trino               |        1194.6 |         13469.8 |   11.28 |      0.09 | False    |
| Q08     | exasol            | trino               |         291.3 |         22597.1 |   77.57 |      0.01 | False    |
| Q09     | exasol            | trino               |        3802.4 |         62055   |   16.32 |      0.06 | False    |
| Q10     | exasol            | trino               |        1090.6 |         19590.2 |   17.96 |      0.06 | False    |
| Q11     | exasol            | trino               |         231.5 |          2999.4 |   12.96 |      0.08 | False    |
| Q12     | exasol            | trino               |         290.8 |          7552.3 |   25.97 |      0.04 | False    |
| Q13     | exasol            | trino               |        2535.4 |         30068.7 |   11.86 |      0.08 | False    |
| Q14     | exasol            | trino               |         314.8 |          9648.3 |   30.65 |      0.03 | False    |
| Q15     | exasol            | trino               |         601.9 |         23083.9 |   38.35 |      0.03 | False    |
| Q16     | exasol            | trino               |        1057.6 |          6651   |    6.29 |      0.16 | False    |
| Q17     | exasol            | trino               |          47.1 |         21258.8 |  451.35 |      0    | False    |
| Q18     | exasol            | trino               |        1845.8 |         23879   |   12.94 |      0.08 | False    |
| Q19     | exasol            | trino               |          47.8 |          8761.2 |  183.29 |      0.01 | False    |
| Q20     | exasol            | trino               |         350.3 |         10304.1 |   29.42 |      0.03 | False    |
| Q21     | exasol            | trino               |         885.9 |         55919.1 |   63.12 |      0.02 | False    |
| Q22     | exasol            | trino               |         344.8 |         10061.9 |   29.18 |      0.03 | False    |

### Per-Stream Statistics

This benchmark was executed using **2 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 11551.0 | 8746.7 | 272.0 | 29497.6 |
| 1 | 55 | 10349.9 | 3927.1 | 686.1 | 35518.0 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 3927.1ms
- Slowest stream median: 8746.7ms
- Stream performance variation: 122.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 3434.3 | 2549.7 | 648.6 | 9623.1 |
| 1 | 55 | 3497.2 | 2812.9 | 414.2 | 9700.3 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 2549.7ms
- Slowest stream median: 2812.9ms
- Stream performance variation: 10.3% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 1039.7 | 832.4 | 47.4 | 4766.0 |
| 1 | 55 | 764.0 | 302.4 | 38.4 | 4661.7 |

**Performance Analysis for Exasol:**
- Fastest stream median: 302.4ms
- Slowest stream median: 832.4ms
- Stream performance variation: 175.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 3895.9 | 2918.6 | 233.3 | 13791.2 |
| 1 | 55 | 3213.5 | 1849.2 | 247.2 | 16020.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1849.2ms
- Slowest stream median: 2918.6ms
- Stream performance variation: 57.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 19619.5 | 14613.4 | 1516.3 | 63474.7 |
| 1 | 55 | 17367.3 | 14555.4 | 2951.8 | 65946.2 |

**Performance Analysis for Trino:**
- Fastest stream median: 14555.4ms
- Slowest stream median: 14613.4ms
- Stream performance variation: 0.4% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams

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
- Median runtime: 592.4ms
- Average runtime: 901.9ms
- Fastest query: 38.4ms
- Slowest query: 4766.0ms

**duckdb:**
- Median runtime: 2700.6ms
- Average runtime: 3465.8ms
- Fastest query: 414.2ms
- Slowest query: 9700.3ms

**starrocks:**
- Median runtime: 2572.6ms
- Average runtime: 3554.7ms
- Fastest query: 233.3ms
- Slowest query: 16020.0ms

**clickhouse:**
- Median runtime: 7026.0ms
- Average runtime: 10950.5ms
- Fastest query: 272.0ms
- Slowest query: 35518.0ms

**trino:**
- Median runtime: 14584.4ms
- Average runtime: 18493.4ms
- Fastest query: 1516.3ms
- Slowest query: 65946.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_2-benchmark.zip`](extscal_streams_2-benchmark.zip)

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
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Clickhouse 26.1.3.52:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 48g
  - max_threads: 8
  - max_memory_usage: 24000000000
  - max_bytes_before_external_group_by: 8000000000
  - max_bytes_before_external_sort: 8000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 16000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 35GB
  - query_max_memory_per_node: 35GB

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
  - memory_limit: 48GB
  - threads: 8


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 2 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts