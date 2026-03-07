import pytest
from typing import Union, Dict, List

class DataNormalizer:
    def _normalize_dict(self, data: Dict) -> Dict:
        # Mock implementation for testing purposes
        return {key.lower(): value for key, value in data.items()}

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

@pytest.fixture
def normalizer():
    return DataNormalizer()

def test_normalize_happy_path(normalizer):
    input_data = {
        "Name": "John",
        "Age": 30,
        "City": "New York"
    }
    expected_output = {
        "name": "john",
        "age": 30,
        "city": "new york"
    }
    assert normalizer.normalize(input_data) == expected_output

def test_normalize_empty_dict(normalizer):
    input_data = {}
    expected_output = {}
    assert normalizer.normalize(input_data) == expected_output

def test_normalize_none(normalizer):
    input_data = None
    expected_output = None
    result = normalizer.normalize(input_data)
    assert result is None

def test_normalize_list_of_dicts(normalizer):
    input_data = [
        {"Name": "John", "Age": 30},
        {"Name": "Jane", "Age": 25}
    ]
    expected_output = [
        {"name": "john", "age": 30},
        {"name": "jane", "age": 25}
    ]
    assert normalizer.normalize(input_data) == expected_output

def test_normalize_list_with_mixed_types(normalizer):
    input_data = [1, {"Name": "John"}, "string"]
    expected_output = [1, {"name": "john"}, "string"]
    assert normalizer.normalize(input_data) == expected_output

def test_normalize_unsupported_type(normalizer):
    input_data = 42
    result = normalizer.normalize(input_data)
    assert result is None