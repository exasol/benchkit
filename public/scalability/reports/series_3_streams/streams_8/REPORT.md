# Streamlined Scalability - Stream Scaling (8 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-09 16:40:52

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
- exasol was the fastest overall with 674.6ms median runtime
- trino was 46.5x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 8 concurrent streams (randomized distribution)

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS225AA0249BAE51DBD with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS225AA0249BAE51DBD

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS225AA0249BAE51DBD to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS225AA0249BAE51DBD /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS34B997F7AFDC83679 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS34B997F7AFDC83679

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS34B997F7AFDC83679 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS34B997F7AFDC83679 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22B9D40DC76BC553A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22B9D40DC76BC553A

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22B9D40DC76BC553A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22B9D40DC76BC553A /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `96g`
- Max threads: `16`
- Max memory usage: `12.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23BBA2997EFB6D3C6 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23BBA2997EFB6D3C6

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23BBA2997EFB6D3C6 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23BBA2997EFB6D3C6 /data

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
- **Execution mode:** Multiuser (8 concurrent streams)
- **Query distribution:** Randomized (seed: 42)
### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip extscal_streams_8-benchmark.zip
cd extscal_streams_8

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
| Clickhouse | 417.34s | 0.12s | 218.84s | 845.23s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 422.47s | 0.11s | 325.37s | 903.15s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 67.88s | 0.33s | 0.00s | 101.18s | N/A | N/A | N/A |
| Duckdb | 425.01s | 0.02s | 130.72s | 568.90s | 412.9 MB | N/A | N/A |
| Exasol | 177.56s | 1.96s | 249.97s | 507.67s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 101.18s
- Starrocks took 903.15s (8.9x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2312.5 |      5 |     12854.8 |   12757.6 |   5139.5 |   4689.2 |  18550.6 |
| Q01     | duckdb     |   1142.7 |      5 |      5433.3 |    5616.3 |   2593.8 |   3028.5 |   8691   |
| Q01     | exasol     |    803   |      5 |      4903.7 |    4646.7 |   1119.3 |   2865.5 |   5785   |
| Q01     | starrocks  |   3625   |      5 |     19834.7 |   28328.6 |  23907.6 |   3077.2 |  66201.6 |
| Q01     | trino      |   5485.9 |      5 |     41416.8 |   36245.2 |  15829.2 |  16895.1 |  51218.2 |
| Q02     | clickhouse |    977.3 |      5 |      9563.8 |    9526.4 |   2313.7 |   5984.3 |  12436.5 |
| Q02     | duckdb     |    268.4 |      5 |      6362.7 |    5720.4 |   2078   |   2094.1 |   7284.3 |
| Q02     | exasol     |     63.8 |      5 |       199   |     190.9 |     51.2 |    108.8 |    249.9 |
| Q02     | starrocks  |    346.5 |      5 |      1158.3 |    1793.5 |   1468.5 |    717.4 |   4363.7 |
| Q02     | trino      |   3480.5 |      5 |      7381.6 |    9962.8 |   7890.1 |   4169.4 |  23695.8 |
| Q03     | clickhouse |   2118.1 |      5 |     12680.8 |   14807.4 |   3314.6 |  12183.1 |  18851.6 |
| Q03     | duckdb     |    711.8 |      5 |      4469.4 |    5350.7 |   2443.1 |   3487.8 |   9589.4 |
| Q03     | exasol     |    290.6 |      5 |      1282.2 |    1305.5 |    631.2 |    563.5 |   1941.2 |
| Q03     | starrocks  |    760.3 |      5 |      2944.3 |    2619   |    691.1 |   1873.9 |   3394.1 |
| Q03     | trino      |   9254.3 |      5 |     47363.1 |   38986.2 |  17881.1 |  12014.4 |  57123.6 |
| Q04     | clickhouse |   6873.2 |      5 |     23905.9 |   22321.8 |   4378.9 |  16731.6 |  27583.5 |
| Q04     | duckdb     |    685.5 |      5 |      7470.5 |    7198.8 |   2355.1 |   4449.9 |  10508.3 |
| Q04     | exasol     |     60.7 |      5 |       382.7 |     360.4 |     77.9 |    225.2 |    412.9 |
| Q04     | starrocks  |    669.8 |      5 |      4230.2 |    4660.2 |   1662.5 |   2533.6 |   6923.3 |
| Q04     | trino      |   5358.1 |      5 |     33118.4 |   29845.7 |   9122.9 |  13652.1 |  35059.2 |
| Q05     | clickhouse |   1740.9 |      5 |     17068.3 |   17992.5 |   3441.9 |  15317.6 |  24010.9 |
| Q05     | duckdb     |    764.7 |      5 |      6657.8 |    7199.3 |    936.4 |   6421.6 |   8498.5 |
| Q05     | exasol     |    259.1 |      5 |      1476.7 |    1375.5 |    213.2 |   1060   |   1576.9 |
| Q05     | starrocks  |    725.4 |      5 |      3626.5 |    3579.7 |    972.4 |   2440.3 |   4779.5 |
| Q05     | trino      |   6116.5 |      5 |     58078.6 |   58537.6 |   6374.5 |  49984.7 |  65429.3 |
| Q06     | clickhouse |    157.5 |      5 |      2707.1 |    2608   |    766.9 |   1382.4 |   3496.6 |
| Q06     | duckdb     |    204.4 |      5 |      7265.3 |    6812.7 |   1438.3 |   4297.9 |   7968   |
| Q06     | exasol     |     39.6 |      5 |       230.3 |     212.4 |     90.3 |     70.8 |    313.9 |
| Q06     | starrocks  |     98.6 |      5 |      1213.1 |    1486.5 |   1451.4 |     84.1 |   3935.3 |
| Q06     | trino      |   2430.6 |      5 |     10631.2 |   13484.6 |   7594.5 |   6652.6 |  22223   |
| Q07     | clickhouse |   7239.9 |      5 |     32059.3 |   29183.8 |  12485.3 |   7372.2 |  38244.7 |
| Q07     | duckdb     |    684.6 |      5 |      4456   |    4308.7 |   2373.1 |    681.8 |   7319.4 |
| Q07     | exasol     |    246.5 |      5 |      1718   |    1373.1 |    716.4 |    263.8 |   1994.9 |
| Q07     | starrocks  |    896.7 |      5 |      3813.7 |    4024.7 |    987.6 |   3132   |   5708.1 |
| Q07     | trino      |   5659.5 |      5 |     37136.3 |   31792.4 |  15344.3 |   5203.4 |  43602.7 |
| Q08     | clickhouse |   2319   |      5 |     19867.1 |   19102.2 |   1712.1 |  16448.7 |  20495.4 |
| Q08     | duckdb     |    736.2 |      5 |      6035.6 |    7610.7 |   3846.3 |   3838.3 |  13598.7 |
| Q08     | exasol     |     71.4 |      5 |       489.8 |     471.7 |     72.1 |    381.1 |    560.6 |
| Q08     | starrocks  |    734.3 |      5 |      2717.7 |    3071.9 |    979.9 |   1965.6 |   4107   |
| Q08     | trino      |   5599   |      5 |     42486   |   41356.8 |  15729.5 |  15678   |  57314.6 |
| Q09     | clickhouse |   1695.6 |      5 |     14697.2 |   15852.3 |   2714.8 |  13661.3 |  20426.4 |
| Q09     | duckdb     |   2327.6 |      5 |      9094.7 |    9436.7 |   1754.6 |   7591.4 |  11920.1 |
| Q09     | exasol     |    921.5 |      5 |      7246.5 |    6613.6 |   1511.2 |   3982.7 |   7762.5 |
| Q09     | starrocks  |   3015.6 |      5 |      6361.4 |    7499   |   2300.5 |   5618.8 |  11258.1 |
| Q09     | trino      |  20781   |      5 |    126424   |  122184   |  18712.8 |  89740.4 | 136578   |
| Q10     | clickhouse |   4362.1 |      5 |     26503   |   28316.2 |   4739.8 |  25183.8 |  36547   |
| Q10     | duckdb     |   1151.8 |      5 |      8039.9 |    7406.2 |   1559.3 |   5161.1 |   8938   |
| Q10     | exasol     |    410   |      5 |      1786.9 |    1601.8 |    772.4 |    669   |   2331   |
| Q10     | starrocks  |   1066.3 |      5 |      3438.4 |    3663   |   1020.4 |   2542.8 |   5293.3 |
| Q10     | trino      |   5518   |      5 |     64866.4 |   55364.2 |  16966.1 |  33615.8 |  70176.4 |
| Q11     | clickhouse |    582.9 |      5 |      7720.9 |    7761.7 |   1234.2 |   6453.4 |   9667.2 |
| Q11     | duckdb     |    111.1 |      5 |      5107.6 |    5552.4 |   1848.5 |   3147.1 |   7642.3 |
| Q11     | exasol     |    103.8 |      5 |       412.6 |     406.1 |     53.8 |    315.3 |    447.8 |
| Q11     | starrocks  |    167.6 |      5 |       792.3 |     715.8 |    233.5 |    378.4 |    927.5 |
| Q11     | trino      |   1230   |      5 |      2647.5 |    4638.5 |   3919   |   1319.3 |  11066.1 |
| Q12     | clickhouse |   1821.4 |      5 |      8062.7 |    8338.8 |   1621.9 |   6529.7 |  10910.1 |
| Q12     | duckdb     |    757.2 |      5 |      8293.7 |    7937.3 |   1266.3 |   5765   |   8902.2 |
| Q12     | exasol     |     80.2 |      5 |       581   |     576.2 |     28.4 |    531.8 |    607.4 |
| Q12     | starrocks  |    307.2 |      5 |      2320.9 |    2782.9 |   1517.4 |   1020.7 |   4515   |
| Q12     | trino      |   4672.1 |      5 |     23880.3 |   24534.8 |   6337.3 |  18850.2 |  34104.5 |
| Q13     | clickhouse |   3363.2 |      5 |     11635   |   11963.4 |   2846.5 |   9056.5 |  16667.8 |
| Q13     | duckdb     |   1885.8 |      5 |      7287.8 |    6654.9 |   3153.5 |   1866.2 |  10060   |
| Q13     | exasol     |    625.3 |      5 |      4281.1 |    3532   |   1501.8 |    917.5 |   4487.8 |
| Q13     | starrocks  |   1677.6 |      5 |     10935   |   10572.4 |   4574.3 |   4047.4 |  14919.1 |
| Q13     | trino      |   8366.1 |      5 |     78944.8 |   62154.2 |  40827.5 |   9890.6 | 108433   |
| Q14     | clickhouse |    216.3 |      5 |      5053.2 |    5180.8 |   1186   |   3480.7 |   6579.2 |
| Q14     | duckdb     |    549.3 |      5 |      5004.2 |    6422.1 |   2165.9 |   4646.5 |   8797.9 |
| Q14     | exasol     |     73.3 |      5 |       582.4 |     584.7 |     14.3 |    567.8 |    607.1 |
| Q14     | starrocks  |    158   |      5 |      1915.5 |    2329.3 |   1952.1 |    957   |   5722.5 |
| Q14     | trino      |   3370.6 |      5 |     31475.4 |   31281   |   3239.4 |  26098.9 |  34947.4 |
| Q15     | clickhouse |    241   |      5 |      5065.6 |    4706.2 |   1656.9 |   2420.5 |   6937.5 |
| Q15     | duckdb     |    471.9 |      5 |      7711.4 |    8465.2 |   2076   |   7312.8 |  12162.6 |
| Q15     | exasol     |    267.6 |      5 |      1341.2 |    1320.8 |     46.6 |   1249.5 |   1361.8 |
| Q15     | starrocks  |    135.5 |      5 |      1431.2 |    2329.9 |   1827.3 |    785.9 |   5273.7 |
| Q15     | trino      |   5985.5 |      5 |     31468.8 |   31546.5 |   1509   |  30015.2 |  33948.1 |
| Q16     | clickhouse |    557.1 |      5 |      7507.5 |    8697.6 |   3385.5 |   5950   |  14601.8 |
| Q16     | duckdb     |    385.5 |      5 |      6952.2 |    6525.2 |   1157.1 |   4497.2 |   7315.7 |
| Q16     | exasol     |    397.7 |      5 |      1903.2 |    1928.4 |    121.7 |   1789.7 |   2095.4 |
| Q16     | starrocks  |    580.1 |      5 |      1414.2 |    1888.9 |    809   |   1366.3 |   3255.8 |
| Q16     | trino      |   2307.2 |      5 |      8373.8 |    8638.8 |    983.9 |   7425.1 |   9889.2 |
| Q17     | clickhouse |    963.6 |      5 |      7837.4 |    8224.1 |   1990.1 |   5575.9 |  10493.8 |
| Q17     | duckdb     |    833.4 |      5 |      6719.3 |    6200.1 |   2061.6 |   3596.1 |   8233.6 |
| Q17     | exasol     |     21.6 |      5 |        69.2 |      80.2 |     26.3 |     56.5 |    114.9 |
| Q17     | starrocks  |    515.3 |      5 |      2185.6 |    2206.5 |   1560.9 |    708.1 |   4477.1 |
| Q17     | trino      |   7639.8 |      5 |     45500.5 |   41583   |  10860.3 |  27318.6 |  51736.7 |
| Q18     | clickhouse |   1932.6 |      5 |     17413.1 |   17247.5 |   5468.2 |   9054   |  24405.5 |
| Q18     | duckdb     |   1580.7 |      5 |      8426.7 |    8189.5 |   2104   |   4835.8 |  10594.7 |
| Q18     | exasol     |    527.8 |      5 |      3510.4 |    3017.4 |   1164.3 |    946.1 |   3697.3 |
| Q18     | starrocks  |   4503.5 |      5 |     22150.1 |   20437   |   6177.9 |  12728.9 |  27198.4 |
| Q18     | trino      |   7738.2 |      5 |     35577.5 |   35164.3 |  10616.6 |  20476.2 |  46723.4 |
| Q19     | clickhouse |   4945.1 |      5 |     29604   |   27988.2 |   6359.2 |  18138.2 |  34872.8 |
| Q19     | duckdb     |    781.9 |      5 |      9247.4 |   10510.8 |   5797.3 |   4248.5 |  19485.1 |
| Q19     | exasol     |     26.2 |      5 |       169.6 |     149.5 |     42.4 |     90   |    189.8 |
| Q19     | starrocks  |    559   |      5 |       895.9 |    1798.1 |   2222.7 |    534.2 |   5755.1 |
| Q19     | trino      |   4032.1 |      5 |     10751.5 |   13706.1 |   8456.6 |   4533.1 |  26431   |
| Q20     | clickhouse |   1885.6 |      5 |     10371.3 |   11569.1 |   2832.4 |   9949   |  16609.3 |
| Q20     | duckdb     |    720.1 |      5 |      7209.6 |    7015.7 |   3941.8 |    727.3 |  11492.8 |
| Q20     | exasol     |    210.2 |      5 |       680.3 |     721.2 |    386.6 |    337.1 |   1139.4 |
| Q20     | starrocks  |    273.8 |      5 |       890.4 |    1089.3 |    706.2 |    305.8 |   2150   |
| Q20     | trino      |   4166.1 |      5 |     28904.8 |   22487.2 |   9927.7 |   7406.8 |  29709.8 |
| Q21     | clickhouse |   2327.5 |      5 |     15325.5 |   15414.8 |   7108.5 |   6793.9 |  25488.7 |
| Q21     | duckdb     |   3676.9 |      5 |      8024.5 |    9239.4 |   2595.3 |   6974.5 |  12332.1 |
| Q21     | exasol     |    371.7 |      5 |      2714.4 |    1911.2 |   1189.3 |    599.5 |   2816.2 |
| Q21     | starrocks  |   6145.6 |      5 |     22791   |   18902.8 |   8549.4 |   7926.7 |  26817   |
| Q21     | trino      |  17928.5 |      5 |     87375.6 |   75386.8 |  26522.8 |  38756.3 | 102453   |
| Q22     | clickhouse |    545.1 |      5 |      7020.8 |    7694.6 |   3368.8 |   3212.3 |  11616   |
| Q22     | duckdb     |    411.4 |      5 |      8652   |    7721.1 |   2283.6 |   3963.4 |   9853.6 |
| Q22     | exasol     |     94.4 |      5 |       603.4 |     580.6 |    119.9 |    427.9 |    696.1 |
| Q22     | starrocks  |    339.2 |      5 |      2983.8 |    3581   |   1839.2 |   1872   |   6547.2 |
| Q22     | trino      |   2642.4 |      5 |      7668.8 |    7785.3 |    697.9 |   7042.3 |   8566.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        4903.7 |          5433.3 |    1.11 |      0.9  | False    |
| Q02     | exasol            | duckdb              |         199   |          6362.7 |   31.97 |      0.03 | False    |
| Q03     | exasol            | duckdb              |        1282.2 |          4469.4 |    3.49 |      0.29 | False    |
| Q04     | exasol            | duckdb              |         382.7 |          7470.5 |   19.52 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1476.7 |          6657.8 |    4.51 |      0.22 | False    |
| Q06     | exasol            | duckdb              |         230.3 |          7265.3 |   31.55 |      0.03 | False    |
| Q07     | exasol            | duckdb              |        1718   |          4456   |    2.59 |      0.39 | False    |
| Q08     | exasol            | duckdb              |         489.8 |          6035.6 |   12.32 |      0.08 | False    |
| Q09     | exasol            | duckdb              |        7246.5 |          9094.7 |    1.26 |      0.8  | False    |
| Q10     | exasol            | duckdb              |        1786.9 |          8039.9 |    4.5  |      0.22 | False    |
| Q11     | exasol            | duckdb              |         412.6 |          5107.6 |   12.38 |      0.08 | False    |
| Q12     | exasol            | duckdb              |         581   |          8293.7 |   14.27 |      0.07 | False    |
| Q13     | exasol            | duckdb              |        4281.1 |          7287.8 |    1.7  |      0.59 | False    |
| Q14     | exasol            | duckdb              |         582.4 |          5004.2 |    8.59 |      0.12 | False    |
| Q15     | exasol            | duckdb              |        1341.2 |          7711.4 |    5.75 |      0.17 | False    |
| Q16     | exasol            | duckdb              |        1903.2 |          6952.2 |    3.65 |      0.27 | False    |
| Q17     | exasol            | duckdb              |          69.2 |          6719.3 |   97.1  |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3510.4 |          8426.7 |    2.4  |      0.42 | False    |
| Q19     | exasol            | duckdb              |         169.6 |          9247.4 |   54.52 |      0.02 | False    |
| Q20     | exasol            | duckdb              |         680.3 |          7209.6 |   10.6  |      0.09 | False    |
| Q21     | exasol            | duckdb              |        2714.4 |          8024.5 |    2.96 |      0.34 | False    |
| Q22     | exasol            | duckdb              |         603.4 |          8652   |   14.34 |      0.07 | False    |
| Q01     | exasol            | starrocks           |        4903.7 |         19834.7 |    4.04 |      0.25 | False    |
| Q02     | exasol            | starrocks           |         199   |          1158.3 |    5.82 |      0.17 | False    |
| Q03     | exasol            | starrocks           |        1282.2 |          2944.3 |    2.3  |      0.44 | False    |
| Q04     | exasol            | starrocks           |         382.7 |          4230.2 |   11.05 |      0.09 | False    |
| Q05     | exasol            | starrocks           |        1476.7 |          3626.5 |    2.46 |      0.41 | False    |
| Q06     | exasol            | starrocks           |         230.3 |          1213.1 |    5.27 |      0.19 | False    |
| Q07     | exasol            | starrocks           |        1718   |          3813.7 |    2.22 |      0.45 | False    |
| Q08     | exasol            | starrocks           |         489.8 |          2717.7 |    5.55 |      0.18 | False    |
| Q09     | exasol            | starrocks           |        7246.5 |          6361.4 |    0.88 |      1.14 | True     |
| Q10     | exasol            | starrocks           |        1786.9 |          3438.4 |    1.92 |      0.52 | False    |
| Q11     | exasol            | starrocks           |         412.6 |           792.3 |    1.92 |      0.52 | False    |
| Q12     | exasol            | starrocks           |         581   |          2320.9 |    3.99 |      0.25 | False    |
| Q13     | exasol            | starrocks           |        4281.1 |         10935   |    2.55 |      0.39 | False    |
| Q14     | exasol            | starrocks           |         582.4 |          1915.5 |    3.29 |      0.3  | False    |
| Q15     | exasol            | starrocks           |        1341.2 |          1431.2 |    1.07 |      0.94 | False    |
| Q16     | exasol            | starrocks           |        1903.2 |          1414.2 |    0.74 |      1.35 | True     |
| Q17     | exasol            | starrocks           |          69.2 |          2185.6 |   31.58 |      0.03 | False    |
| Q18     | exasol            | starrocks           |        3510.4 |         22150.1 |    6.31 |      0.16 | False    |
| Q19     | exasol            | starrocks           |         169.6 |           895.9 |    5.28 |      0.19 | False    |
| Q20     | exasol            | starrocks           |         680.3 |           890.4 |    1.31 |      0.76 | False    |
| Q21     | exasol            | starrocks           |        2714.4 |         22791   |    8.4  |      0.12 | False    |
| Q22     | exasol            | starrocks           |         603.4 |          2983.8 |    4.94 |      0.2  | False    |
| Q01     | exasol            | clickhouse          |        4903.7 |         12854.8 |    2.62 |      0.38 | False    |
| Q02     | exasol            | clickhouse          |         199   |          9563.8 |   48.06 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |        1282.2 |         12680.8 |    9.89 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |         382.7 |         23905.9 |   62.47 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1476.7 |         17068.3 |   11.56 |      0.09 | False    |
| Q06     | exasol            | clickhouse          |         230.3 |          2707.1 |   11.75 |      0.09 | False    |
| Q07     | exasol            | clickhouse          |        1718   |         32059.3 |   18.66 |      0.05 | False    |
| Q08     | exasol            | clickhouse          |         489.8 |         19867.1 |   40.56 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        7246.5 |         14697.2 |    2.03 |      0.49 | False    |
| Q10     | exasol            | clickhouse          |        1786.9 |         26503   |   14.83 |      0.07 | False    |
| Q11     | exasol            | clickhouse          |         412.6 |          7720.9 |   18.71 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |         581   |          8062.7 |   13.88 |      0.07 | False    |
| Q13     | exasol            | clickhouse          |        4281.1 |         11635   |    2.72 |      0.37 | False    |
| Q14     | exasol            | clickhouse          |         582.4 |          5053.2 |    8.68 |      0.12 | False    |
| Q15     | exasol            | clickhouse          |        1341.2 |          5065.6 |    3.78 |      0.26 | False    |
| Q16     | exasol            | clickhouse          |        1903.2 |          7507.5 |    3.94 |      0.25 | False    |
| Q17     | exasol            | clickhouse          |          69.2 |          7837.4 |  113.26 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3510.4 |         17413.1 |    4.96 |      0.2  | False    |
| Q19     | exasol            | clickhouse          |         169.6 |         29604   |  174.55 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         680.3 |         10371.3 |   15.25 |      0.07 | False    |
| Q21     | exasol            | clickhouse          |        2714.4 |         15325.5 |    5.65 |      0.18 | False    |
| Q22     | exasol            | clickhouse          |         603.4 |          7020.8 |   11.64 |      0.09 | False    |
| Q01     | exasol            | trino               |        4903.7 |         41416.8 |    8.45 |      0.12 | False    |
| Q02     | exasol            | trino               |         199   |          7381.6 |   37.09 |      0.03 | False    |
| Q03     | exasol            | trino               |        1282.2 |         47363.1 |   36.94 |      0.03 | False    |
| Q04     | exasol            | trino               |         382.7 |         33118.4 |   86.54 |      0.01 | False    |
| Q05     | exasol            | trino               |        1476.7 |         58078.6 |   39.33 |      0.03 | False    |
| Q06     | exasol            | trino               |         230.3 |         10631.2 |   46.16 |      0.02 | False    |
| Q07     | exasol            | trino               |        1718   |         37136.3 |   21.62 |      0.05 | False    |
| Q08     | exasol            | trino               |         489.8 |         42486   |   86.74 |      0.01 | False    |
| Q09     | exasol            | trino               |        7246.5 |        126424   |   17.45 |      0.06 | False    |
| Q10     | exasol            | trino               |        1786.9 |         64866.4 |   36.3  |      0.03 | False    |
| Q11     | exasol            | trino               |         412.6 |          2647.5 |    6.42 |      0.16 | False    |
| Q12     | exasol            | trino               |         581   |         23880.3 |   41.1  |      0.02 | False    |
| Q13     | exasol            | trino               |        4281.1 |         78944.8 |   18.44 |      0.05 | False    |
| Q14     | exasol            | trino               |         582.4 |         31475.4 |   54.04 |      0.02 | False    |
| Q15     | exasol            | trino               |        1341.2 |         31468.8 |   23.46 |      0.04 | False    |
| Q16     | exasol            | trino               |        1903.2 |          8373.8 |    4.4  |      0.23 | False    |
| Q17     | exasol            | trino               |          69.2 |         45500.5 |  657.52 |      0    | False    |
| Q18     | exasol            | trino               |        3510.4 |         35577.5 |   10.13 |      0.1  | False    |
| Q19     | exasol            | trino               |         169.6 |         10751.5 |   63.39 |      0.02 | False    |
| Q20     | exasol            | trino               |         680.3 |         28904.8 |   42.49 |      0.02 | False    |
| Q21     | exasol            | trino               |        2714.4 |         87375.6 |   32.19 |      0.03 | False    |
| Q22     | exasol            | trino               |         603.4 |          7668.8 |   12.71 |      0.08 | False    |

### Per-Stream Statistics

This benchmark was executed using **8 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 15040.3 | 13470.1 | 6793.9 | 38244.7 |
| 1 | 14 | 11401.7 | 10324.5 | 2833.8 | 20426.4 |
| 2 | 14 | 14435.2 | 12416.0 | 1382.4 | 36547.0 |
| 3 | 14 | 13879.7 | 10124.8 | 2420.5 | 34872.8 |
| 4 | 14 | 14536.3 | 14003.1 | 2620.0 | 32041.2 |
| 5 | 14 | 14586.5 | 10945.6 | 3212.3 | 32059.3 |
| 6 | 13 | 14577.2 | 14324.5 | 3480.7 | 31291.5 |
| 7 | 13 | 13265.8 | 10398.8 | 2707.1 | 36201.6 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 10124.8ms
- Slowest stream median: 14324.5ms
- Stream performance variation: 41.5% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 6675.2 | 7301.8 | 681.8 | 11745.6 |
| 1 | 14 | 7231.6 | 7269.6 | 2094.1 | 13598.7 |
| 2 | 14 | 6782.0 | 7082.2 | 727.3 | 11920.1 |
| 3 | 14 | 7297.2 | 7297.6 | 3147.1 | 19485.1 |
| 4 | 14 | 7119.1 | 7295.2 | 4082.1 | 12332.1 |
| 5 | 14 | 7180.5 | 7298.6 | 3963.4 | 12162.6 |
| 6 | 13 | 7433.4 | 7333.5 | 4449.9 | 12239.6 |
| 7 | 13 | 7449.1 | 7591.4 | 4297.9 | 10508.3 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 7082.2ms
- Slowest stream median: 7591.4ms
- Stream performance variation: 7.2% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 1795.1 | 1423.5 | 263.8 | 4372.2 |
| 1 | 14 | 1193.6 | 525.2 | 59.3 | 7294.9 |
| 2 | 14 | 1762.8 | 795.4 | 70.8 | 6781.5 |
| 3 | 14 | 1497.9 | 835.6 | 56.5 | 5288.3 |
| 4 | 14 | 1530.6 | 1311.7 | 177.6 | 4390.9 |
| 5 | 14 | 1302.7 | 545.4 | 101.1 | 4903.7 |
| 6 | 13 | 1591.0 | 586.1 | 120.4 | 7762.5 |
| 7 | 13 | 1304.5 | 569.8 | 114.9 | 7246.5 |

**Performance Analysis for Exasol:**
- Fastest stream median: 525.2ms
- Slowest stream median: 1423.5ms
- Stream performance variation: 171.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 6597.1 | 3854.5 | 1414.2 | 15347.1 |
| 1 | 14 | 4604.0 | 2706.7 | 888.4 | 24760.5 |
| 2 | 14 | 7288.4 | 2838.4 | 84.1 | 66201.6 |
| 3 | 14 | 7166.7 | 2613.6 | 578.7 | 34438.8 |
| 4 | 14 | 6643.5 | 2221.5 | 792.3 | 25337.9 |
| 5 | 14 | 5818.6 | 4072.3 | 708.1 | 22150.1 |
| 6 | 13 | 5426.9 | 2533.6 | 378.4 | 27198.4 |
| 7 | 13 | 3276.3 | 2983.8 | 717.4 | 8111.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2221.5ms
- Slowest stream median: 4072.3ms
- Stream performance variation: 83.3% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 14 | 39804.4 | 31480.4 | 5203.4 | 108432.7 |
| 1 | 14 | 35888.1 | 26708.8 | 2577.5 | 125373.9 |
| 2 | 14 | 39479.1 | 29307.3 | 4533.1 | 126424.5 |
| 3 | 14 | 34144.9 | 32814.1 | 5582.0 | 91390.2 |
| 4 | 14 | 36383.6 | 31111.2 | 2647.5 | 102453.4 |
| 5 | 14 | 31742.2 | 32740.6 | 5575.2 | 70176.4 |
| 6 | 13 | 40947.8 | 34104.5 | 1319.3 | 136578.2 |
| 7 | 13 | 31293.7 | 23880.3 | 4169.4 | 132802.0 |

**Performance Analysis for Trino:**
- Fastest stream median: 23880.3ms
- Slowest stream median: 34104.5ms
- Stream performance variation: 42.8% difference between fastest and slowest streams
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
- Median runtime: 674.6ms
- Average runtime: 1498.2ms
- Fastest query: 56.5ms
- Slowest query: 7762.5ms

**duckdb:**
- Median runtime: 7286.1ms
- Average runtime: 7140.6ms
- Fastest query: 681.8ms
- Slowest query: 19485.1ms

**starrocks:**
- Median runtime: 3030.5ms
- Average runtime: 5880.0ms
- Fastest query: 84.1ms
- Slowest query: 66201.6ms

**clickhouse:**
- Median runtime: 11715.1ms
- Average runtime: 13966.1ms
- Fastest query: 1382.4ms
- Slowest query: 38244.7ms

**trino:**
- Median runtime: 31395.7ms
- Average runtime: 36212.1ms
- Fastest query: 1319.3ms
- Slowest query: 136578.2ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_8-benchmark.zip`](extscal_streams_8-benchmark.zip)

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
  - memory_limit: 96g
  - max_threads: 16
  - max_memory_usage: 12000000000
  - max_bytes_before_external_group_by: 4000000000
  - max_bytes_before_external_sort: 4000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 8000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 71GB
  - query_max_memory_per_node: 71GB

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
- Measured runs executed across 8 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts