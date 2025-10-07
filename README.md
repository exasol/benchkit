# Database Benchmark Report Framework

A modular framework for running and documenting database benchmarks, with a focus on comparing **Exasol** with other database systems. This repository provides reusable building blocks to launch benchmark environments, collect detailed system information, run benchmark workloads, and generate reports documenting the results.

## Features

- 🏗️ **Modular Architecture**: Fine-grained templates for setup, execution, and reporting
- ☁️ **Multi-Cloud Support**: AWS infrastructure automation with separate instances per database
- 📊 **Benchmark Workloads**: TPC-H with support for custom workloads
- 📝 **Self-Contained Reports**: Generate reproducible reports with all attachments
- 🔧 **Extensible**: Easy to add new systems, workloads, and cloud providers
- 📈 **Rich Visualizations**: Automated generation of performance plots and tables
- 🔍 **Result Verification**: Validate query correctness against expected outputs

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd benchkit

# Install dependencies
python -m pip install -e .

# Run a sample benchmark
make all CFG=configs/exa_vs_ch_1g.yaml
```

This will:
1. Provision cloud infrastructure (if configured)
2. Probe system information
3. Run Exasol vs ClickHouse TPC-H benchmark
4. Generate a complete report with results and reproducibility instructions

📖 **See [Getting Started Guide](GETTING_STARTED.md) for detailed installation and usage instructions.**

## Usage

The framework provides 9 commands for complete benchmark lifecycle management:

```bash
# System information collection
benchkit probe --config configs/my_benchmark.yaml

# Run benchmarks
benchkit run --config configs/my_benchmark.yaml [--systems exasol] [--queries Q01,Q06]

# Generate reports
benchkit report --config configs/my_benchmark.yaml

# Manage infrastructure
benchkit infra apply --provider aws --config configs/my_benchmark.yaml

# Other commands: execute, status, package, verify, cleanup
```

**Status Command** provides comprehensive project insights:
- Overview of all projects (probe, benchmark, report status)
- Detailed status for specific configs (system info, infrastructure, timing)
- Cloud infrastructure details (IPs, connection strings)
- Multiple config support and smart project lookup

📖 **See [Getting Started Guide](GETTING_STARTED.md) for comprehensive CLI documentation and examples.**

## Repository Structure

```
benchkit/
├── benchkit/                  # Core framework
│   ├── cli.py                 # Command-line interface (9 commands)
│   ├── systems/               # Database system implementations
│   ├── workloads/             # Benchmark workloads (TPC-H)
│   ├── gather/                # System information collection
│   ├── run/                   # Benchmark execution
│   ├── report/                # Report generation
│   ├── infra/                 # Cloud infrastructure management
│   ├── package/               # Minimal package creation
│   └── verify/                # Result verification
├── templates/                 # Jinja2 templates for reports
├── configs/                   # Benchmark configurations
├── infra/aws/                 # AWS Terraform modules
├── workloads/tpch/            # TPC-H queries and schemas
└── results/                   # Generated results (auto-created)
```

## Configuration Example

```yaml
project_id: "exasol_vs_clickhouse_tpch"
title: "Exasol vs ClickHouse Performance on TPC-H"

env:
  mode: "aws"
  region: "eu-west-1"
  instances:
    exasol:
      instance_type: "m7i.4xlarge"
    clickhouse:
      instance_type: "m7i.4xlarge"

systems:
  - name: "exasol"
    kind: "exasol"
    version: "2025.1.0"
    setup:
      method: "installer"
      extra:
        dbram: "32g"

  - name: "clickhouse"
    kind: "clickhouse"
    version: "24.12"
    setup:
      method: "native"
      extra:
        memory_limit: "32g"

workload:
  name: "tpch"
  scale_factor: 1
  queries:
    include: ["Q01", "Q03", "Q06", "Q13"]
  runs_per_query: 3
  warmup_runs: 1
```

📖 **See [Getting Started Guide](GETTING_STARTED.md) for more configuration examples.**

## Requirements

- Python 3.10+
- **Terraform** (for cloud infrastructure) - [Installation Guide](https://developer.hashicorp.com/terraform/install)
- At least 16GB RAM (32GB+ recommended for larger benchmarks)
- SSD storage recommended

### AWS Setup (Optional)

For cloud deployments, configure AWS credentials:

```bash
# Create .env file (recommended)
cat > .env << EOF
AWS_PROFILE=default-mfa
AWS_REGION=eu-west-1
EOF
```

**Required AWS Permissions**: `ec2:*`, `ec2:DescribeImages`, `ec2:DescribeAvailabilityZones`

📖 **See [Getting Started Guide](GETTING_STARTED.md) for detailed cloud setup instructions.**

## Extending the Framework

The framework is designed for easy extension:

### Quick Example: Adding a New Database System

1. Create `benchkit/systems/newsystem.py`:

```python
from .base import SystemUnderTest

class NewSystem(SystemUnderTest):
    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        return ["newsystem-driver>=1.0.0"]
    
    def execute_query(self, query: str, query_name: str = None):
        # Use native Python driver for universal connectivity
        pass
    
    # ... implement other required methods
```

2. Register in `benchkit/systems/__init__.py`:

```python
SYSTEM_IMPLEMENTATIONS = {
    "exasol": "ExasolSystem",
    "clickhouse": "ClickHouseSystem",
    "newsystem": "NewSystem",  # Add this line
}
```

📖 **See [Extending the Framework](EXTENDING.md) for comprehensive guides on:**
- Adding new database systems
- Creating custom workloads
- Adding cloud providers
- Customizing reports and visualizations
- Implementing result verification

## Key Design Principles

### 1. Self-Contained Reports

Every report is a complete directory with:
- All result data as attachments
- Exact configuration files
- Minimal reproduction package
- Complete setup commands

### 2. Installation-Independent Connectivity

Uses official Python drivers for universal database connectivity:
- **Exasol**: `pyexasol` - works with Docker, native, cloud, preinstalled
- **ClickHouse**: `clickhouse-connect` - works with any deployment

### 3. Dynamic Dependency Management

Each system defines its own dependencies via `get_python_dependencies()`. Packages only include drivers for databases actually benchmarked.

### 4. Environment-Agnostic Templates

Templates work everywhere - AWS, GCP, Azure, local, on-premises. All tuning parameters documented as copy-pasteable commands.

## Documentation

- 📖 [Getting Started Guide](GETTING_STARTED.md) - Installation, usage, and examples
- 🔧 [Extending the Framework](EXTENDING.md) - Adding systems, workloads, and features

## Dependencies

Core dependencies (automatically installed):
- `typer` - CLI framework
- `jinja2` - Template rendering
- `pyyaml` - Configuration parsing
- `pandas` - Data manipulation
- `matplotlib` - Plotting
- `rich` - CLI formatting
- `boto3` - AWS integration (optional)
- `python-dotenv` - .env file support (optional)

Database-specific drivers loaded dynamically based on systems used.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Security

- Database credentials and licenses should not be committed to the repository
- Use environment variables or `.env` file for sensitive data
- The framework includes basic security practices but should be reviewed for production use

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with ❤️ for reproducible database benchmarking.
