import pytest

from unified_core.intelligence.news_sentiment_signal_integration import fetch_news

class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data

    def json(self):
        return self.json_data

def test_fetch_news_happy_path(mocker):
    symbol = "BTC"
    mock_response = MockResponse(200, {"articles": [{"title": "Article 1", "description": "Description 1"}]})
    mocker.patch('requests.get', return_value=mock_response)
    
    result = fetch_news(symbol)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]['title'] == 'Article 1'
    assert result[0]['description'] == 'Description 1'

def test_fetch_news_empty_articles(mocker):
    symbol = "BTC"
    mock_response = MockResponse(200, {"articles": []})
    mocker.patch('requests.get', return_value=mock_response)
    
    result = fetch_news(symbol)
    assert isinstance(result, list)
    assert len(result) == 0

def test_fetch_news_non_200_status(mocker):
    symbol = "BTC"
    mock_response = MockResponse(404, {})
    mocker.patch('requests.get', return_value=mock_response)
    
    result = fetch_news(symbol)
    assert isinstance(result, list)
    assert len(result) == 0

def test_fetch_news_invalid_symbol(mocker):
    symbol = None
    with pytest.raises(TypeError):
        fetch_news(symbol)

def test_fetch_news_empty_string_symbol(mocker):
    symbol = ""
    result = fetch_news(symbol)
    assert isinstance(result, list)
    assert len(result) == 0