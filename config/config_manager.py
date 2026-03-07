# config/config_manager.py

class ConfigurationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls):
        cls.settings = ConfigLoader().load_config()
        cls.ports = Ports().get_ports()
        cls.validator = ConfigValidator()

    @staticmethod
    def get_settings():
        return ConfigurationManager._instance.settings

    @staticmethod
    def get_ports():
        return ConfigurationManager._instance.ports

    @staticmethod
    def validate_config(config):
        return ConfigurationManager._instance.validator.validate(config)

# config/config_loader.py
class ConfigLoader:
    def load_config(self):
        # Logic to load configuration from a file or database
        pass

# config/ports.py
class Ports:
    def get_ports(self):
        # Logic to retrieve port settings
        pass

# config/config_validator.py
class ConfigValidator:
    def validate(self, config):
        # Logic to validate the configuration
        pass

# Usage example
if __name__ == '__main__':
    config_manager = ConfigurationManager()
    settings = config_manager.get_settings()
    ports = config_manager.get_ports()
    is_valid = config_manager.validate_config(settings)