import pytest

from noogh_console.architecture_1771632504_1771793711 import create_context, Context

def test_create_context_happy_path():
    # Test with valid data_type and data
    result = create_context('type1', 'test_data')
    assert isinstance(result, Context)
    assert result.data == 'test_data'
    assert result.type == 'type1'

    result = create_context('type2', 'another_test_data')
    assert isinstance(result, Context)
    assert result.data == 'another_test_data'
    assert result.type == 'type2'

def test_create_context_edge_cases():
    # Test with empty data
    result = create_context('type1', '')
    assert isinstance(result, Context)
    assert result.data == ''
    assert result.type == 'type1'

    # Test with None as data
    result = create_context('type1', None)
    assert isinstance(result, Context)
    assert result.data is None
    assert result.type == 'type1'

def test_create_context_error_cases():
    # Test with unknown context type
    with pytest.raises(ValueError) as exc_info:
        create_context('unknown_type', 'test_data')
    assert str(exc_info.value) == "Unknown context type"

if __name__ == "__main__":
    pytest.main()