import pytest

from dashboard.app_1771891133_1772081385 import FetchNews, GetStats, ParseNooghFormat, App  # Adjust the import accordingly

class MockFetchNews:
    def __init__(self, news_source):
        pass

    def fetch(self):
        return "Mocked news"

class MockGetStats:
    def __init__(self, data_store):
        pass

    def get_stats(self):
        return {"stats": "mocked"}

class MockParseNooghFormat:
    def parse(self, data):
        return "Parsed data"

def test_init_happy_path():
    fetch_news = MockFetchNews("news_source")
    get_stats = MockGetStats("data_store")
    parse_noogh_format = MockParseNooghFormat()

    app = App(fetch_news, get_stats, parse_noogh_format)

    assert app.fetch_news == fetch_news
    assert app.get_stats == get_stats
    assert app.parse_noogh_format == parse_noogh_format

def test_init_edge_case_none():
    fetch_news = None
    get_stats = None
    parse_noogh_format = None

    app = App(fetch_news, get_stats, parse_noogh_format)

    assert app.fetch_news is None
    assert app.get_stats is None
    assert app.parse_noogh_format is None

def test_init_edge_case_empty():
    fetch_news = ""
    get_stats = ""
    parse_noogh_format = ""

    app = App(fetch_news, get_stats, parse_noogh_format)

    assert app.fetch_news == ""
    assert app.get_stats == ""
    assert app.parse_noogh_format == ""

def test_init_error_case_invalid_fetch_news_type():
    with pytest.raises(TypeError):
        App(123, "data_store", MockParseNooghFormat())

def test_init_error_case_invalid_get_stats_type():
    with pytest.raises(TypeError):
        App("news_source", 123, MockParseNooghFormat())

def test_init_error_case_invalid_parse_noogh_format_type():
    with pytest.raises(TypeError):
        App("news_source", "data_store", 123)