# config/settings.py

class Settings:
    def get_setting(self, name):
        raise NotImplementedError("Subclasses must implement the get_setting method")

class DevelopmentSettings(Settings):
    def get_setting(self, name):
        return f"Development {name}"

class ProductionSettings(Settings):
    def get_setting(self, name):
        return f"Production {name}"