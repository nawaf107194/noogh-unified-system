import pytest

from gateway.app.core.protocol import create_secure_parser, SecureReActParser

def test_create_secure_parser_happy_path():
    """Test normal inputs."""
    parser = create_secure_parser()
    assert isinstance(parser, SecureReActParser)
    assert parser.strict_mode is True

def test_create_secure_parser_explicit_false_strict_mode():
    """Test with explicit False strict_mode."""
    parser = create_secure_parser(strict_mode=False)
    assert isinstance(parser, SecureReActParser)
    assert parser.strict_mode is False

def test_create_secure_parser_edge_case_none_strict_mode():
    """Test with None as strict_mode (should default to True)."""
    parser = create_secure_parser(None)
    assert isinstance(parser, SecureReActParser)
    assert parser.strict_mode is True

def test_create_secure_parser_edge_case_empty_strict_mode():
    """Test with empty string as strict_mode."""
    parser = create_secure_parser('')
    assert isinstance(parser, SecureReactParser)
    assert parser.strict_mode is True

def test_create_secure_parser_error_case_invalid_type():
    """Test with invalid type input (should default to True)."""
    with pytest.raises(TypeError):
        create_secure_parser(123)

def test_create_secure_parser_error_case_non_bool():
    """Test with non-bool value input."""
    with pytest.raises(ValueError):
        create_secure_parser('not a bool')