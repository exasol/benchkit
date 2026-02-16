# Streamlined Scalability - Scale Factor 25 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-02-09 21:44:23

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
- exasol was the fastest overall with 818.1ms median runtime
- trino was 43.9x slower- Tested 550 total query executions across 22 different TPC-H queries
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

# Create 42GB partition for data generation
sudo parted -s /dev/nvme0n1 mkpart primary ext4 1MiB 42GiB

# Create raw partition for Exasol (178GB)
sudo parted -s /dev/nvme0n1 mkpart primary 42GiB 100%

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B9C54A8A861229B with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B9C54A8A861229B

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B9C54A8A861229B to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43B9C54A8A861229B /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6464C098E96E2837F with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6464C098E96E2837F

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6464C098E96E2837F to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6464C098E96E2837F /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS211027B6B825D9A2D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS211027B6B825D9A2D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS211027B6B825D9A2D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS211027B6B825D9A2D /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `24g`
- Max threads: `4`
- Max memory usage: `7.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4AB1E52A4A6845A32 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4AB1E52A4A6845A32

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4AB1E52A4A6845A32 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4AB1E52A4A6845A32 /data

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
- **Scale factor:** 25
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
unzip extscal_sf_25-benchmark.zip
cd extscal_sf_25

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
| Clickhouse | 419.91s | 0.14s | 210.97s | 715.53s | 22.3 GB | 10.0 GB | 2.2x |
| Starrocks | 414.89s | 0.16s | 199.58s | 706.21s | 7.4 GB | 7.4 GB | 1.0x |
| Trino | 114.26s | 0.51s | 0.00s | 182.95s | N/A | N/A | N/A |
| Duckdb | 415.64s | 0.04s | 200.83s | 642.75s | 206.5 MB | N/A | N/A |
| Exasol | 246.01s | 1.99s | 254.91s | 634.49s | 23.9 GB | 5.2 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 182.95s
- Clickhouse took 715.53s (3.9x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4641.1 |      5 |     18682.6 |   18154.4 |   4972.9 |  12092   |  23745.2 |
| Q01     | duckdb     |   2311.1 |      5 |      5391.5 |    5109.8 |    873.7 |   3927.3 |   5893.1 |
| Q01     | exasol     |   1564.4 |      5 |      3548.2 |    4482.1 |   1783.1 |   2726.8 |   6859.9 |
| Q01     | starrocks  |   8131.6 |      5 |     21476.9 |   23038.2 |   6404.2 |  14853.4 |  32422.6 |
| Q01     | trino      |  11949.2 |      5 |     31125   |   29644   |   8505.6 |  15926.6 |  37856.8 |
| Q02     | clickhouse |   1953.2 |      5 |      9376.8 |    9173.2 |   2396.6 |   6453.1 |  12658.6 |
| Q02     | duckdb     |    474.1 |      5 |      4135.9 |    5999.1 |   2751.9 |   3885.4 |   9496.7 |
| Q02     | exasol     |     72.8 |      5 |       233.6 |     236.9 |     34.5 |    195.5 |    284.7 |
| Q02     | starrocks  |    715.9 |      5 |      1118.2 |    1120.1 |    108.1 |    973.8 |   1238.5 |
| Q02     | trino      |   5435.2 |      5 |     17713.4 |   20932.8 |   6515.9 |  14532   |  30666.2 |
| Q03     | clickhouse |   4964.5 |      5 |     11134.7 |   12968   |   6839.3 |   4655.4 |  22617.3 |
| Q03     | duckdb     |   1395.3 |      5 |      4848.6 |    5808.9 |   3086.1 |   3388.9 |  11078.5 |
| Q03     | exasol     |    567.3 |      5 |       569   |    1240.5 |    924.8 |    564   |   2339.6 |
| Q03     | starrocks  |   1560.3 |      5 |      1344.9 |    2044.1 |   1751.7 |    650.3 |   4747.3 |
| Q03     | trino      |  12170.2 |      5 |     45654.8 |   45054.8 |  14299.8 |  24441.8 |  61550.4 |
| Q04     | clickhouse |   5970.4 |      5 |     15489.8 |   16063.8 |   4247.1 |   9772.5 |  20015.5 |
| Q04     | duckdb     |   1329.9 |      5 |      7743.6 |    7653   |   1618.8 |   5595.8 |   9751.2 |
| Q04     | exasol     |    110.1 |      5 |       502.9 |     494.3 |    270.1 |    209.8 |    772.6 |
| Q04     | starrocks  |   1631.1 |      5 |      4215.6 |    3706.7 |   1213.8 |   1612.9 |   4692.2 |
| Q04     | trino      |  11468.7 |      5 |     34075.5 |   35573.8 |   5793.9 |  28106.6 |  43869.8 |
| Q05     | clickhouse |   4609.1 |      5 |     20645.6 |   20761.5 |   2193.9 |  18087.7 |  23484.9 |
| Q05     | duckdb     |   1431.8 |      5 |      5303.5 |    5570.2 |   1245.1 |   4620.3 |   7711.3 |
| Q05     | exasol     |    448.8 |      5 |      1897.4 |    1761.7 |    477.7 |    972.8 |   2180.4 |
| Q05     | starrocks  |   3133.1 |      5 |      8213.3 |    7942.3 |   1302.7 |   6314.1 |   9755.3 |
| Q05     | trino      |  12559.1 |      5 |     42052.8 |   43273.4 |   6907.9 |  36316.4 |  53755.4 |
| Q06     | clickhouse |    276.9 |      5 |      3416.3 |    2704.9 |   1196.1 |    665.5 |   3436.1 |
| Q06     | duckdb     |    409.9 |      5 |      3303.4 |    3288   |    552.3 |   2626.7 |   3990.3 |
| Q06     | exasol     |     71.2 |      5 |       153.1 |     284.6 |    258.2 |     72.3 |    633.6 |
| Q06     | starrocks  |    181.5 |      5 |       285.1 |     346.6 |    201.9 |    196.7 |    691.3 |
| Q06     | trino      |   5312.8 |      5 |     19397.8 |   21392.5 |   7828.2 |  14441.9 |  33998.3 |
| Q07     | clickhouse |  11788.3 |      5 |     37600.1 |   34064.2 |  11375.2 |  14254   |  42723.2 |
| Q07     | duckdb     |   1277.6 |      5 |      4811   |    5727.9 |   4681.6 |   1280   |  13680.6 |
| Q07     | exasol     |    553.9 |      5 |      2442.4 |    2193.7 |   1170.2 |    542.7 |   3558.4 |
| Q07     | starrocks  |   1509.2 |      5 |      3613.7 |    2968.4 |   1278.1 |    993   |   3933   |
| Q07     | trino      |  11261.4 |      5 |     41763   |   48164   |  12320.7 |  35861.7 |  63798.3 |
| Q08     | clickhouse |   5273.2 |      5 |     24695.6 |   25549.8 |   3476.2 |  22005.2 |  31275.3 |
| Q08     | duckdb     |   1358.9 |      5 |      7861.2 |    7243.2 |   3202.5 |   4082   |  11952.8 |
| Q08     | exasol     |    153.1 |      5 |       650.6 |     580.1 |    141.5 |    356   |    685   |
| Q08     | starrocks  |   2959   |      5 |      6539.6 |    6460.6 |    991.8 |   4891.6 |   7528.8 |
| Q08     | trino      |  11078.7 |      5 |     39238.7 |   35799.2 |  15644.4 |  10506.2 |  53524.8 |
| Q09     | clickhouse |   3158.1 |      5 |     15483.1 |   16587.1 |   3715.1 |  13078.8 |  20865.8 |
| Q09     | duckdb     |   4245.4 |      5 |     10130.9 |   10713.7 |   2787.5 |   7928.2 |  14835.4 |
| Q09     | exasol     |   1175.3 |      5 |      4803.7 |    4616.8 |   1232.1 |   3187.4 |   6272.2 |
| Q09     | starrocks  |   6451.3 |      5 |     10780.3 |   10641   |   1195.3 |   9024.4 |  12241.8 |
| Q09     | trino      |  27609.7 |      5 |     65009.3 |   71693.9 |  14160.8 |  60477.1 |  94242.5 |
| Q10     | clickhouse |   7800.8 |      5 |     30229.6 |   30715   |   1956.2 |  28415.2 |  33721.3 |
| Q10     | duckdb     |   2163   |      5 |      5763.3 |    7275.1 |   4081.8 |   3001.8 |  13671   |
| Q10     | exasol     |    646.2 |      5 |      2301.7 |    2229.2 |    658.7 |   1321.9 |   3146.2 |
| Q10     | starrocks  |   2511.2 |      5 |      4443.4 |    4242.3 |    324.5 |   3753.1 |   4487.4 |
| Q10     | trino      |  12274.4 |      5 |     50430.2 |   49951.6 |  15351   |  32067.2 |  73710.9 |
| Q11     | clickhouse |    978.7 |      5 |      6404.2 |    6693.5 |   2970.5 |   4030.3 |  11206.7 |
| Q11     | duckdb     |    209.1 |      5 |      3580.4 |    4443.6 |   2033.8 |   2284.7 |   7037.1 |
| Q11     | exasol     |    119.6 |      5 |       431.6 |     421.2 |    136.3 |    230.4 |    548.9 |
| Q11     | starrocks  |    384.7 |      5 |       767.7 |     786.1 |     36.4 |    765   |    850.4 |
| Q11     | trino      |   2427.2 |      5 |      8913.8 |    7567.1 |   2865.8 |   4056.7 |  10411.4 |
| Q12     | clickhouse |   2879   |      5 |      5606.7 |    6886.6 |   3316.1 |   4065.8 |  12254.1 |
| Q12     | duckdb     |   1528.5 |      5 |      8571.6 |    9470.5 |   2246.2 |   7679.7 |  13335.4 |
| Q12     | exasol     |    146.7 |      5 |       519.5 |     539.7 |    261.8 |    303.2 |    941.8 |
| Q12     | starrocks  |    850.5 |      5 |      1412.1 |    1539.2 |    337.5 |   1314.5 |   2137   |
| Q12     | trino      |   5501.7 |      5 |     40073.2 |   39541.3 |  10392.8 |  28999.4 |  50189.6 |
| Q13     | clickhouse |   3574.4 |      5 |     11515.5 |   11834.1 |   3520.8 |   6369.2 |  15254.7 |
| Q13     | duckdb     |   3623.5 |      5 |      7041.2 |    7305   |   2474   |   3608.6 |  10077.7 |
| Q13     | exasol     |   1428.4 |      5 |      5983.7 |    4863.7 |   2483.2 |   1466.6 |   7541.6 |
| Q13     | starrocks  |   2885.9 |      5 |      7093   |    7545   |   4018.3 |   2747.8 |  13872.4 |
| Q13     | trino      |  16351.8 |      5 |     43424.8 |   47847.4 |   9541.9 |  39156.1 |  62405.7 |
| Q14     | clickhouse |    312.7 |      5 |      3394.8 |    3352.3 |     96.5 |   3243.8 |   3465.6 |
| Q14     | duckdb     |   1043.2 |      5 |      4595   |    6260.4 |   4372.9 |   1022.5 |  11364.6 |
| Q14     | exasol     |    137.8 |      5 |       686.8 |     743.7 |    171.8 |    620.6 |   1040.7 |
| Q14     | starrocks  |    248.3 |      5 |       522.5 |     612.7 |    205.1 |    422.3 |    946.7 |
| Q14     | trino      |   6984.1 |      5 |     26810.4 |   28861.8 |   9219.3 |  16682.8 |  41439.7 |
| Q15     | clickhouse |    265.8 |      5 |      2317.3 |    2107.2 |    776   |   1279.9 |   2882.8 |
| Q15     | duckdb     |    914   |      5 |      6623.3 |    6548   |   2098.9 |   3331.4 |   9091   |
| Q15     | exasol     |    281.7 |      5 |      1217.6 |    1153.3 |    218.8 |    793.7 |   1359.2 |
| Q15     | starrocks  |    244.8 |      5 |       555.2 |     546.8 |     83.6 |    409   |    633.6 |
| Q15     | trino      |  12817   |      5 |     36020.4 |   33617.3 |  10809.9 |  18650.4 |  44333   |
| Q16     | clickhouse |    979.8 |      5 |      5099.9 |    4761.1 |   1293.5 |   2929.4 |   5923.5 |
| Q16     | duckdb     |    666   |      5 |      4425.3 |    4821   |   1766   |   2459.1 |   7088.5 |
| Q16     | exasol     |    554.9 |      5 |      1862.6 |    2182.1 |   1029   |   1339.2 |   3971.2 |
| Q16     | starrocks  |    681.9 |      5 |      1397.1 |    1399.4 |     60.6 |   1319.4 |   1490.2 |
| Q16     | trino      |   4145.2 |      5 |      9175.8 |    9887.6 |   2991.6 |   6400.4 |  13342.4 |
| Q17     | clickhouse |   1653.5 |      5 |     10172.1 |   10002.6 |    842.2 |   8920.2 |  10935.7 |
| Q17     | duckdb     |   1625   |      5 |      6747.6 |    7168.5 |   2404.1 |   4079.4 |  10440.7 |
| Q17     | exasol     |     25.1 |      5 |        99.3 |     120   |     52.7 |     60   |    195.3 |
| Q17     | starrocks  |   1068.4 |      5 |      1993.4 |    1981.7 |    555.9 |   1401.4 |   2869.4 |
| Q17     | trino      |  36026.2 |      5 |    160610   |  161132   |  79491.2 |  34813.4 | 247302   |
| Q18     | clickhouse |   5911.2 |      5 |     22278.6 |   24368.5 |   5092.1 |  20835   |  33314.9 |
| Q18     | duckdb     |   2770.3 |      5 |      7014.6 |    7226.1 |   3362.2 |   2729.7 |  12197.2 |
| Q18     | exasol     |    931.8 |      5 |      2483.3 |    2731.8 |   1058.9 |   1528.5 |   3987.9 |
| Q18     | starrocks  |   5468.3 |      5 |     28526.9 |   30285.1 |   8034.9 |  20540.3 |  42312.6 |
| Q18     | trino      |  14371.7 |      5 |     51350.5 |   52962.8 |  16129.6 |  32906.6 |  77073.6 |
| Q19     | clickhouse |   9589.5 |      5 |     30760.4 |   28613.5 |   5633.4 |  18664.9 |  32158.8 |
| Q19     | duckdb     |   1492.5 |      5 |      6897.6 |    7106   |   2390.2 |   4378.6 |  10955.1 |
| Q19     | exasol     |     55.1 |      5 |       153.1 |     158.3 |     80.7 |     83.9 |    278.1 |
| Q19     | starrocks  |   1409.4 |      5 |      2084.2 |    2194.7 |    307.7 |   1879.3 |   2531.1 |
| Q19     | trino      |   7884.3 |      5 |     29244   |   29534.7 |   3744.5 |  24914.7 |  34550.2 |
| Q20     | clickhouse |   2319.7 |      5 |      9279.2 |    9159.1 |   1239.7 |   7646.1 |  10817.3 |
| Q20     | duckdb     |   1389.2 |      5 |      3980.2 |    5854.5 |   4139.2 |   3366.7 |  13128.8 |
| Q20     | exasol     |    294.8 |      5 |       578   |     819.4 |    356.5 |    537.7 |   1294   |
| Q20     | starrocks  |    475.9 |      5 |      1397.8 |    1370.8 |    621.9 |    738.1 |   2213.5 |
| Q20     | trino      |   7632.6 |      5 |     25691.5 |   27270.8 |   9409.6 |  15007.7 |  37875.6 |
| Q21     | clickhouse |   3874   |      5 |     13729.3 |   14520.4 |   5728.4 |   7429.5 |  23435.9 |
| Q21     | duckdb     |   6462   |      5 |     10125.7 |   10916.9 |   2002.3 |   8945.5 |  13128.1 |
| Q21     | exasol     |    818.5 |      5 |      1781.9 |    2121.6 |   1129.5 |    843.9 |   3655.1 |
| Q21     | starrocks  |   6377.6 |      5 |     17509.8 |   21385.6 |  10933.6 |  11532.3 |  39871.5 |
| Q21     | trino      |  30235.6 |      5 |     74662.4 |   81612.5 |  15102.9 |  68083   | 102136   |
| Q22     | clickhouse |    776.5 |      5 |      5242.2 |    4744.4 |   2156.8 |   1651.5 |   7230   |
| Q22     | duckdb     |    713.6 |      5 |      6285   |    5970.3 |   3854.1 |    712   |   9925.1 |
| Q22     | exasol     |    178.7 |      5 |       676.3 |     606.4 |    254.8 |    180.3 |    842.5 |
| Q22     | starrocks  |    567.5 |      5 |      1111.5 |    1146.3 |    486.6 |    538.4 |   1896.5 |
| Q22     | trino      |   4466.5 |      5 |     18103.1 |   19432.6 |   7153   |  11713.9 |  29988.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        3548.2 |          5391.5 |    1.52 |      0.66 | False    |
| Q02     | exasol            | duckdb              |         233.6 |          4135.9 |   17.71 |      0.06 | False    |
| Q03     | exasol            | duckdb              |         569   |          4848.6 |    8.52 |      0.12 | False    |
| Q04     | exasol            | duckdb              |         502.9 |          7743.6 |   15.4  |      0.06 | False    |
| Q05     | exasol            | duckdb              |        1897.4 |          5303.5 |    2.8  |      0.36 | False    |
| Q06     | exasol            | duckdb              |         153.1 |          3303.4 |   21.58 |      0.05 | False    |
| Q07     | exasol            | duckdb              |        2442.4 |          4811   |    1.97 |      0.51 | False    |
| Q08     | exasol            | duckdb              |         650.6 |          7861.2 |   12.08 |      0.08 | False    |
| Q09     | exasol            | duckdb              |        4803.7 |         10130.9 |    2.11 |      0.47 | False    |
| Q10     | exasol            | duckdb              |        2301.7 |          5763.3 |    2.5  |      0.4  | False    |
| Q11     | exasol            | duckdb              |         431.6 |          3580.4 |    8.3  |      0.12 | False    |
| Q12     | exasol            | duckdb              |         519.5 |          8571.6 |   16.5  |      0.06 | False    |
| Q13     | exasol            | duckdb              |        5983.7 |          7041.2 |    1.18 |      0.85 | False    |
| Q14     | exasol            | duckdb              |         686.8 |          4595   |    6.69 |      0.15 | False    |
| Q15     | exasol            | duckdb              |        1217.6 |          6623.3 |    5.44 |      0.18 | False    |
| Q16     | exasol            | duckdb              |        1862.6 |          4425.3 |    2.38 |      0.42 | False    |
| Q17     | exasol            | duckdb              |          99.3 |          6747.6 |   67.95 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        2483.3 |          7014.6 |    2.82 |      0.35 | False    |
| Q19     | exasol            | duckdb              |         153.1 |          6897.6 |   45.05 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         578   |          3980.2 |    6.89 |      0.15 | False    |
| Q21     | exasol            | duckdb              |        1781.9 |         10125.7 |    5.68 |      0.18 | False    |
| Q22     | exasol            | duckdb              |         676.3 |          6285   |    9.29 |      0.11 | False    |
| Q01     | exasol            | starrocks           |        3548.2 |         21476.9 |    6.05 |      0.17 | False    |
| Q02     | exasol            | starrocks           |         233.6 |          1118.2 |    4.79 |      0.21 | False    |
| Q03     | exasol            | starrocks           |         569   |          1344.9 |    2.36 |      0.42 | False    |
| Q04     | exasol            | starrocks           |         502.9 |          4215.6 |    8.38 |      0.12 | False    |
| Q05     | exasol            | starrocks           |        1897.4 |          8213.3 |    4.33 |      0.23 | False    |
| Q06     | exasol            | starrocks           |         153.1 |           285.1 |    1.86 |      0.54 | False    |
| Q07     | exasol            | starrocks           |        2442.4 |          3613.7 |    1.48 |      0.68 | False    |
| Q08     | exasol            | starrocks           |         650.6 |          6539.6 |   10.05 |      0.1  | False    |
| Q09     | exasol            | starrocks           |        4803.7 |         10780.3 |    2.24 |      0.45 | False    |
| Q10     | exasol            | starrocks           |        2301.7 |          4443.4 |    1.93 |      0.52 | False    |
| Q11     | exasol            | starrocks           |         431.6 |           767.7 |    1.78 |      0.56 | False    |
| Q12     | exasol            | starrocks           |         519.5 |          1412.1 |    2.72 |      0.37 | False    |
| Q13     | exasol            | starrocks           |        5983.7 |          7093   |    1.19 |      0.84 | False    |
| Q14     | exasol            | starrocks           |         686.8 |           522.5 |    0.76 |      1.31 | True     |
| Q15     | exasol            | starrocks           |        1217.6 |           555.2 |    0.46 |      2.19 | True     |
| Q16     | exasol            | starrocks           |        1862.6 |          1397.1 |    0.75 |      1.33 | True     |
| Q17     | exasol            | starrocks           |          99.3 |          1993.4 |   20.07 |      0.05 | False    |
| Q18     | exasol            | starrocks           |        2483.3 |         28526.9 |   11.49 |      0.09 | False    |
| Q19     | exasol            | starrocks           |         153.1 |          2084.2 |   13.61 |      0.07 | False    |
| Q20     | exasol            | starrocks           |         578   |          1397.8 |    2.42 |      0.41 | False    |
| Q21     | exasol            | starrocks           |        1781.9 |         17509.8 |    9.83 |      0.1  | False    |
| Q22     | exasol            | starrocks           |         676.3 |          1111.5 |    1.64 |      0.61 | False    |
| Q01     | exasol            | clickhouse          |        3548.2 |         18682.6 |    5.27 |      0.19 | False    |
| Q02     | exasol            | clickhouse          |         233.6 |          9376.8 |   40.14 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         569   |         11134.7 |   19.57 |      0.05 | False    |
| Q04     | exasol            | clickhouse          |         502.9 |         15489.8 |   30.8  |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        1897.4 |         20645.6 |   10.88 |      0.09 | False    |
| Q06     | exasol            | clickhouse          |         153.1 |          3416.3 |   22.31 |      0.04 | False    |
| Q07     | exasol            | clickhouse          |        2442.4 |         37600.1 |   15.39 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         650.6 |         24695.6 |   37.96 |      0.03 | False    |
| Q09     | exasol            | clickhouse          |        4803.7 |         15483.1 |    3.22 |      0.31 | False    |
| Q10     | exasol            | clickhouse          |        2301.7 |         30229.6 |   13.13 |      0.08 | False    |
| Q11     | exasol            | clickhouse          |         431.6 |          6404.2 |   14.84 |      0.07 | False    |
| Q12     | exasol            | clickhouse          |         519.5 |          5606.7 |   10.79 |      0.09 | False    |
| Q13     | exasol            | clickhouse          |        5983.7 |         11515.5 |    1.92 |      0.52 | False    |
| Q14     | exasol            | clickhouse          |         686.8 |          3394.8 |    4.94 |      0.2  | False    |
| Q15     | exasol            | clickhouse          |        1217.6 |          2317.3 |    1.9  |      0.53 | False    |
| Q16     | exasol            | clickhouse          |        1862.6 |          5099.9 |    2.74 |      0.37 | False    |
| Q17     | exasol            | clickhouse          |          99.3 |         10172.1 |  102.44 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2483.3 |         22278.6 |    8.97 |      0.11 | False    |
| Q19     | exasol            | clickhouse          |         153.1 |         30760.4 |  200.92 |      0    | False    |
| Q20     | exasol            | clickhouse          |         578   |          9279.2 |   16.05 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |        1781.9 |         13729.3 |    7.7  |      0.13 | False    |
| Q22     | exasol            | clickhouse          |         676.3 |          5242.2 |    7.75 |      0.13 | False    |
| Q01     | exasol            | trino               |        3548.2 |         31125   |    8.77 |      0.11 | False    |
| Q02     | exasol            | trino               |         233.6 |         17713.4 |   75.83 |      0.01 | False    |
| Q03     | exasol            | trino               |         569   |         45654.8 |   80.24 |      0.01 | False    |
| Q04     | exasol            | trino               |         502.9 |         34075.5 |   67.76 |      0.01 | False    |
| Q05     | exasol            | trino               |        1897.4 |         42052.8 |   22.16 |      0.05 | False    |
| Q06     | exasol            | trino               |         153.1 |         19397.8 |  126.7  |      0.01 | False    |
| Q07     | exasol            | trino               |        2442.4 |         41763   |   17.1  |      0.06 | False    |
| Q08     | exasol            | trino               |         650.6 |         39238.7 |   60.31 |      0.02 | False    |
| Q09     | exasol            | trino               |        4803.7 |         65009.3 |   13.53 |      0.07 | False    |
| Q10     | exasol            | trino               |        2301.7 |         50430.2 |   21.91 |      0.05 | False    |
| Q11     | exasol            | trino               |         431.6 |          8913.8 |   20.65 |      0.05 | False    |
| Q12     | exasol            | trino               |         519.5 |         40073.2 |   77.14 |      0.01 | False    |
| Q13     | exasol            | trino               |        5983.7 |         43424.8 |    7.26 |      0.14 | False    |
| Q14     | exasol            | trino               |         686.8 |         26810.4 |   39.04 |      0.03 | False    |
| Q15     | exasol            | trino               |        1217.6 |         36020.4 |   29.58 |      0.03 | False    |
| Q16     | exasol            | trino               |        1862.6 |          9175.8 |    4.93 |      0.2  | False    |
| Q17     | exasol            | trino               |          99.3 |        160610   | 1617.42 |      0    | False    |
| Q18     | exasol            | trino               |        2483.3 |         51350.5 |   20.68 |      0.05 | False    |
| Q19     | exasol            | trino               |         153.1 |         29244   |  191.01 |      0.01 | False    |
| Q20     | exasol            | trino               |         578   |         25691.5 |   44.45 |      0.02 | False    |
| Q21     | exasol            | trino               |        1781.9 |         74662.4 |   41.9  |      0.02 | False    |
| Q22     | exasol            | trino               |         676.3 |         18103.1 |   26.77 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 15055.6 | 13991.6 | 665.5 | 39952.8 |
| 1 | 28 | 13240.4 | 10254.0 | 1297.8 | 35790.8 |
| 2 | 27 | 15094.5 | 11515.5 | 3243.8 | 33721.3 |
| 3 | 27 | 13669.9 | 10172.1 | 2758.0 | 42723.2 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 10172.1ms
- Slowest stream median: 13991.6ms
- Stream performance variation: 37.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6608.0 | 6095.6 | 1280.0 | 13680.6 |
| 1 | 28 | 6665.2 | 6456.1 | 712.0 | 11952.8 |
| 2 | 27 | 6738.2 | 5893.1 | 1022.5 | 14835.4 |
| 3 | 27 | 6808.0 | 6285.0 | 2459.1 | 13335.4 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 5893.1ms
- Slowest stream median: 6456.1ms
- Stream performance variation: 9.6% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1839.5 | 1497.5 | 72.3 | 7541.6 |
| 1 | 28 | 1283.0 | 663.5 | 96.1 | 5875.3 |
| 2 | 27 | 1704.1 | 941.8 | 78.9 | 6272.2 |
| 3 | 27 | 1461.7 | 738.1 | 60.0 | 6859.9 |

**Performance Analysis for Exasol:**
- Fastest stream median: 663.5ms
- Slowest stream median: 1497.5ms
- Stream performance variation: 125.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6369.8 | 3287.9 | 196.7 | 39871.5 |
| 1 | 28 | 5852.1 | 1946.1 | 212.7 | 42312.6 |
| 2 | 27 | 6211.2 | 2213.5 | 347.2 | 32422.6 |
| 3 | 27 | 5800.1 | 1441.1 | 582.8 | 32796.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1441.1ms
- Slowest stream median: 3287.9ms
- Stream performance variation: 128.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 42137.5 | 41179.2 | 9175.8 | 92987.8 |
| 1 | 28 | 44289.7 | 33709.8 | 4056.7 | 247302.2 |
| 2 | 27 | 40213.6 | 37809.5 | 4947.1 | 94242.5 |
| 3 | 27 | 44370.8 | 32906.6 | 6400.4 | 204558.1 |

**Performance Analysis for Trino:**
- Fastest stream median: 32906.6ms
- Slowest stream median: 41179.2ms
- Stream performance variation: 25.1% difference between fastest and slowest streams
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
- Median runtime: 818.1ms
- Average runtime: 1571.9ms
- Fastest query: 60.0ms
- Slowest query: 7541.6ms

**duckdb:**
- Median runtime: 6286.9ms
- Average runtime: 6703.6ms
- Fastest query: 712.0ms
- Slowest query: 14835.4ms

**starrocks:**
- Median runtime: 2110.6ms
- Average runtime: 6059.3ms
- Fastest query: 196.7ms
- Slowest query: 42312.6ms

**clickhouse:**
- Median runtime: 11465.0ms
- Average runtime: 14263.0ms
- Fastest query: 665.5ms
- Slowest query: 42723.2ms

**trino:**
- Median runtime: 35941.1ms
- Average runtime: 42761.3ms
- Fastest query: 4056.7ms
- Slowest query: 247302.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_sf_25-benchmark.zip`](extscal_sf_25-benchmark.zip)

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
  - max_memory_usage: 7000000000
  - max_bytes_before_external_group_by: 2500000000
  - max_bytes_before_external_sort: 2500000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 5000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 24GB
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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts