"""
Tool Adapter for NOOGH Neural Engine.

Bridges the tool_executor to actual tool functions.
Provides a ToolRegistry that maps tool names to callables.
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Singleton
_registry: Optional["ToolRegistry"] = None


class ToolRegistry:
    """Simple tool registry that maps names to callables."""

    def __init__(self):
        self._tools: Dict[str, Callable] = {}

    # ------------------------------------------------------------------
    def register_function(self, name: str, func: Callable) -> None:
        """Register a callable under *name*."""
        self._tools[name] = func
        logger.debug(f"Registered tool: {name}")

    # ------------------------------------------------------------------
    async def execute(self, name: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute tool *name* with the given *params*.

        Handles both sync and async callables.
        Extra kwargs (e.g. auth_context) are accepted but not forwarded to keep tools simple.
        """
        func = self._tools.get(name)
        if func is None:
            logger.warning(f"Unknown tool requested: {name}")
            return {
                "success": False,
                "error": f"Tool '{name}' not found",
                "result": {"summary_ar": f"الأداة '{name}' غير متوفرة"},
            }

        try:
            if inspect.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)

            # Normalise: ensure we always return a dict
            if not isinstance(result, dict):
                result = {"success": True, "result": result}
            if "success" not in result:
                result["success"] = True
            return result

        except Exception as exc:
            logger.error(f"Tool '{name}' execution error: {exc}", exc_info=True)
            return {
                "success": False,
                "error": str(exc),
                "result": {"summary_ar": f"فشل تنفيذ الأداة: {exc}"},
            }

    # ------------------------------------------------------------------
    @property
    def tool_names(self):
        return list(self._tools.keys())

    def __len__(self):
        return len(self._tools)

    def __repr__(self):
        return f"<ToolRegistry tools={len(self._tools)}>"


def get_tool_registry() -> ToolRegistry:
    """Return the singleton ToolRegistry (create on first call)."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_default_tools(_registry)
        logger.info(f"🔧 ToolRegistry created with {len(_registry)} tools: {_registry.tool_names}")
    return _registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """Register actual tool implementations from system_tools and basic_tools."""
    try:
        from . import system_tools
        from . import basic_tools

        # Map prompt tool names → actual functions
        registry.register_function("sys.info", system_tools.get_system_status)
        registry.register_function("sys.execute", system_tools.system_shell)
        registry.register_function("fs.read", system_tools.read_system_file)
        registry.register_function("fs.write", system_tools.write_file)
        registry.register_function("mem.search", basic_tools.search_memory)
        
        # Also register under full names for flexibility
        registry.register_function("get_system_status", system_tools.get_system_status)
        registry.register_function("get_gpu_status", system_tools.get_gpu_status)
        registry.register_function("system_shell", system_tools.system_shell)
        registry.register_function("read_system_file", system_tools.read_system_file)
        registry.register_function("get_current_time", system_tools.get_current_time)
        registry.register_function("execute_command", basic_tools.execute_command)
        registry.register_function("read_file", basic_tools.read_file)
        registry.register_function("search_memory", basic_tools.search_memory)

    except Exception as e:
        logger.error(f"Failed to register default tools: {e}", exc_info=True)

