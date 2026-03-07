import pytest
from pathlib import Path
import tempfile
import sys
from unittest.mock import patch, MagicMock

from noogh_unified_system.src.auto_gguf import merge_lora

def test_merge_lora_happy_path(mocker):
    base_model = "test_base_model"
    lora_adapter = "test_lora_adapter"
    output_dir = str(tempfile.mkdtemp())
    
    with patch('noogh_unified_system.src.auto_gguf.AutoModelForCausalLM.from_pretrained') as mock_model:
        model_mock = MagicMock()
        model_mock.device_map = "cpu"
        mock_model.return_value = model_mock
        
        tokenizer_mock = MagicMock()
        
        with patch('noogh_unified_system.src.auto_gguf.AutoTokenizer.from_pretrained', return_value=tokenizer_mock):
            with patch('noogh_unified_system.src.auto_gguf.PeftModel.from_pretrained') as mock_peft_model:
                peft_model_mock = MagicMock()
                mock_peft_model.return_value = peft_model_mock
                
                with patch('noogh_unified_system.src.auto_gguf.Path.mkdir', return_value=None) as mock_mkdir:
                    with patch('noogh_unified_system.src.auto_gguf.merge_lora') as mock_merge_and_unload:
                        result = merge_lora(base_model, lora_adapter, output_dir)
                        
                        assert result == {"success": True, "merged_dir": output_dir}
                        mock_peft_model.assert_called_once_with(model_mock, lora_adapter)
                        peft_model_mock.merge_and_unload.assert_called_once()
                        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_merge_lora_empty_inputs():
    with pytest.raises(ValueError):
        merge_lora("", "")

def test_merge_lora_none_inputs(mocker):
    base_model = None
    lora_adapter = None
    output_dir = None
    
    with patch('noogh_unified_system.src.auto_gguf.AutoModelForCausalLM.from_pretrained', side_effect=ImportError):
        with patch('subprocess.run') as mock_subprocess:
            result = merge_lora(base_model, lora_adapter, output_dir)
            
            assert result == {"success": True, "merged_dir": str(MODELS_DIR / "merged")}
            mock_subprocess.assert_called_once_with(
                [sys.executable, "-m", "peft.merge_and_unload",
                 "--model_name_or_path", base_model,
                 "--peft_model_path", lora_adapter,
                 "--output_dir", output_dir],
                capture_output=True, text=True, timeout=600
            )

def test_merge_lora_error_case(mocker):
    base_model = "test_base_model"
    lora_adapter = "test_lora_adapter"
    output_dir = str(tempfile.mkdtemp())
    
    with patch('noogh_unified_system.src.auto_gguf.AutoModelForCausalLM.from_pretrained', side_effect=ImportError):
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = MagicMock(returncode=1, stderr="Mock error")
            
            result = merge_lora(base_model, lora_adapter, output_dir)
            
            assert result == {"success": False, "error": "Mock error"}
            mock_subprocess.assert_called_once_with(
                [sys.executable, "-m", "peft.merge_and_unload",
                 "--model_name_or_path", base_model,
                 "--peft_model_path", lora_adapter,
                 "--output_dir", output_dir],
                capture_output=True, text=True, timeout=600
            )