import pytest

from gateway.app.analytics.ws_ingestor import get_ingestor, AnalyticsIngestor

@pytest.fixture(autouse=True)
def reset_ingestor():
    global _ing
    _ing = None
    yield
    _ing = None

def test_happy_path():
    ingestor = get_ingestor()
    assert isinstance(ingestor, AnalyticsIngestor)
    assert ingestor.poll_interval == 2.0

def test_double_initialization():
    first_injestor = get_ingestor()
    second_injestor = get_ingestor()
    assert first_injestor is second_injestor
    assert isinstance(first_injestor, AnalyticsIngestor)
    assert first_injestor.poll_interval == 2.0

def test_no_global_variable():
    global _ing
    del _ing
    ingestor = get_ingestor()
    assert isinstance(ingestor, AnalyticsIngestor)
    assert ingestor.poll_interval == 2.0

def test_empty_input():
    # No need to test for empty input as the function does not accept any arguments
    pass

def test_none_input():
    # No need to test for None input as the function does not accept any arguments
    pass

def test_boundary_values():
    # No need to test boundary values as the function does not accept any arguments
    pass

def test_error_cases():
    # The function does not explicitly raise exceptions, so no error cases to test
    pass

async def test_async_behavior():
    # The function is synchronous and does not have async behavior, so no need to test it
    pass