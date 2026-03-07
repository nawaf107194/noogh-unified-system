"""
DependencyMapper - Maps dependencies between modules
"""

import logging
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)


class DependencyMapper:
    """Maps dependencies between modules"""

    def __init__(self):
        """Initialize DependencyMapper"""
        self.dependency_graph = {}
        logger.info("DependencyMapper initialized")

    def add_file_dependencies(self, file_path: str, imports: List[Dict[str, Any]]):
        """
        Add dependencies for a file

        Args:
            file_path: Path to file
            imports: List of imports from CodeAnalyzer
        """
        if file_path not in self.dependency_graph:
            self.dependency_graph[file_path] = set()

        for imp in imports:
            if imp["type"] == "import":
                self.dependency_graph[file_path].add(imp["module"])
            elif imp["type"] == "from_import":
                if imp["module"]:
                    self.dependency_graph[file_path].add(imp["module"])

        logger.info(f"Added {len(imports)} dependencies for {file_path}")

    def get_dependencies(self, file_path: str) -> Set[str]:
        """
        Get all dependencies for a file

        Args:
            file_path: Path to file

        Returns:
            Set of module names
        """
        return self.dependency_graph.get(file_path, set())

    def get_dependents(self, module_name: str) -> List[str]:
        """
        Get all files that depend on a module

        Args:
            module_name: Name of module

        Returns:
            List of file paths
        """
        dependents = []
        for file_path, deps in self.dependency_graph.items():
            if module_name in deps:
                dependents.append(file_path)

        return dependents

    def get_graph(self) -> Dict[str, Set[str]]:
        """
        Get the complete dependency graph

        Returns:
            Dictionary mapping files to their dependencies
        """
        return self.dependency_graph

    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies

        Returns:
            List of circular dependency chains
        """
        # Simple cycle detection (can be improved)
        cycles = []
        visited = set()

        def dfs(node, path):
                    if not isinstance(node, str) or not isinstance(path, list):
                        raise ValueError("node must be a string and path must be a list")

                    if node in path:
                        cycle_start = path.index(node)
                        cycles.append(path[cycle_start:])
                        return

                    if node in visited:
                        return

                    visited.add(node)
                    path.append(node)

                    if not isinstance(self.dependency_graph, dict):
                        raise TypeError("self.dependency_graph must be a dictionary")

                    for dep in self.dependency_graph.get(node, []):
                        if not isinstance(dep, str):
                            raise ValueError(f"Dependency {dep} under node {node} is not a string")
                        try:
                            dfs(dep, path.copy())
                        except Exception as e:
                            print(f"Error occurred during DFS for node {dep}: {e}")

        for file_path in self.dependency_graph:
            dfs(file_path, [])

        logger.info(f"Found {len(cycles)} circular dependencies")
        return cycles


if __name__ == "__main__":
    # Test DependencyMapper
    mapper = DependencyMapper()

    # Add some test dependencies
    mapper.add_file_dependencies(
        "file1.py", [{"type": "import", "module": "os"}, {"type": "from_import", "module": "pathlib", "name": "Path"}]
    )

    print(f"Dependencies for file1.py: {mapper.get_dependencies('file1.py')}")
