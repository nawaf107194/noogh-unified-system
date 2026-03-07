import pytest
from unittest.mock import patch

@pytest.fixture
def mock_env():
    with patch.dict('os.environ', {'NOOGH_STRICT_MODE': '0'}):
        yield

@pytest.fixture
def mock_strict_env():
    with patch.dict('os.environ', {'NOOGH_STRICT_MODE': '1'}):
        yield

@pytest.mark.usefixtures("mock_env")
def test_deprecated_alias_normal(mock_env):
    from coercive_memory import _deprecated_alias

    class NewClass:
        pass

    with pytest.warns(DeprecationWarning) as record:
        alias = _deprecated_alias('old_name', 'new_name', NewClass)
        assert alias is NewClass
        assert len(record) == 1
        assert str(record[0].message) == "old_name is deprecated. Use new_name. This alias will be removed."

@pytest.mark.usefixtures("mock_env")
def test_deprecated_alias_empty_strings(mock_env):
    from coercive_memory import _deprecated_alias

    class NewClass:
        pass

    with pytest.warns(DeprecationWarning) as record:
        alias = _deprecated_alias('', '', NewClass)
        assert alias is NewClass
        assert len(record) == 1
        assert str(record[0].message) == " is deprecated. Use . This alias will be removed."

@pytest.mark.usefixtures("mock_env")
def test_deprecated_alias_none(mock_env):
    from coercive_memory import _deprecated_alias

    class NewClass:
        pass

    with pytest.warns(DeprecationWarning) as record:
        alias = _deprecated_alias(None, None, NewClass)
        assert alias is NewClass
        assert len(record) == 1
        assert str(record[0].message) == "None is deprecated. Use None. This alias will be removed."

@pytest.mark.usefixtures("mock_strict_env")
def test_deprecated_alias_strict_mode(mock_strict_env):
    from coercive_memory import _deprecated_alias

    class NewClass:
        pass

    with pytest.raises(RuntimeError) as excinfo:
        _deprecated_alias('old_name', 'new_name', NewClass)
    assert str(excinfo.value) == "old_name is deprecated. Use new_name. This alias will be removed."

@pytest.mark.usefixtures("mock_env")
def test_deprecated_alias_invalid_inputs(mock_env):
    from coercive_memory import _deprecated_alias

    with pytest.raises(TypeError):
        _deprecated_alias(123, 456, 789)

@pytest.mark.usefixtures("mock_env")
def test_deprecated_alias_with_non_class(mock_env):
    from coercive_memory import _deprecated_alias

    with pytest.raises(TypeError):
        _deprecated_alias('old_name', 'new_name', 'not a class')