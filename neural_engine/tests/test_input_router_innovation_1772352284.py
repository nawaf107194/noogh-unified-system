import pytest
from noogh_unified_system.src.neural_engine.input_router import InputRouter
from noogh_unified_system.src.neural_engine.attention_mechanism import AttentionMechanism
from noogh_unified_system.src.neural_engine.filter_system import FilterSystem
from noogh_unified_system.src.utils.logging import logger

@pytest.fixture
def input_router():
    return InputRouter()

def test_happy_path(input_router):
    assert isinstance(input_router.attention, AttentionMechanism)
    assert isinstance(input_router.filters, FilterSystem)
    assert "InputRouter initialized." in caplog.text

def test_edge_case_none_attention(input_router):
    input_router.attention = None
    assert isinstance(input_router.attention, type(None))
    assert "InputRouter initialized." in caplog.text

def test_edge_case_none_filters(input_router):
    input_router.filters = None
    assert isinstance(input_router.filters, type(None))
    assert "InputRouter initialized." in caplog.text

def test_error_case_invalid_attention(init_args):
    with pytest.raises(TypeError):
        InputRouter(attention=init_args)

def test_error_case_invalid_filters(init_args):
    with pytest.raises(TypeError):
        InputRouter(filters=init_args)