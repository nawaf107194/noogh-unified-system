"""
CodeAnalyzer - Analyzes code structure and extracts information
"""

import ast
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes Python code structure"""

    def __init__(self):
        """Initialize CodeAnalyzer"""
        logger.info("CodeAnalyzer initialized")

    def extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Extract all function definitions from AST

        Args:
            tree: AST tree

        Returns:
            List of function info dictionaries
        """
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "returns": ast.unparse(node.returns) if node.returns else None,
                    "docstring": ast.get_docstring(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                }
                functions.append(func_info)

        logger.info(f"Extracted {len(functions)} functions")
        return functions

    def extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Extract all class definitions from AST

        Args:
            tree: AST tree

        Returns:
            List of class info dictionaries
        """
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Get methods
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)

                class_info = {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": methods,
                    "docstring": ast.get_docstring(node),
                }
                classes.append(class_info)

        logger.info(f"Extracted {len(classes)} classes")
        return classes

    def extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """
        Extract all imports from AST

        Args:
            tree: AST tree

        Returns:
            List of import info dictionaries
        """
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"type": "import", "module": alias.name, "alias": alias.asname, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        }
                    )

        logger.info(f"Extracted {len(imports)} imports")
        return imports

    def get_complexity(self, tree: ast.AST) -> int:
        """
        Calculate cyclomatic complexity

        Args:
            tree: AST tree

        Returns:
            Complexity score
        """
        complexity = 1  # Base complexity

        for node in ast.walk(tree):
            # Count decision points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        return complexity

    def analyze_file(self, tree: ast.AST, file_path: str = None) -> Dict[str, Any]:
        """
        Complete analysis of a file

        Args:
            tree: AST tree
            file_path: Optional file path for context

        Returns:
            Complete analysis dictionary
        """
        analysis = {
            "file": file_path,
            "functions": self.extract_functions(tree),
            "classes": self.extract_classes(tree),
            "imports": self.extract_imports(tree),
            "complexity": self.get_complexity(tree),
            "lines": len(ast.unparse(tree).split("\n")),
        }

        logger.info(f"Analyzed {file_path}: {len(analysis['functions'])} functions, {len(analysis['classes'])} classes")
        return analysis


if __name__ == "__main__":
    # Test CodeAnalyzer
    pass

    from .code_reader import CodeReader

    reader = CodeReader()
    analyzer = CodeAnalyzer()

    # Analyze this file
    tree = reader.parse_python_file(__file__)
    if tree:
        analysis = analyzer.analyze_file(tree, __file__)
        print(f"Functions: {len(analysis['functions'])}")
        print(f"Classes: {len(analysis['classes'])}")
        print(f"Imports: {len(analysis['imports'])}")
        print(f"Complexity: {analysis['complexity']}")
