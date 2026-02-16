# Exasol vs ClickHouse Performance Comparison on TPC-H SF1

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-24 14:26:01

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 4 database systems:
- **exasol**
- **clickhouse**
- **clickhouse_tuned**
- **clickhouse_stat**

**Key Findings:**
- exasol was the fastest overall with 19.9ms median runtime
- clickhouse_tuned was 4.6x slower
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
- **Hostname:** ip-10-0-1-232

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
- **Hostname:** ip-10-0-1-163

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
- **Hostname:** ip-10-0-1-179

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
- **Hostname:** ip-10-0-1-78


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
sudo parted /dev/md0 mklabel gpt

# Execute sudo command on remote system
sudo parted -s /dev/md0 mklabel gpt

# Create 3GB partition for data generation
sudo parted /dev/md0 mkpart primary ext4 1MiB 3GiB

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary ext4 1MiB 3GiB

# Create raw partition for Exasol (555GB)
sudo parted /dev/md0 mkpart primary 3GiB 100%

# Execute sudo command on remote system
sudo parted -s /dev/md0 mkpart primary 3GiB 100%

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
- Database RAM: `32g`
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
    &lt;max_server_memory_usage&gt;106897738956&lt;/max_server_memory_usage&gt;
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
            &lt;max_memory_usage&gt;30000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492195532&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492195532&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `32g`
- Max threads: `16`
- Max memory usage: `30.0GB`

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
    &lt;max_server_memory_usage&gt;106897738956&lt;/max_server_memory_usage&gt;
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
            &lt;max_memory_usage&gt;30000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492195532&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492195532&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `32g`
- Max threads: `16`
- Max memory usage: `30.0GB`

**Data Directory:** `/data/clickhouse`



#### Clickhouse_stat 25.9.4.58 Setup

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
    &lt;max_server_memory_usage&gt;106897732403&lt;/max_server_memory_usage&gt;
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
            &lt;max_memory_usage&gt;30000000000&lt;/max_memory_usage&gt;
            &lt;max_bytes_before_external_sort&gt;73492191027&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492191027&lt;/max_bytes_before_external_group_by&gt;
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
- Memory limit: `32g`
- Max threads: `16`
- Max memory usage: `30.0GB`

**Data Directory:** `/data/clickhouse`




## Workload Configuration

### Benchmark Parameters

- **Workload:** TPCH
- **Scale factor:** 1
- **Data format:** csv
- **Queries tested:** All standard TPCH queries (Q01-Q22)
- **Warmup runs per query:** 1
- **Measured runs per query:** 7

### Execution Command

This benchmark is completely self-contained and includes all tuning configurations:

```bash
# Extract and run the benchmark
unzip exa_vs_ch_1g-benchmark.zip
cd exa_vs_ch_1g

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
| Clickhouse | 131.65s | 35.23s | 166.88s | New infrastructure |
| Clickhouse_stat | 131.65s | 38.37s | 170.03s | New infrastructure |
| Clickhouse_tuned | 131.65s | 38.79s | 170.44s | New infrastructure |
| Exasol | 131.65s | 554.02s | 685.67s | New infrastructure |

**Infrastructure Provisioning:** 131.65s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse had the fastest software installation at 35.23s
- Exasol took 554.02s to install (15.7x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system           |   warmup |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------------|----------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse       |     85.3 |      7 |        83.9 |      88.1 |      7.8 |     81   |    100.1 |
| Q01     | clickhouse_stat  |     83.9 |      7 |        79.7 |      82.8 |      7.9 |     78.2 |    100.5 |
| Q01     | clickhouse_tuned |     86.1 |      7 |        82.5 |      82.8 |      7.6 |     76.3 |     98.8 |
| Q01     | exasol           |     30.7 |      7 |        28.8 |      28.8 |      0.3 |     28.4 |     29.3 |
| Q02     | clickhouse       |     89.1 |      7 |        62.7 |      62.6 |      1.7 |     60.7 |     64.8 |
| Q02     | clickhouse_stat  |     75.2 |      7 |        62.9 |      63.6 |      2.5 |     60.4 |     68   |
| Q02     | clickhouse_tuned |     89.8 |      7 |        61   |      61.3 |      1.7 |     59.4 |     63.1 |
| Q02     | exasol           |     48.7 |      7 |        23.1 |      23.3 |      0.8 |     22.4 |     24.9 |
| Q03     | clickhouse       |    105.6 |      7 |        94.9 |      95.4 |      5.6 |     89.6 |    103.8 |
| Q03     | clickhouse_stat  |    121.4 |      7 |       107.1 |     109.3 |      6.9 |    102.5 |    120.2 |
| Q03     | clickhouse_tuned |    102.8 |      7 |        88   |      91.4 |      5.3 |     87.8 |    102   |
| Q03     | exasol           |     22.4 |      7 |        22.3 |      22.1 |      0.5 |     21.4 |     22.8 |
| Q04     | clickhouse       |     74.5 |      7 |        68.9 |      69.3 |      2.8 |     66.6 |     74.8 |
| Q04     | clickhouse_stat  |     76   |      7 |        73.7 |      73.8 |      1.7 |     71.4 |     76.2 |
| Q04     | clickhouse_tuned |    135.2 |      7 |       129.5 |     134.7 |      9.1 |    125.9 |    149.9 |
| Q04     | exasol           |     10.9 |      7 |         9   |       9.2 |      0.4 |      8.8 |      9.9 |
| Q05     | clickhouse       |    209.7 |      7 |       183.5 |     182.6 |      3.8 |    176.8 |    187.8 |
| Q05     | clickhouse_stat  |    223.6 |      7 |       202.4 |     205.4 |      9.2 |    194.3 |    218.5 |
| Q05     | clickhouse_tuned |    197.2 |      7 |       180.9 |     180   |      4.2 |    174   |    187   |
| Q05     | exasol           |     34   |      7 |        19.2 |      19.4 |      0.4 |     19   |     20   |
| Q06     | clickhouse       |     27.7 |      7 |        21.9 |      22.1 |      0.6 |     21.7 |     23.4 |
| Q06     | clickhouse_stat  |     30.2 |      7 |        25.1 |      28   |      7.7 |     24.9 |     45.4 |
| Q06     | clickhouse_tuned |     27.6 |      7 |        21.6 |      21.6 |      0.3 |     21.2 |     22.1 |
| Q06     | exasol           |      5.9 |      7 |         5.8 |       5.8 |      0.3 |      5.7 |      6.4 |
| Q07     | clickhouse       |    109.2 |      7 |       105.3 |     105.6 |      0.7 |    104.9 |    106.6 |
| Q07     | clickhouse_stat  |    121.8 |      7 |       116.1 |     116.4 |      1.7 |    113.7 |    118.3 |
| Q07     | clickhouse_tuned |    116.8 |      7 |       105.9 |     108.3 |      5.4 |    102.1 |    116.2 |
| Q07     | exasol           |     22.9 |      7 |        19.8 |      19.7 |      0.2 |     19.5 |     20   |
| Q08     | clickhouse       |    160.5 |      7 |       146.2 |     150.7 |      9.5 |    143.6 |    170.1 |
| Q08     | clickhouse_stat  |     97.9 |      7 |        88.4 |      88.1 |      1   |     86.4 |     89.2 |
| Q08     | clickhouse_tuned |    156.2 |      7 |       138.9 |     140.9 |      4.6 |    136.1 |    147.3 |
| Q08     | exasol           |     18.8 |      7 |        17.6 |      19.9 |      6   |     17.3 |     33.5 |
| Q09     | clickhouse       |    209.5 |      7 |       201.5 |     201.1 |      9.2 |    190.9 |    214.4 |
| Q09     | clickhouse_stat  |    157.3 |      7 |       122.5 |     123.2 |      2.4 |    120.7 |    126.1 |
| Q09     | clickhouse_tuned |    212.3 |      7 |       183.2 |     184.2 |      3.9 |    180.6 |    192.7 |
| Q09     | exasol           |     38.2 |      7 |        31.8 |      31.8 |      0.3 |     31.5 |     32.4 |
| Q10     | clickhouse       |    114.6 |      7 |       103.5 |     104   |      6.4 |     96.4 |    115.1 |
| Q10     | clickhouse_stat  |    414.6 |      7 |       404.8 |     400.9 |     35.6 |    337.7 |    444.1 |
| Q10     | clickhouse_tuned |    107.2 |      7 |        95.5 |      96.5 |      6.1 |     90.1 |    109.5 |
| Q10     | exasol           |     48.2 |      7 |        43.7 |      43.7 |      0.5 |     42.9 |     44.5 |
| Q11     | clickhouse       |     44.6 |      7 |        38.7 |      38.6 |      0.7 |     37.9 |     39.5 |
| Q11     | clickhouse_stat  |     45.8 |      7 |        45.5 |      45.9 |      1.6 |     44.4 |     49.2 |
| Q11     | clickhouse_tuned |     45.6 |      7 |        38.2 |      38.3 |      0.7 |     37.3 |     39.3 |
| Q11     | exasol           |     22.2 |      7 |        21.2 |      21.2 |      0.5 |     20.2 |     21.8 |
| Q12     | clickhouse       |     63.3 |      7 |        37.8 |      40.9 |      7   |     37.1 |     56.3 |
| Q12     | clickhouse_stat  |     65.3 |      7 |        56.2 |      55.9 |      9.9 |     46.9 |     75.8 |
| Q12     | clickhouse_tuned |     63.6 |      7 |        37.6 |      40.6 |      7.3 |     36.8 |     57   |
| Q12     | exasol           |     12.8 |      7 |        10.8 |      10.9 |      0.3 |     10.5 |     11.4 |
| Q13     | clickhouse       |    113.7 |      7 |       109.9 |     111.1 |     13.5 |     88.7 |    134.7 |
| Q13     | clickhouse_stat  |    103.4 |      7 |       104.1 |     107.4 |     17.3 |     88.2 |    137.9 |
| Q13     | clickhouse_tuned |    107.1 |      7 |       109.2 |     104.4 |     13   |     84.4 |    121.3 |
| Q13     | exasol           |     40.4 |      7 |        36.3 |      36.5 |      0.9 |     35.2 |     38   |
| Q14     | clickhouse       |     34.9 |      7 |        28.4 |      29.8 |      2.4 |     27.8 |     34   |
| Q14     | clickhouse_stat  |     42.2 |      7 |        38   |      38.7 |      1.4 |     37.5 |     41.2 |
| Q14     | clickhouse_tuned |     33.3 |      7 |        31.7 |      30.8 |      2.6 |     27.6 |     33.5 |
| Q14     | exasol           |      9   |      7 |         8.5 |       8.5 |      0.1 |      8.4 |      8.7 |
| Q15     | clickhouse       |     36.1 |      7 |        32   |      32.1 |      1.7 |     30.5 |     35.7 |
| Q15     | clickhouse_stat  |     44.3 |      7 |        40.2 |      40.3 |      1.3 |     38.3 |     41.6 |
| Q15     | clickhouse_tuned |     38.2 |      7 |        34.1 |      33.6 |      1.4 |     32.1 |     35.6 |
| Q15     | exasol           |     19.8 |      7 |        18.3 |      18.6 |      0.7 |     17.8 |     19.7 |
| Q16     | clickhouse       |     92.4 |      7 |        84.7 |      87.8 |      7.7 |     83.2 |    105.1 |
| Q16     | clickhouse_stat  |     94.3 |      7 |        92.4 |      95.5 |      8.6 |     89.6 |    114.4 |
| Q16     | clickhouse_tuned |    100.1 |      7 |        96.9 |      98.6 |      7.1 |     91.9 |    114   |
| Q16     | exasol           |     95.8 |      7 |        92.2 |      94.5 |      6.7 |     91.1 |    109.5 |
| Q17     | clickhouse       |    131.9 |      7 |        94.4 |      94.2 |      0.9 |     92.8 |     95.1 |
| Q17     | clickhouse_stat  |    138.7 |      7 |       103.9 |     104.1 |      2.2 |    100.5 |    107   |
| Q17     | clickhouse_tuned |     57.4 |      7 |        48.6 |      48.9 |      1.2 |     47.8 |     50.9 |
| Q17     | exasol           |     12.2 |      7 |        10.6 |      10.8 |      0.3 |     10.4 |     11.3 |
| Q18     | clickhouse       |    124.8 |      7 |        95.9 |      96   |      1.3 |     94.8 |     98.6 |
| Q18     | clickhouse_stat  |    141   |      7 |       113.4 |     117   |     10.4 |    111.1 |    140.3 |
| Q18     | clickhouse_tuned |    288.9 |      7 |       212.7 |     213.6 |     13.3 |    199.2 |    233.5 |
| Q18     | exasol           |     29.2 |      7 |        25.8 |      26.3 |      1.1 |     25.5 |     28.4 |
| Q19     | clickhouse       |     89.4 |      7 |        83.5 |      84.2 |      1.9 |     81.7 |     86.5 |
| Q19     | clickhouse_stat  |    137.1 |      7 |       133   |     132.1 |     14.5 |    113.3 |    149   |
| Q19     | clickhouse_tuned |    195.2 |      7 |       183.4 |     182.7 |      2.5 |    178.3 |    185.3 |
| Q19     | exasol           |     10.4 |      7 |         9.8 |       9.7 |      0.7 |      8.8 |     10.6 |
| Q20     | clickhouse       |     44.1 |      7 |        37.2 |      37.5 |      1.2 |     36.3 |     39   |
| Q20     | clickhouse_stat  |     49.9 |      7 |        46.6 |      47.1 |      1.5 |     45.7 |     49.8 |
| Q20     | clickhouse_tuned |     86.3 |      7 |        63.7 |      63.7 |      1.5 |     61.5 |     65.8 |
| Q20     | exasol           |     20.3 |      7 |        19.9 |      20   |      0.5 |     19.4 |     20.7 |
| Q21     | clickhouse       |    605.8 |      7 |       552.6 |     555.3 |     17.9 |    535.1 |    581.7 |
| Q21     | clickhouse_stat  |    577.8 |      7 |       560.3 |     563.3 |     29.4 |    523.4 |    612.8 |
| Q21     | clickhouse_tuned |    382.8 |      7 |       289.2 |     293.8 |     11   |    282   |    308.5 |
| Q21     | exasol           |     21.8 |      7 |        22.5 |      24.1 |      4.3 |     21.8 |     33.7 |
| Q22     | clickhouse       |     50.7 |      7 |        50.6 |      52.9 |      6.4 |     49.8 |     67.4 |
| Q22     | clickhouse_stat  |     59.2 |      7 |        55.1 |      57.7 |      6.4 |     54.7 |     72   |
| Q22     | clickhouse_tuned |     49.2 |      7 |        46.1 |      49.4 |      6   |     45.2 |     62   |
| Q22     | exasol           |     15.4 |      7 |        13   |      13   |      0.2 |     12.8 |     13.3 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | exasol            | clickhouse_tuned    |          28.8 |            82.5 |    2.86 |      0.35 | False    |
| Q02     | exasol            | clickhouse_tuned    |          23.1 |            61   |    2.64 |      0.38 | False    |
| Q03     | exasol            | clickhouse_tuned    |          22.3 |            88   |    3.95 |      0.25 | False    |
| Q04     | exasol            | clickhouse_tuned    |           9   |           129.5 |   14.39 |      0.07 | False    |
| Q05     | exasol            | clickhouse_tuned    |          19.2 |           180.9 |    9.42 |      0.11 | False    |
| Q06     | exasol            | clickhouse_tuned    |           5.8 |            21.6 |    3.72 |      0.27 | False    |
| Q07     | exasol            | clickhouse_tuned    |          19.8 |           105.9 |    5.35 |      0.19 | False    |
| Q08     | exasol            | clickhouse_tuned    |          17.6 |           138.9 |    7.89 |      0.13 | False    |
| Q09     | exasol            | clickhouse_tuned    |          31.8 |           183.2 |    5.76 |      0.17 | False    |
| Q10     | exasol            | clickhouse_tuned    |          43.7 |            95.5 |    2.19 |      0.46 | False    |
| Q11     | exasol            | clickhouse_tuned    |          21.2 |            38.2 |    1.8  |      0.55 | False    |
| Q12     | exasol            | clickhouse_tuned    |          10.8 |            37.6 |    3.48 |      0.29 | False    |
| Q13     | exasol            | clickhouse_tuned    |          36.3 |           109.2 |    3.01 |      0.33 | False    |
| Q14     | exasol            | clickhouse_tuned    |           8.5 |            31.7 |    3.73 |      0.27 | False    |
| Q15     | exasol            | clickhouse_tuned    |          18.3 |            34.1 |    1.86 |      0.54 | False    |
| Q16     | exasol            | clickhouse_tuned    |          92.2 |            96.9 |    1.05 |      0.95 | False    |
| Q17     | exasol            | clickhouse_tuned    |          10.6 |            48.6 |    4.58 |      0.22 | False    |
| Q18     | exasol            | clickhouse_tuned    |          25.8 |           212.7 |    8.24 |      0.12 | False    |
| Q19     | exasol            | clickhouse_tuned    |           9.8 |           183.4 |   18.71 |      0.05 | False    |
| Q20     | exasol            | clickhouse_tuned    |          19.9 |            63.7 |    3.2  |      0.31 | False    |
| Q21     | exasol            | clickhouse_tuned    |          22.5 |           289.2 |   12.85 |      0.08 | False    |
| Q22     | exasol            | clickhouse_tuned    |          13   |            46.1 |    3.55 |      0.28 | False    |
| Q01     | exasol            | clickhouse          |          28.8 |            83.9 |    2.91 |      0.34 | False    |
| Q02     | exasol            | clickhouse          |          23.1 |            62.7 |    2.71 |      0.37 | False    |
| Q03     | exasol            | clickhouse          |          22.3 |            94.9 |    4.26 |      0.23 | False    |
| Q04     | exasol            | clickhouse          |           9   |            68.9 |    7.66 |      0.13 | False    |
| Q05     | exasol            | clickhouse          |          19.2 |           183.5 |    9.56 |      0.1  | False    |
| Q06     | exasol            | clickhouse          |           5.8 |            21.9 |    3.78 |      0.26 | False    |
| Q07     | exasol            | clickhouse          |          19.8 |           105.3 |    5.32 |      0.19 | False    |
| Q08     | exasol            | clickhouse          |          17.6 |           146.2 |    8.31 |      0.12 | False    |
| Q09     | exasol            | clickhouse          |          31.8 |           201.5 |    6.34 |      0.16 | False    |
| Q10     | exasol            | clickhouse          |          43.7 |           103.5 |    2.37 |      0.42 | False    |
| Q11     | exasol            | clickhouse          |          21.2 |            38.7 |    1.83 |      0.55 | False    |
| Q12     | exasol            | clickhouse          |          10.8 |            37.8 |    3.5  |      0.29 | False    |
| Q13     | exasol            | clickhouse          |          36.3 |           109.9 |    3.03 |      0.33 | False    |
| Q14     | exasol            | clickhouse          |           8.5 |            28.4 |    3.34 |      0.3  | False    |
| Q15     | exasol            | clickhouse          |          18.3 |            32   |    1.75 |      0.57 | False    |
| Q16     | exasol            | clickhouse          |          92.2 |            84.7 |    0.92 |      1.09 | True     |
| Q17     | exasol            | clickhouse          |          10.6 |            94.4 |    8.91 |      0.11 | False    |
| Q18     | exasol            | clickhouse          |          25.8 |            95.9 |    3.72 |      0.27 | False    |
| Q19     | exasol            | clickhouse          |           9.8 |            83.5 |    8.52 |      0.12 | False    |
| Q20     | exasol            | clickhouse          |          19.9 |            37.2 |    1.87 |      0.53 | False    |
| Q21     | exasol            | clickhouse          |          22.5 |           552.6 |   24.56 |      0.04 | False    |
| Q22     | exasol            | clickhouse          |          13   |            50.6 |    3.89 |      0.26 | False    |
| Q01     | exasol            | clickhouse_stat     |          28.8 |            79.7 |    2.77 |      0.36 | False    |
| Q02     | exasol            | clickhouse_stat     |          23.1 |            62.9 |    2.72 |      0.37 | False    |
| Q03     | exasol            | clickhouse_stat     |          22.3 |           107.1 |    4.8  |      0.21 | False    |
| Q04     | exasol            | clickhouse_stat     |           9   |            73.7 |    8.19 |      0.12 | False    |
| Q05     | exasol            | clickhouse_stat     |          19.2 |           202.4 |   10.54 |      0.09 | False    |
| Q06     | exasol            | clickhouse_stat     |           5.8 |            25.1 |    4.33 |      0.23 | False    |
| Q07     | exasol            | clickhouse_stat     |          19.8 |           116.1 |    5.86 |      0.17 | False    |
| Q08     | exasol            | clickhouse_stat     |          17.6 |            88.4 |    5.02 |      0.2  | False    |
| Q09     | exasol            | clickhouse_stat     |          31.8 |           122.5 |    3.85 |      0.26 | False    |
| Q10     | exasol            | clickhouse_stat     |          43.7 |           404.8 |    9.26 |      0.11 | False    |
| Q11     | exasol            | clickhouse_stat     |          21.2 |            45.5 |    2.15 |      0.47 | False    |
| Q12     | exasol            | clickhouse_stat     |          10.8 |            56.2 |    5.2  |      0.19 | False    |
| Q13     | exasol            | clickhouse_stat     |          36.3 |           104.1 |    2.87 |      0.35 | False    |
| Q14     | exasol            | clickhouse_stat     |           8.5 |            38   |    4.47 |      0.22 | False    |
| Q15     | exasol            | clickhouse_stat     |          18.3 |            40.2 |    2.2  |      0.46 | False    |
| Q16     | exasol            | clickhouse_stat     |          92.2 |            92.4 |    1    |      1    | False    |
| Q17     | exasol            | clickhouse_stat     |          10.6 |           103.9 |    9.8  |      0.1  | False    |
| Q18     | exasol            | clickhouse_stat     |          25.8 |           113.4 |    4.4  |      0.23 | False    |
| Q19     | exasol            | clickhouse_stat     |           9.8 |           133   |   13.57 |      0.07 | False    |
| Q20     | exasol            | clickhouse_stat     |          19.9 |            46.6 |    2.34 |      0.43 | False    |
| Q21     | exasol            | clickhouse_stat     |          22.5 |           560.3 |   24.9  |      0.04 | False    |
| Q22     | exasol            | clickhouse_stat     |          13   |            55.1 |    4.24 |      0.24 | False    |

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
- Median runtime: 91.8ms
- Average runtime: 104.6ms
- Fastest query: 21.2ms
- Slowest query: 308.5ms

**clickhouse:**
- Median runtime: 86.2ms
- Average runtime: 106.5ms
- Fastest query: 21.7ms
- Slowest query: 581.7ms

**clickhouse_stat:**
- Median runtime: 89.4ms
- Average runtime: 122.6ms
- Fastest query: 24.9ms
- Slowest query: 612.8ms

**exasol:**
- Median runtime: 19.9ms
- Average runtime: 23.5ms
- Fastest query: 5.7ms
- Slowest query: 109.5ms


### Raw Data

The complete dataset is available in the following files:
- **Query results:** [`attachments/runs.csv`](attachments/runs.csv)
- **Summary statistics:** [`attachments/summary.json`](attachments/summary.json)
- **System information:** [`attachments/system.json`](attachments/system.json)
- **Benchmark package:** [`exa_vs_ch_1g-benchmark.zip`](exa_vs_ch_1g-benchmark.zip)

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
  - dbram: 32g
  - optimizer_mode: analytical
  - db_params: [&#39;-writeTouchInit=1&#39;, &#39;-cacheMonitorLimit=0&#39;, &#39;-maxOverallSlbUsageRatio=0.95&#39;, &#39;-useQueryCache=0&#39;, &#39;-query_log_timeout=0&#39;, &#39;-joinOrderMethod=0&#39;, &#39;-etlCheckCertsDefault=0&#39;]

**Clickhouse 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 32g
  - max_threads: 16
  - max_memory_usage: 30000000000

**Clickhouse_tuned 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 32g
  - max_threads: 16
  - max_memory_usage: 30000000000

**Clickhouse_stat 25.9.4.58:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 32g
  - max_threads: 16
  - max_memory_usage: 30000000000
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