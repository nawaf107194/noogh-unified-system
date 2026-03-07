import pytest

from unified_core.observability.metrics import set_gauge, get_metrics

@pytest.fixture
def metrics_instance():
    return get_metrics()

def test_set_gauge_happy_path(metrics_instance):
    """Test happy path with normal inputs"""
    name = "test_metric"
    value = 42.0
    labels = {"environment": "production"}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value == value

def test_set_gauge_edge_case_empty_name(metrics_instance):
    """Test edge case with empty name"""
    name = ""
    value = 42.0
    labels = {"environment": "production"}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value is None

def test_set_gauge_edge_case_none_value(metrics_instance):
    """Test edge case with None value"""
    name = "test_metric"
    value = None
    labels = {"environment": "production"}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value is None

def test_set_gauge_edge_case_empty_labels(metrics_instance):
    """Test edge case with empty labels"""
    name = "test_metric"
    value = 42.0
    labels = {}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value == value

def test_set_gauge_edge_case_NONE_labels(metrics_instance):
    """Test edge case with None labels"""
    name = "test_metric"
    value = 42.0
    labels = None
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value == value

def test_set_gauge_error_case_invalid_name_type(metrics_instance):
    """Test error case with invalid name type"""
    name = 123
    value = 42.0
    labels = {"environment": "production"}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value is None

def test_set_gauge_error_case_invalid_value_type(metrics_instance):
    """Test error case with invalid value type"""
    name = "test_metric"
    value = "42.0"
    labels = {"environment": "production"}
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value is None

def test_set_gauge_error_case_invalid_labels_type(metrics_instance):
    """Test error case with invalid labels type"""
    name = "test_metric"
    value = 42.0
    labels = ["environment", "production"]
    
    set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value is None

# Assuming get_metrics() returns a Metrics instance with async methods
@pytest.mark.asyncio
async def test_set_gauge_async(metrics_instance):
    """Test async behavior of set_gauge"""
    name = "test_metric"
    value = 42.0
    labels = {"environment": "production"}
    
    await set_gauge(name, value, labels)
    gauge_value = metrics_instance.get_gauge(name, labels)
    assert gauge_value == value