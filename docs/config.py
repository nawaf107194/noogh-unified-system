# docs/config.py

class _ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_ConfigManager, cls).__new__(cls)
            # Initialize any default configurations here
            cls._instance.paths = {}
            cls._instance.styles = {}
        return cls._instance

    def set_path(self, key, path):
        self.paths[key] = path

    def get_path(self, key):
        return self.paths.get(key)

    def set_style(self, key, style):
        self.styles[key] = style

    def get_style(self, key):
        return self.styles.get(key)

# Singleton instance of ConfigManager
config_manager = _ConfigManager()