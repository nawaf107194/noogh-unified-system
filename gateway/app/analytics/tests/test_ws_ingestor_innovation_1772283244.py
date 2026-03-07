import pytest

from gateway.app.analytics.ws_ingestor import get_ingestor, AnalyticsIngestor

@pytest.fixture(autouse=True)
def reset_ingestor():
    global _ing
    _ing = None

def test_get_ingestor_happy_path():
    ingestor = get_ingestor()
    assert isinstance(ingestor, AnalyticsIngestor)
    assert ingestor.poll_interval == 2.0

def test_get_ingestor_edge_case_none_input():
    global _ing
    _ing = None
    ingestor1 = get_ingestor()
    ingestor2 = get_ingestor()
    assert ingestor1 is ingestor2
    assert isinstance(ingestor1, AnalyticsIngestor)
    assert ingestor1.poll_interval == 2.0

def test_get_ingestor_edge_case_existing_instance():
    global _ing
    existing_ingestor = AnalyticsIngestor(poll_interval=2.0)
    _ing = existing_ingestor
    ingestor = get_ingestor()
    assert ingestor is existing_ingestor
    assert isinstance(ingestor, AnalyticsIngestor)
    assert ingestor.poll_interval == 2.0

def test_get_ingestor_error_case_invalid_input():
    with pytest.raises(TypeError):
        get_ingestor(poll_interval="not a number")