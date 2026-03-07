import pytest

class Config:
    def __init__(self):
        self.styles = {}

    def set_style(self, key, style):
        self.styles[key] = style

def test_set_style_happy_path():
    config = Config()
    config.set_style('font', 'Arial')
    assert config.styles == {'font': 'Arial'}

def test_set_style_empty_key():
    config = Config()
    config.set_style('', 'Arial')
    assert config.styles == {}

def test_set_style_none_key():
    config = Config()
    config.set_style(None, 'Arial')
    assert config.styles == {None: 'Arial'}

def test_set_style_boundary_values():
    config = Config()
    config.set_style('max_length', 100)
    assert config.styles == {'max_length': 100}

def test_set_style_invalid_key_type():
    config = Config()
    config.set_style(123, 'Arial')
    assert config.styles == {123: 'Arial'}

def test_set_style_invalid_style_value():
    config = Config()
    config.set_style('color', None)
    assert config.styles == {'color': None}