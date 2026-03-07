# config/config_loader.py

import configparser
from typing import Dict, Any

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        config = {}
        parser = configparser.ConfigParser()
        
        # Load the configuration file
        if parser.read(config_path):
            for section in parser.sections():
                config[section] = dict(parser.items(section))
        
        return config

class ConfigLoaderFactory:
    @staticmethod
    def get_config_loader() -> 'ConfigLoader':
        return ConfigLoader()

# Usage example
if __name__ == '__main__':
    loader = ConfigLoaderFactory.get_config_loader()
    config = loader.load_config('config/settings.ini')
    print(config)