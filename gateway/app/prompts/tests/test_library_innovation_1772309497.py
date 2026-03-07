import pytest
from pathlib import Path
from datetime import datetime

class MockPromptManager:
    def __init__(self):
        self.prompts = {}
        self.metadata = {}

    def validate_prompt(self, content, category):
        return {"valid": True}

    def create_prompt(self, name, description, template, category, variables, author, safety_level, is_public):
        prompt_id = len(self.prompts) + 1
        self.prompts[prompt_id] = {
            "name": name,
            "description": description,
            "template": template,
            "category": category,
            "variables": variables,
            "author": author,
            "safety_level": safety_level,
            "is_public": is_public
        }
        return prompt_id

class MockMetadata:
    def __init__(self):
        self.data = {}

class TestProcessSingleImport:

    @pytest.fixture
    def mock_manager(self):
        return MockPromptManager()

    @pytest.fixture
    def mock_metadata(self):
        return MockMetadata()

    @pytest.fixture
    def _process_single_import_method(self, mock_manager, mock_metadata):
        class MockClass:
            manager = mock_manager
            metadata = mock_metadata

            def calculate_quality_score(self, content, filepath):
                return 0.95

            def extract_tags(self, content, filepath):
                return ["tag1", "tag2"]

            def extract_use_cases(self, content):
                return ["use_case1", "use_case2"]
        return MockClass()._process_single_import

    @pytest.mark.parametrize("filepath, category, min_quality, max_size_kb, expected", [
        (Path("/path/to/file"), "category", 0.9, 5.0, {"success": True}),
        (Path("/path/to/empty_file"), "category", 0.9, 5.0, {"success": False, "reason": "too large: 1.0KB"}),
        (None, "category", 0.9, 5.0, {"success": False, "reason": None}),
        ("string_path", "category", 0.9, 5.0, {"success": False, "reason": None}),
    ])
    def test_process_single_import(self, _process_single_import_method, filepath, category, min_quality, max_size_kb, expected):
        result = _process_single_import_method(filepath, category, min_quality, max_size_kb)
        assert result == expected

    @pytest.mark.parametrize("filepath, category, min_quality, max_size_kb, expected", [
        (Path("/path/to/small_file"), "category", 1.0, 5.0, {"success": False, "reason": "low quality: 95.00"}),
        (Path("/path/to/file"), "category", 0.8, 2.5, {"success": False, "reason": "too large: 1.0KB"}),
    ])
    def test_process_single_import_edge_cases(self, _process_single_import_method, filepath, category, min_quality, max_size_kb, expected):
        result = _process_single_import_method(filepath, category, min_quality, max_size_kb)
        assert result == expected

    @pytest.mark.parametrize("filepath, category, min_quality, max_size_kb", [
        (Path("/path/to/file_with_invalid_tags"), "category", 0.9, 5.0),
        (Path("/path/to/file_without_valid_use_cases"), "category", 0.9, 5.0),
    ])
    def test_process_single_import_error_cases(self, _process_single_import_method, filepath, category, min_quality, max_size_kb):
        result = _process_single_import_method(filepath, category, min_quality, max_size_kb)
        assert not result["success"]
        assert "reason" in result

    @pytest.mark.parametrize("filepath, category, min_quality, max_size_kb", [
        (Path("/path/to/file"), "category", 0.9, 5.0),
        (None, "category", 0.9, 5.0),
        ("string_path", "category", 0.9, 5.0),
    ])
    def test_process_single_import_async_behavior(self, _process_single_import_method, filepath, category, min_quality, max_size_kb):
        result = _process_single_import_method(filepath, category, min_quality, max_size_kb)
        assert isinstance(result, dict)