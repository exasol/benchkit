# Streamlined Scalability - Scale Factor 100 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-10 10:44:45

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
- exasol was the fastest overall with 801.9ms median runtime
- trino was 29.8x slower- Tested 550 total query executions across 22 different TPC-H queries
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

# Create 132GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Create raw partition for Exasol (752GB)
sudo parted -s /dev/nvme1n1 mkpart primary 132GiB 100%

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43FA4A651E71CF37A with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43FA4A651E71CF37A

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43FA4A651E71CF37A to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43FA4A651E71CF37A /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23DC35E40AC69FA72 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23DC35E40AC69FA72

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23DC35E40AC69FA72 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS23DC35E40AC69FA72 /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43AF96AE1B9800E1C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43AF96AE1B9800E1C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43AF96AE1B9800E1C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43AF96AE1B9800E1C /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `96g`
- Max threads: `16`
- Max memory usage: `30.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64107C52D697A1041 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64107C52D697A1041

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64107C52D697A1041 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64107C52D697A1041 /data

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
- **Scale factor:** 100
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
unzip extscal_sf_100-benchmark.zip
cd extscal_sf_100

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
| Clickhouse | 868.88s | 0.13s | 444.81s | 1723.13s | 89.2 GB | 39.9 GB | 2.2x |
| Starrocks | 872.08s | 0.12s | 649.52s | 1828.73s | 30.1 GB | 30.1 GB | 1.0x |
| Trino | 146.81s | 0.33s | 0.00s | 205.23s | N/A | N/A | N/A |
| Duckdb | 869.41s | 0.04s | 219.42s | 1115.06s | 825.9 MB | N/A | N/A |
| Exasol | 261.52s | 1.97s | 507.70s | 931.01s | 95.7 GB | 23.0 GB | 4.2x |

**Key Observations:**
- Trino had the fastest preparation time at 205.23s
- Starrocks took 1828.73s (8.9x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4697.2 |      5 |     11512.8 |   13181.5 |   5605.8 |   7048.7 |  19695.7 |
| Q01     | duckdb     |   2251.6 |      5 |      5331.5 |    6906.7 |   3325.9 |   4851.2 |  12769.7 |
| Q01     | exasol     |   1585   |      5 |      5234.7 |    4656   |   1238   |   2562.3 |   5616.3 |
| Q01     | starrocks  |   7001   |      5 |     28056.2 |   29310.8 |  15588.6 |   7948.1 |  44710.4 |
| Q01     | trino      |  10074.5 |      5 |     14883.7 |   28637.6 |  22811.1 |  12091   |  63975.7 |
| Q02     | clickhouse |   2109.7 |      5 |     10202.3 |    8955.3 |   3352.5 |   5202.2 |  12501.8 |
| Q02     | duckdb     |    488.5 |      5 |      7153.6 |    6341.9 |   2253   |   3412.3 |   8424.8 |
| Q02     | exasol     |    101.6 |      5 |       196.7 |     202.9 |     28.2 |    163.4 |    230.8 |
| Q02     | starrocks  |    448.5 |      5 |      1106.1 |    1127.8 |    158.3 |    907.4 |   1311.1 |
| Q02     | trino      |   5561.2 |      5 |     17123.5 |   14409.1 |   6518.1 |   7306.8 |  22343.5 |
| Q03     | clickhouse |   7478.9 |      5 |     20084.9 |   18903   |   8600.2 |   7276.5 |  27277.3 |
| Q03     | duckdb     |   1507.1 |      5 |      6086.5 |    7268.4 |   3867.7 |   2970.3 |  11344   |
| Q03     | exasol     |    602   |      5 |       644.7 |    1276   |    898.7 |    609.5 |   2373.3 |
| Q03     | starrocks  |   3298.6 |      5 |      3371.9 |    5521.4 |   4405.2 |   2805.8 |  13167.6 |
| Q03     | trino      |  18688   |      5 |     31808.2 |   34689.4 |  17529.6 |  16775.5 |  54345   |
| Q04     | clickhouse |  15118.5 |      5 |     33085   |   34025.2 |   4041.8 |  29947.3 |  39457.3 |
| Q04     | duckdb     |   1442.9 |      5 |      7071.5 |    6976.5 |   1840.3 |   4534.9 |   9499.9 |
| Q04     | exasol     |    114.7 |      5 |       374.4 |     359.6 |    123.2 |    173.8 |    505.7 |
| Q04     | starrocks  |   1305.6 |      5 |      3902.6 |    4147.5 |   2158.3 |   1773.1 |   6665.2 |
| Q04     | trino      |  10031.4 |      5 |     22648.2 |   29058.7 |  21696.3 |  15199.4 |  67295.3 |
| Q05     | clickhouse |   5584.3 |      5 |     27285.6 |   26462.1 |   2225   |  22709.1 |  28320.7 |
| Q05     | duckdb     |   1674.7 |      5 |      5952.5 |    7940   |   4264.6 |   4062.6 |  14840.9 |
| Q05     | exasol     |    473   |      5 |      1529.3 |    1446.6 |    227.4 |   1044.9 |   1607.5 |
| Q05     | starrocks  |   3299.9 |      5 |     12114.5 |   11276.3 |   5160.4 |   5460.7 |  17554.9 |
| Q05     | trino      |  20224.1 |      5 |     71235.5 |   65004.3 |  25928.2 |  34803.9 | 100919   |
| Q06     | clickhouse |    285.1 |      5 |      3244   |    4041.6 |   2567.1 |   1547   |   7338.2 |
| Q06     | duckdb     |    407   |      5 |      7121   |    6959.4 |   3879.9 |   3005.3 |  10944.1 |
| Q06     | exasol     |     75.1 |      5 |       263.2 |     269.9 |    180.6 |    105.7 |    564.9 |
| Q06     | starrocks  |    171.1 |      5 |       818.1 |     748.3 |    473.4 |    221.5 |   1342.9 |
| Q06     | trino      |   4789.5 |      5 |     16771.6 |   19525.1 |  13158.2 |   6733.5 |  40504.2 |
| Q07     | clickhouse |  15337.5 |      5 |     36870.7 |   40767.2 |  15026.1 |  23430.2 |  64654.6 |
| Q07     | duckdb     |   1440.5 |      5 |      6376.4 |    7011   |   1814.7 |   5343.1 |   9163.8 |
| Q07     | exasol     |    576.5 |      5 |      2135.4 |    1883.1 |    736.5 |    582.8 |   2369.9 |
| Q07     | starrocks  |   2807   |      5 |      8022.4 |    9065.1 |   5410.1 |   2627.6 |  16922.8 |
| Q07     | trino      |  10955.9 |      5 |     17238.7 |   25350   |  17322.7 |  16106.3 |  56205.5 |
| Q08     | clickhouse |   7330.2 |      5 |     29962.6 |   32475.3 |   6599.5 |  24391.9 |  39720.5 |
| Q08     | duckdb     |   1535.2 |      5 |      8869.5 |    8448.8 |   2902.4 |   5289.9 |  11376.4 |
| Q08     | exasol     |    136.9 |      5 |       503.2 |     462.2 |    121.7 |    257.1 |    578.1 |
| Q08     | starrocks  |   1898.1 |      5 |      4372.9 |    4153.7 |    899.4 |   3052.5 |   5407.6 |
| Q08     | trino      |  10554   |      5 |     32042.9 |   49314.7 |  34475.1 |  17970.8 |  86699.4 |
| Q09     | clickhouse |   4748.6 |      5 |     23591.6 |   21946.7 |   6814.1 |  12246.2 |  29236   |
| Q09     | duckdb     |   4488.2 |      5 |      7974.6 |    8153.4 |   2679.5 |   4510.7 |  11866.5 |
| Q09     | exasol     |   2000.1 |      5 |      7739.7 |    7504   |    627.7 |   6471.7 |   8054.7 |
| Q09     | starrocks  |   5823   |      5 |     14802.4 |   13622.6 |   2945.4 |   8399.1 |  15394.2 |
| Q09     | trino      |  44122.8 |      5 |    165238   |  179770   |  42548   | 143710   | 248543   |
| Q10     | clickhouse |   9090.2 |      5 |     27483.7 |   31185.7 |   5840.6 |  26245.9 |  38559.7 |
| Q10     | duckdb     |   2286.7 |      5 |      8640.7 |    8139   |   1868.8 |   5317.7 |   9745.2 |
| Q10     | exasol     |    802.1 |      5 |      2463.1 |    2065.4 |    616.9 |   1382.5 |   2553.2 |
| Q10     | starrocks  |   2444.8 |      5 |      4287.1 |    5684.1 |   2090.7 |   4020.7 |   8167.3 |
| Q10     | trino      |  11741   |      5 |     67564.6 |   52461.2 |  27652.2 |  15625.6 |  79241.3 |
| Q11     | clickhouse |   1274   |      5 |      3473.6 |    4729   |   2144.6 |   2633.7 |   7093.9 |
| Q11     | duckdb     |    218.8 |      5 |      6907.2 |    6839.9 |    734.9 |   5716.1 |   7584   |
| Q11     | exasol     |    180.3 |      5 |       450.6 |     439.8 |     95.3 |    287.4 |    537.5 |
| Q11     | starrocks  |    340.4 |      5 |       787.7 |     874   |    257.9 |    647.8 |   1253.3 |
| Q11     | trino      |   1975.9 |      5 |      5242.6 |    6095.3 |   3167.1 |   2779.5 |  10748.7 |
| Q12     | clickhouse |   3955.4 |      5 |      4861.2 |    5798.3 |   3443.6 |   3551.4 |  11810.3 |
| Q12     | duckdb     |   1607.8 |      5 |      5104.8 |    5767.8 |   1708.5 |   4263   |   7603.5 |
| Q12     | exasol     |    152.8 |      5 |       585   |     636.2 |     88.5 |    564.5 |    767.6 |
| Q12     | starrocks  |    563.9 |      5 |      2243.1 |    2027.2 |    769.1 |   1107.1 |   2937.4 |
| Q12     | trino      |   6037.9 |      5 |     22180.8 |   27203.7 |  12894.8 |  19333.9 |  49862.6 |
| Q13     | clickhouse |   6433.2 |      5 |     15941.3 |   16178.3 |   1948.9 |  14181.1 |  18564.7 |
| Q13     | duckdb     |   4019.6 |      5 |      7902.8 |    7949.6 |   2578.2 |   4069.5 |  11165.7 |
| Q13     | exasol     |   1297.6 |      5 |      4666.8 |    4232.7 |   1110.5 |   2265.8 |   4977.9 |
| Q13     | starrocks  |   3610.5 |      5 |     11480.9 |    9781.7 |   4334.5 |   3662   |  13690.2 |
| Q13     | trino      |  17298.2 |      5 |     51656.7 |   69677.3 |  32368.3 |  42263.3 | 118092   |
| Q14     | clickhouse |    339.1 |      5 |      3533.5 |    4807.7 |   3745   |    823.6 |   9545.6 |
| Q14     | duckdb     |   1128.7 |      5 |      6342.7 |    6949.2 |   4315.4 |   1180.5 |  11949   |
| Q14     | exasol     |    154.2 |      5 |       665.4 |     677.6 |    139.2 |    542.4 |    904.5 |
| Q14     | starrocks  |    313.1 |      5 |      1612.6 |    1515.3 |    695.9 |    775.5 |   2345.3 |
| Q14     | trino      |   6921.1 |      5 |     24031.9 |   25746.5 |  12602   |  14033.8 |  47026.7 |
| Q15     | clickhouse |    523.8 |      5 |      4100.6 |    5899   |   4678.9 |   2548.5 |  13790.4 |
| Q15     | duckdb     |    929   |      5 |      6628   |    6933.5 |   3025.5 |   3431.1 |  11768.5 |
| Q15     | exasol     |    532.1 |      5 |      1570.2 |    1548   |     61.7 |   1461.6 |   1622   |
| Q15     | starrocks  |    247.7 |      5 |       649.2 |    1213.2 |    989.6 |    484.5 |   2739.5 |
| Q15     | trino      |  11898.6 |      5 |     39550.9 |   36676.7 |  17549.7 |  18667.3 |  62008.6 |
| Q16     | clickhouse |   1033.8 |      5 |     12301.4 |   11599.9 |   3184.6 |   7790.9 |  15376   |
| Q16     | duckdb     |    757   |      5 |      8248.6 |    7791.8 |   3670.4 |   3647.2 |  11502.3 |
| Q16     | exasol     |    663.5 |      5 |      2014.8 |    2015.7 |    138.1 |   1884.5 |   2208.6 |
| Q16     | starrocks  |    797.8 |      5 |      1083.6 |    1102.7 |    160.7 |    953.1 |   1358.3 |
| Q16     | trino      |   3540.8 |      5 |      7939.9 |   11115.6 |   4981.5 |   7209.4 |  18290.2 |
| Q17     | clickhouse |   2329.5 |      5 |     10069.2 |   11063.1 |   4043.1 |   6981.2 |  17217.2 |
| Q17     | duckdb     |   1661.8 |      5 |      7581.1 |    7231.7 |   1494.4 |   5266.8 |   9147.8 |
| Q17     | exasol     |     33.7 |      5 |        71.3 |      72.1 |      4   |     68.1 |     76.4 |
| Q17     | starrocks  |   1095.1 |      5 |      3268.7 |    3386.1 |   1628.2 |   1399   |   5369.1 |
| Q17     | trino      |  14028.4 |      5 |     55038.1 |   51481.4 |  14638.4 |  27418.6 |  66548.6 |
| Q18     | clickhouse |   6778.2 |      5 |     24961.4 |   26928.9 |   5445.6 |  21679.7 |  35978.2 |
| Q18     | duckdb     |   3509.3 |      5 |      8098.3 |    9373.2 |   3225.2 |   5873   |  13798.1 |
| Q18     | exasol     |   1057.5 |      5 |      3565.2 |    3219.8 |    801.2 |   1809   |   3769.2 |
| Q18     | starrocks  |   9590.4 |      5 |     43613   |   37432.5 |  10982.4 |  24067.7 |  47622.8 |
| Q18     | trino      |  16570.8 |      5 |     48316.7 |   54297.1 |  19303.2 |  30541.3 |  81155.7 |
| Q19     | clickhouse |   9733   |      5 |     31884   |   30010.7 |   6582.2 |  20213.7 |  37365.2 |
| Q19     | duckdb     |   1631.7 |      5 |      4754.9 |    8197.1 |   6739.6 |   3868.1 |  19941.1 |
| Q19     | exasol     |     41.2 |      5 |        78.2 |      97.3 |     29.6 |     73.6 |    133.1 |
| Q19     | starrocks  |   1575.3 |      5 |      2247.2 |    3876   |   2636.3 |   1658.9 |   7607.5 |
| Q19     | trino      |   7981.7 |      5 |     12428.6 |   17719.1 |  13829.7 |   8808.9 |  42270.4 |
| Q20     | clickhouse |   3346.9 |      5 |     14642.5 |   13755.3 |   5378.6 |   6414.5 |  20319.9 |
| Q20     | duckdb     |   1466.3 |      5 |      7503.1 |    7727.3 |   3291   |   3809.3 |  11185.7 |
| Q20     | exasol     |    412.6 |      5 |       836.2 |     923   |    227.8 |    683.5 |   1178.6 |
| Q20     | starrocks  |    634.7 |      5 |      1313.7 |    1299.9 |    269.2 |   1046   |   1717.6 |
| Q20     | trino      |   7839.2 |      5 |     11800.4 |   13617   |   5257.4 |   8656.5 |  21161.9 |
| Q21     | clickhouse |   5601.3 |      5 |     18662.6 |   20070.3 |   5691.9 |  14475.3 |  29259   |
| Q21     | duckdb     |   7991.3 |      5 |     12328.4 |   12870.1 |   1694.8 |  10715.1 |  14629.4 |
| Q21     | exasol     |    817   |      5 |      2593.9 |    2234.8 |    808.1 |   1170.8 |   2970.7 |
| Q21     | starrocks  |  13382.7 |      5 |     32254.3 |   30408.5 |  10193.7 |  13359   |  40576   |
| Q21     | trino      |  44704.1 |      5 |    118064   |  127102   |  51886.2 |  71211.1 | 210836   |
| Q22     | clickhouse |    824.3 |      5 |      8866.9 |   11332.4 |   5664.1 |   6367.6 |  18534   |
| Q22     | duckdb     |    828.9 |      5 |      5442.9 |    6490.4 |   3484.8 |   3103.3 |  11798.8 |
| Q22     | exasol     |    182.4 |      5 |       642.5 |     572.2 |    172.2 |    266.4 |    667.3 |
| Q22     | starrocks  |    570.8 |      5 |      1439   |    1520.8 |    835.7 |    530.9 |   2826.5 |
| Q22     | trino      |   5107.3 |      5 |     15321   |   17925.7 |   7893.2 |  12321   |  31848   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | duckdb              |        5234.7 |          5331.5 |    1.02 |      0.98 | False    |
| Q02     | exasol            | duckdb              |         196.7 |          7153.6 |   36.37 |      0.03 | False    |
| Q03     | exasol            | duckdb              |         644.7 |          6086.5 |    9.44 |      0.11 | False    |
| Q04     | exasol            | duckdb              |         374.4 |          7071.5 |   18.89 |      0.05 | False    |
| Q05     | exasol            | duckdb              |        1529.3 |          5952.5 |    3.89 |      0.26 | False    |
| Q06     | exasol            | duckdb              |         263.2 |          7121   |   27.06 |      0.04 | False    |
| Q07     | exasol            | duckdb              |        2135.4 |          6376.4 |    2.99 |      0.33 | False    |
| Q08     | exasol            | duckdb              |         503.2 |          8869.5 |   17.63 |      0.06 | False    |
| Q09     | exasol            | duckdb              |        7739.7 |          7974.6 |    1.03 |      0.97 | False    |
| Q10     | exasol            | duckdb              |        2463.1 |          8640.7 |    3.51 |      0.29 | False    |
| Q11     | exasol            | duckdb              |         450.6 |          6907.2 |   15.33 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         585   |          5104.8 |    8.73 |      0.11 | False    |
| Q13     | exasol            | duckdb              |        4666.8 |          7902.8 |    1.69 |      0.59 | False    |
| Q14     | exasol            | duckdb              |         665.4 |          6342.7 |    9.53 |      0.1  | False    |
| Q15     | exasol            | duckdb              |        1570.2 |          6628   |    4.22 |      0.24 | False    |
| Q16     | exasol            | duckdb              |        2014.8 |          8248.6 |    4.09 |      0.24 | False    |
| Q17     | exasol            | duckdb              |          71.3 |          7581.1 |  106.33 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        3565.2 |          8098.3 |    2.27 |      0.44 | False    |
| Q19     | exasol            | duckdb              |          78.2 |          4754.9 |   60.8  |      0.02 | False    |
| Q20     | exasol            | duckdb              |         836.2 |          7503.1 |    8.97 |      0.11 | False    |
| Q21     | exasol            | duckdb              |        2593.9 |         12328.4 |    4.75 |      0.21 | False    |
| Q22     | exasol            | duckdb              |         642.5 |          5442.9 |    8.47 |      0.12 | False    |
| Q01     | exasol            | starrocks           |        5234.7 |         28056.2 |    5.36 |      0.19 | False    |
| Q02     | exasol            | starrocks           |         196.7 |          1106.1 |    5.62 |      0.18 | False    |
| Q03     | exasol            | starrocks           |         644.7 |          3371.9 |    5.23 |      0.19 | False    |
| Q04     | exasol            | starrocks           |         374.4 |          3902.6 |   10.42 |      0.1  | False    |
| Q05     | exasol            | starrocks           |        1529.3 |         12114.5 |    7.92 |      0.13 | False    |
| Q06     | exasol            | starrocks           |         263.2 |           818.1 |    3.11 |      0.32 | False    |
| Q07     | exasol            | starrocks           |        2135.4 |          8022.4 |    3.76 |      0.27 | False    |
| Q08     | exasol            | starrocks           |         503.2 |          4372.9 |    8.69 |      0.12 | False    |
| Q09     | exasol            | starrocks           |        7739.7 |         14802.4 |    1.91 |      0.52 | False    |
| Q10     | exasol            | starrocks           |        2463.1 |          4287.1 |    1.74 |      0.57 | False    |
| Q11     | exasol            | starrocks           |         450.6 |           787.7 |    1.75 |      0.57 | False    |
| Q12     | exasol            | starrocks           |         585   |          2243.1 |    3.83 |      0.26 | False    |
| Q13     | exasol            | starrocks           |        4666.8 |         11480.9 |    2.46 |      0.41 | False    |
| Q14     | exasol            | starrocks           |         665.4 |          1612.6 |    2.42 |      0.41 | False    |
| Q15     | exasol            | starrocks           |        1570.2 |           649.2 |    0.41 |      2.42 | True     |
| Q16     | exasol            | starrocks           |        2014.8 |          1083.6 |    0.54 |      1.86 | True     |
| Q17     | exasol            | starrocks           |          71.3 |          3268.7 |   45.84 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3565.2 |         43613   |   12.23 |      0.08 | False    |
| Q19     | exasol            | starrocks           |          78.2 |          2247.2 |   28.74 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         836.2 |          1313.7 |    1.57 |      0.64 | False    |
| Q21     | exasol            | starrocks           |        2593.9 |         32254.3 |   12.43 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         642.5 |          1439   |    2.24 |      0.45 | False    |
| Q01     | exasol            | clickhouse          |        5234.7 |         11512.8 |    2.2  |      0.45 | False    |
| Q02     | exasol            | clickhouse          |         196.7 |         10202.3 |   51.87 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         644.7 |         20084.9 |   31.15 |      0.03 | False    |
| Q04     | exasol            | clickhouse          |         374.4 |         33085   |   88.37 |      0.01 | False    |
| Q05     | exasol            | clickhouse          |        1529.3 |         27285.6 |   17.84 |      0.06 | False    |
| Q06     | exasol            | clickhouse          |         263.2 |          3244   |   12.33 |      0.08 | False    |
| Q07     | exasol            | clickhouse          |        2135.4 |         36870.7 |   17.27 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |         503.2 |         29962.6 |   59.54 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        7739.7 |         23591.6 |    3.05 |      0.33 | False    |
| Q10     | exasol            | clickhouse          |        2463.1 |         27483.7 |   11.16 |      0.09 | False    |
| Q11     | exasol            | clickhouse          |         450.6 |          3473.6 |    7.71 |      0.13 | False    |
| Q12     | exasol            | clickhouse          |         585   |          4861.2 |    8.31 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |        4666.8 |         15941.3 |    3.42 |      0.29 | False    |
| Q14     | exasol            | clickhouse          |         665.4 |          3533.5 |    5.31 |      0.19 | False    |
| Q15     | exasol            | clickhouse          |        1570.2 |          4100.6 |    2.61 |      0.38 | False    |
| Q16     | exasol            | clickhouse          |        2014.8 |         12301.4 |    6.11 |      0.16 | False    |
| Q17     | exasol            | clickhouse          |          71.3 |         10069.2 |  141.22 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3565.2 |         24961.4 |    7    |      0.14 | False    |
| Q19     | exasol            | clickhouse          |          78.2 |         31884   |  407.72 |      0    | False    |
| Q20     | exasol            | clickhouse          |         836.2 |         14642.5 |   17.51 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |        2593.9 |         18662.6 |    7.19 |      0.14 | False    |
| Q22     | exasol            | clickhouse          |         642.5 |          8866.9 |   13.8  |      0.07 | False    |
| Q01     | exasol            | trino               |        5234.7 |         14883.7 |    2.84 |      0.35 | False    |
| Q02     | exasol            | trino               |         196.7 |         17123.5 |   87.05 |      0.01 | False    |
| Q03     | exasol            | trino               |         644.7 |         31808.2 |   49.34 |      0.02 | False    |
| Q04     | exasol            | trino               |         374.4 |         22648.2 |   60.49 |      0.02 | False    |
| Q05     | exasol            | trino               |        1529.3 |         71235.5 |   46.58 |      0.02 | False    |
| Q06     | exasol            | trino               |         263.2 |         16771.6 |   63.72 |      0.02 | False    |
| Q07     | exasol            | trino               |        2135.4 |         17238.7 |    8.07 |      0.12 | False    |
| Q08     | exasol            | trino               |         503.2 |         32042.9 |   63.68 |      0.02 | False    |
| Q09     | exasol            | trino               |        7739.7 |        165238   |   21.35 |      0.05 | False    |
| Q10     | exasol            | trino               |        2463.1 |         67564.6 |   27.43 |      0.04 | False    |
| Q11     | exasol            | trino               |         450.6 |          5242.6 |   11.63 |      0.09 | False    |
| Q12     | exasol            | trino               |         585   |         22180.8 |   37.92 |      0.03 | False    |
| Q13     | exasol            | trino               |        4666.8 |         51656.7 |   11.07 |      0.09 | False    |
| Q14     | exasol            | trino               |         665.4 |         24031.9 |   36.12 |      0.03 | False    |
| Q15     | exasol            | trino               |        1570.2 |         39550.9 |   25.19 |      0.04 | False    |
| Q16     | exasol            | trino               |        2014.8 |          7939.9 |    3.94 |      0.25 | False    |
| Q17     | exasol            | trino               |          71.3 |         55038.1 |  771.92 |      0    | False    |
| Q18     | exasol            | trino               |        3565.2 |         48316.7 |   13.55 |      0.07 | False    |
| Q19     | exasol            | trino               |          78.2 |         12428.6 |  158.93 |      0.01 | False    |
| Q20     | exasol            | trino               |         836.2 |         11800.4 |   14.11 |      0.07 | False    |
| Q21     | exasol            | trino               |        2593.9 |        118064   |   45.52 |      0.02 | False    |
| Q22     | exasol            | trino               |         642.5 |         15321   |   23.85 |      0.04 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 18628.8 | 17682.2 | 3244.0 | 38559.7 |
| 1 | 28 | 17711.0 | 11891.3 | 823.6 | 64654.6 |
| 2 | 27 | 18638.2 | 18117.1 | 2237.9 | 38865.2 |
| 3 | 27 | 16660.6 | 12301.4 | 1547.0 | 42014.4 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 11891.3ms
- Slowest stream median: 18117.1ms
- Stream performance variation: 52.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 7631.4 | 7560.6 | 2970.3 | 14629.4 |
| 1 | 28 | 7472.0 | 6767.6 | 3412.3 | 13798.1 |
| 2 | 27 | 7861.8 | 7306.4 | 3868.1 | 19941.1 |
| 3 | 27 | 7635.9 | 7599.1 | 1180.5 | 14840.9 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 6767.6ms
- Slowest stream median: 7599.1ms
- Stream performance variation: 12.3% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 1899.1 | 1846.8 | 105.7 | 4977.9 |
| 1 | 28 | 1364.8 | 553.6 | 68.1 | 8054.7 |
| 2 | 27 | 1890.2 | 836.2 | 73.6 | 7873.4 |
| 3 | 27 | 1538.8 | 666.9 | 71.3 | 7739.7 |

**Performance Analysis for Exasol:**
- Fastest stream median: 553.6ms
- Slowest stream median: 1846.8ms
- Stream performance variation: 233.6% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 9030.7 | 5437.7 | 221.5 | 40576.0 |
| 1 | 28 | 7467.5 | 2939.5 | 649.2 | 47622.8 |
| 2 | 27 | 8191.8 | 2247.2 | 325.3 | 44797.2 |
| 3 | 27 | 7864.7 | 2482.3 | 787.7 | 43613.0 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2247.2ms
- Slowest stream median: 5437.7ms
- Stream performance variation: 142.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 46329.0 | 38533.6 | 4032.4 | 131394.4 |
| 1 | 28 | 39657.8 | 29633.3 | 7673.5 | 150250.0 |
| 2 | 27 | 47195.2 | 19333.9 | 2779.5 | 248543.4 |
| 3 | 27 | 40833.0 | 22572.7 | 5242.6 | 210835.7 |

**Performance Analysis for Trino:**
- Fastest stream median: 19333.9ms
- Slowest stream median: 38533.6ms
- Stream performance variation: 99.3% difference between fastest and slowest streams
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
- Median runtime: 801.9ms
- Average runtime: 1672.5ms
- Fastest query: 68.1ms
- Slowest query: 8054.7ms

**duckdb:**
- Median runtime: 7341.8ms
- Average runtime: 7648.5ms
- Fastest query: 1180.5ms
- Slowest query: 19941.1ms

**starrocks:**
- Median runtime: 2994.9ms
- Average runtime: 8140.7ms
- Fastest query: 221.5ms
- Slowest query: 47622.8ms

**clickhouse:**
- Median runtime: 16084.5ms
- Average runtime: 17914.4ms
- Fastest query: 823.6ms
- Slowest query: 64654.6ms

**trino:**
- Median runtime: 23866.8ms
- Average runtime: 43494.5ms
- Fastest query: 2779.5ms
- Slowest query: 248543.4ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_sf_100-benchmark.zip`](extscal_sf_100-benchmark.zip)

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
  - max_memory_usage: 30000000000
  - max_bytes_before_external_group_by: 10000000000
  - max_bytes_before_external_sort: 10000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 20000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 96GB
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
- Measured runs executed across 4 concurrent streams (randomized distribution)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts