# system_utils.py

class SystemUtils:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_config_path():
        from pathlib import Path
        return Path(__file__).parent / "config"

    @staticmethod
    def load_json_config(config_path):
        import json
        with open(config_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def validate_data_model(data, schema):
        from jsonschema import validate
        validate(data, schema)
        return True

    @staticmethod
    def get_data_router_connection():
        from data_router import DataRouter
        return DataRouter()

    @staticmethod
    def serialize_model(model):
        from .test_serializer import ModelSerializer
        return ModelSerializer.serialize(model)

    @staticmethod
    def get_storage_strategy():
        from .architecture_1772118128 import StorageStrategy
        return StorageStrategy()