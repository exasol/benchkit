# Streamlined Scalability - Scale Factor 50 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.2xlarge
**Date:** 2026-02-10 10:28:40

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
- exasol was the fastest overall with 909.0ms median runtime
- trino was 36.2x slower- Tested 550 total query executions across 22 different TPC-H queries
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2881B74EF40398C6C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2881B74EF40398C6C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2881B74EF40398C6C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2881B74EF40398C6C /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6657678C6B71B85DD with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6657678C6B71B85DD

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6657678C6B71B85DD to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS6657678C6B71B85DD /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EAEA92F99E3A8A0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EAEA92F99E3A8A0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EAEA92F99E3A8A0 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS24EAEA92F99E3A8A0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `48g`
- Max threads: `8`
- Max memory usage: `15.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22A8D8BB3EA2E7E30 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22A8D8BB3EA2E7E30

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22A8D8BB3EA2E7E30 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22A8D8BB3EA2E7E30 /data

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
unzip extscal_sf_50-benchmark.zip
cd extscal_sf_50

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
| Clickhouse | 543.84s | 0.12s | 262.66s | 1008.95s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 549.95s | 0.13s | 349.06s | 1057.55s | 15.0 GB | 15.0 GB | 1.0x |
| Trino | 139.66s | 0.37s | 0.00s | 202.16s | N/A | N/A | N/A |
| Duckdb | 547.87s | 0.04s | 207.47s | 781.43s | 412.9 MB | N/A | N/A |
| Exasol | 273.66s | 1.92s | 304.07s | 721.87s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 202.16s
- Starrocks took 1057.55s (5.2x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4575.9 |      5 |     18051.5 |   16958.7 |   3500.7 |  10802.3 |  19187.2 |
| Q01     | duckdb     |   2245.6 |      5 |      5734.7 |    6348.9 |   2432.5 |   4341.1 |  10552.1 |
| Q01     | exasol     |   1605.5 |      5 |      5644.7 |    4746.8 |   1383.2 |   2577.3 |   5727.9 |
| Q01     | starrocks  |   6764.7 |      5 |     18733.1 |   19934.5 |   6684.6 |  11790.6 |  29827.1 |
| Q01     | trino      |  10257.2 |      5 |     35021.5 |   34422.1 |  14827   |  17632.7 |  49082.6 |
| Q02     | clickhouse |   2006.1 |      5 |     10425.7 |   10453.2 |   4676.1 |   4167.5 |  16081.4 |
| Q02     | duckdb     |    464.2 |      5 |      4677.1 |    5392.4 |   1745.3 |   3676.7 |   7479.2 |
| Q02     | exasol     |    243.9 |      5 |       206   |     216.6 |     24   |    189.6 |    243   |
| Q02     | starrocks  |    473.2 |      5 |       921.6 |     966.8 |    238.2 |    761.7 |   1357.4 |
| Q02     | trino      |   5484.1 |      5 |     16333.7 |   22020.4 |  11679.2 |   9160.7 |  34456.4 |
| Q03     | clickhouse |   7356   |      5 |     20297.5 |   18450.9 |   8561.3 |   6177.6 |  27872.7 |
| Q03     | duckdb     |   1406.8 |      5 |      2989.5 |    3711.8 |   2693   |   1239.2 |   6921.2 |
| Q03     | exasol     |    616.8 |      5 |       668.3 |    1623.8 |   1367.7 |    610.7 |   3338.4 |
| Q03     | starrocks  |   1580.7 |      5 |      1695.5 |    2677.8 |   1868.3 |   1263.2 |   5538.1 |
| Q03     | trino      |  13539.6 |      5 |     34667.6 |   30873.7 |  13760.1 |  14688.8 |  49395.9 |
| Q04     | clickhouse |   8934.6 |      5 |     22509.9 |   22948.8 |   3349.8 |  19179.2 |  27224.4 |
| Q04     | duckdb     |   1327.9 |      5 |      8639.1 |    8798.2 |   2762.8 |   4858.2 |  12309.1 |
| Q04     | exasol     |    111.3 |      5 |       426.6 |     502.6 |    226   |    223.1 |    744.3 |
| Q04     | starrocks  |   1301.2 |      5 |      4192.5 |    4172.5 |    803.8 |   2937.9 |   5156.7 |
| Q04     | trino      |   9734.6 |      5 |     31584.3 |   28450   |   9873   |  16706.5 |  39360.5 |
| Q05     | clickhouse |   5997   |      5 |     23636.2 |   23220.5 |   3009.5 |  19783.8 |  27276.3 |
| Q05     | duckdb     |   1476.2 |      5 |      5476.7 |    7124.4 |   3913.6 |   3582.4 |  13689.4 |
| Q05     | exasol     |    486   |      5 |      1999   |    1763.7 |    522.4 |    845.9 |   2125.1 |
| Q05     | starrocks  |   2594   |      5 |      9436   |    8800.5 |   2269.1 |   6293.6 |  11086.5 |
| Q05     | trino      |  12575.5 |      5 |     73210.8 |   80098.9 |  20794.9 |  64145.1 | 116624   |
| Q06     | clickhouse |    301.1 |      5 |      2554   |    2532.4 |    563.8 |   1867.2 |   3380.3 |
| Q06     | duckdb     |    406.5 |      5 |      3106.2 |    3850.3 |   3505.2 |    415.2 |   9728.2 |
| Q06     | exasol     |     72.2 |      5 |       272.9 |     287   |    179.6 |    139.2 |    579.1 |
| Q06     | starrocks  |    205.8 |      5 |       416.4 |     499.5 |    241.1 |    282.2 |    836.2 |
| Q06     | trino      |   4519.6 |      5 |     16573.2 |   15802.4 |   7303   |   7066.6 |  23624   |
| Q07     | clickhouse |  13957   |      5 |     37609.9 |   35049   |  13895.1 |  12426.2 |  50654.7 |
| Q07     | duckdb     |   1318.8 |      5 |      5109.2 |    6779.1 |   2595.6 |   4799.3 |  10579.3 |
| Q07     | exasol     |    605   |      5 |      2384.7 |    2101.2 |    832.2 |    632.2 |   2646.4 |
| Q07     | starrocks  |   1498.6 |      5 |      4089   |    3516.6 |   1290.2 |   1466.5 |   4660.6 |
| Q07     | trino      |   9676.2 |      5 |     35129   |   37250.6 |  13530.7 |  18061.9 |  55190.8 |
| Q08     | clickhouse |   7545.2 |      5 |     28943.4 |   27673.8 |   5063.9 |  19422.4 |  33231.2 |
| Q08     | duckdb     |   1441.1 |      5 |      4825.3 |    6287.3 |   2727.3 |   4082.3 |  10700.9 |
| Q08     | exasol     |    181.2 |      5 |       584.3 |     550   |    199.2 |    222.2 |    712.1 |
| Q08     | starrocks  |   2133.5 |      5 |      7509   |    7703.2 |   1678.6 |   5422.1 |   9630.2 |
| Q08     | trino      |  13247.1 |      5 |     34271.2 |   45315.2 |  20282   |  27778.1 |  69250.6 |
| Q09     | clickhouse |   4162.8 |      5 |     19604.7 |   19012.3 |   3063.2 |  14083.2 |  21569.4 |
| Q09     | duckdb     |   4415.3 |      5 |      9689.4 |   10006   |   3018.8 |   6892.2 |  13703.7 |
| Q09     | exasol     |   2009.4 |      5 |      9734.9 |    8984.1 |   1540.5 |   6368.3 |  10064.5 |
| Q09     | starrocks  |   5893.5 |      5 |     11476.5 |   11296   |    631.9 |  10389.9 |  11980.9 |
| Q09     | trino      |  31214.9 |      5 |    120219   |  110067   |  18182.5 |  87697.6 | 125860   |
| Q10     | clickhouse |   8793.2 |      5 |     30491.9 |   32065.8 |   4212.3 |  28466.2 |  38028   |
| Q10     | duckdb     |   2129.6 |      5 |      8865   |    8041.2 |   2115.8 |   4275.8 |   9260   |
| Q10     | exasol     |    720.8 |      5 |      2419.4 |    2117.1 |    708.1 |   1343.7 |   2739.7 |
| Q10     | starrocks  |   2095   |      5 |      4487.6 |    4520.2 |    373.3 |   4205.2 |   5121   |
| Q10     | trino      |  13559.3 |      5 |     76438.7 |   72973.5 |  31800.8 |  36600.7 | 114536   |
| Q11     | clickhouse |   1054.1 |      5 |      8719   |    8622   |   2780.7 |   4460.8 |  12003.3 |
| Q11     | duckdb     |    199.2 |      5 |      6597.3 |    7618.2 |   1814.2 |   6202.4 |  10340.9 |
| Q11     | exasol     |    149.1 |      5 |       453   |     451.3 |    113.6 |    275.7 |    586.4 |
| Q11     | starrocks  |    316.8 |      5 |       550.1 |     585.3 |     58.4 |    542.2 |    678.4 |
| Q11     | trino      |   1937.2 |      5 |      5305.6 |    4858.8 |   1797.9 |   1937.1 |   6510.6 |
| Q12     | clickhouse |   3387.2 |      5 |      5732.8 |    7690.5 |   5427.5 |   4056.8 |  17314.9 |
| Q12     | duckdb     |   1497.7 |      5 |      7662.3 |    7104.6 |   4112.4 |   1497.9 |  11845.2 |
| Q12     | exasol     |    149.5 |      5 |       553.9 |     668.2 |    226.4 |    421.1 |    926   |
| Q12     | starrocks  |    618.3 |      5 |      1612.1 |    1611.8 |     98.8 |   1482.6 |   1737.8 |
| Q12     | trino      |   6686.8 |      5 |     26922.9 |   22777   |   8808.5 |   8963   |  29919.2 |
| Q13     | clickhouse |   4470.9 |      5 |     12259.2 |   13579.6 |   4312.2 |   9570.4 |  20934.8 |
| Q13     | duckdb     |   3680.4 |      5 |      7437.3 |    8380.2 |   4013   |   3687.5 |  14635.3 |
| Q13     | exasol     |   1492.5 |      5 |      5691.6 |    5269.2 |   1391.9 |   2846.9 |   6383.1 |
| Q13     | starrocks  |   3221.8 |      5 |      9341.4 |    8659.5 |   3281.1 |   3354.2 |  11597.1 |
| Q13     | trino      |  16145.1 |      5 |     64388.9 |   63578   |  22442.8 |  32870.9 |  87992.4 |
| Q14     | clickhouse |    329.4 |      5 |      3278   |    3625.3 |   1692.9 |   1512.1 |   6141.7 |
| Q14     | duckdb     |   1066.7 |      5 |      4391.9 |    6262.2 |   3632.2 |   2358.2 |  10637.8 |
| Q14     | exasol     |    144.8 |      5 |       678.5 |     740.9 |    146   |    629.3 |    981.5 |
| Q14     | starrocks  |    220.7 |      5 |       650   |     662.7 |    219.9 |    446.8 |    961.4 |
| Q14     | trino      |   6422.2 |      5 |     23396.3 |   30303.7 |  14438.4 |  21282.6 |  55626.3 |
| Q15     | clickhouse |    345.2 |      5 |      2515.7 |    3317.3 |   1998.9 |    960.6 |   6059.5 |
| Q15     | duckdb     |    898.1 |      5 |      4887.4 |    4922.2 |   2935.3 |    903   |   7834.4 |
| Q15     | exasol     |    389.5 |      5 |      1415.2 |    1475.9 |    150   |   1378.9 |   1742   |
| Q15     | starrocks  |    218.6 |      5 |       477.4 |     537   |    210.2 |    377.8 |    905   |
| Q15     | trino      |  11644.9 |      5 |     30504.4 |   32096.7 |   7372   |  22389.4 |  42672.5 |
| Q16     | clickhouse |    977.7 |      5 |      6183.1 |    7000.4 |   3841.4 |   3927.2 |  13309   |
| Q16     | duckdb     |    662.4 |      5 |      4192.6 |    4585.4 |   3193.3 |    660.1 |   9578   |
| Q16     | exasol     |    600.6 |      5 |      2091.2 |    2077.8 |     53.9 |   1999   |   2133.2 |
| Q16     | starrocks  |    736.5 |      5 |      1384.3 |    1499   |    485.8 |    909.2 |   2230.6 |
| Q16     | trino      |   3632.1 |      5 |     14959.6 |   20882.6 |  12061.6 |   9932.5 |  34930.9 |
| Q17     | clickhouse |   1900.7 |      5 |      6723.9 |    9493.4 |   4718.4 |   6188.4 |  17309.8 |
| Q17     | duckdb     |   1598.8 |      5 |      6880.7 |    7131   |    780.6 |   6369.9 |   8445.7 |
| Q17     | exasol     |     28.4 |      5 |       109.5 |     103.9 |     26.7 |     66.9 |    135.2 |
| Q17     | starrocks  |   1460.2 |      5 |      3374.6 |    3671.5 |    780.3 |   3044.1 |   4937.9 |
| Q17     | trino      |  13920.2 |      5 |     47057.4 |   44999.9 |   8531.5 |  31651.3 |  54841.6 |
| Q18     | clickhouse |   6660.3 |      5 |     32306.6 |   32255.5 |   8271.2 |  23362.4 |  44594.5 |
| Q18     | duckdb     |   3034.3 |      5 |      8302   |    8601.5 |   2208.1 |   6326.2 |  11329.1 |
| Q18     | exasol     |    987.4 |      5 |      3457.2 |    3145.2 |    833   |   1666.4 |   3692   |
| Q18     | starrocks  |   6231.8 |      5 |     33087.6 |   32760   |  10386.2 |  21746   |  49133.6 |
| Q18     | trino      |  12395.4 |      5 |     56273.5 |   48672   |  15486.8 |  22293.6 |  59591.1 |
| Q19     | clickhouse |   9692.1 |      5 |     28247.5 |   29010.9 |   2523.1 |  27137   |  33312.4 |
| Q19     | duckdb     |   1517.7 |      5 |      5174.9 |    5299.4 |   2516.4 |   1515.4 |   8495.4 |
| Q19     | exasol     |     59.4 |      5 |       161.7 |     147   |     36.8 |     90.9 |    186.7 |
| Q19     | starrocks  |   2083.3 |      5 |      3778.7 |    4026.8 |    740.8 |   3181.7 |   4930.3 |
| Q19     | trino      |   7417.7 |      5 |     17316.7 |   15111.3 |   4727.8 |   9479.4 |  20266.4 |
| Q20     | clickhouse |   2621.5 |      5 |     11487   |   10594.6 |   2543.1 |   7634.1 |  13690.5 |
| Q20     | duckdb     |   1383.7 |      5 |      6750.6 |    6465.9 |   3480.7 |   3117.4 |  11721.8 |
| Q20     | exasol     |    343.3 |      5 |      1056.1 |     966.2 |    397   |    463.7 |   1419.4 |
| Q20     | starrocks  |    472.9 |      5 |      1283.1 |    1286.4 |    187.7 |   1038.3 |   1564.8 |
| Q20     | trino      |   7171   |      5 |     15463.6 |   21529.7 |  12141.2 |  10328.7 |  40777   |
| Q21     | clickhouse |   4881.6 |      5 |     15034.4 |   16219.8 |   2394.8 |  14540.9 |  20209   |
| Q21     | duckdb     |   6844.9 |      5 |      9398.9 |    9462.8 |   1877.9 |   6893.5 |  12134.7 |
| Q21     | exasol     |    837.8 |      5 |      2140.8 |    2522.3 |   1017.3 |   1321.1 |   3735.3 |
| Q21     | starrocks  |   7664.9 |      5 |     23400   |   20661.8 |   5364.8 |  12587.4 |  25829.9 |
| Q21     | trino      |  32423.3 |      5 |     78350.6 |   77411.7 |  23709   |  51651.2 | 109018   |
| Q22     | clickhouse |    863   |      5 |      8155.7 |    6485.3 |   2803.4 |   3135.5 |   8726.4 |
| Q22     | duckdb     |    783.6 |      5 |      8028.2 |    9930.1 |   4735.1 |   4260.9 |  15396.9 |
| Q22     | exasol     |    178   |      5 |       684.8 |     620   |    187   |    293.1 |    757.1 |
| Q22     | starrocks  |    641   |      5 |      1486   |    1389.5 |    500.6 |    539.3 |   1851.5 |
| Q22     | trino      |   4674.6 |      5 |     12187.5 |   14928.5 |   6016.3 |  10508.3 |  24865.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        5644.7 |          5734.7 |    1.02 |      0.98 | False    |
| Q02     | exasol            | duckdb              |         206   |          4677.1 |   22.7  |      0.04 | False    |
| Q03     | exasol            | duckdb              |         668.3 |          2989.5 |    4.47 |      0.22 | False    |
| Q04     | exasol            | duckdb              |         426.6 |          8639.1 |   20.25 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1999   |          5476.7 |    2.74 |      0.37 | False    |
| Q06     | exasol            | duckdb              |         272.9 |          3106.2 |   11.38 |      0.09 | False    |
| Q07     | exasol            | duckdb              |        2384.7 |          5109.2 |    2.14 |      0.47 | False    |
| Q08     | exasol            | duckdb              |         584.3 |          4825.3 |    8.26 |      0.12 | False    |
| Q09     | exasol            | duckdb              |        9734.9 |          9689.4 |    1    |      1    | True     |
| Q10     | exasol            | duckdb              |        2419.4 |          8865   |    3.66 |      0.27 | False    |
| Q11     | exasol            | duckdb              |         453   |          6597.3 |   14.56 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         553.9 |          7662.3 |   13.83 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        5691.6 |          7437.3 |    1.31 |      0.77 | False    |
| Q14     | exasol            | duckdb              |         678.5 |          4391.9 |    6.47 |      0.15 | False    |
| Q15     | exasol            | duckdb              |        1415.2 |          4887.4 |    3.45 |      0.29 | False    |
| Q16     | exasol            | duckdb              |        2091.2 |          4192.6 |    2    |      0.5  | False    |
| Q17     | exasol            | duckdb              |         109.5 |          6880.7 |   62.84 |      0.02 | False    |
| Q18     | exasol            | duckdb              |        3457.2 |          8302   |    2.4  |      0.42 | False    |
| Q19     | exasol            | duckdb              |         161.7 |          5174.9 |   32    |      0.03 | False    |
| Q20     | exasol            | duckdb              |        1056.1 |          6750.6 |    6.39 |      0.16 | False    |
| Q21     | exasol            | duckdb              |        2140.8 |          9398.9 |    4.39 |      0.23 | False    |
| Q22     | exasol            | duckdb              |         684.8 |          8028.2 |   11.72 |      0.09 | False    |
| Q01     | exasol            | starrocks           |        5644.7 |         18733.1 |    3.32 |      0.3  | False    |
| Q02     | exasol            | starrocks           |         206   |           921.6 |    4.47 |      0.22 | False    |
| Q03     | exasol            | starrocks           |         668.3 |          1695.5 |    2.54 |      0.39 | False    |
| Q04     | exasol            | starrocks           |         426.6 |          4192.5 |    9.83 |      0.1  | False    |
| Q05     | exasol            | starrocks           |        1999   |          9436   |    4.72 |      0.21 | False    |
| Q06     | exasol            | starrocks           |         272.9 |           416.4 |    1.53 |      0.66 | False    |
| Q07     | exasol            | starrocks           |        2384.7 |          4089   |    1.71 |      0.58 | False    |
| Q08     | exasol            | starrocks           |         584.3 |          7509   |   12.85 |      0.08 | False    |
| Q09     | exasol            | starrocks           |        9734.9 |         11476.5 |    1.18 |      0.85 | False    |
| Q10     | exasol            | starrocks           |        2419.4 |          4487.6 |    1.85 |      0.54 | False    |
| Q11     | exasol            | starrocks           |         453   |           550.1 |    1.21 |      0.82 | False    |
| Q12     | exasol            | starrocks           |         553.9 |          1612.1 |    2.91 |      0.34 | False    |
| Q13     | exasol            | starrocks           |        5691.6 |          9341.4 |    1.64 |      0.61 | False    |
| Q14     | exasol            | starrocks           |         678.5 |           650   |    0.96 |      1.04 | True     |
| Q15     | exasol            | starrocks           |        1415.2 |           477.4 |    0.34 |      2.96 | True     |
| Q16     | exasol            | starrocks           |        2091.2 |          1384.3 |    0.66 |      1.51 | True     |
| Q17     | exasol            | starrocks           |         109.5 |          3374.6 |   30.82 |      0.03 | False    |
| Q18     | exasol            | starrocks           |        3457.2 |         33087.6 |    9.57 |      0.1  | False    |
| Q19     | exasol            | starrocks           |         161.7 |          3778.7 |   23.37 |      0.04 | False    |
| Q20     | exasol            | starrocks           |        1056.1 |          1283.1 |    1.21 |      0.82 | False    |
| Q21     | exasol            | starrocks           |        2140.8 |         23400   |   10.93 |      0.09 | False    |
| Q22     | exasol            | starrocks           |         684.8 |          1486   |    2.17 |      0.46 | False    |
| Q01     | exasol            | clickhouse          |        5644.7 |         18051.5 |    3.2  |      0.31 | False    |
| Q02     | exasol            | clickhouse          |         206   |         10425.7 |   50.61 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         668.3 |         20297.5 |   30.37 |      0.03 | False    |
| Q04     | exasol            | clickhouse          |         426.6 |         22509.9 |   52.77 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1999   |         23636.2 |   11.82 |      0.08 | False    |
| Q06     | exasol            | clickhouse          |         272.9 |          2554   |    9.36 |      0.11 | False    |
| Q07     | exasol            | clickhouse          |        2384.7 |         37609.9 |   15.77 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         584.3 |         28943.4 |   49.54 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        9734.9 |         19604.7 |    2.01 |      0.5  | False    |
| Q10     | exasol            | clickhouse          |        2419.4 |         30491.9 |   12.6  |      0.08 | False    |
| Q11     | exasol            | clickhouse          |         453   |          8719   |   19.25 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |         553.9 |          5732.8 |   10.35 |      0.1  | False    |
| Q13     | exasol            | clickhouse          |        5691.6 |         12259.2 |    2.15 |      0.46 | False    |
| Q14     | exasol            | clickhouse          |         678.5 |          3278   |    4.83 |      0.21 | False    |
| Q15     | exasol            | clickhouse          |        1415.2 |          2515.7 |    1.78 |      0.56 | False    |
| Q16     | exasol            | clickhouse          |        2091.2 |          6183.1 |    2.96 |      0.34 | False    |
| Q17     | exasol            | clickhouse          |         109.5 |          6723.9 |   61.41 |      0.02 | False    |
| Q18     | exasol            | clickhouse          |        3457.2 |         32306.6 |    9.34 |      0.11 | False    |
| Q19     | exasol            | clickhouse          |         161.7 |         28247.5 |  174.69 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |        1056.1 |         11487   |   10.88 |      0.09 | False    |
| Q21     | exasol            | clickhouse          |        2140.8 |         15034.4 |    7.02 |      0.14 | False    |
| Q22     | exasol            | clickhouse          |         684.8 |          8155.7 |   11.91 |      0.08 | False    |
| Q01     | exasol            | trino               |        5644.7 |         35021.5 |    6.2  |      0.16 | False    |
| Q02     | exasol            | trino               |         206   |         16333.7 |   79.29 |      0.01 | False    |
| Q03     | exasol            | trino               |         668.3 |         34667.6 |   51.87 |      0.02 | False    |
| Q04     | exasol            | trino               |         426.6 |         31584.3 |   74.04 |      0.01 | False    |
| Q05     | exasol            | trino               |        1999   |         73210.8 |   36.62 |      0.03 | False    |
| Q06     | exasol            | trino               |         272.9 |         16573.2 |   60.73 |      0.02 | False    |
| Q07     | exasol            | trino               |        2384.7 |         35129   |   14.73 |      0.07 | False    |
| Q08     | exasol            | trino               |         584.3 |         34271.2 |   58.65 |      0.02 | False    |
| Q09     | exasol            | trino               |        9734.9 |        120219   |   12.35 |      0.08 | False    |
| Q10     | exasol            | trino               |        2419.4 |         76438.7 |   31.59 |      0.03 | False    |
| Q11     | exasol            | trino               |         453   |          5305.6 |   11.71 |      0.09 | False    |
| Q12     | exasol            | trino               |         553.9 |         26922.9 |   48.61 |      0.02 | False    |
| Q13     | exasol            | trino               |        5691.6 |         64388.9 |   11.31 |      0.09 | False    |
| Q14     | exasol            | trino               |         678.5 |         23396.3 |   34.48 |      0.03 | False    |
| Q15     | exasol            | trino               |        1415.2 |         30504.4 |   21.55 |      0.05 | False    |
| Q16     | exasol            | trino               |        2091.2 |         14959.6 |    7.15 |      0.14 | False    |
| Q17     | exasol            | trino               |         109.5 |         47057.4 |  429.75 |      0    | False    |
| Q18     | exasol            | trino               |        3457.2 |         56273.5 |   16.28 |      0.06 | False    |
| Q19     | exasol            | trino               |         161.7 |         17316.7 |  107.09 |      0.01 | False    |
| Q20     | exasol            | trino               |        1056.1 |         15463.6 |   14.64 |      0.07 | False    |
| Q21     | exasol            | trino               |        2140.8 |         78350.6 |   36.6  |      0.03 | False    |
| Q22     | exasol            | trino               |         684.8 |         12187.5 |   17.8  |      0.06 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 16918.8 | 14787.6 | 2481.4 | 37768.8 |
| 1 | 28 | 15863.4 | 14854.6 | 960.6 | 38028.0 |
| 2 | 27 | 16773.1 | 14083.2 | 2219.6 | 44594.5 |
| 3 | 27 | 15204.7 | 11840.7 | 1867.2 | 50654.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 11840.7ms
- Slowest stream median: 14854.6ms
- Stream performance variation: 25.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6949.7 | 6972.8 | 1239.2 | 14635.3 |
| 1 | 28 | 6857.6 | 6625.3 | 415.2 | 15396.9 |
| 2 | 27 | 6797.6 | 6750.6 | 660.1 | 13703.7 |
| 3 | 27 | 7051.0 | 6876.3 | 1497.9 | 12309.1 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6625.3ms
- Slowest stream median: 6972.8ms
- Stream performance variation: 5.2% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 2150.2 | 2057.2 | 139.2 | 6383.1 |
| 1 | 28 | 1514.3 | 693.8 | 66.9 | 10064.5 |
| 2 | 27 | 2123.6 | 891.9 | 90.9 | 9734.9 |
| 3 | 27 | 1683.7 | 757.1 | 119.4 | 9929.1 |

**Performance Analysis for Exasol:**
- Fastest stream median: 693.8ms
- Slowest stream median: 2057.2ms
- Stream performance variation: 196.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 6914.8 | 4040.1 | 282.2 | 33087.6 |
| 1 | 28 | 6335.7 | 3500.4 | 416.4 | 49133.6 |
| 2 | 27 | 6718.6 | 4205.2 | 550.1 | 29827.1 |
| 3 | 27 | 5732.5 | 1851.5 | 302.0 | 23548.1 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1851.5ms
- Slowest stream median: 4205.2ms
- Stream performance variation: 127.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 41748.4 | 35228.7 | 6020.7 | 109018.3 |
| 1 | 28 | 37557.6 | 33053.8 | 4519.8 | 87697.6 |
| 2 | 27 | 43105.6 | 28722.6 | 1937.1 | 125859.9 |
| 3 | 27 | 36581.6 | 29919.2 | 5305.6 | 123497.4 |

**Performance Analysis for Trino:**
- Fastest stream median: 28722.6ms
- Slowest stream median: 35228.7ms
- Stream performance variation: 22.7% difference between fastest and slowest streams
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
- Median runtime: 909.0ms
- Average runtime: 1867.3ms
- Fastest query: 66.9ms
- Slowest query: 10064.5ms

**duckdb:**
- Median runtime: 6886.4ms
- Average runtime: 6913.8ms
- Fastest query: 415.2ms
- Slowest query: 15396.9ms

**starrocks:**
- Median runtime: 3364.4ms
- Average runtime: 6429.0ms
- Fastest query: 282.2ms
- Slowest query: 49133.6ms

**clickhouse:**
- Median runtime: 14021.7ms
- Average runtime: 16193.6ms
- Fastest query: 960.6ms
- Slowest query: 50654.7ms

**trino:**
- Median runtime: 32893.2ms
- Average runtime: 39746.5ms
- Fastest query: 1937.1ms
- Slowest query: 125859.9ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_sf_50-benchmark.zip`](extscal_sf_50-benchmark.zip)

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
  - max_memory_usage: 15000000000
  - max_bytes_before_external_group_by: 5000000000
  - max_bytes_before_external_sort: 5000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 10000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 48GB
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