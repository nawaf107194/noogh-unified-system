import pytest
from unittest.mock import patch, Mock
import requests
from unified_core.intelligence.news_sentiment_signal_integration import NewsSentimentSignalIntegration

# Mock the NewsSentimentSignalIntegration class to isolate the fetch_news method
class TestNewsSentimentSignalIntegration:
    @pytest.fixture
    def news_api_key(self):
        return "fake_api_key"

    @pytest.fixture
    def news_client(self, news_api_key):
        client = NewsSentimentSignalIntegration()
        client.news_api_key = news_api_key
        return client

    @patch('requests.get')
    def test_fetch_news_happy_path(self, mock_get, news_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {"title": "News Article 1", "description": "Description 1"},
                {"title": "News Article 2", "description": "Description 2"}
            ]
        }
        mock_get.return_value = mock_response

        result = news_client.fetch_news("BTC")
        assert len(result) == 2
        assert result[0]['title'] == 'News Article 1'
        assert result[0]['description'] == 'Description 1'

    @patch('requests.get')
    def test_fetch_news_empty_articles(self, mock_get, news_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": []
        }
        mock_get.return_value = mock_response

        result = news_client.fetch_news("BTC")
        assert len(result) == 0

    @patch('requests.get')
    def test_fetch_news_non_200_status(self, mock_get, news_client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = news_client.fetch_news("BTC")
        assert len(result) == 0

    @patch('requests.get')
    def test_fetch_news_invalid_symbol(self, mock_get, news_client):
        with pytest.raises(ValueError):
            news_client.fetch_news(None)

    @patch('requests.get')
    def test_fetch_news_empty_symbol(self, mock_get, news_client):
        with pytest.raises(ValueError):
            news_client.fetch_news("")