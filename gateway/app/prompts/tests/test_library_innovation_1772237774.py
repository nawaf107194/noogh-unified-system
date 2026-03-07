import pytest
from pathlib import Path
from typing import List, Dict
from unittest.mock import patch, MagicMock

from gateway.app.prompts.library import Library

class MockLibrary(Library):
    def __init__(self):
        self.collection_dir = Path("test_collection")
        self.imported = []
        self.skipped = []

    def _process_single_import(self, filepath, category, min_quality, max_size_kb):
        return {
            "success": True,
            "data": {
                "quality": 0.9,
                "tags": ["feature", "enhancement"]
            }
        }

def test_smart_import_happy_path():
    library = MockLibrary()
    result = library.smart_import(categories=["core"], limit=1)
    assert len(result["imported"]) == 1
    assert len(result["skipped"]) == 0

def test_smart_import_with_empty_categories():
    library = MockLibrary()
    result = library.smart_import(categories=[])
    assert len(result["imported"]) == 0
    assert len(result["skipped"]) == 0

def test_smart_import_with_invalid_category():
    library = MockLibrary()
    with patch.object(library.collection_dir, "glob", return_value=[]):
        result = library.smart_import(categories=["nonexistent"])
    assert len(result["imported"]) == 0
    assert len(result["skipped"]) == 1

def test_smart_import_with_limit_reached():
    library = MockLibrary()
    for _ in range(2):
        with patch.object(library.collection_dir, "glob", return_value=[Path("file.txt")]):
            result = library.smart_import(categories=["core"], limit=2)
    assert len(result["imported"]) == 2
    assert len(result["skipped"]) == 0

def test_smart_import_with_skipped_files():
    library = MockLibrary()
    with patch.object(library.collection_dir, "glob", return_value=[Path("file.txt")]):
        result = library.smart_import(categories=["core"], limit=1, min_quality=1.0)
    assert len(result["imported"]) == 0
    assert len(result["skipped"]) == 1

def test_smart_import_with_no_files():
    library = MockLibrary()
    with patch.object(library.collection_dir, "glob", return_value=[]):
        result = library.smart_import(categories=["core"])
    assert len(result["imported"]) == 0
    assert len(result["skipped"]) == 0

def test_smart_import_with_async_behavior():
    async def mock_process_single_import(self, filepath, category, min_quality, max_size_kb):
        return {
            "success": True,
            "data": {
                "quality": 0.9,
                "tags": ["feature", "enhancement"]
            }
        }

    library = MockLibrary()
    with patch.object(library, "_process_single_import", side_effect=mock_process_single_import):
        result = library.smart_import(categories=["core"], limit=1)
    assert len(result["imported"]) == 1
    assert len(result["skipped"]) == 0