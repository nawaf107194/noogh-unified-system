import pytest
from typing import List, Tuple

from gateway.app.routing.dynamic_endpoint_router import DynamicEndpointRouter

@pytest.fixture
def valid_endpoints():
    return [("endpoint1", 10), ("endpoint2", 5)]

def test_init_happy_path(valid_endpoints):
    router = DynamicEndpointRouter(valid_endpoints)
    assert len(router.endpoints) == 2
    assert router.endpoint_map == {"endpoint1": 10, "endpoint2": 5}

def test_init_empty_list():
    router = DynamicEndpointRouter([])
    assert len(router.endpoints) == 0
    assert router.endpoint_map == {}

def test_init_none_input():
    router = DynamicEndpointRouter(None)
    assert router.endpoints is None
    assert router.endpoint_map is None

def test_init_invalid_input():
    with pytest.raises(TypeError):
        DynamicEndpointRouter("not a list")