from typing import Type, Dict, Any, Optional
from .noogh_exec_mcp_base import NooGHExecMCPBase

class ExecMCPFactory:
    def __init__(self):
        self._exec_mcp_map: Dict[str, Type[NooGHExecMCPBase]] = {}

    def register(self, name: str, exec_mcp_class: Type[NooGHExecMCPBase]):
        """Register a new ExecMCP implementation"""
        self._exec_mcp_map[name] = exec_mcp_class

    def create_exec_mcp(self, name: str, **kwargs) -> Optional[NooGHExecMCPBase]:
        """Create an ExecMCP instance by name"""
        exec_mcp_class = self._exec_mcp_map.get(name)
        if exec_mcp_class is None:
            raise ValueError(f"Unknown ExecMCP type: {name}")
        return exec_mcp_class(**kwargs)