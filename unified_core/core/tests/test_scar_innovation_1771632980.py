import pytest

from unified_core.core.scar import _deprecated_alias, DeprecationWarning

def test_deprecated_alias_happy_path():
    class NewClass:
        pass
    
    result = _deprecated_alias('old_name', 'new_name', NewClass)
    assert result == NewClass

def test_deprecated_alias_empty_old_name():
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning):
        result = _deprecated_alias('', 'new_name', NewClass)
        assert result == NewClass

def test_deprecated_alias_none_new_name():
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning):
        result = _deprecated_alias('old_name', None, NewClass)
        assert result == NewClass

def test_deprecated_alias_boundary_old_name():
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning):
        result = _deprecated_alias('a' * 1000, 'new_name', NewClass)
        assert result == NewClass

def test_deprecated_alias_boundary_new_name():
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning):
        result = _deprecated_alias('old_name', 'b' * 1000, NewClass)
        assert result == NewClass

def test_deprecated_alias_strict_mode_enabled():
    os.environ["NOOGH_STRICT_MODE"] = "1"
    
    class NewClass:
        pass
    
    with pytest.raises(RuntimeError):
        _deprecated_alias('old_name', 'new_name', NewClass)

def test_deprecated_alias_strict_mode_disabled():
    os.environ["NOOGH_STRICT_MODE"] = "0"
    
    class NewClass:
        pass
    
    with pytest.warns(DeprecationWarning):
        result = _deprecated_alias('old_name', 'new_name', NewClass)
        assert result == NewClass

def test_deprecated_alias_invalid_new_class():
    with pytest.raises(TypeError):
        _deprecated_alias('old_name', 'new_name', None)