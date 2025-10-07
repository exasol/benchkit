"""Validate that all public methods are properly marked with decorators."""

import ast
import sys
from pathlib import Path


class MarkerValidator:
    """Validate that all public methods have appropriate markers."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_file(self, filepath: Path) -> list[str]:
        """Check that all public methods have appropriate markers.

        Args:
            filepath: Path to Python file to validate

        Returns:
            List of error messages (empty if no errors)
        """
        try:
            source = filepath.read_text()
            tree = ast.parse(source)
        except SyntaxError as e:
            return [f"{filepath}: Syntax error - {e}"]

        validator = MarkerCheckVisitor(filepath)
        validator.visit(tree)

        return validator.errors

    def validate_all_framework_files(self) -> bool:
        """Validate all framework files have proper markers.

        Returns:
            True if all files pass validation, False otherwise
        """
        files_to_check = [
            "benchkit/systems/base.py",
            "benchkit/systems/exasol.py",
            "benchkit/systems/clickhouse.py",
            "benchkit/util.py",
            "benchkit/config.py",
        ]

        all_errors = []
        for file in files_to_check:
            filepath = Path(file)
            if not filepath.exists():
                print(f"Warning: File not found: {file}")
                continue

            errors = self.validate_file(filepath)
            all_errors.extend(errors)

        if all_errors:
            print("❌ Marker validation failed:")
            for error in all_errors:
                print(f"  {error}")
            return False

        print("✅ All public methods properly marked")
        return True


class MarkerCheckVisitor(ast.NodeVisitor):
    """Visit all methods and check for markers."""

    REQUIRED_MARKERS = {"workload_only", "exclude_from_package"}

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.errors: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class and check its methods."""
        self.current_class: str | None = node.name
        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                self._check_method(item, node.name)

        # Continue visiting nested classes
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check module-level functions."""
        if self._is_public_function(node):
            markers = self._get_markers(node)

            if not markers:
                self.errors.append(
                    f"{self.filepath}:{node.lineno} - "
                    f"Function '{node.name}' missing marker decorator"
                )

        self.generic_visit(node)

    def _check_method(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, class_name: str
    ) -> None:
        """Check if method has a marker decorator."""
        # Skip private methods (start with _) and special methods (like __init__)
        if not self._is_public_method(node):
            return

        # Skip abstract methods (they're marked in base class)
        if self._is_abstract_method(node):
            return

        markers = self._get_markers(node)

        if not markers:
            self.errors.append(
                f"{self.filepath}:{node.lineno} - "
                f"Method '{class_name}.{node.name}' missing marker decorator"
            )
        elif len(markers) > 1:
            self.errors.append(
                f"{self.filepath}:{node.lineno} - "
                f"Method '{class_name}.{node.name}' has multiple markers: {markers}"
            )

    def _is_public_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if method is public (not private/dunder)."""
        # Skip properties (they can't have custom attributes)
        if self._is_property(node):
            return False
        return not node.name.startswith("_")

    def _is_property(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if method is a property."""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == "property":
                return True
        return False

    def _is_public_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function is public (not private)."""
        return not node.name.startswith("_")

    def _is_abstract_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if method has @abstractmethod decorator."""
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id == "abstractmethod":
                return True
        return False

    def _get_markers(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> set:
        """Extract marker decorators from node."""
        markers = set()
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in self.REQUIRED_MARKERS:
                markers.add(dec.id)
        return markers


def main() -> None:
    """Run marker validation as a script."""
    validator = MarkerValidator()
    success = validator.validate_all_framework_files()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
