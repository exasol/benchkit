# Extending the Benchmark Framework

This guide explains how to extend the database benchmark framework with new systems, workloads, cloud providers, and reporting features.

## Table of Contents

- [Adding New Database Systems](#adding-new-database-systems)
- [Adding New Workloads](#adding-new-workloads)
- [Adding Cloud Providers](#adding-cloud-providers)
- [Customizing Reports](#customizing-reports)
- [Adding Result Verification](#adding-result-verification)
- [Best Practices](#best-practices)

## Adding New Database Systems

### Overview

The framework uses an abstract base class `SystemUnderTest` that all database systems must implement. Systems define their own Python dependencies and can work with any installation method (Docker, native, cloud, preinstalled).

### Step 1: Create System Implementation

Create a new file `benchkit/systems/newsystem.py`:

```python
from pathlib import Path
from typing import Any

from .base import SystemUnderTest


class NewSystem(SystemUnderTest):
    """Implementation for NewSystem database."""

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """
        Return Python packages required by this system.
        
        This enables dynamic dependency management - packages only include
        drivers for databases actually benchmarked.
        """
        return ["newsystem-driver>=1.0.0"]

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # Add system-specific initialization
        self.port = self.setup_config.get("port", 5432)
        self.database = self.setup_config.get("database", "benchmark")
        self.host = self.setup_config.get("host", "localhost")

    def install(self) -> bool:
        """Install the database system."""
        method = self.setup_config.get("method", "docker")
        
        if method == "docker":
            return self._install_docker()
        elif method == "native":
            return self._install_native()
        elif method == "preinstalled":
            return self.is_already_installed()
        else:
            print(f"Unsupported installation method: {method}")
            return False

    def _install_docker(self) -> bool:
        """Install using Docker."""
        container_name = f"newsystem_{self.name}"

        # Remove existing container
        self.execute_command(f"docker rm -f {container_name} || true")

        # Start new container
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{self.port}:{self.port}",
            "-v", f"{self.data_dir}:/var/lib/newsystem",
            f"newsystem:latest"
        ]

        result = self.execute_command(" ".join(cmd))
        if not result["success"]:
            print(f"Failed to start container: {result['stderr']}")
            return False

        return self.wait_for_health()

    def _install_native(self) -> bool:
        """Install using native package manager."""
        # Record installation commands for report
        self.record_command("apt-get update")
        self.record_command("apt-get install -y newsystem")
        
        # Execute installation
        result = self.execute_command("apt-get update && apt-get install -y newsystem")
        return result["success"]

    def start(self) -> bool:
        """Start the database system."""
        method = self.setup_config.get("method")
        
        if method == "docker":
            result = self.execute_command(f"docker start newsystem_{self.name}")
            return result["success"] and self.wait_for_health()
        elif method == "native":
            result = self.execute_command("systemctl start newsystem")
            return result["success"] and self.wait_for_health()
        
        return True

    def is_healthy(self, quiet: bool = False) -> bool:
        """Check if the system is healthy."""
        try:
            # Use Python driver for universal connectivity
            import newsystem_driver
            
            conn = newsystem_driver.connect(
                host=self.host,
                port=self.port,
                database=self.database
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            if not quiet:
                print(f"Health check failed: {e}")
            return False

    def create_schema(self, schema_name: str) -> bool:
        """Create a schema/database."""
        sql = f"CREATE SCHEMA IF NOT EXISTS {schema_name}"
        result = self.execute_query(sql, query_name=f"create_schema_{schema_name}")
        return result.get("success", False)

    def load_data(self, table_name: str, data_path: Path, **kwargs: Any) -> bool:
        """Load data into a table."""
        schema_name = kwargs.get("schema", "benchmark")
        file_format = kwargs.get("format", "csv")

        if file_format.lower() == "csv":
            sql = f"""
            COPY {schema_name}.{table_name}
            FROM '{data_path}'
            WITH (FORMAT CSV, DELIMITER '|')
            """
            result = self.execute_query(sql, query_name=f"load_{table_name}")
            return result.get("success", False)
        else:
            print(f"Unsupported format: {file_format}")
            return False

    def execute_query(self, query: str, query_name: str | None = None) -> dict[str, Any]:
        """
        Execute a SQL query using native Python driver.
        
        This provides installation-independent connectivity that works with
        Docker, native, cloud, and preinstalled deployments.
        """
        import time
        import newsystem_driver
        
        if not query_name:
            query_name = "unnamed_query"

        try:
            start_time = time.time()
            
            # Connect using native driver
            conn = newsystem_driver.connect(
                host=self.host,
                port=self.port,
                database=self.database
            )
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            rows = cursor.fetchall() if cursor.description else []
            row_count = len(rows) if cursor.description else cursor.rowcount
            
            # Commit and close
            conn.commit()
            cursor.close()
            conn.close()
            
            elapsed_s = time.time() - start_time

            return {
                "success": True,
                "elapsed_s": elapsed_s,
                "elapsed_ms": elapsed_s * 1000,
                "rows_returned": row_count,
                "query_name": query_name,
                "error": None
            }

        except Exception as e:
            elapsed_s = time.time() - start_time if 'start_time' in locals() else 0
            
            return {
                "success": False,
                "elapsed_s": elapsed_s,
                "elapsed_ms": elapsed_s * 1000,
                "rows_returned": 0,
                "query_name": query_name,
                "error": str(e)
            }

    def teardown(self) -> bool:
        """Clean up the system."""
        method = self.setup_config.get("method")
        success = True

        if method == "docker":
            container_name = f"newsystem_{self.name}"
            stop_result = self.execute_command(f"docker stop {container_name} || true")
            remove_result = self.execute_command(f"docker rm {container_name} || true")
            success = stop_result["success"] and remove_result["success"]
        elif method == "native":
            result = self.execute_command("systemctl stop newsystem")
            success = result["success"]

        return success

    def get_connection_string(self, public_ip: str, private_ip: str) -> str:
        """
        Get CLI connection string for this database system.
        
        This is used by the status command to display copy-pasteable
        connection commands with all necessary parameters.
        
        Args:
            public_ip: Public IP address of the system
            private_ip: Private IP address of the system
            
        Returns:
            Complete CLI command string to connect to the database
        """
        port = self.setup_config.get("port", 5432)
        username = self.setup_config.get("username", "postgres")
        database = self.setup_config.get("database", "benchmark")
        
        # Return complete CLI command with all parameters
        return f"newsystem-cli --host {public_ip} --port {port} --user {username} --database {database}"
```

**Key Implementation Notes**:

1. **Connection String Method**: The `get_connection_string()` method provides CLI commands for the status display
2. **Dynamic Dependencies**: `get_python_dependencies()` ensures only needed drivers are included
3. **Installation Independence**: `execute_query()` uses native drivers that work everywhere
4. **Command Recording**: Use `record_command()` to document setup steps in reports

### Step 2: Register the System

Add your system to `benchkit/systems/__init__.py`:

```python
SYSTEM_IMPLEMENTATIONS = {
    "exasol": "ExasolSystem",
    "clickhouse": "ClickHouseSystem",
    "newsystem": "NewSystem",  # Add this line
}

def _lazy_import_system(kind: str) -> type[SystemUnderTest]:
    """Lazy import of system class."""
    if kind == "exasol":
        from .exasol import ExasolSystem
        return ExasolSystem
    if kind == "clickhouse":
        from .clickhouse import ClickHouseSystem
        return ClickHouseSystem
    if kind == "newsystem":  # Add this block
        from .newsystem import NewSystem
        return NewSystem
    raise ValueError(f"Unknown system kind: {kind}")
```

### Step 3: Create Configuration Example

Add a configuration example in `configs/newsystem_example.yaml`:

```yaml
project_id: "newsystem_benchmark"
title: "NewSystem Performance Evaluation"
author: "Your Name"

env:
  mode: "local"  # or aws/gcp/azure

systems:
  - name: "newsystem"
    kind: "newsystem"
    version: "13.0"
    setup:
      method: "native"  # docker, native, or preinstalled
      host: "localhost"
      port: 5432
      database: "benchmark"
      data_dir: "/data/newsystem"
      extra:
        memory_limit: "16g"
        max_connections: "100"

workload:
  name: "tpch"
  scale_factor: 1
  queries:
    include: ["Q01", "Q06", "Q13"]
  runs_per_query: 3
  warmup_runs: 1
```

### Step 4: Add System-Specific DDL (Optional)

If using standard workloads like TPC-H, add system-specific DDL in the workload implementation (`benchkit/workloads/tpch.py`):

```python
def _get_newsystem_ddls(self) -> dict[str, str]:
    """Get NewSystem-specific table DDLs."""
    return {
        "lineitem": """
        CREATE TABLE {schema}.{table} (
            L_ORDERKEY BIGINT NOT NULL,
            L_PARTKEY BIGINT NOT NULL,
            -- ... (full schema adapted for NewSystem)
        )
        """,
        # ... other tables
    }
```

## Adding New Workloads

### Step 1: Create Workload Implementation

Create `benchkit/workloads/newworkload.py`:

```python
from pathlib import Path
from typing import Any

from .base import Workload
from ..systems.base import SystemUnderTest


class NewWorkload(Workload):
    """Implementation for a new benchmark workload."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.query_timeout = config.get("query_timeout", 3600)
        self.data_source = config.get("data_source", "generated")

    def generate_data(self, output_dir: Path) -> bool:
        """Generate workload data."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for table in self.get_table_names():
                table_file = output_dir / f"{table}.csv"
                self._generate_table_data(table, table_file)
            
            return True
        except Exception as e:
            print(f"Data generation failed: {e}")
            return False

    def _generate_table_data(self, table_name: str, output_file: Path) -> None:
        """Generate data for a specific table."""
        # Implement table-specific data generation
        # This could use libraries like Faker, or custom generators
        with open(output_file, 'w') as f:
            # Write CSV data
            f.write("col1|col2|col3\n")
            for i in range(1000):
                f.write(f"{i}|value_{i}|{i * 10}\n")

    def create_schema(self, system: SystemUnderTest) -> bool:
        """Create schema and tables for the workload."""
        schema_name = self.get_schema_name()

        # Create schema
        if not system.create_schema(schema_name):
            return False

        # Create tables
        table_ddls = self._get_table_ddls(system.kind)

        for table_name, ddl in table_ddls.items():
            full_ddl = ddl.format(schema=schema_name, table=table_name)
            result = system.execute_query(full_ddl, query_name=f"create_table_{table_name}")

            if not result.get("success", False):
                print(f"Failed to create table {table_name}: {result.get('error')}")
                return False

        return True

    def load_data(self, system: SystemUnderTest) -> bool:
        """Load data into the database system."""
        schema_name = self.get_schema_name()

        for table_name in self.get_table_names():
            data_file = self.data_dir / f"{table_name}.csv"

            if not data_file.exists():
                print(f"Data file not found: {data_file}")
                return False

            success = system.load_data(
                table_name,
                data_file,
                schema=schema_name,
                format="csv"
            )

            if not success:
                print(f"Failed to load {table_name}")
                return False

        return True

    def get_queries(self, system: SystemUnderTest | None = None) -> dict[str, str]:
        """Get workload queries."""
        queries = {}

        # Load queries from files or define inline
        query_dir = Path("workloads") / self.name / "queries"

        if query_dir.exists():
            for query_file in sorted(query_dir.glob("*.sql")):
                query_name = query_file.stem
                with open(query_file, 'r') as f:
                    queries[query_name] = f.read()
        else:
            # Define queries inline
            queries = self._get_inline_queries()

        return queries

    def _get_inline_queries(self) -> dict[str, str]:
        """Define queries inline if no query files exist."""
        return {
            "Q01": "SELECT COUNT(*) FROM {schema}.table1",
            "Q02": "SELECT AVG(value) FROM {schema}.table2 WHERE condition = 'test'",
        }

    def get_table_names(self) -> list[str]:
        """Get list of table names for this workload."""
        return ["table1", "table2", "table3"]

    def get_schema_name(self) -> str:
        """Get schema name for this workload."""
        return self.config.get("schema", "benchmark")

    def _get_table_ddls(self, system_kind: str) -> dict[str, str]:
        """Get table DDL statements for specific database system."""
        if system_kind == "exasol":
            return self._get_exasol_ddls()
        elif system_kind == "clickhouse":
            return self._get_clickhouse_ddls()
        else:
            return self._get_generic_ddls()

    def _get_exasol_ddls(self) -> dict[str, str]:
        """Get Exasol-specific DDLs."""
        return {
            "table1": """
            CREATE TABLE {schema}.{table} (
                id DECIMAL(10,0) NOT NULL,
                name VARCHAR(100),
                value DECIMAL(15,2)
            )
            """
        }

    def _get_clickhouse_ddls(self) -> dict[str, str]:
        """Get ClickHouse-specific DDLs."""
        return {
            "table1": """
            CREATE TABLE {schema}.{table} (
                id UInt32,
                name String,
                value Decimal64(2)
            ) ENGINE = MergeTree() ORDER BY id
            """
        }

    def _get_generic_ddls(self) -> dict[str, str]:
        """Get generic SQL DDLs."""
        return self._get_exasol_ddls()
```

### Step 2: Register the Workload

Add to `benchkit/workloads/__init__.py`:

```python
from .tpch import TPCH
from .newworkload import NewWorkload

WORKLOAD_IMPLEMENTATIONS = {
    "tpch": TPCH,
    "newworkload": NewWorkload,  # Add this line
}

def create_workload(config: dict) -> Workload:
    """Factory function to create a workload."""
    workload_name = config.get("name")
    
    if workload_name not in WORKLOAD_IMPLEMENTATIONS:
        available = ", ".join(WORKLOAD_IMPLEMENTATIONS.keys())
        raise ValueError(f"Unknown workload: {workload_name}. Available: {available}")
    
    workload_class = WORKLOAD_IMPLEMENTATIONS[workload_name]
    return workload_class(config)
```

### Step 3: Create Workload Directory Structure

```bash
mkdir -p workloads/newworkload/queries
mkdir -p workloads/newworkload/data
mkdir -p workloads/newworkload/schemas
```

### Step 4: Add Query Files

Create query files in `workloads/newworkload/queries/`:

```sql
-- workloads/newworkload/queries/Q01.sql
SELECT
    category,
    COUNT(*) as count,
    AVG(value) as avg_value
FROM {schema}.table1
GROUP BY category
ORDER BY count DESC;
```

## Adding Cloud Providers

### Current Status

The framework currently supports AWS with Terraform. Adding GCP or Azure follows a similar pattern.

### Step 1: Create Infrastructure Module

Create `infra/gcp/main.tf` or `infra/azure/main.tf`:

```hcl
# Example for GCP
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

resource "google_compute_instance" "benchmark" {
  name         = "benchmark-${var.project_id}"
  machine_type = var.machine_type
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  # ... additional configuration
}

output "instance_ip" {
  value = google_compute_instance.benchmark.network_interface[0].access_config[0].nat_ip
}
```

### Step 2: Update Infrastructure Manager

Extend `benchkit/infra/manager.py` to support the new provider:

```python
def _prepare_terraform_vars(self) -> dict[str, str]:
    """Prepare terraform variables from configuration."""
    # ... existing code ...

    elif self.provider == "gcp":
        tf_vars.update({
            "project": env_config.get("project", ""),
            "zone": env_config.get("zone", ""),
            "machine_type": env_config.get("machine_type", tf_vars["instance_type"]),
        })
    
    return tf_vars

def get_infrastructure_ips(self) -> dict[str, dict[str, str]] | None:
    """
    Get public and private IPs for all systems in the infrastructure.
    
    This method is used by the status command to display infrastructure details.
    It parses terraform outputs and returns IP information for each system.
    
    Returns:
        Dictionary mapping system names to their IP addresses:
        {
            "system_name": {
                "public_ip": "1.2.3.4",
                "private_ip": "10.0.0.1"
            }
        }
    """
    if self.provider not in ["aws", "gcp", "azure"]:
        return None
    
    try:
        result = self._run_terraform_command("output", ["-json"])
        if not result.success or not result.outputs:
            return None
        
        outputs = result.outputs
        public_ips = outputs.get("system_public_ips", {})
        private_ips = outputs.get("system_private_ips", {})
        
        # Build infrastructure details
        infra_ips = {}
        for system_name, public_ip in public_ips.items():
            infra_ips[system_name] = {
                "public_ip": public_ip,
                "private_ip": private_ips.get(system_name, "-")
            }
        
        return infra_ips
    except Exception:
        return None
```

**Infrastructure Integration**: The `get_infrastructure_ips()` method provides a clean abstraction for retrieving instance IPs, used by the status command to display infrastructure details and connection strings.

## Customizing Reports

### Step 1: Create Custom Visualizations

Add to `benchkit/report/figures.py`:

```python
def create_custom_plot(df: pd.DataFrame, output_dir: Path) -> str:
    """Create a custom visualization."""
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 8))

    # Implement custom plotting logic
    for system in df['system'].unique():
        system_data = df[df['system'] == system]
        ax.plot(system_data['query'], system_data['elapsed_ms'], 
                marker='o', label=system)

    ax.set_xlabel('Query')
    ax.set_ylabel('Execution Time (ms)')
    ax.set_title('Custom Performance Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_file = output_dir / "custom_plot.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()

    return str(output_file)
```

### Step 2: Add Custom Tables

Add to `benchkit/report/tables.py`:

```python
def create_custom_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a custom analysis table."""
    custom_analysis = df.groupby("system").agg({
        "elapsed_ms": ["mean", "std", "min", "max"],
        "rows_returned": "sum"
    }).round(2)

    return custom_analysis
```

### Step 3: Create Custom Template Snippets

Create `templates/snippets/custom_analysis.md.j2`:

```markdown
### Custom Analysis Section

{{ custom_table_markdown }}

#### Key Insights

{% for insight in custom_insights %}
- {{ insight }}
{% endfor %}
```

### Step 4: Extend Report Template

Modify `templates/report.md.j2` to include custom sections:

```jinja2
## Results

{% include "custom_analysis.md.j2" %}

<!-- Rest of template -->
```

## Adding Result Verification

### Step 1: Create Verification Module

Create `benchkit/verify/verifier.py`:

```python
from pathlib import Path
from typing import Any

class ResultVerifier:
    """Verify query results against expected data."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.expected_results_dir = Path("workloads") / config["workload"]["name"] / "expected"

    def verify_query_result(self, query_name: str, result_data: Any) -> bool:
        """Verify a single query result."""
        expected_file = self.expected_results_dir / f"{query_name}.csv"
        
        if not expected_file.exists():
            print(f"No expected results for {query_name}")
            return True  # Skip if no expected results
        
        # Load expected results
        with open(expected_file, 'r') as f:
            expected = f.read()
        
        # Compare with actual results
        # Implement comparison logic based on your needs
        return True
```

### Step 2: Add to CLI

The `verify` command is already implemented in `benchkit/cli.py`. Extend the verification logic in `benchkit/verify/__init__.py`.

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

## References

- [Getting Started Guide](GETTING_STARTED.md) - Basic usage instructions
- [README](../README.md) - Quick start and overview

This extensible design allows the framework to grow and adapt to new requirements while maintaining consistency and reliability across all components.
