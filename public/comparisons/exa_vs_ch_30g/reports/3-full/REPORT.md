# Exasol vs ClickHouse Performance Comparison on TPC-H SF30

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-24 15:46:50

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **clickhouse**
- **clickhouse_tuned**
- **clickhouse_stat**

**Key Findings:**
- exasol was the fastest overall with 165.9ms median runtime
- clickhouse_stat was 10.0x slower
- Tested 616 total query executions across 22 different TPC-H queries

## Systems Under Test

### Exasol 2025.1.0

**Software Configuration:**
- **Database:** exasol 2025.1.0
- **Setup method:** installer

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-172

### Clickhouse 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-139

### Clickhouse_tuned 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-243

### Clickhouse_stat 25.9.4.58

**Software Configuration:**
- **Database:** clickhouse 25.9.4.58
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-205


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r5d.4xlarge
- **Clickhouse Instance:** r5d.4xlarge
- **Clickhouse_tuned Instance:** r5d.4xlarge
- **Clickhouse_stat Instance:** r5d.4xlarge


### Database Configuration

The following commands were **actually executed** during the benchmark setup. You can copy and paste these to reproduce the installation:

#### Exasol 2025.1.0 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

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
sudo parted /dev/md0 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/md0 mklabel gpt

# Create 48GB partition for data generation
sudo parted /dev/md0 mkpart primary ext4 1MiB 48GiB

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary ext4 1MiB 48GiB

# Create raw partition for Exasol (510GB)
sudo parted /dev/md0 mkpart primary 48GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary 48GiB 100%

# Format /dev/md0p1 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0p1

# Create mount point /data/tpch_gen
sudo mkdir -p /data/tpch_gen

# Mount /dev/md0p1 to /data/tpch_gen
sudo mount /dev/md0p1 /data/tpch_gen

# Set ownership of /data/tpch_gen to $(whoami):$(whoami)
sudo chown -R $(whoami):$(whoami) /data/tpch_gen

```

**User Setup:**
```bash
# Create Exasol system user
sudo useradd -m exasol

# Add exasol user to sudo group
sudo usermod -aG sudo exasol

# Set password for exasol user (interactive)
sudo passwd exasol

```

**Tool Setup:**
```bash
# Download c4 cluster management tool v4.28.2
wget https://x-up.s3.amazonaws.com/releases/c4/linux/x86_64/4.28.2/c4 -O c4 &amp;&amp; chmod +x c4

```

**SSH Setup:**
```bash
# Generate SSH key pair for cluster communication
ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N &#34;&#34;

```

**Configuration:**
```bash
# Create c4 configuration file on remote system
cat &gt; /tmp/exasol_c4.conf &lt;&lt; &#39;EOF&#39;
CCC_HOST_ADDRS=&#34;&lt;PRIVATE_IP&gt;&#34;
CCC_HOST_EXTERNAL_ADDRS=&#34;&lt;SERVER_IP&gt;&#34;
CCC_HOST_DATADISK=/dev/md0p2
CCC_HOST_IMAGE_USER=exasol
CCC_HOST_IMAGE_PASSWORD=&lt;EXASOL_IMAGE_PASSWORD&gt;
CCC_HOST_KEY_PAIR_FILE=id_rsa
CCC_PLAY_RESERVE_NODES=0
CCC_PLAY_WORKING_COPY=@exasol-2025.1.0
CCC_PLAY_DB_PASSWORD=&lt;EXASOL_DB_PASSWORD&gt;
CCC_PLAY_ADMIN_PASSWORD=&lt;EXASOL_ADMIN_PASSWORD&gt;
CCC_ADMINUI_START_SERVER=true
EOF

```

**Cluster Deployment:**
```bash
# Deploy Exasol cluster using c4
./c4 host play -i /tmp/exasol_c4.conf

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

**Cluster Management:**
```bash
# Get cluster play ID for confd_client operations
c4 ps

```


**Tuning Parameters:**
- Database RAM: `64g`
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



#### Clickhouse_tuned 25.9.4.58 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

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

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create ClickHouse data directory under /data
sudo mkdir -p /data/clickhouse

# Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# Update package lists
sudo apt-get update

# Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# Install ClickHouse server and client version &lt;SERVER_IP&gt;
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;106897742233&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;8&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;16&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# Configure ClickHouse user profile with password and query settings
sudo tee /etc/clickhouse-server/users.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;users&gt;
        &lt;default replace=&#34;true&#34;&gt;
            &lt;password_sha256_hex&gt;2cca9d8714615f4132390a3db9296d39ec051b3faff87be7ea5f7fe0e2de14c9&lt;/password_sha256_hex&gt;
            &lt;networks&gt;
                &lt;ip&gt;::/0&lt;/ip&gt;
            &lt;/networks&gt;
        &lt;/default&gt;
    &lt;/users&gt;
    &lt;profiles&gt;
        &lt;default&gt;
            &lt;max_threads&gt;16&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;60000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492197785&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492197785&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# Start ClickHouse server service
sudo systemctl start clickhouse-server

# Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```


**Tuning Parameters:**
- Memory limit: `64g`
- Max threads: `16`
- Max memory usage: `60.0GB`

**Data Directory:** `/data/clickhouse`



#### Clickhouse 25.9.4.58 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

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

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create ClickHouse data directory under /data
sudo mkdir -p /data/clickhouse

# Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# Update package lists
sudo apt-get update

# Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# Install ClickHouse server and client version &lt;SERVER_IP&gt;
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;106897745510&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;8&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;16&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# Configure ClickHouse user profile with password and query settings
sudo tee /etc/clickhouse-server/users.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;users&gt;
        &lt;default replace=&#34;true&#34;&gt;
            &lt;password_sha256_hex&gt;2cca9d8714615f4132390a3db9296d39ec051b3faff87be7ea5f7fe0e2de14c9&lt;/password_sha256_hex&gt;
            &lt;networks&gt;
                &lt;ip&gt;::/0&lt;/ip&gt;
            &lt;/networks&gt;
        &lt;/default&gt;
    &lt;/users&gt;
    &lt;profiles&gt;
        &lt;default&gt;
            &lt;max_threads&gt;16&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;60000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492200038&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492200038&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# Start ClickHouse server service
sudo systemctl start clickhouse-server

# Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```


**Tuning Parameters:**
- Memory limit: `64g`
- Max threads: `16`
- Max memory usage: `60.0GB`

**Data Directory:** `/data/clickhouse`



#### Clickhouse_stat 25.9.4.58 Setup

**Storage Configuration:**
```bash
# Stop existing RAID array at /dev/md0 if present
sudo mdadm --stop /dev/md0 2&gt;/dev/null || true

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

# Format /dev/md0 with ext4 filesystem
sudo mkfs.ext4 -F /dev/md0

# Create mount point /data
sudo mkdir -p /data

# Mount /dev/md0 to /data
sudo mount /dev/md0 /data

# Set ownership of /data to ubuntu:ubuntu
sudo chown -R ubuntu:ubuntu /data

# Create ClickHouse data directory under /data
sudo mkdir -p /data/clickhouse

# Set ownership of /data/clickhouse to clickhouse:clickhouse
sudo chown -R clickhouse:clickhouse /data/clickhouse

```

**Prerequisites:**
```bash
# Update package lists
sudo apt-get update

# Install prerequisite packages for secure repository access
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg

```

**Repository Setup:**
```bash
# Add ClickHouse GPG key to system keyring
curl -fsSL &#39;https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key&#39; | sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

# Add ClickHouse official repository to APT sources
ARCH=$(dpkg --print-architecture) &amp;&amp; echo &#34;deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg arch=${ARCH}] https://packages.clickhouse.com/deb stable main&#34; | sudo tee /etc/apt/sources.list.d/clickhouse.list

# Update package lists with ClickHouse repository
sudo apt-get update

```

**Installation:**
```bash
# Install ClickHouse server and client version &lt;SERVER_IP&gt;
sudo apt-get install -y clickhouse-server=25.9.4.58 clickhouse-client=25.9.4.58

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;tmp_path&gt;/data/clickhouse/tmp&lt;/tmp_path&gt;
    &lt;max_server_memory_usage&gt;106897748787&lt;/max_server_memory_usage&gt;
    &lt;max_concurrent_queries&gt;8&lt;/max_concurrent_queries&gt;
    &lt;background_pool_size&gt;16&lt;/background_pool_size&gt;
    &lt;background_schedule_pool_size&gt;16&lt;/background_schedule_pool_size&gt;
    &lt;max_table_size_to_drop&gt;50000000000&lt;/max_table_size_to_drop&gt;
&lt;/clickhouse&gt;
EOF

```

**User Configuration:**
```bash
# Configure ClickHouse user profile with password and query settings
sudo tee /etc/clickhouse-server/users.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;users&gt;
        &lt;default replace=&#34;true&#34;&gt;
            &lt;password_sha256_hex&gt;2cca9d8714615f4132390a3db9296d39ec051b3faff87be7ea5f7fe0e2de14c9&lt;/password_sha256_hex&gt;
            &lt;networks&gt;
                &lt;ip&gt;::/0&lt;/ip&gt;
            &lt;/networks&gt;
        &lt;/default&gt;
    &lt;/users&gt;
    &lt;profiles&gt;
        &lt;default&gt;
            &lt;max_threads&gt;16&lt;/max_threads&gt;
            &lt;max_memory_usage&gt;60000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492202291&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492202291&lt;/max_bytes_before_external_group_by&gt;
            &lt;join_use_nulls&gt;1&lt;/join_use_nulls&gt;
            &lt;allow_experimental_correlated_subqueries&gt;1&lt;/allow_experimental_correlated_subqueries&gt;
            &lt;optimize_read_in_order&gt;1&lt;/optimize_read_in_order&gt;
            &lt;max_insert_threads&gt;8&lt;/max_insert_threads&gt;
            &lt;allow_experimental_statistics&gt;1&lt;/allow_experimental_statistics&gt;
            &lt;allow_statistics_optimize&gt;1&lt;/allow_statistics_optimize&gt;
        &lt;/default&gt;
    &lt;/profiles&gt;
&lt;/clickhouse&gt;
EOF

```

**Service Management:**
```bash
# Start ClickHouse server service
sudo systemctl start clickhouse-server

# Enable ClickHouse server to start on boot
sudo systemctl enable clickhouse-server

```


**Tuning Parameters:**
- Memory limit: `64g`
- Max threads: `16`
- Max memory usage: `60.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 30
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 7

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_30g-benchmark.zip
cd exa_vs_ch_30g

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

The following table shows the time taken to provision cloud instances and install database software:

| System | Instance Provisioning | Software Installation | Total Setup Time | Notes |
|--------|----------------------|----------------------|------------------|-------|
| Clickhouse_stat | 138.11s | 33.63s | 171.74s | New infrastructure |
| Clickhouse | 138.11s | 33.82s | 171.94s | New infrastructure |
| Clickhouse_tuned | 138.11s | 35.86s | 173.97s | New infrastructure |
| Exasol | 138.11s | 552.89s | 691.00s | New infrastructure |

**Infrastructure Provisioning:** 138.11s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse_stat had the fastest software installation at 33.63s
- Exasol took 552.89s to install (16.4x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |   1603.8 |      7 |      1592.2 |    1597.4 |     16.2 |   1580.2 |   1618.2 |
| Q01     | clickhouse_stat  |   1759.4 |      7 |      1750.8 |    1755.9 |      9.1 |   1746.1 |   1768   |
| Q01     | clickhouse_tuned |   1611.5 |      7 |      1613.6 |    1616.4 |      9.5 |   1605.9 |   1633.8 |
| Q01     | exasol           |    621.5 |      7 |       622.3 |     622.5 |      1   |    621.4 |    623.9 |
| Q02     | clickhouse       |    836.1 |      7 |       611.2 |     613.4 |     15.6 |    597.2 |    636.8 |
| Q02     | clickhouse_stat  |    663.8 |      7 |       531.5 |     530.9 |      7.5 |    518.3 |    538.4 |
| Q02     | clickhouse_tuned |    824.7 |      7 |       615.3 |     622.6 |     15.1 |    601.5 |    639.5 |
| Q02     | exasol           |     67.4 |      7 |        51.9 |      52   |      0.5 |     51.2 |     52.5 |
| Q03     | clickhouse       |   2683.9 |      7 |      2435   |    2423.9 |     27.6 |   2379.3 |   2445.5 |
| Q03     | clickhouse_stat  |   3171.3 |      7 |      2801.3 |    2817.1 |     55.1 |   2744.9 |   2908.5 |
| Q03     | clickhouse_tuned |   2698.7 |      7 |      2440.4 |    2437.9 |     34.2 |   2389.2 |   2487.8 |
| Q03     | exasol           |    219.1 |      7 |       213.5 |     210.2 |      7.5 |    200.7 |    220.5 |
| Q04     | clickhouse       |   1482.4 |      7 |      1410.4 |    1386.6 |     40.4 |   1336.4 |   1427.2 |
| Q04     | clickhouse_stat  |   1676.7 |      7 |      1614.4 |    1613.5 |     24.1 |   1579.7 |   1638.8 |
| Q04     | clickhouse_tuned |   5293.9 |      7 |      4707   |    4685.3 |    158.3 |   4406.2 |   4930.7 |
| Q04     | exasol           |     49.5 |      7 |        48   |      48.3 |      1   |     47.2 |     50.3 |
| Q05     | clickhouse       |   5639.2 |      7 |      5338.4 |    5324.9 |     59.9 |   5252.4 |   5402.4 |
| Q05     | clickhouse_stat  |   6255.9 |      7 |      5460.1 |    5534.6 |    177.6 |   5357   |   5882   |
| Q05     | clickhouse_tuned |   5811.4 |      7 |      5313.8 |    5319.9 |     76   |   5231.7 |   5438.4 |
| Q05     | exasol           |    207.2 |      7 |       154.4 |     154.4 |      0.8 |    153.1 |    155.5 |
| Q06     | clickhouse       |    132.3 |      7 |       126.7 |     127.6 |      4.9 |    122.7 |    136.7 |
| Q06     | clickhouse_stat  |    334.2 |      7 |       158   |     162.4 |      9.9 |    153.7 |    182.2 |
| Q06     | clickhouse_tuned |    276.8 |      7 |       128.3 |     128.3 |      3   |    124.8 |    134.1 |
| Q06     | exasol           |     32.8 |      7 |        32.3 |      32.2 |      0.3 |     31.6 |     32.5 |
| Q07     | clickhouse       |   3212.4 |      7 |      2920.1 |    2898   |     77.7 |   2789.7 |   2973.2 |
| Q07     | clickhouse_stat  |   3340.7 |      7 |      3063.2 |    3064.8 |     26.5 |   3036.9 |   3112   |
| Q07     | clickhouse_tuned |   3241.6 |      7 |      2951.5 |    2947.1 |     73.2 |   2828.7 |   3025.1 |
| Q07     | exasol           |    183.2 |      7 |       177.6 |     177.6 |      1.2 |    176.4 |    179.5 |
| Q08     | clickhouse       |   5644.9 |      7 |      5646.5 |    5661.7 |     66.9 |   5566.5 |   5757.2 |
| Q08     | clickhouse_stat  |   1116.1 |      7 |      1113.6 |    1111.4 |     23.8 |   1080.9 |   1149.9 |
| Q08     | clickhouse_tuned |   5676.7 |      7 |      5712.7 |    5702.9 |     54.3 |   5610.2 |   5773   |
| Q08     | exasol           |     71.2 |      7 |        60.7 |      66.8 |     17   |     59.9 |    105.4 |
| Q09     | clickhouse       |   7980.7 |      7 |      7560.3 |    7544.3 |     90   |   7372.7 |   7653.5 |
| Q09     | clickhouse_stat  |   3635.7 |      7 |      3163.1 |    3149.8 |     63.7 |   3051.4 |   3221.2 |
| Q09     | clickhouse_tuned |   8137.7 |      7 |      7658.8 |    7640.9 |     90.6 |   7540   |   7751.1 |
| Q09     | exasol           |    727.5 |      7 |       696.8 |     697.3 |      1.3 |    696.2 |    699.5 |
| Q10     | clickhouse       |   1892.8 |      7 |      1615.7 |    1633.6 |     47.7 |   1573.7 |   1716.8 |
| Q10     | clickhouse_stat  |   1874.1 |      7 |      1736.3 |    1741.9 |     41.6 |   1679.9 |   1794.3 |
| Q10     | clickhouse_tuned |   1901   |      7 |      1652   |    1649   |     54   |   1589.7 |   1722.3 |
| Q10     | exasol           |    348.8 |      7 |       343.7 |     342.6 |      5.6 |    333.8 |    348.5 |
| Q11     | clickhouse       |    456.4 |      7 |       389.9 |     393.1 |     11.9 |    378.4 |    410.8 |
| Q11     | clickhouse_stat  |    462.6 |      7 |       401.3 |     400.3 |      7.3 |    389.1 |    409.2 |
| Q11     | clickhouse_tuned |    459.2 |      7 |       400.8 |     403.3 |     10.1 |    387.1 |    417.8 |
| Q11     | exasol           |    117.5 |      7 |       121   |     120.8 |      1.8 |    118.7 |    123.7 |
| Q12     | clickhouse       |   1321.7 |      7 |       528.8 |     526.7 |     13   |    505.8 |    540.7 |
| Q12     | clickhouse_stat  |    817.5 |      7 |       669.3 |     659.2 |     34.2 |    583.2 |    684.7 |
| Q12     | clickhouse_tuned |   1294   |      7 |       530.9 |     532.5 |     10.5 |    517.6 |    549.7 |
| Q12     | exasol           |     65.1 |      7 |        63.4 |      63.3 |      0.5 |     62.6 |     64   |
| Q13     | clickhouse       |   2631.6 |      7 |      2431.7 |    2452   |     47.2 |   2407.5 |   2536.3 |
| Q13     | clickhouse_stat  |   2692   |      7 |      2440.9 |    2449.5 |     64.1 |   2359.8 |   2574.1 |
| Q13     | clickhouse_tuned |   2674.4 |      7 |      2443.7 |    2463.2 |     66.7 |   2371.2 |   2555.2 |
| Q13     | exasol           |    451.6 |      7 |       449.1 |     448.5 |      2   |    445.1 |    451.3 |
| Q14     | clickhouse       |    129.5 |      7 |       129   |     129.3 |      2.6 |    126   |    134.6 |
| Q14     | clickhouse_stat  |    250.5 |      7 |       243.3 |     249.8 |     14   |    235   |    268.5 |
| Q14     | clickhouse_tuned |    130.9 |      7 |       131.4 |     130.7 |      2.1 |    127.3 |    133.1 |
| Q14     | exasol           |     57.6 |      7 |        57.7 |      57.8 |      0.4 |     57.3 |     58.3 |
| Q15     | clickhouse       |    215.9 |      7 |       182   |     180.1 |     24.6 |    154.3 |    212.6 |
| Q15     | clickhouse_stat  |    290.6 |      7 |       236.1 |     236.6 |      4   |    231.9 |    242.8 |
| Q15     | clickhouse_tuned |    216.5 |      7 |       191.3 |     189.7 |     19.4 |    169.5 |    215.5 |
| Q15     | exasol           |    208.4 |      7 |       205.9 |     205.6 |      2.4 |    200.4 |    207.7 |
| Q16     | clickhouse       |    331.8 |      7 |       338.3 |     338.6 |      1.8 |    336.7 |    341.3 |
| Q16     | clickhouse_stat  |    335.3 |      7 |       347.3 |     349.4 |      9.5 |    339.8 |    362.8 |
| Q16     | clickhouse_tuned |    499.9 |      7 |       441.2 |     442.5 |     10.3 |    433.8 |    464.3 |
| Q16     | exasol           |    385.1 |      7 |       377.5 |     378.6 |      5.6 |    373.5 |    390.1 |
| Q17     | clickhouse       |   2784.8 |      7 |      2589.9 |    2580   |     24.1 |   2543.7 |   2609.2 |
| Q17     | clickhouse_stat  |   3027   |      7 |      2805.5 |    2796.9 |     40.9 |   2709.8 |   2841.4 |
| Q17     | clickhouse_tuned |    701   |      7 |       811.8 |     814.3 |      7.1 |    805.3 |    823.3 |
| Q17     | exasol           |     22.1 |      7 |        21.6 |      21.4 |      0.5 |     20.7 |     22   |
| Q18     | clickhouse       |   2571.2 |      7 |      2556.2 |    2543.1 |     49.9 |   2464.5 |   2597.9 |
| Q18     | clickhouse_stat  |   2784.2 |      7 |      2755.6 |    2760.3 |     72.1 |   2651.6 |   2887.8 |
| Q18     | clickhouse_tuned |   7973.3 |      7 |      6865.3 |    6884.1 |    122.3 |   6743   |   7133.7 |
| Q18     | exasol           |    419.8 |      7 |       418.9 |     418.9 |      1.3 |    417.2 |    421.2 |
| Q19     | clickhouse       |   1597.7 |      7 |      1618.7 |    1621.8 |      9.8 |   1609.9 |   1636.6 |
| Q19     | clickhouse_stat  |   2754.2 |      7 |      2800.3 |    2803.1 |     33.9 |   2761.3 |   2861.4 |
| Q19     | clickhouse_tuned |   4301.4 |      7 |      3895.4 |    3903.5 |     17.5 |   3891.7 |   3939.6 |
| Q19     | exasol           |     22   |      7 |        22.2 |      22.2 |      0.3 |     21.8 |     22.6 |
| Q20     | clickhouse       |    248.9 |      7 |       217.2 |     217.3 |      2   |    213.7 |    219.4 |
| Q20     | clickhouse_stat  |    332.2 |      7 |       275.3 |     274.9 |      4.6 |    266   |    280.9 |
| Q20     | clickhouse_tuned |   1094.3 |      7 |       847.9 |     847.2 |     24.7 |    827.8 |    897.7 |
| Q20     | exasol           |    230.4 |      7 |       228.7 |     227.7 |      1.5 |    225.8 |    229.1 |
| Q21     | clickhouse       |  21315.7 |      7 |     20869.6 |   20892.9 |    122.7 |  20749.5 |  21093.3 |
| Q21     | clickhouse_stat  |  21772.8 |      7 |     21243.2 |   21235.4 |    175.2 |  20921.7 |  21416.4 |
| Q21     | clickhouse_tuned |  11408.7 |      7 |      9568.8 |    9638   |    182.4 |   9425.1 |   9982.5 |
| Q21     | exasol           |    263.7 |      7 |       261.9 |     268.3 |     18.3 |    260.3 |    309.7 |
| Q22     | clickhouse       |    395.8 |      7 |       379.7 |     393.8 |     28.7 |    368.4 |    446.5 |
| Q22     | clickhouse_stat  |    412.5 |      7 |       396.7 |     395.4 |      9.2 |    383.4 |    410.6 |
| Q22     | clickhouse_tuned |    404.8 |      7 |       362.4 |     358.3 |     32.5 |    315.6 |    394.1 |
| Q22     | exasol           |     80.7 |      7 |        78.8 |      78.7 |      0.3 |     78.2 |     79.1 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse_tuned    |         622.3 |          1613.6 |    2.59 |      0.39 | False    |
| Q02     | exasol            | clickhouse_tuned    |          51.9 |           615.3 |   11.86 |      0.08 | False    |
| Q03     | exasol            | clickhouse_tuned    |         213.5 |          2440.4 |   11.43 |      0.09 | False    |
| Q04     | exasol            | clickhouse_tuned    |          48   |          4707   |   98.06 |      0.01 | False    |
| Q05     | exasol            | clickhouse_tuned    |         154.4 |          5313.8 |   34.42 |      0.03 | False    |
| Q06     | exasol            | clickhouse_tuned    |          32.3 |           128.3 |    3.97 |      0.25 | False    |
| Q07     | exasol            | clickhouse_tuned    |         177.6 |          2951.5 |   16.62 |      0.06 | False    |
| Q08     | exasol            | clickhouse_tuned    |          60.7 |          5712.7 |   94.11 |      0.01 | False    |
| Q09     | exasol            | clickhouse_tuned    |         696.8 |          7658.8 |   10.99 |      0.09 | False    |
| Q10     | exasol            | clickhouse_tuned    |         343.7 |          1652   |    4.81 |      0.21 | False    |
| Q11     | exasol            | clickhouse_tuned    |         121   |           400.8 |    3.31 |      0.3  | False    |
| Q12     | exasol            | clickhouse_tuned    |          63.4 |           530.9 |    8.37 |      0.12 | False    |
| Q13     | exasol            | clickhouse_tuned    |         449.1 |          2443.7 |    5.44 |      0.18 | False    |
| Q14     | exasol            | clickhouse_tuned    |          57.7 |           131.4 |    2.28 |      0.44 | False    |
| Q15     | exasol            | clickhouse_tuned    |         205.9 |           191.3 |    0.93 |      1.08 | True     |
| Q16     | exasol            | clickhouse_tuned    |         377.5 |           441.2 |    1.17 |      0.86 | False    |
| Q17     | exasol            | clickhouse_tuned    |          21.6 |           811.8 |   37.58 |      0.03 | False    |
| Q18     | exasol            | clickhouse_tuned    |         418.9 |          6865.3 |   16.39 |      0.06 | False    |
| Q19     | exasol            | clickhouse_tuned    |          22.2 |          3895.4 |  175.47 |      0.01 | False    |
| Q20     | exasol            | clickhouse_tuned    |         228.7 |           847.9 |    3.71 |      0.27 | False    |
| Q21     | exasol            | clickhouse_tuned    |         261.9 |          9568.8 |   36.54 |      0.03 | False    |
| Q22     | exasol            | clickhouse_tuned    |          78.8 |           362.4 |    4.6  |      0.22 | False    |
| Q01     | exasol            | clickhouse          |         622.3 |          1592.2 |    2.56 |      0.39 | False    |
| Q02     | exasol            | clickhouse          |          51.9 |           611.2 |   11.78 |      0.08 | False    |
| Q03     | exasol            | clickhouse          |         213.5 |          2435   |   11.41 |      0.09 | False    |
| Q04     | exasol            | clickhouse          |          48   |          1410.4 |   29.38 |      0.03 | False    |
| Q05     | exasol            | clickhouse          |         154.4 |          5338.4 |   34.58 |      0.03 | False    |
| Q06     | exasol            | clickhouse          |          32.3 |           126.7 |    3.92 |      0.25 | False    |
| Q07     | exasol            | clickhouse          |         177.6 |          2920.1 |   16.44 |      0.06 | False    |
| Q08     | exasol            | clickhouse          |          60.7 |          5646.5 |   93.02 |      0.01 | False    |
| Q09     | exasol            | clickhouse          |         696.8 |          7560.3 |   10.85 |      0.09 | False    |
| Q10     | exasol            | clickhouse          |         343.7 |          1615.7 |    4.7  |      0.21 | False    |
| Q11     | exasol            | clickhouse          |         121   |           389.9 |    3.22 |      0.31 | False    |
| Q12     | exasol            | clickhouse          |          63.4 |           528.8 |    8.34 |      0.12 | False    |
| Q13     | exasol            | clickhouse          |         449.1 |          2431.7 |    5.41 |      0.18 | False    |
| Q14     | exasol            | clickhouse          |          57.7 |           129   |    2.24 |      0.45 | False    |
| Q15     | exasol            | clickhouse          |         205.9 |           182   |    0.88 |      1.13 | True     |
| Q16     | exasol            | clickhouse          |         377.5 |           338.3 |    0.9  |      1.12 | True     |
| Q17     | exasol            | clickhouse          |          21.6 |          2589.9 |  119.9  |      0.01 | False    |
| Q18     | exasol            | clickhouse          |         418.9 |          2556.2 |    6.1  |      0.16 | False    |
| Q19     | exasol            | clickhouse          |          22.2 |          1618.7 |   72.91 |      0.01 | False    |
| Q20     | exasol            | clickhouse          |         228.7 |           217.2 |    0.95 |      1.05 | True     |
| Q21     | exasol            | clickhouse          |         261.9 |         20869.6 |   79.69 |      0.01 | False    |
| Q22     | exasol            | clickhouse          |          78.8 |           379.7 |    4.82 |      0.21 | False    |
| Q01     | exasol            | clickhouse_stat     |         622.3 |          1750.8 |    2.81 |      0.36 | False    |
| Q02     | exasol            | clickhouse_stat     |          51.9 |           531.5 |   10.24 |      0.1  | False    |
| Q03     | exasol            | clickhouse_stat     |         213.5 |          2801.3 |   13.12 |      0.08 | False    |
| Q04     | exasol            | clickhouse_stat     |          48   |          1614.4 |   33.63 |      0.03 | False    |
| Q05     | exasol            | clickhouse_stat     |         154.4 |          5460.1 |   35.36 |      0.03 | False    |
| Q06     | exasol            | clickhouse_stat     |          32.3 |           158   |    4.89 |      0.2  | False    |
| Q07     | exasol            | clickhouse_stat     |         177.6 |          3063.2 |   17.25 |      0.06 | False    |
| Q08     | exasol            | clickhouse_stat     |          60.7 |          1113.6 |   18.35 |      0.05 | False    |
| Q09     | exasol            | clickhouse_stat     |         696.8 |          3163.1 |    4.54 |      0.22 | False    |
| Q10     | exasol            | clickhouse_stat     |         343.7 |          1736.3 |    5.05 |      0.2  | False    |
| Q11     | exasol            | clickhouse_stat     |         121   |           401.3 |    3.32 |      0.3  | False    |
| Q12     | exasol            | clickhouse_stat     |          63.4 |           669.3 |   10.56 |      0.09 | False    |
| Q13     | exasol            | clickhouse_stat     |         449.1 |          2440.9 |    5.44 |      0.18 | False    |
| Q14     | exasol            | clickhouse_stat     |          57.7 |           243.3 |    4.22 |      0.24 | False    |
| Q15     | exasol            | clickhouse_stat     |         205.9 |           236.1 |    1.15 |      0.87 | False    |
| Q16     | exasol            | clickhouse_stat     |         377.5 |           347.3 |    0.92 |      1.09 | True     |
| Q17     | exasol            | clickhouse_stat     |          21.6 |          2805.5 |  129.88 |      0.01 | False    |
| Q18     | exasol            | clickhouse_stat     |         418.9 |          2755.6 |    6.58 |      0.15 | False    |
| Q19     | exasol            | clickhouse_stat     |          22.2 |          2800.3 |  126.14 |      0.01 | False    |
| Q20     | exasol            | clickhouse_stat     |         228.7 |           275.3 |    1.2  |      0.83 | False    |
| Q21     | exasol            | clickhouse_stat     |         261.9 |         21243.2 |   81.11 |      0.01 | False    |
| Q22     | exasol            | clickhouse_stat     |          78.8 |           396.7 |    5.03 |      0.2  | False    |

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

**clickhouse_tuned:**
- Median runtime: 1615.2ms
- Average runtime: 2698.1ms
- Fastest query: 124.8ms
- Slowest query: 9982.5ms

**clickhouse:**
- Median runtime: 1608.8ms
- Average runtime: 2794.5ms
- Fastest query: 122.7ms
- Slowest query: 21093.3ms

**clickhouse_stat:**
- Median runtime: 1659.3ms
- Average runtime: 2549.7ms
- Fastest query: 153.7ms
- Slowest query: 21416.4ms

**exasol:**
- Median runtime: 165.9ms
- Average runtime: 214.4ms
- Fastest query: 20.7ms
- Slowest query: 699.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_30g-benchmark.zip`](exa_vs_ch_30g-benchmark.zip)

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

**Exasol 2025.1.0:**
- **Setup method:** installer
- **Data directory:** 
- **Applied configurations:**
  - dbram: 64g
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Clickhouse 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 64g
  - max_threads: 16
  - max_memory_usage: 60000000000

**Clickhouse_tuned 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 64g
  - max_threads: 16
  - max_memory_usage: 60000000000

**Clickhouse_stat 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 64g
  - max_threads: 16
  - max_memory_usage: 60000000000
  - allow_experimental_statistics: 1
  - allow_statistics_optimize: 1


## Methodology Notes

**Environment Consistency:**
- All systems tested on identical hardware specifications
- Same operating system and software versions
- Consistent resource allocation and container limits

**Execution Protocol:**
- 1 warmup run(s) per query (results discarded)
- 7 measured runs per query (results recorded)
- Wall-clock time measured by benchmark client
- Database processes restarted between test runs for consistency

**Configuration Management:**
- All tuning parameters documented in this post
- Configuration commands provided for exact reproduction
- System-specific optimizations applied as documented above
- Benchmark package contains all configuration files and scripts