# config/config_repository.py

class ConfigRepository:
    def __init__(self, config_source):
        self.config_source = config_source

    def get_configuration(self, config_name):
        # Implement logic to retrieve configuration from the source
        return self.config_source.get(config_name)

    def save_configuration(self, config_name, config_data):
        # Implement logic to save configuration to the source
        self.config_source[config_name] = config_data

    def delete_configuration(self, config_name):
        # Implement logic to delete configuration from the source
        if config_name in self.config_source:
            del self.config_source[config_name]