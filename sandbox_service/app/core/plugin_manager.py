from typing import Dict, Type, Protocol, runtime_checkable

@runtime_checkable
class SandboxPlugin(Protocol):
    """Interface for sandbox plugins"""
    @classmethod
    def get_plugin_type(cls) -> str:
        """Return the type identifier for this plugin"""
        ...
    
    async def initialize(self, config: Dict) -> None:
        """Initialize the sandbox implementation"""
        ...
    
    async def execute(self, input_data: Dict) -> Dict:
        """Execute the sandbox logic"""
        ...

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Type[SandboxPlugin]] = {}
        
    def register_plugin(self, plugin_type: str, plugin_class: Type[SandboxPlugin]):
        """Register a new plugin"""
        if not issubclass(plugin_class, SandboxPlugin):
            raise ValueError("Plugin must implement SandboxPlugin interface")
        self.plugins[plugin_type] = plugin_class
        
    def get_plugin(self, plugin_type: str) -> Type[SandboxPlugin]:
        """Get a registered plugin"""
        if plugin_type not in self.plugins:
            raise ValueError(f"Plugin {plugin_type} not registered")
        return self.plugins[plugin_type]
        
    async def create_plugin_instance(self, plugin_type: str, config: Dict) -> SandboxPlugin:
        """Create an instance of the specified plugin"""
        plugin_class = self.get_plugin(plugin_type)
        instance = plugin_class()
        await instance.initialize(config)
        return instance