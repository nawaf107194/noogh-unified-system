# neural_engine/config_manager.py

from singleton_decorator import singleton

@singleton
class ConfigManager:
    def __init__(self, config_source=None):
        self.config_source = config_source or {}
        self.settings = {}

    def load_config(self):
        # Load configuration from a real DB tool or API
        # Example: self.settings = DataRouter.get_configuration()
        pass

    def get_setting(self, key):
        if not self.settings:
            self.load_config()
        return self.settings.get(key)

    def set_setting(self, key, value):
        self.settings[key] = value
        # Optionally, save the setting back to the config source
        # Example: DataRouter.update_configuration(self.settings)