# Database Benchmark Report Framework

A modular framework for running and documenting database benchmarks, with a focus on comparing **Exasol** with
other database systems. This repository provides reusable building blocks to launch benchmark environments,
collect detailed system information, run benchmark workloads, and generate reports documenting the results.

## Features

- 🏗️ **Modular Architecture**: Fine-grained templates for setup, execution, and reporting
- ☁️ **Multi-Cloud Support**: Infrastructure automation with separate instances per database
- 📊 **Benchmark Workloads**: TPC-H, Estuary, and support for custom workloads
- 📝 **Self-Contained Reports**: Generate reproducible reports with all attachments
- 🔧 **Extensible**: Easy to add new systems, workloads, and cloud providers
- 📈 **Rich Visualizations**: Automated generation of performance plots and tables
- 🔍 **Result Verification**: Validate query correctness against expected outputs
- 📦 **Benchmark Suites**: Orchestrate multiple benchmarks with state management and resumable runs
- 🌐 **Static Dashboards**: Publish interactive benchmark comparison websites

## Requirements

- Python 3.10+
- **Terraform** (for cloud infrastructure) - [Installation Guide](https://developer.hashicorp.com/terraform/install)

## Quick Start

> [!TIP]
> You might have to set up a python virtual environment for installing python packages.

> [!CAUTION]
> The sample benchmark uses AWS cloud infrastructure. See [Getting Started Guide](user-docs/GETTING_STARTED.md)
> for detailed cloud setup instructions.
> Note that AWS infrastructure is usually not free to use.

```shell
# 1. Clone and enter the repository
git clone https://github.com/exasol/benchkit.git
cd benchkit

# 2. Install dependencies and local package
python -m pip install -e .

# 3. Copy and edit example environment
cp .env.example .env
$EDITOR .env

# 4. Validate your configuration
benchkit check --config configs/exa_vs_ch_1g.yaml

# 5. Run sample benchmark
make all CFG=configs/exa_vs_ch_1g.yaml

# 6. Clean up AWS resources
make infra-destroy CFG=configs/exa_vs_ch_1g.yaml

# 7. View benchmark report
cat results/exa_vs_ch_1g/reports/*/REPORT.md
# Or open HTML version in browser
```

## Usage

The framework provides 13 main commands (plus 9 suite subcommands) for complete benchmark lifecycle management:

```bash
# Manage infrastructure
benchkit infra apply --provider aws --config configs/my_benchmark.yaml

# System information collection
benchkit probe --config configs/my_benchmark.yaml

# Run benchmarks
benchkit run --config configs/my_benchmark.yaml [--systems exasol] [--queries Q01,Q06]

# Generate reports
benchkit report --config configs/my_benchmark.yaml

# Suite management (orchestrate multiple benchmarks)
benchkit suite run ./my-benchmark-suite/
benchkit suite status ./my-benchmark-suite/
benchkit suite publish ./my-benchmark-suite/

# Other commands: check, setup, load, execute, status, package, verify, cleanup, combine
```

> [!INFO]
> Note that the config parameter can also be set through an **environment variable** for all commands:
> 
> ```shell
> export BENCHKIT_CONFIG=configs/my_benchmark.yaml
> 
> benchkit check
> ```

**Status Command** provides comprehensive project insights:

- Overview of all projects (probe, benchmark, report status)
- Detailed status for specific configs (system info, infrastructure, timing)
- Cloud infrastructure details (IPs, connection strings)
- Multiple config support and smart project lookup

📖 **See [Getting Started Guide](user-docs/GETTING_STARTED.md) for comprehensive CLI documentation and examples.**

## Repository Structure (User Version)

```
benchkit/
├── benchkit/                  # Core framework
├── configs/                   # Benchmark configurations
│   └── extended_scalability/  # Example benchmark suite
└── results/                   # Generated results (auto-created)
```

See [Developer Guide](dev-docs/DEVELOPERS.md) for a more detailed structure definition.

## Defining Your Own Benchmarks

You can easily create your own benchmark by creating a yaml configuration file combining

- One infrastructure provider (aws/docker/local/...)
- One workload (benchmark type) to be executed
- Multiple systems (software) to be tested

📖 **See [Getting Started Guide](user-docs/GETTING_STARTED.md) for information on how to create
benchmark configurations using supported modules.**

## Support Matrix

### Systems

| System     | AWS | Docker | Multinode | Stream Load |
|------------|-----|--------|-----------|-------------|
| Exasol     | ✓   | ✗      | ✓         | ✓           |
| ClickHouse | ✓   | ✗      | ✓         | ✗           |
| Trino      | ✓   | ✗      | ✓         | ✗           |
| StarRocks  | ✓   | ✗      | ✓         | ✓           |
| DuckDB     | N/A | N/A    | ✗         | ✓           |

### Workloads

<!-- link definitions for table headers -->
[estuary]: benchkit/workloads/estuary/README.md "Estuary Warehouse Report"

| Workload       | Exasol | ClickHouse | Trino | StarRocks | DuckDB |
|----------------|--------|------------|-------|-----------|--------|
| TPC-H          | ✓      | ✓          | ✓     | ✓         | ✓      |
| [Estuary]      | WIP    | ✗          | ✗     | ✗         | ✗      |

Notes:
- **Multinode**: Supports clustered deployments with multiple nodes
- **Stream Load**: Supports parallel data loading via streaming protocols
- **DuckDB**: Embedded database, runs locally without infrastructure


## Benchmark Suites

For complex benchmarking studies (e.g., scalability testing across multiple dimensions), the framework
supports **benchmark suites** - collections of related benchmarks organized into series.

```bash
# Initialize a new suite
benchkit suite init ./my-suite --name "My Benchmark Suite"

# View execution plan (dry-run)
benchkit suite run ./my-suite --dry-run

# Run all benchmarks (with automatic resume on interruption)
benchkit suite run ./my-suite

# Check status of all benchmarks
benchkit suite status ./my-suite

# Generate static comparison dashboard
benchkit suite publish ./my-suite --output docs/
```

**Suite Structure**:
```
my-suite/
├── suite.yaml              # Suite configuration
├── series/
│   ├── 01_node_scaling/    # Series: test node counts
│   │   ├── nodes_1.yaml
│   │   ├── nodes_4.yaml
│   │   └── nodes_8.yaml
│   └── 02_data_scaling/    # Series: test data sizes
│       ├── sf_25.yaml
│       └── sf_100.yaml
└── .benchkit/              # State directory (auto-managed)
```

See [configs/extended_scalability/](configs/extended_scalability/) for a comprehensive example
comparing 5 database systems across node scaling, data volume, and concurrency dimensions.

## Documentation

### For Users

- 📖 [Getting Started Guide](user-docs/GETTING_STARTED.md) - Installation, usage, and examples

### For Developers

- 🔧 [Extending the Framework](dev-docs/EXTENDING.md) - Adding systems, workloads, and features

## License

This project is licensed under the MIT License - see the LICENSE file for details.
All names used are copyright and owned by the respective companies.

---

Built with ❤️ for reproducible database benchmarking.
