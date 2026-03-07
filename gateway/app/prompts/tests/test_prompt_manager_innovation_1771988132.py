import os
from unittest.mock import patch

def test_load_uc3_strict_happy_path():
    with patch("builtins.open", mock_open(read_data="Mocked UC3 prompt")) as mock_file:
        pm = PromptManager()  # Assuming PromptManager is the class containing _load_uc3_strict
        result = pm._load_uc3_strict()
        assert result == "Mocked UC3 prompt"

def test_load_uc3_strict_no_file():
    with patch("os.path.exists", return_value=False):
        pm = PromptManager()
        result = pm._load_uc3_strict()
        assert result == "You are UC3, a Unified Cognitive Control Agent."

def test_load_uc3_strict_empty_file():
    with patch("builtins.open", mock_open(read_data="")) as mock_file:
        pm = PromptManager()
        result = pm._load_uc3_strict()
        assert result == ""

def test_load_uc3_strict_none_path():
    with patch.dict("os.environ", {"NOUGH_UNIFIED_SYSTEM_ROOT": None}):
        pm = PromptManager()
        result = pm._load_uc3_strict()
        assert result == "You are UC3, a Unified Cognitive Control Agent."

def test_load_uc3_strict_invalid_root():
    with patch.dict("os.environ", {"NOUGH_UNIFIED_SYSTEM_ROOT": "/invalid/path"}):
        pm = PromptManager()
        result = pm._load_uc3_strict()
        assert result == "You are UC3, a Unified Cognitive Control Agent."