import importlib
import pkgutil
from typing import Dict, List

class DependencyResolver:
    def __init__(self):
        self._module_dependencies = {}
        self._loaded_modules = set()

    def add_module_dependency(self, module_name: str, dependencies: List[str]):
        """Add dependencies for a given module."""
        self._module_dependencies[module_name] = dependencies

    def resolve_dependencies(self, module_names: List[str]) -> List[str]:
        """Resolve and return the list of modules in the correct loading order."""
        resolved_order = []
        visited = set()
        
        def visit(module_name: str) -> None:
            if module_name in visited:
                return
            visited.add(module_name)
            
            for dep in self._module_dependencies.get(module_name, []):
                visit(dep)
                
            if module_name not in self._loaded_modules:
                resolved_order.append(module_name)
                self._loaded_modules.add(module_name)
                
        for module_name in module_names:
            visit(module_name)
            
        return resolved_order

    def load_module(self, module_name: str) -> None:
        """Load a module using importlib."""
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            print(f"Failed to load module {module_name}: {e}")

    def load_modules(self, module_names: List[str]) -> None:
        """Load modules in the correct order based on their dependencies."""
        resolved_order = self.resolve_dependencies(module_names)
        for module_name in resolved_order:
            self.load_module(module_name)

def discover_modules(package):
    """Discover all submodules within a package."""
    modules = []
    prefix = f"{package.__name__}."
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
        modules.append(modname)
    return modules

# Example usage
if __name__ == "__main__":
    resolver = DependencyResolver()
    resolver.add_module_dependency("neural_engine.api.auth", ["noogh.utils.security"])
    resolver.add_module_dependency("gateway.app.analytics.event_store", ["memory_storage.architecture_1771283668"])
    
    # Discover and load modules from a package
    discovered_modules = discover_modules(shared)
    resolver.load_modules(discovered_modules)