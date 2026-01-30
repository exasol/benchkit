# Main Developers Guide

## Key Design Principles

### 1. Self-Contained Reports

Every report is a complete directory with:
- All result data as attachments
- Full configuration files being used
- Minimal reproduction package
- Complete setup commands

### 2. Installation-Independent Connectivity

Uses official Python drivers for universal database connectivity:

- **Exasol**: `pyexasol` - works with Docker, native, cloud, preinstalled
- **ClickHouse**: `clickhouse-connect` - works with any deployment
- **Trino**: `trino` - works with any Trino/Presto deployment
- **StarRocks**: `starrocks` - uses MySQL protocol
- **DuckDB**: `duckdb` - embedded, no network connectivity needed

### 3. Dynamic Dependency Management

Each system defines its own dependencies via `get_python_dependencies()`. Packages only include drivers for databases actually benchmarked.

### 4. Environment-Agnostic Templates

Templates work everywhere - AWS, GCP, Azure, local, on-premises. All tuning parameters documented as copy-pasteable commands.

## Repository Structure

```
benchkit/
├── benchkit/                  # Core framework
│   ├── cli/                   # Command-line interface (13 commands)
│   ├── systems/               # Database system implementations (5 systems)
│   ├── workloads/             # Benchmark workloads (TPC-H, ClickBench, Estuary)
│   ├── gather/                # System information collection
│   ├── run/                   # Benchmark execution
│   ├── report/                # Report generation
│   ├── infra/                 # Cloud infrastructure management
│   ├── package/               # Minimal package creation
│   ├── verify/                # Result verification
│   ├── combine/               # Result combination from multiple projects
│   ├── storage/               # Storage backends (local, S3)
│   └── common/                # Shared utilities and markers
├── templates/                 # Jinja2 templates for reports
├── configs/                   # Benchmark configurations
├── infra/aws/                 # AWS Terraform templates (source)
├── workloads/tpch/            # TPC-H queries and schemas
└── results/                   # Generated results (auto-created)
    └── <project_id>/          # Per-project results
        └── terraform/         # Terraform state (per-project isolation)
```

## System Capabilities

Systems declare their capabilities via class attributes in `benchkit/systems/base.py`:

### SUPPORTS_MULTINODE

```python
class ExasolSystem(SystemUnderTest):
    SUPPORTS_MULTINODE = True  # System can be deployed as a cluster
```

When `True`, the system can be deployed with `node_count > 1` in configuration. The infrastructure manager will provision multiple instances and pass a list of instance managers to the system.

**Currently supported**: Exasol, ClickHouse, Trino, StarRocks

### SUPPORTS_STREAMLOAD

```python
class StarrocksSystem(SystemUnderTest):
    SUPPORTS_STREAMLOAD = True  # System supports streaming data ingestion
```

When `True`, the system supports parallel data loading via streaming protocols (HTTP, etc.) rather than file-based loading.

**Currently supported**: Exasol, StarRocks, DuckDB

### LOAD_TIMEOUT_MULTIPLIER

Systems can override the default load timeout by setting `LOAD_TIMEOUT_MULTIPLIER`. For example, `LOAD_TIMEOUT_MULTIPLIER = 2.0` doubles the timeout for data loading operations.

## Query Categories

Workloads can define query categories via the `get_query_categories()` method. This enables:
- Grouping queries by type (simple, medium, complex)
- Running subsets of queries by category
- Incremental result reporting

```python
class TPCH(Workload):
    def get_query_categories(self) -> dict[str, list[str]]:
        return {
            "simple": ["Q01", "Q06", "Q12", "Q14", "Q15"],
            "medium": ["Q03", "Q04", "Q05", "Q07", "Q10"],
            "complex": ["Q02", "Q08", "Q09", "Q11", "Q13", "Q16-Q22"],
        }
```

## Parallel Data Loading

The `load_workers` configuration option enables parallel data loading for large datasets:

```yaml
workload:
  name: "tpch"
  scale_factor: 100
  load_workers: 4  # Load 4 tables concurrently
```

This is particularly useful for:
- Large TPC-H scale factors (SF 100+)
- Systems with fast network/disk I/O
- Reducing total benchmark setup time

The parallel loader respects table dependencies and system-specific loading methods.

## Adding New Workloads

A workload defines the contents of the benchmark, in terms of

- **data model**, typically a set of DDL queries stored under `workloads/<name>`
- **table data**, generated or otherwise defined by code under `benchkit/workloads/`
- **query execution logic**, defined by code under `benchkit/workloads/`
- **benchmark queries**, stored as SQL files under `workloads/<name>`

📖 **See [Extending Guide](EXTENDING.md) for details**

## Adding Query Variants To Existing Workloads

> [!NOTE]
> Section needs content.

## Adding New Systems

Systems are defined by python code at `benchkit/systems/`, which needs to provide methods to

- **deploy** the software on supported infrastructure providers
- **configure** the software according to the benchmark configuration
- **execute SQL** statements
- **load data** (CSV) into tables

📖 **See [Extending Guide](EXTENDING.md) for details**

## Adding New Infrastructure Providers

> [!NOTE]
> Section needs content.

📖 **See [Extending Guide](EXTENDING.md) for details**


## Best Practices

### Code Quality

1. **Follow existing patterns**: Study `ExasolSystem` and `ClickHouseSystem` implementations
2. **Error handling**: Always include proper error handling and logging
3. **Documentation**: Add docstrings explaining complex logic
4. **Type hints**: Use type hints for better code clarity

### Installation Independence

1. **Use Python drivers**: Prefer official Python drivers over CLI tools
2. **Universal connectivity**: Code should work with Docker, native, cloud, preinstalled
3. **Graceful fallback**: Provide fallback mechanisms when drivers unavailable

### Dynamic Dependencies

1. **Implement `get_python_dependencies()`**: Each system declares its dependencies
2. **Minimal packages**: Only include what's needed for the specific benchmark
3. **Version pinning**: Specify minimum versions for dependencies

### Testing

1. **Unit tests**: Create tests for new functionality in `tests/`
2. **Integration tests**: Test with actual database systems when possible
3. **Cross-environment**: Test across Docker, native, and cloud deployments

### Configuration

1. **Validation**: Add configuration validation for new parameters
2. **Defaults**: Provide sensible defaults for optional parameters
3. **Documentation**: Document all configuration options

### Security

1. **Credentials**: Never commit credentials or sensitive data
2. **Input validation**: Validate all user inputs
3. **Least privilege**: Use minimal required permissions

### Extension Checklist

When adding a new component, verify:

- [ ] Follows base class interface
- [ ] Implements `get_python_dependencies()` (for systems)
- [ ] Configuration validation includes new parameters
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] Error handling implemented
- [ ] Resource cleanup implemented
- [ ] Works across deployment methods
