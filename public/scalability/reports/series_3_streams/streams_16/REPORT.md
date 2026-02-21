# Streamlined Scalability - Stream Scaling (16 Streams)

**Author:** Benchmark Team
**Environment:** aws / eu-west-1 / r6id.16xlarge
**Date:** 2026-02-17 17:35:56

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
- exasol was the fastest overall with 387.1ms median runtime
- trino was 50.6x slower- Tested 550 total query executions across 22 different TPC-H queries
- **Execution mode:** Multiuser with 16 concurrent streams (randomized distribution)

## Systems Under Test

### Exasol 2025.2.0

**Software Configuration:**
- **Database:** exasol 2025.2.0
- **Setup method:** installer
- **Data device:** /dev/exasol.storage


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.16xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 64 vCPUs
- **Memory:** 495.8GB RAM
- **Hostname:** ip-10-0-1-215

### Clickhouse 26.1.3.52

**Software Configuration:**
- **Database:** clickhouse 26.1.3.52
- **Setup method:** native
- **Data directory:** /data/clickhouse


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.16xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 64 vCPUs
- **Memory:** 495.8GB RAM
- **Hostname:** ip-10-0-1-184

### Trino 479

**Software Configuration:**
- **Database:** trino 479
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.16xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 64 vCPUs
- **Memory:** 495.8GB RAM
- **Hostname:** ip-10-0-1-107

### Starrocks 4.0.6

**Software Configuration:**
- **Database:** starrocks 4.0.6
- **Setup method:** native


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.16xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 64 vCPUs
- **Memory:** 495.8GB RAM
- **Hostname:** ip-10-0-1-153

### Duckdb 1.4.4

**Software Configuration:**
- **Database:** duckdb 1.4.4
- **Setup method:** native
- **Data directory:** /data/duckdb


**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r6id.16xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8375C CPU @ 2.90GHz
- **CPU Cores:** 64 vCPUs
- **Memory:** 495.8GB RAM
- **Hostname:** ip-10-0-1-180


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r6id.16xlarge
- **Clickhouse Instance:** r6id.16xlarge
- **Trino Instance:** r6id.16xlarge
- **Starrocks Instance:** r6id.16xlarge
- **Duckdb Instance:** r6id.16xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.2.0 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/nvme2n1
sudo wipefs -a /dev/nvme2n1 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/nvme1n1
sudo wipefs -a /dev/nvme1n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme2n1
sudo mdadm --zero-superblock /dev/nvme2n1 2&gt;/dev/null || true

# Clear RAID superblock on /dev/nvme1n1
sudo mdadm --zero-superblock /dev/nvme1n1 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/nvme2n1 /dev/nvme1n1

# Wait for RAID array /dev/md0 to be ready
sudo mdadm --wait /dev/md0 2&gt;/dev/null || true

# Create mdadm configuration directory
sudo mkdir -p /etc/mdadm

# Save RAID configuration
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf

# Create GPT partition table
sudo parted -s /dev/md0 mklabel gpt

# Create 70GB partition for data generation
sudo parted -s /dev/md0 mkpart primary ext4 1MiB 70GiB

# Create raw partition for Exasol (3468GB)
sudo parted -s /dev/md0 mkpart primary 70GiB 100%

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
sudo mkdir -p ~exasol/.ssh &amp;&amp; echo &#39;ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCuR2MkdmOBISnXFODvvpjnjifcZe/xKAIC+E8AMOtkLwyuElz4m6V/p4vMUWOkbkvfPKMVL/An6vqRHXjH88wJuA59FYjAaXauEoYyYomNcxEFLbAtm8TTAisW2RcY+xDtZAx9wGiNgDmMNRZFaGVK6+nRNh9ZPZzD60tyLobZVASdUE0zZ5H5Cov2g1fAe6MCp62/1PpkWmXMTwXns6zoow/8Vtd0MC01OZjBAhb7Eef0GMSF8sSjJb5SVJ+SPR8Ztulxv07I1Z8/GXUSXaP9E+4NkpBBhVQrpC/2hrqQfTLwapKdzCP0NsLR4qJfKlAfu/RkgJgpgmUOSpfIetqz ubuntu@ip-10-0-1-215&#39; | sudo tee ~exasol/.ssh/authorized_keys &gt; /dev/null &amp;&amp; sudo chown -R exasol:exasol ~exasol/.ssh &amp;&amp; sudo chmod 700 ~exasol/.ssh &amp;&amp; sudo chmod 600 ~exasol/.ssh/authorized_keys

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



#### Trino 479 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43756D2BBD3AA6B04
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43756D2BBD3AA6B04 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C753C8608EABEDD
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C753C8608EABEDD 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43756D2BBD3AA6B04
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43756D2BBD3AA6B04 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C753C8608EABEDD
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C753C8608EABEDD 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS43756D2BBD3AA6B04 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C753C8608EABEDD

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
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS436C57E973CFFA352
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS436C57E973CFFA352 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS640F1B83AFAAFB32D
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS640F1B83AFAAFB32D 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS436C57E973CFFA352
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS436C57E973CFFA352 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS640F1B83AFAAFB32D
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS640F1B83AFAAFB32D 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS436C57E973CFFA352 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS640F1B83AFAAFB32D

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
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4325D27F2918D9E44
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4325D27F2918D9E44 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C4E764A41E3B5CE
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C4E764A41E3B5CE 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4325D27F2918D9E44
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4325D27F2918D9E44 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C4E764A41E3B5CE
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C4E764A41E3B5CE 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS4325D27F2918D9E44 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS64C4E764A41E3B5CE

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
- Memory limit: `384g`
- Max threads: `64`
- Max memory usage: `24.0GB`

**Data Directory:** `/data/clickhouse`



#### Duckdb 1.4.4 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1BDDF0E3383FD18C7
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1BDDF0E3383FD18C7 2&gt;/dev/null || true

# Clear filesystem signatures on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22669018B9009737C
sudo wipefs -a /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22669018B9009737C 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1BDDF0E3383FD18C7
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1BDDF0E3383FD18C7 2&gt;/dev/null || true

# Clear RAID superblock on /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22669018B9009737C
sudo mdadm --zero-superblock /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22669018B9009737C 2&gt;/dev/null || true

# Create RAID0 array from 2 devices
yes | sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS1BDDF0E3383FD18C7 /dev/disk/by-id/nvme-Amazon_EC2_NVMe_Instance_Storage_AWS22669018B9009737C

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
- Memory limit: `384GB`

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
| Clickhouse | 376.00s | 0.12s | 201.75s | 809.92s | 57.2 GB | 21.9 GB | 2.6x |
| Starrocks | 375.43s | 0.14s | 312.85s | 843.30s | 6.0 GB | 6.0 GB | 1.0x |
| Trino | 32.76s | 0.33s | 0.00s | 46.51s | N/A | N/A | N/A |
| Duckdb | 372.98s | 0.02s | 70.15s | 446.62s | 412.9 MB | N/A | N/A |
| Exasol | 117.39s | 1.65s | 212.08s | 380.13s | 47.9 GB | 10.5 GB | 4.6x |

**Key Observations:**
- Trino had the fastest preparation time at 46.51s
- Starrocks took 843.30s (18.1x slower)

### Performance Summary

| query   | system     |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |    871.4 |      5 |      8482.9 |    9662.4 |   2877.4 |   6964.7 |  13488.7 |
| Q01     | duckdb     |    345.9 |      5 |      4895.7 |    4579.8 |   2233.7 |   1023.8 |   7218.9 |
| Q01     | exasol     |    221.6 |      5 |      1956.9 |    2014.6 |    488.3 |   1313.4 |   2523.9 |
| Q01     | starrocks  |   1194.6 |      5 |      3358.3 |    3419.4 |    611.1 |   2736.8 |   4254   |
| Q01     | trino      |   2490.3 |      5 |     15160.8 |   17992.7 |  10146.3 |   5119.2 |  28896.4 |
| Q02     | clickhouse |    482.9 |      5 |      7512.6 |    7397.3 |   4325.6 |    457.4 |  11406.4 |
| Q02     | duckdb     |    170   |      5 |      4942.5 |    4564.2 |   2208.1 |    782.8 |   6481.6 |
| Q02     | exasol     |     72.6 |      5 |       150.4 |     149.1 |     36.7 |     92.8 |    193.7 |
| Q02     | starrocks  |    268.5 |      5 |      3107.9 |    3094.9 |    798.8 |   1851.6 |   4018.4 |
| Q02     | trino      |   2172.5 |      5 |      6662.7 |    6966.6 |   1760   |   4973.8 |   9811.9 |
| Q03     | clickhouse |   1599.3 |      5 |      8144.3 |    7128.9 |   2178.8 |   3488.1 |   8952.9 |
| Q03     | duckdb     |    228.7 |      5 |      4952.8 |    4491.8 |    920.7 |   3078.6 |   5342.5 |
| Q03     | exasol     |    143   |      5 |       783.9 |     749.1 |    350.1 |    254.5 |   1083.9 |
| Q03     | starrocks  |    412   |      5 |      3371.9 |    3445.2 |   3174.1 |    295.6 |   7111.2 |
| Q03     | trino      |   7509.1 |      5 |     28929.5 |   23360.1 |  16041   |   6251.8 |  41621.1 |
| Q04     | clickhouse |   8280.8 |      5 |     24840.4 |   22120.5 |   8664.7 |   7479.3 |  29746.6 |
| Q04     | duckdb     |    230.1 |      5 |      5013.6 |    5020.3 |   1506   |   2814.3 |   6471.2 |
| Q04     | exasol     |     26.6 |      5 |       208.3 |     172.9 |     66.8 |    100.2 |    229   |
| Q04     | starrocks  |    284.6 |      5 |      2897.8 |    3213.5 |    549.6 |   2826.3 |   4113   |
| Q04     | trino      |   3653.1 |      5 |     20252.1 |   20103   |  10735.5 |   7922.1 |  33165.3 |
| Q05     | clickhouse |   1964.9 |      5 |     18381.7 |   20764.4 |   3965.8 |  17511.6 |  25382.6 |
| Q05     | duckdb     |    238.5 |      5 |      5750.2 |    5921.4 |   1017.1 |   4943.6 |   7023.1 |
| Q05     | exasol     |    143.3 |      5 |       713.9 |     695.6 |    104.2 |    520.2 |    780.7 |
| Q05     | starrocks  |    345.7 |      5 |      6345.4 |    6273.1 |    538   |   5526.2 |   6850.9 |
| Q05     | trino      |   3269.4 |      5 |     20323.8 |   29172.2 |  18158.4 |  13841.8 |  53682.5 |
| Q06     | clickhouse |     86   |      5 |      2071.6 |    1835.1 |    669.7 |    893.9 |   2418.9 |
| Q06     | duckdb     |     54.3 |      5 |      4887.6 |    4754   |    861.4 |   3428.9 |   5831.7 |
| Q06     | exasol     |     18.6 |      5 |        85.1 |      96.5 |     48.5 |     34.9 |    165.4 |
| Q06     | starrocks  |     56.5 |      5 |       107.1 |     207.7 |    179.2 |     46.5 |    465.8 |
| Q06     | trino      |   1222.7 |      5 |      5332.6 |    7901.5 |   7306.7 |   1341.8 |  16072.8 |
| Q07     | clickhouse |   4119.8 |      5 |      5755.6 |    6286   |   1188.8 |   5273.5 |   8181.9 |
| Q07     | duckdb     |    230.3 |      5 |      4489   |    4563.7 |    543   |   3947.8 |   5240.1 |
| Q07     | exasol     |     89   |      5 |       801.3 |     695   |    370.4 |     85.4 |   1065.4 |
| Q07     | starrocks  |    463.3 |      5 |      5414.1 |    4666.9 |   2511.4 |    501.9 |   7265.4 |
| Q07     | trino      |   3470.4 |      5 |     28215.4 |   28031.9 |  13415.1 |  10033   |  43677.5 |
| Q08     | clickhouse |   2853.2 |      5 |     30594.3 |   26885.5 |   7008.4 |  15169.3 |  31686.9 |
| Q08     | duckdb     |    253.3 |      5 |      5307   |    5781.4 |   1106.2 |   4697.3 |   7009.9 |
| Q08     | exasol     |     33.5 |      5 |       261.6 |     253.4 |     63.7 |    146.7 |    315.6 |
| Q08     | starrocks  |    382   |      5 |      4906.6 |    4511.5 |   1029   |   3369.5 |   5759.1 |
| Q08     | trino      |   3455.3 |      5 |     17090.4 |   23172.7 |  14890.3 |   4834.3 |  40556.8 |
| Q09     | clickhouse |   2284.6 |      5 |     22572.9 |   22480.2 |   1210.8 |  21153.3 |  24123.9 |
| Q09     | duckdb     |    909.8 |      5 |      6464.5 |    6372.9 |   1100.5 |   5210.1 |   7720.5 |
| Q09     | exasol     |    265.1 |      5 |      3093.1 |    3012.6 |    257.2 |   2656.3 |   3287   |
| Q09     | starrocks  |   1291.7 |      5 |      9248   |    9029.4 |    565.6 |   8031.2 |   9421.7 |
| Q09     | trino      |  18696.8 |      5 |     92971.2 |   94845.4 |   6342.5 |  89311.4 | 105509   |
| Q10     | clickhouse |   2816.3 |      5 |     15491.2 |   14242.9 |   2629.3 |  10672.5 |  17036.2 |
| Q10     | duckdb     |    405.3 |      5 |      4724.6 |    4738   |    500.7 |   4168.1 |   5408.6 |
| Q10     | exasol     |    319.7 |      5 |      1344.9 |    1313.5 |    501.1 |    527.5 |   1754.2 |
| Q10     | starrocks  |    569.6 |      5 |      5563.1 |    5510   |    692.3 |   4424.2 |   6319.2 |
| Q10     | trino      |   3421   |      5 |     30722.7 |   28052.6 |   8636.4 |  17768.2 |  37477.5 |
| Q11     | clickhouse |    626.9 |      5 |      4184.9 |    3781.3 |   1687   |   1062.4 |   5684.7 |
| Q11     | duckdb     |     48.1 |      5 |      4854.4 |    4640.4 |   2311.5 |   1069.6 |   7475.7 |
| Q11     | exasol     |    117.2 |      5 |       317.8 |     288.6 |     74.6 |    159.3 |    341.7 |
| Q11     | starrocks  |     84   |      5 |      2689.7 |    2888.1 |   1647.2 |   1142.6 |   4923.5 |
| Q11     | trino      |    895.7 |      5 |      3044.4 |    4396   |   3159.9 |   2112.1 |   9909.7 |
| Q12     | clickhouse |   1443.3 |      5 |      4460.1 |    4753.3 |   1684.1 |   3337.2 |   7578.1 |
| Q12     | duckdb     |    211.7 |      5 |      5333   |    5127.1 |   1489.9 |   3028.8 |   6559.7 |
| Q12     | exasol     |     31.9 |      5 |       259.5 |     235.8 |    105.4 |     65.9 |    337   |
| Q12     | starrocks  |    134   |      5 |      2140.1 |    2292.1 |   1145   |   1176.1 |   3848.2 |
| Q12     | trino      |   1389.4 |      5 |     19077.4 |   18399.7 |   2336.8 |  14856.7 |  21033.3 |
| Q13     | clickhouse |   2028.1 |      5 |      9266.6 |   10604.7 |   2815.6 |   8160.6 |  14229.4 |
| Q13     | duckdb     |    751.7 |      5 |      5186.8 |    4496.6 |   2168.5 |    674.3 |   5846.4 |
| Q13     | exasol     |    198.8 |      5 |      2053.3 |    1468.5 |   1023.6 |    308.5 |   2304.5 |
| Q13     | starrocks  |    674.5 |      5 |      5661.3 |    5508.5 |   2278.3 |   3149.3 |   7931   |
| Q13     | trino      |   3448.4 |      5 |     55519.1 |   40837.9 |  27302.7 |   8578.3 |  66670.3 |
| Q14     | clickhouse |     89.2 |      5 |      1720   |    2180.4 |    964.1 |   1143.6 |   3336.7 |
| Q14     | duckdb     |    186.5 |      5 |      3976.4 |    4365.7 |   1531.5 |   3212.5 |   6926   |
| Q14     | exasol     |     28.5 |      5 |       313.8 |     284.2 |    135.7 |     48.2 |    377   |
| Q14     | starrocks  |    124.3 |      5 |      2909.9 |    2778.1 |   1213.1 |    885.7 |   4084.9 |
| Q14     | trino      |   1711.1 |      5 |     20919.8 |   20875   |   4169.9 |  16277.9 |  25446.9 |
| Q15     | clickhouse |    219.1 |      5 |      3176.1 |    2979.9 |   1064.4 |   1383.8 |   4286.3 |
| Q15     | duckdb     |    150.9 |      5 |      5789.9 |    5512.1 |   1069   |   3808.7 |   6468.2 |
| Q15     | exasol     |    270.9 |      5 |       813.2 |     767.8 |    158.3 |    489.6 |    882.3 |
| Q15     | starrocks  |    102.1 |      5 |      3037.5 |    3122.8 |   1627.3 |    965.7 |   5551.6 |
| Q15     | trino      |   2557.2 |      5 |     21303.9 |   22405.4 |   5230.1 |  18138   |  31307.2 |
| Q16     | clickhouse |    317.5 |      5 |      5430.8 |    5558.7 |   1565   |   3331.1 |   7685.2 |
| Q16     | duckdb     |    174.7 |      5 |      4642.2 |    4518.1 |    897.4 |   3369   |   5771.7 |
| Q16     | exasol     |    337.8 |      5 |      1195.1 |    1051.3 |    305.9 |    603.1 |   1305.2 |
| Q16     | starrocks  |    354.2 |      5 |      3310.1 |    3128.6 |   1000.8 |   1534.8 |   4287.6 |
| Q16     | trino      |   2577.7 |      5 |      3644.5 |    7284.8 |   5305.5 |   3280.7 |  13808.8 |
| Q17     | clickhouse |    375.2 |      5 |      7182.3 |    5684.2 |   3076.4 |    338.3 |   7590.9 |
| Q17     | duckdb     |    238.5 |      5 |      4979.4 |    5494.5 |   1071.8 |   4787.8 |   7375.7 |
| Q17     | exasol     |     24.1 |      5 |        67.7 |      64.8 |     17.2 |     44.6 |     88.1 |
| Q17     | starrocks  |    139.5 |      5 |      2660.7 |    2444   |   1114.5 |   1069.3 |   3755.5 |
| Q17     | trino      |   4693.3 |      5 |     37678   |   39043.8 |  13313   |  19918.1 |  57021.6 |
| Q18     | clickhouse |   2511   |      5 |     27937.3 |   24130.4 |   7906.8 |  10694.3 |  29771.3 |
| Q18     | duckdb     |    590.2 |      5 |      5656   |    5776.4 |   1022.5 |   4717.8 |   6928.1 |
| Q18     | exasol     |    273.8 |      5 |      1983.8 |    1889.4 |    344.3 |   1296   |   2180.2 |
| Q18     | starrocks  |   1956.2 |      5 |      7504.7 |    8164.1 |   1203.6 |   7001.9 |   9648   |
| Q18     | trino      |   7743.7 |      5 |     43333.3 |   38553.2 |   8655.2 |  24921.7 |  45839.1 |
| Q19     | clickhouse |   1579.8 |      5 |     11884   |   13341.7 |   6001.4 |   5094.3 |  20179.2 |
| Q19     | duckdb     |    258.5 |      5 |      5832   |    5665.4 |    811.6 |   4767.4 |   6581.3 |
| Q19     | exasol     |     16.2 |      5 |        53.7 |      60.4 |     21.6 |     33.7 |     87.9 |
| Q19     | starrocks  |    183.9 |      5 |      1585.3 |    1616.4 |   1135   |    296.1 |   3267.3 |
| Q19     | trino      |   2078.9 |      5 |     18366.9 |   13907   |   7876.5 |   3836.6 |  20553.6 |
| Q20     | clickhouse |   1161.2 |      5 |      7318.1 |    7586.9 |   2836.1 |   4059.3 |  11955.6 |
| Q20     | duckdb     |    255.5 |      5 |      6385.9 |    5834.8 |   1585.6 |   3669.3 |   7372.1 |
| Q20     | exasol     |    142.9 |      5 |       463.9 |     434.4 |    175.9 |    141.1 |    573.4 |
| Q20     | starrocks  |    159.3 |      5 |      2951.3 |    3490.6 |   1319.7 |   2114.4 |   5519   |
| Q20     | trino      |   2890.2 |      5 |     18609   |   15903.7 |   8973   |   6280.3 |  27519.8 |
| Q21     | clickhouse |   2951.3 |      5 |     14393   |   15702.1 |   3532.3 |  12293.8 |  20162.4 |
| Q21     | duckdb     |   1525.4 |      5 |      5423.7 |    5280   |   1878.8 |   2614   |   7631   |
| Q21     | exasol     |    129.9 |      5 |       717   |     796.1 |    540.4 |    131.6 |   1515.7 |
| Q21     | starrocks  |   3590.1 |      5 |     10216.1 |    9137.8 |   2774.3 |   6040.6 |  12461.2 |
| Q21     | trino      |  11790.7 |      5 |     49786.9 |   57222.1 |  27163.1 |  29908.8 |  87088.7 |
| Q22     | clickhouse |    219.9 |      5 |      6027.2 |    5351.9 |   1506.7 |   2879.1 |   6487.3 |
| Q22     | duckdb     |    175.3 |      5 |      5263.1 |    5571.6 |    990.2 |   4632.1 |   7201.4 |
| Q22     | exasol     |     35.8 |      5 |       328.2 |     321.5 |     16.9 |    296.7 |    340   |
| Q22     | starrocks  |    178.7 |      5 |      4914.6 |    4802.2 |   1694.6 |   2588.2 |   6691.9 |
| Q22     | trino      |   1346.4 |      5 |      3726.2 |    3981.1 |    817   |   3337.5 |   5335.8 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse          |        1956.9 |          8482.9 |    4.33 |      0.23 | False    |
| Q02     | exasol            | clickhouse          |         150.4 |          7512.6 |   49.95 |      0.02 | False    |
| Q03     | exasol            | clickhouse          |         783.9 |          8144.3 |   10.39 |      0.1  | False    |
| Q04     | exasol            | clickhouse          |         208.3 |         24840.4 |  119.25 |      0.01 | False    |
| Q05     | exasol            | clickhouse          |         713.9 |         18381.7 |   25.75 |      0.04 | False    |
| Q06     | exasol            | clickhouse          |          85.1 |          2071.6 |   24.34 |      0.04 | False    |
| Q07     | exasol            | clickhouse          |         801.3 |          5755.6 |    7.18 |      0.14 | False    |
| Q08     | exasol            | clickhouse          |         261.6 |         30594.3 |  116.95 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |        3093.1 |         22572.9 |    7.3  |      0.14 | False    |
| Q10     | exasol            | clickhouse          |        1344.9 |         15491.2 |   11.52 |      0.09 | False    |
| Q11     | exasol            | clickhouse          |         317.8 |          4184.9 |   13.17 |      0.08 | False    |
| Q12     | exasol            | clickhouse          |         259.5 |          4460.1 |   17.19 |      0.06 | False    |
| Q13     | exasol            | clickhouse          |        2053.3 |          9266.6 |    4.51 |      0.22 | False    |
| Q14     | exasol            | clickhouse          |         313.8 |          1720   |    5.48 |      0.18 | False    |
| Q15     | exasol            | clickhouse          |         813.2 |          3176.1 |    3.91 |      0.26 | False    |
| Q16     | exasol            | clickhouse          |        1195.1 |          5430.8 |    4.54 |      0.22 | False    |
| Q17     | exasol            | clickhouse          |          67.7 |          7182.3 |  106.09 |      0.01 | False    |
| Q18     | exasol            | clickhouse          |        1983.8 |         27937.3 |   14.08 |      0.07 | False    |
| Q19     | exasol            | clickhouse          |          53.7 |         11884   |  221.3  |      0    | False    |
| Q20     | exasol            | clickhouse          |         463.9 |          7318.1 |   15.78 |      0.06 | False    |
| Q21     | exasol            | clickhouse          |         717   |         14393   |   20.07 |      0.05 | False    |
| Q22     | exasol            | clickhouse          |         328.2 |          6027.2 |   18.36 |      0.05 | False    |
| Q01     | exasol            | duckdb              |        1956.9 |          4895.7 |    2.5  |      0.4  | False    |
| Q02     | exasol            | duckdb              |         150.4 |          4942.5 |   32.86 |      0.03 | False    |
| Q03     | exasol            | duckdb              |         783.9 |          4952.8 |    6.32 |      0.16 | False    |
| Q04     | exasol            | duckdb              |         208.3 |          5013.6 |   24.07 |      0.04 | False    |
| Q05     | exasol            | duckdb              |         713.9 |          5750.2 |    8.05 |      0.12 | False    |
| Q06     | exasol            | duckdb              |          85.1 |          4887.6 |   57.43 |      0.02 | False    |
| Q07     | exasol            | duckdb              |         801.3 |          4489   |    5.6  |      0.18 | False    |
| Q08     | exasol            | duckdb              |         261.6 |          5307   |   20.29 |      0.05 | False    |
| Q09     | exasol            | duckdb              |        3093.1 |          6464.5 |    2.09 |      0.48 | False    |
| Q10     | exasol            | duckdb              |        1344.9 |          4724.6 |    3.51 |      0.28 | False    |
| Q11     | exasol            | duckdb              |         317.8 |          4854.4 |   15.28 |      0.07 | False    |
| Q12     | exasol            | duckdb              |         259.5 |          5333   |   20.55 |      0.05 | False    |
| Q13     | exasol            | duckdb              |        2053.3 |          5186.8 |    2.53 |      0.4  | False    |
| Q14     | exasol            | duckdb              |         313.8 |          3976.4 |   12.67 |      0.08 | False    |
| Q15     | exasol            | duckdb              |         813.2 |          5789.9 |    7.12 |      0.14 | False    |
| Q16     | exasol            | duckdb              |        1195.1 |          4642.2 |    3.88 |      0.26 | False    |
| Q17     | exasol            | duckdb              |          67.7 |          4979.4 |   73.55 |      0.01 | False    |
| Q18     | exasol            | duckdb              |        1983.8 |          5656   |    2.85 |      0.35 | False    |
| Q19     | exasol            | duckdb              |          53.7 |          5832   |  108.6  |      0.01 | False    |
| Q20     | exasol            | duckdb              |         463.9 |          6385.9 |   13.77 |      0.07 | False    |
| Q21     | exasol            | duckdb              |         717   |          5423.7 |    7.56 |      0.13 | False    |
| Q22     | exasol            | duckdb              |         328.2 |          5263.1 |   16.04 |      0.06 | False    |
| Q01     | exasol            | starrocks           |        1956.9 |          3358.3 |    1.72 |      0.58 | False    |
| Q02     | exasol            | starrocks           |         150.4 |          3107.9 |   20.66 |      0.05 | False    |
| Q03     | exasol            | starrocks           |         783.9 |          3371.9 |    4.3  |      0.23 | False    |
| Q04     | exasol            | starrocks           |         208.3 |          2897.8 |   13.91 |      0.07 | False    |
| Q05     | exasol            | starrocks           |         713.9 |          6345.4 |    8.89 |      0.11 | False    |
| Q06     | exasol            | starrocks           |          85.1 |           107.1 |    1.26 |      0.79 | False    |
| Q07     | exasol            | starrocks           |         801.3 |          5414.1 |    6.76 |      0.15 | False    |
| Q08     | exasol            | starrocks           |         261.6 |          4906.6 |   18.76 |      0.05 | False    |
| Q09     | exasol            | starrocks           |        3093.1 |          9248   |    2.99 |      0.33 | False    |
| Q10     | exasol            | starrocks           |        1344.9 |          5563.1 |    4.14 |      0.24 | False    |
| Q11     | exasol            | starrocks           |         317.8 |          2689.7 |    8.46 |      0.12 | False    |
| Q12     | exasol            | starrocks           |         259.5 |          2140.1 |    8.25 |      0.12 | False    |
| Q13     | exasol            | starrocks           |        2053.3 |          5661.3 |    2.76 |      0.36 | False    |
| Q14     | exasol            | starrocks           |         313.8 |          2909.9 |    9.27 |      0.11 | False    |
| Q15     | exasol            | starrocks           |         813.2 |          3037.5 |    3.74 |      0.27 | False    |
| Q16     | exasol            | starrocks           |        1195.1 |          3310.1 |    2.77 |      0.36 | False    |
| Q17     | exasol            | starrocks           |          67.7 |          2660.7 |   39.3  |      0.03 | False    |
| Q18     | exasol            | starrocks           |        1983.8 |          7504.7 |    3.78 |      0.26 | False    |
| Q19     | exasol            | starrocks           |          53.7 |          1585.3 |   29.52 |      0.03 | False    |
| Q20     | exasol            | starrocks           |         463.9 |          2951.3 |    6.36 |      0.16 | False    |
| Q21     | exasol            | starrocks           |         717   |         10216.1 |   14.25 |      0.07 | False    |
| Q22     | exasol            | starrocks           |         328.2 |          4914.6 |   14.97 |      0.07 | False    |
| Q01     | exasol            | trino               |        1956.9 |         15160.8 |    7.75 |      0.13 | False    |
| Q02     | exasol            | trino               |         150.4 |          6662.7 |   44.3  |      0.02 | False    |
| Q03     | exasol            | trino               |         783.9 |         28929.5 |   36.9  |      0.03 | False    |
| Q04     | exasol            | trino               |         208.3 |         20252.1 |   97.23 |      0.01 | False    |
| Q05     | exasol            | trino               |         713.9 |         20323.8 |   28.47 |      0.04 | False    |
| Q06     | exasol            | trino               |          85.1 |          5332.6 |   62.66 |      0.02 | False    |
| Q07     | exasol            | trino               |         801.3 |         28215.4 |   35.21 |      0.03 | False    |
| Q08     | exasol            | trino               |         261.6 |         17090.4 |   65.33 |      0.02 | False    |
| Q09     | exasol            | trino               |        3093.1 |         92971.2 |   30.06 |      0.03 | False    |
| Q10     | exasol            | trino               |        1344.9 |         30722.7 |   22.84 |      0.04 | False    |
| Q11     | exasol            | trino               |         317.8 |          3044.4 |    9.58 |      0.1  | False    |
| Q12     | exasol            | trino               |         259.5 |         19077.4 |   73.52 |      0.01 | False    |
| Q13     | exasol            | trino               |        2053.3 |         55519.1 |   27.04 |      0.04 | False    |
| Q14     | exasol            | trino               |         313.8 |         20919.8 |   66.67 |      0.02 | False    |
| Q15     | exasol            | trino               |         813.2 |         21303.9 |   26.2  |      0.04 | False    |
| Q16     | exasol            | trino               |        1195.1 |          3644.5 |    3.05 |      0.33 | False    |
| Q17     | exasol            | trino               |          67.7 |         37678   |  556.54 |      0    | False    |
| Q18     | exasol            | trino               |        1983.8 |         43333.3 |   21.84 |      0.05 | False    |
| Q19     | exasol            | trino               |          53.7 |         18366.9 |  342.03 |      0    | False    |
| Q20     | exasol            | trino               |         463.9 |         18609   |   40.11 |      0.02 | False    |
| Q21     | exasol            | trino               |         717   |         49786.9 |   69.44 |      0.01 | False    |
| Q22     | exasol            | trino               |         328.2 |          3726.2 |   11.35 |      0.09 | False    |

### Per-Stream Statistics

This benchmark was executed using **16 concurrent streams** to simulate multi-user workload. The following tables show the performance distribution across streams for each system:

#### Clickhouse

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 14780.4 | 12414.7 | 4707.9 | 23994.4 |
| 1 | 7 | 10872.0 | 7743.4 | 2259.3 | 28716.9 |
| 10 | 7 | 13267.7 | 9511.2 | 2660.0 | 24355.8 |
| 11 | 7 | 10865.4 | 11032.0 | 2015.9 | 24270.5 |
| 12 | 7 | 13611.7 | 10248.2 | 5258.1 | 26223.7 |
| 13 | 7 | 14590.5 | 18353.0 | 2355.7 | 31771.2 |
| 14 | 6 | 10471.7 | 8575.6 | 2808.6 | 28669.6 |
| 15 | 6 | 14949.0 | 12869.0 | 3057.3 | 28606.5 |
| 2 | 7 | 12394.0 | 10757.8 | 1112.9 | 22991.9 |
| 3 | 7 | 13669.1 | 12325.8 | 4194.5 | 26677.6 |
| 4 | 7 | 12304.3 | 14196.4 | 2852.2 | 25267.2 |
| 5 | 7 | 11546.0 | 8815.0 | 1910.0 | 27118.3 |
| 6 | 7 | 15380.9 | 13410.7 | 4219.2 | 25531.2 |
| 7 | 7 | 9005.0 | 7169.0 | 1603.6 | 28139.5 |
| 8 | 7 | 14504.2 | 12812.7 | 4377.3 | 31335.8 |
| 9 | 7 | 12580.0 | 7934.7 | 1389.3 | 27514.2 |

**Performance Analysis for Clickhouse:**
- Fastest stream median: 7169.0ms
- Slowest stream median: 18353.0ms
- Stream performance variation: 156.0% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Duckdb

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 4710.8 | 5186.8 | 674.3 | 7631.0 |
| 1 | 7 | 4736.8 | 5342.5 | 782.8 | 7475.7 |
| 10 | 7 | 5248.6 | 4960.6 | 3669.3 | 7034.4 |
| 11 | 7 | 5285.0 | 4932.1 | 3808.7 | 7023.1 |
| 12 | 7 | 5304.4 | 4943.6 | 3947.8 | 7218.9 |
| 13 | 7 | 5340.0 | 4963.7 | 4160.5 | 7201.4 |
| 14 | 6 | 5427.3 | 5149.4 | 4453.1 | 6926.0 |
| 15 | 6 | 5412.7 | 5095.6 | 4290.2 | 6928.9 |
| 2 | 7 | 4959.0 | 4724.6 | 1023.8 | 7720.5 |
| 3 | 7 | 5045.6 | 5349.1 | 1069.6 | 7375.7 |
| 4 | 7 | 5075.8 | 5214.1 | 2614.0 | 6468.2 |
| 5 | 7 | 5102.9 | 5052.7 | 2814.3 | 6481.6 |
| 6 | 7 | 5133.5 | 5332.1 | 3028.8 | 6260.3 |
| 7 | 7 | 5142.2 | 5263.1 | 3212.5 | 6352.6 |
| 8 | 7 | 5175.5 | 5240.1 | 3369.0 | 6717.3 |
| 9 | 7 | 5212.6 | 4972.5 | 3428.9 | 7137.5 |

**Performance Analysis for Duckdb:**
- Fastest stream median: 4724.6ms
- Slowest stream median: 5349.1ms
- Stream performance variation: 13.2% difference between fastest and slowest streams
- This demonstrates **consistent** performance across concurrent streams
#### Exasol

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 921.7 | 713.9 | 254.5 | 2279.1 |
| 1 | 7 | 367.4 | 331.8 | 51.6 | 1083.9 |
| 10 | 7 | 888.2 | 463.9 | 33.7 | 3287.0 |
| 11 | 7 | 868.4 | 573.4 | 145.2 | 2523.9 |
| 12 | 7 | 768.9 | 661.9 | 87.9 | 2429.3 |
| 13 | 7 | 800.1 | 329.8 | 44.6 | 2051.7 |
| 14 | 6 | 640.6 | 315.8 | 282.9 | 2053.3 |
| 15 | 6 | 974.7 | 563.9 | 215.2 | 3180.5 |
| 2 | 7 | 987.1 | 527.5 | 131.6 | 2656.3 |
| 3 | 7 | 648.4 | 226.7 | 76.4 | 2180.2 |
| 4 | 7 | 853.3 | 813.2 | 117.8 | 1754.2 |
| 5 | 7 | 588.3 | 312.8 | 100.4 | 1736.9 |
| 6 | 7 | 838.2 | 100.2 | 50.2 | 3093.1 |
| 7 | 7 | 333.9 | 193.7 | 48.2 | 1305.2 |
| 8 | 7 | 976.0 | 860.8 | 85.4 | 2304.5 |
| 9 | 7 | 786.3 | 146.7 | 71.9 | 2846.0 |

**Performance Analysis for Exasol:**
- Fastest stream median: 100.2ms
- Slowest stream median: 860.8ms
- Stream performance variation: 759.1% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Starrocks

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 4850.0 | 5628.3 | 294.6 | 7616.9 |
| 1 | 7 | 3117.2 | 2845.1 | 732.1 | 5253.8 |
| 10 | 7 | 4391.9 | 4119.2 | 771.7 | 8202.2 |
| 11 | 7 | 3547.1 | 3296.6 | 2240.8 | 5707.9 |
| 12 | 7 | 4017.0 | 4211.8 | 1382.4 | 7305.8 |
| 13 | 7 | 4293.5 | 3303.3 | 2296.0 | 6616.1 |
| 14 | 6 | 4132.3 | 4259.6 | 2139.8 | 5612.3 |
| 15 | 6 | 4235.7 | 4166.9 | 1288.2 | 7930.8 |
| 2 | 7 | 4741.4 | 4111.3 | 1477.9 | 8256.0 |
| 3 | 7 | 4300.5 | 2690.9 | 852.7 | 10318.1 |
| 4 | 7 | 4736.6 | 3391.1 | 43.2 | 12856.1 |
| 5 | 7 | 4306.6 | 4902.1 | 1653.6 | 7843.1 |
| 6 | 7 | 4439.9 | 3017.5 | 1323.9 | 10799.3 |
| 7 | 7 | 3137.8 | 3142.1 | 338.6 | 7225.9 |
| 8 | 7 | 4476.3 | 5090.6 | 1203.6 | 7423.1 |
| 9 | 7 | 4332.3 | 3946.9 | 148.9 | 8520.8 |

**Performance Analysis for Starrocks:**
- Fastest stream median: 2690.9ms
- Slowest stream median: 5628.3ms
- Stream performance variation: 109.2% difference between fastest and slowest streams
- This demonstrates **varying** performance across concurrent streams
#### Trino

| Stream ID | Queries Executed | Avg Runtime (ms) | Median Runtime (ms) | Min Runtime (ms) | Max Runtime (ms) |
|-----------|------------------|------------------|---------------------|------------------|------------------|
| 0 | 7 | 31307.3 | 34038.9 | 6251.8 | 55519.1 |
| 1 | 7 | 23091.6 | 24574.2 | 3044.4 | 40556.8 |
| 10 | 7 | 29218.6 | 20255.8 | 5332.6 | 105508.7 |
| 11 | 7 | 22299.7 | 17549.4 | 6280.3 | 53682.5 |
| 12 | 7 | 16642.9 | 15160.8 | 2112.1 | 33218.0 |
| 13 | 7 | 26034.3 | 27997.8 | 3337.5 | 45839.1 |
| 14 | 6 | 24219.1 | 20322.6 | 2851.5 | 59340.0 |
| 15 | 6 | 30676.8 | 18286.2 | 3644.5 | 91246.8 |
| 2 | 7 | 29471.0 | 19077.4 | 3280.7 | 95188.9 |
| 3 | 7 | 28544.9 | 20252.1 | 4062.1 | 84624.1 |
| 4 | 7 | 30440.1 | 19137.5 | 1426.9 | 87088.7 |
| 5 | 7 | 18821.5 | 21303.9 | 4107.4 | 37477.5 |
| 6 | 7 | 29079.3 | 19797.3 | 3836.6 | 89311.4 |
| 7 | 7 | 15517.3 | 7922.1 | 3366.2 | 57021.6 |
| 8 | 7 | 24637.8 | 14081.7 | 10033.0 | 66670.3 |
| 9 | 7 | 29560.3 | 16072.8 | 1341.8 | 92971.2 |

**Performance Analysis for Trino:**
- Fastest stream median: 7922.1ms
- Slowest stream median: 34038.9ms
- Stream performance variation: 329.7% difference between fastest and slowest streams
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
- Median runtime: 387.1ms
- Average runtime: 764.3ms
- Fastest query: 33.7ms
- Slowest query: 3287.0ms

**duckdb:**
- Median runtime: 5015.9ms
- Average runtime: 5139.5ms
- Fastest query: 674.3ms
- Slowest query: 7720.5ms

**starrocks:**
- Median runtime: 3893.8ms
- Average runtime: 4191.1ms
- Fastest query: 43.2ms
- Slowest query: 12856.1ms

**clickhouse:**
- Median runtime: 9672.2ms
- Average runtime: 12801.1ms
- Fastest query: 1112.9ms
- Slowest query: 31771.2ms

**trino:**
- Median runtime: 19603.7ms
- Average runtime: 25564.0ms
- Fastest query: 1341.8ms
- Slowest query: 105508.7ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`extscal_streams_16-benchmark.zip`](extscal_streams_16-benchmark.zip)

## Reproducibility

### System Requirements

Based on our testing environment:

- **CPU:** 64 logical cores
- **Memory:** 495.8GB RAM
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
  - memory_limit: 384g
  - max_threads: 64
  - max_memory_usage: 24000000000
  - max_bytes_before_external_group_by: 8000000000
  - max_bytes_before_external_sort: 8000000000
  - join_algorithm: grace_hash
  - max_bytes_in_join: 16000000000

**Trino 479:**
- **Setup method:** native
- **Data directory:** 
- **Applied configurations:**
  - query_max_memory: 286GB
  - query_max_memory_per_node: 286GB

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
  - memory_limit: 384GB
  - threads: 64


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