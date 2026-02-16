# Streamlined Scalability - Stream Scaling (2 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-02-09 17:32:18

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 5 database systems:
- **exasol**
- **duckdb**
- **starrocks**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 1094.5ms median runtime
- trino was 35.1x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 2 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage

### Clickhouse 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** native
- **Data directory:** /data/clickhouse

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native

### Starrocks 4.0.4

**Software Configuration:**
- **Database:** starrocks 4.0.4
- **Setup method:** native

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


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
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (150GB)
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10AF1FBC56A5D0DE7 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10AF1FBC56A5D0DE7

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10AF1FBC56A5D0DE7 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10AF1FBC56A5D0DE7 /data

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



#### Starrocks 4.0.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44227BFD28AD58E37 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44227BFD28AD58E37

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44227BFD28AD58E37 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS44227BFD28AD58E37 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create starrocks data directory
sudo mkdir -p /data/starrocks

# Set ownership of /data/starrocks to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data/starrocks

```


**Tuning Parameters:**

**Data Directory:** `/data/starrocks`



#### Clickhouse 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS650185060D4308FC1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS650185060D4308FC1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS650185060D4308FC1 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS650185060D4308FC1 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `24g`
- Max threads: `4`
- Max memory usage: `12.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS274B72A61BA97B65B with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS274B72A61BA97B65B

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS274B72A61BA97B65B to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS274B72A61BA97B65B /data

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
| Clickhouse | 812.93s | 0.13s | 451.45s | 1482.70s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 798.13s | 0.14s | 406.01s | 1377.79s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 268.67s | 0.64s | 0.00s | 390.11s | N/A | N/A | N/A |
| Duckdb | 822.86s | 0.04s | 376.96s | 1252.17s | 412.9 MB | N/A | N/A |
| Exasol | 493.99s | 2.03s | 518.50s | 1381.95s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 390.11s
- Clickhouse took 1482.70s (3.8x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   9080.7 |      5 |     18063.3 |   18045.3 |   1581.6 |  15994.1 |  20332.5 |
| Q01     | duckdb     |   7767.6 |      5 |      6429.7 |    6810.9 |   2556.6 |   4551.6 |  11121.9 |
| Q01     | exasol     |   3099.1 |      5 |      5767.1 |    5204.6 |   1180.5 |   3114.3 |   5896.3 |
| Q01     | starrocks  |  13333.7 |      5 |     18980.1 |   18894.3 |    327.4 |  18535.6 |  19279.8 |
| Q01     | trino      |  21084.2 |      5 |     35391.2 |   35612.7 |   4511.8 |  30011.9 |  42345.1 |
| Q02     | clickhouse |   3941.7 |      5 |      7005   |    6853.1 |    591.2 |   5868.1 |   7360.7 |
| Q02     | duckdb     |    945.9 |      5 |      8048.3 |    6598.2 |   2917.3 |   3404.5 |   9844.3 |
| Q02     | exasol     |     98.9 |      5 |       193.1 |     194.3 |     36.9 |    138.2 |    233.1 |
| Q02     | starrocks  |    893.5 |      5 |      1114.3 |    1129.4 |    266.6 |    746.1 |   1412.7 |
| Q02     | trino      |  10376.5 |      5 |     16983.6 |   17266.6 |   3598.6 |  12428   |  21333.7 |
| Q03     | clickhouse |   9222.3 |      5 |      9167.8 |   13133.3 |   5725.2 |   8717.3 |  19906.2 |
| Q03     | duckdb     |   3657.5 |      5 |      4212   |    6266.3 |   5587.1 |   2605.2 |  16068.2 |
| Q03     | exasol     |   1095.4 |      5 |      1096.9 |    1483.2 |    536.2 |   1090.5 |   2135.1 |
| Q03     | starrocks  |   3482.8 |      5 |      3326.8 |    4253.5 |   1348.5 |   3187.5 |   5803.6 |
| Q03     | trino      |  25893.6 |      5 |     24925.5 |   31504.4 |  11312.3 |  23762.9 |  50051.4 |
| Q04     | clickhouse |  13797.6 |      5 |     20367.5 |   18502.1 |   4609   |  10354.3 |  21562.3 |
| Q04     | duckdb     |   2815.9 |      5 |      6324.9 |    9662.3 |   5882.7 |   4646.9 |  16157.6 |
| Q04     | exasol     |    207.4 |      5 |       405   |     405.7 |    139.8 |    205.6 |    600.5 |
| Q04     | starrocks  |   2947.1 |      5 |      4936.3 |    5315.3 |   1771.3 |   2837.3 |   7255.6 |
| Q04     | trino      |  20257.2 |      5 |     35831.1 |   33861.2 |   7852.9 |  20200.5 |  39542.9 |
| Q05     | clickhouse |   8900.4 |      5 |     18866   |   19033.9 |    588.7 |  18233.4 |  19702.9 |
| Q05     | duckdb     |   3157.1 |      5 |      8197.1 |    6948.1 |   2342.3 |   3631.5 |   8807.1 |
| Q05     | exasol     |    887.8 |      5 |      1692.4 |    1634.1 |    102.7 |   1472.4 |   1710.6 |
| Q05     | starrocks  |   5990.3 |      5 |      8573.2 |    9455.2 |   1944.4 |   7509.7 |  12337.5 |
| Q05     | trino      |  23271.7 |      5 |     51651   |   59690.2 |  18859.2 |  42130.8 |  90976.7 |
| Q06     | clickhouse |    635   |      5 |      1005.3 |     870.9 |    311   |    528.1 |   1153.7 |
| Q06     | duckdb     |    816.4 |      5 |      2104.8 |    3053.9 |   1788   |   1669.6 |   6011.9 |
| Q06     | exasol     |    134.6 |      5 |       260.6 |     211.3 |     69.5 |    135   |    264.5 |
| Q06     | starrocks  |    352.1 |      5 |       504.1 |     464.3 |    141   |    262.6 |    618.9 |
| Q06     | trino      |   8711.6 |      5 |     19920.5 |   28422.1 |  21037.8 |   7936.6 |  60865   |
| Q07     | clickhouse |  26429.6 |      5 |     45848.6 |   42588.3 |  10287.7 |  24396.1 |  49236.2 |
| Q07     | duckdb     |   2627.4 |      5 |      6020.9 |    4992.9 |   2147.6 |   2666.6 |   7114.8 |
| Q07     | exasol     |   1104.4 |      5 |      2000.7 |    1824.3 |    490.7 |   1104.9 |   2350.5 |
| Q07     | starrocks  |   3661.6 |      5 |      6232.1 |    6265.8 |   2405.7 |   3440.6 |   9898.5 |
| Q07     | trino      |  19081.2 |      5 |     56517.7 |   50563.9 |  15544.4 |  26878.9 |  66328.5 |
| Q08     | clickhouse |   9920.9 |      5 |     23034.3 |   22920.7 |    738.6 |  22081.6 |  23914.9 |
| Q08     | duckdb     |   2897.2 |      5 |      5686.7 |    8975.5 |   5032.7 |   5332.8 |  16582.3 |
| Q08     | exasol     |    260.1 |      5 |       509.6 |     458.3 |    133.4 |    261.7 |    592   |
| Q08     | starrocks  |   5130.4 |      5 |      8050   |    7529   |    891.3 |   6026.8 |   8091.7 |
| Q08     | trino      |  19460.9 |      5 |     50685.5 |   52016.9 |   9163.7 |  44078   |  66901.9 |
| Q09     | clickhouse |   6363.8 |      5 |     10285.4 |   10356.5 |    239.2 |  10028.9 |  10608.1 |
| Q09     | duckdb     |   8923.1 |      5 |     11969.7 |   12006.7 |   2012.5 |   9758.2 |  14819.2 |
| Q09     | exasol     |   3873.1 |      5 |      7959.4 |    7874.8 |    289.6 |   7524.5 |   8176.7 |
| Q09     | starrocks  |  10974.2 |      5 |     15749.8 |   16260.6 |   2774.9 |  14031.8 |  20945.2 |
| Q09     | trino      |  56915.1 |      5 |    106413   |  105048   |  10158.4 |  88912.9 | 116438   |
| Q10     | clickhouse |  17125.6 |      5 |     32612.5 |   32575.8 |   1596.1 |  30616.5 |  34771.1 |
| Q10     | duckdb     |   4194.5 |      5 |      6621.7 |    5858.8 |   1617.5 |   4070.4 |   7358.7 |
| Q10     | exasol     |   1197.3 |      5 |      1217   |    1659.7 |    620.1 |   1200.1 |   2374   |
| Q10     | starrocks  |   4069.7 |      5 |      7365.2 |    7213.9 |    489.4 |   6538.8 |   7801.7 |
| Q10     | trino      |  22075.8 |      5 |     55446.4 |   53057.8 |  18945   |  35654.2 |  81763.6 |
| Q11     | clickhouse |   1956.4 |      5 |      3902.9 |    3706.1 |   1134   |   1798.9 |   4749.9 |
| Q11     | duckdb     |    401.8 |      5 |      6442.7 |    6179.1 |   2510.5 |   3169.9 |   9267.1 |
| Q11     | exasol     |    219.2 |      5 |       400.8 |     356.7 |    128   |    224.7 |    523.4 |
| Q11     | starrocks  |    581.7 |      5 |       782.5 |     784.1 |    159.3 |    537.5 |    939.8 |
| Q11     | trino      |   3445.4 |      5 |      5727.9 |    6739.2 |   3475.2 |   2946.3 |  12192.7 |
| Q12     | clickhouse |   6773.5 |      5 |      5585.7 |    5809.5 |    382.7 |   5452.1 |   6327.2 |
| Q12     | duckdb     |   3085.7 |      5 |      6837.1 |    7591.8 |   2656.6 |   5596.9 |  12107.8 |
| Q12     | exasol     |    280   |      5 |       551.6 |     556.7 |     13.3 |    544.8 |    577   |
| Q12     | starrocks  |   1389.4 |      5 |      2439.5 |    2382.4 |    458.6 |   1895.1 |   3004.6 |
| Q12     | trino      |  11824.4 |      5 |     23767.3 |   23841   |   5313.9 |  16011   |  29770.7 |
| Q13     | clickhouse |   7529.5 |      5 |     13905.5 |   12642.7 |   3531.6 |   6716.6 |  15295.3 |
| Q13     | duckdb     |   7522.1 |      5 |     10421.7 |    9817.7 |   1410.1 |   7328.2 |  10705.2 |
| Q13     | exasol     |   2914.5 |      5 |      5384.6 |    4947.5 |   1152.1 |   2927   |   5813.5 |
| Q13     | starrocks  |   6195.6 |      5 |      8635   |    8043.3 |   1217.2 |   6002.2 |   8888.6 |
| Q13     | trino      |  30816.6 |      5 |     61439.6 |   62881.8 |  17786.4 |  38175.2 |  87942.9 |
| Q14     | clickhouse |    568.3 |      5 |      1244.6 |    1313.3 |    249   |   1042.9 |   1719.6 |
| Q14     | duckdb     |   2088.3 |      5 |      4819.8 |    4452.9 |    848.8 |   3086.3 |   5217.2 |
| Q14     | exasol     |    270.9 |      5 |       569.2 |     608.7 |    109.9 |    478.5 |    768.8 |
| Q14     | starrocks  |    362.5 |      5 |       692.3 |     678.4 |     97.6 |    560.3 |    808   |
| Q14     | trino      |  22070.3 |      5 |     28290.6 |   31921.6 |   7488.3 |  26493.1 |  44831.1 |
| Q15     | clickhouse |    495.1 |      5 |      1086.3 |    1061.1 |    113.6 |    886.9 |   1165.9 |
| Q15     | duckdb     |   1745.6 |      5 |      4569.3 |    7208.3 |   5457.4 |   2701.4 |  15513.6 |
| Q15     | exasol     |    659.9 |      5 |      1245   |    1229.5 |     36.5 |   1166.2 |   1255.5 |
| Q15     | starrocks  |    480.9 |      5 |       642   |     611.2 |    104.2 |    455.7 |    712.6 |
| Q15     | trino      |  23838.7 |      5 |     47115.5 |   52707.3 |  19001.8 |  28449.5 |  78080.7 |
| Q16     | clickhouse |   1912.1 |      5 |      4620.7 |    4519.8 |    352.9 |   4040.7 |   4949.5 |
| Q16     | duckdb     |   1281.6 |      5 |      2046.5 |    2414.6 |   1242.9 |   1301.2 |   4077.9 |
| Q16     | exasol     |    967.6 |      5 |      1757.8 |    1811.7 |    109.2 |   1708   |   1951.5 |
| Q16     | starrocks  |   1241.4 |      5 |      1337.7 |    1378.1 |     74.4 |   1307.4 |   1483.2 |
| Q16     | trino      |   8617.6 |      5 |     24853.3 |   30051.5 |  20094.8 |  16212   |  64955.8 |
| Q17     | clickhouse |   3965.6 |      5 |      6815.7 |    6845.3 |    703.4 |   6081.6 |   7919.7 |
| Q17     | duckdb     |   3220.5 |      5 |      6353.1 |    6693.2 |   2668.2 |   3262.2 |  10607.9 |
| Q17     | exasol     |     35.3 |      5 |        74.2 |      94.6 |     43.1 |     56.5 |    144   |
| Q17     | starrocks  |   2066.8 |      5 |      2786.3 |    2900.8 |    405.8 |   2530   |   3589.6 |
| Q17     | trino      |  29159.4 |      5 |     51879.5 |   55984.2 |  11675.5 |  48230.1 |  76691.3 |
| Q18     | clickhouse |   9902.5 |      5 |     21868.4 |   21523.2 |    874.5 |  20551   |  22578.8 |
| Q18     | duckdb     |   5959.5 |      5 |      9306   |   10562.6 |   3304.1 |   7620.5 |  14852.8 |
| Q18     | exasol     |   1829.3 |      5 |      3392.7 |    3103.4 |    719.4 |   1830.1 |   3520.7 |
| Q18     | starrocks  |  12136.2 |      5 |     20895.6 |   23916.6 |   7697.2 |  18712.6 |  37512   |
| Q18     | trino      |  29030.4 |      5 |     64382.5 |   66558.5 |  13410.3 |  54316.6 |  88808.3 |
| Q19     | clickhouse |  19264.6 |      5 |     37581.4 |   31330   |  11041.1 |  19182.1 |  40350.5 |
| Q19     | duckdb     |   3043.5 |      5 |      5518.6 |    4762.6 |   1266.1 |   3010.3 |   5777.9 |
| Q19     | exasol     |     84.4 |      5 |       117.3 |     149.8 |     86.6 |     83.6 |    290   |
| Q19     | starrocks  |   3002.3 |      5 |      3372.7 |    3303.4 |    420.8 |   2842.4 |   3724.3 |
| Q19     | trino      |  22734.4 |      5 |     34688.2 |   34358.3 |   6978   |  25960.5 |  43021.4 |
| Q20     | clickhouse |   5127.2 |      5 |      8920.8 |    8210.2 |   2711.8 |   3822.3 |  11232.5 |
| Q20     | duckdb     |   2760.8 |      5 |      5637.3 |    5111.2 |    957.8 |   3632.6 |   5852.9 |
| Q20     | exasol     |    581   |      5 |       584.9 |     812.8 |    316.5 |    578.1 |   1176.6 |
| Q20     | starrocks  |   1094.2 |      5 |      1287.5 |    1292.5 |    292.7 |   1004.8 |   1701.2 |
| Q20     | trino      |  23666.5 |      5 |     35326.1 |   34603.5 |   5805.4 |  25992.2 |  41624   |
| Q21     | clickhouse |   7910.2 |      5 |     15605.5 |   13692.9 |   4498.7 |   6398.2 |  17532.3 |
| Q21     | duckdb     |  13463.4 |      5 |     15449.5 |   15369.5 |   1280.2 |  13882.4 |  17311.4 |
| Q21     | exasol     |   1608.1 |      5 |      1659   |    2356.1 |   1002.7 |   1644   |   3809.1 |
| Q21     | starrocks  |  13888.8 |      5 |     27436.5 |   23517.4 |   9113.4 |  13707.8 |  32440.6 |
| Q21     | trino      |  68280.5 |      5 |    133331   |  135333   |  16159   | 119668   | 157370   |
| Q22     | clickhouse |   1764.1 |      5 |      4341.5 |    3848.2 |   1180.6 |   1775.1 |   4659.3 |
| Q22     | duckdb     |   1538.8 |      5 |      3311   |    3230.6 |    890.4 |   1990.9 |   4285   |
| Q22     | exasol     |    341.9 |      5 |       659   |     603.2 |    148   |    340.3 |    698.8 |
| Q22     | starrocks  |   1008.5 |      5 |      1493.6 |    1430.3 |    284.1 |    962.5 |   1731.5 |
| Q22     | trino      |   9398.8 |      5 |     18623.4 |   20786.6 |  10418.4 |   9366.1 |  37845.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        5767.1 |          6429.7 |    1.11 |      0.9  | False    |
| Q02     | exasol            | duckdb              |         193.1 |          8048.3 |   41.68 |      0.02 | False    |
| Q03     | exasol            | duckdb              |        1096.9 |          4212   |    3.84 |      0.26 | False    |
| Q04     | exasol            | duckdb              |         405   |          6324.9 |   15.62 |      0.06 | False    |
| Q05     | exasol            | duckdb              |        1692.4 |          8197.1 |    4.84 |      0.21 | False    |
| Q06     | exasol            | duckdb              |         260.6 |          2104.8 |    8.08 |      0.12 | False    |
| Q07     | exasol            | duckdb              |        2000.7 |          6020.9 |    3.01 |      0.33 | False    |
| Q08     | exasol            | duckdb              |         509.6 |          5686.7 |   11.16 |      0.09 | False    |
| Q09     | exasol            | duckdb              |        7959.4 |         11969.7 |    1.5  |      0.66 | False    |
| Q10     | exasol            | duckdb              |        1217   |          6621.7 |    5.44 |      0.18 | False    |
| Q11     | exasol            | duckdb              |         400.8 |          6442.7 |   16.07 |      0.06 | False    |
| Q12     | exasol            | duckdb              |         551.6 |          6837.1 |   12.4  |      0.08 | False    |
| Q13     | exasol            | duckdb              |        5384.6 |         10421.7 |    1.94 |      0.52 | False    |
| Q14     | exasol            | duckdb              |         569.2 |          4819.8 |    8.47 |      0.12 | False    |
| Q15     | exasol            | duckdb              |        1245   |          4569.3 |    3.67 |      0.27 | False    |
| Q16     | exasol            | duckdb              |        1757.8 |          2046.5 |    1.16 |      0.86 | False    |
| Q17     | exasol            | duckdb              |          74.2 |          6353.1 |   85.62 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3392.7 |          9306   |    2.74 |      0.36 | False    |
| Q19     | exasol            | duckdb              |         117.3 |          5518.6 |   47.05 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         584.9 |          5637.3 |    9.64 |      0.1  | False    |
| Q21     | exasol            | duckdb              |        1659   |         15449.5 |    9.31 |      0.11 | False    |
| Q22     | exasol            | duckdb              |         659   |          3311   |    5.02 |      0.2  | False    |
| Q01     | exasol            | starrocks           |        5767.1 |         18980.1 |    3.29 |      0.3  | False    |
| Q02     | exasol            | starrocks           |         193.1 |          1114.3 |    5.77 |      0.17 | False    |
| Q03     | exasol            | starrocks           |        1096.9 |          3326.8 |    3.03 |      0.33 | False    |
| Q04     | exasol            | starrocks           |         405   |          4936.3 |   12.19 |      0.08 | False    |
| Q05     | exasol            | starrocks           |        1692.4 |          8573.2 |    5.07 |      0.2  | False    |
| Q06     | exasol            | starrocks           |         260.6 |           504.1 |    1.93 |      0.52 | False    |
| Q07     | exasol            | starrocks           |        2000.7 |          6232.1 |    3.11 |      0.32 | False    |
| Q08     | exasol            | starrocks           |         509.6 |          8050   |   15.8  |      0.06 | False    |
| Q09     | exasol            | starrocks           |        7959.4 |         15749.8 |    1.98 |      0.51 | False    |
| Q10     | exasol            | starrocks           |        1217   |          7365.2 |    6.05 |      0.17 | False    |
| Q11     | exasol            | starrocks           |         400.8 |           782.5 |    1.95 |      0.51 | False    |
| Q12     | exasol            | starrocks           |         551.6 |          2439.5 |    4.42 |      0.23 | False    |
| Q13     | exasol            | starrocks           |        5384.6 |          8635   |    1.6  |      0.62 | False    |
| Q14     | exasol            | starrocks           |         569.2 |           692.3 |    1.22 |      0.82 | False    |
| Q15     | exasol            | starrocks           |        1245   |           642   |    0.52 |      1.94 | True     |
| Q16     | exasol            | starrocks           |        1757.8 |          1337.7 |    0.76 |      1.31 | True     |
| Q17     | exasol            | starrocks           |          74.2 |          2786.3 |   37.55 |      0.03 | False    |
| Q18     | exasol            | starrocks           |        3392.7 |         20895.6 |    6.16 |      0.16 | False    |
| Q19     | exasol            | starrocks           |         117.3 |          3372.7 |   28.75 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         584.9 |          1287.5 |    2.2  |      0.45 | False    |
| Q21     | exasol            | starrocks           |        1659   |         27436.5 |   16.54 |      0.06 | False    |
| Q22     | exasol            | starrocks           |         659   |          1493.6 |    2.27 |      0.44 | False    |
| Q01     | exasol            | clickhouse          |        5767.1 |         18063.3 |    3.13 |      0.32 | False    |
| Q02     | exasol            | clickhouse          |         193.1 |          7005   |   36.28 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |        1096.9 |          9167.8 |    8.36 |      0.12 | False    |
| Q04     | exasol            | clickhouse          |         405   |         20367.5 |   50.29 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1692.4 |         18866   |   11.15 |      0.09 | False    |
| Q06     | exasol            | clickhouse          |         260.6 |          1005.3 |    3.86 |      0.26 | False    |
| Q07     | exasol            | clickhouse          |        2000.7 |         45848.6 |   22.92 |      0.04 | False    |
| Q08     | exasol            | clickhouse          |         509.6 |         23034.3 |   45.2  |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        7959.4 |         10285.4 |    1.29 |      0.77 | False    |
| Q10     | exasol            | clickhouse          |        1217   |         32612.5 |   26.8  |      0.04 | False    |
| Q11     | exasol            | clickhouse          |         400.8 |          3902.9 |    9.74 |      0.1  | False    |
| Q12     | exasol            | clickhouse          |         551.6 |          5585.7 |   10.13 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        5384.6 |         13905.5 |    2.58 |      0.39 | False    |
| Q14     | exasol            | clickhouse          |         569.2 |          1244.6 |    2.19 |      0.46 | False    |
| Q15     | exasol            | clickhouse          |        1245   |          1086.3 |    0.87 |      1.15 | True     |
| Q16     | exasol            | clickhouse          |        1757.8 |          4620.7 |    2.63 |      0.38 | False    |
| Q17     | exasol            | clickhouse          |          74.2 |          6815.7 |   91.86 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3392.7 |         21868.4 |    6.45 |      0.16 | False    |
| Q19     | exasol            | clickhouse          |         117.3 |         37581.4 |  320.39 |      0    | False    |
| Q20     | exasol            | clickhouse          |         584.9 |          8920.8 |   15.25 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        1659   |         15605.5 |    9.41 |      0.11 | False    |
| Q22     | exasol            | clickhouse          |         659   |          4341.5 |    6.59 |      0.15 | False    |
| Q01     | exasol            | trino               |        5767.1 |         35391.2 |    6.14 |      0.16 | False    |
| Q02     | exasol            | trino               |         193.1 |         16983.6 |   87.95 |      0.01 | False    |
| Q03     | exasol            | trino               |        1096.9 |         24925.5 |   22.72 |      0.04 | False    |
| Q04     | exasol            | trino               |         405   |         35831.1 |   88.47 |      0.01 | False    |
| Q05     | exasol            | trino               |        1692.4 |         51651   |   30.52 |      0.03 | False    |
| Q06     | exasol            | trino               |         260.6 |         19920.5 |   76.44 |      0.01 | False    |
| Q07     | exasol            | trino               |        2000.7 |         56517.7 |   28.25 |      0.04 | False    |
| Q08     | exasol            | trino               |         509.6 |         50685.5 |   99.46 |      0.01 | False    |
| Q09     | exasol            | trino               |        7959.4 |        106413   |   13.37 |      0.07 | False    |
| Q10     | exasol            | trino               |        1217   |         55446.4 |   45.56 |      0.02 | False    |
| Q11     | exasol            | trino               |         400.8 |          5727.9 |   14.29 |      0.07 | False    |
| Q12     | exasol            | trino               |         551.6 |         23767.3 |   43.09 |      0.02 | False    |
| Q13     | exasol            | trino               |        5384.6 |         61439.6 |   11.41 |      0.09 | False    |
| Q14     | exasol            | trino               |         569.2 |         28290.6 |   49.7  |      0.02 | False    |
| Q15     | exasol            | trino               |        1245   |         47115.5 |   37.84 |      0.03 | False    |
| Q16     | exasol            | trino               |        1757.8 |         24853.3 |   14.14 |      0.07 | False    |
| Q17     | exasol            | trino               |          74.2 |         51879.5 |  699.18 |      0    | False    |
| Q18     | exasol            | trino               |        3392.7 |         64382.5 |   18.98 |      0.05 | False    |
| Q19     | exasol            | trino               |         117.3 |         34688.2 |  295.72 |      0    | False    |
| Q20     | exasol            | trino               |         584.9 |         35326.1 |   60.4  |      0.02 | False    |
| Q21     | exasol            | trino               |        1659   |        133331   |   80.37 |      0.01 | False    |
| Q22     | exasol            | trino               |         659   |         18623.4 |   28.26 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **2 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 14744.9 | 12213.5 | 528.1 | 45848.6 |
| 1 | 55 | 12471.7 | 7021.7 | 886.9 | 49236.2 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7021.7ms
- Slowest stream median: 12213.5ms
- Stream performance variation: 73.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 7101.5 | 6011.9 | 1301.2 | 17311.4 |
| 1 | 55 | 6950.1 | 5779.2 | 1318.4 | 16582.3 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 5779.2ms
- Slowest stream median: 6011.9ms
- Stream performance variation: 4.0% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 1965.4 | 1255.5 | 83.6 | 7959.4 |
| 1 | 55 | 1451.1 | 568.3 | 56.5 | 8176.7 |

**Performance Analysis for Exasol:**
- Fastest stream median: 568.3ms
- Slowest stream median: 1255.5ms
- Stream performance variation: 120.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 7227.0 | 5803.6 | 262.6 | 30259.5 |
| 1 | 55 | 6138.5 | 2719.0 | 504.1 | 37512.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2719.0ms
- Slowest stream median: 5803.6ms
- Stream performance variation: 113.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 55 | 49369.6 | 37180.3 | 2946.3 | 157370.4 |
| 1 | 55 | 43613.1 | 39542.9 | 5200.3 | 133331.3 |

**Performance Analysis for Trino:**
- Fastest stream median: 37180.3ms
- Slowest stream median: 39542.9ms
- Stream performance variation: 6.4% difference between fastest and slowest streams
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
- Median runtime: 1094.5ms
- Average runtime: 1708.2ms
- Fastest query: 56.5ms
- Slowest query: 8176.7ms

**duckdb:**
- Median runtime: 5804.5ms
- Average runtime: 7025.8ms
- Fastest query: 1301.2ms
- Slowest query: 17311.4ms

**starrocks:**
- Median runtime: 3349.8ms
- Average runtime: 6682.7ms
- Fastest query: 262.6ms
- Slowest query: 37512.0ms

**clickhouse:**
- Median runtime: 10156.7ms
- Average runtime: 13608.3ms
- Fastest query: 528.1ms
- Slowest query: 49236.2ms

**trino:**
- Median runtime: 38375.1ms
- Average runtime: 46491.4ms
- Fastest query: 2946.3ms
- Slowest query: 157370.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_2-benchmark.zip`](extscal_streams_2-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- See `attachments/system.json` for detailed system specifications

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

**Clickhouse 25.10.2.65:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 24g
  - max_threads: 4
  - max_memory_usage: 12000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 8000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 18GB
  - query_max_memory_per_node: 18GB

**Starrocks 4.0.4:**
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
- Measured runs executed across 2 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts