# noogh/utils/config_manager.py

class ConfigManager:
    def __init__(self, config_source):
        self.config_source = config_source

    def load_config(self):
        return self.config_source.load()

    def save_config(self, config_data):
        return self.config_source.save(config_data)

class ConfigSource:
    def load(self):
        raise NotImplementedError("Subclasses must implement the load method")

    def save(self, data):
        raise NotImplementedError("Subclasses must implement the save method")

class FileConfigSource(ConfigSource):
    def __init__(self, file_path):
        self.file_path = file_path

    def load(self):
        with open(self.file_path, 'r') as file:
            return json.load(file)

    def save(self, data):
        with open(self.file_path, 'w') as file:
            json.dump(data, file)

class DatabaseConfigSource(ConfigSource):
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def load(self):
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT config FROM settings")
        result = cursor.fetchone()
        return result[0] if result else {}

    def save(self, data):
        cursor = self.db_connection.cursor()
        cursor.execute("UPDATE settings SET config = %s", (data,))
        self.db_connection.commit()

# Usage example
if __name__ == '__main__':
    file_source = FileConfigSource('config.json')
    db_source = DatabaseConfigSource(db_connection)

    file_config_manager = ConfigManager(file_source)
    db_config_manager = ConfigManager(db_source)

    print("File config:", file_config_manager.load_config())
    file_config_manager.save_config({"new_key": "new_value"})

    print("DB config:", db_config_manager.load_config())
    db_config_manager.save_config({"new_key": "new_value"})