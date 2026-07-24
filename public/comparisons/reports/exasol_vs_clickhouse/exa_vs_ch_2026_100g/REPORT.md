# Exasol 2026.1 vs ClickHouse 25.10 vs 26.4 — TPC-H SF100

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r6id.8xlarge
**Date:** 2026-06-22 13:33:37

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 3 database systems:
- **exasol**
- **clickhouse_26_4**
- **clickhouse_25_10**

**Key Findings:**
- exasol was the fastest overall with 254.2ms median runtime
- clickhouse_25_10 was 11.3x slower- Tested 990 total query executions across 22 different TPC-H queries

## Systems Under Test

### Clickhouse_25_10 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** preinstalled


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-240

### Clickhouse_26_4 26.4.4.38

**Software Configuration:**
- **Database:** clickhouse 26.4.4.38
- **Setup method:** preinstalled


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-151

### Exasol 2026.1.0

**Software Configuration:**
- **Database:** exasol 2026.1.0
- **Setup method:** preinstalled
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.8xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 32 vCPUs
- **Memory:** 247.7GB RAM
- **Hostname:** ip-10-0-1-215


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Clickhouse_25_10 Instance:** r6id.8xlarge
- **Clickhouse_26_4 Instance:** r6id.8xlarge
- **Exasol Instance:** r6id.8xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2026.1.0 Setup

**Storage Configuration:**
```bash
# Create GPT partition table
sudo parted -s /dev/nvme1n1 mklabel gpt

# Create 132GB partition for data generation
sudo parted -s /dev/nvme1n1 mkpart primary ext4 1MiB 132GiB

# Create raw partition for Exasol (1637GB)
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

# Distribute ubuntu SSH key to exasol user
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCtc95BkOyTV6vi9N6t5IhWl+G58Pj5eGHs8H4mPOSr22rQZaI48pIdTLuo90rTDFkEsoG8aCX5jn7qEChVZ47/jofU/Nk4AoHVlz5jKmgx4l/f4zjATWB0SyhN46KkVV4okYTHlUtE/WTiEa23dxfWDm55PlIaJuOQ0TYH1tiDs2Ncw5LwbT+uEzAq3mAmV0eugzgTcN4vukf0i/2E8J6hP4SM73P+ojj/DhmHt2V/YwdYdq6qIqpIEdZVO0vq/huXhqxlZJID7oxy20XAUhCyngDgiZXzygcssDjYmfcgjgRG/9/bB58WQq7TLaQExaGwIXo0kfdmnvQGcZz7Hgq5 ubuntu@ip-10-0-1-215&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure localhost SSH access to exasol user
ssh-keyscan -H localhost &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
ssh-keyscan -H 127.0.0.1 &gt;&gt; ~/.ssh/known_hosts 2&gt;/dev/null || true
mkdir -p ~/.ssh
touch ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; &#39;SSHEOF&#39;

Host localhost 127.0.0.1
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
chmod 600 ~/.ssh/config

# Generate SSH key pair for exasol user
sudo -u exasol bash -c &#39;mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh &amp;&amp; if [ ! -f ~/.ssh/id_rsa ]; then ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34; -q; fi&#39;

# [All 1 Nodes] Cross-distribute exasol SSH keys for cluster communication
# Collect exasol public keys from all nodes, distribute to all authorized_keys
sudo cat ~exasol/.ssh/id_rsa.pub  # on each node
echo &#39;&lt;KEY&gt;&#39; | sudo tee -a ~exasol/.ssh/authorized_keys &gt; /dev/null
sudo chown exasol:exasol ~exasol/.ssh/authorized_keys &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

# Configure exasol SSH config for cluster nodes
sudo -u exasol bash -c &#39;
mkdir -p ~/.ssh &amp;&amp; chmod 700 ~/.ssh
touch ~/.ssh/config &amp;&amp; chmod 600 ~/.ssh/config
grep -q &#34;Host localhost&#34; ~/.ssh/config 2&gt;/dev/null || cat &gt;&gt; ~/.ssh/config &lt;&lt; SSHEOF

Host localhost 127.0.0.1 &lt;PRIVATE_IP&gt; &lt;PUBLIC_IP&gt;
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
SSHEOF
&#39;

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



#### Clickhouse_new 26.4.4.38 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS431211C2959BCCFB5 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS431211C2959BCCFB5

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS431211C2959BCCFB5 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS431211C2959BCCFB5 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `230g`
- Max threads: `32`
- Max memory usage: `200.0GB`

**Data Directory:** `/data/clickhouse`



#### Clickhouse_old 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Format /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS227301E96BD17BE58 with ext4 filesystem
sudo mkfs.ext4 -F /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS227301E96BD17BE58

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS227301E96BD17BE58 to /data
sudo mount /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS227301E96BD17BE58 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `230g`
- Max threads: `32`
- Max memory usage: `200.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 100
- **Data format:** tbl
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 2
- **Measured runs per query:** 15
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_2026_100g-benchmark.zip
cd exa_vs_ch_2026_100g

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


### Performance Summary

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse_25_10 |   2718.2 |     15 |      2798   |    2820.5 |    102.5 |   2711.6 |   2992   |
| Q01     | clickhouse_26_4  |   2625.1 |     15 |      2522.3 |    2533.5 |     30   |   2507.2 |   2618.9 |
| Q01     | exasol           |    809.9 |     15 |       809.4 |     807.3 |      4   |    799.7 |    811.9 |
| Q02     | clickhouse_25_10 |   1468.2 |     15 |      1292.5 |    1297.6 |     34.4 |   1247.5 |   1373.3 |
| Q02     | clickhouse_26_4  |   3999   |     15 |      4042.5 |    4047.5 |    124.4 |   3873.4 |   4451.2 |
| Q02     | exasol           |     86.2 |     15 |        78.6 |      78.6 |      1.1 |     76.6 |     80.1 |
| Q03     | clickhouse_25_10 |   4982.3 |     15 |      4941.7 |    4970.6 |    145.6 |   4801.5 |   5324   |
| Q03     | clickhouse_26_4  |   1417.3 |     15 |      1400.8 |    1403.8 |      8.7 |   1393.8 |   1421.1 |
| Q03     | exasol           |    354.6 |     15 |       354.8 |     359   |      9.6 |    351.8 |    389   |
| Q04     | clickhouse_25_10 |   2863.2 |     15 |      2632.7 |    2638.7 |    100.3 |   2467.2 |   2796   |
| Q04     | clickhouse_26_4  |   1581.8 |     15 |      1580.8 |    1581.5 |      5.9 |   1569.5 |   1595.5 |
| Q04     | exasol           |     64   |     15 |        62.4 |      62.5 |      0.8 |     61.4 |     64.6 |
| Q05     | clickhouse_25_10 |  13123.3 |     15 |     12833.6 |   12719.9 |    612.2 |  11604.8 |  13437.2 |
| Q05     | clickhouse_26_4  |   1793.9 |     15 |      1771.9 |    1776.8 |     15.2 |   1764.7 |   1817.9 |
| Q05     | exasol           |    276.3 |     15 |       221.9 |     222   |      1.6 |    219.7 |    224.4 |
| Q06     | clickhouse_25_10 |    927.7 |     15 |       217.6 |     220   |      5.7 |    213.9 |    233.7 |
| Q06     | clickhouse_26_4  |    151.2 |     15 |       145.4 |     145.8 |      1.1 |    144.6 |    148.9 |
| Q06     | exasol           |     43.1 |     15 |        43   |      43   |      0.4 |     42.2 |     43.9 |
| Q07     | clickhouse_25_10 |   6947.1 |     15 |      5390.3 |    5361.9 |    223.9 |   5071.9 |   5745.6 |
| Q07     | clickhouse_26_4  |   1123.3 |     15 |      1108.7 |    1114.4 |     16.1 |   1097.2 |   1152.8 |
| Q07     | exasol           |    292.4 |     15 |       291.3 |     290.8 |      2.7 |    284.1 |    294.9 |
| Q08     | clickhouse_25_10 |   8808   |     15 |     10068   |   10074.7 |    452   |   9297.1 |  10971.1 |
| Q08     | clickhouse_26_4  |   1619.8 |     15 |      1621.3 |    1624   |      8   |   1611.8 |   1636.2 |
| Q08     | exasol           |     80.2 |     15 |        81   |      80.9 |      0.9 |     79.4 |     82.2 |
| Q09     | clickhouse_25_10 |  18591   |     15 |     17520   |   17405.5 |   1147.6 |  14629.1 |  18591.3 |
| Q09     | clickhouse_26_4  |   5154.5 |     15 |      5223.4 |    5222.2 |     25   |   5181   |   5264.7 |
| Q09     | exasol           |   1026.7 |     15 |      1022.9 |    1031.1 |     29   |   1018.5 |   1134.4 |
| Q10     | clickhouse_25_10 |   4136.9 |     15 |      3457.4 |    3423.9 |    118.5 |   3235.1 |   3590.5 |
| Q10     | clickhouse_26_4  |   2372.6 |     15 |      2360.4 |    2364.4 |     14.3 |   2347   |   2393.5 |
| Q10     | exasol           |    591.6 |     15 |       590.9 |     591.6 |      5.7 |    583.5 |    603.9 |
| Q11     | clickhouse_25_10 |    936.3 |     15 |       675.8 |     682.7 |     26.3 |    653.4 |    740   |
| Q11     | clickhouse_26_4  |    478.6 |     15 |       436.8 |     433   |     24.1 |    387.8 |    471.6 |
| Q11     | exasol           |    155.8 |     15 |       156.5 |     155.9 |      3.9 |    148.2 |    161.8 |
| Q12     | clickhouse_25_10 |   1827.8 |     15 |       851.9 |     850.3 |     13.4 |    830.2 |    870.6 |
| Q12     | clickhouse_26_4  |    864.5 |     15 |       802.1 |     805.7 |      9.6 |    797.7 |    828.7 |
| Q12     | exasol           |     88.5 |     15 |        86.2 |      86.3 |      1.1 |     84.6 |     88.6 |
| Q13     | clickhouse_25_10 |   5951   |     15 |      5880.4 |    5883.9 |    159.9 |   5644.2 |   6127.9 |
| Q13     | clickhouse_26_4  |   2452   |     15 |      2107.8 |    2125.7 |     47.6 |   2089.8 |   2273.8 |
| Q13     | exasol           |    694.5 |     15 |       697.1 |     698.4 |      5.6 |    692.3 |    712.6 |
| Q14     | clickhouse_25_10 |    257.3 |     15 |       263.3 |     263   |      6.3 |    253.7 |    274.4 |
| Q14     | clickhouse_26_4  |    207.2 |     15 |       202.1 |     204.8 |      6.4 |    200.5 |    219.2 |
| Q14     | exasol           |    107.3 |     15 |        87.8 |      88   |      1.5 |     85.5 |     91.1 |
| Q15     | clickhouse_25_10 |    434.3 |     15 |       394.8 |     400.4 |     20.1 |    379.2 |    445.3 |
| Q15     | clickhouse_26_4  |    322.4 |     15 |       320.6 |     319.4 |     18   |    282.9 |    346.8 |
| Q15     | exasol           |    385.5 |     15 |       391.4 |     401.2 |     26.3 |    375.7 |    464.2 |
| Q16     | clickhouse_25_10 |    540.9 |     15 |       524.6 |     523.5 |     16.7 |    478.5 |    549.6 |
| Q16     | clickhouse_26_4  |    422.9 |     15 |       422.7 |     422.8 |      7.9 |    403.9 |    437.4 |
| Q16     | exasol           |    487.5 |     15 |       471.8 |     471.3 |      4.9 |    459.2 |    478.9 |
| Q17     | clickhouse_25_10 |   8347.5 |     15 |      8405.3 |    8410.8 |    130.8 |   8175.5 |   8619   |
| Q17     | clickhouse_26_4  |   1511   |     15 |      1489.2 |    1490.9 |      8.2 |   1481.6 |   1507.6 |
| Q17     | exasol           |     30.9 |     15 |        30.3 |      30.3 |      0.4 |     29.3 |     31   |
| Q18     | clickhouse_25_10 |   7910.5 |     15 |      7670.3 |    7646.8 |    178.8 |   7334.6 |   7975.9 |
| Q18     | clickhouse_26_4  |   5826.2 |     15 |      5577.8 |    5576.4 |     39.7 |   5509.7 |   5674.8 |
| Q18     | exasol           |    671.7 |     15 |       661.9 |     663.7 |     10.6 |    652.2 |    691.9 |
| Q19     | clickhouse_25_10 |   3007.3 |     15 |      2902.6 |    2926.2 |     75.1 |   2796.1 |   3065.7 |
| Q19     | clickhouse_26_4  |   1544.2 |     15 |      1507.3 |    1512.3 |     13.5 |   1498.3 |   1537.5 |
| Q19     | exasol           |     27.5 |     15 |        27.3 |      27.2 |      0.2 |     26.9 |     27.5 |
| Q20     | clickhouse_25_10 |    654.6 |     15 |       617.9 |     618.1 |     15.7 |    595.4 |    650.1 |
| Q20     | clickhouse_26_4  |    465.1 |     15 |       457.1 |     459.4 |      8.1 |    450.9 |    484.1 |
| Q20     | exasol           |    306.1 |     15 |       324.2 |     308.3 |     19.6 |    285.8 |    327.3 |
| Q21     | clickhouse_25_10 |  55935.1 |     15 |     57752.3 |   57043.3 |   4280.2 |  47777.5 |  62675.1 |
| Q21     | clickhouse_26_4  |  75767.1 |     15 |     76654.9 |   76592.8 |    502.4 |  75853.5 |  77884.5 |
| Q21     | exasol           |    443.2 |     15 |       441.2 |     448.6 |     32.5 |    436.1 |    565.9 |
| Q22     | clickhouse_25_10 |    876.8 |     15 |       830.7 |     847.7 |     49.7 |    776   |    954.4 |
| Q22     | clickhouse_26_4  |    695   |     15 |       682.4 |     680.6 |     25.1 |    621.1 |    719.2 |
| Q22     | exasol           |     92.9 |     15 |        92.2 |      92.1 |      0.7 |     91   |     93.2 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | clickhouse_25_10  | exasol              |        2798   |           809.4 |    0.29 |      3.46 | True     |
| Q02     | clickhouse_25_10  | exasol              |        1292.5 |            78.6 |    0.06 |     16.44 | True     |
| Q03     | clickhouse_25_10  | exasol              |        4941.7 |           354.8 |    0.07 |     13.93 | True     |
| Q04     | clickhouse_25_10  | exasol              |        2632.7 |            62.4 |    0.02 |     42.19 | True     |
| Q05     | clickhouse_25_10  | exasol              |       12833.6 |           221.9 |    0.02 |     57.84 | True     |
| Q06     | clickhouse_25_10  | exasol              |         217.6 |            43   |    0.2  |      5.06 | True     |
| Q07     | clickhouse_25_10  | exasol              |        5390.3 |           291.3 |    0.05 |     18.5  | True     |
| Q08     | clickhouse_25_10  | exasol              |       10068   |            81   |    0.01 |    124.3  | True     |
| Q09     | clickhouse_25_10  | exasol              |       17520   |          1022.9 |    0.06 |     17.13 | True     |
| Q10     | clickhouse_25_10  | exasol              |        3457.4 |           590.9 |    0.17 |      5.85 | True     |
| Q11     | clickhouse_25_10  | exasol              |         675.8 |           156.5 |    0.23 |      4.32 | True     |
| Q12     | clickhouse_25_10  | exasol              |         851.9 |            86.2 |    0.1  |      9.88 | True     |
| Q13     | clickhouse_25_10  | exasol              |        5880.4 |           697.1 |    0.12 |      8.44 | True     |
| Q14     | clickhouse_25_10  | exasol              |         263.3 |            87.8 |    0.33 |      3    | True     |
| Q15     | clickhouse_25_10  | exasol              |         394.8 |           391.4 |    0.99 |      1.01 | True     |
| Q16     | clickhouse_25_10  | exasol              |         524.6 |           471.8 |    0.9  |      1.11 | True     |
| Q17     | clickhouse_25_10  | exasol              |        8405.3 |            30.3 |    0    |    277.4  | True     |
| Q18     | clickhouse_25_10  | exasol              |        7670.3 |           661.9 |    0.09 |     11.59 | True     |
| Q19     | clickhouse_25_10  | exasol              |        2902.6 |            27.3 |    0.01 |    106.32 | True     |
| Q20     | clickhouse_25_10  | exasol              |         617.9 |           324.2 |    0.52 |      1.91 | True     |
| Q21     | clickhouse_25_10  | exasol              |       57752.3 |           441.2 |    0.01 |    130.9  | True     |
| Q22     | clickhouse_25_10  | exasol              |         830.7 |            92.2 |    0.11 |      9.01 | True     |
| Q01     | clickhouse_25_10  | clickhouse_26_4     |        2798   |          2522.3 |    0.9  |      1.11 | True     |
| Q02     | clickhouse_25_10  | clickhouse_26_4     |        1292.5 |          4042.5 |    3.13 |      0.32 | False    |
| Q03     | clickhouse_25_10  | clickhouse_26_4     |        4941.7 |          1400.8 |    0.28 |      3.53 | True     |
| Q04     | clickhouse_25_10  | clickhouse_26_4     |        2632.7 |          1580.8 |    0.6  |      1.67 | True     |
| Q05     | clickhouse_25_10  | clickhouse_26_4     |       12833.6 |          1771.9 |    0.14 |      7.24 | True     |
| Q06     | clickhouse_25_10  | clickhouse_26_4     |         217.6 |           145.4 |    0.67 |      1.5  | True     |
| Q07     | clickhouse_25_10  | clickhouse_26_4     |        5390.3 |          1108.7 |    0.21 |      4.86 | True     |
| Q08     | clickhouse_25_10  | clickhouse_26_4     |       10068   |          1621.3 |    0.16 |      6.21 | True     |
| Q09     | clickhouse_25_10  | clickhouse_26_4     |       17520   |          5223.4 |    0.3  |      3.35 | True     |
| Q10     | clickhouse_25_10  | clickhouse_26_4     |        3457.4 |          2360.4 |    0.68 |      1.46 | True     |
| Q11     | clickhouse_25_10  | clickhouse_26_4     |         675.8 |           436.8 |    0.65 |      1.55 | True     |
| Q12     | clickhouse_25_10  | clickhouse_26_4     |         851.9 |           802.1 |    0.94 |      1.06 | True     |
| Q13     | clickhouse_25_10  | clickhouse_26_4     |        5880.4 |          2107.8 |    0.36 |      2.79 | True     |
| Q14     | clickhouse_25_10  | clickhouse_26_4     |         263.3 |           202.1 |    0.77 |      1.3  | True     |
| Q15     | clickhouse_25_10  | clickhouse_26_4     |         394.8 |           320.6 |    0.81 |      1.23 | True     |
| Q16     | clickhouse_25_10  | clickhouse_26_4     |         524.6 |           422.7 |    0.81 |      1.24 | True     |
| Q17     | clickhouse_25_10  | clickhouse_26_4     |        8405.3 |          1489.2 |    0.18 |      5.64 | True     |
| Q18     | clickhouse_25_10  | clickhouse_26_4     |        7670.3 |          5577.8 |    0.73 |      1.38 | True     |
| Q19     | clickhouse_25_10  | clickhouse_26_4     |        2902.6 |          1507.3 |    0.52 |      1.93 | True     |
| Q20     | clickhouse_25_10  | clickhouse_26_4     |         617.9 |           457.1 |    0.74 |      1.35 | True     |
| Q21     | clickhouse_25_10  | clickhouse_26_4     |       57752.3 |         76654.9 |    1.33 |      0.75 | False    |
| Q22     | clickhouse_25_10  | clickhouse_26_4     |         830.7 |           682.4 |    0.82 |      1.22 | True     |


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

![Runtime Distribution (CDF)](attachments/figures/query_runtime_cdf.png)

*Cumulative distribution function showing the probability that a query completes within a given time. Curves closer to the left indicate better performance.*

**Interactive version:** [View interactive chart](attachments/figures/query_runtime_cdf.html) for interactive exploration.

> **Note:** All visualizations are available as both static PNG images (shown above) and interactive HTML charts (linked). The interactive versions allow you to zoom, pan, and hover for detailed information.

### Key Observations

**exasol:**
- Median runtime: 254.2ms
- Average runtime: 319.9ms
- Fastest query: 26.9ms
- Slowest query: 1134.4ms

**clickhouse_26_4:**
- Median runtime: 1500.0ms
- Average runtime: 5110.8ms
- Fastest query: 144.6ms
- Slowest query: 77884.5ms

**clickhouse_25_10:**
- Median runtime: 2876.5ms
- Average runtime: 6683.2ms
- Fastest query: 213.9ms
- Slowest query: 62675.1ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_2026_100g-benchmark.zip`](exa_vs_ch_2026_100g-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 32 logical cores
- **Memory:** 247.7GB RAM
- **Storage:** NVMe SSD recommended for optimal performance
- **OS:** Linux

### Configuration Files

The exact configuration used for this benchmark is available at:
[`attachments/config.yaml`](attachments/config.yaml)

### System Specifications

**Clickhouse_25_10 25.10.2.65:**
- **Setup method:** preinstalled
- **Data directory:** 
- **Applied configurations:**
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000

**Clickhouse_26_4 26.4.4.38:**
- **Setup method:** preinstalled
- **Data directory:** 
- **Applied configurations:**
  - clickhouse_settings: {&#39;use_top_k_dynamic_filtering&#39;: 1, &#39;use_skip_indexes_for_top_k&#39;: 1, &#39;optimize_aggregation_in_order&#39;: 1, &#39;query_plan_convert_join_to_in&#39;: 1, &#39;enable_join_runtime_filters&#39;: 1}
  - memory_limit: 230g
  - max_threads: 32
  - max_memory_usage: 200000000000
  - max_bytes_before_external_group_by: 100000000000
  - max_bytes_before_external_sort: 100000000000

**Exasol 2026.1.0:**
- **Setup method:** preinstalled
- **Data directory:** 
- **Applied configurations:**
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 2 warmup run(s) per query (sequential, results discarded)
- 15 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts