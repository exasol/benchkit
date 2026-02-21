# Streamlined Scalability - Scale Factor 100 (Single Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-19 21:03:41

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
- exasol was the fastest overall with 801.9ms median runtime
- trino was 29.8x slower- Tested 550 total query executions across 22 different TPC-H queries
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
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-7

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
- **Instance Type:** r6id.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 123.8GB RAM
- **Hostname:** ip-10-0-1-131

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



#### Starrocks 4.0.6 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3AA8F947648AEBF1D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3AA8F947648AEBF1D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3AA8F947648AEBF1D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3AA8F947648AEBF1D /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43180E450D224A19F with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43180E450D224A19F

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43180E450D224A19F to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43180E450D224A19F /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

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
| Clickhouse | 866.01s | 0.15s | 439.14s | 1687.33s | 114.5 GB | 43.9 GB | 2.6x |
| Starrocks | 869.58s | 0.14s | 671.04s | 1855.30s | 30.1 GB | 30.1 GB | 1.0x |
| Trino | 146.81s | 0.33s | 0.00s | 205.23s | N/A | N/A | N/A |
| Duckdb | 869.41s | 0.04s | 219.42s | 1115.06s | 825.9 MB | N/A | N/A |
| Exasol | 261.52s | 1.97s | 507.70s | 931.01s | 95.7 GB | 23.0 GB | 4.2x |

**Key Observations:**
- Trino had the fastest preparation time at 205.23s
- Starrocks took 1855.30s (9.0x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   4854.6 |      5 |     12005.5 |   13464.7 |   3675.8 |  10823   |  19756.6 |
| Q01     | duckdb     |   2251.6 |      5 |      5331.5 |    6906.7 |   3325.9 |   4851.2 |  12769.7 |
| Q01     | exasol     |   1585   |      5 |      5234.7 |    4656   |   1238   |   2562.3 |   5616.3 |
| Q01     | starrocks  |   7200.5 |      5 |     29929.5 |   35019.3 |  21431.4 |   7073   |  63426.8 |
| Q01     | trino      |  10074.5 |      5 |     14883.7 |   28637.6 |  22811.1 |  12091   |  63975.7 |
| Q02     | clickhouse |   2616.4 |      5 |      9274.1 |    8351.1 |   3470.9 |   3957   |  12998.8 |
| Q02     | duckdb     |    488.5 |      5 |      7153.6 |    6341.9 |   2253   |   3412.3 |   8424.8 |
| Q02     | exasol     |    101.6 |      5 |       196.7 |     202.9 |     28.2 |    163.4 |    230.8 |
| Q02     | starrocks  |    478.7 |      5 |      1045.5 |    1080.4 |     96.5 |    994.5 |   1229.9 |
| Q02     | trino      |   5561.2 |      5 |     17123.5 |   14409.1 |   6518.1 |   7306.8 |  22343.5 |
| Q03     | clickhouse |   2625.7 |      5 |     14378.3 |   11625.4 |   6281.4 |   3357.1 |  17633.8 |
| Q03     | duckdb     |   1507.1 |      5 |      6086.5 |    7268.4 |   3867.7 |   2970.3 |  11344   |
| Q03     | exasol     |    602   |      5 |       644.7 |    1276   |    898.7 |    609.5 |   2373.3 |
| Q03     | starrocks  |   3579.5 |      5 |      3539   |    4364   |   1698.6 |   2908.3 |   6348.6 |
| Q03     | trino      |  18688   |      5 |     31808.2 |   34689.4 |  17529.6 |  16775.5 |  54345   |
| Q04     | clickhouse |  14990.8 |      5 |     24097.7 |   23722.6 |   5799.5 |  15153.4 |  31462.7 |
| Q04     | duckdb     |   1442.9 |      5 |      7071.5 |    6976.5 |   1840.3 |   4534.9 |   9499.9 |
| Q04     | exasol     |    114.7 |      5 |       374.4 |     359.6 |    123.2 |    173.8 |    505.7 |
| Q04     | starrocks  |   1401.9 |      5 |      6424   |    6178.3 |   3017.2 |   1819.8 |  10117.7 |
| Q04     | trino      |  10031.4 |      5 |     22648.2 |   29058.7 |  21696.3 |  15199.4 |  67295.3 |
| Q05     | clickhouse |   6673.7 |      5 |     22990.8 |   24648.7 |   5188.2 |  19376.3 |  30305.1 |
| Q05     | duckdb     |   1674.7 |      5 |      5952.5 |    7940   |   4264.6 |   4062.6 |  14840.9 |
| Q05     | exasol     |    473   |      5 |      1529.3 |    1446.6 |    227.4 |   1044.9 |   1607.5 |
| Q05     | starrocks  |   3399.2 |      5 |      8452.4 |    9780.3 |   5030.1 |   5684.3 |  18122.8 |
| Q05     | trino      |  20224.1 |      5 |     71235.5 |   65004.3 |  25928.2 |  34803.9 | 100919   |
| Q06     | clickhouse |    278.9 |      5 |      2191.5 |    3594.2 |   3001.7 |   1882   |   8925.3 |
| Q06     | duckdb     |    407   |      5 |      7121   |    6959.4 |   3879.9 |   3005.3 |  10944.1 |
| Q06     | exasol     |     75.1 |      5 |       263.2 |     269.9 |    180.6 |    105.7 |    564.9 |
| Q06     | starrocks  |    183.1 |      5 |       460.3 |     577.8 |    336.7 |    218.2 |    936.4 |
| Q06     | trino      |   4789.5 |      5 |     16771.6 |   19525.1 |  13158.2 |   6733.5 |  40504.2 |
| Q07     | clickhouse |   6919.1 |      5 |      6825.9 |    7904   |   2202.1 |   6257.7 |  11621.7 |
| Q07     | duckdb     |   1440.5 |      5 |      6376.4 |    7011   |   1814.7 |   5343.1 |   9163.8 |
| Q07     | exasol     |    576.5 |      5 |      2135.4 |    1883.1 |    736.5 |    582.8 |   2369.9 |
| Q07     | starrocks  |   2689.4 |      5 |      9429.6 |    8223.4 |   3264   |   2680.7 |  11070.4 |
| Q07     | trino      |  10955.9 |      5 |     17238.7 |   25350   |  17322.7 |  16106.3 |  56205.5 |
| Q08     | clickhouse |   7518.6 |      5 |     28472.6 |   27839.1 |   4436.4 |  21884.9 |  33876.7 |
| Q08     | duckdb     |   1535.2 |      5 |      8869.5 |    8448.8 |   2902.4 |   5289.9 |  11376.4 |
| Q08     | exasol     |    136.9 |      5 |       503.2 |     462.2 |    121.7 |    257.1 |    578.1 |
| Q08     | starrocks  |   1994.5 |      5 |      3745.9 |    4284.6 |   1393.3 |   3038.4 |   6629.2 |
| Q08     | trino      |  10554   |      5 |     32042.9 |   49314.7 |  34475.1 |  17970.8 |  86699.4 |
| Q09     | clickhouse |   5019.8 |      5 |     22495.7 |   21058.3 |   4718.9 |  15490.2 |  27122.6 |
| Q09     | duckdb     |   4488.2 |      5 |      7974.6 |    8153.4 |   2679.5 |   4510.7 |  11866.5 |
| Q09     | exasol     |   2000.1 |      5 |      7739.7 |    7504   |    627.7 |   6471.7 |   8054.7 |
| Q09     | starrocks  |   6213.2 |      5 |     17924.3 |   17152.3 |   4847.9 |   9828.3 |  23356.7 |
| Q09     | trino      |  44122.8 |      5 |    165238   |  179770   |  42548   | 143710   | 248543   |
| Q10     | clickhouse |   6500.3 |      5 |     23865.2 |   20701.6 |   6100.3 |  10815.4 |  25035.2 |
| Q10     | duckdb     |   2286.7 |      5 |      8640.7 |    8139   |   1868.8 |   5317.7 |   9745.2 |
| Q10     | exasol     |    802.1 |      5 |      2463.1 |    2065.4 |    616.9 |   1382.5 |   2553.2 |
| Q10     | starrocks  |   2642.3 |      5 |      6421.2 |    6031.8 |   1486.4 |   4454.5 |   7476.7 |
| Q10     | trino      |  11741   |      5 |     67564.6 |   52461.2 |  27652.2 |  15625.6 |  79241.3 |
| Q11     | clickhouse |   1556.1 |      5 |      4440.7 |    6710.3 |   5849   |   1307.6 |  16080.2 |
| Q11     | duckdb     |    218.8 |      5 |      6907.2 |    6839.9 |    734.9 |   5716.1 |   7584   |
| Q11     | exasol     |    180.3 |      5 |       450.6 |     439.8 |     95.3 |    287.4 |    537.5 |
| Q11     | starrocks  |    331.6 |      5 |       571.7 |     580.5 |    126.1 |    438.8 |    769.7 |
| Q11     | trino      |   1975.9 |      5 |      5242.6 |    6095.3 |   3167.1 |   2779.5 |  10748.7 |
| Q12     | clickhouse |   3923.1 |      5 |      6670.6 |    6119.4 |   2778.7 |   2505.1 |   9126.6 |
| Q12     | duckdb     |   1607.8 |      5 |      5104.8 |    5767.8 |   1708.5 |   4263   |   7603.5 |
| Q12     | exasol     |    152.8 |      5 |       585   |     636.2 |     88.5 |    564.5 |    767.6 |
| Q12     | starrocks  |    597.9 |      5 |      1699.4 |    2063   |    856   |   1394.6 |   3438.7 |
| Q12     | trino      |   6037.9 |      5 |     22180.8 |   27203.7 |  12894.8 |  19333.9 |  49862.6 |
| Q13     | clickhouse |   4493.9 |      5 |     13510.8 |   13218.9 |   4026.6 |   8901.3 |  19400   |
| Q13     | duckdb     |   4019.6 |      5 |      7902.8 |    7949.6 |   2578.2 |   4069.5 |  11165.7 |
| Q13     | exasol     |   1297.6 |      5 |      4666.8 |    4232.7 |   1110.5 |   2265.8 |   4977.9 |
| Q13     | starrocks  |   3942.5 |      5 |     10245   |   11951.3 |   7351.6 |   3854.8 |  23956.4 |
| Q13     | trino      |  17298.2 |      5 |     51656.7 |   69677.3 |  32368.3 |  42263.3 | 118092   |
| Q14     | clickhouse |    324.3 |      5 |      6971.6 |    6208.2 |   3373.3 |   2655.6 |  10548.8 |
| Q14     | duckdb     |   1128.7 |      5 |      6342.7 |    6949.2 |   4315.4 |   1180.5 |  11949   |
| Q14     | exasol     |    154.2 |      5 |       665.4 |     677.6 |    139.2 |    542.4 |    904.5 |
| Q14     | starrocks  |    303.7 |      5 |       964   |    1486.5 |    970.7 |    799.8 |   3097.7 |
| Q14     | trino      |   6921.1 |      5 |     24031.9 |   25746.5 |  12602   |  14033.8 |  47026.7 |
| Q15     | clickhouse |    486.7 |      5 |      3101.4 |    3471.9 |   1510.6 |   1372.6 |   4964.9 |
| Q15     | duckdb     |    929   |      5 |      6628   |    6933.5 |   3025.5 |   3431.1 |  11768.5 |
| Q15     | exasol     |    532.1 |      5 |      1570.2 |    1548   |     61.7 |   1461.6 |   1622   |
| Q15     | starrocks  |    285.6 |      5 |       762.3 |    1625.3 |   1615.3 |    385.1 |   4181.2 |
| Q15     | trino      |  11898.6 |      5 |     39550.9 |   36676.7 |  17549.7 |  18667.3 |  62008.6 |
| Q16     | clickhouse |   1037.5 |      5 |      5891.1 |    7122.3 |   3555.5 |   4181.6 |  13303.3 |
| Q16     | duckdb     |    757   |      5 |      8248.6 |    7791.8 |   3670.4 |   3647.2 |  11502.3 |
| Q16     | exasol     |    663.5 |      5 |      2014.8 |    2015.7 |    138.1 |   1884.5 |   2208.6 |
| Q16     | starrocks  |    873.2 |      5 |      1563.9 |    1467.4 |    258.1 |   1101.6 |   1775.9 |
| Q16     | trino      |   3540.8 |      5 |      7939.9 |   11115.6 |   4981.5 |   7209.4 |  18290.2 |
| Q17     | clickhouse |   2290.8 |      5 |      9626.1 |    9016.7 |   2776.8 |   5234.8 |  12623.2 |
| Q17     | duckdb     |   1661.8 |      5 |      7581.1 |    7231.7 |   1494.4 |   5266.8 |   9147.8 |
| Q17     | exasol     |     33.7 |      5 |        71.3 |      72.1 |      4   |     68.1 |     76.4 |
| Q17     | starrocks  |   1145.9 |      5 |      3812   |    3557.7 |   1220.2 |   1570   |   4853.7 |
| Q17     | trino      |  14028.4 |      5 |     55038.1 |   51481.4 |  14638.4 |  27418.6 |  66548.6 |
| Q18     | clickhouse |   6829.8 |      5 |     24515.3 |   24076.3 |   3020.2 |  20436   |  27434.5 |
| Q18     | duckdb     |   3509.3 |      5 |      8098.3 |    9373.2 |   3225.2 |   5873   |  13798.1 |
| Q18     | exasol     |   1057.5 |      5 |      3565.2 |    3219.8 |    801.2 |   1809   |   3769.2 |
| Q18     | starrocks  |  10208.5 |      5 |     40242.9 |   37995.8 |   8402.5 |  26845.3 |  49012.1 |
| Q18     | trino      |  16570.8 |      5 |     48316.7 |   54297.1 |  19303.2 |  30541.3 |  81155.7 |
| Q19     | clickhouse |   9721.9 |      5 |     27785.5 |   24579.5 |   8752   |   9051.1 |  30213.2 |
| Q19     | duckdb     |   1631.7 |      5 |      4754.9 |    8197.1 |   6739.6 |   3868.1 |  19941.1 |
| Q19     | exasol     |     41.2 |      5 |        78.2 |      97.3 |     29.6 |     73.6 |    133.1 |
| Q19     | starrocks  |   1622.2 |      5 |      2320   |    2635.6 |    812.3 |   1888.3 |   3987.3 |
| Q19     | trino      |   7981.7 |      5 |     12428.6 |   17719.1 |  13829.7 |   8808.9 |  42270.4 |
| Q20     | clickhouse |   3283.4 |      5 |     10800.6 |   10032.9 |   2933.9 |   5454.6 |  12638.7 |
| Q20     | duckdb     |   1466.3 |      5 |      7503.1 |    7727.3 |   3291   |   3809.3 |  11185.7 |
| Q20     | exasol     |    412.6 |      5 |       836.2 |     923   |    227.8 |    683.5 |   1178.6 |
| Q20     | starrocks  |    609.4 |      5 |      1257   |    1302.4 |    442.7 |    881.7 |   2024.4 |
| Q20     | trino      |   7839.2 |      5 |     11800.4 |   13617   |   5257.4 |   8656.5 |  21161.9 |
| Q21     | clickhouse |   5533   |      5 |     19282.7 |   18232.9 |   5140.4 |  12721   |  25574.6 |
| Q21     | duckdb     |   7991.3 |      5 |     12328.4 |   12870.1 |   1694.8 |  10715.1 |  14629.4 |
| Q21     | exasol     |    817   |      5 |      2593.9 |    2234.8 |    808.1 |   1170.8 |   2970.7 |
| Q21     | starrocks  |  14370.1 |      5 |     35504.9 |   31474.4 |  11210.1 |  15688.1 |  45052.7 |
| Q21     | trino      |  44704.1 |      5 |    118064   |  127102   |  51886.2 |  71211.1 | 210836   |
| Q22     | clickhouse |    885   |      5 |     10783.9 |    9561.5 |   2901.5 |   6245   |  12131.3 |
| Q22     | duckdb     |    828.9 |      5 |      5442.9 |    6490.4 |   3484.8 |   3103.3 |  11798.8 |
| Q22     | exasol     |    182.4 |      5 |       642.5 |     572.2 |    172.2 |    266.4 |    667.3 |
| Q22     | starrocks  |    613.7 |      5 |      1449   |    1923.2 |   1672   |    544.4 |   4835.4 |
| Q22     | trino      |   5107.3 |      5 |     15321   |   17925.7 |   7893.2 |  12321   |  31848   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        5234.7 |         12005.5 |    2.29 |      0.44 | False    |
| Q02     | exasol            | clickhouse          |         196.7 |          9274.1 |   47.15 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         644.7 |         14378.3 |   22.3  |      0.04 | False    |
| Q04     | exasol            | clickhouse          |         374.4 |         24097.7 |   64.36 |      0.02 | False    |
| Q05     | exasol            | clickhouse          |        1529.3 |         22990.8 |   15.03 |      0.07 | False    |
| Q06     | exasol            | clickhouse          |         263.2 |          2191.5 |    8.33 |      0.12 | False    |
| Q07     | exasol            | clickhouse          |        2135.4 |          6825.9 |    3.2  |      0.31 | False    |
| Q08     | exasol            | clickhouse          |         503.2 |         28472.6 |   56.58 |      0.02 | False    |
| Q09     | exasol            | clickhouse          |        7739.7 |         22495.7 |    2.91 |      0.34 | False    |
| Q10     | exasol            | clickhouse          |        2463.1 |         23865.2 |    9.69 |      0.1  | False    |
| Q11     | exasol            | clickhouse          |         450.6 |          4440.7 |    9.86 |      0.1  | False    |
| Q12     | exasol            | clickhouse          |         585   |          6670.6 |   11.4  |      0.09 | False    |
| Q13     | exasol            | clickhouse          |        4666.8 |         13510.8 |    2.9  |      0.35 | False    |
| Q14     | exasol            | clickhouse          |         665.4 |          6971.6 |   10.48 |      0.1  | False    |
| Q15     | exasol            | clickhouse          |        1570.2 |          3101.4 |    1.98 |      0.51 | False    |
| Q16     | exasol            | clickhouse          |        2014.8 |          5891.1 |    2.92 |      0.34 | False    |
| Q17     | exasol            | clickhouse          |          71.3 |          9626.1 |  135.01 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        3565.2 |         24515.3 |    6.88 |      0.15 | False    |
| Q19     | exasol            | clickhouse          |          78.2 |         27785.5 |  355.31 |      0    | False    |
| Q20     | exasol            | clickhouse          |         836.2 |         10800.6 |   12.92 |      0.08 | False    |
| Q21     | exasol            | clickhouse          |        2593.9 |         19282.7 |    7.43 |      0.13 | False    |
| Q22     | exasol            | clickhouse          |         642.5 |         10783.9 |   16.78 |      0.06 | False    |
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
| Q01     | exasol            | starrocks           |        5234.7 |         29929.5 |    5.72 |      0.17 | False    |
| Q02     | exasol            | starrocks           |         196.7 |          1045.5 |    5.32 |      0.19 | False    |
| Q03     | exasol            | starrocks           |         644.7 |          3539   |    5.49 |      0.18 | False    |
| Q04     | exasol            | starrocks           |         374.4 |          6424   |   17.16 |      0.06 | False    |
| Q05     | exasol            | starrocks           |        1529.3 |          8452.4 |    5.53 |      0.18 | False    |
| Q06     | exasol            | starrocks           |         263.2 |           460.3 |    1.75 |      0.57 | False    |
| Q07     | exasol            | starrocks           |        2135.4 |          9429.6 |    4.42 |      0.23 | False    |
| Q08     | exasol            | starrocks           |         503.2 |          3745.9 |    7.44 |      0.13 | False    |
| Q09     | exasol            | starrocks           |        7739.7 |         17924.3 |    2.32 |      0.43 | False    |
| Q10     | exasol            | starrocks           |        2463.1 |          6421.2 |    2.61 |      0.38 | False    |
| Q11     | exasol            | starrocks           |         450.6 |           571.7 |    1.27 |      0.79 | False    |
| Q12     | exasol            | starrocks           |         585   |          1699.4 |    2.9  |      0.34 | False    |
| Q13     | exasol            | starrocks           |        4666.8 |         10245   |    2.2  |      0.46 | False    |
| Q14     | exasol            | starrocks           |         665.4 |           964   |    1.45 |      0.69 | False    |
| Q15     | exasol            | starrocks           |        1570.2 |           762.3 |    0.49 |      2.06 | True     |
| Q16     | exasol            | starrocks           |        2014.8 |          1563.9 |    0.78 |      1.29 | True     |
| Q17     | exasol            | starrocks           |          71.3 |          3812   |   53.46 |      0.02 | False    |
| Q18     | exasol            | starrocks           |        3565.2 |         40242.9 |   11.29 |      0.09 | False    |
| Q19     | exasol            | starrocks           |          78.2 |          2320   |   29.67 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         836.2 |          1257   |    1.5  |      0.67 | False    |
| Q21     | exasol            | starrocks           |        2593.9 |         35504.9 |   13.69 |      0.07 | False    |
| Q22     | exasol            | starrocks           |         642.5 |          1449   |    2.26 |      0.44 | False    |
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
| 0 | 28 | 13668.5 | 13662.5 | 1372.6 | 30305.1 |
| 1 | 28 | 13433.1 | 9832.2 | 2121.6 | 31462.7 |
| 2 | 27 | 14903.7 | 12721.0 | 1307.6 | 29993.1 |
| 3 | 27 | 12779.9 | 9126.6 | 2191.5 | 33876.7 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 9126.6ms
- Slowest stream median: 13662.5ms
- Stream performance variation: 49.7% difference between fastest and slowest streams
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
| 0 | 28 | 9534.2 | 5079.9 | 218.2 | 45052.7 |
| 1 | 28 | 7946.9 | 3338.5 | 460.3 | 63426.8 |
| 2 | 27 | 8832.9 | 3097.7 | 341.6 | 49012.1 |
| 3 | 27 | 8363.6 | 3438.7 | 502.5 | 40242.9 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 3097.7ms
- Slowest stream median: 5079.9ms
- Stream performance variation: 64.0% difference between fastest and slowest streams
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

**clickhouse:**
- Median runtime: 11813.6ms
- Average runtime: 13693.7ms
- Fastest query: 1307.6ms
- Slowest query: 33876.7ms

**duckdb:**
- Median runtime: 7341.8ms
- Average runtime: 7648.5ms
- Fastest query: 1180.5ms
- Slowest query: 19941.1ms

**exasol:**
- Median runtime: 801.9ms
- Average runtime: 1672.5ms
- Fastest query: 68.1ms
- Slowest query: 8054.7ms

**starrocks:**
- Median runtime: 3588.8ms
- Average runtime: 8670.7ms
- Fastest query: 218.2ms
- Slowest query: 63426.8ms

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