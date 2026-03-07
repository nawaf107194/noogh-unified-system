import pytest
from src.tools.utils import safe_divide

def test_serialization_happy_path():
    result = safe_divide(10, 2)
    assert result == 5

def test_serialization_edge_case_zero_denominator():
    result = safe_divide(10, 0)
    assert result is None or result == float('inf')

def test_serialization_edge_case_none_input():
    result = safe_divide(None, 2)
    assert result is None

def test_serialization_error_case_non_number_input():
    with pytest.raises(TypeError):
        result = safe_divide("10", 2)

def test_serialization_async_behavior():
    async def async_safe_divide(a, b):
        return await safe_divide(a, b)

    import asyncio
    result = asyncio.run(async_safe_divide(10, 2))
    assert result == 5

    result = asyncio.run(async_safe_divide(None, 2))
    assert result is None

    with pytest.raises(TypeError):
        result = asyncio.run(async_safe_divide("10", 2))