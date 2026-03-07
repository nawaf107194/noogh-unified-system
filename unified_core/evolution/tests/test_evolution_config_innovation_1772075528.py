import os
from unittest.mock import patch

from unified_core.evolution.evolution_config import _env

def test_env_happy_path():
    with patch.dict(os.environ, {"NOOGH_EVO_key": "123"}):
        assert _env("key", 0) == "123"
        assert _env("key", 0, int) == 123
        assert _env("key", 0.5, float) == 123.0

def test_env_empty():
    with patch.dict(os.environ, {}):
        assert _env("nonexistent", "default") == "default"

def test_env_none():
    with patch.dict(os.environ, {"NOOGH_EVO_key": None}):
        assert _env("key", 0) is None
        assert _env("key", 0, int) is None
        assert _env("key", 0.5, float) is None

def test_env_invalid_cast():
    with patch.dict(os.environ, {"NOOGH_EVO_key": "not_an_int"}):
        assert _env("key", 0, int) == 0
        assert _env("key", 0.5, float) == 0.5

def test_env_boundary_cases():
    with patch.dict(os.environ, {"NOOGH_EVO_key": "-123"}):
        assert _env("key", 0, int) == -123
        assert _env("key", 0.5, float) == -123.0

def test_env_empty_string_cast():
    with patch.dict(os.environ, {"NOOGH_EVO_key": ""}):
        assert _env("key", "default") == ""
        assert _env("key", "", str) == ""

def test_env_none_cast():
    with patch.dict(os.environ, {"NOOGH_EVO_key": None}):
        assert _env("key", None, int) is None
        assert _env("key", None, float) is None