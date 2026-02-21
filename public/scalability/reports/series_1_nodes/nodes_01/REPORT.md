# Streamlined Scalability - Node Scaling (1 Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** N/A

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary


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
- **Hostname:** ip-10-0-1-183

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
- **Hostname:** ip-10-0-1-49

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
- **Hostname:** ip-10-0-1-102

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
- **Hostname:** ip-10-0-1-112


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
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuyXvteDMDjBYJETlLhd3p37+9RQ6bNJXyQwjv5qUwTnjjQIj3VSHUubduNPuvH6AS9mRlemRCc7+m43M3GJxUFQVx6yY/M5ohg/VY5D8greDR3FCoLxVkswNg1IMxC7WV8+Q8KihZ1dsrGEUFrX7SkW7u9B6gGYgYX50E0ESyCgwDiT/oS4BeRrKEtC+/fXvItohrjMN/XhQGljDePpxK412R2U8gYTli5d4RNMVDLBGba0ShqKCUJrxmgaud4AE12rTtFMO+9FGDEDBSaNd9nyyY1pDWg8SGGE/LhQVmpzY8g2R9Z3N9sPOqHtiJq9wltjCMzXqGUsyezYpb2nN3 ubuntu@ip-10-0-1-183&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS15D215C4F70FB9B60 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS15D215C4F70FB9B60

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS15D215C4F70FB9B60 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS15D215C4F70FB9B60 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66BAB823647EEDD13 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66BAB823647EEDD13

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66BAB823647EEDD13 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS66BAB823647EEDD13 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2389575C982FAFA81 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2389575C982FAFA81

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2389575C982FAFA81 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2389575C982FAFA81 /data

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
unzip extscal_nodes_1-benchmark.zip
cd extscal_nodes_1

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
| Clickhouse | 427.36s | 0.11s | 213.87s | 839.23s | 57.2 GB | 21.9 GB | 2.6x |
| Starrocks | 425.50s | 0.09s | 324.40s | 908.01s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 65.31s | 0.37s | 0.00s | 97.49s | N/A | N/A | N/A |
| Exasol | 178.28s | 1.98s | 258.85s | 518.86s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 97.49s
- Starrocks took 908.01s (9.3x slower)

### Performance Summary

| query   | system     |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |      5 |      5657.4 |    6241.5 |   1098   |   5222.1 |   7522.7 |
| Q01     | exasol     |      5 |      2527.5 |    2254.6 |    592.9 |   1217.8 |   2615.4 |
| Q01     | starrocks  |      5 |     11538.4 |   11463.3 |   5162   |   6000.2 |  16886.1 |
| Q01     | trino      |      5 |      9005.9 |   14344.2 |  11428.5 |   6770.2 |  34303.3 |
| Q02     | clickhouse |      5 |      6288.3 |    5413.7 |   2410.3 |   1881   |   7618.1 |
| Q02     | exasol     |      5 |       112.9 |     111.6 |     21   |     78.3 |    130.2 |
| Q02     | starrocks  |      5 |       803.4 |     787.5 |    260.2 |    401.9 |   1135.9 |
| Q02     | trino      |      5 |      3248.5 |    4888.3 |   2908.9 |   2609.9 |   9596.1 |
| Q03     | clickhouse |      5 |      9590.5 |    9436.2 |   4028.4 |   4355.5 |  14682.2 |
| Q03     | exasol     |      5 |       478.8 |     645   |    328.3 |    308.5 |   1017.1 |
| Q03     | starrocks  |      5 |       648.6 |    1456.4 |   1357.2 |    536.5 |   3659   |
| Q03     | trino      |      5 |     19362.6 |   19790.8 |   6201.4 |  13316.3 |  28470.6 |
| Q04     | clickhouse |      5 |     13490.2 |   12326.4 |   3382.2 |   6437.8 |  14520   |
| Q04     | exasol     |      5 |       205.3 |     194.4 |     54.2 |    115.6 |    258.6 |
| Q04     | starrocks  |      5 |      2194.8 |    2128.4 |    483.1 |   1502.8 |   2790.4 |
| Q04     | trino      |      5 |     10647.9 |   13288.1 |   6598.9 |   7364.4 |  24246.1 |
| Q05     | clickhouse |      5 |     18323.7 |   17395.7 |   2879.2 |  12445.1 |  19680.7 |
| Q05     | exasol     |      5 |       649   |     652   |    127.4 |    486.4 |    830.3 |
| Q05     | starrocks  |      5 |      3374.8 |    3013.1 |    638.1 |   2042.9 |   3576.3 |
| Q05     | trino      |      5 |     26133.4 |   26330.9 |   8659.6 |  14197.7 |  38645.2 |
| Q06     | clickhouse |      5 |      1247.9 |    1540.6 |   1516.3 |    464.1 |   4151.6 |
| Q06     | exasol     |      5 |       144.4 |     140.6 |     81.3 |     51.1 |    262.2 |
| Q06     | starrocks  |      5 |       466.6 |     848.5 |   1092.6 |     85   |   2726.1 |
| Q06     | trino      |      5 |      4705.5 |    5965.8 |   4047.7 |   2532.5 |  12987.2 |
| Q07     | clickhouse |      5 |      4005.6 |    4359.5 |   1292.3 |   2983.6 |   6083.9 |
| Q07     | exasol     |      5 |       855.1 |     779.5 |    303.4 |    262.3 |   1016.9 |
| Q07     | starrocks  |      5 |      2206.1 |    2262.6 |   1187.8 |    829.4 |   3976.4 |
| Q07     | trino      |      5 |      9783.3 |   14426   |   8840.3 |   7006.8 |  25294.3 |
| Q08     | clickhouse |      5 |     21646.1 |   21312.5 |   3095.3 |  17587.7 |  25412.3 |
| Q08     | exasol     |      5 |       278   |     248.9 |     62.2 |    150   |    300   |
| Q08     | starrocks  |      5 |      1851.3 |    3013.6 |   2014.9 |   1295.1 |   5931.6 |
| Q08     | trino      |      5 |      9542.6 |   12399.1 |   6931   |   7819.1 |  24559.3 |
| Q09     | clickhouse |      5 |     16523.2 |   17505.4 |   4915.6 |  12614   |  25794.3 |
| Q09     | exasol     |      5 |      3609.1 |    3607.3 |    204.1 |   3390.2 |   3817   |
| Q09     | starrocks  |      5 |      7692.5 |    7486.2 |   2153.6 |   5322.3 |  10522.7 |
| Q09     | trino      |      5 |     66501.1 |   72909.3 |  11963.6 |  62483.3 |  91942   |
| Q10     | clickhouse |      5 |     13522   |   12170.1 |   3448.6 |   6687.6 |  15352.1 |
| Q10     | exasol     |      5 |      1278.1 |    1065.9 |    360.1 |    643.5 |   1356.3 |
| Q10     | starrocks  |      5 |      3185.5 |    3592   |    917.7 |   2528.9 |   4688.4 |
| Q10     | trino      |      5 |     25959.9 |   26343.9 |  11327.7 |  14232.3 |  38141.4 |
| Q11     | clickhouse |      5 |      1851.7 |    2002.3 |   1190.5 |    754.4 |   3554.7 |
| Q11     | exasol     |      5 |       247.7 |     231.4 |     67   |    118.9 |    299.1 |
| Q11     | starrocks  |      5 |       596.2 |     585.4 |     59.1 |    491.6 |    647.9 |
| Q11     | trino      |      5 |      3998.9 |    4031.3 |   2644.2 |   1159.6 |   7829.6 |
| Q12     | clickhouse |      5 |      2467.7 |    4439.3 |   4364.9 |   1955.1 |  12156.5 |
| Q12     | exasol     |      5 |       298.8 |     293.9 |     30.3 |    258.9 |    334.8 |
| Q12     | starrocks  |      5 |      1011.2 |    1104.5 |    530.6 |    510.3 |   1930.1 |
| Q12     | trino      |      5 |      7979.1 |   10224   |   5938.7 |   5035.5 |  19596.2 |
| Q13     | clickhouse |      5 |      6309   |    7190.1 |   2979.5 |   4118.9 |  10752.8 |
| Q13     | exasol     |      5 |      2214   |    1964.3 |    564.3 |    986.5 |   2393.8 |
| Q13     | starrocks  |      5 |      4689.6 |    4567.7 |   1009.1 |   3099.6 |   5619.2 |
| Q13     | trino      |      5 |     23648.3 |   28654.4 |  11373.9 |  17770.7 |  42245.2 |
| Q14     | clickhouse |      5 |      3122.3 |    2936.2 |   1070.9 |   1309.5 |   4032.9 |
| Q14     | exasol     |      5 |       313.6 |     305.8 |     28.3 |    272   |    340.3 |
| Q14     | starrocks  |      5 |       667   |    1343.7 |   1198.7 |    513.3 |   3311   |
| Q14     | trino      |      5 |     16519.5 |   15822.8 |   7374   |   7759.6 |  26678.3 |
| Q15     | clickhouse |      5 |      1278.7 |    1663.1 |   1595.5 |    384.8 |   4441.1 |
| Q15     | exasol     |      5 |       753.6 |     736.3 |     32.1 |    687.8 |    765.9 |
| Q15     | starrocks  |      5 |      1339.3 |    1551.9 |   1234.9 |    513.2 |   3647.6 |
| Q15     | trino      |      5 |     12477.6 |   13865.7 |   4110.8 |  10719.6 |  20675.3 |
| Q16     | clickhouse |      5 |      2712.3 |    4661.4 |   3532.6 |   1912.6 |  10348.1 |
| Q16     | exasol     |      5 |      1089.5 |    1064.1 |     54.5 |    968.1 |   1096.7 |
| Q16     | starrocks  |      5 |      1015.9 |     997.8 |    192   |    763.1 |   1284.3 |
| Q16     | trino      |      5 |      4193.4 |    4337.8 |   1081.1 |   3258.1 |   5931.4 |
| Q17     | clickhouse |      5 |      3063.4 |    5603.2 |   4252   |   2085   |  11972.8 |
| Q17     | exasol     |      5 |        47.4 |      53.1 |      9.1 |     47.1 |     67.9 |
| Q17     | starrocks  |      5 |      2770   |    2480.2 |    721.3 |   1485.5 |   3119   |
| Q17     | trino      |      5 |     31312.1 |   31769.4 |  17468.9 |  12237.6 |  57848.3 |
| Q18     | clickhouse |      5 |     19581.1 |   19112.1 |   2338.1 |  15156.2 |  21348.5 |
| Q18     | exasol     |      5 |      1815   |    1731.5 |    192.3 |   1391.4 |   1856.6 |
| Q18     | starrocks  |      5 |     11827.9 |   12278.1 |   1584.8 |  10703.4 |  14892.2 |
| Q18     | trino      |      5 |     21350.2 |   23523.4 |   7205.3 |  16023.2 |  33241.7 |
| Q19     | clickhouse |      5 |     14298.5 |   13953.6 |   6107.6 |   4509.6 |  21474.3 |
| Q19     | exasol     |      5 |        51   |      53.2 |     21.6 |     28.3 |     81.5 |
| Q19     | starrocks  |      5 |      1484   |    1671.3 |    942   |    875.2 |   3148.7 |
| Q19     | trino      |      5 |      5332.4 |    8264.7 |   7021.2 |   4493.7 |  20764.2 |
| Q20     | clickhouse |      5 |      3981.6 |    4199.5 |   1630.6 |   2595.8 |   6714.8 |
| Q20     | exasol     |      5 |       378.4 |     418.8 |    126.2 |    254.1 |    557.1 |
| Q20     | starrocks  |      5 |      1015.7 |    1540.7 |   1084.3 |    787.9 |   3392.1 |
| Q20     | trino      |      5 |      5822.7 |    6307.5 |   1914.5 |   4439   |   9161.6 |
| Q21     | clickhouse |      5 |     11770.5 |   13128.8 |   4048.2 |   8699.5 |  18140.7 |
| Q21     | exasol     |      5 |      1196.8 |     990.5 |    372   |    533.3 |   1326.6 |
| Q21     | starrocks  |      5 |     12112.7 |   12048   |    836.5 |  10873.7 |  13133.5 |
| Q21     | trino      |      5 |     49813.8 |   50030.9 |  14148.2 |  30034.9 |  70030.3 |
| Q22     | clickhouse |      5 |      4425.3 |    5934.5 |   3673.6 |   3413.8 |  12317.1 |
| Q22     | exasol     |      5 |       322.5 |     295.6 |     94.1 |    135.1 |    382.6 |
| Q22     | starrocks  |      5 |      1467.4 |    1532.4 |    957.9 |    312.9 |   2575.5 |
| Q22     | trino      |      5 |      6944.9 |    7280.4 |   2981   |   3890.4 |  11930.8 |



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


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_1-benchmark.zip`](extscal_nodes_1-benchmark.zip)

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