from typing import Dict, Type

class Plugin:
    """Base class for dashboard plugins."""
    def setup(self) -> None:
        """Initialize plugin components and register services."""
        raise NotImplementedError

class PluginManager:
    """Manages plugin lifecycle and feature registration."""
    def __init__(self) -> None:
        self.plugins: Dict[str, Plugin] = {}
        
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a new plugin."""
        plugin_id = plugin.__class__.__name__
        if plugin_id not in self.plugins:
            self.plugins[plugin_id] = plugin
            plugin.setup()
            
    def get_plugin(self, plugin_id: str) -> Plugin:
        """Retrieve a registered plugin."""
        return self.plugins.get(plugin_id)
    
PLUGIN_MANAGER = PluginManager()