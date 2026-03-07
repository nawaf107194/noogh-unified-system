# noogh/utils/config_manager.py

class ConfigManager:
    def __init__(self, config_source):
        self.config = self._load_config(config_source)

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data)

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, 'r') as file:
            return cls(file.read())

    @classmethod
    def from_db(cls, db_connection):
        return cls(db_connection.query("SELECT config FROM settings"))

    def _load_config(self, source):
        if isinstance(source, str):
            return self._parse_json(source)
        elif hasattr(source, 'read'):
            return self._parse_json(source.read())
        else:
            raise ValueError("Unsupported config source type")

    @staticmethod
    def _parse_json(json_data):
        import json
        return json.loads(json_data)

# Usage example

if __name__ == '__main__':
    # Using JSON string
    config_json = '{"key": "value"}'
    config_manager = ConfigManager.from_json(config_json)
    print(config_manager.config)

    # Using file
    with open('config.json', 'r') as file:
        config_manager_file = ConfigManager.from_file(file)
        print(config_manager_file.config)

    # Using database connection
    from some_db_library import DatabaseConnection
    db_connection = DatabaseConnection()
    config_manager_db = ConfigManager.from_db(db_connection)
    print(config_manager_db.config)