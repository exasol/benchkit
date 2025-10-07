"""Remove unused imports after code minimization."""

import ast
from pathlib import Path


class ImportCleaner:
    """Clean unused imports from minimized Python files."""

    def clean_file(self, filepath: Path) -> str:
        """Remove unused imports from a Python file.

        Args:
            filepath: Path to Python file

        Returns:
            Cleaned source code as string
        """
        source = filepath.read_text()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            # If we can't parse it, return unchanged
            return source

        # 1. Collect all imports
        import_collector = ImportCollector()
        import_collector.visit(tree)

        # 2. Collect all name usages
        name_collector = NameCollector()
        name_collector.visit(tree)

        # 3. Remove unused imports
        cleaner = UnusedImportRemover(
            import_collector.imports, name_collector.used_names
        )
        new_tree = cleaner.visit(tree)

        try:
            return ast.unparse(new_tree)
        except Exception:
            return source


class ImportCollector(ast.NodeVisitor):
    """Collect all imports from AST."""

    def __init__(self) -> None:
        self.imports: dict[str, ast.Import | ast.ImportFrom] = {}

    def visit_Import(self, node: ast.Import) -> None:
        """Collect simple imports: import foo"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Collect from imports: from foo import bar"""
        for alias in node.names:
            if alias.name == "*":
                # Star imports are always kept
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node


class NameCollector(ast.NodeVisitor):
    """Collect all name usages in code (excluding imports)."""

    def __init__(self) -> None:
        self.used_names: set[str] = set()
        self._in_import = False

    def visit_Import(self, node: ast.Import) -> None:
        """Skip import statements themselves."""
        self._in_import = True
        self.generic_visit(node)
        self._in_import = False

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Skip import-from statements themselves."""
        self._in_import = True
        self.generic_visit(node)
        self._in_import = False

    def visit_Name(self, node: ast.Name) -> None:
        """Collect name usages."""
        if not self._in_import:
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Collect attribute access (e.g., foo.bar -> collect 'foo')."""
        if isinstance(node.value, ast.Name):
            if not self._in_import:
                self.used_names.add(node.value.id)
        self.generic_visit(node)


class UnusedImportRemover(ast.NodeTransformer):
    """Remove imports that are not used in the code."""

    def __init__(self, imports: dict, used_names: set[str]):
        self.imports = imports
        self.used_names = used_names

    def visit_Import(self, node: ast.Import) -> ast.Import | None:
        """Remove unused simple imports."""
        used_aliases = []

        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name in self.used_names:
                used_aliases.append(alias)

        if not used_aliases:
            return None  # Remove entire import

        node.names = used_aliases
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom | None:
        """Remove unused from-imports."""
        # Always keep star imports
        if any(alias.name == "*" for alias in node.names):
            return node

        used_aliases = []

        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if name in self.used_names:
                used_aliases.append(alias)

        if not used_aliases:
            return None  # Remove entire import

        node.names = used_aliases
        return node
