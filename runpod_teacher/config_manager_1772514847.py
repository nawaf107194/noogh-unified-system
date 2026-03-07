# runpod_teacher/config_manager.py

import json
import os
from singleton_decorator import singleton

@singleton
class ConfigManager:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config_data = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file {self.config_path} not found.")
        
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def get_config(self, key):
        return self.config_data.get(key, None)

    def set_config(self, key, value):
        self.config_data[key] = value
        with open(self.config_path, 'w') as file:
            json.dump(self.config_data, file, indent=4)