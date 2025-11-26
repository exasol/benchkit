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

### 3. Dynamic Dependency Management

Each system defines its own dependencies via `get_python_dependencies()`. Packages only include drivers for databases actually benchmarked.

### 4. Environment-Agnostic Templates

Templates work everywhere - AWS, GCP, Azure, local, on-premises. All tuning parameters documented as copy-pasteable commands.

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

## Adding New Systems

See [Extending Guide](EXTENDING.md)

## Adding New Infrastructure Providers

See [Extending Guide](EXTENDING.md)

## Adding New Workloads

See [Extending Guide](EXTENDING.md)

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
