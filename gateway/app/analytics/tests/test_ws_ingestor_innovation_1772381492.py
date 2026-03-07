import pytest

from gateway.app.analytics.ws_ingestor import get_ingestor, _ing, AnalyticsIngestor

@pytest.fixture(autouse=True)
def reset_ingredient():
    global _ing
    _ing = None

def test_get_ingestor_happy_path():
    # Call the function multiple times to ensure it returns the same instance
    ingestor1 = get_ingestor()
    ingestor2 = get_ingestor()
    
    assert isinstance(ingestor1, AnalyticsIngestor)
    assert ingestor1 == ingestor2

def test_get_ingestor_edge_case_none():
    global _ing
    _ing = None
    
    result = get_ingestor()
    
    assert isinstance(result, AnalyticsIngestor)

def test_get_ingestor_edge_case_instance_exists():
    global _ing
    existing_ingredient = AnalyticsIngestor(poll_interval=2.0)
    _ing = existing_ingredient
    
    result = get_ingestor()
    
    assert isinstance(result, AnalyticsIngestor)
    assert result == existing_ingredient

def test_get_ingestor_async_behavior():
    # Since the function is synchronous and does not involve async behavior,
    # there is no need to create tests for async behavior in this case.
    pass