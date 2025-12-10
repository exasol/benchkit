"""AST-based code minimization for workload packages.

This module removes code marked with @exclude_from_package decorator
while preserving code marked with @workload_only or unmarked code.
"""

import ast
from pathlib import Path
from typing import Any


class CodeMinimizer:
    """Minimize Python files by removing excluded code."""

    def __init__(self, package_dir: Path):
        self.package_dir = package_dir
        self.stats = {
            "methods_removed": 0,
            "functions_removed": 0,
            "lines_before": 0,
            "lines_after": 0,
            "files_processed": 0,
        }

    def minimize_file(self, filepath: Path) -> str:
        """Minimize a Python file by removing excluded code.

        Args:
            filepath: Path to Python file to minimize

        Returns:
            Minimized source code as string
        """
        source = filepath.read_text()
        self.stats["lines_before"] += len(source.splitlines())

        # Check if original has future annotations - ast.unparse() strips this
        has_future_annotations = "from __future__ import annotations" in source

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            print(f"Warning: Could not parse {filepath}: {e}")
            return source

        # Transform AST: remove excluded nodes
        transformer = ExclusionTransformer()
        new_tree = transformer.visit(tree)

        # Remove marker imports
        new_tree = self._remove_marker_imports(new_tree)

        # Convert back to source
        try:
            minimized = ast.unparse(new_tree)
        except Exception as e:
            print(f"Warning: Could not unparse {filepath}: {e}")
            return source

        # Re-add future annotations if it was present in original
        # This is critical for TYPE_CHECKING imports to work correctly
        if (
            has_future_annotations
            and "from __future__ import annotations" not in minimized
        ):
            minimized = "from __future__ import annotations\n\n" + minimized

        # Update stats
        self.stats["lines_after"] += len(minimized.splitlines())
        self.stats["methods_removed"] += transformer.methods_removed
        self.stats["functions_removed"] += transformer.functions_removed
        self.stats["files_processed"] += 1

        return minimized

    def minimize_all(self) -> dict[str, Any]:
        """Minimize all Python files in package.

        Returns:
            Statistics dictionary with removal counts and line counts
        """
        for py_file in self.package_dir.rglob("*.py"):
            if self._should_minimize(py_file):
                minimized = self.minimize_file(py_file)
                py_file.write_text(minimized)

        return self.stats

    def _should_minimize(self, filepath: Path) -> bool:
        """Check if file should be minimized."""
        # Skip __init__.py files (usually minimal)
        if filepath.name == "__init__.py":
            return False

        # Skip files in test directories
        if "test" in str(filepath):
            return False

        return True

    def _remove_marker_imports(self, tree: ast.Module) -> ast.Module:
        """Remove imports of marker decorators."""
        new_body = []

        for node in tree.body:
            # Remove: from ..package.markers import ...
            if isinstance(node, ast.ImportFrom):
                if (
                    node.module
                    and "markers" in node.module
                    and any(
                        alias.name in ("workload_only", "exclude_from_package")
                        for alias in node.names
                    )
                ):
                    continue  # Skip this import

            new_body.append(node)

        tree.body = new_body
        return tree


class ExclusionTransformer(ast.NodeTransformer):
    """AST transformer that removes @exclude_from_package nodes."""

    def __init__(self) -> None:
        self.methods_removed = 0
        self.functions_removed = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Filter class methods based on decorators."""
        filtered_body: list[ast.stmt] = []

        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                if not self._is_excluded(item):
                    # Keep method, but remove marker decorators
                    cleaned_item = self._remove_marker_decorators(item)
                    # Continue visiting child nodes
                    visited_item = self.generic_visit(cleaned_item)
                    if visited_item is not None and isinstance(visited_item, ast.stmt):
                        filtered_body.append(visited_item)
                else:
                    self.methods_removed += 1
            else:
                # Continue visiting other nodes (nested classes, etc.)
                visited_item = self.generic_visit(item)
                if visited_item is not None and isinstance(visited_item, ast.stmt):
                    filtered_body.append(visited_item)

        node.body = filtered_body
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef | None:
        """Filter module-level functions."""
        if self._is_excluded(node):
            self.functions_removed += 1
            return None  # Remove from AST

        # Remove marker decorators and continue visiting
        cleaned_node = self._remove_marker_decorators(node)
        visited_node = self.generic_visit(cleaned_node)
        # generic_visit returns AST which might be FunctionDef
        if isinstance(visited_node, ast.FunctionDef):
            return visited_node
        return None

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef | None:
        """Filter async module-level functions."""
        if self._is_excluded(node):
            self.functions_removed += 1
            return None  # Remove from AST

        # Remove marker decorators and continue visiting
        cleaned_node = self._remove_marker_decorators(node)
        visited_node = self.generic_visit(cleaned_node)
        # generic_visit returns AST which might be AsyncFunctionDef
        if isinstance(visited_node, ast.AsyncFunctionDef):
            return visited_node
        return None

    def _is_excluded(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if node has @exclude_from_package decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == "exclude_from_package":
                    return True
            # Handle decorated decorators: @classmethod + @exclude_from_package
            elif isinstance(decorator, ast.Call) and isinstance(
                decorator.func, ast.Name
            ):
                if decorator.func.id == "exclude_from_package":
                    return True

        return False

    def _remove_marker_decorators(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        """Remove @workload_only and @exclude_from_package decorators."""
        new_decorators: list[ast.expr] = []

        for decorator in node.decorator_list:
            # Remove simple decorators: @workload_only, @exclude_from_package
            if isinstance(decorator, ast.Name):
                if decorator.id not in ("workload_only", "exclude_from_package"):
                    new_decorators.append(decorator)
            # Remove called decorators: @workload_only(), @exclude_from_package()
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id not in (
                        "workload_only",
                        "exclude_from_package",
                    ):
                        new_decorators.append(decorator)
                else:
                    new_decorators.append(decorator)
            else:
                new_decorators.append(decorator)

        node.decorator_list = new_decorators
        return node
