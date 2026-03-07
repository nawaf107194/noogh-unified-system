import json
from typing import Any, Dict, List, Union

class DataNormalizer:
    """
    A class to handle data normalization across different modules.
    It ensures that all data passed through it adheres to a common format.
    """

    def __init__(self, schema: Dict[str, type]):
        """
        Initialize the normalizer with a schema defining the expected data types.
        
        :param schema: A dictionary where keys are field names and values are expected data types.
        """
        self.schema = schema

    def normalize(self, data: Union[Dict, List]) -> Union[Dict, List]:
        """
        Normalize the input data according to the defined schema.
        
        :param data: The data to be normalized.
        :return: Normalized data.
        """
        if isinstance(data, dict):
            return self._normalize_dict(data)
        elif isinstance(data, list):
            return [self.normalize(item) for item in data]
        else:
            raise ValueError("Unsupported data type")

    def _normalize_dict(self, data: Dict) -> Dict:
        normalized_data = {}
        for key, value in data.items():
            if key in self.schema:
                expected_type = self.schema[key]
                normalized_value = self._convert_to_type(value, expected_type)
                normalized_data[key] = normalized_value
            else:
                # If key not in schema, skip it
                continue
        return normalized_data

    def _convert_to_type(self, value: Any, target_type: type) -> Any:
        try:
            if target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            elif target_type == str:
                return str(value)
            elif target_type == bool:
                return bool(value)
            elif target_type == list:
                return list(value)
            elif target_type == dict:
                return dict(value)
            else:
                return value  # Fallback to original value if type conversion fails
        except (ValueError, TypeError):
            return value  # Return original value if conversion fails

# Example usage
if __name__ == "__main__":
    # Define a sample schema
    schema = {
        "id": int,
        "name": str,
        "value": float,
        "enabled": bool,
        "tags": list,
        "metadata": dict
    }
    
    # Create a normalizer instance
    normalizer = DataNormalizer(schema)
    
    # Sample data to normalize
    sample_data = {
        "id": "123",
        "name": "Sample Item",
        "value": "10.5",
        "enabled": "true",
        "tags": ["tag1", "tag2"],
        "metadata": {"key": "value"},
        "extra_field": "extra"
    }
    
    # Normalize the data
    normalized_data = normalizer.normalize(sample_data)
    print(json.dumps(normalized_data, indent=2))