import pytest
from unittest.mock import patch, MagicMock
from gateway.app.ml.hf_data_manager import HFDataManager

@pytest.fixture
def data_manager():
    return HFDataManager()

@patch('gateway.app.ml.hf_data_manager.HFDataManager.api')
def test_search_datasets_happy_path(mock_api, data_manager):
    mock_response = [
        MagicMock(id="1", description="Dataset 1", tags=["tag1"], lastModified="2023-04-01T00:00:00Z"),
        MagicMock(id="2", description="Dataset 2", tags=[], lastModified="2023-04-02T00:00:00Z")
    ]
    mock_api.list_datasets.return_value = mock_response
    results = data_manager.search_datasets("query", limit=2)
    assert len(results) == 2
    assert results[0] == {
        "id": "1",
        "description": "Dataset 1...",
        "downloads": None,
        "likes": None,
        "tags": ["tag1"],
        "author": None,
        "last_modified": "2023-04-01T00:00:00Z"
    }
    assert results[1] == {
        "id": "2",
        "description": "Dataset 2...",
        "downloads": None,
        "likes": None,
        "tags": [],
        "author": None,
        "last_modified": "2023-04-02T00:00:00Z"
    }

@patch('gateway.app.ml.hf_data_manager.HFDataManager.api')
def test_search_datasets_empty_query(mock_api, data_manager):
    with patch.object(data_manager.logger, 'warning') as mock_logger:
        results = data_manager.search_datasets("", limit=10)
        assert not results
        mock_logger.assert_called_once_with("Empty query received, returning default")

@patch('gateway.app.ml.hf_data_manager.HFDataManager.api')
def test_search_datasets_none_query(mock_api, data_manager):
    with patch.object(data_manager.logger, 'warning') as mock_logger:
        results = data_manager.search_datasets(None, limit=10)
        assert not results
        mock_logger.assert_called_once_with("Empty query received, returning default")

@patch('gateway.app.ml.hf_data_manager.HFDataManager.api')
def test_search_datasets_limit(mock_api, data_manager):
    mock_response = [
        MagicMock(id="1", description="Dataset 1", tags=["tag1"], lastModified="2023-04-01T00:00:00Z"),
        MagicMock(id="2", description="Dataset 2", tags=[], lastModified="2023-04-02T00:00:00Z"),
        MagicMock(id="3", description="Dataset 3", tags=["tag2"], lastModified="2023-04-03T00:00:00Z")
    ]
    mock_api.list_datasets.return_value = mock_response
    results = data_manager.search_datasets("query", limit=2)
    assert len(results) == 2

@patch('gateway.app.ml.hf_data_manager.HFDataManager.api')
def test_search_datasets_no_results(mock_api, data_manager):
    mock_api.list_datasets.return_value = []
    results = data_manager.search_datasets("query", limit=10)
    assert not results