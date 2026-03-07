# dashboard/config_manager.py

from dataclasses import dataclass
from typing import Optional, Dict, Any
from dashboard.architecture_1772153141 import StatePersistenceStrategy

@dataclass
class DashboardConfig:
    """Data class for holding dashboard configuration properties"""
    theme: str = "default"
    layout: str = "vertical"
    widgets: Dict[str, bool] = None
    permissions: Dict[str, bool] = None

class DashboardConfigManager:
    """Centralized configuration manager for dashboard components"""
    
    def __init__(self, state_persistence: StatePersistenceStrategy):
        self.state_persistence = state_persistence
        self.config = DashboardConfig()
        
    def load_config(self) -> None:
        """Load dashboard configuration from persistence layer"""
        config_data = self.state_persistence.load("dashboard_config")
        if config_data:
            self._apply_config(config_data)
            
    def save_config(self) -> None:
        """Save current configuration to persistence layer"""
        self.state_persistence.save("dashboard_config", self._get_config_dict())
        
    def update_theme(self, theme_name: str) -> None:
        """Update and save theme configuration"""
        self.config.theme = theme_name
        self.save_config()
        
    def update_layout(self, layout_name: str) -> None:
        """Update and save layout configuration"""
        self.config.layout = layout_name
        self.save_config()
        
    def _apply_config(self, config_dict: Dict[str, Any]) -> None:
        """Apply configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
    def _get_config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return {
            'theme': self.config.theme,
            'layout': self.config.layout,
            'widgets': self.config.widgets,
            'permissions': self.config.permissions
        }
        
    @property
    def current_config(self) -> DashboardConfig:
        """Get current configuration object"""
        return self.config