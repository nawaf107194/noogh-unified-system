# noogh-console/coordinator.py

class ArchitecturalCoordinator:
    def __init__(self, components=None):
        self.components = components or []
        self._setup_component_dependencies()
        
    def _setup_component_dependencies(self):
        """Automatically wire component dependencies"""
        for component in self.components:
            for dep in getattr(component, 'dependencies', []):
                if dep in [c.__class__.__name__ for c in self.components]:
                    idx = [c.__class__.__name__ for c in self.components].index(dep)
                    setattr(component, dep.lower(), self.components[idx])

    def initialize_components(self):
        """Initialize all architectural components in order"""
        for component in self.components:
            if hasattr(component, 'initialize'):
                component.initialize()

    async def execute_pipeline(self, data):
        """Execute architectural components in sequence"""
        for component in self.components:
            data = await component.process(data)
        return data

    def register_component(self, component):
        """Register new architectural component"""
        self.components.append(component)
        self._setup_component_dependencies()