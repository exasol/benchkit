"""Base classes for benchmark workloads."""

import random
import threading
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from ..systems.base import SystemUnderTest


class Workload(ABC):
    """Abstract base class for benchmark workloads."""

    def __init__(self, config: dict[str, Any]):
        self.name = config["name"]
        self.scale_factor = config.get("scale_factor", 1)
        self.config = config
        self.data_dir = Path(f"data/{self.name}/sf{self.scale_factor}")

    @abstractmethod
    def generate_data(self, output_dir: Path) -> bool:
        """
        Generate benchmark data.

        Args:
            output_dir: Directory to store generated data

        Returns:
            True if data generation successful, False otherwise
        """
        pass

    @abstractmethod
    def create_schema(self, system: SystemUnderTest) -> bool:
        """
        Create database schema and tables for the workload.

        Args:
            system: System under test to create schema on

        Returns:
            True if schema creation successful, False otherwise
        """
        pass

    @abstractmethod
    def load_data(self, system: SystemUnderTest) -> bool:
        """
        Load generated data into the database system.

        Args:
            system: System under test to load data into

        Returns:
            True if data loading successful, False otherwise
        """
        pass

    @abstractmethod
    def get_queries(self, system: SystemUnderTest|None = None) -> dict[str, str]:
        """
        Get the benchmark queries.

        Args:
            system: Optional system under test for query template resolution

        Returns:
            Dictionary mapping query names to SQL text
        """
        pass

    @abstractmethod
    def get_all_query_names(self) -> list[str]:
        """
        Get list of all query names available in this workload.

        Returns:
            List of query names (e.g., ["Q01", "Q02", ...])
        """
        pass

    @abstractmethod
    def run_query(
        self, system: SystemUnderTest, query_name: str, query_sql: str
    ) -> dict[str, Any]:
        """
        Execute a single benchmark query.

        Args:
            system: System under test
            query_name: Name of the query
            query_sql: SQL text to execute

        Returns:
            Query execution result dictionary
        """
        pass

    def prepare(self, system: SystemUnderTest) -> bool:
        """
        Prepare the workload for execution (generate data, create schema, load data).

        Args:
            system: System under test

        Returns:
            True if preparation successful, False otherwise
        """
        from ..util import Timer

        # Initialize preparation timings
        self.preparation_timings = {}

        # Check if system provides a custom data generation directory (e.g., on additional disk)
        custom_data_dir = system.get_data_generation_directory(self)
        if custom_data_dir:
            self.data_dir = Path(custom_data_dir)
            print(f"Using system-provided data directory: {self.data_dir}")

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generate data if not already present
        if not self._is_data_generated():
            print(f"Generating {self.name} data (SF={self.scale_factor})...")
            with Timer(f"Data generation (SF={self.scale_factor})") as timer:
                if not self.generate_data(self.data_dir):
                    print("Data generation failed")
                    return False
            self.preparation_timings["data_generation_s"] = timer.elapsed
            print(f"  ✓ Data generated in {timer.elapsed:.2f}s")
        else:
            print("Data already exists, skipping generation")
            self.preparation_timings["data_generation_s"] = 0.0

        # Create schema
        print(f"Creating schema for {self.name}...")
        with Timer("Schema creation") as timer:
            if not self.create_schema(system):
                print("Schema creation failed")
                return False
        self.preparation_timings["schema_creation_s"] = timer.elapsed
        print(f"  ✓ Schema created in {timer.elapsed:.2f}s")

        # Load data
        print(f"Loading {self.name} data...")
        with Timer("Data loading") as timer:
            if not self.load_data(system):
                print("Data loading failed")
                return False
        self.preparation_timings["data_loading_s"] = timer.elapsed
        print(f"  ✓ Data loaded in {timer.elapsed:.2f}s")

        # Calculate total preparation time
        self.preparation_timings["total_preparation_s"] = sum(
            self.preparation_timings.values()
        )

        return True

    def run_workload(
        self,
        system: SystemUnderTest,
        query_names: list[str],
        runs_per_query: int = 3,
        warmup_runs: int = 1,
        num_streams: int = 1,
        randomize: bool = False,
        random_seed: int | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Execute the full workload against a system.

        Args:
            system: System under test
            query_names: List of query names to execute
            runs_per_query: Number of measured runs per query
            warmup_runs: Number of warmup runs per query
            num_streams: Number of concurrent execution streams (1 = sequential)
            randomize: Whether to randomize query execution order across streams
            random_seed: Optional random seed for reproducibility

        Returns:
            Dictionary with 'measured' and 'warmup' keys containing lists of query execution results
        """
        # Decision logic: single-stream (sequential) or multi-stream (concurrent)
        if num_streams <= 1:
            return self._run_workload_sequential(
                system, query_names, runs_per_query, warmup_runs
            )
        else:
            return self._run_workload_multiuser(
                system,
                query_names,
                runs_per_query,
                warmup_runs,
                num_streams,
                randomize,
                random_seed,
            )

    def _run_workload_sequential(
        self,
        system: SystemUnderTest,
        query_names: list[str],
        runs_per_query: int,
        warmup_runs: int,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Execute workload sequentially on a single connection.

        Args:
            system: System under test
            query_names: List of query names to execute
            runs_per_query: Number of measured runs per query
            warmup_runs: Number of warmup runs per query

        Returns:
            Dictionary with 'measured' and 'warmup' keys containing results
        """
        all_queries = self.get_queries()
        measured_results = []
        warmup_results = []

        for query_name in query_names:
            if query_name not in all_queries:
                print(f"Warning: Query {query_name} not found in workload")
                continue

            query_sql = all_queries[query_name]
            print(f"Running {query_name}...")

            # Warmup runs (sequential)
            for warmup in range(warmup_runs):
                print(f"  Warmup {warmup + 1}/{warmup_runs}")
                result = self.run_query(
                    system, f"{query_name}_warmup_{warmup + 1}", query_sql
                )
                result.update(
                    {
                        "run_number": warmup + 1,
                        "system": system.name,
                        "workload": self.name,
                        "scale_factor": self.scale_factor,
                        "variant": self.config.get("variant", "official"),
                        "stream_id": None,  # Sequential execution has no stream
                    }
                )
                warmup_results.append(result)

            # Measured runs (sequential)
            for run in range(runs_per_query):
                print(f"  Run {run + 1}/{runs_per_query}")
                result = self.run_query(system, query_name, query_sql)
                result.update(
                    {
                        "run_number": run + 1,
                        "system": system.name,
                        "workload": self.name,
                        "scale_factor": self.scale_factor,
                        "variant": self.config.get("variant", "official"),
                        "stream_id": None,  # Sequential execution has no stream
                    }
                )
                measured_results.append(result)

        return {"measured": measured_results, "warmup": warmup_results}

    def _run_workload_multiuser(
        self,
        system: SystemUnderTest,
        query_names: list[str],
        runs_per_query: int,
        warmup_runs: int,
        num_streams: int,
        randomize: bool,
        random_seed: int | None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Execute workload with multiple concurrent streams.

        Args:
            system: System under test
            query_names: List of query names to execute
            runs_per_query: Number of measured runs per query
            warmup_runs: Number of warmup runs per query
            num_streams: Number of concurrent execution streams
            randomize: Whether to randomize query execution order
            random_seed: Optional random seed for reproducibility

        Returns:
            Dictionary with 'measured' and 'warmup' keys containing results
        """
        all_queries = self.get_queries()
        warmup_results = []

        print(f"Running multiuser workload with {num_streams} concurrent streams")
        print(f"Randomize: {randomize}, Seed: {random_seed}")

        # Phase 1: Warmup runs (sequential, single connection)
        print("\nPhase 1: Warmup runs (sequential)")
        for query_name in query_names:
            if query_name not in all_queries:
                print(f"Warning: Query {query_name} not found in workload")
                continue

            query_sql = all_queries[query_name]
            print(f"Running {query_name} warmup...")

            for warmup in range(warmup_runs):
                print(f"  Warmup {warmup + 1}/{warmup_runs}")
                result = self.run_query(
                    system, f"{query_name}_warmup_{warmup + 1}", query_sql
                )
                result.update(
                    {
                        "run_number": warmup + 1,
                        "system": system.name,
                        "workload": self.name,
                        "scale_factor": self.scale_factor,
                        "variant": self.config.get("variant", "official"),
                        "stream_id": None,  # Warmup is sequential
                    }
                )
                warmup_results.append(result)

        # Phase 2: Measured runs (multiuser with concurrent streams)
        print(f"\nPhase 2: Measured runs ({num_streams} concurrent streams)")

        # Build list of all query executions: [(query_name, run_number), ...]
        query_executions = []
        for query_name in query_names:
            if query_name not in all_queries:
                continue
            for run in range(1, runs_per_query + 1):
                query_executions.append((query_name, run))

        total_executions = len(query_executions)
        print(
            f"Total query executions: {total_executions} "
            f"({len(query_names)} queries × {runs_per_query} runs)"
        )

        # Randomize if requested
        if randomize:
            rng = random.Random(random_seed)
            rng.shuffle(query_executions)
            print(f"Query execution order randomized (seed: {random_seed})")
        else:
            print("Query execution order: round-robin")

        # Distribute query executions across streams
        stream_assignments: list[list[tuple[str, int]]] = [
            [] for _ in range(num_streams)
        ]
        for idx, query_exec in enumerate(query_executions):
            stream_id = idx % num_streams
            stream_assignments[stream_id].append(query_exec)

        # Print distribution
        for stream_id, assignments in enumerate(stream_assignments):
            print(f"  Stream {stream_id}: {len(assignments)} queries")

        # Execute queries concurrently using ThreadPoolExecutor
        measured_results = []
        results_lock = threading.Lock()

        def collect_result(result: dict[str, Any]) -> None:
            """Thread-safe result collection."""
            with results_lock:
                measured_results.append(result)

        with ThreadPoolExecutor(max_workers=num_streams) as executor:
            # Submit all streams
            futures = []
            for stream_id, assignments in enumerate(stream_assignments):
                future = executor.submit(
                    self._execute_stream,
                    stream_id,
                    assignments,
                    all_queries,
                    system,
                    collect_result,
                )
                futures.append(future)

            # Wait for all streams to complete
            for future in as_completed(futures):
                try:
                    stream_id, queries_executed = future.result()
                    print(f"  Stream {stream_id} completed: {queries_executed} queries")
                except Exception as e:
                    print(f"  Stream execution failed: {e}")

        print(f"\nCompleted: {len(measured_results)} total query executions")

        return {"measured": measured_results, "warmup": warmup_results}

    def _execute_stream(
        self,
        stream_id: int,
        query_assignments: list[tuple[str, int]],
        all_queries: dict[str, str],
        system: SystemUnderTest,
        result_callback: Callable[[dict[str, Any]], None],
    ) -> tuple[int, int]:
        """
        Execute queries for a single stream.

        Args:
            stream_id: ID of this stream (0-based)
            query_assignments: List of (query_name, run_number) tuples to execute
            all_queries: Dictionary of all available queries
            system: System under test
            result_callback: Callback function to collect results (thread-safe)

        Returns:
            Tuple of (stream_id, number_of_queries_executed)
        """
        queries_executed = 0

        for query_name, run_number in query_assignments:
            query_sql = all_queries[query_name]

            try:
                # Execute query
                result = self.run_query(system, query_name, query_sql)

                # Add metadata
                result.update(
                    {
                        "run_number": run_number,
                        "system": system.name,
                        "workload": self.name,
                        "scale_factor": self.scale_factor,
                        "variant": self.config.get("variant", "official"),
                        "stream_id": stream_id,
                    }
                )

                # Collect result via thread-safe callback
                result_callback(result)
                queries_executed += 1

            except Exception as e:
                # Log error but continue with other queries
                print(f"  Stream {stream_id}: Error executing {query_name}: {e}")

                # Record failed execution
                error_result = {
                    "query": query_name,
                    "elapsed_ms": 0,
                    "success": False,
                    "error": str(e),
                    "run_number": run_number,
                    "system": system.name,
                    "workload": self.name,
                    "scale_factor": self.scale_factor,
                    "variant": self.config.get("variant", "official"),
                    "stream_id": stream_id,
                }
                result_callback(error_result)

        return stream_id, queries_executed

    def get_schema_name(self) -> str:
        """Get the schema name for this workload."""
        return f"{self.name}_sf{self.scale_factor}"

    @classmethod
    def get_python_dependencies(cls) -> list[str]:
        """Return list of Python packages required by this workload."""
        return []

    def get_data_size_info(self) -> dict[str, Any]:
        """Get information about generated data size."""
        info = {
            "scale_factor": self.scale_factor,
            "data_directory": str(self.data_dir),
            "data_exists": self._is_data_generated(),
        }

        if self._is_data_generated():
            # Calculate total size of data files
            total_size = sum(
                f.stat().st_size for f in self.data_dir.rglob("*") if f.is_file()
            )
            info["total_size_bytes"] = total_size
            info["total_size_mb"] = int(round(total_size / (1024 * 1024), 2))

        return info

    def _is_data_generated(self) -> bool:
        """Check if data has already been generated."""
        # Default implementation - check if data directory exists and is not empty
        return self.data_dir.exists() and any(self.data_dir.iterdir())

    def get_workload_description(self) -> dict[str, Any]:
        """
        Get workload description for report.

        Returns:
            Dictionary with 'short' and 'full' description, and optional 'characteristics' list
        """
        return {
            "short": f"{self.name.upper()} benchmark workload",
            "full": f"This benchmark uses the {self.name.upper()} workload at scale factor {self.scale_factor}.",
        }

    def get_table_info(self) -> dict[str, dict[str, Any]]:
        """
        Return table metadata (names, columns, descriptions).

        Returns:
            Dictionary mapping table names to table metadata including:
            - description: Human-readable description
            - columns: List of column names
            - cardinality_sf1: Approximate row count at SF=1 (optional)
            - relationships: List of relationship descriptions (optional)
        """
        # Default implementation - subclasses should override
        return {}

    def get_setup_script_info(self) -> dict[str, str]:
        """
        Return descriptions of setup steps.

        Returns:
            Dictionary mapping script names to human-readable descriptions
        """
        return {
            "schema_creation": "Create database schema and tables",
            "index_creation": "Create indexes for query optimization",
            "table_analysis": "Analyze tables and update statistics",
        }

    def get_rendered_setup_scripts(self, system: SystemUnderTest) -> dict[str, str]:
        """
        Return rendered setup scripts for a specific system.

        Args:
            system: System under test to render scripts for

        Returns:
            Dictionary mapping script names to rendered SQL content
        """
        # Default implementation - subclasses should override if they use setup scripts
        return {}

    def get_workload_info(self) -> dict[str, Any]:
        """Get comprehensive information about this workload."""
        # Get query names - try to get from get_all_query_names() if available,
        # otherwise fall back to empty list (workload can override this method)
        try:
            if hasattr(self, "get_all_query_names"):
                query_names = self.get_all_query_names()
            else:
                # Try to get queries without system parameter (may fail for some workloads)
                try:
                    queries = self.get_queries()
                    query_names = list(queries.keys())
                except (ValueError, TypeError):
                    query_names = []
        except Exception:
            query_names = []

        return {
            "name": self.name,
            "description": self.get_workload_description(),
            "scale_factor": self.scale_factor,
            "config": self.config,
            "data_info": self.get_data_size_info(),
            "query_names": query_names,
            "query_count": len(query_names),
            "table_info": self.get_table_info(),
            "setup_steps": self.get_setup_script_info(),
            "schema_name": self.get_schema_name(),
        }


def get_workload_class(workload_name: str) -> type | None:
    """
    Dynamically import and return the workload class for the given workload name.

    Args:
        workload_name: The workload identifier (e.g., 'tpch', 'tpcds')

    Returns:
        The workload class if found, None otherwise
    """
    import importlib
    import inspect

    class_name = f"{workload_name.upper()}Workload"
    module_name = f"benchkit.workloads.{workload_name}"

    try:
        module = importlib.import_module(module_name)

        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            return cls if isinstance(cls, type) else None
        else:
            # Try to find any class that inherits from Workload
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    inspect.isclass(attr)
                    and issubclass(attr, Workload)
                    and attr != Workload
                ):
                    return attr

            return None

    except ImportError:
        return None
