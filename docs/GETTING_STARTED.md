# Getting Started with the Database Benchmark Framework

This comprehensive guide will help you install, configure, and run your first database benchmark using the framework.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Your First Benchmark](#your-first-benchmark)
- [CLI Commands Reference](#cli-commands-reference)
- [Configuration Guide](#configuration-guide)
- [Cloud Deployment](#cloud-deployment)
- [Remote Deployment](#remote-deployment)
- [Customizing Benchmarks](#customizing-benchmarks)
- [Troubleshooting](#troubleshooting)
- [Example Workflows](#example-workflows)

## Prerequisites

### System Requirements (Benchmark Host)

- **Operating System**: Linux (Ubuntu 22.04+ recommended)
- **Python**: 3.10 or higher
- **Memory**: 2GB RAM minimum

### System Requirements (System Host)

- **Operating System**: Linux (Ubuntu 22.04+ recommended)
- **Python**: 3.10 or higher
- **Memory**: Depends on benchmark settings
- **Storage**: Depends on benchmark settings

### Software Dependencies (ubuntu syntax, when starting at zero)

```shell
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and development tools
sudo apt-get install -y python3.10 python3-pip python3-venv build-essential git

# Install Docker (optional, for containerized systems)
sudo apt-get install -y docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Log out and log back in for Docker group changes to take effect
```

## Installation

### 1. Clone the Repository

```shell
git clone https://github.com/exasol/benchkit.git
cd benchkit
```

### 2. Set Up Python Environment

```shell
# Create virtual environment
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Install the framework
pip install -e .

# Verify installation
benchkit --help
```

You should see the framework's help message with 13 main commands (plus the `suite` command group with 9 subcommands).

## Your First Benchmark

Let's run a simple benchmark comparing Exasol and ClickHouse on TPC-H queries.

### 1. Check the Sample Configuration

```bash
cat configs/exa_vs_ch_1g.yaml
```

This configuration defines:
- Three systems: Exasol, ClickHouse and Clickhouse with tuned queries
- TPC-H workload at scale factor 1
- 7 runs per query with 1 warmup run

### 2. Prepare Data Directory (Cloud: automatic, Local: required)

```bash
# Create data directory
sudo mkdir -p /data
sudo chown $USER:$USER /data

# Create system-specific directories
mkdir -p /data/{exasol,clickhouse,tpch}
```

> [!NOTE]
> For cloud (AWS) deployments, data directories are created automatically on remote instances.

### 3. Run the Benchmark

#### Option A: Run Everything at Once

The included Makefile provides some shortcuts combining multiple calls to `benchkit`.
Run `make` without arguments to get a command overview.

```bash
# Run the complete benchmark pipeline
make all CFG=configs/exa_vs_ch_1g.yaml
```

This will:
1. Probe system information
2. Run the benchmark
3. Generate a report
4. Leave the cloud infrastructure running

#### Option B: Run Step by Step

For more control, run each step individually:

```bash
# 1. Probe system information
benchkit probe --config configs/exa_vs_ch_1g.yaml

# 2. Run the benchmark
benchkit run --config configs/exa_vs_ch_1g.yaml

# 3. Generate report
benchkit report --config configs/exa_vs_ch_1g.yaml
```

### 4. Check Results

After the benchmark completes:

```bash
# View results directory
ls -la results/exa_vs_ch_1g/
```

## CLI Commands Reference

The framework provides 13 main commands plus 9 suite subcommands for complete benchmark lifecycle management.

### 1. `probe` - System Information Collection

Collect detailed system information for reproducibility:

```bash
# Probe all configured systems
benchkit probe --config configs/my_benchmark.yaml

# Probe specific systems only
benchkit probe --config configs/my_benchmark.yaml --systems exasol,clickhouse

# Enable debug output
benchkit probe --config configs/my_benchmark.yaml --debug
```

**Output**: Creates `results/<project_id>/system.json` (or `system_<systemname>.json` for cloud setups)

> [!IMPORTANT]
> Note that `probe` will automatically call `infra apply` if necessary, possibly starting cost-incurring services.

### 2. `run` - Execute Benchmarks

Execute benchmarks against configured database systems:

```bash
# Run all systems and queries
benchkit run --config configs/my_benchmark.yaml

# Run specific systems
benchkit run --config configs/my_benchmark.yaml --systems exasol

# Run specific queries
benchkit run --config configs/my_benchmark.yaml --queries Q01,Q06,Q13

# Run with multiple filters
benchkit run --config configs/my_benchmark.yaml --systems exasol --queries Q01,Q06

# Force rerun (overwrite existing results)
benchkit run --config configs/my_benchmark.yaml --force

# Enable debug output
benchkit run --config configs/my_benchmark.yaml --debug
```

**Output**: Creates `results/<project_id>/runs.csv` with all benchmark results

### 3. `execute` - Remote Execution

Execute workload against a specific system (used in remote packages):

```bash
# Execute on a specific system
benchkit execute --config config.yaml --system exasol

# With debug output
benchkit execute --config config.yaml --system exasol --debug
```

This command is primarily used when running benchmarks from extracted packages on remote systems.

### 4. `report` - Generate Reports

Create self-contained reports from benchmark results:

```bash
# Generate report from results
benchkit report --config configs/my_benchmark.yaml
```

**Output**: Creates a self-contained report directory:
```
results/<project-name>/reports/<report-name>
├── REPORT.md                         # Main report
├── REPORT.html                       # Main report (HTML format)
├── attachments/                      # All result files and figures
│   ├── runs.csv
│   ├── system.json
│   ├── config.yaml
│   └── figures/
└── <project>-workload.zip          # Minimal reproduction package
```

### 5. `status` - Project Status

Show comprehensive status of benchmark projects:

```bash
# Show overview of all projects (default)
benchkit status

# Show detailed status for specific config
benchkit status --config configs/my_benchmark.yaml

# Show status for multiple configs
benchkit status --config configs/bench1.yaml --config configs/bench2.yaml

# Show status for specific project by name
benchkit status --project my_benchmark_project_id
```

**Output Examples**:

1. **All Projects Overview** (default):
```
Benchmark Status Summary
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━┓
┃ Project     ┃ Systems      ┃ Workload ┃ Probe ┃ Bench ┃ Report ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━┩
│ exa_vs_ch   │ exasol, ch   │ tpch SF1 │   ✓   │   ✓   │   ✗    │
│ pg_vs_mysql │ postgres, my │ tpch SF10│   ✗   │   ✗   │   ✗    │
└─────────────┴──────────────┴──────────┴───────┴───────┴────────┘
```

2. **Detailed Status** (with config):
```
═══ my_benchmark ═══
Config: configs/my_benchmark.yaml

  Title           Database Performance Comparison
  Author          Your Name
  Environment     aws
  Systems         exasol, clickhouse
  Workload        tpch (SF=100)
  Queries/Runs    10 runs, 2 warmup

                           Status
┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status ┃ Details                            ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ System Info    │   ✓    │ 2 systems (14,062 bytes)           │
│ Benchmark      │   ✓    │ 308 queries across 2 systems       │
│ Reports        │   ✓    │ Generated at posts/my_benchmark/   │
│ Infrastructure │   ✓    │ Provisioned in 123.1s at 2025-10-06│
└────────────────┴────────┴────────────────────────────────────┘

System Installations: exasol: ✓ (529.1s), clickhouse: ✓ (33.5s)
```

3. **Infrastructure Details** (for cloud environments):
```
                      Infrastructure Details
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ System     ┃ Public IP     ┃ Private IP ┃ Connection String                               ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ exasol     │ 1.2.3.4       │ 10.0.1.5   │ exaplus -c 1.2.3.4:8563 -u sys -p <password> -s │
│            │               │            │ benchmark                                       │
│ clickhouse │ 5.6.7.8       │ 10.0.1.10  │ clickhouse-client --host 5.6.7.8 --port 9000    │
│            │               │            │ --user default --database benchmark --password  │
└────────────┴───────────────┴────────────┴─────────────────────────────────────────────────┘
```

**Features**:
- **Smart File Detection**: Detects both local (`system.json`) and cloud (`system_*.json`) patterns
- **Connection Strings**: Shows copy-pasteable CLI commands with all parameters (host, port, user, schema/database)
- **Infrastructure IPs**: Displays public and private IPs for cloud deployments
- **Timing Information**: Shows when infrastructure was provisioned and installation durations
- **Multiple Configs**: Can check status for multiple configurations at once

### 6. `infra` - Infrastructure Management

Manage cloud infrastructure with Terraform:

```bash
# Plan infrastructure changes
benchkit infra plan --provider aws --config configs/my_benchmark.yaml

# Deploy infrastructure
benchkit infra apply --provider aws --config configs/my_benchmark.yaml

# Deploy specific systems only
benchkit infra apply --provider aws --config configs/my_benchmark.yaml --systems exasol

# Deploy without waiting for initialization
benchkit infra apply --provider aws --config configs/my_benchmark.yaml --no-wait

# Destroy infrastructure
benchkit infra destroy --provider aws --config configs/my_benchmark.yaml
```

**Supported Providers**: Currently `aws` (GCP and Azure support coming)

### 7. `package` - Create Benchmark Packages

Create portable, minimal benchmark packages:

```bash
# Create package in default location
benchkit package --config configs/my_benchmark.yaml

# Create package in specific directory
benchkit package --config configs/my_benchmark.yaml --output packages/
```

**Output**: Creates a `.zip` file containing:
- Essential framework code (only what's needed for execution)
- Configuration files
- Workload definitions
- Execution scripts
- System-specific Python dependencies (dynamically determined)

### 8. `verify` - Result Verification

Validate query correctness against expected outputs:

```bash
# Verify all systems
benchkit verify --config configs/my_benchmark.yaml

# Verify specific systems
benchkit verify --config configs/my_benchmark.yaml --systems exasol

# With debug output
benchkit verify --config configs/my_benchmark.yaml --debug
```

> [!NOTE]
> Requires expected results in `workloads/<workload_name>/expected/`

### 9. `cleanup` - System Cleanup

Clean up running systems after benchmark execution:

```bash
# Cleanup with confirmation prompt
benchkit cleanup --config configs/my_benchmark.yaml

# Cleanup without confirmation
benchkit cleanup --config configs/my_benchmark.yaml --confirm
```

Use this to teardown systems without destroying cloud infrastructure.

### 10. `combine` - Merge Multiple Benchmarks

Combine benchmark results from multiple separately-run projects into a single unified project for comparison:

```bash
# Combine Exasol from one benchmark with ClickHouse from another
benchkit combine \
    --source configs/exasol_sf100.yaml:exasol \
    --source configs/clickhouse_sf100.yaml:clickhouse \
    --output exasol_vs_clickhouse

# Compare two versions with rename to avoid name conflicts
benchkit combine \
    --source configs/exasol_v8.yaml:exasol:exasol_v8 \
    --source configs/exasol_v9.yaml:exasol:exasol_v9 \
    --output exasol_version_comparison

# Combine with custom title and author
benchkit combine \
    --source proj1.yaml:sys1 \
    --source proj2.yaml:sys2 \
    --output combined \
    --title "Performance Comparison" \
    --author "Your Name"

# Combine without auto-generating report
benchkit combine \
    --source proj1.yaml:sys1 \
    --source proj2.yaml:sys2 \
    --output combined \
    --no-report
```

**Source Syntax**: `config.yaml:system1,system2` or with renaming: `config.yaml:sys1:new_name`

**Options**:
- `--source` / `-s` (required, multiple): Source specification
- `--output` / `-o` (required): Output project ID
- `--title` / `-t`: Report title
- `--author` / `-a`: Report author
- `--no-report`: Skip report generation
- `--force` / `-f`: Overwrite existing output

**Output**: Creates `results/<output>/` with merged results and regenerated report

> [!IMPORTANT]
> All source benchmarks must have identical workload configurations (scale factor, queries, runs per query) to be combined.

### 11. `suite` - Benchmark Suite Management

Orchestrate multiple related benchmarks as a cohesive study with state management and resumable runs:

```bash
# Initialize a new suite
benchkit suite init ./my-suite --name "My Benchmark Suite"

# List all configurations in a suite
benchkit suite list ./my-suite

# View execution plan without running (dry-run)
benchkit suite run ./my-suite --dry-run

# Run all benchmarks in a suite
benchkit suite run ./my-suite

# Run specific series only
benchkit suite run ./my-suite --series series_1_nodes

# Run specific benchmark
benchkit suite run ./my-suite --benchmark series_1_nodes/nodes_4

# Resume after interruption (skips completed benchmarks)
benchkit suite run ./my-suite --resume

# Run systems sequentially (reduces cloud resource pressure)
benchkit suite run ./my-suite --systems sequential

# Check status of all benchmarks
benchkit suite status ./my-suite

# Synchronize state with actual results
benchkit suite sync ./my-suite

# Generate reports for completed benchmarks
benchkit suite report ./my-suite

# Generate static comparison dashboard
benchkit suite publish ./my-suite --output docs/dashboard

# Reset suite state (clear completion markers)
benchkit suite reset ./my-suite

# Validate suite structure and configurations
benchkit suite validate ./my-suite
```

**Suite Structure**:
```
my-suite/
├── suite.yaml              # Suite configuration
├── series/
│   ├── series_1_nodes/     # Series directory
│   │   ├── nodes_1.yaml    # Benchmark configs
│   │   └── nodes_4.yaml
│   └── series_2_sf/
│       └── sf_100.yaml
└── .benchkit/              # State directory (auto-managed)
    └── state.json
```

**Suite Configuration (suite.yaml)**:
```yaml
name: "My Benchmark Suite"
version: "1.0.0"
description: "Performance study description"

series:
  series_1_nodes:
    name: "Node Scaling"
    description: "Test horizontal scaling"
    enabled: true
  series_2_sf:
    name: "Data Scaling"
    enabled: false  # Disabled series are skipped

execution:
  mode: sequential
  continue_on_failure: true
  pause_between: 30

infrastructure:
  cleanup_after_each: true
```

See [public/scalability/](../public/scalability/) for a comprehensive example.

## Configuration Guide

### Basic Configuration Structure

```yaml
project_id: "my_benchmark"           # Unique identifier
title: "My Database Comparison"      # Human-readable title
author: "Your Name"                  # Author attribution

env:                                 # Environment configuration
  mode: "local"                      # local, remote, aws, gcp, azure
  
systems:                             # Database systems to benchmark
  - name: "system1"
    kind: "exasol"
    version: "2025.1.0"
    setup:
      method: "installer"            # preinstalled, installer, native, docker
      extra: {}                      # System-specific parameters

workload:                            # Benchmark workload
  name: "tpch"
  scale_factor: 1
  queries:
    include: ["Q01", "Q06"]
  runs_per_query: 3
  warmup_runs: 1

report:                              # Report generation (optional)
  output_path: "posts/my-benchmark.md"
  show_boxplots: true
  show_heatmap: true
```

### Environment Modes

The framework supports three environment modes that control **where** your benchmark runs. Each mode determines how the framework connects to machines and manages infrastructure.

| Feature | Local | Remote | AWS |
|---------|-------|--------|-----|
| Infrastructure | Your machine | Pre-provisioned | Auto-provisioned (Terraform) |
| SSH required | No | Yes | Yes (automatic) |
| Disk setup | Manual | Automatic | Automatic |
| Setup methods | docker, preinstalled | installer, native, preinstalled | installer, native |
| Terraform | No | No | Yes |
| Best for | Dev/testing | Existing servers, on-prem | Reproducible cloud benchmarks |

#### Local Mode

```yaml
env:
  mode: "local"
```

Runs benchmarks on the current machine. The simplest mode — no SSH, no remote machines.

**When to use**: Development, testing, quick checks, or when the database is already running locally.

**Compatible setup methods**: `docker`, `preinstalled`

#### Remote Mode

```yaml
env:
  mode: "remote"
  nodes:
    exasol:
      public_ip: "54.93.100.10"
      private_ip: "10.0.1.5"
    clickhouse:
      public_ip: "54.93.100.20"
  ssh_private_key_path: "~/.ssh/benchmark-key.pem"
  ssh_user: "ubuntu"
```

Connects via SSH to pre-provisioned machines that you manage yourself. The framework handles disk setup, database installation, and benchmarking over SSH — identical to cloud mode, but without Terraform.

**When to use**: Existing servers, on-premises hardware, VMs from any provider, or machines provisioned outside the framework.

**Required fields**:
- `nodes` — maps each system name to its IP address(es)
- `ssh_private_key_path` — path to the SSH private key

**Node structure**: For single-node systems, use a dictionary with `public_ip` (and optionally `private_ip`). For multinode clusters, use a list of dictionaries:

```yaml
# Single node
nodes:
  exasol:
    public_ip: "54.93.100.10"
    private_ip: "10.0.1.5"

# Multinode cluster
nodes:
  exasol:
    - public_ip: "54.93.100.10"
      private_ip: "10.0.1.5"
    - public_ip: "54.93.100.11"
      private_ip: "10.0.1.6"
```

**Compatible setup methods**: `preinstalled`, `installer`, `native`

> [!NOTE]
> For `installer` configs in remote mode, use **literal IP addresses** (not `$VAR` references) because there is no Terraform state to resolve variables from.

#### AWS Mode

```yaml
env:
  mode: "aws"
  region: "eu-west-1"
  instances:
    exasol:
      instance_type: "m7i.4xlarge"   # 16 vCPUs, 64GB RAM
      disk:
        type: "nvme"
        size_gb: 40
    clickhouse:
      instance_type: "m7i.4xlarge"
      disk:
        type: "nvme"
        size_gb: 30
  os_image: "ubuntu-22.04"
  ssh_user: "ubuntu"
  ssh_private_key_path: "~/.ssh/id_rsa"
  ssh_key_name: "my-aws-key"         # Optional: for SSH access
```

Provisions separate EC2 instances for each system via Terraform, enabling:
- Native database installations
- Dedicated resources per system
- Network isolation
- Production-like environments

**When to use**: Reproducible benchmarks, production-scale tests, automated pipelines.

**Compatible setup methods**: `installer`, `native`

See [Cloud Deployment](#cloud-deployment) for the full AWS setup guide.

### Setup Methods

Setup methods control **how** the database gets installed on the target machine. They work in combination with [environment modes](#environment-modes) to cover different deployment scenarios.

#### `preinstalled`

The database is already running — benchkit just connects and runs queries. No installation, no disk setup.

```yaml
systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.1.0"
    setup:
      method: "preinstalled"
      host: "54.93.100.10"
      port: 8563
      username: "sys"
      password: "exasol456"
      schema: "BENCHMARK"
```

**Required fields**: `host`, `port`, credentials (`username`/`password`)

**Works with**: `local`, `remote`, `aws`

#### `installer`

Benchkit installs the database from scratch using the system's own installer tool. For Exasol, this means the c4 cluster tool. Includes disk setup and full configuration.

```yaml
systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.2.0"
    setup:
      method: "installer"
      node_count: 1
      use_additional_disk: true
      c4_version: "4.28.5"
      host_addrs: "10.0.1.5"
      host_external_addrs: "54.93.100.10"
      image_password: "exasol123"
      db_password: "exasol456"
      admin_password: "exasol789"
      db_mem_size: 12000
      schema: "BENCHMARK"
```

**Works with**: `remote`, `aws`

> [!IMPORTANT]
> In remote mode, use **literal IPs** in `host_addrs`/`host_external_addrs` — not `$VAR` references, since there is no Terraform state to resolve variables from.

#### `native`

Benchkit installs the database via system package manager (e.g., `apt` for ClickHouse). Includes disk setup and service configuration.

```yaml
systems:
  - name: "clickhouse"
    kind: "clickhouse"
    version: "25.1.3.23"
    setup:
      method: "native"
      use_additional_disk: true
      data_dir: "/data/clickhouse"
      host: "54.93.100.20"
      port: 8123
      username: "default"
      password: "clickhouse123"
      extra:
        max_memory_usage: "8000000000"
        max_threads: "16"
```

**Works with**: `remote`, `aws`

#### `docker`

Benchkit runs the database in a Docker container on the local machine. Only available in local mode.

```yaml
systems:
  - name: "clickhouse"
    kind: "clickhouse"
    version: "24.12"
    setup:
      method: "docker"
      container_name: "clickhouse_bench"
      host: "localhost"
      port: 9000
      http_port: 8123
      data_dir: "/data/clickhouse"
```

**Works with**: `local`

### System Configuration

#### Exasol System

```yaml
systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.1.0"
    setup:
      method: "installer"             # Native c4 installation
      host_addrs: "$EXASOL_PRIVATE_IP"
      host_external_addrs: "$EXASOL_PUBLIC_IP"
      data_dir: "/data/exasol"
      extra:
        dbram: "32g"                  # Database RAM allocation
        license_file: "/path/to/license.xml"
```

#### ClickHouse System

```yaml
systems:
  - name: "clickhouse"
    kind: "clickhouse"
    version: "24.12"
    setup:
      method: "native"                # APT package installation
      host: "$CLICKHOUSE_PRIVATE_IP"
      port: 9000
      http_port: 8123
      data_dir: "/data/clickhouse"
      extra:
        memory_limit: "32g"
        max_threads: "16"
        max_memory_usage: "30000000000"
```

### Workload Configuration

#### TPC-H Workload

```yaml
workload:
  name: "tpch"
  scale_factor: 100                   # Dataset size in GB
  queries:
    include: ["Q01", "Q03", "Q06"]    # Specific queries
    # OR
    # exclude: ["Q17", "Q20"]         # Exclude specific queries
  runs_per_query: 5                   # Repeat each query
  warmup_runs: 2                      # Warmup runs (not measured)
  query_timeout: 3600                 # Timeout in seconds
```

**Common Scale Factors**:
- SF 1 = 1GB (testing)
- SF 10 = 10GB (development)
- SF 100 = 100GB (production-like)
- SF 1000 = 1TB (large-scale)

## Cloud Deployment

### AWS Deployment

> [!NOTE]
> **Required AWS Permissions**: `ec2:*`, `ec2:DescribeImages`, `ec2:DescribeAvailabilityZones`

#### 1. Configure AWS Credentials

Choose one of these methods:

**Method A: .env File (Recommended)**

```bash
# Create .env file in project root
cat > .env << EOF
AWS_PROFILE=default-mfa
AWS_REGION=eu-west-1
EOF
```

**Method B: Environment Variables**

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=eu-west-1
```

**Method C: AWS CLI**

```bash
aws configure
# Or use profiles:
export AWS_PROFILE=benchmark-user
```

#### 2. Create SSH Key (Optional)

```bash
# Create EC2 key pair
aws ec2 create-key-pair \
  --key-name benchmark-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/benchmark-key.pem

chmod 600 ~/.ssh/benchmark-key.pem
```

#### 3. Update Configuration for AWS

```yaml
env:
  mode: "aws"
  region: "eu-west-1"
  ssh_key_name: "benchmark-key"      # Optional
  instances:
    exasol:
      instance_type: "m7i.4xlarge"
    clickhouse:
      instance_type: "m7i.4xlarge"
```

#### 4. Deploy Infrastructure

```bash
# Plan infrastructure
benchkit infra plan --provider aws --config configs/my_benchmark.yaml

# Review plan, then apply
benchkit infra apply --provider aws --config configs/my_benchmark.yaml
```

#### 5. Run Benchmark

```bash
# Probe remote systems
benchkit probe --config configs/my_benchmark.yaml

# Run benchmark
benchkit run --config configs/my_benchmark.yaml

# Generate report
benchkit report --config configs/my_benchmark.yaml
```

#### 6. Cleanup

```bash
# Remove infrastructure
benchkit infra destroy --provider aws --config configs/my_benchmark.yaml
```

### AWS Instance Type Selection

**For Analytical Workloads (TPC-H)**:
- `m7i.2xlarge` (8 vCPU, 32GB) - Small tests
- `m7i.4xlarge` (16 vCPU, 64GB) - Standard benchmarks
- `m7i.8xlarge` (32 vCPU, 128GB) - Large-scale benchmarks
- `r7i.4xlarge` (16 vCPU, 128GB) - Memory-intensive workloads

**Cost Considerations**:
- Use smaller instances for development/testing
- Scale up for production benchmarks
- Consider spot instances for cost savings
- Remember to destroy infrastructure when done

## Remote Deployment

Remote mode lets you run benchmarks on pre-provisioned machines — servers you already have access to via SSH. This is useful for on-premises hardware, VMs from any cloud provider, shared infrastructure, or machines provisioned outside the framework.

Unlike AWS mode, remote mode does **not** use Terraform. You provide the IP addresses directly in the configuration, and the framework handles everything else (disk setup, database installation, data loading, benchmarking) over SSH.

### Prerequisites

- SSH access to the target machine(s)
- An SSH private key file
- Ubuntu 22.04 (or a supported OS) on the target machines
- The SSH user must have `sudo` access (for disk setup and installation)

### Remote with Preinstalled Database

The simplest remote scenario: the database is already installed and running. Benchkit just connects and runs queries.

```yaml
project_id: "remote_exasol_bench"
title: "Remote Exasol Benchmark"
author: "Benchmark Team"

env:
  mode: "remote"
  nodes:
    exasol:
      public_ip: "54.93.100.10"
  ssh_private_key_path: "~/.ssh/benchmark-key.pem"
  ssh_user: "ubuntu"

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.2.0"
    setup:
      method: "preinstalled"
      host: "54.93.100.10"
      port: 8563
      username: "sys"
      password: "exasol456"
      schema: "BENCHMARK"

workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
```

**Workflow**:

```bash
benchkit check --config configs/remote_preinstalled.yaml
benchkit run --config configs/remote_preinstalled.yaml
benchkit report --config configs/remote_preinstalled.yaml
```

### Remote with Installer

For a fresh machine where benchkit installs the database from scratch. Disk setup runs automatically (identical to cloud mode).

```yaml
project_id: "remote_exasol_install"
title: "Remote Exasol (Fresh Install)"
author: "Benchmark Team"

env:
  mode: "remote"
  nodes:
    exasol:
      public_ip: "54.93.100.10"
      private_ip: "10.0.1.5"
  ssh_private_key_path: "~/.ssh/benchmark-key.pem"
  ssh_user: "ubuntu"

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.2.0"
    setup:
      method: "installer"
      node_count: 1
      use_additional_disk: true
      c4_version: "4.28.5"
      host_addrs: "10.0.1.5"
      host_external_addrs: "54.93.100.10"
      image_password: "exasol123"
      db_password: "exasol456"
      admin_password: "exasol789"
      db_mem_size: 12000
      schema: "BENCHMARK"

workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
```

**Workflow**:

```bash
benchkit check --config configs/remote_installer.yaml
benchkit setup --config configs/remote_installer.yaml
benchkit load --config configs/remote_installer.yaml
benchkit run --config configs/remote_installer.yaml
benchkit report --config configs/remote_installer.yaml
```

> [!IMPORTANT]
> Use **literal IP addresses** in `host_addrs` and `host_external_addrs` — not `$VAR` references. Remote mode has no Terraform state to resolve variables from.

### Remote with Multiple Systems

Compare different databases on separate machines by listing each under `nodes`:

```yaml
project_id: "remote_exa_vs_ch"
title: "Remote Exasol vs ClickHouse"
author: "Benchmark Team"

env:
  mode: "remote"
  nodes:
    exasol:
      public_ip: "54.93.100.10"
    clickhouse:
      public_ip: "54.93.100.20"
  ssh_private_key_path: "~/.ssh/benchmark-key.pem"
  ssh_user: "ubuntu"

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.2.0"
    setup:
      method: "preinstalled"
      host: "54.93.100.10"
      port: 8563
      username: "sys"
      password: "exasol456"
      schema: "BENCHMARK"

  - name: "clickhouse"
    kind: "clickhouse"
    version: "25.1.3.23"
    setup:
      method: "preinstalled"
      host: "54.93.100.20"
      port: 8123
      username: "default"
      password: "clickhouse123"

workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
```

### Remote Multinode Cluster

For multinode clusters, list multiple IPs under the system's `nodes` entry and set `node_count` in the system setup:

```yaml
project_id: "remote_exasol_2node"
title: "Remote Exasol 2-Node Cluster"
author: "Benchmark Team"

env:
  mode: "remote"
  nodes:
    exasol:
      - public_ip: "54.93.100.10"
        private_ip: "10.0.1.5"
      - public_ip: "54.93.100.11"
        private_ip: "10.0.1.6"
  ssh_private_key_path: "~/.ssh/benchmark-key.pem"
  ssh_user: "ubuntu"

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.2.0"
    setup:
      method: "installer"
      node_count: 2
      use_additional_disk: true
      c4_version: "4.28.5"
      image_password: "exasol123"
      db_password: "exasol456"
      admin_password: "exasol789"
      db_mem_size: 12000
      schema: "BENCHMARK"

workload:
  name: "tpch"
  scale_factor: 1
  runs_per_query: 3
  warmup_runs: 1
```

### Working Examples

The `configs/remote_test/` directory contains a complete, tested remote mode example suite:

| Config | Description |
|--------|-------------|
| `01_remote_exasol_installer.yaml` | Fresh Exasol install via c4 |
| `02_remote_exasol_preinstalled.yaml` | Connect to existing Exasol |
| `03_remote_clickhouse.yaml` | Fresh ClickHouse native install |
| `04_remote_exa_vs_ch.yaml` | Two-system comparison |
| `05_remote_exasol_multinode.yaml` | 2-node Exasol cluster |

These configs use `{{placeholder}}` values that are filled in by the test suite's `setup_ips.sh` script after provisioning machines.

## Customizing Benchmarks

### Running Subsets

#### Run Specific Systems

```bash
# Only Exasol
benchkit run --config configs/exa_vs_ch_1g.yaml --systems exasol

# Only ClickHouse
benchkit run --config configs/exa_vs_ch_1g.yaml --systems clickhouse

# Multiple systems
benchkit run --config configs/exa_vs_ch_1g.yaml --systems exasol,clickhouse
```

#### Run Specific Queries

```bash
# Fast queries for testing
benchkit run --config configs/exa_vs_ch_1g.yaml --queries Q01,Q06

# Single query
benchkit run --config configs/exa_vs_ch_1g.yaml --queries Q06

# Multiple queries
benchkit run --config configs/exa_vs_ch_1g.yaml --queries Q01,Q03,Q06,Q13
```

#### Combine Filters

```bash
# Test Exasol with fast queries
benchkit run --config configs/exa_vs_ch_1g.yaml \
  --systems exasol \
  --queries Q01,Q06
```

### Creating Custom Configurations

#### 1. Copy Sample Configuration

```bash
cp configs/exa_vs_ch_1g.yaml configs/my_benchmark.yaml
```

#### 2. Modify Parameters

```yaml
project_id: "my_custom_benchmark"
title: "Custom Performance Analysis"

workload:
  scale_factor: 10              # Smaller for faster testing
  queries:
    include: ["Q01", "Q06"]     # Only fast queries
  runs_per_query: 3
  warmup_runs: 1

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.1.0"
    setup:
      extra:
        dbram: "16g"            # Adjust based on available RAM
```

#### 3. Run Custom Benchmark

```bash
benchkit run --config configs/my_benchmark.yaml
benchkit report --config configs/my_benchmark.yaml
```

## Troubleshooting

### Common Issues

#### Docker Permission Errors

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker ps
```

#### Database Connection Failures

```bash
# Check if containers are running
docker ps

# Check container logs
docker logs exasol_exasol
docker logs clickhouse_clickhouse

# Test database connectivity
benchkit status --project my_benchmark
```

#### Out of Memory Errors

**Solution 1: Reduce Scale Factor**

```yaml
workload:
  scale_factor: 10  # Instead of 100
```

**Solution 2: Increase System Memory**

```yaml
systems:
  - name: "exasol"
    setup:
      extra:
        dbram: "16g"  # Instead of 32g
```

**Solution 3: Use Cloud with More Resources**

```yaml
env:
  mode: "aws"
  instances:
    exasol:
      instance_type: "r7i.4xlarge"  # 128GB RAM
```

#### Disk Space Issues

```bash
# Check disk usage
df -h

# Clean up old results
make clean

# Remove unused Docker images
docker system prune -a

# Clean benchmark data
rm -rf data/tpch/sf100/
```

#### AWS Credential Errors

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check .env file
cat .env

# Test AWS connection
aws ec2 describe-regions --region eu-west-1
```

#### Terraform Errors

```bash
# Terraform state is stored per-project in results/<project_id>/terraform/
cd results/<project_id>/terraform

# Initialize Terraform (if needed)
terraform init

# Check state
terraform show

# Force unlock if needed
terraform force-unlock <LOCK_ID>
```

### Debug Mode

Enable debug output for detailed troubleshooting:

```bash
# Debug probe
benchkit probe --config configs/my_benchmark.yaml --debug

# Debug run
benchkit run --config configs/my_benchmark.yaml --debug

# Debug verify
benchkit verify --config configs/my_benchmark.yaml --debug
```

### Getting Help

1. **Check logs**: Look in `results/<project_id>/` for detailed logs
2. **Validate configuration**: Ensure YAML syntax is correct
3. **Test connectivity**: Use `benchkit status` to verify systems
4. **Start small**: Begin with SF 1 and few queries
5. **Review documentation**: Check [README](../README.md) and [EXTENDING](EXTENDING.md)

## Example Workflows

### Quick Performance Check

```bash
# Fast benchmark for development
benchkit run --config configs/exa_vs_ch_1g.yaml \
  --queries Q01,Q06 \
  --systems exasol,clickhouse

# View results
benchkit status --project exa_vs_ch_1g
```

### Comprehensive Analysis

```bash
# Full TPC-H benchmark
benchkit probe --config configs/comprehensive.yaml
benchkit run --config configs/comprehensive.yaml
benchkit report --config configs/comprehensive.yaml
```

### Cost Optimization Study

```bash
# Test different instance types
for instance in m7i.2xlarge m7i.4xlarge m7i.8xlarge; do
  sed "s/instance_type: .*/instance_type: $instance/" \
    configs/base.yaml > configs/test_$instance.yaml
  make all CFG=configs/test_$instance.yaml
done

# Compare results
benchkit status
```

### Regression Testing

```bash
# Baseline benchmark
benchkit run --config configs/baseline_v1.yaml

# New version benchmark
benchkit run --config configs/baseline_v2.yaml

# Compare results manually or with verification
benchkit verify --config configs/baseline_v2.yaml
```

### Multi-Scale Testing

```bash
# Test across different data sizes
for sf in 1 10 100; do
  sed "s/scale_factor: .*/scale_factor: $sf/" \
    configs/base.yaml > configs/sf_$sf.yaml
  benchkit run --config configs/sf_$sf.yaml
done
```

### Rerunning Failed Queries

```bash
# Force rerun with debug
benchkit run --config configs/my_benchmark.yaml \
  --force \
  --queries Q17,Q20 \
  --debug
```

### Multi-Dimensional Scalability Study

```bash
# Use the scalability suite for comprehensive testing
cd public/scalability

# Preview the execution plan
benchkit suite run . --dry-run

# Run node scaling series only
benchkit suite run . --series series_1_nodes

# Run all enabled series with resume capability
benchkit suite run . --resume

# Check progress
benchkit suite status .

# Generate comparison dashboard
benchkit suite publish . --output results/scalability_dashboard
```

### Creating a Custom Suite

```bash
# Initialize new suite
benchkit suite init ./my-study --name "Database Comparison Study"

# Add benchmark configurations to series directories
cp configs/exasol_sf100.yaml ./my-study/series/01_baseline/
cp configs/clickhouse_sf100.yaml ./my-study/series/01_baseline/

# Run the suite
benchkit suite run ./my-study
```

## Understanding Output

### Results Directory Structure

```
results/my_benchmark/
├── system.json                      # System specifications
├── system_exasol.json              # Exasol system info (cloud mode)
├── system_clickhouse.json          # ClickHouse system info (cloud mode)
├── runs.csv                        # All benchmark results
├── summary.json                    # Summary statistics
└── figures/                        # Generated visualizations
    ├── query_runtime_boxplot.png
    ├── median_runtime_bar.png
    └── performance_heatmap.png
```

### runs.csv Format

```csv
system,query,run,elapsed_ms,rows_returned,success,error
exasol,Q01,1,1234.56,10,true,
exasol,Q01,2,1235.67,10,true,
clickhouse,Q01,1,2345.67,10,true,
```

### Report Structure

```
results/my-benchmark/reports/<report-name>/
├── REPORT.md                       # Complete report
├── REPORT.html                     # Complete report (HTML format)
├── attachments/
│   ├── runs.csv                    # Raw results
│   ├── system.json                 # System info
│   ├── config.yaml                 # Exact configuration
│   └── figures/                    # All visualizations
└── my-benchmark-benchmark.zip      # Reproduction package
```

## Next Steps

Once you have a basic benchmark working:

1. **Explore Configurations**: Try different scale factors and query sets
2. **Add Systems**: See [EXTENDING.md](../dev-docs/EXTENDING.md) for adding new databases
3. **Custom Workloads**: Create domain-specific benchmarks
4. **Automate**: Set up CI/CD pipelines for regular benchmarking
5. **Share Results**: Publish your benchmark methodology and results

## Additional Resources

- [README](../README.md) - Framework overview and quick reference
- [Extending the Framework](../dev-docs/EXTENDING.md) - Add systems, workloads, and features

This framework provides a solid foundation for database benchmarking. Start with the simple examples above and gradually explore more advanced features as you become comfortable with the system.
