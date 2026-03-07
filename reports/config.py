# reports/config.py

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
            # Initialize your configuration settings here
            cls._instance.settings = {}
        return cls._instance

    def get_setting(self, key):
        return self.settings.get(key)

    def set_setting(self, key, value):
        self.settings[key] = value

# Example usage in another module
from reports.config import Config

def apply_config():
    config = Config()
    config.set_setting('api_key', 'your_api_key_here')
    print(config.get_setting('api_key'))

if __name__ == "__main__":
    apply_config()