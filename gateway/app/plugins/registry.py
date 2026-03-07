from typing import Any, Dict


class PluginRegistry:
    _instance = None

    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}  # Map tool_name -> func

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def register_plugin(self, name: str, metadata: dict):
        self.plugins[name] = metadata

    def register_tool(self, name: str, func: Any):
        if name in self.tools:
            raise ValueError(f"Tool {name} already registered in plugins")
        self.tools[name] = func

    def clear(self):
        self.plugins.clear()
        self.tools.clear()
