import jsonschema
from jsonschema import validate

class DataValidationFramework:
    def __init__(self, schema_path):
        with open(schema_path, 'r') as file:
            self.schema = json.load(file)

    def validate_data(self, data):
        try:
            validate(instance=data, schema=self.schema)
            print("Data is valid.")
        except jsonschema.exceptions.ValidationError as err:
            print(f"Data validation error: {err}")

    @staticmethod
    def create_schema_example():
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["name", "age"]
        }

if __name__ == "__main__":
    # Example usage
    schema_path = 'data_schema.json'
    
    # Create an example schema file
    with open(schema_path, 'w') as file:
        json.dump(DataValidationFramework.create_schema_example(), file)
    
    # Sample data to validate
    sample_data = {
        "name": "John Doe",
        "age": 30,
        "email": "john.doe@example.com"
    }
    
    validator = DataValidationFramework(schema_path)
    validator.validate_data(sample_data)