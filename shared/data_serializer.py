import json
import yaml

class DataSerializer:
    @staticmethod
    def serialize(data, format='json'):
        """
        Serialize data into a specified format.
        
        Args:
            data: The data to be serialized.
            format: The format to serialize the data into ('json', 'yaml').
            
        Returns:
            str: The serialized data as a string.
        """
        if format == 'json':
            return json.dumps(data)
        elif format == 'yaml':
            return yaml.dump(data)
        else:
            raise ValueError("Unsupported format. Use 'json' or 'yaml'.")
    
    @staticmethod
    def deserialize(data_str, format='json'):
        """
        Deserialize data from a specified format.
        
        Args:
            data_str: The serialized data as a string.
            format: The format of the serialized data ('json', 'yaml').
            
        Returns:
            The deserialized data.
        """
        if format == 'json':
            return json.loads(data_str)
        elif format == 'yaml':
            return yaml.safe_load(data_str)
        else:
            raise ValueError("Unsupported format. Use 'json' or 'yaml'.")

# Example usage
if __name__ == "__main__":
    sample_data = {
        "name": "John Doe",
        "age": 30,
        "is_student": False,
        "courses": ["Math", "Science"]
    }
    
    # Serialize to JSON
    json_serialized = DataSerializer.serialize(sample_data, 'json')
    print(f"Serialized to JSON: {json_serialized}")
    
    # Deserialize from JSON
    deserialized_data = DataSerializer.deserialize(json_serialized, 'json')
    print(f"Deserialized from JSON: {deserialized_data}")
    
    # Serialize to YAML
    yaml_serialized = DataSerializer.serialize(sample_data, 'yaml')
    print(f"Serialized to YAML: {yaml_serialized}")
    
    # Deserialize from YAML
    deserialized_data_yaml = DataSerializer.deserialize(yaml_serialized, 'yaml')
    print(f"Deserialized from YAML: {deserialized_data_yaml}")