# Streamlined Scalability - Stream Scaling (16 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2026-02-09 15:13:37

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 5 database systems:
- **exasol**
- **starrocks**
- **duckdb**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 711.4ms median runtime
- trino was 43.8x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 16 concurrent streams (randomized distribution)

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
- **Exasol Instance:** r6id.8xlarge
- **Clickhouse Instance:** r6id.8xlarge
- **Trino Instance:** r6id.8xlarge
- **Starrocks Instance:** r6id.8xlarge
- **Duckdb Instance:** r6id.8xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (1699GB)
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22BA64D77A1767C7C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22BA64D77A1767C7C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22BA64D77A1767C7C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22BA64D77A1767C7C /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22FE6547727409E56 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22FE6547727409E56

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22FE6547727409E56 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22FE6547727409E56 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS643D12ED95BB86228 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS643D12ED95BB86228

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS643D12ED95BB86228 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS643D12ED95BB86228 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `192g`
- Max threads: `32`
- Max memory usage: `12.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6424666D239C31CEB with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6424666D239C31CEB

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6424666D239C31CEB to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6424666D239C31CEB /data

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
- Memory limit: `192GB`

**Data Directory:** `/data/duckdb`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 50
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 5
- **Execution mode:** Multiuser (16 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip extscal_streams_16-benchmark.zip
cd extscal_streams_16

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
| Clickhouse | 376.90s | 0.12s | 204.66s | 797.38s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 377.75s | 0.08s | 314.19s | 846.37s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 38.35s | 0.32s | 0.00s | 57.45s | N/A | N/A | N/A |
| Duckdb | 376.71s | 0.02s | 99.98s | 483.33s | 412.9 MB | N/A | N/A |
| Exasol | 131.08s | 1.94s | 239.84s | 423.67s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 57.45s
- Starrocks took 846.37s (14.7x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   1269.4 |      5 |     12660.9 |   12318.7 |   4181.1 |   6269.1 |  17672.5 |
| Q01     | duckdb     |    602.6 |      5 |      7508.7 |    6998   |   3319.3 |   1629.4 |  10780.2 |
| Q01     | exasol     |    410.3 |      5 |      3397.6 |    3483.3 |    793.1 |   2319.3 |   4298.5 |
| Q01     | starrocks  |   1968.1 |      5 |      6558.2 |    5892.9 |   1466.6 |   3516.4 |   7157.6 |
| Q01     | trino      |   3602.1 |      5 |     46795.2 |   39069.7 |  15203.7 |  12167.9 |  47398.8 |
| Q02     | clickhouse |    609.6 |      5 |     12180.2 |   10351.9 |   5346.7 |    927.4 |  14204   |
| Q02     | duckdb     |    178   |      5 |      7838.5 |    6872.6 |   3280.8 |   1179.8 |   9506.5 |
| Q02     | exasol     |     63   |      5 |       232.5 |     213.8 |     66.4 |     96.9 |    260.5 |
| Q02     | starrocks  |    274   |      5 |      1818.5 |    2633.9 |   2008.3 |   1203.6 |   6165.7 |
| Q02     | trino      |   3045.2 |      5 |      8983   |   10186.6 |   3479.7 |   7992.5 |  16360.2 |
| Q03     | clickhouse |   1313   |      5 |     14049.8 |   13920.8 |   7448.7 |   5544.3 |  21730.6 |
| Q03     | duckdb     |    371.3 |      5 |      7117   |    6766.1 |   1268.9 |   4771.4 |   8096.2 |
| Q03     | exasol     |    188.5 |      5 |      1384.5 |    1355.7 |    600.3 |    391.7 |   2023.4 |
| Q03     | starrocks  |    501.8 |      5 |      3810.5 |    3372.8 |   3009.8 |    339.6 |   7312.4 |
| Q03     | trino      |   7533.8 |      5 |     34046.9 |   40984.7 |  33358.8 |   6634.6 |  86592.6 |
| Q04     | clickhouse |   6638.1 |      5 |     27505.5 |   26005.4 |   6590.3 |  14593.5 |  30696.1 |
| Q04     | duckdb     |    368.2 |      5 |      7399.3 |    7504.4 |   2236.8 |   4160.9 |   9616.8 |
| Q04     | exasol     |     36.8 |      5 |       416.6 |     362.3 |    177.7 |    127.8 |    593.9 |
| Q04     | starrocks  |    404.9 |      5 |      8042.5 |    6142.4 |   3029.8 |   2382.9 |   8569   |
| Q04     | trino      |   3145.7 |      5 |     32342.2 |   34753.4 |  21958.2 |   5726.5 |  67397.3 |
| Q05     | clickhouse |   1061.5 |      5 |     19110.7 |   19738.9 |   1637.7 |  18569.1 |  22502.6 |
| Q05     | duckdb     |    393.4 |      5 |      8526.4 |    8949   |   1204.4 |   7842.3 |  10406.3 |
| Q05     | exasol     |    169.9 |      5 |      1273.3 |    1113.4 |    249.6 |    727.8 |   1296.6 |
| Q05     | starrocks  |    439.1 |      5 |      6517.2 |    8074.7 |   2438.5 |   6136   |  10946.7 |
| Q05     | trino      |   3611   |      5 |     53187.7 |   48677.1 |  16909.8 |  19027.6 |  59788.7 |
| Q06     | clickhouse |    102   |      5 |      2983.3 |    3220.9 |   1684.7 |   1341.7 |   5396.7 |
| Q06     | duckdb     |    103   |      5 |      7286.6 |    7212.9 |   1333.8 |   5137.3 |   8852.9 |
| Q06     | exasol     |     23.7 |      5 |       226.4 |     213.6 |     69   |    117.4 |    285.1 |
| Q06     | starrocks  |     53.6 |      5 |      1944.9 |    1726.2 |   1571.5 |     46   |   3935.9 |
| Q06     | trino      |   1777.7 |      5 |     13789.6 |   13289.2 |   9101   |   3400.4 |  22443.4 |
| Q07     | clickhouse |   4908.5 |      5 |     31511.1 |   30941.5 |  11797.9 |  11408.2 |  40904.2 |
| Q07     | duckdb     |    368.3 |      5 |      6627.9 |    6841.6 |    641.8 |   6140   |   7815.2 |
| Q07     | exasol     |    138.3 |      5 |      1593.5 |    1295.6 |    630.1 |    235.6 |   1779   |
| Q07     | starrocks  |    562   |      5 |      6444.9 |    7070   |   1945.6 |   4845.8 |   9132.1 |
| Q07     | trino      |   3864   |      5 |     41412.4 |   37194   |  11052.1 |  21271.8 |  48446   |
| Q08     | clickhouse |   1450.6 |      5 |     22386.9 |   22831.5 |   1664.9 |  21140.1 |  25501.7 |
| Q08     | duckdb     |    393   |      5 |      7848.3 |    8369.8 |   1608.8 |   6886.4 |  10151.2 |
| Q08     | exasol     |     45.8 |      5 |       461   |     444.1 |     93.9 |    284.4 |    518.1 |
| Q08     | starrocks  |    458.6 |      5 |      6571.3 |    6355.1 |   1611.7 |   3768.4 |   8222   |
| Q08     | trino      |   3402   |      5 |     51129.1 |   46205   |  20660   |  10193.7 |  60206.5 |
| Q09     | clickhouse |   1113   |      5 |     18168.9 |   18209.2 |    975.7 |  17275   |  19565.1 |
| Q09     | duckdb     |   1323.4 |      5 |      9210.6 |    9392.4 |   1573.3 |   7840.7 |  11298.7 |
| Q09     | exasol     |    478.6 |      5 |      5428.9 |    5429.3 |    612.5 |   4804.2 |   6375.6 |
| Q09     | starrocks  |   1546.2 |      5 |     12792.2 |   13201.4 |    871.7 |  12241.1 |  14282.7 |
| Q09     | trino      |  18545.8 |      5 |    122799   |  129315   |  20006.5 | 107591   | 159311   |
| Q10     | clickhouse |   2726.6 |      5 |     32884.8 |   31992.2 |   1714   |  29317   |  33383.3 |
| Q10     | duckdb     |    626.5 |      5 |      7313.4 |    7339.5 |    600.8 |   6647.4 |   8143.7 |
| Q10     | exasol     |    341.2 |      5 |      1887.1 |    1937.7 |   1005.4 |    785   |   3072.5 |
| Q10     | starrocks  |    661.6 |      5 |      6713.5 |    6270.6 |   1117.6 |   4903.5 |   7249.1 |
| Q10     | trino      |   3636.3 |      5 |     52824.2 |   43214   |  21965.8 |   9395.8 |  62052.8 |
| Q11     | clickhouse |    467.4 |      5 |      9748.5 |    9493.9 |   2331.9 |   5857.5 |  12102.3 |
| Q11     | duckdb     |     67.3 |      5 |      7421   |    7031   |   3402.1 |   1701   |  11073.7 |
| Q11     | exasol     |    126.3 |      5 |       483.9 |     469.8 |     70   |    361.2 |    553.8 |
| Q11     | starrocks  |    105.1 |      5 |       983.9 |    1590   |   1583.6 |    358   |   4328.5 |
| Q11     | trino      |    922.7 |      5 |      4737.5 |    6912.9 |   3845.8 |   3810.3 |  12508.9 |
| Q12     | clickhouse |   1351.5 |      5 |      8680.6 |    7609.6 |   2477.2 |   3920.7 |  10059   |
| Q12     | duckdb     |    401.1 |      5 |      8171   |    7968.2 |   2073.4 |   4538.3 |   9762.9 |
| Q12     | exasol     |     48.3 |      5 |       542.7 |     515.6 |    149.8 |    344.6 |    722.7 |
| Q12     | starrocks  |    181.8 |      5 |      3126.3 |    3642.9 |   2044   |   1639.4 |   7019.4 |
| Q12     | trino      |   1797.2 |      5 |     26437.8 |   27403.4 |   9592.2 |  12693.9 |  36791.5 |
| Q13     | clickhouse |   2108.9 |      5 |     16912.7 |   16193.9 |   7330.2 |   5303.9 |  23668.3 |
| Q13     | duckdb     |   1065.8 |      5 |      7962.4 |    6766.9 |   3249.5 |   1022   |   8868.5 |
| Q13     | exasol     |    344.3 |      5 |      4117.3 |    3470.6 |   1547.1 |    722.7 |   4426.1 |
| Q13     | starrocks  |   1030.2 |      5 |     12051.8 |   10767.1 |   2732.8 |   6115.9 |  12938.9 |
| Q13     | trino      |   4946.6 |      5 |    106463   |   92060.9 |  45762.7 |  12303.7 | 127403   |
| Q14     | clickhouse |    114.4 |      5 |      4588.1 |    4604.9 |   1932.2 |   2030   |   6924.7 |
| Q14     | duckdb     |    290.4 |      5 |      6277.3 |    6646.2 |   2090   |   4831.6 |   9987   |
| Q14     | exasol     |     43.4 |      5 |       581.5 |     555.7 |    140   |    329.1 |    700   |
| Q14     | starrocks  |    105.3 |      5 |      5513.3 |    6079   |   2479.2 |   3336   |   9079.4 |
| Q14     | trino      |   2207.7 |      5 |     31376   |   27527.4 |  11275.2 |   7559.1 |  34979.3 |
| Q15     | clickhouse |    201.7 |      5 |      4011   |    4345.9 |   1859.9 |   2373.8 |   7186.4 |
| Q15     | duckdb     |    247.2 |      5 |      8846.5 |    8266.9 |   1547.8 |   5768.9 |   9491.8 |
| Q15     | exasol     |    216   |      5 |      1460.6 |    1474.8 |    190.7 |   1276.2 |   1768.6 |
| Q15     | starrocks  |    100.9 |      5 |      6590.1 |    7165.6 |   2917.3 |   4288.9 |  10833.8 |
| Q15     | trino      |   3598   |      5 |     30169.1 |   30518.7 |   2281.8 |  28070   |  33764   |
| Q16     | clickhouse |    349.1 |      5 |      8345.2 |    8149.3 |   2740.9 |   5374.3 |  12092.9 |
| Q16     | duckdb     |    246.8 |      5 |      6625   |    6811.5 |   1408.4 |   5033.1 |   8722.5 |
| Q16     | exasol     |    348.4 |      5 |      2156.1 |    2084.1 |    250.8 |   1661.9 |   2327.4 |
| Q16     | starrocks  |    395.4 |      5 |      1981.7 |    3128.1 |   2874.8 |   1358.4 |   8164.7 |
| Q16     | trino      |   1995.8 |      5 |      9349.2 |    8842.4 |   3333.6 |   5553.8 |  13794.3 |
| Q17     | clickhouse |    542.6 |      5 |     10937.8 |    8487.1 |   3984.9 |   3098.6 |  11817.2 |
| Q17     | duckdb     |    444.4 |      5 |      7914.7 |    7010.5 |   3905.9 |    436   |  10906.4 |
| Q17     | exasol     |     21.4 |      5 |        95.8 |      92.4 |     33.2 |     39.7 |    131.4 |
| Q17     | starrocks  |    184.4 |      5 |      5807.4 |    5097.6 |   2465.5 |   2443.2 |   7441.4 |
| Q17     | trino      |   4333.7 |      5 |     65983.7 |   56595.2 |  16665.3 |  32908.4 |  69611.5 |
| Q18     | clickhouse |   1140.7 |      5 |     18043.9 |   16686.1 |   3794.6 |  10756.8 |  20647.2 |
| Q18     | duckdb     |    880.9 |      5 |      8456   |    8638.5 |   1379   |   7214   |  10127.4 |
| Q18     | exasol     |    324   |      5 |      3155.7 |    3031.6 |   1009.8 |   1334.5 |   3949.2 |
| Q18     | starrocks  |   2659.5 |      5 |      9655.1 |   10901.1 |   4109.2 |   7566.2 |  17995.6 |
| Q18     | trino      |   6785.3 |      5 |     49329.7 |   43138.9 |  17733.2 |  20392.4 |  63293.1 |
| Q19     | clickhouse |   2577.1 |      5 |     26628.9 |   24225.7 |   6533.2 |  15074.9 |  30081.5 |
| Q19     | duckdb     |    429.6 |      5 |      8850.5 |    8484   |   1096.8 |   7238.2 |   9487.3 |
| Q19     | exasol     |     18.3 |      5 |        79.7 |     122.6 |     93.5 |     54.5 |    275.6 |
| Q19     | starrocks  |    259.5 |      5 |      2485.4 |    2542.5 |   1256.1 |    686.5 |   4105.7 |
| Q19     | trino      |   2475.7 |      5 |      7355.9 |   14680.1 |  12138.4 |   3923   |  28508.9 |
| Q20     | clickhouse |    995.6 |      5 |     14619.8 |   14356.3 |   2417.5 |  10873.2 |  17239.4 |
| Q20     | duckdb     |    400.6 |      5 |     10480.8 |    8975.9 |   2451   |   5522.2 |  10889.2 |
| Q20     | exasol     |    158.5 |      5 |       798.6 |     847.6 |    371.1 |    359.1 |   1344   |
| Q20     | starrocks  |    170.3 |      5 |      4586.7 |    5358.9 |   2080.5 |   3737.2 |   8669.6 |
| Q20     | trino      |   2731.2 |      5 |     26787.3 |   22980.6 |  10920   |   4761.9 |  33451.9 |
| Q21     | clickhouse |   1608.7 |      5 |     17448.4 |   17275.3 |   4388.4 |  12561   |  22107   |
| Q21     | duckdb     |   2119.1 |      5 |      8159.6 |    7887.4 |   2822.7 |   3829.5 |  11360.1 |
| Q21     | exasol     |    207.4 |      5 |       834.2 |    1299.9 |    993.2 |    451.2 |   2435.4 |
| Q21     | starrocks  |   4287.7 |      5 |     12637   |   15584.9 |   8711.1 |   5182.7 |  28225.7 |
| Q21     | trino      |  13741   |      5 |     64726.4 |   64567.9 |  37235.1 |  14986   | 101194   |
| Q22     | clickhouse |    268.5 |      5 |      8838.3 |    8803.5 |   1987.2 |   5719.9 |  10687.8 |
| Q22     | duckdb     |    243.7 |      5 |      7641.2 |    8220.4 |   6124.5 |    268.7 |  17489.2 |
| Q22     | exasol     |     55.4 |      5 |       593.2 |     590.5 |     97.9 |    434.3 |    681.2 |
| Q22     | starrocks  |    193.1 |      5 |      7127   |    6122.7 |   2321   |   3073.2 |   8452.5 |
| Q22     | trino      |   1604.7 |      5 |      5863.6 |    5912.7 |    187.3 |   5717.2 |   6206.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        3397.6 |          6558.2 |    1.93 |      0.52 | False    |
| Q02     | exasol            | starrocks           |         232.5 |          1818.5 |    7.82 |      0.13 | False    |
| Q03     | exasol            | starrocks           |        1384.5 |          3810.5 |    2.75 |      0.36 | False    |
| Q04     | exasol            | starrocks           |         416.6 |          8042.5 |   19.31 |      0.05 | False    |
| Q05     | exasol            | starrocks           |        1273.3 |          6517.2 |    5.12 |      0.2  | False    |
| Q06     | exasol            | starrocks           |         226.4 |          1944.9 |    8.59 |      0.12 | False    |
| Q07     | exasol            | starrocks           |        1593.5 |          6444.9 |    4.04 |      0.25 | False    |
| Q08     | exasol            | starrocks           |         461   |          6571.3 |   14.25 |      0.07 | False    |
| Q09     | exasol            | starrocks           |        5428.9 |         12792.2 |    2.36 |      0.42 | False    |
| Q10     | exasol            | starrocks           |        1887.1 |          6713.5 |    3.56 |      0.28 | False    |
| Q11     | exasol            | starrocks           |         483.9 |           983.9 |    2.03 |      0.49 | False    |
| Q12     | exasol            | starrocks           |         542.7 |          3126.3 |    5.76 |      0.17 | False    |
| Q13     | exasol            | starrocks           |        4117.3 |         12051.8 |    2.93 |      0.34 | False    |
| Q14     | exasol            | starrocks           |         581.5 |          5513.3 |    9.48 |      0.11 | False    |
| Q15     | exasol            | starrocks           |        1460.6 |          6590.1 |    4.51 |      0.22 | False    |
| Q16     | exasol            | starrocks           |        2156.1 |          1981.7 |    0.92 |      1.09 | True     |
| Q17     | exasol            | starrocks           |          95.8 |          5807.4 |   60.62 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3155.7 |          9655.1 |    3.06 |      0.33 | False    |
| Q19     | exasol            | starrocks           |          79.7 |          2485.4 |   31.18 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         798.6 |          4586.7 |    5.74 |      0.17 | False    |
| Q21     | exasol            | starrocks           |         834.2 |         12637   |   15.15 |      0.07 | False    |
| Q22     | exasol            | starrocks           |         593.2 |          7127   |   12.01 |      0.08 | False    |
| Q01     | exasol            | duckdb              |        3397.6 |          7508.7 |    2.21 |      0.45 | False    |
| Q02     | exasol            | duckdb              |         232.5 |          7838.5 |   33.71 |      0.03 | False    |
| Q03     | exasol            | duckdb              |        1384.5 |          7117   |    5.14 |      0.19 | False    |
| Q04     | exasol            | duckdb              |         416.6 |          7399.3 |   17.76 |      0.06 | False    |
| Q05     | exasol            | duckdb              |        1273.3 |          8526.4 |    6.7  |      0.15 | False    |
| Q06     | exasol            | duckdb              |         226.4 |          7286.6 |   32.18 |      0.03 | False    |
| Q07     | exasol            | duckdb              |        1593.5 |          6627.9 |    4.16 |      0.24 | False    |
| Q08     | exasol            | duckdb              |         461   |          7848.3 |   17.02 |      0.06 | False    |
| Q09     | exasol            | duckdb              |        5428.9 |          9210.6 |    1.7  |      0.59 | False    |
| Q10     | exasol            | duckdb              |        1887.1 |          7313.4 |    3.88 |      0.26 | False    |
| Q11     | exasol            | duckdb              |         483.9 |          7421   |   15.34 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         542.7 |          8171   |   15.06 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        4117.3 |          7962.4 |    1.93 |      0.52 | False    |
| Q14     | exasol            | duckdb              |         581.5 |          6277.3 |   10.8  |      0.09 | False    |
| Q15     | exasol            | duckdb              |        1460.6 |          8846.5 |    6.06 |      0.17 | False    |
| Q16     | exasol            | duckdb              |        2156.1 |          6625   |    3.07 |      0.33 | False    |
| Q17     | exasol            | duckdb              |          95.8 |          7914.7 |   82.62 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3155.7 |          8456   |    2.68 |      0.37 | False    |
| Q19     | exasol            | duckdb              |          79.7 |          8850.5 |  111.05 |      0.01 | False    |
| Q20     | exasol            | duckdb              |         798.6 |         10480.8 |   13.12 |      0.08 | False    |
| Q21     | exasol            | duckdb              |         834.2 |          8159.6 |    9.78 |      0.1  | False    |
| Q22     | exasol            | duckdb              |         593.2 |          7641.2 |   12.88 |      0.08 | False    |
| Q01     | exasol            | clickhouse          |        3397.6 |         12660.9 |    3.73 |      0.27 | False    |
| Q02     | exasol            | clickhouse          |         232.5 |         12180.2 |   52.39 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |        1384.5 |         14049.8 |   10.15 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |         416.6 |         27505.5 |   66.02 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1273.3 |         19110.7 |   15.01 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         226.4 |          2983.3 |   13.18 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        1593.5 |         31511.1 |   19.77 |      0.05 | False    |
| Q08     | exasol            | clickhouse          |         461   |         22386.9 |   48.56 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        5428.9 |         18168.9 |    3.35 |      0.3  | False    |
| Q10     | exasol            | clickhouse          |        1887.1 |         32884.8 |   17.43 |      0.06 | False    |
| Q11     | exasol            | clickhouse          |         483.9 |          9748.5 |   20.15 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |         542.7 |          8680.6 |   16    |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        4117.3 |         16912.7 |    4.11 |      0.24 | False    |
| Q14     | exasol            | clickhouse          |         581.5 |          4588.1 |    7.89 |      0.13 | False    |
| Q15     | exasol            | clickhouse          |        1460.6 |          4011   |    2.75 |      0.36 | False    |
| Q16     | exasol            | clickhouse          |        2156.1 |          8345.2 |    3.87 |      0.26 | False    |
| Q17     | exasol            | clickhouse          |          95.8 |         10937.8 |  114.17 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3155.7 |         18043.9 |    5.72 |      0.17 | False    |
| Q19     | exasol            | clickhouse          |          79.7 |         26628.9 |  334.11 |      0    | False    |
| Q20     | exasol            | clickhouse          |         798.6 |         14619.8 |   18.31 |      0.05 | False    |
| Q21     | exasol            | clickhouse          |         834.2 |         17448.4 |   20.92 |      0.05 | False    |
| Q22     | exasol            | clickhouse          |         593.2 |          8838.3 |   14.9  |      0.07 | False    |
| Q01     | exasol            | trino               |        3397.6 |         46795.2 |   13.77 |      0.07 | False    |
| Q02     | exasol            | trino               |         232.5 |          8983   |   38.64 |      0.03 | False    |
| Q03     | exasol            | trino               |        1384.5 |         34046.9 |   24.59 |      0.04 | False    |
| Q04     | exasol            | trino               |         416.6 |         32342.2 |   77.63 |      0.01 | False    |
| Q05     | exasol            | trino               |        1273.3 |         53187.7 |   41.77 |      0.02 | False    |
| Q06     | exasol            | trino               |         226.4 |         13789.6 |   60.91 |      0.02 | False    |
| Q07     | exasol            | trino               |        1593.5 |         41412.4 |   25.99 |      0.04 | False    |
| Q08     | exasol            | trino               |         461   |         51129.1 |  110.91 |      0.01 | False    |
| Q09     | exasol            | trino               |        5428.9 |        122799   |   22.62 |      0.04 | False    |
| Q10     | exasol            | trino               |        1887.1 |         52824.2 |   27.99 |      0.04 | False    |
| Q11     | exasol            | trino               |         483.9 |          4737.5 |    9.79 |      0.1  | False    |
| Q12     | exasol            | trino               |         542.7 |         26437.8 |   48.72 |      0.02 | False    |
| Q13     | exasol            | trino               |        4117.3 |        106463   |   25.86 |      0.04 | False    |
| Q14     | exasol            | trino               |         581.5 |         31376   |   53.96 |      0.02 | False    |
| Q15     | exasol            | trino               |        1460.6 |         30169.1 |   20.66 |      0.05 | False    |
| Q16     | exasol            | trino               |        2156.1 |          9349.2 |    4.34 |      0.23 | False    |
| Q17     | exasol            | trino               |          95.8 |         65983.7 |  688.77 |      0    | False    |
| Q18     | exasol            | trino               |        3155.7 |         49329.7 |   15.63 |      0.06 | False    |
| Q19     | exasol            | trino               |          79.7 |          7355.9 |   92.29 |      0.01 | False    |
| Q20     | exasol            | trino               |         798.6 |         26787.3 |   33.54 |      0.03 | False    |
| Q21     | exasol            | trino               |         834.2 |         64726.4 |   77.59 |      0.01 | False    |
| Q22     | exasol            | trino               |         593.2 |          5863.6 |    9.88 |      0.1  | False    |

### Per-Stream Statistics

This benchmark was executed using **16 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 16596.0 | 19911.9 | 5303.9 | 29317.0 |
| 1 | 7 | 10962.3 | 10705.3 | 927.4 | 21949.6 |
| 10 | 7 | 16021.0 | 15074.9 | 1341.7 | 33383.3 |
| 11 | 7 | 13180.2 | 13993.1 | 2373.8 | 19110.7 |
| 12 | 7 | 17011.6 | 10998.1 | 7406.8 | 31251.1 |
| 13 | 7 | 17252.6 | 18043.9 | 3098.6 | 31511.1 |
| 14 | 6 | 12680.0 | 12729.0 | 4588.1 | 23179.2 |
| 15 | 6 | 17131.1 | 13900.6 | 5374.3 | 40904.2 |
| 2 | 7 | 15622.5 | 13168.3 | 8680.6 | 32884.8 |
| 3 | 7 | 16011.1 | 12102.3 | 5349.1 | 30291.7 |
| 4 | 7 | 14298.0 | 14049.8 | 2983.3 | 33133.0 |
| 5 | 7 | 14247.6 | 12634.7 | 4011.0 | 31242.9 |
| 6 | 7 | 17553.5 | 18527.3 | 3920.7 | 30081.5 |
| 7 | 7 | 11370.6 | 10687.8 | 2030.0 | 30696.1 |
| 8 | 7 | 17328.4 | 13281.3 | 5760.0 | 39632.7 |
| 9 | 7 | 12536.7 | 10937.8 | 1960.5 | 21140.1 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 10687.8ms
- Slowest stream median: 19911.9ms
- Stream performance variation: 86.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 7103.4 | 7962.4 | 1022.0 | 11360.1 |
| 1 | 7 | 7147.4 | 8096.2 | 1179.8 | 11073.7 |
| 10 | 7 | 7900.5 | 7692.5 | 5522.2 | 10480.8 |
| 11 | 7 | 7966.1 | 7763.8 | 5768.9 | 10406.3 |
| 12 | 7 | 7008.1 | 7421.0 | 268.7 | 10780.2 |
| 13 | 7 | 8093.4 | 7508.7 | 436.0 | 17489.2 |
| 14 | 6 | 8188.8 | 7333.8 | 6775.8 | 10751.0 |
| 15 | 6 | 8224.8 | 7926.9 | 6625.0 | 10011.6 |
| 2 | 7 | 7454.2 | 7313.4 | 1629.4 | 11298.7 |
| 3 | 7 | 7578.3 | 8159.6 | 1701.0 | 10906.4 |
| 4 | 7 | 7626.5 | 7818.2 | 3829.5 | 9491.8 |
| 5 | 7 | 7667.6 | 7471.5 | 4160.9 | 9506.5 |
| 6 | 7 | 7716.2 | 7840.7 | 4538.3 | 9449.4 |
| 7 | 7 | 7730.9 | 7641.2 | 4831.6 | 9616.8 |
| 8 | 7 | 7782.8 | 7815.2 | 5033.1 | 10127.4 |
| 9 | 7 | 7837.1 | 7914.7 | 5137.3 | 10686.3 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 7313.4ms
- Slowest stream median: 8159.6ms
- Stream performance variation: 11.6% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 1800.4 | 1128.7 | 391.7 | 4117.3 |
| 1 | 7 | 626.0 | 461.0 | 96.9 | 2023.4 |
| 10 | 7 | 1521.1 | 1044.9 | 55.8 | 5554.4 |
| 11 | 7 | 1572.0 | 1273.3 | 247.5 | 4298.5 |
| 12 | 7 | 1397.0 | 1276.7 | 275.6 | 4144.8 |
| 13 | 7 | 1502.6 | 593.9 | 39.7 | 3949.2 |
| 14 | 6 | 1305.4 | 626.9 | 518.1 | 4176.8 |
| 15 | 6 | 1690.6 | 1102.3 | 397.7 | 5428.9 |
| 2 | 7 | 1815.7 | 785.0 | 359.1 | 4804.2 |
| 3 | 7 | 1079.3 | 416.6 | 92.7 | 3610.6 |
| 4 | 7 | 1471.7 | 1367.5 | 172.4 | 2815.0 |
| 5 | 7 | 1091.7 | 593.2 | 231.8 | 3072.5 |
| 6 | 7 | 1552.2 | 344.6 | 54.5 | 6375.6 |
| 7 | 7 | 603.7 | 329.1 | 102.2 | 2177.5 |
| 8 | 7 | 1740.0 | 1334.5 | 235.6 | 4426.1 |
| 9 | 7 | 1375.7 | 284.4 | 95.8 | 4983.4 |

**Performance Analysis for Exasol:**
- Fastest stream median: 284.4ms
- Slowest stream median: 1367.5ms
- Stream performance variation: 380.8% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 7329.8 | 7236.3 | 339.6 | 12938.9 |
| 1 | 7 | 4678.8 | 4328.5 | 1818.5 | 7263.6 |
| 10 | 7 | 6516.7 | 4903.5 | 686.5 | 12737.6 |
| 11 | 7 | 5143.0 | 6063.7 | 1203.6 | 9502.6 |
| 12 | 7 | 5796.9 | 6753.9 | 792.5 | 10526.6 |
| 13 | 7 | 6422.4 | 5807.4 | 3073.2 | 9655.1 |
| 14 | 6 | 6395.2 | 5988.9 | 1486.9 | 12125.7 |
| 15 | 6 | 6350.0 | 5932.6 | 1981.7 | 12241.1 |
| 2 | 7 | 7078.3 | 7157.6 | 1358.4 | 14282.7 |
| 3 | 7 | 6767.4 | 3140.8 | 358.0 | 28225.7 |
| 4 | 7 | 7133.7 | 6590.1 | 46.0 | 19586.0 |
| 5 | 7 | 6407.8 | 6165.7 | 1743.9 | 10833.8 |
| 6 | 7 | 6763.7 | 4105.7 | 1639.4 | 17995.6 |
| 7 | 7 | 5100.0 | 2773.5 | 2237.6 | 9079.4 |
| 8 | 7 | 6586.0 | 6444.9 | 1362.2 | 10603.1 |
| 9 | 7 | 6436.9 | 6571.3 | 391.6 | 13953.5 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2773.5ms
- Slowest stream median: 7236.3ms
- Stream performance variation: 160.9% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 46562.5 | 19027.6 | 6634.6 | 127403.1 |
| 1 | 7 | 35936.8 | 31376.0 | 3810.3 | 69611.5 |
| 10 | 7 | 42630.1 | 33158.2 | 3923.0 | 159310.7 |
| 11 | 7 | 34783.3 | 33764.0 | 8983.0 | 52338.7 |
| 12 | 7 | 32356.9 | 27288.0 | 4161.9 | 86592.6 |
| 13 | 7 | 35340.4 | 36788.7 | 6206.1 | 53370.3 |
| 14 | 6 | 41011.3 | 31861.3 | 4737.5 | 99691.5 |
| 15 | 6 | 46973.6 | 40470.6 | 5953.9 | 122799.1 |
| 2 | 7 | 43450.4 | 41942.1 | 5553.8 | 107591.4 |
| 3 | 7 | 38769.8 | 28508.9 | 9345.9 | 99812.0 |
| 4 | 7 | 44816.5 | 28867.7 | 13789.6 | 101193.5 |
| 5 | 7 | 29206.9 | 30169.1 | 5863.6 | 67397.3 |
| 6 | 7 | 42166.3 | 35175.3 | 5726.5 | 138064.5 |
| 7 | 7 | 22766.3 | 22443.4 | 5967.4 | 45164.1 |
| 8 | 7 | 37327.1 | 29309.2 | 9560.8 | 106463.2 |
| 9 | 7 | 41349.6 | 22050.4 | 3400.4 | 118808.8 |

**Performance Analysis for Trino:**
- Fastest stream median: 19027.6ms
- Slowest stream median: 41942.1ms
- Stream performance variation: 120.4% difference between fastest and slowest streams
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
- Median runtime: 711.4ms
- Average runtime: 1382.0ms
- Fastest query: 39.7ms
- Slowest query: 6375.6ms

**starrocks:**
- Median runtime: 6089.8ms
- Average runtime: 6305.5ms
- Fastest query: 46.0ms
- Slowest query: 28225.7ms

**duckdb:**
- Median runtime: 7789.5ms
- Average runtime: 7679.7ms
- Fastest query: 268.7ms
- Slowest query: 17489.2ms

**clickhouse:**
- Median runtime: 13224.8ms
- Average runtime: 14989.2ms
- Fastest query: 927.4ms
- Slowest query: 40904.2ms

**trino:**
- Median runtime: 31134.0ms
- Average runtime: 38365.0ms
- Fastest query: 3400.4ms
- Slowest query: 159310.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_16-benchmark.zip`](extscal_streams_16-benchmark.zip)

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
  - memory_limit: 192g
  - max_threads: 32
  - max_memory_usage: 12000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 8000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 143GB
  - query_max_memory_per_node: 143GB

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
  - memory_limit: 192GB
  - threads: 32


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (sequential, results discarded)
- 5 measured runs per query (results recorded)
- Measured runs executed across 16 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts