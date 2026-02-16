# Streamlined Scalability - Node Scaling (1 Node)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.4xlarge
**Date:** 2026-02-10 11:33:11

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **starrocks**
- **clickhouse**
- **trino**

**Key Findings:**
- exasol was the fastest overall with 468.2ms median runtime
- trino was 25.7x slower- Tested 440 total query executions across 22 different TPC-H queries
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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B7DFAC6F2A5A957C with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B7DFAC6F2A5A957C

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B7DFAC6F2A5A957C to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1B7DFAC6F2A5A957C /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443ADCDEE7DF9529D with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443ADCDEE7DF9529D

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443ADCDEE7DF9529D to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS443ADCDEE7DF9529D /data

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
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2311E8505E0ADDEC5 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2311E8505E0ADDEC5

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2311E8505E0ADDEC5 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2311E8505E0ADDEC5 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse

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
| Clickhouse | 426.99s | 0.12s | 216.54s | 856.25s | 44.6 GB | 20.0 GB | 2.2x |
| Starrocks | 426.00s | 0.13s | 328.86s | 910.96s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 63.93s | 0.34s | 0.00s | 97.63s | N/A | N/A | N/A |
| Exasol | 177.57s | 1.94s | 255.81s | 513.63s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 97.63s
- Starrocks took 910.96s (9.3x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |   2365.2 |      5 |      6425.9 |    6745.3 |   2388.6 |   4216.2 |  10686.5 |
| Q01     | exasol     |    798.4 |      5 |      2445.2 |    2220.4 |    589   |   1203.8 |   2653.1 |
| Q01     | starrocks  |   3625.5 |      5 |     10852.4 |   12437.3 |   4382.6 |   7840.1 |  17178.2 |
| Q01     | trino      |   5443.5 |      5 |      7870.1 |    8823.8 |   2951.3 |   6405.7 |  13820.7 |
| Q02     | clickhouse |   1009.9 |      5 |      6385   |    6336.8 |   2712.6 |   3037.4 |   9130   |
| Q02     | exasol     |     67.4 |      5 |       116.3 |     117.5 |      5.4 |    112.7 |    126.3 |
| Q02     | starrocks  |    338.5 |      5 |       805.7 |     750.7 |    253   |    497.9 |   1114.8 |
| Q02     | trino      |   3366.6 |      5 |      5494   |    6368.7 |   3675.9 |   2318   |  12355   |
| Q03     | clickhouse |   3810.5 |      5 |     11674.6 |   12173.6 |   6456.9 |   3634   |  20931.7 |
| Q03     | exasol     |    295.5 |      5 |       547.9 |     621.2 |    337.2 |    290.7 |    978.1 |
| Q03     | starrocks  |    797.7 |      5 |       682.1 |    1625.7 |   1716.2 |    542.6 |   4545.4 |
| Q03     | trino      |   8695.8 |      5 |     22026.5 |   22031.4 |  10212.6 |  11229   |  34651.9 |
| Q04     | clickhouse |   7461.1 |      5 |     16843.6 |   17093   |   1775.9 |  14565.6 |  19472.6 |
| Q04     | exasol     |     61.4 |      5 |       176.6 |     143.7 |     62.8 |     73.4 |    196.3 |
| Q04     | starrocks  |    665.2 |      5 |      1993.7 |    2381.1 |   1597.3 |    517.2 |   4174.8 |
| Q04     | trino      |   4697.7 |      5 |      7918.4 |    9294   |   3238.1 |   6320.9 |  14611.4 |
| Q05     | clickhouse |   4651.4 |      5 |     17898.7 |   18279.6 |   3607.1 |  13136.2 |  22262.7 |
| Q05     | exasol     |    263.7 |      5 |       674.4 |     690.4 |    107.1 |    540.3 |    805.7 |
| Q05     | starrocks  |    727.2 |      5 |      2766.9 |    2765.6 |   1087.7 |   1584.5 |   4328.4 |
| Q05     | trino      |   7090.7 |      5 |     20318.9 |   25234.7 |  12142.8 |  10611.6 |  39158.4 |
| Q06     | clickhouse |    157.9 |      5 |      1372.7 |    1636.7 |   1294.7 |    319.2 |   3521.6 |
| Q06     | exasol     |     39.4 |      5 |       133.1 |     125.3 |     60.4 |     67   |    215.1 |
| Q06     | starrocks  |     92.9 |      5 |       429.4 |     586.5 |    573.8 |     89.7 |   1525.9 |
| Q06     | trino      |   2464   |      5 |      8698.2 |    8191.4 |   4853.6 |   2713.3 |  13443.4 |
| Q07     | clickhouse |   7369.6 |      5 |     27606   |   22718.1 |   8881   |  10633.8 |  29925.2 |
| Q07     | exasol     |    250.6 |      5 |       795.1 |     719.2 |    274.8 |    246.5 |    958.4 |
| Q07     | starrocks  |    855   |      5 |      2356.1 |    2363.1 |    956.7 |    822.1 |   3283.6 |
| Q07     | trino      |   5207.1 |      5 |     18938.9 |   17921.2 |  10537.9 |   7447.8 |  34314.5 |
| Q08     | clickhouse |   6349.8 |      5 |     25520.2 |   23650.5 |   5263.2 |  15070.7 |  28338.8 |
| Q08     | exasol     |     72.2 |      5 |       252.8 |     224.6 |     54.8 |    131.4 |    262.7 |
| Q08     | starrocks  |    701.6 |      5 |      2892.1 |    2606.6 |    466.9 |   1924.1 |   2992.9 |
| Q08     | trino      |   5444.1 |      5 |     13570.9 |   14014.5 |   4219.6 |   8872.5 |  20557.2 |
| Q09     | clickhouse |   4843.4 |      5 |     15244.3 |   15702.7 |   3535.2 |  11215.1 |  20324.1 |
| Q09     | exasol     |    931.5 |      5 |      3380.2 |    3353.2 |    192.4 |   3123.9 |   3543.7 |
| Q09     | starrocks  |   2829.6 |      5 |      8196.5 |    7323.9 |   1490.9 |   4837.6 |   8288.2 |
| Q09     | trino      |  20560.7 |      5 |     83490   |   87024.3 |  17272   |  70983.6 | 110646   |
| Q10     | clickhouse |   4512.5 |      5 |     17056   |   17056.6 |    836.3 |  15837.8 |  18105   |
| Q10     | exasol     |    405.5 |      5 |      1163.5 |    1006.9 |    294.8 |    676.7 |   1261.9 |
| Q10     | starrocks  |   1013.9 |      5 |      4379.3 |    4111.9 |   1262.4 |   2164.2 |   5661.1 |
| Q10     | trino      |   5470.7 |      5 |     17741.2 |   18689.4 |   4697.2 |  14170.9 |  24333.6 |
| Q11     | clickhouse |    599.3 |      5 |      5056.9 |    5639.4 |   1457   |   4324.3 |   8095.9 |
| Q11     | exasol     |    102.6 |      5 |       229.5 |     212.5 |     53.4 |    120.1 |    258.5 |
| Q11     | starrocks  |    142.8 |      5 |       447.4 |     466.9 |    149.3 |    260.4 |    670.6 |
| Q11     | trino      |   1286.4 |      5 |      2903.8 |    3025.6 |   1453.6 |   1204.8 |   5104.4 |
| Q12     | clickhouse |   1896.1 |      5 |      5492.7 |    4743.2 |   1944.6 |   2388.3 |   6498.7 |
| Q12     | exasol     |     80.2 |      5 |       272.5 |     283   |     31.9 |    252.5 |    318.4 |
| Q12     | starrocks  |    306.4 |      5 |       783.8 |     894.6 |    269.5 |    645.8 |   1243.2 |
| Q12     | trino      |   4505.7 |      5 |      8646   |    9985.5 |   3294.4 |   6394.6 |  14336.7 |
| Q13     | clickhouse |   2973.2 |      5 |      8730.2 |    8423.2 |   2169.9 |   5768.3 |  11563.9 |
| Q13     | exasol     |    623   |      5 |      2130   |    1924.9 |    599.8 |    862.5 |   2324.1 |
| Q13     | starrocks  |   1750   |      5 |      4141   |    3834.3 |   1207.7 |   1837.8 |   4766.4 |
| Q13     | trino      |   8341.4 |      5 |     24295.2 |   30694.4 |  17717.3 |  17683.3 |  61225.3 |
| Q14     | clickhouse |    202.2 |      5 |      3704.9 |    3655.6 |   1921.6 |   1744.8 |   6275.2 |
| Q14     | exasol     |     74.6 |      5 |       270   |     306.1 |     70.6 |    232.7 |    391.9 |
| Q14     | starrocks  |    159.4 |      5 |       726.4 |     973.1 |    496.2 |    678.5 |   1841.2 |
| Q14     | trino      |   3311.4 |      5 |     10592.8 |   11407   |   6178.5 |   4813.6 |  21392.5 |
| Q15     | clickhouse |    284.2 |      5 |      1451.6 |    2046.4 |   1993.3 |    559.2 |   5410.1 |
| Q15     | exasol     |    255.7 |      5 |       708.7 |     703.6 |     67.1 |    612.3 |    795.8 |
| Q15     | starrocks  |    137.5 |      5 |       741.2 |     891.5 |    545.1 |    323.8 |   1757.3 |
| Q15     | trino      |   5940.4 |      5 |     10881.3 |   10466.8 |   1530.9 |   8280.1 |  12265.6 |
| Q16     | clickhouse |    577.3 |      5 |      5836.3 |    4813.7 |   2128.3 |   2059.3 |   6995.5 |
| Q16     | exasol     |    398.2 |      5 |       990.2 |    1009.3 |     28.4 |    986.5 |   1045.9 |
| Q16     | starrocks  |    610.7 |      5 |       942   |     951.9 |    124   |    819.2 |   1089.8 |
| Q16     | trino      |   2190.8 |      5 |      6479.6 |    5817   |   1579.7 |   3216.4 |   7164.3 |
| Q17     | clickhouse |   1008.2 |      5 |      7015.2 |    5966.8 |   2877   |   2540.4 |   8786.3 |
| Q17     | exasol     |     21.3 |      5 |        42.6 |      44.1 |      6.9 |     37.3 |     54.6 |
| Q17     | starrocks  |    514.8 |      5 |      1479.2 |    1467.6 |    924.3 |    625.1 |   2963.8 |
| Q17     | trino      |   7894.7 |      5 |     19496.7 |   21719.8 |   9981   |  12377.4 |  36967.5 |
| Q18     | clickhouse |   5865.1 |      5 |     20276.2 |   20508.8 |   2238.7 |  17898   |  23509   |
| Q18     | exasol     |    525.9 |      5 |      1709   |    1635.4 |    196.8 |   1295.5 |   1788.8 |
| Q18     | starrocks  |   4598.7 |      5 |     12545   |   12863.5 |   1758.9 |  11374.4 |  15850.5 |
| Q18     | trino      |   7319.3 |      5 |     21735.1 |   25109.8 |   8302.1 |  17976.2 |  36829.9 |
| Q19     | clickhouse |   5030.1 |      5 |     12451.2 |   14349.7 |   4613.9 |  10574.3 |  21968   |
| Q19     | exasol     |     24.5 |      5 |        43.1 |      50.4 |     20.6 |     23.7 |     72.3 |
| Q19     | starrocks  |    596.3 |      5 |      1536.8 |    1482.3 |    433.4 |    892   |   1988.3 |
| Q19     | trino      |   3992.8 |      5 |      5544   |    6563.4 |   2205.8 |   4364.9 |   9973.1 |
| Q20     | clickhouse |   1773.3 |      5 |      7918.3 |    7507.1 |   2974.8 |   3850.4 |  10415.9 |
| Q20     | exasol     |    214.9 |      5 |       455.5 |     428.7 |    123.1 |    260.5 |    584.9 |
| Q20     | starrocks  |    319.1 |      5 |      1078.6 |    1165.1 |    611.7 |    524.8 |   1958.9 |
| Q20     | trino      |   4179.5 |      5 |      7540.7 |    8761   |   3510.7 |   4932.8 |  13094.3 |
| Q21     | clickhouse |   4863.7 |      5 |     16917.2 |   15288.4 |   3109.9 |  10123.5 |  17746   |
| Q21     | exasol     |    379.2 |      5 |       926.8 |     880.5 |    324.3 |    529.4 |   1217.5 |
| Q21     | starrocks  |   6202.2 |      5 |     12260.1 |   11799.6 |   4206.4 |   6632.1 |  18081.4 |
| Q21     | trino      |  18284.3 |      5 |     44224.4 |   45872.7 |  13924.5 |  26712.9 |  63495.8 |
| Q22     | clickhouse |    483.2 |      5 |      5184.4 |    5961.2 |   2969.6 |   2797.5 |  10612.5 |
| Q22     | exasol     |     94.5 |      5 |       326.3 |     317.4 |    151.1 |    114.1 |    535.8 |
| Q22     | starrocks  |    342.2 |      5 |       823.9 |     761.8 |    259.6 |    311.1 |    956.2 |
| Q22     | trino      |   2546   |      5 |      6293.5 |    6391.6 |    923.3 |   5397.3 |   7881   |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | starrocks           |        2445.2 |         10852.4 |    4.44 |      0.23 | False    |
| Q02     | exasol            | starrocks           |         116.3 |           805.7 |    6.93 |      0.14 | False    |
| Q03     | exasol            | starrocks           |         547.9 |           682.1 |    1.24 |      0.8  | False    |
| Q04     | exasol            | starrocks           |         176.6 |          1993.7 |   11.29 |      0.09 | False    |
| Q05     | exasol            | starrocks           |         674.4 |          2766.9 |    4.1  |      0.24 | False    |
| Q06     | exasol            | starrocks           |         133.1 |           429.4 |    3.23 |      0.31 | False    |
| Q07     | exasol            | starrocks           |         795.1 |          2356.1 |    2.96 |      0.34 | False    |
| Q08     | exasol            | starrocks           |         252.8 |          2892.1 |   11.44 |      0.09 | False    |
| Q09     | exasol            | starrocks           |        3380.2 |          8196.5 |    2.42 |      0.41 | False    |
| Q10     | exasol            | starrocks           |        1163.5 |          4379.3 |    3.76 |      0.27 | False    |
| Q11     | exasol            | starrocks           |         229.5 |           447.4 |    1.95 |      0.51 | False    |
| Q12     | exasol            | starrocks           |         272.5 |           783.8 |    2.88 |      0.35 | False    |
| Q13     | exasol            | starrocks           |        2130   |          4141   |    1.94 |      0.51 | False    |
| Q14     | exasol            | starrocks           |         270   |           726.4 |    2.69 |      0.37 | False    |
| Q15     | exasol            | starrocks           |         708.7 |           741.2 |    1.05 |      0.96 | False    |
| Q16     | exasol            | starrocks           |         990.2 |           942   |    0.95 |      1.05 | True     |
| Q17     | exasol            | starrocks           |          42.6 |          1479.2 |   34.72 |      0.03 | False    |
| Q18     | exasol            | starrocks           |        1709   |         12545   |    7.34 |      0.14 | False    |
| Q19     | exasol            | starrocks           |          43.1 |          1536.8 |   35.66 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         455.5 |          1078.6 |    2.37 |      0.42 | False    |
| Q21     | exasol            | starrocks           |         926.8 |         12260.1 |   13.23 |      0.08 | False    |
| Q22     | exasol            | starrocks           |         326.3 |           823.9 |    2.52 |      0.4  | False    |
| Q01     | exasol            | clickhouse          |        2445.2 |          6425.9 |    2.63 |      0.38 | False    |
| Q02     | exasol            | clickhouse          |         116.3 |          6385   |   54.9  |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         547.9 |         11674.6 |   21.31 |      0.05 | False    |
| Q04     | exasol            | clickhouse          |         176.6 |         16843.6 |   95.38 |      0.01 | False    |
| Q05     | exasol            | clickhouse          |         674.4 |         17898.7 |   26.54 |      0.04 | False    |
| Q06     | exasol            | clickhouse          |         133.1 |          1372.7 |   10.31 |      0.1  | False    |
| Q07     | exasol            | clickhouse          |         795.1 |         27606   |   34.72 |      0.03 | False    |
| Q08     | exasol            | clickhouse          |         252.8 |         25520.2 |  100.95 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        3380.2 |         15244.3 |    4.51 |      0.22 | False    |
| Q10     | exasol            | clickhouse          |        1163.5 |         17056   |   14.66 |      0.07 | False    |
| Q11     | exasol            | clickhouse          |         229.5 |          5056.9 |   22.03 |      0.05 | False    |
| Q12     | exasol            | clickhouse          |         272.5 |          5492.7 |   20.16 |      0.05 | False    |
| Q13     | exasol            | clickhouse          |        2130   |          8730.2 |    4.1  |      0.24 | False    |
| Q14     | exasol            | clickhouse          |         270   |          3704.9 |   13.72 |      0.07 | False    |
| Q15     | exasol            | clickhouse          |         708.7 |          1451.6 |    2.05 |      0.49 | False    |
| Q16     | exasol            | clickhouse          |         990.2 |          5836.3 |    5.89 |      0.17 | False    |
| Q17     | exasol            | clickhouse          |          42.6 |          7015.2 |  164.68 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        1709   |         20276.2 |   11.86 |      0.08 | False    |
| Q19     | exasol            | clickhouse          |          43.1 |         12451.2 |  288.89 |      0    | False    |
| Q20     | exasol            | clickhouse          |         455.5 |          7918.3 |   17.38 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |         926.8 |         16917.2 |   18.25 |      0.05 | False    |
| Q22     | exasol            | clickhouse          |         326.3 |          5184.4 |   15.89 |      0.06 | False    |
| Q01     | exasol            | trino               |        2445.2 |          7870.1 |    3.22 |      0.31 | False    |
| Q02     | exasol            | trino               |         116.3 |          5494   |   47.24 |      0.02 | False    |
| Q03     | exasol            | trino               |         547.9 |         22026.5 |   40.2  |      0.02 | False    |
| Q04     | exasol            | trino               |         176.6 |          7918.4 |   44.84 |      0.02 | False    |
| Q05     | exasol            | trino               |         674.4 |         20318.9 |   30.13 |      0.03 | False    |
| Q06     | exasol            | trino               |         133.1 |          8698.2 |   65.35 |      0.02 | False    |
| Q07     | exasol            | trino               |         795.1 |         18938.9 |   23.82 |      0.04 | False    |
| Q08     | exasol            | trino               |         252.8 |         13570.9 |   53.68 |      0.02 | False    |
| Q09     | exasol            | trino               |        3380.2 |         83490   |   24.7  |      0.04 | False    |
| Q10     | exasol            | trino               |        1163.5 |         17741.2 |   15.25 |      0.07 | False    |
| Q11     | exasol            | trino               |         229.5 |          2903.8 |   12.65 |      0.08 | False    |
| Q12     | exasol            | trino               |         272.5 |          8646   |   31.73 |      0.03 | False    |
| Q13     | exasol            | trino               |        2130   |         24295.2 |   11.41 |      0.09 | False    |
| Q14     | exasol            | trino               |         270   |         10592.8 |   39.23 |      0.03 | False    |
| Q15     | exasol            | trino               |         708.7 |         10881.3 |   15.35 |      0.07 | False    |
| Q16     | exasol            | trino               |         990.2 |          6479.6 |    6.54 |      0.15 | False    |
| Q17     | exasol            | trino               |          42.6 |         19496.7 |  457.67 |      0    | False    |
| Q18     | exasol            | trino               |        1709   |         21735.1 |   12.72 |      0.08 | False    |
| Q19     | exasol            | trino               |          43.1 |          5544   |  128.63 |      0.01 | False    |
| Q20     | exasol            | trino               |         455.5 |          7540.7 |   16.55 |      0.06 | False    |
| Q21     | exasol            | trino               |         926.8 |         44224.4 |   47.72 |      0.02 | False    |
| Q22     | exasol            | trino               |         326.3 |          6293.5 |   19.29 |      0.05 | False    |

### Per-Stream Statistics

This benchmark was executed using **4 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 11341.7 | 10378.6 | 678.6 | 29554.8 |
| 1 | 28 | 11080.3 | 8502.1 | 559.2 | 27606.0 |
| 2 | 27 | 10864.8 | 10574.3 | 2291.3 | 28338.8 |
| 3 | 27 | 10382.1 | 6498.7 | 319.2 | 29925.2 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 6498.7ms
- Slowest stream median: 10574.3ms
- Stream performance variation: 62.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 874.9 | 816.6 | 67.0 | 2324.1 |
| 1 | 28 | 639.3 | 263.9 | 37.3 | 3543.7 |
| 2 | 27 | 873.6 | 455.5 | 23.7 | 3529.9 |
| 3 | 27 | 707.7 | 315.5 | 42.6 | 3380.2 |

**Performance Analysis for Exasol:**
- Fastest stream median: 263.9ms
- Slowest stream median: 816.6ms
- Stream performance variation: 209.4% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 3656.3 | 1960.8 | 89.7 | 18081.4 |
| 1 | 28 | 2966.6 | 1483.1 | 260.4 | 15850.5 |
| 2 | 27 | 3571.2 | 1604.5 | 517.2 | 17009.3 |
| 3 | 27 | 3357.8 | 1243.2 | 196.5 | 17178.2 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 1243.2ms
- Slowest stream median: 1960.8ms
- Stream performance variation: 57.7% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 28 | 19495.9 | 13470.9 | 3586.2 | 61225.3 |
| 1 | 28 | 17594.3 | 12334.4 | 2318.0 | 110645.9 |
| 2 | 27 | 20003.8 | 12468.5 | 1204.8 | 83490.0 |
| 3 | 27 | 16237.5 | 8872.5 | 2328.6 | 98367.5 |

**Performance Analysis for Trino:**
- Fastest stream median: 8872.5ms
- Slowest stream median: 13470.9ms
- Stream performance variation: 51.8% difference between fastest and slowest streams
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
- Median runtime: 468.2ms
- Average runtime: 773.6ms
- Fastest query: 23.7ms
- Slowest query: 3543.7ms

**starrocks:**
- Median runtime: 1594.5ms
- Average runtime: 3386.6ms
- Fastest query: 89.7ms
- Slowest query: 18081.4ms

**clickhouse:**
- Median runtime: 9013.4ms
- Average runtime: 10922.6ms
- Fastest query: 319.2ms
- Slowest query: 29925.2ms

**trino:**
- Median runtime: 12022.8ms
- Average runtime: 18336.7ms
- Fastest query: 1204.8ms
- Slowest query: 110645.9ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_nodes_1-benchmark.zip`](extscal_nodes_1-benchmark.zip)

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

**Starrocks 4.0.4:**
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