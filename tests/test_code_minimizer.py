"""Tests for AST-based code minimizer."""

import ast
import tempfile
from pathlib import Path

from benchkit.package.code_minimizer import CodeMinimizer, ExclusionTransformer


def test_excludes_marked_methods():
    """Test that @exclude_from_package methods are removed."""
    code = """
from benchkit.package.markers import exclude_from_package, workload_only

class TestSystem:
    @workload_only
    def execute_query(self):
        pass

    @exclude_from_package
    def install(self):
        pass

    @exclude_from_package
    def setup_storage(self):
        pass
"""
    tree = ast.parse(code)
    transformer = ExclusionTransformer()
    result = transformer.visit(tree)

    # Check that install() and setup_storage() were removed
    class_node = result.body[1]  # TestSystem class (after import)
    method_names = [m.name for m in class_node.body if isinstance(m, ast.FunctionDef)]

    assert "execute_query" in method_names
    assert "install" not in method_names
    assert "setup_storage" not in method_names
    assert transformer.methods_removed == 2


def test_removes_marker_decorators():
    """Test that marker decorators are removed from remaining code."""
    code = """
from benchkit.package.markers import workload_only

class TestSystem:
    @workload_only
    def execute_query(self):
        return "test"
"""
    tree = ast.parse(code)
    transformer = ExclusionTransformer()
    result = transformer.visit(tree)

    # Check that @workload_only decorator was removed
    class_node = result.body[1]  # TestSystem class
    execute_query = class_node.body[0]

    assert len(execute_query.decorator_list) == 0


def test_minimizer_reduces_file():
    """Test that minimizer reduces file size."""
    code = '''
from benchkit.package.markers import exclude_from_package, workload_only

class TestSystem:
    @workload_only
    def needed_method(self):
        """This should be kept."""
        return True

    @exclude_from_package
    def not_needed_method(self):
        """This should be removed."""
        return False

    @exclude_from_package
    def another_excluded(self):
        """Also removed."""
        pass
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text(code)

        minimizer = CodeMinimizer(Path(tmpdir))
        minimized = minimizer.minimize_file(test_file)

        # Verify exclusions
        assert "needed_method" in minimized
        assert "not_needed_method" not in minimized
        assert "another_excluded" not in minimized

        # Verify markers removed
        assert "@workload_only" not in minimized
        assert "@exclude_from_package" not in minimized
        assert "from benchkit.package.markers import" not in minimized


def test_preserves_other_decorators():
    """Test that non-marker decorators are preserved."""
    code = """
from benchkit.package.markers import workload_only

class TestSystem:
    @staticmethod
    @workload_only
    def static_method():
        pass

    @classmethod
    @workload_only
    def class_method(cls):
        pass
"""
    tree = ast.parse(code)
    transformer = ExclusionTransformer()
    result = transformer.visit(tree)

    class_node = result.body[1]

    # Check that @staticmethod and @classmethod are preserved
    static_method = class_node.body[0]
    assert any(
        isinstance(d, ast.Name) and d.id == "staticmethod"
        for d in static_method.decorator_list
    )

    class_method = class_node.body[1]
    assert any(
        isinstance(d, ast.Name) and d.id == "classmethod"
        for d in class_method.decorator_list
    )

    # Check that @workload_only was removed
    assert not any(
        isinstance(d, ast.Name) and d.id == "workload_only"
        for d in static_method.decorator_list
    )
    assert not any(
        isinstance(d, ast.Name) and d.id == "workload_only"
        for d in class_method.decorator_list
    )
