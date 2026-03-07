# reports/config.py

class ConfigurationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._configurations = {}
        return cls._instance

    def register_configuration(self, name, config):
        self._configurations[name] = config

    def get_configuration(self, name):
        return self._configurations.get(name)

class ConfigFactory:
    @staticmethod
    def create_config_manager():
        return ConfigurationManager()

# Usage example
if __name__ == '__main__':
    factory = ConfigFactory()
    manager = factory.create_config_manager()
    manager.register_configuration('default', {'api_key': '12345'})
    config = manager.get_configuration('default')
    print(config)