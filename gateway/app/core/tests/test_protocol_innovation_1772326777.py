import pytest

from gateway.app.core.protocol import create_secure_parser, SecureReActParser

def test_create_secure_parser_happy_path():
    """Test creating a secure parser with default strict_mode"""
    parser = create_secure_parser()
    assert isinstance(parser, SecureReActParser)
    assert parser.strict_mode == True

def test_create_secure_parser_non_strict_mode():
    """Test creating a secure parser in non-strict mode"""
    parser = create_secure_parser(strict_mode=False)
    assert isinstance(parser, SecureReActParser)
    assert parser.strict_mode == False

def test_create_secure_parser_none_input():
    """Test passing None as strict_mode parameter"""
    parser = create_secure_parser(None)
    assert isinstance(parser, SecureReactParser)
    assert parser.strict_mode == True

def test_create_secure_parser_empty_strict_mode():
    """Test passing an empty string as strict_mode parameter"""
    with pytest.raises(TypeError):
        create_secure_parser("")

def test_create_secure_parser_non_boolean_input():
    """Test passing a non-boolean value as strict_mode parameter"""
    with pytest.raises(TypeError):
        create_secure_parser(123)

def test_create_secure_parser_async_behavior():
    # SecureReActParser is not an async function, so this test is not applicable
    pass