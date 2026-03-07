"""
CodeReader - Reads and parses project files
Enables Noug to read its own source code
"""

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeReader:
    """Reads and parses code files from the project"""

    def __init__(self, project_root: str = None):
        """
        Initialize CodeReader

        Args:
            project_root: Root directory of the project (defaults to noug-neural-os)
        """
        if project_root is None:
            # Auto-detect project root
            current_file = Path(__file__).resolve()
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        logger.info(f"CodeReader initialized with project root: {self.project_root}")

    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read a single file

        Args:
            file_path: Path to file (relative to project root or absolute)

        Returns:
            File contents as string, or None if error
        """
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.project_root / path

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.info(f"Read file: {path} ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    def parse_python_file(self, file_path: str) -> Optional[ast.AST]:
        """
        Parse a Python file into AST

        Args:
            file_path: Path to Python file

        Returns:
            AST tree or None if error
        """
        content = self.read_file(file_path)
        if content is None:
            return None

        try:
            tree = ast.parse(content, filename=str(file_path))
            logger.info(f"Parsed {file_path} into AST")
            return tree
        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return None

    def list_python_files(self, directory: str = None) -> List[Path]:
        """
        List all Python files in a directory

        Args:
            directory: Directory to search (defaults to project root)

        Returns:
            List of Python file paths
        """
        if directory is None:
            search_dir = self.project_root
        else:
            search_dir = Path(directory)
            if not search_dir.is_absolute():
                search_dir = self.project_root / search_dir

        python_files = []
        for path in search_dir.rglob("*.py"):
            # Skip __pycache__ and venv
            if "__pycache__" not in str(path) and "venv" not in str(path):
                python_files.append(path)

        logger.info(f"Found {len(python_files)} Python files in {search_dir}")
        return python_files

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata about a file

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path

        if not path.exists():
            return {"error": "File not found"}

        stat = path.stat()

        return {
            "path": str(path),
            "name": path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "is_python": path.suffix == ".py",
            "relative_path": str(path.relative_to(self.project_root)),
        }

    def read_module(self, module_path: str) -> Dict[str, Any]:
        """
        Read an entire module (directory with __init__.py)

        Args:
            module_path: Path to module directory

        Returns:
            Dictionary with module info and files
        """
        path = Path(module_path)
        if not path.is_absolute():
            path = self.project_root / path

        if not path.is_dir():
            return {"error": "Not a directory"}

        # Check for __init__.py
        init_file = path / "__init__.py"
        has_init = init_file.exists()

        # Get all Python files in module
        files = []
        for py_file in path.glob("*.py"):
            files.append({"name": py_file.name, "path": str(py_file), "size": py_file.stat().st_size})

        return {"module_path": str(path), "is_package": has_init, "files": files, "file_count": len(files)}

    def search_in_files(self, pattern: str, directory: str = None) -> List[Dict[str, Any]]:
        """
        Search for a pattern in Python files

        Args:
            pattern: String to search for
            directory: Directory to search in

        Returns:
            List of matches with file and line info
        """
        files = self.list_python_files(directory)
        matches = []

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            matches.append(
                                {
                                    "file": str(file_path.relative_to(self.project_root)),
                                    "line": line_num,
                                    "content": line.strip(),
                                }
                            )
            except Exception as e:
                logger.warning(f"Error searching {file_path}: {e}")

        logger.info(f"Found {len(matches)} matches for '{pattern}'")
        return matches


if __name__ == "__main__":
    # Test CodeReader
    reader = CodeReader()

    # List Python files
    files = reader.list_python_files()
    print(f"Found {len(files)} Python files")

    # Read this file
    content = reader.read_file(__file__)
    print(f"Read {len(content)} characters from this file")

    # Search for "class"
    matches = reader.search_in_files("class CodeReader")
    print(f"Found {len(matches)} matches")
