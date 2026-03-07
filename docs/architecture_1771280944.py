# docs/config.py
class Config:
    def __init__(self, settings):
        self.settings = settings

# docs/__init__.py
from .config import Config

def initialize_docs(config):
    # Use the config object here
    print(f"Docs initialized with settings: {config.settings}")

# Example usage:
if __name__ == "__main__":
    # Create a configuration instance
    config = Config(settings={"theme": "dark", "language": "en"})
    
    # Pass the config to the initialization function
    initialize_docs(config)