import pytest
from typing import Union, Dict, List

class DataNormalizer:
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

    def _normalize_dict(self, data: Dict):
        # Example normalization logic
        normalized_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                normalized_data[key] = self._normalize_dict(value)
            elif isinstance(value, list):
                normalized_data[key] = [self.normalize(item) for item in value]
            else:
                normalized_data[key] = value.upper()
        return normalized_data

def test_normalize_happy_path():
    normalizer = DataNormalizer()
    data = {
        "name": "John Doe",
        "age": 30,
        "address": {
            "street": "123 Main St",
            "city": "Anytown"
        },
        "hobbies": ["Reading", "Traveling"]
    }
    expected_output = {
        "NAME": "JOHN DOE",
        "AGE": 30,
        "ADDRESS": {
            "STREET": "123 MAIN ST",
            "CITY": "ANYTOWN"
        },
        "HOBBIES": ["READING", "TRAVELING"]
    }
    assert normalizer.normalize(data) == expected_output

def test_normalize_empty_dict():
    normalizer = DataNormalizer()
    data = {}
    assert normalizer.normalize(data) == {}

def test_normalize_none_input():
    normalizer = DataNormalizer()
    data = None
    with pytest.raises(ValueError):
        normalizer.normalize(data)

def test_normalize_non_dict_list():
    normalizer = DataNormalizer()
    data = ["item1", "item2"]
    assert normalizer.normalize(data) == ["ITEM1", "ITEM2"]

def test_normalize_empty_list():
    normalizer = DataNormalizer()
    data = []
    assert normalizer.normalize(data) == []

def test_normalize_mixed_types():
    normalizer = DataNormalizer()
    data = {
        "name": "John Doe",
        "age": 30,
        "address": ["123 Main St", "Anytown"],
        "hobbies": {"Reading": "Books"}
    }
    expected_output = {
        "NAME": "JOHN DOE",
        "AGE": 30,
        "ADDRESS": ["123 MAIN ST", "ANYTOWN"],
        "HOBBIES": {"READING": "BOOKS"}
    }
    assert normalizer.normalize(data) == expected_output