import pytest
from gateway.app.core.analytics import get_analytics, AnalyticsStore

def test_get_analytics_happy_path():
    data_dir = "/path/to/test/data"
    analytics_store = get_analytics(data_dir)
    assert isinstance(analytics_store, AnalyticsStore)
    assert analytics_store.db_path == os.path.join(data_dir, ".noogh_memory", "analytics.db")

def test_get_analytics_empty_string():
    with pytest.raises(ValueError) as exc_info:
        get_analytics("")
    assert str(exc_info.value) == "data_dir is required for AnalyticsStore"

def test_get_analytics_none():
    with pytest.raises(ValueError) as exc_info:
        get_analytics(None)
    assert str(exc_info.value) == "data_dir is required for AnalyticsStore"