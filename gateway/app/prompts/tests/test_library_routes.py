import pytest
from gateway.app.prompts.library_routes import PromptLibrary, do_import

class MockRequest:
    def __init__(self, categories=None, min_quality=None, max_size_kb=None, limit=None):
        self.categories = categories
        self.min_quality = min_quality
        self.max_size_kb = max_size_kb
        self.limit = limit

def test_do_import_happy_path(tmpdir):
    request = MockRequest(categories=["category1", "category2"], min_quality=0.8, max_size_kb=500, limit=10)
    collection_path = str(tmpdir / "collection")
    library = PromptLibrary(collection_path)
    library.mock_smart_import = lambda _categories, _min_quality, _max_size_kb, _limit: [{"id": "prompt1"}, {"id": "prompt2"}]

    do_import()

    with open("data/prompts/last_import.json", "r") as f:
        results = json.load(f)

    assert results == [{"id": "prompt1"}, {"id": "prompt2"}]
    assert len(results) == 2

def test_do_import_edge_cases(tmpdir):
    request = MockRequest(categories=[], min_quality=None, max_size_kb=0, limit=None)
    collection_path = str(tmpdir / "collection")
    library = PromptLibrary(collection_path)
    library.mock_smart_import = lambda _categories, _min_quality, _max_size_kb, _limit: []

    do_import()

    with open("data/prompts/last_import.json", "r") as f:
        results = json.load(f)

    assert results == []
    assert len(results) == 0

def test_do_import_error_cases(tmpdir):
    request = MockRequest(categories=None, min_quality=1.5, max_size_kb=None, limit=-1)
    collection_path = str(tmpdir / "collection")
    library = PromptLibrary(collection_path)
    library.mock_smart_import = lambda _categories, _min_quality, _max_size_kb, _limit: []

    do_import()

    with open("data/prompts/last_import.json", "r") as f:
        results = json.load(f)

    assert results == []
    assert len(results) == 0

def test_do_import_async_behavior(tmpdir):
    request = MockRequest(categories=["category1"], min_quality=0.8, max_size_kb=500, limit=1)
    collection_path = str(tmpdir / "collection")
    library = PromptLibrary(collection_path)
    library.mock_smart_import = lambda _categories, _min_quality, _max_size_kb, _limit: [{"id": "prompt1"}]

    do_import()

    with open("data/prompts/last_import.json", "r") as f:
        results = json.load(f)

    assert results == [{"id": "prompt1"}]
    assert len(results) == 1