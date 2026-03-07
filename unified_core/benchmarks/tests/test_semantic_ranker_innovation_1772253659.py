import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from unified_core.benchmarks.semantic_ranker import get_ranker, SemanticToolRanker, SemanticRankerFallback

CHROMADB_AVAILABLE = True  # Mock this variable for testing purposes

@pytest.fixture
def mock_chromadb_available():
    with patch('unified_core.benchmarks.semantic_ranker.CHROMADB_AVAILABLE', new_callable=MagicMock) as mock:
        yield mock

class TestGetRanker:

    @pytest.mark.parametrize("persist", [True, False])
    def test_happy_path(self, mock_chromadb_available):
        mock_chromadb_available.return_value = True
        ranker = get_ranker(persist)
        assert isinstance(ranker, SemanticToolRanker)

    @pytest.mark.parametrize("persist", [None, ""])
    def test_edge_cases_no_persistence(self, mock_chromadb_available):
        mock_chromadb_available.return_value = True
        ranker = get_ranker(persist=persist)
        assert isinstance(ranker, SemanticToolRanker)

    @pytest.mark.parametrize("persist", ["invalid_path"])
    def test_error_cases_invalid_persistence_path(self, mock_chromadb_available):
        mock_chromadb_available.return_value = True
        ranker = get_ranker(persist=persist)
        assert isinstance(ranker, SemanticToolRanker)  # No exception is raised

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not available")
    def test_fallback_when_chromadb_unavailable(self, mock_chromadb_available):
        mock_chromadb_available.return_value = False
        ranker = get_ranker()
        assert isinstance(ranker, SemanticRankerFallback)