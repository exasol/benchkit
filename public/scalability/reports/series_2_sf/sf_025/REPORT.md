# Streamlined Scalability - Scale Factor 25 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.xlarge
**Date:** 2026-02-19 19:40:20

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
- exasol was the fastest overall with 818.1ms median runtime
- trino was 43.9x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 4 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


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
- **Hostname:** ip-10-0-1-102

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


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
- **Hostname:** ip-10-0-1-95

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



#### Starrocks 4.0.6 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45151CBF2542614D6 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45151CBF2542614D6

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45151CBF2542614D6 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45151CBF2542614D6 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45FCC058CA4532B87 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45FCC058CA4532B87

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45FCC058CA4532B87 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS45FCC058CA4532B87 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

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
| Clickhouse | 418.82s | 0.15s | 206.33s | 706.40s | 28.6 GB | 11.0 GB | 2.6x |
| Starrocks | 416.16s | 0.17s | 210.08s | 712.98s | 2.7 GB | 2.7 GB | 1.0x |
| Trino | 114.26s | 0.51s | 0.00s | 182.95s | N/A | N/A | N/A |
| Duckdb | 415.64s | 0.04s | 200.83s | 642.75s | 206.5 MB | N/A | N/A |
| Exasol | 246.01s | 1.99s | 254.91s | 634.49s | 23.9 GB | 5.2 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 182.95s
- Starrocks took 712.98s (3.9x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4570.7 |      5 |     13990.5 |   14314.7 |   1944.6 |  12359   |  16974.5 |
| Q01     | duckdb     |   2311.1 |      5 |      5391.5 |    5109.8 |    873.7 |   3927.3 |   5893.1 |
| Q01     | exasol     |   1564.4 |      5 |      3548.2 |    4482.1 |   1783.1 |   2726.8 |   6859.9 |
| Q01     | starrocks  |   6708.4 |      5 |     22508.8 |   22306.7 |   4246.5 |  16145.7 |  28107.1 |
| Q01     | trino      |  11949.2 |      5 |     31125   |   29644   |   8505.6 |  15926.6 |  37856.8 |
| Q02     | clickhouse |   2465.4 |      5 |      5851.2 |    6064.7 |   1238.3 |   4644.2 |   7500.6 |
| Q02     | duckdb     |    474.1 |      5 |      4135.9 |    5999.1 |   2751.9 |   3885.4 |   9496.7 |
| Q02     | exasol     |     72.8 |      5 |       233.6 |     236.9 |     34.5 |    195.5 |    284.7 |
| Q02     | starrocks  |    552.3 |      5 |      1024.6 |    1086.3 |    179.9 |    873.9 |   1348   |
| Q02     | trino      |   5435.2 |      5 |     17713.4 |   20932.8 |   6515.9 |  14532   |  30666.2 |
| Q03     | clickhouse |   1891.1 |      5 |      6612.3 |    6664.8 |   1704   |   4285.4 |   9042   |
| Q03     | duckdb     |   1395.3 |      5 |      4848.6 |    5808.9 |   3086.1 |   3388.9 |  11078.5 |
| Q03     | exasol     |    567.3 |      5 |       569   |    1240.5 |    924.8 |    564   |   2339.6 |
| Q03     | starrocks  |   1140.5 |      5 |      1443   |    2097.8 |   1600.5 |    704.3 |   3901.4 |
| Q03     | trino      |  12170.2 |      5 |     45654.8 |   45054.8 |  14299.8 |  24441.8 |  61550.4 |
| Q04     | clickhouse |   5982.8 |      5 |     17002.3 |   15815.1 |   6688.6 |   4867.1 |  23209.4 |
| Q04     | duckdb     |   1329.9 |      5 |      7743.6 |    7653   |   1618.8 |   5595.8 |   9751.2 |
| Q04     | exasol     |    110.1 |      5 |       502.9 |     494.3 |    270.1 |    209.8 |    772.6 |
| Q04     | starrocks  |   1157.7 |      5 |      5402.8 |    4973.8 |   2364.5 |   1427.4 |   7676.8 |
| Q04     | trino      |  11468.7 |      5 |     34075.5 |   35573.8 |   5793.9 |  28106.6 |  43869.8 |
| Q05     | clickhouse |   3544.5 |      5 |     16506   |   18330.9 |   3860.4 |  15161.2 |  24806.2 |
| Q05     | duckdb     |   1431.8 |      5 |      5303.5 |    5570.2 |   1245.1 |   4620.3 |   7711.3 |
| Q05     | exasol     |    448.8 |      5 |      1897.4 |    1761.7 |    477.7 |    972.8 |   2180.4 |
| Q05     | starrocks  |   2193.8 |      5 |      7640.7 |    7869.4 |   1098   |   6746.3 |   9322.2 |
| Q05     | trino      |  12559.1 |      5 |     42052.8 |   43273.4 |   6907.9 |  36316.4 |  53755.4 |
| Q06     | clickhouse |    358.9 |      5 |      2733.3 |    2277.1 |   1222.9 |    646.3 |   3473.5 |
| Q06     | duckdb     |    409.9 |      5 |      3303.4 |    3288   |    552.3 |   2626.7 |   3990.3 |
| Q06     | exasol     |     71.2 |      5 |       153.1 |     284.6 |    258.2 |     72.3 |    633.6 |
| Q06     | starrocks  |    188.5 |      5 |       435.9 |     395.5 |    123.3 |    211.4 |    507   |
| Q06     | trino      |   5312.8 |      5 |     19397.8 |   21392.5 |   7828.2 |  14441.9 |  33998.3 |
| Q07     | clickhouse |   5427.8 |      5 |      7456.9 |    7828.2 |   3619.7 |   3488.9 |  13450.2 |
| Q07     | duckdb     |   1277.6 |      5 |      4811   |    5727.9 |   4681.6 |   1280   |  13680.6 |
| Q07     | exasol     |    553.9 |      5 |      2442.4 |    2193.7 |   1170.2 |    542.7 |   3558.4 |
| Q07     | starrocks  |   1087   |      5 |      3587.6 |    3095.2 |   1145.1 |   1202.2 |   4002.4 |
| Q07     | trino      |  11261.4 |      5 |     41763   |   48164   |  12320.7 |  35861.7 |  63798.3 |
| Q08     | clickhouse |   5367.2 |      5 |     24378.7 |   24225.9 |   1813.6 |  22100.2 |  26540.9 |
| Q08     | duckdb     |   1358.9 |      5 |      7861.2 |    7243.2 |   3202.5 |   4082   |  11952.8 |
| Q08     | exasol     |    153.1 |      5 |       650.6 |     580.1 |    141.5 |    356   |    685   |
| Q08     | starrocks  |   2197.5 |      5 |      6465.4 |    6797   |    630   |   6288.2 |   7826.3 |
| Q08     | trino      |  11078.7 |      5 |     39238.7 |   35799.2 |  15644.4 |  10506.2 |  53524.8 |
| Q09     | clickhouse |   3065   |      5 |     15711.2 |   15195.6 |   3134   |  11417.8 |  19347.2 |
| Q09     | duckdb     |   4245.4 |      5 |     10130.9 |   10713.7 |   2787.5 |   7928.2 |  14835.4 |
| Q09     | exasol     |   1175.3 |      5 |      4803.7 |    4616.8 |   1232.1 |   3187.4 |   6272.2 |
| Q09     | starrocks  |   5865.2 |      5 |     11425.7 |   12230.4 |   2186.6 |  10565.1 |  16043.5 |
| Q09     | trino      |  27609.7 |      5 |     65009.3 |   71693.9 |  14160.8 |  60477.1 |  94242.5 |
| Q10     | clickhouse |   5506.2 |      5 |     16679.8 |   16248.4 |   1729.8 |  14100.8 |  17864.8 |
| Q10     | duckdb     |   2163   |      5 |      5763.3 |    7275.1 |   4081.8 |   3001.8 |  13671   |
| Q10     | exasol     |    646.2 |      5 |      2301.7 |    2229.2 |    658.7 |   1321.9 |   3146.2 |
| Q10     | starrocks  |   2276.5 |      5 |      4734   |    5263.6 |   1254.3 |   4457   |   7472.1 |
| Q10     | trino      |  12274.4 |      5 |     50430.2 |   49951.6 |  15351   |  32067.2 |  73710.9 |
| Q11     | clickhouse |   1601.6 |      5 |      3965.7 |    3282.7 |   1881.7 |    682.2 |   5202.9 |
| Q11     | duckdb     |    209.1 |      5 |      3580.4 |    4443.6 |   2033.8 |   2284.7 |   7037.1 |
| Q11     | exasol     |    119.6 |      5 |       431.6 |     421.2 |    136.3 |    230.4 |    548.9 |
| Q11     | starrocks  |    339.8 |      5 |       762.5 |     941.6 |    480.5 |    634.8 |   1782.1 |
| Q11     | trino      |   2427.2 |      5 |      8913.8 |    7567.1 |   2865.8 |   4056.7 |  10411.4 |
| Q12     | clickhouse |   2735.7 |      5 |      6191.4 |    5986.3 |   1273.2 |   4394.5 |   7485.2 |
| Q12     | duckdb     |   1528.5 |      5 |      8571.6 |    9470.5 |   2246.2 |   7679.7 |  13335.4 |
| Q12     | exasol     |    146.7 |      5 |       519.5 |     539.7 |    261.8 |    303.2 |    941.8 |
| Q12     | starrocks  |    698.1 |      5 |      2116.9 |    2084.9 |    528.5 |   1589.5 |   2915.6 |
| Q12     | trino      |   5501.7 |      5 |     40073.2 |   39541.3 |  10392.8 |  28999.4 |  50189.6 |
| Q13     | clickhouse |   3056.4 |      5 |      9759.3 |    9987   |    519.8 |   9680   |  10909.3 |
| Q13     | duckdb     |   3623.5 |      5 |      7041.2 |    7305   |   2474   |   3608.6 |  10077.7 |
| Q13     | exasol     |   1428.4 |      5 |      5983.7 |    4863.7 |   2483.2 |   1466.6 |   7541.6 |
| Q13     | starrocks  |   2771   |      5 |      6507   |    7191.8 |   3491.2 |   2953.7 |  10936.2 |
| Q13     | trino      |  16351.8 |      5 |     43424.8 |   47847.4 |   9541.9 |  39156.1 |  62405.7 |
| Q14     | clickhouse |    259.5 |      5 |      1590.4 |    2202.9 |   1066   |   1162.9 |   3429.2 |
| Q14     | duckdb     |   1043.2 |      5 |      4595   |    6260.4 |   4372.9 |   1022.5 |  11364.6 |
| Q14     | exasol     |    137.8 |      5 |       686.8 |     743.7 |    171.8 |    620.6 |   1040.7 |
| Q14     | starrocks  |    185.2 |      5 |       613.4 |     617.8 |     48.9 |    567.5 |    697.8 |
| Q14     | trino      |   6984.1 |      5 |     26810.4 |   28861.8 |   9219.3 |  16682.8 |  41439.7 |
| Q15     | clickhouse |    244.2 |      5 |      2545.2 |    2273.4 |    624.8 |   1514.8 |   2850.7 |
| Q15     | duckdb     |    914   |      5 |      6623.3 |    6548   |   2098.9 |   3331.4 |   9091   |
| Q15     | exasol     |    281.7 |      5 |      1217.6 |    1153.3 |    218.8 |    793.7 |   1359.2 |
| Q15     | starrocks  |    316.4 |      5 |       763.8 |     705.8 |    257.5 |    403.7 |   1025.4 |
| Q15     | trino      |  12817   |      5 |     36020.4 |   33617.3 |  10809.9 |  18650.4 |  44333   |
| Q16     | clickhouse |    912.8 |      5 |      4775.5 |    6344.5 |   3401.9 |   4352.3 |  12390.8 |
| Q16     | duckdb     |    666   |      5 |      4425.3 |    4821   |   1766   |   2459.1 |   7088.5 |
| Q16     | exasol     |    554.9 |      5 |      1862.6 |    2182.1 |   1029   |   1339.2 |   3971.2 |
| Q16     | starrocks  |    768.6 |      5 |      1458.3 |    1411.3 |    207.9 |   1066.2 |   1617   |
| Q16     | trino      |   4145.2 |      5 |      9175.8 |    9887.6 |   2991.6 |   6400.4 |  13342.4 |
| Q17     | clickhouse |   1658.9 |      5 |      8546.5 |    8501.1 |   1541.5 |   6082   |   9992.2 |
| Q17     | duckdb     |   1625   |      5 |      6747.6 |    7168.5 |   2404.1 |   4079.4 |  10440.7 |
| Q17     | exasol     |     25.1 |      5 |        99.3 |     120   |     52.7 |     60   |    195.3 |
| Q17     | starrocks  |   1174.7 |      5 |      1632   |    2227.5 |   1268.1 |   1493.2 |   4467   |
| Q17     | trino      |  36026.2 |      5 |    160610   |  161132   |  79491.2 |  34813.4 | 247302   |
| Q18     | clickhouse |   5642.1 |      5 |     25925.3 |   24854.9 |   3049.9 |  19589   |  27426.1 |
| Q18     | duckdb     |   2770.3 |      5 |      7014.6 |    7226.1 |   3362.2 |   2729.7 |  12197.2 |
| Q18     | exasol     |    931.8 |      5 |      2483.3 |    2731.8 |   1058.9 |   1528.5 |   3987.9 |
| Q18     | starrocks  |   6012.4 |      5 |     27661   |   30643.5 |   6047.7 |  26532.3 |  41191.1 |
| Q18     | trino      |  14371.7 |      5 |     51350.5 |   52962.8 |  16129.6 |  32906.6 |  77073.6 |
| Q19     | clickhouse |   9133.5 |      5 |     33978.5 |   28901.4 |  11145.9 |   9058.5 |  35033.9 |
| Q19     | duckdb     |   1492.5 |      5 |      6897.6 |    7106   |   2390.2 |   4378.6 |  10955.1 |
| Q19     | exasol     |     55.1 |      5 |       153.1 |     158.3 |     80.7 |     83.9 |    278.1 |
| Q19     | starrocks  |   1393.9 |      5 |      2363.7 |    2324.4 |    474.6 |   1676.5 |   2996.6 |
| Q19     | trino      |   7884.3 |      5 |     29244   |   29534.7 |   3744.5 |  24914.7 |  34550.2 |
| Q20     | clickhouse |   2194.8 |      5 |      5482.1 |    6288.6 |   1654.6 |   4922.7 |   8838.5 |
| Q20     | duckdb     |   1389.2 |      5 |      3980.2 |    5854.5 |   4139.2 |   3366.7 |  13128.8 |
| Q20     | exasol     |    294.8 |      5 |       578   |     819.4 |    356.5 |    537.7 |   1294   |
| Q20     | starrocks  |    534.1 |      5 |      1027.8 |    1018.2 |    278.1 |    661.9 |   1423.9 |
| Q20     | trino      |   7632.6 |      5 |     25691.5 |   27270.8 |   9409.6 |  15007.7 |  37875.6 |
| Q21     | clickhouse |   3903.3 |      5 |     14076   |   12352.5 |   3714.3 |   5984.8 |  15016.7 |
| Q21     | duckdb     |   6462   |      5 |     10125.7 |   10916.9 |   2002.3 |   8945.5 |  13128.1 |
| Q21     | exasol     |    818.5 |      5 |      1781.9 |    2121.6 |   1129.5 |    843.9 |   3655.1 |
| Q21     | starrocks  |   6652.3 |      5 |     20267.4 |   20418.1 |   8554.1 |   9873.2 |  33360.6 |
| Q21     | trino      |  30235.6 |      5 |     74662.4 |   81612.5 |  15102.9 |  68083   | 102136   |
| Q22     | clickhouse |    960.8 |      5 |      6239.6 |    6076.5 |   1427   |   4437.5 |   7838.8 |
| Q22     | duckdb     |    713.6 |      5 |      6285   |    5970.3 |   3854.1 |    712   |   9925.1 |
| Q22     | exasol     |    178.7 |      5 |       676.3 |     606.4 |    254.8 |    180.3 |    842.5 |
| Q22     | starrocks  |    581.2 |      5 |      1820.3 |    1929   |   1305.2 |    520.9 |   3871   |
| Q22     | trino      |   4466.5 |      5 |     18103.1 |   19432.6 |   7153   |  11713.9 |  29988.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        3548.2 |         13990.5 |    3.94 |      0.25 | False    |
| Q02     | exasol            | clickhouse          |         233.6 |          5851.2 |   25.05 |      0.04 | False    |
| Q03     | exasol            | clickhouse          |         569   |          6612.3 |   11.62 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |         502.9 |         17002.3 |   33.81 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |        1897.4 |         16506   |    8.7  |      0.11 | False    |
| Q06     | exasol            | clickhouse          |         153.1 |          2733.3 |   17.85 |      0.06 | False    |
| Q07     | exasol            | clickhouse          |        2442.4 |          7456.9 |    3.05 |      0.33 | False    |
| Q08     | exasol            | clickhouse          |         650.6 |         24378.7 |   37.47 |      0.03 | False    |
| Q09     | exasol            | clickhouse          |        4803.7 |         15711.2 |    3.27 |      0.31 | False    |
| Q10     | exasol            | clickhouse          |        2301.7 |         16679.8 |    7.25 |      0.14 | False    |
| Q11     | exasol            | clickhouse          |         431.6 |          3965.7 |    9.19 |      0.11 | False    |
| Q12     | exasol            | clickhouse          |         519.5 |          6191.4 |   11.92 |      0.08 | False    |
| Q13     | exasol            | clickhouse          |        5983.7 |          9759.3 |    1.63 |      0.61 | False    |
| Q14     | exasol            | clickhouse          |         686.8 |          1590.4 |    2.32 |      0.43 | False    |
| Q15     | exasol            | clickhouse          |        1217.6 |          2545.2 |    2.09 |      0.48 | False    |
| Q16     | exasol            | clickhouse          |        1862.6 |          4775.5 |    2.56 |      0.39 | False    |
| Q17     | exasol            | clickhouse          |          99.3 |          8546.5 |   86.07 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        2483.3 |         25925.3 |   10.44 |      0.1  | False    |
| Q19     | exasol            | clickhouse          |         153.1 |         33978.5 |  221.94 |      0    | False    |
| Q20     | exasol            | clickhouse          |         578   |          5482.1 |    9.48 |      0.11 | False    |
| Q21     | exasol            | clickhouse          |        1781.9 |         14076   |    7.9  |      0.13 | False    |
| Q22     | exasol            | clickhouse          |         676.3 |          6239.6 |    9.23 |      0.11 | False    |
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
| Q01     | exasol            | starrocks           |        3548.2 |         22508.8 |    6.34 |      0.16 | False    |
| Q02     | exasol            | starrocks           |         233.6 |          1024.6 |    4.39 |      0.23 | False    |
| Q03     | exasol            | starrocks           |         569   |          1443   |    2.54 |      0.39 | False    |
| Q04     | exasol            | starrocks           |         502.9 |          5402.8 |   10.74 |      0.09 | False    |
| Q05     | exasol            | starrocks           |        1897.4 |          7640.7 |    4.03 |      0.25 | False    |
| Q06     | exasol            | starrocks           |         153.1 |           435.9 |    2.85 |      0.35 | False    |
| Q07     | exasol            | starrocks           |        2442.4 |          3587.6 |    1.47 |      0.68 | False    |
| Q08     | exasol            | starrocks           |         650.6 |          6465.4 |    9.94 |      0.1  | False    |
| Q09     | exasol            | starrocks           |        4803.7 |         11425.7 |    2.38 |      0.42 | False    |
| Q10     | exasol            | starrocks           |        2301.7 |          4734   |    2.06 |      0.49 | False    |
| Q11     | exasol            | starrocks           |         431.6 |           762.5 |    1.77 |      0.57 | False    |
| Q12     | exasol            | starrocks           |         519.5 |          2116.9 |    4.07 |      0.25 | False    |
| Q13     | exasol            | starrocks           |        5983.7 |          6507   |    1.09 |      0.92 | False    |
| Q14     | exasol            | starrocks           |         686.8 |           613.4 |    0.89 |      1.12 | True     |
| Q15     | exasol            | starrocks           |        1217.6 |           763.8 |    0.63 |      1.59 | True     |
| Q16     | exasol            | starrocks           |        1862.6 |          1458.3 |    0.78 |      1.28 | True     |
| Q17     | exasol            | starrocks           |          99.3 |          1632   |   16.44 |      0.06 | False    |
| Q18     | exasol            | starrocks           |        2483.3 |         27661   |   11.14 |      0.09 | False    |
| Q19     | exasol            | starrocks           |         153.1 |          2363.7 |   15.44 |      0.06 | False    |
| Q20     | exasol            | starrocks           |         578   |          1027.8 |    1.78 |      0.56 | False    |
| Q21     | exasol            | starrocks           |        1781.9 |         20267.4 |   11.37 |      0.09 | False    |
| Q22     | exasol            | starrocks           |         676.3 |          1820.3 |    2.69 |      0.37 | False    |
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
| 0 | 28 | 11010.8 | 9703.2 | 1514.8 | 33978.5 |
| 1 | 28 | 10263.3 | 7857.7 | 1162.9 | 25925.3 |
| 2 | 27 | 12020.3 | 9058.5 | 646.3 | 35033.9 |
| 3 | 27 | 11106.0 | 7838.8 | 1590.4 | 34343.9 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7838.8ms
- Slowest stream median: 9703.2ms
- Stream performance variation: 23.8% difference between fastest and slowest streams
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
| 0 | 28 | 6575.2 | 3782.3 | 211.4 | 33360.6 |
| 1 | 28 | 5947.1 | 2703.9 | 333.1 | 41191.1 |
| 2 | 27 | 6447.3 | 2179.1 | 507.0 | 28107.1 |
| 3 | 27 | 6053.6 | 2116.9 | 490.3 | 30198.2 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2116.9ms
- Slowest stream median: 3782.3ms
- Stream performance variation: 78.7% difference between fastest and slowest streams
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

**clickhouse:**
- Median runtime: 8384.2ms
- Average runtime: 11091.7ms
- Fastest query: 646.3ms
- Slowest query: 35033.9ms

**duckdb:**
- Median runtime: 6286.9ms
- Average runtime: 6703.6ms
- Fastest query: 712.0ms
- Slowest query: 14835.4ms

**exasol:**
- Median runtime: 818.1ms
- Average runtime: 1571.9ms
- Fastest query: 60.0ms
- Slowest query: 7541.6ms

**starrocks:**
- Median runtime: 2407.2ms
- Average runtime: 6255.9ms
- Fastest query: 211.4ms
- Slowest query: 41191.1ms

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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts