# Exasol 2026.1 vs ClickHouse 25.10 vs 26.4 — TPC-H SF30

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2026-06-21 17:44:34

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 3 database systems:
- **exasol**
- **clickhouse_26_4**
- **clickhouse_25_10**

**Key Findings:**
- exasol was the fastest overall with 183.2ms median runtime
- clickhouse_25_10 was 8.8x slower- Tested 462 total query executions across 22 different TPC-H queries

## Systems Under Test

### Clickhouse_25_10 25.10.2.65

**Software Configuration:**
- **Database:** clickhouse 25.10.2.65
- **Setup method:** preinstalled


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-184

### Clickhouse_26_4 26.4.4.38

**Software Configuration:**
- **Database:** clickhouse 26.4.4.38
- **Setup method:** preinstalled


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-57

### Exasol 2026.1.0

**Software Configuration:**
- **Database:** exasol 2026.1.0
- **Setup method:** preinstalled
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-201


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Clickhouse_25_10 Instance:** r5d.4xlarge
- **Clickhouse_26_4 Instance:** r5d.4xlarge
- **Exasol Instance:** r5d.4xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2026.1.0 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/nvme1n1
sudo wipefs -a /dev/nvme1n1 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/nvme2n1
sudo wipefs -a /dev/nvme2n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme1n1
sudo mdadm --zero-superblock /dev/nvme1n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme2n1
sudo mdadm --zero-superblock /dev/nvme2n1 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/nvme1n1 /dev/nvme2n1

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Create GPT partition table
sudo parted -s /dev/md0 mklabel gpt

# Create 48GB partition for data generation
sudo parted -s /dev/md0 mkpart primary ext4 1MiB 48GiB

# Create raw partition for Exasol (510GB)
sudo parted -s /dev/md0 mkpart primary 48GiB 100%

# Format /dev/md0p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0p1

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0p1 to /data
sudo mount /dev/md0p1 /data

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
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDIbKS3T0R0Z84crhgcjG4MDctj9+ZG16L9TiT8fBi9kwrvGhIcqnpBu8tTuEUyLgNnUxRWdt3Spbp3pTNSrhKIPL+HgT4dYJRkCyfJuyHamSlyvUnF+HJAnRhQfvOP0ftiHhIHzXQXfD+q7wY7yBEDt7vcS46j3uQuIAEgV14N7R0zUaaXe7VoWAQDd7uKv7/+u1+hV8Fm4ERmMiLSHv2B09wm0TgNzjjYxq1vJ0JS9E1//4bxx5NfS1ntbFAqR2XlfT0PL983pIfWUUCBe4iMaZOqM/mJ93BiQHbLdh0MPV7AeI5/VqYaET3e9FmqikqtGd+XnZOFxSVQKsr8bWxZ ubuntu@ip-10-0-1-201&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

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
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2341BFF4FE5314358
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2341BFF4FE5314358 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2F59D26DE14015E8E
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2F59D26DE14015E8E 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2341BFF4FE5314358
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2341BFF4FE5314358 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2F59D26DE14015E8E
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2F59D26DE14015E8E 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2341BFF4FE5314358 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS2F59D26DE14015E8E

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `100g`
- Max threads: `16`
- Max memory usage: `100.0GB`

**Data Directory:** `/data/clickhouse`



#### Clickhouse_old 25.10.2.65 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222741C863E8693E7
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222741C863E8693E7 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3954A97A36D215063
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3954A97A36D215063 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222741C863E8693E7
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222741C863E8693E7 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3954A97A36D215063
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3954A97A36D215063 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS222741C863E8693E7 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS3954A97A36D215063

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create clickhouse data directory
sudo mkdir -p /data/clickhouse &amp;&amp; sudo chmod 1777 /data/clickhouse

```


**Tuning Parameters:**
- Memory limit: `100g`
- Max threads: `16`
- Max memory usage: `100.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 30
- **Data format:** tbl
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 7
- **Execution mode:** Sequential (single connection)

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_2026_30g-benchmark.zip
cd exa_vs_ch_2026_30g

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
| Q01     | clickhouse_25_10 |   1648.4 |      7 |      1634.9 |    1637.1 |     10.8 |   1624.5 |   1653.2 |
| Q01     | clickhouse_26_4  |   1509.2 |      7 |      1441.7 |    1453.3 |     33.4 |   1417.6 |   1502.4 |
| Q01     | exasol           |    648.3 |      7 |       623.2 |     623.7 |      1.5 |    621.8 |    626.4 |
| Q02     | clickhouse_25_10 |    802.6 |      7 |       595.7 |     609.5 |     25   |    592.4 |    660.6 |
| Q02     | clickhouse_26_4  |   1314.2 |      7 |      1263.8 |    1273.6 |     36.8 |   1232.9 |   1346.9 |
| Q02     | exasol           |     77.3 |      7 |        54.4 |      54.4 |      1.4 |     52.2 |     56.2 |
| Q03     | clickhouse_25_10 |   2733.4 |      7 |      2471.8 |    2485.2 |     36.5 |   2431.9 |   2540.2 |
| Q03     | clickhouse_26_4  |    855.8 |      7 |       846.2 |     846.1 |     15.6 |    824.6 |    867.7 |
| Q03     | exasol           |    277.4 |      7 |       254.4 |     253.6 |      1.7 |    250.6 |    255.2 |
| Q04     | clickhouse_25_10 |   1280.6 |      7 |      1221.2 |    1222.7 |      8.5 |   1210.2 |   1234.2 |
| Q04     | clickhouse_26_4  |   1032.5 |      7 |      1021.9 |    1028.7 |     23.3 |   1015.6 |   1080.8 |
| Q04     | exasol           |     50.8 |      7 |        48.4 |      48.6 |      0.5 |     48.1 |     49.7 |
| Q05     | clickhouse_25_10 |   6056.1 |      7 |      5475.7 |    5463.2 |     90.4 |   5309.4 |   5561   |
| Q05     | clickhouse_26_4  |   1273.3 |      7 |      1277.7 |    1277.6 |     13   |   1262.6 |   1299.3 |
| Q05     | exasol           |    224.7 |      7 |       172.2 |     172.5 |      0.8 |    171.5 |    174   |
| Q06     | clickhouse_25_10 |    285.7 |      7 |       121.2 |     122.5 |      2.7 |    119.8 |    126.8 |
| Q06     | clickhouse_26_4  |    121.9 |      7 |       114.9 |     115.1 |      2.9 |    111.7 |    119.4 |
| Q06     | exasol           |     33.5 |      7 |        33   |      42   |     23.8 |     32.5 |     96   |
| Q07     | clickhouse_25_10 |   3073.2 |      7 |      2825.6 |    2791.7 |     81.5 |   2629.7 |   2875   |
| Q07     | clickhouse_26_4  |    726.7 |      7 |       701.7 |     715.6 |     46.8 |    683.2 |    820.4 |
| Q07     | exasol           |    265.8 |      7 |       211.4 |     211.5 |      1.3 |    209.7 |    213   |
| Q08     | clickhouse_25_10 |   5796.8 |      7 |      5720.4 |    5728.3 |     31.2 |   5686.7 |   5765.9 |
| Q08     | clickhouse_26_4  |   1133.4 |      7 |      1141   |    1139   |     11.8 |   1120.3 |   1158.1 |
| Q08     | exasol           |     95.5 |      7 |        64.9 |      64.7 |      1.3 |     63.3 |     66.7 |
| Q09     | clickhouse_25_10 |   8313.7 |      7 |      7774.5 |    7720.9 |    101.3 |   7568.3 |   7828.2 |
| Q09     | clickhouse_26_4  |   3007.3 |      7 |      2950.3 |    2952   |     32.3 |   2916.4 |   3001.7 |
| Q09     | exasol           |    811.2 |      7 |       761.5 |     762.8 |      3.8 |    759.2 |    769.4 |
| Q10     | clickhouse_25_10 |   1918.3 |      7 |      1626.3 |    1641.5 |     41.8 |   1601   |   1718.8 |
| Q10     | clickhouse_26_4  |   1529.3 |      7 |      1474.4 |    1480.2 |     15.8 |   1463.5 |   1503.8 |
| Q10     | exasol           |    414.4 |      7 |       379.7 |     379.5 |      6.1 |    371.4 |    390.3 |
| Q11     | clickhouse_25_10 |    424.7 |      7 |       363.8 |     369.7 |     11.8 |    361   |    394.1 |
| Q11     | clickhouse_26_4  |    274.7 |      7 |       238   |     242.2 |     10   |    232.5 |    260   |
| Q11     | exasol           |    140.2 |      7 |       128.9 |     131.3 |      8.4 |    124.2 |    149.2 |
| Q12     | clickhouse_25_10 |   1316   |      7 |       526.9 |     529   |     12.9 |    514.3 |    547.1 |
| Q12     | clickhouse_26_4  |    640.5 |      7 |       501.4 |     505.8 |     15.6 |    488.1 |    526.4 |
| Q12     | exasol           |     95.5 |      7 |        64.6 |      64.8 |      0.6 |     64.3 |     65.8 |
| Q13     | clickhouse_25_10 |   2609.4 |      7 |      2426.6 |    2401   |    112.8 |   2166.9 |   2504   |
| Q13     | clickhouse_26_4  |   1479   |      7 |      1303.5 |    1285.2 |     44.6 |   1235.3 |   1338.7 |
| Q13     | exasol           |    605.3 |      7 |       567.5 |     567.9 |      2.7 |    564.8 |    573   |
| Q14     | clickhouse_25_10 |    140.7 |      7 |       133.5 |     131.9 |      7.6 |    122.8 |    143.2 |
| Q14     | clickhouse_26_4  |    142.6 |      7 |       133.9 |     133.9 |      1.7 |    131.4 |    136.1 |
| Q14     | exasol           |     81.9 |      7 |        61.8 |      61.7 |      0.8 |     60.9 |     62.9 |
| Q15     | clickhouse_25_10 |    201.2 |      7 |       155.7 |     158.8 |      8.6 |    152.5 |    177.1 |
| Q15     | clickhouse_26_4  |    197.5 |      7 |       164.9 |     177.6 |     21.7 |    159.7 |    221   |
| Q15     | exasol           |    214.4 |      7 |       213   |     213.2 |      4.7 |    205   |    220.9 |
| Q16     | clickhouse_25_10 |    274.9 |      7 |       280.3 |     286.6 |     14.8 |    275.6 |    319   |
| Q16     | clickhouse_26_4  |    303.4 |      7 |       292.8 |     293.6 |     10.9 |    282.2 |    316.3 |
| Q16     | exasol           |    422.4 |      7 |       388.3 |     390.1 |     12   |    376.8 |    414.3 |
| Q17     | clickhouse_25_10 |   2846.6 |      7 |      2633.7 |    2616   |     42.4 |   2534.8 |   2660.9 |
| Q17     | clickhouse_26_4  |    836.5 |      7 |       847   |     849   |      9.8 |    838.4 |    865.6 |
| Q17     | exasol           |     25.8 |      7 |        22.9 |      22.8 |      0.3 |     22.3 |     23.1 |
| Q18     | clickhouse_25_10 |   2636.2 |      7 |      2570.6 |    2582.2 |     50.7 |   2511.7 |   2652.5 |
| Q18     | clickhouse_26_4  |   3078.6 |      7 |      2794.5 |    2812.8 |     49.3 |   2758.3 |   2887.3 |
| Q18     | exasol           |    431.9 |      7 |       429.4 |     429.2 |      1.2 |    427.4 |    431.2 |
| Q19     | clickhouse_25_10 |   1580.1 |      7 |      1585.6 |    1594.3 |     18.3 |   1579.3 |   1621.7 |
| Q19     | clickhouse_26_4  |   1149.6 |      7 |      1128.1 |    1126.7 |     14.7 |   1109.7 |   1148   |
| Q19     | exasol           |     36.2 |      7 |        25.4 |      32   |     18   |     24.4 |     72.9 |
| Q20     | clickhouse_25_10 |    257.1 |      7 |       242.9 |     235.2 |     13   |    219.7 |    247.3 |
| Q20     | clickhouse_26_4  |    354.6 |      7 |       313.5 |     316.1 |      6   |    310.6 |    327.9 |
| Q20     | exasol           |    292.6 |      7 |       232.6 |     227.6 |     15.5 |    192.5 |    235.5 |
| Q21     | clickhouse_25_10 |  21564   |      7 |     21041.8 |   21141.8 |    205.6 |  20936.6 |  21538.9 |
| Q21     | clickhouse_26_4  |  31652.3 |      7 |     32167.3 |   31969.2 |    564   |  30912.3 |  32486.7 |
| Q21     | exasol           |    407.5 |      7 |       311.6 |     312.1 |      1.5 |    310.4 |    314.3 |
| Q22     | clickhouse_25_10 |    378.2 |      7 |       476.5 |     475.8 |      7.3 |    467.1 |    484.7 |
| Q22     | clickhouse_26_4  |    400   |      7 |       468.2 |     445.4 |     47.7 |    381.9 |    490.1 |
| Q22     | exasol           |     87   |      7 |        74.1 |      74   |      0.5 |     73.3 |     74.7 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | clickhouse_25_10  | exasol              |        1634.9 |           623.2 |    0.38 |      2.62 | True     |
| Q02     | clickhouse_25_10  | exasol              |         595.7 |            54.4 |    0.09 |     10.95 | True     |
| Q03     | clickhouse_25_10  | exasol              |        2471.8 |           254.4 |    0.1  |      9.72 | True     |
| Q04     | clickhouse_25_10  | exasol              |        1221.2 |            48.4 |    0.04 |     25.23 | True     |
| Q05     | clickhouse_25_10  | exasol              |        5475.7 |           172.2 |    0.03 |     31.8  | True     |
| Q06     | clickhouse_25_10  | exasol              |         121.2 |            33   |    0.27 |      3.67 | True     |
| Q07     | clickhouse_25_10  | exasol              |        2825.6 |           211.4 |    0.07 |     13.37 | True     |
| Q08     | clickhouse_25_10  | exasol              |        5720.4 |            64.9 |    0.01 |     88.14 | True     |
| Q09     | clickhouse_25_10  | exasol              |        7774.5 |           761.5 |    0.1  |     10.21 | True     |
| Q10     | clickhouse_25_10  | exasol              |        1626.3 |           379.7 |    0.23 |      4.28 | True     |
| Q11     | clickhouse_25_10  | exasol              |         363.8 |           128.9 |    0.35 |      2.82 | True     |
| Q12     | clickhouse_25_10  | exasol              |         526.9 |            64.6 |    0.12 |      8.16 | True     |
| Q13     | clickhouse_25_10  | exasol              |        2426.6 |           567.5 |    0.23 |      4.28 | True     |
| Q14     | clickhouse_25_10  | exasol              |         133.5 |            61.8 |    0.46 |      2.16 | True     |
| Q15     | clickhouse_25_10  | exasol              |         155.7 |           213   |    1.37 |      0.73 | False    |
| Q16     | clickhouse_25_10  | exasol              |         280.3 |           388.3 |    1.39 |      0.72 | False    |
| Q17     | clickhouse_25_10  | exasol              |        2633.7 |            22.9 |    0.01 |    115.01 | True     |
| Q18     | clickhouse_25_10  | exasol              |        2570.6 |           429.4 |    0.17 |      5.99 | True     |
| Q19     | clickhouse_25_10  | exasol              |        1585.6 |            25.4 |    0.02 |     62.43 | True     |
| Q20     | clickhouse_25_10  | exasol              |         242.9 |           232.6 |    0.96 |      1.04 | True     |
| Q21     | clickhouse_25_10  | exasol              |       21041.8 |           311.6 |    0.01 |     67.53 | True     |
| Q22     | clickhouse_25_10  | exasol              |         476.5 |            74.1 |    0.16 |      6.43 | True     |
| Q01     | clickhouse_25_10  | clickhouse_26_4     |        1634.9 |          1441.7 |    0.88 |      1.13 | True     |
| Q02     | clickhouse_25_10  | clickhouse_26_4     |         595.7 |          1263.8 |    2.12 |      0.47 | False    |
| Q03     | clickhouse_25_10  | clickhouse_26_4     |        2471.8 |           846.2 |    0.34 |      2.92 | True     |
| Q04     | clickhouse_25_10  | clickhouse_26_4     |        1221.2 |          1021.9 |    0.84 |      1.2  | True     |
| Q05     | clickhouse_25_10  | clickhouse_26_4     |        5475.7 |          1277.7 |    0.23 |      4.29 | True     |
| Q06     | clickhouse_25_10  | clickhouse_26_4     |         121.2 |           114.9 |    0.95 |      1.05 | True     |
| Q07     | clickhouse_25_10  | clickhouse_26_4     |        2825.6 |           701.7 |    0.25 |      4.03 | True     |
| Q08     | clickhouse_25_10  | clickhouse_26_4     |        5720.4 |          1141   |    0.2  |      5.01 | True     |
| Q09     | clickhouse_25_10  | clickhouse_26_4     |        7774.5 |          2950.3 |    0.38 |      2.64 | True     |
| Q10     | clickhouse_25_10  | clickhouse_26_4     |        1626.3 |          1474.4 |    0.91 |      1.1  | True     |
| Q11     | clickhouse_25_10  | clickhouse_26_4     |         363.8 |           238   |    0.65 |      1.53 | True     |
| Q12     | clickhouse_25_10  | clickhouse_26_4     |         526.9 |           501.4 |    0.95 |      1.05 | True     |
| Q13     | clickhouse_25_10  | clickhouse_26_4     |        2426.6 |          1303.5 |    0.54 |      1.86 | True     |
| Q14     | clickhouse_25_10  | clickhouse_26_4     |         133.5 |           133.9 |    1    |      1    | False    |
| Q15     | clickhouse_25_10  | clickhouse_26_4     |         155.7 |           164.9 |    1.06 |      0.94 | False    |
| Q16     | clickhouse_25_10  | clickhouse_26_4     |         280.3 |           292.8 |    1.04 |      0.96 | False    |
| Q17     | clickhouse_25_10  | clickhouse_26_4     |        2633.7 |           847   |    0.32 |      3.11 | True     |
| Q18     | clickhouse_25_10  | clickhouse_26_4     |        2570.6 |          2794.5 |    1.09 |      0.92 | False    |
| Q19     | clickhouse_25_10  | clickhouse_26_4     |        1585.6 |          1128.1 |    0.71 |      1.41 | True     |
| Q20     | clickhouse_25_10  | clickhouse_26_4     |         242.9 |           313.5 |    1.29 |      0.77 | False    |
| Q21     | clickhouse_25_10  | clickhouse_26_4     |       21041.8 |         32167.3 |    1.53 |      0.65 | False    |
| Q22     | clickhouse_25_10  | clickhouse_26_4     |         476.5 |           468.2 |    0.98 |      1.02 | True     |


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
- Median runtime: 183.2ms
- Average runtime: 233.6ms
- Fastest query: 22.3ms
- Slowest query: 769.4ms

**clickhouse_26_4:**
- Median runtime: 941.7ms
- Average runtime: 2383.6ms
- Fastest query: 111.7ms
- Slowest query: 32486.7ms

**clickhouse_25_10:**
- Median runtime: 1611.6ms
- Average runtime: 2815.7ms
- Fastest query: 119.8ms
- Slowest query: 21538.9ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_2026_30g-benchmark.zip`](exa_vs_ch_2026_30g-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 16 logical cores
- **Memory:** 124.4GB RAM
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
- 1 warmup run(s) per query (sequential, results discarded)
- 7 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts