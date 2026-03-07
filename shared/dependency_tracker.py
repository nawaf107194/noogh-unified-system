import importlib.util
import os
from typing import Dict, List

class DependencyTracker:
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = {}

    def scan_directory(self, directory: str) -> None:
        """Scans the given directory for Python files and tracks their imports."""
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    module_name = file_path.replace(os.sep, '.').replace('.py', '')
                    self.track_imports(module_name, file_path)

    def track_imports(self, module_name: str, file_path: str) -> None:
        """Tracks the imports of a given Python file."""
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return
        if hasattr(module, '__file__'):
            with open(module.__file__, 'r') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('import ') or line.startswith('from '):
                        self.add_dependency(module_name, line.strip())

    def add_dependency(self, module_name: str, import_statement: str) -> None:
        """Adds a dependency from the given module to the imported module."""
        if module_name not in self.dependencies:
            self.dependencies[module_name] = []
        self.dependencies[module_name].append(import_statement)

    def print_dependencies(self) -> None:
        """Prints all tracked dependencies."""
        for module, dependencies in self.dependencies.items():
            print(f"{module} depends on:")
            for dep in dependencies:
                print(f"  - {dep}")

# Example usage
if __name__ == "__main__":
    tracker = DependencyTracker()
    # Replace with actual directory paths you want to track
    tracker.scan_directory('agents')
    tracker.scan_directory('neural_engine')
    tracker.print_dependencies()