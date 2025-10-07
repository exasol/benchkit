# Exasol vs ClickHouse Performance Comparison on TPC-H SF30

**Author:** Oleksandr Kozachuk, Principal Architect at Exasol AG
**Environment:** aws / eu-west-1 / r5d.4xlarge
**Date:** 2025-10-09 09:48:49

> **Note:** Sensitive information (passwords, IP addresses) has been sanitized for security reasons. Placeholders like `<EXASOL_DB_PASSWORD>`, `<PRIVATE_IP>`, and `<PUBLIC_IP>` are used throughout this document. When reproducing this benchmark, substitute these with your actual credentials and addresses.

This document shows exactly how the benchmark was run so it can be reproduced.

## Executive Summary

We compared 2 database systems:
- **clickhouse**
- **exasol**

**Key Findings:**
- exasol was the fastest overall with 164.3ms median runtime
- clickhouse was 9.7x slower
- Tested 308 total query executions across 22 different TPC-H queries

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
- **Hostname:** ip-10-0-1-8

### Clickhouse 25.9.3.48

**Software Configuration:**
- **Database:** clickhouse 25.9.3.48
- **Setup method:** native
- **Data directory:** /data/clickhouse

**Hardware Specifications:**
- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Instance Type:** r5d.4xlarge
- **CPU:** Intel(R) Xeon(R) Platinum 8259CL CPU @ 2.50GHz
- **CPU Cores:** 16 vCPUs
- **Memory:** 124.4GB RAM
- **Hostname:** ip-10-0-1-95


**Detailed system information:** See attachments for complete system specifications

## Test Environment

This benchmark was executed on the following infrastructure:

### Hardware Specifications

- **Cloud Provider:** AWS
- **Region:** eu-west-1
- **Exasol Instance:** r5d.4xlarge
- **Clickhouse Instance:** r5d.4xlarge


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



#### Clickhouse 25.9.3.48 Setup

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
sudo apt-get install -y clickhouse-server=25.9.3.48 clickhouse-client=25.9.3.48

```

**Configuration:**
```bash
# Create custom ClickHouse configuration file
sudo tee /etc/clickhouse-server/config.d/benchmark.xml &gt; /dev/null &lt;&lt; &#39;EOF&#39;
&lt;clickhouse&gt;
    &lt;listen_host&gt;::&lt;/listen_host&gt;
    &lt;path&gt;/data/clickhouse&lt;/path&gt;
    &lt;max_server_memory_usage&gt;106897729126&lt;/max_server_memory_usage&gt;
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
            &lt;max_bytes_before_external_sort&gt;73492188774&lt;/max_bytes_before_external_sort&gt;
            &lt;max_bytes_before_external_group_by&gt;73492188774&lt;/max_bytes_before_external_group_by&gt;
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
| Clickhouse | 132.74s | 32.19s | 164.93s | New infrastructure |
| Exasol | 132.74s | 570.02s | 702.76s | New infrastructure |

**Infrastructure Provisioning:** 132.74s
- Cloud instances were provisioned (VMs created, networking configured)

**Software Installation Comparison:**
- Clickhouse had the fastest software installation at 32.19s
- Exasol took 570.02s to install (17.7x slower)


### Workload Preparation Timings


### Performance Summary

| query   | system     |   runs |   median_ms |   mean_ms |   std_ms |   min_ms |   max_ms |
|---------|------------|--------|-------------|-----------|----------|----------|----------|
| Q01     | clickhouse |      7 |      1597   |    1601.8 |     13.5 |   1584.2 |   1617.4 |
| Q01     | exasol     |      7 |       606.3 |     606.7 |      2   |    604.2 |    610.4 |
| Q02     | clickhouse |      7 |       612.9 |     609.4 |      8.9 |    595.2 |    617.9 |
| Q02     | exasol     |      7 |        48.3 |      48.4 |      0.8 |     47.2 |     49.4 |
| Q03     | clickhouse |      7 |      2371.4 |    2381.9 |     34.8 |   2345.4 |   2446.2 |
| Q03     | exasol     |      7 |       206.1 |     204.4 |      4.9 |    193.6 |    208.2 |
| Q04     | clickhouse |      7 |      1365.1 |    1359.4 |     44.1 |   1316.1 |   1429.5 |
| Q04     | exasol     |      7 |        46.3 |      46.2 |      0.4 |     45.7 |     46.7 |
| Q05     | clickhouse |      7 |      5278.6 |    5290.5 |     38.9 |   5261.1 |   5375.7 |
| Q05     | exasol     |      7 |       148.9 |     150.5 |      3.5 |    147.9 |    157.7 |
| Q06     | clickhouse |      7 |       122.5 |     123   |      1.8 |    121.5 |    126.9 |
| Q06     | exasol     |      7 |        30.9 |      30.8 |      0.1 |     30.6 |     31   |
| Q07     | clickhouse |      7 |      2936.8 |    2915.8 |     85.2 |   2750.8 |   3019.6 |
| Q07     | exasol     |      7 |       172.2 |     172.1 |      0.7 |    170.9 |    172.9 |
| Q08     | clickhouse |      7 |      5668.4 |    5642.5 |     52   |   5571.1 |   5701.6 |
| Q08     | exasol     |      7 |        57.5 |      60.7 |      8.4 |     56.8 |     79.7 |
| Q09     | clickhouse |      7 |      7596.1 |    7584.1 |     58.1 |   7483.4 |   7664.5 |
| Q09     | exasol     |      7 |       657.4 |     657.7 |      1.4 |    656.3 |    660.7 |
| Q10     | clickhouse |      7 |      1652.5 |    1635.2 |     53.1 |   1560.1 |   1692.3 |
| Q10     | exasol     |      7 |       333.6 |     333.1 |      2.8 |    327.1 |    335.3 |
| Q11     | clickhouse |      7 |       384.6 |     383.8 |      5.1 |    376.9 |    390.2 |
| Q11     | exasol     |      7 |       118.8 |     119.3 |      1.3 |    117.4 |    121   |
| Q12     | clickhouse |      7 |       522   |     524.7 |     11.9 |    505.1 |    539.3 |
| Q12     | exasol     |      7 |        62.3 |      62.4 |      0.8 |     61.4 |     63.6 |
| Q13     | clickhouse |      7 |      2346.3 |    2354.1 |    118.2 |   2134   |   2515.4 |
| Q13     | exasol     |      7 |       437.8 |     437.8 |      1.4 |    436.2 |    439.3 |
| Q14     | clickhouse |      7 |       128.3 |     128.4 |      0.8 |    127.5 |    129.6 |
| Q14     | exasol     |      7 |        55.9 |      56.2 |      0.7 |     55.7 |     57.5 |
| Q15     | clickhouse |      7 |       155.3 |     158   |      5.4 |    154.1 |    168.5 |
| Q15     | exasol     |      7 |       200.3 |     200.9 |      2.3 |    198.7 |    205.7 |
| Q16     | clickhouse |      7 |       334.6 |     340   |     11.6 |    330.6 |    360.2 |
| Q16     | exasol     |      7 |       369.8 |     372.7 |     10.6 |    364.5 |    395.9 |
| Q17     | clickhouse |      7 |      2567.9 |    2565.2 |     25   |   2514.6 |   2595.1 |
| Q17     | exasol     |      7 |        20.1 |      20   |      0.4 |     19.2 |     20.6 |
| Q18     | clickhouse |      7 |      2516   |    2525.4 |     27.7 |   2504.6 |   2584.7 |
| Q18     | exasol     |      7 |       409.4 |     410.3 |      2.2 |    408.4 |    414.7 |
| Q19     | clickhouse |      7 |      1595.9 |    1606.8 |     25.4 |   1575.2 |   1650.2 |
| Q19     | exasol     |      7 |        19.9 |      19.8 |      0.3 |     19.4 |     20.1 |
| Q20     | clickhouse |      7 |       216.8 |     216.9 |      4.4 |    210.4 |    223.6 |
| Q20     | exasol     |      7 |       221.4 |     221   |      1.2 |    218.7 |    222.4 |
| Q21     | clickhouse |      7 |     20754.4 |   20738.3 |     78   |  20638.5 |  20866.1 |
| Q21     | exasol     |      7 |       253.2 |     258.5 |     14.2 |    250.5 |    290.1 |
| Q22     | clickhouse |      7 |       381.9 |     379.6 |      7.9 |    365.1 |    389.8 |
| Q22     | exasol     |      7 |        76   |      76.1 |      0.4 |     75.6 |     76.6 |

### System Comparison

| query   | baseline_system   | comparison_system   |   baseline_ms |   comparison_ms |   ratio |   speedup | faster   |
|---------|-------------------|---------------------|---------------|-----------------|---------|-----------|----------|
| Q01     | clickhouse        | exasol              |        1597   |           606.3 |    0.38 |      2.63 | True     |
| Q02     | clickhouse        | exasol              |         612.9 |            48.3 |    0.08 |     12.69 | True     |
| Q03     | clickhouse        | exasol              |        2371.4 |           206.1 |    0.09 |     11.51 | True     |
| Q04     | clickhouse        | exasol              |        1365.1 |            46.3 |    0.03 |     29.48 | True     |
| Q05     | clickhouse        | exasol              |        5278.6 |           148.9 |    0.03 |     35.45 | True     |
| Q06     | clickhouse        | exasol              |         122.5 |            30.9 |    0.25 |      3.96 | True     |
| Q07     | clickhouse        | exasol              |        2936.8 |           172.2 |    0.06 |     17.05 | True     |
| Q08     | clickhouse        | exasol              |        5668.4 |            57.5 |    0.01 |     98.58 | True     |
| Q09     | clickhouse        | exasol              |        7596.1 |           657.4 |    0.09 |     11.55 | True     |
| Q10     | clickhouse        | exasol              |        1652.5 |           333.6 |    0.2  |      4.95 | True     |
| Q11     | clickhouse        | exasol              |         384.6 |           118.8 |    0.31 |      3.24 | True     |
| Q12     | clickhouse        | exasol              |         522   |            62.3 |    0.12 |      8.38 | True     |
| Q13     | clickhouse        | exasol              |        2346.3 |           437.8 |    0.19 |      5.36 | True     |
| Q14     | clickhouse        | exasol              |         128.3 |            55.9 |    0.44 |      2.3  | True     |
| Q15     | clickhouse        | exasol              |         155.3 |           200.3 |    1.29 |      0.78 | False    |
| Q16     | clickhouse        | exasol              |         334.6 |           369.8 |    1.11 |      0.9  | False    |
| Q17     | clickhouse        | exasol              |        2567.9 |            20.1 |    0.01 |    127.76 | True     |
| Q18     | clickhouse        | exasol              |        2516   |           409.4 |    0.16 |      6.15 | True     |
| Q19     | clickhouse        | exasol              |        1595.9 |            19.9 |    0.01 |     80.2  | True     |
| Q20     | clickhouse        | exasol              |         216.8 |           221.4 |    1.02 |      0.98 | False    |
| Q21     | clickhouse        | exasol              |       20754.4 |           253.2 |    0.01 |     81.97 | True     |
| Q22     | clickhouse        | exasol              |         381.9 |            76   |    0.2  |      5.02 | True     |

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

**clickhouse:**
- Median runtime: 1592.7ms
- Average runtime: 2775.7ms
- Fastest query: 121.5ms
- Slowest query: 20866.1ms

**exasol:**
- Median runtime: 164.3ms
- Average runtime: 207.5ms
- Fastest query: 19.2ms
- Slowest query: 660.7ms


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

**Clickhouse 25.9.3.48:**
- **Setup method:** native
- **Data directory:** /data/clickhouse
- **Applied configurations:**
  - memory_limit: 64g
  - max_threads: 16
  - max_memory_usage: 60000000000


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