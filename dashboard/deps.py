# dashboard/deps.py

from unified_core.core.config_manager import ConfigManager
from .app_1771891133 import App1771891133
from .plugin_manager import PluginManager

def get_config_manager():
    return ConfigManager()

def get_plugin_manager(config_manager):
    return PluginManager(config_manager)

def get_app(plugin_manager):
    return App1771891133(plugin_manager)