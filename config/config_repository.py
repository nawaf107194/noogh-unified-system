# config/config_repository.py

class ConfigRepository:
    def __init__(self, config_manager):
        self.config_manager = config_manager

    def get_config(self):
        return self.config_manager.get_config()

    def update_config(self, new_config):
        self.config_manager.update_config(new_config)

    def delete_config(self, key):
        self.config_manager.delete_config(key)