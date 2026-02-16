# Streamlined Scalability - Stream Scaling (4 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-02-09 16:54:46

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
- exasol was the fastest overall with 759.5ms median runtime
- trino was 37.9x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS340518195A687B6D8 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS340518195A687B6D8

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS340518195A687B6D8 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS340518195A687B6D8 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS223874FA14A0325BB with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS223874FA14A0325BB

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS223874FA14A0325BB to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS223874FA14A0325BB /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10C13CC961BA7B5A7 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10C13CC961BA7B5A7

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10C13CC961BA7B5A7 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS10C13CC961BA7B5A7 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `12.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS649774C4015AE52E0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS649774C4015AE52E0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS649774C4015AE52E0 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS649774C4015AE52E0 /data

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
| Clickhouse | 550.97s | 0.13s | 276.69s | 1037.24s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 552.49s | 0.14s | 346.91s | 1057.69s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 141.36s | 0.39s | 0.00s | 200.57s | N/A | N/A | N/A |
| Duckdb | 539.82s | 0.04s | 198.56s | 764.56s | 412.9 MB | N/A | N/A |
| Exasol | 275.71s | 2.01s | 311.31s | 732.89s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 200.57s
- Starrocks took 1057.69s (5.3x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4648.8 |      5 |     14084.8 |   14921.6 |   3800.2 |  10215.2 |  20420   |
| Q01     | duckdb     |   2249.2 |      5 |      5401.9 |    5169.9 |    650   |   4445.1 |   5952.6 |
| Q01     | exasol     |   1607   |      5 |      5463   |    4717.5 |   1314.4 |   2625.5 |   5698.9 |
| Q01     | starrocks  |   6707.7 |      5 |     20841.2 |   20175.1 |   6807.4 |  11472.6 |  30047.8 |
| Q01     | trino      |  10187.2 |      5 |     42558.7 |   33982.7 |  14703.2 |  15281.5 |  48225   |
| Q02     | clickhouse |   2042.1 |      5 |      6877.4 |    7899.4 |   3367   |   4015.6 |  13122.9 |
| Q02     | duckdb     |    468.4 |      5 |      4117.3 |    5160.5 |   2410   |   3588.7 |   9426   |
| Q02     | exasol     |     88.1 |      5 |       205.1 |     206.8 |     25.1 |    181.5 |    248.1 |
| Q02     | starrocks  |    495.4 |      5 |       895.8 |     900.6 |    199.6 |    694.8 |   1194   |
| Q02     | trino      |   4631.4 |      5 |     10455.9 |    9943.7 |   1348.1 |   7776.5 |  11324   |
| Q03     | clickhouse |   4545   |      5 |     10867.1 |   12268   |   7284.1 |   4257.4 |  20355.8 |
| Q03     | duckdb     |   1418   |      5 |      3977.1 |    6582.8 |   5053.8 |   1277.3 |  12218.1 |
| Q03     | exasol     |    622.1 |      5 |       637.6 |    1344.6 |   1019.2 |    584   |   2605.7 |
| Q03     | starrocks  |   1494.8 |      5 |      1738.5 |    2669.8 |   1704.5 |   1316.4 |   4998.3 |
| Q03     | trino      |  13566.6 |      5 |     32120.9 |   37887.6 |  13869.2 |  21694   |  54452.7 |
| Q04     | clickhouse |   8943.4 |      5 |     22664   |   24561.8 |   8279.8 |  16162.7 |  37306.9 |
| Q04     | duckdb     |   1346.3 |      5 |      9162.2 |    8588.4 |   1535.8 |   6823   |  10214.1 |
| Q04     | exasol     |    110.9 |      5 |       418.3 |     439.2 |    220.3 |    172.8 |    783.1 |
| Q04     | starrocks  |   1281.5 |      5 |      3914.8 |    4173.4 |    866.7 |   3158.3 |   5203   |
| Q04     | trino      |   9775.4 |      5 |     27421.3 |   32961.1 |  12322.3 |  21036   |  51940.8 |
| Q05     | clickhouse |   3513.6 |      5 |     16862.2 |   17961.9 |   4038.3 |  13414.2 |  24446.7 |
| Q05     | duckdb     |   1488.5 |      5 |      5395   |    5877.5 |   1340.1 |   4853.7 |   8227.8 |
| Q05     | exasol     |    493.1 |      5 |      1682   |    1528.4 |    451.6 |    735.8 |   1872.8 |
| Q05     | starrocks  |   2620.8 |      5 |      7537.6 |    8468.9 |   3080.2 |   5271.9 |  12615   |
| Q05     | trino      |  12848.6 |      5 |     64701.7 |   77982.3 |  25018.3 |  62361   | 120861   |
| Q06     | clickhouse |    293.5 |      5 |      2980.5 |    3239.2 |   1761.6 |    981   |   5769.7 |
| Q06     | duckdb     |    404.8 |      5 |      3640   |    2952.5 |   1594.4 |    419.4 |   4231.3 |
| Q06     | exasol     |     72.6 |      5 |       263.3 |     278.4 |    186.1 |    134.7 |    591   |
| Q06     | starrocks  |    196.1 |      5 |       452.8 |     522.4 |    204.1 |    292.2 |    805.2 |
| Q06     | trino      |   4240.2 |      5 |     16645.1 |   15175.1 |   7347.7 |   7198.1 |  23316.1 |
| Q07     | clickhouse |  13288   |      5 |     38645.8 |   36474.9 |  14618   |  12758.2 |  52568.3 |
| Q07     | duckdb     |   1327.8 |      5 |      4980.2 |    4787.5 |   2561   |   1347.9 |   8492.8 |
| Q07     | exasol     |    615.5 |      5 |      2541.7 |    2085.1 |    886.8 |    570.2 |   2736.5 |
| Q07     | starrocks  |   1519.7 |      5 |      4577.9 |    4015.2 |   1436.3 |   1459.3 |   4900.2 |
| Q07     | trino      |  10072.8 |      5 |     26615.6 |   26232.6 |  11300.4 |  14293.7 |  39766.4 |
| Q08     | clickhouse |   5050.8 |      5 |     22085   |   20885.6 |   3702.4 |  14558.2 |  23979.9 |
| Q08     | duckdb     |   1442.3 |      5 |      8069.1 |    7042.6 |   1667.8 |   4634   |   8315.1 |
| Q08     | exasol     |    163.6 |      5 |       578.9 |     567.6 |    172.6 |    292.2 |    717.4 |
| Q08     | starrocks  |   2180.3 |      5 |      6036   |    6644   |    987.3 |   5839.1 |   8028.4 |
| Q08     | trino      |  10084.2 |      5 |     26219.4 |   30435.5 |  16894.6 |  15556.3 |  59503.8 |
| Q09     | clickhouse |   2968.9 |      5 |     13858.6 |   13830.1 |   2566.9 |  10255.5 |  17508.7 |
| Q09     | duckdb     |   4420.8 |      5 |      9754.2 |   10637.7 |   3391.2 |   7189.4 |  16195.6 |
| Q09     | exasol     |   2071.6 |      5 |      8404.9 |    8000.6 |   1026.9 |   6231.6 |   8685.3 |
| Q09     | starrocks  |   5904.2 |      5 |     11540.9 |   11655.1 |   1037.7 |  10467.7 |  12921.6 |
| Q09     | trino      |  30288.3 |      5 |    109375   |  132734   |  64418.1 |  92019.7 | 246976   |
| Q10     | clickhouse |   8469.8 |      5 |     30095.1 |   31393.6 |   3774.5 |  28288.2 |  37397.3 |
| Q10     | duckdb     |   2150.3 |      5 |      5905.1 |    7649.2 |   4499.7 |   3107.9 |  14754.8 |
| Q10     | exasol     |    745.8 |      5 |      2281.8 |    1997.8 |    695.2 |   1212.7 |   2619.4 |
| Q10     | starrocks  |   2115.1 |      5 |      4815.8 |    4714.9 |    393.9 |   4065.3 |   5064.1 |
| Q10     | trino      |  10136.8 |      5 |     44153.5 |   47518.2 |  23715.3 |  19407.2 |  82051.2 |
| Q11     | clickhouse |    992.2 |      5 |      8673.2 |    8753.6 |   2115.9 |   6509.5 |  11741.9 |
| Q11     | duckdb     |    200.7 |      5 |      4230.7 |    4708.5 |   1903.1 |   2442.9 |   7097.2 |
| Q11     | exasol     |    162.3 |      5 |       500.6 |     491.4 |    169.1 |    242.7 |    717.9 |
| Q11     | starrocks  |    314.2 |      5 |       601.5 |     588.4 |    108   |    406.1 |    686.7 |
| Q11     | trino      |   1899.3 |      5 |      5456.7 |    5493.8 |   1804.9 |   2674.6 |   7305.9 |
| Q12     | clickhouse |   3327.4 |      5 |      5623   |    6358   |   3262   |   3574.1 |  11747.5 |
| Q12     | duckdb     |   1531.3 |      5 |      8414.6 |    9673.9 |   2689.8 |   7890.8 |  14265   |
| Q12     | exasol     |    149.9 |      5 |       561.9 |     598.6 |    163.6 |    480.7 |    883.3 |
| Q12     | starrocks  |    619.9 |      5 |      1596.7 |    1580.1 |    237.7 |   1328.7 |   1876.1 |
| Q12     | trino      |   4853.9 |      5 |     29560.8 |   28528.4 |   7924   |  15272.6 |  35703.9 |
| Q13     | clickhouse |   4472.3 |      5 |     12371.1 |   13096.5 |   2887.5 |   9615.1 |  17510.3 |
| Q13     | duckdb     |   3668   |      5 |      7277.1 |    8105.2 |   3345.9 |   3693.5 |  12389.3 |
| Q13     | exasol     |   1487.9 |      5 |      5356.9 |    4897.5 |   1307.4 |   2591.6 |   5815.6 |
| Q13     | starrocks  |   3261.7 |      5 |      8263.8 |    7869.1 |   2980.8 |   3298.7 |  11581   |
| Q13     | trino      |  16142.6 |      5 |     68181.1 |   59475   |  19351.9 |  31250.7 |  77324.8 |
| Q14     | clickhouse |    320   |      5 |      5271.6 |    4604.9 |   1757.7 |   1975.8 |   6453.1 |
| Q14     | duckdb     |   1064.9 |      5 |      4833.6 |    6492.7 |   3405.1 |   3169.7 |  10705.9 |
| Q14     | exasol     |    148.5 |      5 |       586   |     613.5 |     58   |    565.9 |    698.5 |
| Q14     | starrocks  |    222.1 |      5 |       590   |     611.6 |    157.7 |    435.1 |    866.7 |
| Q14     | trino      |   6279.7 |      5 |     23146.3 |   22872.6 |   5786.1 |  14550.9 |  30898.9 |
| Q15     | clickhouse |    343   |      5 |      5754.1 |    4653.4 |   2105   |   2266.9 |   6552.7 |
| Q15     | duckdb     |    901.7 |      5 |      6306.9 |    5563.1 |   1506.5 |   3352.7 |   6764   |
| Q15     | exasol     |    406.3 |      5 |      1304.4 |    1295.7 |     41.5 |   1233.8 |   1340.5 |
| Q15     | starrocks  |    225.6 |      5 |       488.6 |     578   |    178.1 |    456.7 |    875.7 |
| Q15     | trino      |  11509.5 |      5 |     29353.1 |   31563.5 |   9429.3 |  20318.2 |  46187.5 |
| Q16     | clickhouse |   1021.4 |      5 |      6886.2 |    7238.1 |   2755.1 |   4413.3 |  11020   |
| Q16     | duckdb     |    679.1 |      5 |      4474.2 |    5144   |   1571.7 |   3530.2 |   7412.8 |
| Q16     | exasol     |    611.5 |      5 |      1952.3 |    1952.1 |     69   |   1863.8 |   2019.6 |
| Q16     | starrocks  |    734.6 |      5 |      1152.3 |    1115.3 |    178.1 |    842.2 |   1272.6 |
| Q16     | trino      |   3159.4 |      5 |     13834.7 |   14750.3 |   4766.6 |   9901.8 |  22324.6 |
| Q17     | clickhouse |   1956.2 |      5 |      7716.9 |    8778.6 |   3666.5 |   4838.9 |  14541.2 |
| Q17     | duckdb     |   1615.4 |      5 |      6939.5 |    6425.8 |   3589   |   1607.6 |  10574.2 |
| Q17     | exasol     |     30.4 |      5 |        95.9 |      98.6 |     42.6 |     62.9 |    168.6 |
| Q17     | starrocks  |   1470.4 |      5 |      3343.1 |    3380.2 |    583.2 |   2604.3 |   4085.3 |
| Q17     | trino      |  13219.9 |      5 |     41507.1 |   38248.6 |   9391.3 |  27608.3 |  48305.3 |
| Q18     | clickhouse |   4668.1 |      5 |     22603.5 |   24191.9 |   7507.6 |  17912.1 |  37086.6 |
| Q18     | duckdb     |   3053.6 |      5 |      7376.9 |    8287.2 |   2225.6 |   6792.2 |  12204.5 |
| Q18     | exasol     |    983.2 |      5 |      3447.5 |    3123   |    756.2 |   1772.6 |   3509.7 |
| Q18     | starrocks  |   6193.4 |      5 |     33731.3 |   33233.6 |   9654.1 |  24127.9 |  48571.9 |
| Q18     | trino      |  12671.6 |      5 |     62013.9 |   61128.7 |  19805.5 |  29438.7 |  79499.1 |
| Q19     | clickhouse |   9807.4 |      5 |     27132.7 |   26449.5 |   3223.4 |  20990   |  29566   |
| Q19     | duckdb     |   1540   |      5 |      7203.7 |    7461.3 |   2784.5 |   3946   |  11751.1 |
| Q19     | exasol     |     59.3 |      5 |       140.3 |     183.8 |    112   |     89.5 |    353.6 |
| Q19     | starrocks  |   2146   |      5 |      4332.7 |    4100.7 |   1063.7 |   2328.2 |   4979.7 |
| Q19     | trino      |   7200.3 |      5 |     11272.2 |   18343.5 |  11576.6 |   8573   |  34088.6 |
| Q20     | clickhouse |   2660.4 |      5 |      8954.6 |    9488.1 |   2439.8 |   6528.8 |  12754.7 |
| Q20     | duckdb     |   1380   |      5 |      4053.6 |    6043.5 |   4633.1 |   3104   |  14189.8 |
| Q20     | exasol     |    347.2 |      5 |       936.4 |     908.1 |    359.7 |    509.9 |   1386.2 |
| Q20     | starrocks  |    480.4 |      5 |      1117.2 |    1194.1 |    467.4 |    797.9 |   1992.9 |
| Q20     | trino      |   7260.8 |      5 |     12701.3 |   17711.7 |  11116.5 |  11256.2 |  37386.1 |
| Q21     | clickhouse |   4087.9 |      5 |     14840.3 |   15864   |   3779.1 |  12293.6 |  21969.5 |
| Q21     | duckdb     |   6901   |      5 |      9871.1 |   11463.8 |   2417   |   9377.5 |  14147.4 |
| Q21     | exasol     |    852.8 |      5 |      2463.9 |    2585.3 |   1166.9 |   1198.2 |   3786   |
| Q21     | starrocks  |   7636   |      5 |     22137.6 |   20124.2 |   5259.3 |  10836.4 |  23610.8 |
| Q21     | trino      |  31430.9 |      5 |     82925.8 |   75013.3 |  28606.5 |  32975.5 | 109692   |
| Q22     | clickhouse |    924.7 |      5 |      7590.8 |    6482.3 |   2588.1 |   3111.2 |   9317.9 |
| Q22     | duckdb     |    797.6 |      5 |     10051.4 |    9996.7 |   3264   |   6091.7 |  14916.1 |
| Q22     | exasol     |    177.7 |      5 |       642.7 |     572.1 |    185.3 |    250.8 |    703.7 |
| Q22     | starrocks  |    606.6 |      5 |      1497.7 |    1346.7 |    478.4 |    540.4 |   1812.4 |
| Q22     | trino      |   4754.1 |      5 |     13427.5 |   14524.1 |   4815.5 |  10926.7 |  22796.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        5463   |          5401.9 |    0.99 |      1.01 | True     |
| Q02     | exasol            | duckdb              |         205.1 |          4117.3 |   20.07 |      0.05 | False    |
| Q03     | exasol            | duckdb              |         637.6 |          3977.1 |    6.24 |      0.16 | False    |
| Q04     | exasol            | duckdb              |         418.3 |          9162.2 |   21.9  |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1682   |          5395   |    3.21 |      0.31 | False    |
| Q06     | exasol            | duckdb              |         263.3 |          3640   |   13.82 |      0.07 | False    |
| Q07     | exasol            | duckdb              |        2541.7 |          4980.2 |    1.96 |      0.51 | False    |
| Q08     | exasol            | duckdb              |         578.9 |          8069.1 |   13.94 |      0.07 | False    |
| Q09     | exasol            | duckdb              |        8404.9 |          9754.2 |    1.16 |      0.86 | False    |
| Q10     | exasol            | duckdb              |        2281.8 |          5905.1 |    2.59 |      0.39 | False    |
| Q11     | exasol            | duckdb              |         500.6 |          4230.7 |    8.45 |      0.12 | False    |
| Q12     | exasol            | duckdb              |         561.9 |          8414.6 |   14.98 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        5356.9 |          7277.1 |    1.36 |      0.74 | False    |
| Q14     | exasol            | duckdb              |         586   |          4833.6 |    8.25 |      0.12 | False    |
| Q15     | exasol            | duckdb              |        1304.4 |          6306.9 |    4.84 |      0.21 | False    |
| Q16     | exasol            | duckdb              |        1952.3 |          4474.2 |    2.29 |      0.44 | False    |
| Q17     | exasol            | duckdb              |          95.9 |          6939.5 |   72.36 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3447.5 |          7376.9 |    2.14 |      0.47 | False    |
| Q19     | exasol            | duckdb              |         140.3 |          7203.7 |   51.34 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         936.4 |          4053.6 |    4.33 |      0.23 | False    |
| Q21     | exasol            | duckdb              |        2463.9 |          9871.1 |    4.01 |      0.25 | False    |
| Q22     | exasol            | duckdb              |         642.7 |         10051.4 |   15.64 |      0.06 | False    |
| Q01     | exasol            | starrocks           |        5463   |         20841.2 |    3.81 |      0.26 | False    |
| Q02     | exasol            | starrocks           |         205.1 |           895.8 |    4.37 |      0.23 | False    |
| Q03     | exasol            | starrocks           |         637.6 |          1738.5 |    2.73 |      0.37 | False    |
| Q04     | exasol            | starrocks           |         418.3 |          3914.8 |    9.36 |      0.11 | False    |
| Q05     | exasol            | starrocks           |        1682   |          7537.6 |    4.48 |      0.22 | False    |
| Q06     | exasol            | starrocks           |         263.3 |           452.8 |    1.72 |      0.58 | False    |
| Q07     | exasol            | starrocks           |        2541.7 |          4577.9 |    1.8  |      0.56 | False    |
| Q08     | exasol            | starrocks           |         578.9 |          6036   |   10.43 |      0.1  | False    |
| Q09     | exasol            | starrocks           |        8404.9 |         11540.9 |    1.37 |      0.73 | False    |
| Q10     | exasol            | starrocks           |        2281.8 |          4815.8 |    2.11 |      0.47 | False    |
| Q11     | exasol            | starrocks           |         500.6 |           601.5 |    1.2  |      0.83 | False    |
| Q12     | exasol            | starrocks           |         561.9 |          1596.7 |    2.84 |      0.35 | False    |
| Q13     | exasol            | starrocks           |        5356.9 |          8263.8 |    1.54 |      0.65 | False    |
| Q14     | exasol            | starrocks           |         586   |           590   |    1.01 |      0.99 | False    |
| Q15     | exasol            | starrocks           |        1304.4 |           488.6 |    0.37 |      2.67 | True     |
| Q16     | exasol            | starrocks           |        1952.3 |          1152.3 |    0.59 |      1.69 | True     |
| Q17     | exasol            | starrocks           |          95.9 |          3343.1 |   34.86 |      0.03 | False    |
| Q18     | exasol            | starrocks           |        3447.5 |         33731.3 |    9.78 |      0.1  | False    |
| Q19     | exasol            | starrocks           |         140.3 |          4332.7 |   30.88 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         936.4 |          1117.2 |    1.19 |      0.84 | False    |
| Q21     | exasol            | starrocks           |        2463.9 |         22137.6 |    8.98 |      0.11 | False    |
| Q22     | exasol            | starrocks           |         642.7 |          1497.7 |    2.33 |      0.43 | False    |
| Q01     | exasol            | clickhouse          |        5463   |         14084.8 |    2.58 |      0.39 | False    |
| Q02     | exasol            | clickhouse          |         205.1 |          6877.4 |   33.53 |      0.03 | False    |
| Q03     | exasol            | clickhouse          |         637.6 |         10867.1 |   17.04 |      0.06 | False    |
| Q04     | exasol            | clickhouse          |         418.3 |         22664   |   54.18 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1682   |         16862.2 |   10.03 |      0.1  | False    |
| Q06     | exasol            | clickhouse          |         263.3 |          2980.5 |   11.32 |      0.09 | False    |
| Q07     | exasol            | clickhouse          |        2541.7 |         38645.8 |   15.2  |      0.07 | False    |
| Q08     | exasol            | clickhouse          |         578.9 |         22085   |   38.15 |      0.03 | False    |
| Q09     | exasol            | clickhouse          |        8404.9 |         13858.6 |    1.65 |      0.61 | False    |
| Q10     | exasol            | clickhouse          |        2281.8 |         30095.1 |   13.19 |      0.08 | False    |
| Q11     | exasol            | clickhouse          |         500.6 |          8673.2 |   17.33 |      0.06 | False    |
| Q12     | exasol            | clickhouse          |         561.9 |          5623   |   10.01 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        5356.9 |         12371.1 |    2.31 |      0.43 | False    |
| Q14     | exasol            | clickhouse          |         586   |          5271.6 |    9    |      0.11 | False    |
| Q15     | exasol            | clickhouse          |        1304.4 |          5754.1 |    4.41 |      0.23 | False    |
| Q16     | exasol            | clickhouse          |        1952.3 |          6886.2 |    3.53 |      0.28 | False    |
| Q17     | exasol            | clickhouse          |          95.9 |          7716.9 |   80.47 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3447.5 |         22603.5 |    6.56 |      0.15 | False    |
| Q19     | exasol            | clickhouse          |         140.3 |         27132.7 |  193.39 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         936.4 |          8954.6 |    9.56 |      0.1  | False    |
| Q21     | exasol            | clickhouse          |        2463.9 |         14840.3 |    6.02 |      0.17 | False    |
| Q22     | exasol            | clickhouse          |         642.7 |          7590.8 |   11.81 |      0.08 | False    |
| Q01     | exasol            | trino               |        5463   |         42558.7 |    7.79 |      0.13 | False    |
| Q02     | exasol            | trino               |         205.1 |         10455.9 |   50.98 |      0.02 | False    |
| Q03     | exasol            | trino               |         637.6 |         32120.9 |   50.38 |      0.02 | False    |
| Q04     | exasol            | trino               |         418.3 |         27421.3 |   65.55 |      0.02 | False    |
| Q05     | exasol            | trino               |        1682   |         64701.7 |   38.47 |      0.03 | False    |
| Q06     | exasol            | trino               |         263.3 |         16645.1 |   63.22 |      0.02 | False    |
| Q07     | exasol            | trino               |        2541.7 |         26615.6 |   10.47 |      0.1  | False    |
| Q08     | exasol            | trino               |         578.9 |         26219.4 |   45.29 |      0.02 | False    |
| Q09     | exasol            | trino               |        8404.9 |        109375   |   13.01 |      0.08 | False    |
| Q10     | exasol            | trino               |        2281.8 |         44153.5 |   19.35 |      0.05 | False    |
| Q11     | exasol            | trino               |         500.6 |          5456.7 |   10.9  |      0.09 | False    |
| Q12     | exasol            | trino               |         561.9 |         29560.8 |   52.61 |      0.02 | False    |
| Q13     | exasol            | trino               |        5356.9 |         68181.1 |   12.73 |      0.08 | False    |
| Q14     | exasol            | trino               |         586   |         23146.3 |   39.5  |      0.03 | False    |
| Q15     | exasol            | trino               |        1304.4 |         29353.1 |   22.5  |      0.04 | False    |
| Q16     | exasol            | trino               |        1952.3 |         13834.7 |    7.09 |      0.14 | False    |
| Q17     | exasol            | trino               |          95.9 |         41507.1 |  432.82 |      0    | False    |
| Q18     | exasol            | trino               |        3447.5 |         62013.9 |   17.99 |      0.06 | False    |
| Q19     | exasol            | trino               |         140.3 |         11272.2 |   80.34 |      0.01 | False    |
| Q20     | exasol            | trino               |         936.4 |         12701.3 |   13.56 |      0.07 | False    |
| Q21     | exasol            | trino               |        2463.9 |         82925.8 |   33.66 |      0.03 | False    |
| Q22     | exasol            | trino               |         642.7 |         13427.5 |   20.89 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 15292.3 | 13086.2 | 981.0 | 41817.6 |
| 1 | 28 | 13972.7 | 11433.9 | 1975.8 | 37306.9 |
| 2 | 27 | 15132.6 | 12754.7 | 2583.2 | 37397.3 |
| 3 | 27 | 13665.8 | 8906.7 | 2472.9 | 52568.3 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 8906.7ms
- Slowest stream median: 13086.2ms
- Stream performance variation: 46.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6767.6 | 6199.3 | 1277.3 | 14147.4 |
| 1 | 28 | 6992.0 | 6865.9 | 419.4 | 14916.1 |
| 2 | 27 | 7072.8 | 6823.0 | 2374.9 | 16195.6 |
| 3 | 27 | 7142.1 | 6181.3 | 3104.0 | 14265.0 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6181.3ms
- Slowest stream median: 6865.9ms
- Stream performance variation: 11.1% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 2007.6 | 1868.3 | 134.7 | 5495.0 |
| 1 | 28 | 1426.4 | 673.5 | 66.0 | 8685.3 |
| 2 | 27 | 1977.3 | 883.3 | 89.5 | 8676.5 |
| 3 | 27 | 1588.3 | 586.0 | 62.9 | 8404.9 |

**Performance Analysis for Exasol:**
- Fastest stream median: 586.0ms
- Slowest stream median: 1868.3ms
- Stream performance variation: 218.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6770.5 | 4321.6 | 292.2 | 33851.4 |
| 1 | 28 | 6180.6 | 2840.9 | 435.1 | 48571.9 |
| 2 | 27 | 6411.1 | 4332.7 | 406.1 | 30047.8 |
| 3 | 27 | 6021.4 | 1876.1 | 600.4 | 25885.3 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1876.1ms
- Slowest stream median: 4332.7ms
- Stream performance variation: 130.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 39273.7 | 31685.8 | 5456.7 | 109691.9 |
| 1 | 28 | 34776.2 | 27425.5 | 5224.5 | 114191.8 |
| 2 | 27 | 42681.8 | 21036.0 | 2674.6 | 246976.1 |
| 3 | 27 | 34693.5 | 28799.6 | 6807.2 | 92019.7 |

**Performance Analysis for Trino:**
- Fastest stream median: 21036.0ms
- Slowest stream median: 31685.8ms
- Stream performance variation: 50.6% difference between fastest and slowest streams
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
- Median runtime: 759.5ms
- Average runtime: 1749.3ms
- Fastest query: 62.9ms
- Slowest query: 8685.3ms

**duckdb:**
- Median runtime: 6778.1ms
- Average runtime: 6991.6ms
- Fastest query: 419.4ms
- Slowest query: 16195.6ms

**starrocks:**
- Median runtime: 3499.7ms
- Average runtime: 6348.2ms
- Fastest query: 292.2ms
- Slowest query: 48571.9ms

**clickhouse:**
- Median runtime: 12332.4ms
- Average runtime: 14518.0ms
- Fastest query: 981.0ms
- Slowest query: 52568.3ms

**trino:**
- Median runtime: 28785.1ms
- Average runtime: 37841.2ms
- Fastest query: 2674.6ms
- Slowest query: 246976.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_4-benchmark.zip`](extscal_streams_4-benchmark.zip)

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
  - memory_limit: 48g
  - max_threads: 8
  - max_memory_usage: 12000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 8000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 35GB
  - query_max_memory_per_node: 35GB

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts