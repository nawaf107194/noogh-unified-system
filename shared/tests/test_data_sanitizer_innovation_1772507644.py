import pytest

from shared.data_sanitizer import sanitize_list, DataSanitizer

class TestDataSanitizer:

    def test_sanitize_list_happy_path(self):
        data = ["hello", 123, "world", 45.67]
        expected_result = [DataSanitizer.sanitize_string("hello"), 123, DataSanitizer.sanitize_string("world"), 45.67]
        result = sanitize_list(data)
        assert result == expected_result

    def test_sanitize_list_empty_list(self):
        data = []
        expected_result = []
        result = sanitize_list(data)
        assert result == expected_result

    def test_sanitize_list_none_input(self):
        data = None
        result = sanitize_list(data)
        assert result is None

    def test_sanitize_list_mixed_types(self):
        data = [None, "test", 42, {"key": "value"}, [1, 2, 3], (4, 5)]
        expected_result = [None, DataSanitizer.sanitize_string("test"), 42, {"key": "value"}, [1, 2, 3], (4, 5)]
        result = sanitize_list(data)
        assert result == expected_result

    def test_sanitize_list_invalid_input(self):
        data = set([1, 2, 3])
        result = sanitize_list(data)
        assert result is None