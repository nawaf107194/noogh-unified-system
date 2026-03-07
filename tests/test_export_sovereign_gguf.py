import pytest
from unittest.mock import MagicMock, patch
from export_sovereign_gguf import main

# Mock objects for testing
class MockFastLanguageModel:
    @staticmethod
    def from_pretrained(model_name, max_seq_length, dtype, load_in_4bit):
        return (MagicMock(), MagicMock())

    def save_pretrained_gguf(self, directory, tokenizer, quantization_method):
        pass

    def save_pretrained_merged(self, directory, tokenizer, save_method):
        pass

# Patch the FastLanguageModel class
@pytest.fixture(autouse=True)
def patch_fast_language_model(monkeypatch):
    monkeypatch.setattr("export_sovereign_gguf.FastLanguageModel", MockFastLanguageModel)

# Test case for happy path
def test_main_happy_path(capsys):
    with patch('export_sovereign_gguf.LORA_PATH', 'test_model_path'):
        with patch('export_sovereign_gguf.GGUF_DIR', 'test_export_dir'):
            main()
            captured = capsys.readouterr()
            assert "🚀 Loading model and adapters from test_model_path..." in captured.out
            assert "📦 Exporting to GGUF (q8_0)..." in captured.out
            assert "✅ Export successful! Check test_export_dir" in captured.out

# Test case for edge case - empty LORA_PATH
def test_main_empty_lora_path(capsys):
    with patch('export_sovereign_gguf.LORA_PATH', ''):
        with patch('export_sovereign_gguf.GGUF_DIR', 'test_export_dir'):
            main()
            captured = capsys.readouterr()
            assert "🚀 Loading model and adapters from ..." in captured.out
            assert "📦 Exporting to GGUF (q8_0)..." in captured.out
            assert "✅ Export successful! Check test_export_dir" in captured.out

# Test case for error case - invalid LORA_PATH
def test_main_invalid_lora_path(capsys):
    with patch('export_sovereign_gguf.LORA_PATH', 'invalid_path'):
        with patch('export_sovereign_gguf.GGUF_DIR', 'test_export_dir'):
            main()
            captured = capsys.readouterr()
            assert "🚀 Loading model and adapters from invalid_path..." in captured.out
            assert "📦 Exporting to GGUF (q8_0)..." in captured.out
            assert "✅ Export successful! Check test_export_dir" in captured.out

# Test case for error case - exception during export
def test_main_export_exception(capsys):
    with patch('export_sovereign_gguf.LORA_PATH', 'test_model_path'):
        with patch('export_sovereign_gguf.GGUF_DIR', 'test_export_dir'):
            with patch.object(MockFastLanguageModel, 'save_pretrained_gguf', side_effect=Exception("Export failed")):
                main()
                captured = capsys.readouterr()
                assert "🚀 Loading model and adapters from test_model_path..." in captured.out
                assert "📦 Exporting to GGUF (q8_0)..." in captured.out
                assert "❌ Export failed: Export failed" in captured.out
                assert "Attempting to save as 16-bit safetensors first..." in captured.out

# Test case for async behavior - not applicable in this synchronous function
# This function does not have any asynchronous behavior, so no test is needed for this aspect.